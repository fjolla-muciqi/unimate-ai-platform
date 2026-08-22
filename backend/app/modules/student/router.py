from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.schedule import Schedule
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.course import CourseResponse
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