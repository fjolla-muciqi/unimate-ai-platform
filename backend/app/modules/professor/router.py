"""Pamja e profesorit mbi lëndët e veta.

Pasqyra e `/api/student/me/*`, por e ndërtuar mbi `Course.professor_id`
në vend të `Enrollment`. Çdo query niset nga rreshti `Professor` i
nxjerrë prej JWT-së — asnjë id profesori nuk pranohet nga klienti,
prandaj një profesor nuk sheh dot studentët e një kolegu.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_professor
from app.core.teaching import (
    professor_sees_enrollment,
    professor_sees_schedule,
    teaches_course,
)
from app.models.course import Course
from app.models.course_group import CourseGroup
from app.models.document import Document
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.faculty import Faculty
from app.models.professor import Professor
from app.models.schedule import Schedule
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.dashboard import (
    DashboardExam,
    DashboardSlot,
    ProfessorCourse,
    ProfessorDashboard,
    ProfessorStudent,
)
from app.schemas.exam import ExamResponse
from app.schemas.schedule import ScheduleResponse
from app.core.clock import utcnow


router = APIRouter(
    prefix="/api/professor/me",
    tags=["Professor"],
)


UPCOMING_EXAM_LIMIT = 5


def current_professor(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
) -> Professor:
    """Rreshti `Professor` i lidhur me llogarinë e kyçur.

    `require_professor` garanton rolin; kjo garanton se roli ka edhe
    një rekord të vërtetë pas vetes. Një llogari PROFESSOR pa
    `Professor.user_id` do të kalonte guard-in por s'do të kishte
    asnjë lëndë — më mirë një 404 i qartë sesa lista bosh.
    """

    professor = db.scalar(
        select(Professor).where(Professor.user_id == current_user.id)
    )

    if professor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "This account has no professor record. "
                "Ask an administrator to link it."
            ),
        )

    return professor


def taught_course_ids(professor: Professor, db: Session) -> list[int]:
    return list(
        db.scalars(
            select(Course.id).where(teaches_course(professor.id))
        ).all()
    )


def count_enrolled(
    professor: Professor, course_ids: list[int], db: Session
) -> int:
    """Studentët e grupeve të këtij profesori në këto lëndë."""

    if not course_ids:
        return 0

    return db.scalar(
        select(func.count())
        .select_from(Enrollment)
        .join(Course, Course.id == Enrollment.course_id)
        .where(
            Enrollment.course_id.in_(course_ids),
            Enrollment.status == "ACTIVE",
            professor_sees_enrollment(professor.id),
        )
    ) or 0


@router.get(
    "/courses",
    response_model=list[ProfessorCourse],
)
def get_my_courses(
    db: Session = Depends(get_db),
    professor: Professor = Depends(current_professor),
):
    courses = db.scalars(
        select(Course)
        .where(teaches_course(professor.id))
        .order_by(Course.semester, Course.name)
    ).all()

    return [
        ProfessorCourse(
            id=course.id,
            code=course.code,
            name=course.name,
            ects=course.ects,
            semester=course.semester,
            enrolled_students=count_enrolled(professor, [course.id], db),
        )
        for course in courses
    ]


@router.get(
    "/schedule",
    response_model=list[ScheduleResponse],
)
def get_my_schedule(
    db: Session = Depends(get_db),
    professor: Professor = Depends(current_professor),
):
    # Ligjëratat e përbashkëta dhe ato të grupeve të tij, jo të kolegëve.
    return db.scalars(
        select(Schedule)
        .join(Course, Course.id == Schedule.course_id)
        .where(professor_sees_schedule(professor.id))
        .order_by(Schedule.day_of_week, Schedule.start_time)
    ).all()


@router.get(
    "/exams",
    response_model=list[ExamResponse],
)
def get_my_exams(
    db: Session = Depends(get_db),
    professor: Professor = Depends(current_professor),
):
    course_ids = taught_course_ids(professor, db)

    if not course_ids:
        return []

    return db.scalars(
        select(Exam)
        .where(Exam.course_id.in_(course_ids))
        .order_by(Exam.exam_date)
    ).all()


@router.get(
    "/students",
    response_model=list[ProfessorStudent],
)
def get_my_students(
    course_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
    professor: Professor = Depends(current_professor),
):
    """Studentët e regjistruar në lëndët e këtij profesori.

    `course_code` vjen nga klienti, prandaj filtri mbi grupet e
    profesorit mbetet i pandryshuar sipër tij: një kod lënde i huaj, ose
    grupi i një kolegu te e njëjta lëndë, kthen listë bosh.
    """

    query = (
        select(User, StudentProfile, Course, CourseGroup)
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .join(
            Enrollment,
            Enrollment.student_profile_id == StudentProfile.id,
        )
        .join(Course, Course.id == Enrollment.course_id)
        .outerjoin(CourseGroup, CourseGroup.id == Enrollment.group_id)
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

    return [
        ProfessorStudent(
            student_profile_id=profile.id,
            full_name=f"{user.first_name} {user.last_name}",
            email=user.email,
            student_number=profile.student_number,
            academic_year=profile.academic_year,
            course_code=course.code,
            course_name=course.name,
            group_name=group.name if group else None,
        )
        for user, profile, course, group in rows
    ]


@router.get(
    "/dashboard",
    response_model=ProfessorDashboard,
)
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    professor: Professor = Depends(current_professor),
):
    course_ids = taught_course_ids(professor, db)

    courses_by_id = {
        course.id: course
        for course in (
            db.scalars(
                select(Course).where(Course.id.in_(course_ids))
            ).all()
            if course_ids
            else []
        )
    }

    now = utcnow()
    today = now.strftime("%A")

    today_slots = (
        db.scalars(
            select(Schedule)
            .join(Course, Course.id == Schedule.course_id)
            .where(
                professor_sees_schedule(professor.id),
                Schedule.day_of_week == today,
            )
            .order_by(Schedule.start_time)
        ).all()
        if course_ids
        else []
    )

    upcoming_exams = (
        db.scalars(
            select(Exam)
            .where(
                Exam.course_id.in_(course_ids),
                Exam.exam_date >= now,
            )
            .order_by(Exam.exam_date)
            .limit(UPCOMING_EXAM_LIMIT)
        ).all()
        if course_ids
        else []
    )

    faculty = (
        db.get(Faculty, professor.faculty_id)
        if professor.faculty_id
        else None
    )

    my_documents = db.scalar(
        select(func.count())
        .select_from(Document)
        .where(
            Document.uploaded_by == current_user.id,
            Document.is_active.is_(True),
        )
    ) or 0

    return ProfessorDashboard(
        full_name=professor.full_name,
        title=professor.title,
        faculty_name=faculty.name if faculty else None,
        office=professor.office,
        consultation_hours=professor.consultation_hours,
        courses_taught=len(course_ids),
        total_students=count_enrolled(professor, course_ids, db),
        today=today,
        today_schedule=[
            DashboardSlot(
                course_code=courses_by_id[slot.course_id].code,
                course_name=courses_by_id[slot.course_id].name,
                start_time=slot.start_time,
                end_time=slot.end_time,
                room=slot.room,
            )
            for slot in today_slots
            if slot.course_id in courses_by_id
        ],
        upcoming_exams=[
            DashboardExam(
                course_code=courses_by_id[exam.course_id].code,
                course_name=courses_by_id[exam.course_id].name,
                exam_type=exam.exam_type,
                exam_date=exam.exam_date,
                room=exam.room,
                days_until=(exam.exam_date - now).days,
            )
            for exam in upcoming_exams
            if exam.course_id in courses_by_id
        ],
        my_documents=my_documents,
    )
