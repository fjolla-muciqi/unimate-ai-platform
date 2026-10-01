"""Academic Data Agent.

Lexon të dhënat akademike të studentit nga PostgreSQL dhe i
kthen si tekst i lexueshëm. Këto funksione përdoren si tools
nga orchestrator-i, prandaj përgjigja duhet të jetë e qartë
edhe për modelin edhe për studentin.
"""

from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.periods import period_for_semester
from app.core.teaching import student_sees_schedule, teacher_of_enrollment
from app.models.course import Course
from app.models.course_group import CourseGroup
from app.models.deadline import Deadline
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.notification import Notification
from app.models.program import Program
from app.models.schedule import Schedule
from app.models.student_profile import StudentProfile


DAY_NAMES_SQ = {
    "Monday": "E hënë",
    "Tuesday": "E martë",
    "Wednesday": "E mërkurë",
    "Thursday": "E enjte",
    "Friday": "E premte",
    "Saturday": "E shtunë",
    "Sunday": "E diel",
}

DAY_ORDER = list(DAY_NAMES_SQ.keys())


def _format_time_range(start, end) -> str:
    return (
        f"{start.strftime('%H:%M')}-"
        f"{end.strftime('%H:%M')}"
    )


def answer_courses(profile: StudentProfile, db: Session) -> str:
    rows = db.execute(
        select(Course, Enrollment)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(
            Enrollment.student_profile_id == profile.id,
            Enrollment.status == "ACTIVE",
        )
        .order_by(Course.semester, Course.name)
    ).all()

    if not rows:
        return "Studenti nuk është i regjistruar në asnjë lëndë aktive."

    courses = [course for course, _ in rows]
    lines = []

    # Profesori i grupit të studentit, jo çdo profesor i lëndës: kur e
    # njëjta lëndë jepet nga disa, studenti pyet për të vetin.
    for course, enrollment in rows:
        teacher = teacher_of_enrollment(enrollment, course, db)
        group = db.get(CourseGroup, enrollment.group_id) if enrollment.group_id else None

        details = [f"semestri {course.semester}", f"{course.ects} ECTS"]

        if group is not None:
            details.append(group.name)

        if teacher is not None:
            details.append(f"profesori {teacher.full_name}")

        lines.append(f"- {course.name} ({course.code}), " + ", ".join(details))

    total_ects = sum(course.ects for course in courses)

    return (
        "Lëndët aktive të studentit:\n"
        + "\n".join(lines)
        + f"\nTotal: {len(courses)} lëndë, {total_ects} ECTS."
    )


def answer_schedule(
    profile: StudentProfile,
    db: Session,
    day_of_week: str | None = None,
) -> str:
    query = (
        select(Schedule)
        .join(Course, Course.id == Schedule.course_id)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(
            Enrollment.student_profile_id == profile.id,
            Enrollment.status == "ACTIVE",
            # Ligjëratat e përbashkëta dhe ato të grupit të studentit.
            student_sees_schedule(),
        )
    )

    if day_of_week:
        query = query.where(Schedule.day_of_week == day_of_week)

    schedules = db.scalars(query).all()

    if not schedules:
        if day_of_week:
            day = DAY_NAMES_SQ.get(day_of_week, day_of_week)
            return f"Studenti nuk ka ligjërata të planifikuara ditën {day}."

        return "Studenti nuk ka orar të regjistruar."

    schedules = sorted(
        schedules,
        key=lambda s: (
            DAY_ORDER.index(s.day_of_week)
            if s.day_of_week in DAY_ORDER
            else len(DAY_ORDER),
            s.start_time,
        ),
    )

    lines = []

    for schedule in schedules:
        day = DAY_NAMES_SQ.get(schedule.day_of_week, schedule.day_of_week)
        room = f", salla {schedule.room}" if schedule.room else ""

        lines.append(
            f"- {day}, "
            f"{_format_time_range(schedule.start_time, schedule.end_time)}: "
            f"{schedule.course.name} ({schedule.course.code}){room}"
        )

    return "Orari javor i studentit:\n" + "\n".join(lines)


def answer_exams(
    profile: StudentProfile,
    db: Session,
    only_upcoming: bool = True,
    course_code: str | None = None,
) -> str:
    query = (
        select(Exam)
        .join(Course, Course.id == Exam.course_id)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(
            Enrollment.student_profile_id == profile.id,
            Enrollment.status == "ACTIVE",
        )
    )

    if course_code:
        query = query.where(Course.code == course_code.upper())

    exams = db.scalars(query.order_by(Exam.exam_date)).all()

    if only_upcoming:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        exams = [exam for exam in exams if exam.exam_date >= now]

    if not exams:
        return (
            "Nuk u gjet asnjë provim që i përgjigjet këtyre kritereve "
            "për lëndët aktive të studentit."
        )

    lines = []

    for exam in exams:
        room = f", salla {exam.room}" if exam.room else ""

        lines.append(
            f"- {exam.course.name} ({exam.course.code}): {exam.exam_type}, "
            f"{exam.exam_date.strftime('%d.%m.%Y %H:%M')}{room}"
        )

    label = "Provimet e ardhshme" if only_upcoming else "Të gjitha provimet"

    return f"{label} të studentit:\n" + "\n".join(lines)


def answer_profile(profile: StudentProfile, db: Session) -> str:
    program = db.get(Program, profile.program_id)

    program_name = program.name if program else "i panjohur"
    degree = program.degree_level if program else "i panjohur"
    faculty = program.faculty.name if program and program.faculty else None
    period = period_for_semester(profile.semester, db)

    lines = [
        "Profili akademik i studentit:",
        f"- Numri i studentit: {profile.student_number}",
    ]

    if faculty:
        lines.append(f"- Fakulteti: {faculty}")

    lines += [
        f"- Programi: {program_name} ({degree})",
        f"- Viti i studimit: {profile.study_year}",
        f"- Semestri i kurrikulës: {profile.semester}",
    ]

    if period is not None:
        lines.append(f"- Periudha akademike: {period.label}")

    if program is not None and not program.ects_is_official:
        lines.append(
            "- Shënim: ECTS-të e lëndëve në sistem janë demonstrative, "
            "jo zyrtare."
        )

    lines.append(f"- Gjuha e preferuar: {profile.preferred_language}")

    return "\n".join(lines)


def answer_course_catalog(
    db: Session,
    query_text: str | None = None,
    semester: int | None = None,
    program_id: int | None = None,
) -> str:
    """Katalogu i plotë i lëndëve, jo vetëm ato ku studenti
    është i regjistruar."""

    query = select(Course)

    if query_text:
        pattern = f"%{query_text.strip()}%"
        query = query.where(Course.name.ilike(pattern))

    if semester is not None:
        query = query.where(Course.semester == semester)

    if program_id is not None:
        query = query.where(Course.program_id == program_id)

    courses = db.scalars(
        query.order_by(Course.semester, Course.name).limit(30)
    ).all()

    if not courses:
        return "Nuk u gjet asnjë lëndë në katalog me këto kritere."

    lines = [
        f"- {course.name} ({course.code}), semestri {course.semester}, "
        f"{course.ects} ECTS"
        for course in courses
    ]

    return "Lëndë nga katalogu i universitetit:\n" + "\n".join(lines)


def answer_course_details(
    db: Session,
    course_code: str,
) -> str:
    """Detajet e plota të një lënde: profesori, parakushtet,
    syllabus-i dhe orari."""

    course = db.scalar(
        select(Course).where(Course.code == course_code.upper())
    )

    if course is None:
        return f"Nuk u gjet asnjë lëndë me kodin {course_code.upper()}."

    lines = [
        f"{course.name} ({course.code})",
        f"- ECTS: {course.ects}",
        f"- Semestri: {course.semester}",
    ]

    if course.professor is not None:
        professor = course.professor

        lines.append(f"- Profesori: {professor.full_name}")

        if professor.email:
            lines.append(f"- Email i profesorit: {professor.email}")

        if professor.consultation_hours:
            lines.append(
                f"- Konsultimet: {professor.consultation_hours}"
            )

    if course.description:
        lines.append(f"- Përshkrimi: {course.description}")

    prerequisites = [
        link.prerequisite for link in course.prerequisites
    ]

    if prerequisites:
        names = ", ".join(
            f"{item.name} ({item.code})" for item in prerequisites
        )
        lines.append(f"- Parakushtet: {names}")
    else:
        lines.append("- Parakushtet: nuk ka")

    if course.syllabus:
        lines.append(f"- Syllabus:\n{course.syllabus}")

    schedules = db.scalars(
        select(Schedule).where(Schedule.course_id == course.id)
    ).all()

    if schedules:
        slots = "; ".join(
            f"{DAY_NAMES_SQ.get(item.day_of_week, item.day_of_week)} "
            f"{_format_time_range(item.start_time, item.end_time)}"
            f"{f' ({item.room})' if item.room else ''}"
            for item in schedules
        )
        lines.append(f"- Ligjëratat: {slots}")

    return "\n".join(lines)


def answer_deadlines(
    db: Session,
    profile: StudentProfile | None = None,
    only_upcoming: bool = True,
    deadline_type: str | None = None,
) -> str:
    """Afatet administrative: regjistrime, pagesa, aplikime,
    diplomim dhe evente."""

    query = select(Deadline)

    if profile is not None:
        # Afatet pa program vlejnë për të gjithë studentët.
        query = query.where(
            or_(
                Deadline.program_id.is_(None),
                Deadline.program_id == profile.program_id,
            )
        )

    if deadline_type:
        query = query.where(
            Deadline.deadline_type == deadline_type.upper()
        )

    if only_upcoming:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        query = query.where(Deadline.due_date >= now)

    deadlines = db.scalars(
        query.order_by(Deadline.due_date).limit(30)
    ).all()

    if not deadlines:
        return "Nuk u gjet asnjë afat me këto kritere."

    lines = []

    for item in deadlines:
        line = (
            f"- {item.title} ({item.deadline_type}): "
            f"{item.due_date.strftime('%d.%m.%Y %H:%M')}"
        )

        if item.description:
            line += f" — {item.description}"

        lines.append(line)

    return "Afatet:\n" + "\n".join(lines)


def answer_notifications(
    db: Session,
    profile: StudentProfile | None = None,
    limit: int = 10,
) -> str:
    query = select(Notification).where(
        Notification.is_active.is_(True)
    )

    if profile is not None:
        query = query.where(
            or_(
                Notification.program_id.is_(None),
                Notification.program_id == profile.program_id,
            )
        )

    notifications = db.scalars(
        query.order_by(Notification.created_at.desc()).limit(limit)
    ).all()

    if not notifications:
        return "Nuk ka njoftime aktive."

    lines = [
        f"- [{item.severity}] {item.title}: {item.body} "
        f"({item.created_at.strftime('%d.%m.%Y')})"
        for item in notifications
    ]

    return "Njoftimet e fundit:\n" + "\n".join(lines)
