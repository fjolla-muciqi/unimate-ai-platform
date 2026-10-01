from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.program import Program
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.student_profile import (
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
)


router = APIRouter(
    prefix="/api/student-profiles",
    tags=["Student Profiles"],
)


@router.post(
    "",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student_profile(
    profile_data: StudentProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.get(User, profile_data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only users with STUDENT role can have a student profile.",
        )

    existing_profile = db.scalar(
        select(StudentProfile).where(
            StudentProfile.user_id == profile_data.user_id
        )
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student profile already exists for this user.",
        )

    program = db.get(Program, profile_data.program_id)

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found.",
        )

    existing_number = db.scalar(
        select(StudentProfile).where(
            StudentProfile.student_number == profile_data.student_number
        )
    )

    if existing_number:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student number already exists.",
        )

    profile = StudentProfile(
        user_id=profile_data.user_id,
        student_number=profile_data.student_number,
        program_id=profile_data.program_id,
        study_year=profile_data.study_year,
        semester=profile_data.semester,
        preferred_language=profile_data.preferred_language,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


@router.get(
    "/me",
    response_model=StudentProfileResponse,
)
def get_my_student_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    "",
    response_model=list[StudentProfileResponse],
)
def get_student_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return db.scalars(
        select(StudentProfile).order_by(StudentProfile.id)
    ).all()


@router.put(
    "/{profile_id}",
    response_model=StudentProfileResponse,
)
def update_student_profile(
    profile_id: int,
    profile_data: StudentProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    profile = db.get(StudentProfile, profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    update_data = profile_data.model_dump(exclude_unset=True)

    if "program_id" in update_data:
        program = db.get(Program, update_data["program_id"])

        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found.",
            )

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile