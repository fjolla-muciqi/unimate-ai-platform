"""Mbush bazën me të dhëna demo.

Idempotent: mund të ekzekutohet disa herë pa krijuar dublikatë.

    python -m scripts.seed
"""

from datetime import datetime, time, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.rag.ingestion import ingest_document_in_background
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
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
from scripts.demo_faculties import (
    CS_EXTRA_COURSES,
    EXTRA_FACULTIES,
    FACULTY_DOCUMENTS,
)
from scripts.demo_documents import DEMO_DOCUMENTS, write_pdf


ADMIN_EMAIL = "admin@unimate.edu"
ADMIN_PASSWORD = "Admin123!"

STUDENT_EMAIL = "student@unimate.edu"
STUDENT_PASSWORD = "Student123!"

# Profesorët kyçen me emailin e tyre nga lista PROFESSORS më poshtë.
PROFESSOR_PASSWORD = "Professor123!"

PROGRAM_NAME = "Shkenca Kompjuterike"
FACULTY_NAME = "Fakulteti i Inxhinierisë Kompjuterike"

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

# Kodi i lëndës -> mbiemri i profesorit që e ligjëron.
COURSE_PROFESSORS = {
    "CS201": "Hoxha",
    "CS202": "Berisha",
    "CS203": "Hoxha",
    "CS301": "Berisha",
}

# Lënda -> parakushtet e saj.
PREREQUISITES = {
    "CS201": ["CS101", "CS102"],
    "CS202": ["CS101"],
    "CS203": ["CS101"],
    "CS301": ["CS201"],
}

SYLLABI = {
    "CS201": """Java 1-2: Analiza e kompleksitetit, notacioni O i madh.
Java 3-5: Lista, stack, queue, listat e lidhura.
Java 6-8: Pemët binare, pemët e kërkimit, balancimi AVL.
Java 9-11: Hash tabelat dhe trajtimi i përplasjeve.
Java 12-14: Algoritmet e renditjes dhe kërkimit, programimi dinamik.""",
    "CS202": """Java 1-3: Modeli relacional, algjebra relacionale.
Java 4-7: SQL — SELECT, JOIN, agregime, nënpyetje.
Java 8-10: Normalizimi, format normale 1NF deri 3NF dhe BCNF.
Java 11-14: Transaksionet, ACID, indekset dhe optimizimi.""",
    "CS203": """Java 1-3: Klasat, objektet, enkapsulimi.
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

COURSES = [
    {
        "code": "CS101",
        "name": "Hyrje në Programim",
        "ects": 6,
        "semester": 1,
        "description": (
            "Bazat e programimit në Python: tipet e të dhënave, "
            "kontrolli i rrjedhës, funksionet dhe strukturat bazë."
        ),
    },
    {
        "code": "CS102",
        "name": "Matematikë Diskrete",
        "ects": 6,
        "semester": 1,
        "description": (
            "Logjika, bashkësitë, relacionet, kombinatorika dhe "
            "hyrje në teorinë e grafeve."
        ),
    },
    {
        "code": "CS201",
        "name": "Algoritme dhe Struktura të Dhënash",
        "ects": 7,
        "semester": 3,
        "description": (
            "Kompleksiteti algoritmik, listat, pemët, hash tabelat, "
            "renditja dhe kërkimi."
        ),
    },
    {
        "code": "CS202",
        "name": "Bazat e të Dhënave",
        "ects": 6,
        "semester": 3,
        "description": (
            "Modelimi relacional, SQL, normalizimi dhe transaksionet."
        ),
    },
    {
        "code": "CS203",
        "name": "Programim i Orientuar në Objekte",
        "ects": 6,
        "semester": 3,
        "description": (
            "Klasat, trashëgimia, polimorfizmi dhe modelet e dizajnit."
        ),
    },
    {
        "code": "CS301",
        "name": "Inteligjenca Artificiale",
        "ects": 7,
        "semester": 5,
        "description": (
            "Kërkimi, arsyetimi, mësimi i makinës dhe modelet gjuhësore."
        ),
    },
]

SCHEDULES = [
    ("CS201", "Monday", time(9, 0), time(10, 30), "A-201"),
    ("CS201", "Wednesday", time(9, 0), time(10, 30), "A-201"),
    ("CS202", "Monday", time(11, 0), time(12, 30), "B-104"),
    ("CS202", "Thursday", time(14, 0), time(15, 30), "Lab-2"),
    ("CS203", "Tuesday", time(10, 0), time(11, 30), "A-105"),
    ("CS203", "Friday", time(12, 0), time(13, 30), "Lab-1"),
]

# Provimet vendosen relativisht ndaj datës së sotme, që të mbeten
# gjithmonë "të ardhshme" pavarësisht kur ekzekutohet seed-i.
EXAMS = [
    ("CS201", "FINAL", 21, time(10, 0), "A-201"),
    ("CS202", "MIDTERM", 10, time(9, 0), "B-104"),
    ("CS203", "FINAL", 28, time(13, 0), "A-105"),
    ("CS201", "MIDTERM", -35, time(10, 0), "A-201"),
]

ENROLLED_COURSE_CODES = ["CS201", "CS202", "CS203"]

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

    faculty = Faculty(
        name=FACULTY_NAME,
        description=(
            "Fakulteti që mbulon programet e shkencave kompjuterike "
            "dhe inxhinierisë softuerike."
        ),
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

        return program

    program = Program(
        name=PROGRAM_NAME,
        faculty_id=faculty.id,
        degree_level="BACHELOR",
        specialization="Inxhinieri Softuerike",
        total_ects=180,
        duration_years=3,
        description=(
            "Program trevjeçar bachelor në shkenca kompjuterike me "
            "fokus në inxhinieri softuerike dhe inteligjencë artificiale."
        ),
        graduation_requirements=(
            "Për diplomim kërkohen 180 ECTS, përfundimi i të gjitha "
            "lëndëve të detyrueshme, praktika profesionale prej 4 javësh "
            "dhe mbrojtja e temës së diplomës."
        ),
    )

    db.add(program)
    db.flush()

    return program


def seed_courses(
    db: Session,
    program: Program,
    professors: dict[str, Professor],
) -> dict[str, Course]:
    courses: dict[str, Course] = {}

    for data in COURSES:
        course = db.scalar(
            select(Course).where(Course.code == data["code"])
        )

        if course is None:
            course = Course(program_id=program.id, **data)
            db.add(course)
            db.flush()

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
        academic_year=2,
        semester=3,
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
                academic_year=2,
                semester=3,
                preferred_language="sq",
            )

            db.add(profile)
            db.flush()

            created += 1

        # Kohorta ndjek të njëjtat lëndë bazë, por jo të gjitha:
        # kështu "lëndët e mia" ndryshojnë vërtet nga student në
        # student.
        for code in ENROLLED_COURSE_CODES[: 2 + index % 2]:
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
    """Semestrat që i mungonin programit SHK dhe tre fakultete të tjera.

    Kthen numrin e fakulteteve, programeve dhe lëndëve të demos.
    """

    for data in CS_EXTRA_COURSES:
        get_or_create_course(db, course_from_tuple(cs_program, data))

    for spec in EXTRA_FACULTIES:
        faculty = db.scalar(
            select(Faculty).where(Faculty.name == spec["faculty"])
        )

        if faculty is None:
            faculty = Faculty(
                name=spec["faculty"], description=spec["description"]
            )
            db.add(faculty)
            db.flush()

        program = db.scalar(
            select(Program).where(Program.name == spec["program"]["name"])
        )

        if program is None:
            program = Program(faculty_id=faculty.id, **spec["program"])
            db.add(program)
            db.flush()

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
                faculty_id=faculty.id, user_id=account.id, **data
            )
            db.add(professor)
            db.flush()

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


def document_scope(db: Session, spec: dict) -> tuple[int | None, int | None]:
    """Fakulteti dhe lënda e një dokumenti demo, nga emrat te specifikimi."""

    if spec.get("course"):
        course = db.scalar(select(Course).where(Course.code == spec["course"]))
        program = db.get(Program, course.program_id)

        return program.faculty_id, course.id

    if spec.get("faculty"):
        faculty = db.scalar(
            select(Faculty).where(Faculty.name == spec["faculty"])
        )

        return faculty.id, None

    return None, None


# Lëndët me më shumë se një grup: kodi -> [(grupi, mbiemri i profesorit)].
# Lëndët e tjera me profesor marrin vetëm "Grupi A" me koordinatorin.
EXTRA_GROUPS = {
    "CS201": [("Grupi A", "Hoxha"), ("Grupi B", "Berisha")],
}

# Ushtrimet e veçanta të çdo grupi të CS201, të enjten, në orë që nuk
# përplasen me ligjëratat e përbashkëta të studentit demo.
GROUP_SCHEDULES = {
    ("CS201", "Grupi A"): ("Thursday", time(11, 0), time(12, 30), "Lab-1"),
    ("CS201", "Grupi B"): ("Thursday", time(16, 0), time(17, 30), "Lab-1"),
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

        if not file_path.exists():
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

        # Rifreskohet në çdo nisje, që edhe dokumentet e seed-uara para
        # se të ekzistonte fusha ta marrin vendin e tyre.
        document.faculty_id, document.course_id = document_scope(db, spec)

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
        courses = seed_courses(db, program, professors)
        catalog = seed_extra_faculties(db, program)

        schedules_created = seed_schedules(db, courses)
        exams_created = seed_exams(db, courses)
        prerequisites_created = seed_prerequisites(db, courses)
        deadlines_created = seed_deadlines(db, program)
        notifications_created = seed_notifications(db, admin)

        profile = seed_student_profile(db, student, program)
        enrollments_created = seed_enrollments(db, profile, courses)
        cohort_created = seed_cohort(db, program, courses)
        groups_created = seed_groups(db, professors, profile)

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
