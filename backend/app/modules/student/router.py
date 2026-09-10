from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.course import Course
from app.models.deadline import Deadline
from app.models.document import Document, DocumentStatus
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.notification import Notification
from app.models.program import Program
from app.models.schedule import Schedule
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.course import CourseResponse
from app.schemas.dashboard import (
    DashboardExam,
    DashboardProgress,
    DashboardResponse,
    DashboardSlot,
)
from app.schemas.exam import ExamResponse
from app.schemas.schedule import ScheduleResponse


router = APIRouter(
    prefix="/api/student/me",
    tags=["Student Dashboard"],
)


def get_student_profile(
    current_user: User,
    db: Session,
) -> StudentProfile:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required.",
        )

    profile = db.scalar(
        select(StudentProfile).where(
            StudentProfile.user_id == current_user.id
        )
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    return profile


@router.get(
    "/courses",
    response_model=list[CourseResponse],
)
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_student_profile(current_user, db)

    courses = db.scalars(
        select(Course)
        .join(
            Enrollment,
            Enrollment.course_id == Course.id,
        )
        .where(
            Enrollment.student_profile_id == profile.id,
            Enrollment.status == "ACTIVE",
        )
        .order_by(
            Course.semester,
            Course.name,
        )
    ).all()

    return courses


@router.get(
    "/schedule",
    response_model=list[ScheduleResponse],
)
def get_my_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_student_profile(current_user, db)

    schedules = db.scalars(
        select(Schedule)
        .join(
            Course,
            Course.id == Schedule.course_id,
        )
        .join(
            Enrollment,
            Enrollment.course_id == Course.id,
        )
        .where(
            Enrollment.student_profile_id == profile.id,
            Enrollment.status == "ACTIVE",
        )
        .order_by(
            Schedule.day_of_week,
            Schedule.start_time,
        )
    ).all()

    return schedules


@router.get(
    "/exams",
    response_model=list[ExamResponse],
)
def get_my_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_student_profile(current_user, db)

    exams = db.scalars(
        select(Exam)
        .join(
            Course,
            Course.id == Exam.course_id,
        )
        .join(
            Enrollment,
            Enrollment.course_id == Course.id,
        )
        .where(
            Enrollment.student_profile_id == profile.id,
            Enrollment.status == "ACTIVE",
        )
        .order_by(Exam.exam_date)
    ).all()

    return exams


# Sa provime të ardhshme shfaqen te dashboard-i.
UPCOMING_EXAM_LIMIT = 3


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gjithçka që kërkon faqja kryesore e studentit, në një kërkesë.

    Të gjitha numërimet nisin nga profili i nxjerrë prej JWT-së,
    kurrë nga një id i dërguar nga klienti.
    """

    profile = get_student_profile(current_user, db)
    program = db.get(Program, profile.program_id)

    now = datetime.utcnow()

    enrollments = db.scalars(
        select(Enrollment).where(
            Enrollment.student_profile_id == profile.id
        )
    ).all()

    course_ids = [row.course_id for row in enrollments]

    active_course_ids = [
        row.course_id
        for row in enrollments
        if row.status == "ACTIVE"
    ]

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

    # Kreditet e fituara janë ato të lëndëve të përfunduara; lëndët
    # aktive numërohen veçmas që studenti të shohë edhe sa ka në
    # dorë këtë semestër.
    earned_ects = sum(
        courses_by_id[row.course_id].ects
        for row in enrollments
        if row.status == "COMPLETED" and row.course_id in courses_by_id
    )

    in_progress_ects = sum(
        courses_by_id[course_id].ects
        for course_id in active_course_ids
        if course_id in courses_by_id
    )

    required_ects = program.total_ects if program else 0

    today = now.strftime("%A")

    today_slots = (
        db.scalars(
            select(Schedule)
            .where(
                Schedule.course_id.in_(active_course_ids),
                Schedule.day_of_week == today,
            )
            .order_by(Schedule.start_time)
        ).all()
        if active_course_ids
        else []
    )

    upcoming_exams = (
        db.scalars(
            select(Exam)
            .where(
                Exam.course_id.in_(active_course_ids),
                Exam.exam_date >= now,
            )
            .order_by(Exam.exam_date)
            .limit(UPCOMING_EXAM_LIMIT)
        ).all()
        if active_course_ids
        else []
    )

    deadline_count = db.scalar(
        select(func.count())
        .select_from(Deadline)
        .where(
            Deadline.due_date >= now,
            or_(
                Deadline.program_id.is_(None),
                Deadline.program_id == profile.program_id,
            ),
        )
    ) or 0

    notification_count = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.is_active.is_(True),
            or_(
                Notification.program_id.is_(None),
                Notification.program_id == profile.program_id,
            ),
        )
    ) or 0

    # Vetëm dokumentet e indeksuara: një dokument që ende përpunohet
    # nuk i përgjigjet dot pyetjeve të studentit.
    document_count = db.scalar(
        select(func.count())
        .select_from(Document)
        .where(
            Document.is_active.is_(True),
            Document.status == DocumentStatus.INDEXED,
        )
    ) or 0

    return DashboardResponse(
        full_name=f"{current_user.first_name} {current_user.last_name}",
        student_number=profile.student_number,
        program_name=program.name if program else "",
        academic_year=profile.academic_year,
        semester=profile.semester,
        active_courses=len(active_course_ids),
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
        upcoming_deadlines=deadline_count,
        active_notifications=notification_count,
        available_documents=document_count,
        progress=DashboardProgress(
            earned_ects=earned_ects,
            in_progress_ects=in_progress_ects,
            required_ects=required_ects,
            percent=(
                round(earned_ects / required_ects * 100, 1)
                if required_ects
                else 0.0
            ),
        ),
    )
