"""Të dhënat akademike të profesorit.

Pasqyra e `academic_agent.py`, por e ndërtuar mbi lëndët që profesori
**ligjëron**, jo mbi ato ku është i regjistruar. I njëjti agjent dhe të
njëjtat tools i shërbejnë të dy roleve; ndryshon vetëm burimi i
filtrimit — lëndët dhe grupet që ligjëron (`core/teaching.py`) në vend
të `Enrollment`.

Kjo është arsyeja pse `ToolContext` mban edhe `profile` edhe
`professor`: modeli nuk zgjedh kurrë se të dhënat e kujt të lexojë.
Roli i përcaktuar nga JWT-ja e zgjedh atë para se tool-i të nisë.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agents.academic_agent import (
    DAY_NAMES_SQ,
    DAY_ORDER,
    _format_time_range,
)
from app.core.teaching import (
    count_professor_students,
    professor_sees_enrollment,
    professor_sees_schedule,
    teaches_course,
)
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.faculty import Faculty
from app.models.professor import Professor
from app.models.schedule import Schedule
from app.models.student_profile import StudentProfile
from app.models.user import User


NO_COURSES_MESSAGE = (
    "Këtij profesori nuk i është caktuar asnjë lëndë."
)


def taught_courses(professor: Professor, db: Session) -> list[Course]:
    return list(
        db.scalars(
            select(Course)
            .where(teaches_course(professor.id))
            .order_by(Course.semester, Course.name)
        ).all()
    )


def answer_courses(professor: Professor, db: Session) -> str:
    courses = taught_courses(professor, db)

    if not courses:
        return NO_COURSES_MESSAGE

    lines = [
        f"- {course.name} ({course.code}), semestri {course.semester}, "
        f"{course.ects} ECTS, "
        f"{count_professor_students(professor.id, course.id, db)} "
        "studentë në grupet e tij"
        for course in courses
    ]

    return (
        "Lëndët që ligjëron ky profesor:\n"
        + "\n".join(lines)
        + f"\nTotal: {len(courses)} lëndë."
    )


def answer_schedule(
    professor: Professor,
    db: Session,
    day_of_week: str | None = None,
) -> str:
    query = (
        select(Schedule)
        .join(Course, Course.id == Schedule.course_id)
        .where(professor_sees_schedule(professor.id))
    )

    if day_of_week:
        query = query.where(Schedule.day_of_week == day_of_week)

    schedules = db.scalars(query).all()

    if not schedules:
        if day_of_week:
            day = DAY_NAMES_SQ.get(day_of_week, day_of_week)

            return (
                f"Ky profesor nuk ka ligjërata të planifikuara "
                f"ditën {day}."
            )

        return "Këtij profesori nuk i është caktuar orar."

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

    return "Orari i ligjëratave të këtij profesori:\n" + "\n".join(lines)


def answer_exams(
    professor: Professor,
    db: Session,
    only_upcoming: bool = True,
    course_code: str | None = None,
) -> str:
    query = (
        select(Exam)
        .join(Course, Course.id == Exam.course_id)
        .where(teaches_course(professor.id))
    )

    if course_code:
        query = query.where(Course.code == course_code.upper())

    exams = db.scalars(query.order_by(Exam.exam_date)).all()

    if only_upcoming:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        exams = [exam for exam in exams if exam.exam_date >= now]

    if not exams:
        return (
            "Nuk u gjet asnjë provim për lëndët që ligjëron ky "
            "profesor."
        )

    lines = []

    for exam in exams:
        room = f", salla {exam.room}" if exam.room else ""

        lines.append(
            f"- {exam.course.name} ({exam.course.code}): {exam.exam_type}, "
            f"{exam.exam_date.strftime('%d.%m.%Y %H:%M')}{room}, "
            f"{count_professor_students(professor.id, exam.course_id, db)} "
            "kandidatë nga grupet e tij"
        )

    label = "Provimet e ardhshme" if only_upcoming else "Të gjitha provimet"

    return f"{label} të lëndëve të këtij profesori:\n" + "\n".join(lines)


def answer_profile(professor: Professor, db: Session) -> str:
    faculty = (
        db.get(Faculty, professor.faculty_id)
        if professor.faculty_id
        else None
    )

    courses = taught_courses(professor, db)

    return (
        "Profili i profesorit:\n"
        f"- Emri: {professor.full_name}\n"
        f"- Fakulteti: {faculty.name if faculty else 'i pacaktuar'}\n"
        f"- Zyra: {professor.office or 'e pacaktuar'}\n"
        f"- Konsultimet: "
        f"{professor.consultation_hours or 'të papublikuara'}\n"
        f"- Lëndë që ligjëron: {len(courses)}"
    )


def answer_students(
    professor: Professor,
    db: Session,
    course_code: str | None = None,
) -> str:
    """Studentët e regjistruar në lëndët e këtij profesori.

    Kufizimi te grupet e profesorit është i pashmangshëm në query: edhe
    nëse modeli kërkon një kod lënde që nuk i takon, ose një lëndë që e
    jep edhe një koleg, filtri i mbetet sipër dhe kthen vetëm studentët
    e grupeve të tij.
    """

    query = (
        select(User, StudentProfile, Course)
        .join(
            StudentProfile,
            StudentProfile.user_id == User.id,
        )
        .join(
            Enrollment,
            Enrollment.student_profile_id == StudentProfile.id,
        )
        .join(Course, Course.id == Enrollment.course_id)
        .where(
            professor_sees_enrollment(professor.id),
            Enrollment.status == "ACTIVE",
        )
    )

    if course_code:
        query = query.where(Course.code == course_code.upper())

    rows = db.execute(
        query.order_by(Course.code, User.last_name, User.first_name)
    ).all()

    if not rows:
        if course_code:
            return (
                f"Nuk u gjet asnjë student i regjistruar në lëndën "
                f"{course_code.upper()} te lëndët e këtij profesori. "
                "Kontrollo nëse kodi i lëndës i takon vërtet atij."
            )

        return "Asnjë student nuk është i regjistruar në këto lëndë."

    by_course: dict[str, list[str]] = {}

    for user, profile, course in rows:
        label = f"{course.name} ({course.code})"

        by_course.setdefault(label, []).append(
            f"{user.first_name} {user.last_name} — "
            f"nr. {profile.student_number}, viti {profile.study_year}"
        )

    sections = []

    for label, students in by_course.items():
        listed = "\n".join(f"  - {student}" for student in students)

        sections.append(
            f"- {label}: {len(students)} studentë\n{listed}"
        )

    return "Studentët e regjistruar:\n" + "\n".join(sections)


__all__ = [
    "answer_courses",
    "answer_schedule",
    "answer_exams",
    "answer_profile",
    "answer_students",
    "taught_courses",
    "NO_COURSES_MESSAGE",
]
