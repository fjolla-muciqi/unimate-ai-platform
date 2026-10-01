"""Mbush bazën me të dhëna demo.

Idempotent: mund të ekzekutohet disa herë pa krijuar dublikatë.

    python -m scripts.seed
"""

import hashlib
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.ai.rag.ingestion import ingest_document_in_background
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.periods import period_for_semester
from app.core.security import hash_password
from app.core.teaching import least_filled_group
from app.models.academic_period import (
    SUMMER,
    WINTER,
    AcademicPeriod,
    term_for_semester,
)
from app.models.course import Course
from app.models.course_group import CourseGroup
from app.models.course_prerequisite import CoursePrerequisite
from app.models.deadline import Deadline
from app.models.document import Document, DocumentStatus
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.exam import Exam
from app.models.notification import Notification
from app.models.professor import Professor
from app.models.program import Program
from app.models.schedule import Schedule
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from scripts.curriculum import (
    CURRICULUM,
    FACULTY_DESCRIPTION,
    FACULTY_NAME,
    LEGACY_CODES,
    LEGACY_FACULTY_NAME,
    LEGACY_PROGRAM_NAME,
    PREREQUISITES,
    PROGRAM,
    PROGRAM_NAME,
)
from scripts.demo_faculties import EXTRA_FACULTIES, FACULTY_DOCUMENTS
from scripts.demo_documents import DEMO_DOCUMENTS, write_pdf


ADMIN_EMAIL = "admin@unimate.edu"
ADMIN_PASSWORD = "Admin123!"

STUDENT_EMAIL = "student@unimate.edu"
STUDENT_PASSWORD = "Student123!"

# Profesorët kyçen me emailin e tyre nga lista PROFESSORS më poshtë.
PROFESSOR_PASSWORD = "Professor123!"

PROFESSORS = [
    {
        "first_name": "Arben",
        "last_name": "Hoxha",
        "title": "Prof. Dr.",
        "email": "arben.hoxha@unimate.edu",
        "office": "B-210",
        "consultation_hours": "E martë 12:00-14:00, zyra B-210",
    },
    {
        "first_name": "Elira",
        "last_name": "Berisha",
        "title": "Doc. Dr.",
        "email": "elira.berisha@unimate.edu",
        "office": "A-115",
        "consultation_hours": "E enjte 10:00-12:00, zyra A-115",
    },
]

# Kodi i lëndës -> mbiemri i profesorit koordinator. Profesorët e demos
# janë fiktivë; lëndët e tjera i cakton administratori.
COURSE_PROFESSORS = {
    "SKI-301": "Hoxha",
    "SKI-302": "Berisha",
    "SKI-303": "Berisha",
    "SKI-304": "Hoxha",
    "SKI-305": "Hoxha",
    "SKI-306": "Berisha",
    "SKI-505": "Berisha",
}

SYLLABI = {
    "SKI-305": """Java 1-2: Analiza e kompleksitetit, notacioni O i madh.
Java 3-5: Lista, stack, queue, listat e lidhura.
Java 6-8: Pemët binare, pemët e kërkimit, balancimi AVL.
Java 9-11: Hash tabelat dhe trajtimi i përplasjeve.
Java 12-14: Algoritmet e renditjes dhe kërkimit, programimi dinamik.""",
    "SKI-303": """Java 1-3: Modeli relacional, algjebra relacionale.
Java 4-7: SQL — SELECT, JOIN, agregime, nënpyetje.
Java 8-10: Normalizimi, format normale 1NF deri 3NF dhe BCNF.
Java 11-14: Transaksionet, ACID, indekset dhe optimizimi.""",
    "SKI-301": """Java 1-3: Klasat, objektet, enkapsulimi.
Java 4-7: Trashëgimia, polimorfizmi, klasat abstrakte.
Java 8-11: Interfaces, kompozimi mbi trashëgiminë.
Java 12-14: Modelet e dizajnit — Factory, Strategy, Observer.""",
}

# Afatet vendosen relativisht ndaj sotmes.
DEADLINES = [
    ("Regjistrimi i lëndëve për semestrin veror", "REGISTRATION", 14,
     "Regjistrimi bëhet online në portalin e studentit."),
    ("Pagesa e këstit të dytë", "PAYMENT", 30,
     "Kësti paguhet në bankë ose online, me numrin e studentit si referencë."),
    ("Aplikimi për temë diplome", "GRADUATION", 45,
     "Kërkohen së paku 150 ECTS të përfunduara."),
    ("Java e hapur e fakultetit", "EVENT", 7,
     "Prezantime nga industria dhe laboratorët kërkimorë."),
]

NOTIFICATIONS = [
    ("Orari i ri i konsultimeve", "INFO",
     "Konsultimet e profesorëve janë përditësuar për këtë semestër."),
    ("Afati i regjistrimit po mbyllet", "WARNING",
     "Regjistrimi i lëndëve mbyllet për dy javë. Mos e lini në fund."),
]

# Orari javor i semestrit 3, pa përplasje për studentin demo.
SCHEDULES = [
    ("SKI-305", "Monday", time(9, 0), time(10, 30), "A-201"),
    ("SKI-305", "Wednesday", time(9, 0), time(10, 30), "A-201"),
    ("SKI-303", "Monday", time(11, 0), time(12, 30), "B-104"),
    ("SKI-303", "Thursday", time(14, 0), time(15, 30), "Lab-2"),
    ("SKI-301", "Tuesday", time(10, 0), time(11, 30), "A-105"),
    ("SKI-301", "Friday", time(12, 0), time(13, 30), "Lab-1"),
    ("SKI-302", "Tuesday", time(12, 0), time(13, 30), "A-210"),
    ("SKI-302", "Wednesday", time(11, 0), time(12, 30), "A-210"),
    ("SKI-304", "Wednesday", time(14, 0), time(15, 30), "Lab-3"),
    ("SKI-304", "Friday", time(9, 0), time(10, 30), "Lab-3"),
    ("SKI-306", "Tuesday", time(14, 0), time(15, 30), "Lab-2"),
    ("SKI-306", "Friday", time(14, 0), time(15, 30), "Lab-2"),
]

# Provimet vendosen relativisht ndaj datës së sotme, që të mbeten
# gjithmonë "të ardhshme" pavarësisht kur ekzekutohet seed-i.
EXAMS = [
    ("SKI-305", "FINAL", 21, time(10, 0), "A-201"),
    ("SKI-303", "MIDTERM", 10, time(9, 0), "B-104"),
    ("SKI-301", "FINAL", 28, time(13, 0), "A-105"),
    ("SKI-305", "MIDTERM", -35, time(10, 0), "A-201"),
    ("SKI-302", "MIDTERM", 17, time(11, 0), "A-210"),
    ("SKI-304", "MIDTERM", 24, time(9, 0), "Lab-3"),
    ("SKI-306", "FINAL", 35, time(12, 0), "Lab-2"),
]

# Studentja demo është në vitin e dytë, semestri 3.
DEMO_SEMESTER = 3
ENROLLED_COURSE_CODES = [
    code for code, _, _, semester, _ in CURRICULUM if semester == DEMO_SEMESTER
]

# Periudhat akademike: (viti akademik, periudha, fillimi, mbarimi).
PERIODS = [
    ("2025/2026", WINTER, date(2025, 10, 1), date(2026, 1, 31)),
    ("2025/2026", SUMMER, date(2026, 2, 23), date(2026, 6, 30)),
    ("2026/2027", WINTER, date(2026, 10, 1), date(2027, 1, 31)),
    ("2026/2027", SUMMER, date(2027, 2, 22), date(2027, 6, 30)),
]
CURRENT_PERIOD = ("2026/2027", WINTER)

# Kolegët e studentit demo. Fjalëkalimi është i njëjtë për të gjithë
# sepse asnjëri nuk përdoret për t'u kyçur gjatë demos.
COHORT_PASSWORD = "Student123!"

COHORT_NAMES = [
    ("Bleron", "Hoxha"),
    ("Endrit", "Gashi"),
    ("Erza", "Berisha"),
    ("Fatlum", "Rexhepi"),
    ("Gentiana", "Morina"),
    ("Ilir", "Shala"),
    ("Jeta", "Kelmendi"),
    ("Leart", "Bytyqi"),
    ("Liridona", "Zeqiri"),
    ("Mergim", "Ahmeti"),
    ("Rina", "Salihu"),
    ("Valon", "Sylejmani"),
    ("Vjosa", "Demiri"),
    ("Ylber", "Maloku"),
]


def get_or_create_user(
    db: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRole,
) -> User:
    user = db.scalar(select(User).where(User.email == email))

    if user:
        return user

    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )

    db.add(user)
    db.flush()

    return user


def get_or_create_faculty(db: Session) -> Faculty:
    faculty = db.scalar(
        select(Faculty).where(Faculty.name == FACULTY_NAME)
    )

    if faculty:
        return faculty

    # Baza e demos së mëparshme riemërtohet në vend, që dokumentet dhe
    # profesorët e lidhur të mbeten.
    faculty = db.scalar(
        select(Faculty).where(Faculty.name == LEGACY_FACULTY_NAME)
    )

    if faculty:
        faculty.name = FACULTY_NAME
        faculty.description = FACULTY_DESCRIPTION
        db.flush()

        return faculty

    faculty = Faculty(
        name=FACULTY_NAME,
        description=FACULTY_DESCRIPTION,
    )

    db.add(faculty)
    db.flush()

    return faculty


def seed_professors(
    db: Session,
    faculty: Faculty,
) -> dict[str, Professor]:
    """Profesorët, secili me llogarinë e vet për t'u kyçur.

    Pa `Professor.user_id` të mbushur, roli PROFESSOR do të ekzistonte
    vetëm në enum: askush nuk do të mund të kyçej si profesor dhe
    tools 'get_my_' nuk do të gjenin asnjë lëndë.
    """

    professors: dict[str, Professor] = {}

    for data in PROFESSORS:
        professor = db.scalar(
            select(Professor).where(
                Professor.last_name == data["last_name"],
                Professor.first_name == data["first_name"],
            )
        )

        if professor is None:
            professor = Professor(faculty_id=faculty.id, **data)
            db.add(professor)
            db.flush()

        if professor.user_id is None:
            account = get_or_create_user(
                db,
                email=data["email"],
                password=PROFESSOR_PASSWORD,
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=UserRole.PROFESSOR,
            )

            professor.user_id = account.id
            db.flush()

        if professor.faculty_id is None:
            professor.faculty_id = faculty.id

        professors[professor.last_name] = professor

    return professors


def seed_prerequisites(db: Session, courses: dict[str, Course]) -> int:
    created = 0

    for code, required_codes in PREREQUISITES.items():
        course = courses.get(code)

        if course is None:
            continue

        for required_code in required_codes:
            required = courses.get(required_code)

            if required is None:
                continue

            exists = db.scalar(
                select(CoursePrerequisite).where(
                    CoursePrerequisite.course_id == course.id,
                    CoursePrerequisite.prerequisite_id == required.id,
                )
            )

            if exists:
                continue

            db.add(
                CoursePrerequisite(
                    course_id=course.id,
                    prerequisite_id=required.id,
                )
            )

            created += 1

    return created


def seed_deadlines(db: Session, program: Program) -> int:
    today = datetime.now().replace(
        hour=23, minute=59, second=0, microsecond=0
    )

    created = 0

    for title, deadline_type, day_offset, description in DEADLINES:
        due_date = today + timedelta(days=day_offset)

        exists = db.scalar(
            select(Deadline).where(Deadline.title == title)
        )

        # Datat e demos janë relative ndaj ditës së nisjes. Pa këtë
        # rifreskim, një bazë e seed-uar javë më parë do të tregonte
        # afate që kanë kaluar tashmë.
        if exists:
            exists.due_date = due_date
            continue

        db.add(
            Deadline(
                title=title,
                description=description,
                deadline_type=deadline_type,
                due_date=due_date,
                program_id=(
                    program.id if deadline_type == "REGISTRATION" else None
                ),
            )
        )

        created += 1

    return created


def seed_notifications(db: Session, admin: User) -> int:
    created = 0

    for title, severity, body in NOTIFICATIONS:
        exists = db.scalar(
            select(Notification).where(Notification.title == title)
        )

        if exists:
            continue

        db.add(
            Notification(
                title=title,
                body=body,
                severity=severity,
                created_by=admin.id,
            )
        )

        created += 1

    return created


def get_or_create_program(db: Session, faculty: Faculty) -> Program:
    program = db.scalar(
        select(Program).where(Program.name == PROGRAM_NAME)
    )

    if program:
        # Programet e krijuara para se programi të lidhej me fakultetin
        # kanë mbetur pa të; pa fakultet, studentët e tyre nuk shohin
        # dokumentet e fakultetit te kërkimi.
        if program.faculty_id is None:
            program.faculty_id = faculty.id

        # Fushat bosh (p.sh. programi i krijuar nga admini) plotësohen;
        # ato që admini i ka shkruar nuk preken.
        for field in ("description", "graduation_requirements"):
            if not getattr(program, field):
                setattr(program, field, PROGRAM[field])

        return program

    legacy = db.scalar(
        select(Program).where(Program.name == LEGACY_PROGRAM_NAME)
    )

    if legacy:
        legacy.name = PROGRAM_NAME
        legacy.faculty_id = faculty.id

        for field, value in PROGRAM.items():
            setattr(legacy, field, value)

        db.flush()

        return legacy

    program = Program(name=PROGRAM_NAME, faculty_id=faculty.id, **PROGRAM)

    db.add(program)
    db.flush()

    return program


def merge_legacy_program(db: Session, program: Program) -> bool:
    """Bashkon programin e vjetër "Shkenca Kompjuterike" te programi i ri.

    Ndodh kur admini e ka krijuar vetë programin e ri: studentët, lëndët,
    afatet dhe njoftimet e të vjetrit kalojnë te i riu, dhe i vjetri
    fshihet bosh.
    """

    legacy = db.scalar(
        select(Program).where(
            Program.name == LEGACY_PROGRAM_NAME,
            Program.id != program.id,
        )
    )

    if legacy is None:
        return False

    for model in (StudentProfile, Course, Deadline, Notification):
        for row in db.scalars(
            select(model).where(model.program_id == legacy.id)
        ).all():
            row.program_id = program.id

    db.flush()
    db.expire(legacy)
    db.delete(legacy)
    db.flush()

    return True


def migrate_legacy_curriculum(db: Session, program: Program) -> int:
    """Kalon një bazë me lëndët CSxxx te kurrikula SKI-xxx, një herë.

    Lëndët riemërtohen në vend: regjistrimet, grupet, materialet dhe
    bisedat ekzistuese mbeten të lidhura. Parakushtet e vjetra fshihen
    (rikrijohen nga kurrikula), dhe regjistrimet e studentëve në lëndë
    të një semestri tjetër nga ai i tyre hiqen, sepse lëndët kanë
    ndryshuar semestër.
    """

    legacy = db.scalars(
        select(Course).where(Course.code.in_(LEGACY_CODES))
    ).all()

    if not legacy:
        return 0

    catalog = {entry[0]: entry for entry in CURRICULUM}

    for course in legacy:
        code, name, ects, semester, description = catalog[
            LEGACY_CODES[course.code]
        ]

        if db.scalar(select(Course.id).where(Course.code == code)):
            continue

        # Titujt e materialeve javore fillojnë me kodin e lëndës.
        for document in db.scalars(
            select(Document).where(
                Document.course_id == course.id,
                Document.title.startswith(f"{course.code} · "),
            )
        ).all():
            document.title = code + document.title[len(course.code):]

        course.code = code
        course.name = name
        course.ects = ects
        course.semester = semester
        course.description = description
        course.program_id = program.id
        course.syllabus = None

    db.flush()

    program_courses = select(Course.id).where(Course.program_id == program.id)

    db.execute(
        delete(CoursePrerequisite).where(
            CoursePrerequisite.course_id.in_(program_courses)
        )
    )

    db.flush()

    return len(legacy)


def sync_semester_enrollments(db: Session, program: Program) -> int:
    """Çdo student i programit ndjek lëndët e semestrit të tij.

    Thirret vetëm pas kalimit te kurrikula e re, njësoj si regjistrimi
    automatik i onboarding-ut; më vonë regjistrimet i menaxhon admini.
    Lëndët e programit nga semestra të tjerë hiqen, sepse me kurrikulën
    e re kanë ndryshuar semestër.
    """

    created = 0

    profiles = db.scalars(
        select(StudentProfile).where(StudentProfile.program_id == program.id)
    ).all()

    for profile in profiles:
        enrolled = set()

        for enrollment in db.scalars(
            select(Enrollment).where(
                Enrollment.student_profile_id == profile.id
            )
        ).all():
            course = db.get(Course, enrollment.course_id)

            # Lëndët e përfunduara janë historik: mbeten.
            if (
                enrollment.status == "ACTIVE"
                and course.program_id == program.id
                and course.semester != profile.semester
            ):
                db.delete(enrollment)
            else:
                enrolled.add(course.id)

        db.flush()

        courses = db.scalars(
            select(Course).where(
                Course.program_id == program.id,
                Course.semester == profile.semester,
            )
        ).all()

        for course in courses:
            if course.id in enrolled:
                continue

            group = least_filled_group(course.id, db)

            db.add(
                Enrollment(
                    student_profile_id=profile.id,
                    course_id=course.id,
                    group_id=group.id if group else None,
                    status="ACTIVE",
                )
            )
            db.flush()
            created += 1

    return created


def seed_courses(
    db: Session,
    program: Program,
    professors: dict[str, Professor],
) -> dict[str, Course]:
    courses: dict[str, Course] = {}

    for code, name, ects, semester, description in CURRICULUM:
        course = db.scalar(select(Course).where(Course.code == code))

        if course is None:
            course = Course(
                code=code,
                name=name,
                ects=ects,
                semester=semester,
                description=description,
                program_id=program.id,
            )
            db.add(course)
            db.flush()

        # Emri dhe semestri ndjekin kurrikulën; ECTS-të jo, sepse janë
        # demonstrative dhe administratori mund t'i ketë ndryshuar.
        course.name = name
        course.semester = semester

        # Syllabus-i dhe profesori mbushen edhe për lëndë ekzistuese,
        # që seed-i i vjetër të pasurohet pa u rikrijuar baza.
        if not course.syllabus and course.code in SYLLABI:
            course.syllabus = SYLLABI[course.code]

        if course.professor_id is None:
            last_name = COURSE_PROFESSORS.get(course.code)
            professor = professors.get(last_name) if last_name else None

            if professor is not None:
                course.professor_id = professor.id

        courses[course.code] = course

    db.flush()

    return courses


def seed_periods(db: Session) -> int:
    created = 0

    for academic_year, term, start, end in PERIODS:
        period = db.scalar(
            select(AcademicPeriod).where(
                AcademicPeriod.academic_year == academic_year,
                AcademicPeriod.term == term,
            )
        )

        if period is None:
            db.add(
                AcademicPeriod(
                    academic_year=academic_year,
                    term=term,
                    start_date=start,
                    end_date=end,
                    is_current=False,
                )
            )
            created += 1

    db.flush()

    # Periudhën aktuale e zgjedh administratori; seed-i e cakton vetëm
    # kur nuk ka asnjë.
    has_current = db.scalar(
        select(AcademicPeriod.id).where(AcademicPeriod.is_current.is_(True))
    )

    if has_current is None:
        academic_year, term = CURRENT_PERIOD
        current = db.scalar(
            select(AcademicPeriod).where(
                AcademicPeriod.academic_year == academic_year,
                AcademicPeriod.term == term,
            )
        )
        current.is_current = True
        db.flush()

    return created


# Viti akademik kur studentët e demos ndoqën vitin e parë.
HISTORY_ACADEMIC_YEAR = "2025/2026"


def seed_completed_history(db: Session, program: Program) -> int:
    """Lëndët e vitit të parë, të përfunduara në 2025/2026.

    Studentët e demos janë në vitin e dytë: semestrat 1 dhe 2 i kanë
    kaluar, semestri 1 në periudhën dimërore dhe 2 në verore. Kështu
    progresi tregon 60 ECTS dhe regjistrimet e vjetra kanë periudhën e
    tyre, jo atë aktuale.
    """

    periods = {
        period.term: period
        for period in db.scalars(
            select(AcademicPeriod).where(
                AcademicPeriod.academic_year == HISTORY_ACADEMIC_YEAR
            )
        ).all()
    }

    courses = db.scalars(
        select(Course).where(
            Course.program_id == program.id,
            Course.semester < DEMO_SEMESTER,
        )
    ).all()

    profiles = db.scalars(
        select(StudentProfile)
        .join(User, User.id == StudentProfile.user_id)
        .where(
            StudentProfile.program_id == program.id,
            StudentProfile.semester == DEMO_SEMESTER,
            or_(
                User.email == STUDENT_EMAIL,
                User.email.like("%@student.unimate.edu"),
            ),
        )
    ).all()

    created = 0

    for profile in profiles:
        enrolled = set(
            db.scalars(
                select(Enrollment.course_id).where(
                    Enrollment.student_profile_id == profile.id
                )
            ).all()
        )

        for course in courses:
            if course.id in enrolled:
                continue

            period = periods.get(term_for_semester(course.semester))

            db.add(
                Enrollment(
                    student_profile_id=profile.id,
                    course_id=course.id,
                    period_id=period.id if period else None,
                    status="COMPLETED",
                )
            )
            created += 1

    db.flush()

    return created


def assign_enrollment_periods(db: Session) -> int:
    """Regjistrimet pa periudhë marrin atë të semestrit të lëndës."""

    enrollments = db.scalars(
        select(Enrollment).where(Enrollment.period_id.is_(None))
    ).all()

    for enrollment in enrollments:
        period = period_for_semester(enrollment.course.semester, db)
        enrollment.period_id = period.id if period else None

    db.flush()

    return len(enrollments)


def seed_schedules(db: Session, courses: dict[str, Course]) -> int:
    created = 0

    for code, day, start, end, room in SCHEDULES:
        course = courses[code]

        exists = db.scalar(
            select(Schedule).where(
                Schedule.course_id == course.id,
                Schedule.day_of_week == day,
                Schedule.start_time == start,
            )
        )

        if exists:
            continue

        db.add(
            Schedule(
                course_id=course.id,
                day_of_week=day,
                start_time=start,
                end_time=end,
                room=room,
            )
        )

        created += 1

    return created


def seed_exams(db: Session, courses: dict[str, Course]) -> int:
    today = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    created = 0

    for code, exam_type, day_offset, exam_time, room in EXAMS:
        course = courses[code]

        exam_date = today + timedelta(days=day_offset)
        exam_date = exam_date.replace(
            hour=exam_time.hour,
            minute=exam_time.minute,
        )

        exists = db.scalar(
            select(Exam).where(
                Exam.course_id == course.id,
                Exam.exam_type == exam_type,
            )
        )

        # Si te afatet: provimet demo mbeten gjithmonë në të ardhmen.
        if exists:
            exists.exam_date = exam_date
            continue

        db.add(
            Exam(
                course_id=course.id,
                exam_type=exam_type,
                exam_date=exam_date,
                room=room,
            )
        )

        created += 1

    return created


def seed_student_profile(
    db: Session,
    student: User,
    program: Program,
) -> StudentProfile:
    profile = db.scalar(
        select(StudentProfile).where(
            StudentProfile.user_id == student.id
        )
    )

    if profile:
        return profile

    profile = StudentProfile(
        user_id=student.id,
        student_number="2024-CS-001",
        program_id=program.id,
        study_year=2,
        semester=DEMO_SEMESTER,
        preferred_language="sq",
    )

    db.add(profile)
    db.flush()

    return profile


def seed_cohort(
    db: Session,
    program: Program,
    courses: dict[str, Course],
) -> int:
    """Kolegët e studentit demo.

    Nuk përdoren për t'u kyçur; ekzistojnë që numrat e panelit të
    administratorit dhe testet e izolimit të kenë të dhëna reale të
    huaja përballë.
    """

    created = 0

    for index, (first_name, last_name) in enumerate(
        COHORT_NAMES,
        start=2,
    ):
        email = (
            f"{first_name.lower()}.{last_name.lower()}"
            "@student.unimate.edu"
        )

        user = get_or_create_user(
            db,
            email=email,
            password=COHORT_PASSWORD,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.STUDENT,
        )

        profile = db.scalar(
            select(StudentProfile).where(
                StudentProfile.user_id == user.id
            )
        )

        if profile is None:
            profile = StudentProfile(
                user_id=user.id,
                student_number=f"2024-CS-{index:03d}",
                program_id=program.id,
                study_year=2,
                semester=DEMO_SEMESTER,
                preferred_language="sq",
            )

            db.add(profile)
            db.flush()

            created += 1

        # Lëndët e semestrit janë të detyrueshme: e gjithë kohorta i
        # ndjek të gjashta.
        for code in ENROLLED_COURSE_CODES:
            course = courses[code]

            exists = db.scalar(
                select(Enrollment).where(
                    Enrollment.student_profile_id == profile.id,
                    Enrollment.course_id == course.id,
                )
            )

            if exists:
                continue

            db.add(
                Enrollment(
                    student_profile_id=profile.id,
                    course_id=course.id,
                    status="ACTIVE",
                )
            )

    return created


def course_from_tuple(program: Program, data: tuple) -> dict:
    code, name, ects, semester, description = data

    return {
        "code": code,
        "name": name,
        "ects": ects,
        "semester": semester,
        "description": description,
        "program_id": program.id,
    }


def get_or_create_course(db: Session, fields: dict) -> Course:
    course = db.scalar(select(Course).where(Course.code == fields["code"]))

    if course is None:
        course = Course(**fields)
        db.add(course)
        db.flush()

    return course


def seed_extra_faculties(db: Session, cs_program: Program) -> dict:
    """Tre fakultetet e tjera të demos, me programet dhe lëndët e tyre.

    Kthen numrin e fakulteteve, programeve dhe lëndëve të demos.
    """

    for spec in EXTRA_FACULTIES:
        program = db.scalar(
            select(Program).where(Program.name == spec["program"]["name"])
        )

        # Fakulteti krijohet vetëm bashkë me programin, në bazë të re. Kur
        # programi ekziston, struktura i përket administratorit: një
        # fakultet që ai e ka fshirë nuk rikrijohet.
        if program is None:
            faculty = db.scalar(
                select(Faculty).where(Faculty.name == spec["faculty"])
            )

            if faculty is None:
                faculty = Faculty(
                    name=spec["faculty"], description=spec["description"]
                )
                db.add(faculty)
                db.flush()

            program = Program(faculty_id=faculty.id, **spec["program"])
            db.add(program)
            db.flush()

        faculty = db.scalar(
            select(Faculty).where(Faculty.name == spec["faculty"])
        )

        # Plotësohet vetëm ajo që mungon: programi pa fakultet lidhet me
        # fakultetin me të njëjtin emër, dhe përshkrimi bosh mbushet.
        if faculty is not None:
            if program.faculty_id is None:
                program.faculty_id = faculty.id

            if not faculty.description:
                faculty.description = spec["description"]

        data = spec["professor"]
        professor = db.scalar(
            select(Professor).where(Professor.email == data["email"])
        )

        if professor is None:
            account = get_or_create_user(
                db,
                email=data["email"],
                password=PROFESSOR_PASSWORD,
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=UserRole.PROFESSOR,
            )
            professor = Professor(
                faculty_id=program.faculty_id, user_id=account.id, **data
            )
            db.add(professor)
            db.flush()

        if professor.faculty_id is None:
            professor.faculty_id = program.faculty_id

        for course_data in spec["courses"]:
            course = get_or_create_course(
                db, course_from_tuple(program, course_data)
            )

            if course.code in spec["teaches"] and course.professor_id is None:
                course.professor_id = professor.id

    db.flush()

    return {
        "faculties": db.scalar(select(func.count()).select_from(Faculty)),
        "programs": db.scalar(select(func.count()).select_from(Program)),
        "courses": db.scalar(select(func.count()).select_from(Course)),
    }


def document_scope(
    db: Session, spec: dict
) -> tuple[int | None, int | None] | None:
    """Fakulteti dhe lënda e një dokumenti demo, nga emrat te specifikimi.

    None kur lënda ose fakulteti nuk ekziston më (e ka fshirë admini):
    atëherë dokumenti mbetet me fushëveprimin që ka.
    """

    if spec.get("course"):
        course = db.scalar(select(Course).where(Course.code == spec["course"]))

        if course is None:
            return None

        program = db.get(Program, course.program_id)

        return program.faculty_id, course.id

    if spec.get("faculty"):
        faculty = db.scalar(
            select(Faculty).where(Faculty.name == spec["faculty"])
        )

        return (faculty.id, None) if faculty else None

    return None, None


# Lëndët me më shumë se një grup: kodi -> [(grupi, mbiemri i profesorit)].
# Lëndët e tjera me profesor marrin vetëm "Grupi A" me koordinatorin.
EXTRA_GROUPS = {
    "SKI-305": [("Grupi A", "Hoxha"), ("Grupi B", "Berisha")],
}

# Ushtrimet e veçanta të çdo grupi të SKI-305, të enjten, në orë që nuk
# përplasen me ligjëratat e përbashkëta të studentit demo.
GROUP_SCHEDULES = {
    ("SKI-305", "Grupi A"): ("Thursday", time(11, 0), time(12, 30), "Lab-1"),
    ("SKI-305", "Grupi B"): ("Thursday", time(16, 0), time(17, 30), "Lab-1"),
}


def seed_groups(
    db: Session,
    professors: dict[str, Professor],
    demo_profile: StudentProfile,
) -> int:
    """Grupet e lëndëve dhe caktimi i studentëve në to.

    Studentët pa grup shpërndahen me radhë mes grupeve të lëndës, që
    kohorta e demos të ketë studentë te secili profesor.
    """

    created = 0

    for course in db.scalars(select(Course).order_by(Course.code)).all():
        wanted = EXTRA_GROUPS.get(course.code)

        if wanted is None:
            if course.professor_id is None:
                continue

            wanted = [("Grupi A", None)]

        for name, last_name in wanted:
            group = db.scalar(
                select(CourseGroup).where(
                    CourseGroup.course_id == course.id,
                    CourseGroup.name == name,
                )
            )

            if group is None:
                professor = professors.get(last_name) if last_name else None
                group = CourseGroup(
                    course_id=course.id,
                    name=name,
                    professor_id=(
                        professor.id if professor else course.professor_id
                    ),
                )
                db.add(group)
                db.flush()
                created += 1

            slot = GROUP_SCHEDULES.get((course.code, name))

            if slot is not None:
                day, start, end, room = slot
                exists = db.scalar(
                    select(Schedule).where(
                        Schedule.group_id == group.id,
                        Schedule.day_of_week == day,
                    )
                )

                if exists is None:
                    db.add(
                        Schedule(
                            course_id=course.id,
                            group_id=group.id,
                            day_of_week=day,
                            start_time=start,
                            end_time=end,
                            room=room,
                        )
                    )

        groups = db.scalars(
            select(CourseGroup)
            .where(CourseGroup.course_id == course.id)
            .order_by(CourseGroup.name)
        ).all()

        if not groups:
            continue

        unassigned = db.scalars(
            select(Enrollment)
            .where(
                Enrollment.course_id == course.id,
                Enrollment.group_id.is_(None),
            )
            .order_by(Enrollment.id)
        ).all()

        for index, enrollment in enumerate(unassigned):
            enrollment.group_id = groups[index % len(groups)].id

        # Një bazë e migruar i ka të gjithë studentët te "Grupi A", dhe
        # grupi i ri do të mbetej bosh. Rishpërndahen një herë, kur një
        # grup është bosh; studentja demo mbetet te grupi i parë.
        if course.code in EXTRA_GROUPS:
            counts = [
                len(
                    db.scalars(
                        select(Enrollment).where(Enrollment.group_id == group.id)
                    ).all()
                )
                for group in groups
            ]

            if 0 in counts:
                cohort = db.scalars(
                    select(Enrollment)
                    .where(Enrollment.course_id == course.id)
                    .order_by(Enrollment.id)
                ).all()

                others = [
                    enrollment
                    for enrollment in cohort
                    if enrollment.student_profile_id != demo_profile.id
                ]

                for enrollment in cohort:
                    if enrollment.student_profile_id == demo_profile.id:
                        enrollment.group_id = groups[0].id

                for index, enrollment in enumerate(others):
                    enrollment.group_id = groups[(index + 1) % len(groups)].id

    db.flush()

    return created


def spec_fingerprint(spec: dict) -> str:
    content = json.dumps(spec, ensure_ascii=False, sort_keys=True)

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def seed_documents(db: Session, admin: User) -> list[Document]:
    """Krijon PDF-të demo dhe rreshtat përkatës në bazë.

    Skedari shkruhet vetëm nëse mungon, dhe rreshti krijohet vetëm
    nëse nuk ekziston — që seed-i të mbetet idempotent. Indeksimi
    bëhet veçmas te `index_documents`.
    """

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    documents: list[Document] = []

    for spec in DEMO_DOCUMENTS + FACULTY_DOCUMENTS:
        file_path = upload_dir / spec["file_name"]

        # Gjurma e specifikimit ruhet pranë PDF-së: kur teksti i demos
        # ndryshon (p.sh. kurrikula e re), PDF-ja rishkruhet dhe
        # dokumenti ri-indeksohet.
        fingerprint = spec_fingerprint(spec)
        marker = file_path.with_name(file_path.name + ".spec")
        changed = (
            not marker.exists()
            or marker.read_text(encoding="utf-8") != fingerprint
        )

        if changed or not file_path.exists():
            write_pdf(spec, file_path)

        document = db.scalar(
            select(Document).where(
                Document.file_name == spec["file_name"]
            )
        )

        if document is None:
            document = Document(
                title=spec["title"],
                description=spec["description"],
                file_name=spec["file_name"],
                file_path=file_path.as_posix(),
                document_type=spec["document_type"],
                academic_year=spec["academic_year"],
                uploaded_by=admin.id,
                status=DocumentStatus.PENDING,
            )

            db.add(document)
            db.flush()

        elif changed:
            document.title = spec["title"]
            document.description = spec["description"]
            document.academic_year = spec["academic_year"]
            document.status = DocumentStatus.PENDING

        marker.write_text(fingerprint, encoding="utf-8")

        # Rifreskohet në çdo nisje, që edhe dokumentet e seed-uara para
        # se të ekzistonte fusha ta marrin vendin e tyre.
        scope = document_scope(db, spec)

        if scope is not None:
            document.faculty_id, document.course_id = scope

        documents.append(document)

    return documents


def index_documents(documents: list[Document]) -> tuple[int, int]:
    """Kalon dokumentet demo nëpër pipeline-in RAG.

    Kthen (të indeksuara, të dështuara). Dështimi nuk e ndal seed-in:
    pjesa tjetër e të dhënave demo është e vlefshme edhe pa Qdrant,
    dhe administratori mund të shtypë "Ri-indekso" më vonë.
    """

    indexed = 0
    failed = 0

    for document in documents:
        if document.status == DocumentStatus.INDEXED:
            continue

        ingest_document_in_background(document.id)

        db = SessionLocal()

        try:
            refreshed = db.get(Document, document.id)

            if (
                refreshed is not None
                and refreshed.status == DocumentStatus.INDEXED
            ):
                indexed += 1
            else:
                failed += 1

        finally:
            db.close()

    return indexed, failed


def seed_enrollments(
    db: Session,
    profile: StudentProfile,
    courses: dict[str, Course],
) -> int:
    created = 0

    for code in ENROLLED_COURSE_CODES:
        course = courses[code]

        exists = db.scalar(
            select(Enrollment).where(
                Enrollment.student_profile_id == profile.id,
                Enrollment.course_id == course.id,
            )
        )

        if exists:
            continue

        db.add(
            Enrollment(
                student_profile_id=profile.id,
                course_id=course.id,
                status="ACTIVE",
            )
        )

        created += 1

    return created


def main() -> None:
    db = SessionLocal()

    try:
        admin = get_or_create_user(
            db,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            first_name="Admin",
            last_name="UniMate",
            role=UserRole.ADMIN,
        )

        student = get_or_create_user(
            db,
            email=STUDENT_EMAIL,
            password=STUDENT_PASSWORD,
            first_name="Arta",
            last_name="Krasniqi",
            role=UserRole.STUDENT,
        )

        faculty = get_or_create_faculty(db)
        program = get_or_create_program(db, faculty)
        professors = seed_professors(db, faculty)
        merged = merge_legacy_program(db, program)
        migrated = migrate_legacy_curriculum(db, program)
        courses = seed_courses(db, program, professors)
        catalog = seed_extra_faculties(db, program)
        periods_created = seed_periods(db)

        schedules_created = seed_schedules(db, courses)
        exams_created = seed_exams(db, courses)
        prerequisites_created = seed_prerequisites(db, courses)
        deadlines_created = seed_deadlines(db, program)
        notifications_created = seed_notifications(db, admin)

        profile = seed_student_profile(db, student, program)
        enrollments_created = seed_enrollments(db, profile, courses)
        cohort_created = seed_cohort(db, program, courses)
        groups_created = seed_groups(db, professors, profile)
        synced = (
            sync_semester_enrollments(db, program)
            if migrated or merged
            else 0
        )
        history_created = seed_completed_history(db, program)
        periods_assigned = assign_enrollment_periods(db)

        documents = seed_documents(db, admin)

        db.commit()

        # Indeksimi vjen pas commit-it sepse hap sesionin e vet dhe
        # ka nevojë që dokumentet të ekzistojnë tashmë në bazë.
        document_ids = [document.id for document in documents]

        indexed, failed = index_documents(documents)

        print("Seed u përfundua.")
        print(f"  Admin:     {admin.email} / {ADMIN_PASSWORD}")
        print(f"  Student:   {student.email} / {STUDENT_PASSWORD}")

        for professor in professors.values():
            account = db.get(User, professor.user_id)

            if account is not None:
                print(
                    f"  Profesor:  {account.email} "
                    f"/ {PROFESSOR_PASSWORD}"
                )

        print(f"  Fakulteti: {faculty.name}")
        print(f"  Programi:  {program.name}")
        print(
            f"  Katalogu:  {catalog['faculties']} fakultete, "
            f"{catalog['programs']} programe, {catalog['courses']} lëndë"
        )
        print(f"  Profesorë: {len(professors)}")
        print(f"  Lëndë të riemërtuara (CS -> SKI): {migrated}")
        print(f"  Programi i vjetër u bashkua: {'po' if merged else 'jo'}")
        print(f"  Periudha të reja:        {periods_created}")
        print(f"  Regjistrime të semestrit: {synced}")
        print(f"  Regjistrime me periudhë: {periods_assigned}")
        print(f"  Lëndë të përfunduara (viti 1): {history_created}")
        print(f"  Orare të reja:        {schedules_created}")
        print(f"  Provime të reja:      {exams_created}")
        print(f"  Parakushte të reja:   {prerequisites_created}")
        print(f"  Afate të reja:        {deadlines_created}")
        print(f"  Njoftime të reja:     {notifications_created}")
        print(f"  Regjistrime të reja:  {enrollments_created}")
        print(f"  Studentë të kohortës: {cohort_created}")
        print(f"  Grupe të reja:        {groups_created}")
        print(f"  Dokumente demo:       {len(document_ids)}")
        print(f"  Të indeksuara tani:   {indexed}")

        if failed:
            print(
                f"  KUJDES: {failed} dokumente nuk u indeksuan. "
                "Kontrollo nëse Qdrant është duke punuar "
                f"({settings.qdrant_url}) dhe përdor "
                "'Ri-indekso' te paneli i administratorit."
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
