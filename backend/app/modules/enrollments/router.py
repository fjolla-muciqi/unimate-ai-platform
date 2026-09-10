from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.audit_log import AuditEvent
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentUpdate,
)


router = APIRouter(
    prefix="/api/enrollments",
    tags=["Enrollments"],
)


@router.post(
    "",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student = db.get(
        StudentProfile,
        enrollment_data.student_profile_id,
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    course = db.get(
        Course,
        enrollment_data.course_id,
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    enrollment = Enrollment(
        student_profile_id=enrollment_data.student_profile_id,
        course_id=enrollment_data.course_id,
        status=enrollment_data.status,
    )

    db.add(enrollment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this course.",
        )

    db.refresh(enrollment)

    return enrollment


@router.get(
    "",
    response_model=list[EnrollmentResponse],
)
def get_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return db.scalars(
        select(Enrollment).order_by(Enrollment.id)
    ).all()


@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
)
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Një regjistrim i vetëm.

    Administratori i sheh të gjitha; studenti vetëm të vetat. Id-ja
    vjen nga URL-ja, prandaj pronësia verifikohet këtu përpara se të
    kthehet çdo gjë — përndryshe kush do të mund të numëronte
    regjistrimet e të tjerëve duke provuar id.
    """

    enrollment = db.get(
        Enrollment,
        enrollment_id,
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    if current_user.role != UserRole.ADMIN:
        profile = db.scalar(
            select(StudentProfile).where(
                StudentProfile.user_id == current_user.id
            )
        )

        if (
            profile is None
            or enrollment.student_profile_id != profile.id
        ):
            record_event(
                db=db,
                user_id=current_user.id,
                event_type=AuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
                detail=(
                    f"Tentativë leximi e regjistrimit "
                    f"{enrollment_id} që i përket një studenti tjetër."
                ),
                rule="enrollment_ownership",
            )

            db.commit()

            # 404 dhe jo 403: një 403 do të konfirmonte se ky
            # regjistrim ekziston.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enrollment not found.",
            )

    return enrollment


@router.put(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    enrollment = db.get(
        Enrollment,
        enrollment_id,
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    update_data = enrollment_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(enrollment, field, value)

    db.commit()
    db.refresh(enrollment)

    return enrollment


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    enrollment = db.get(
        Enrollment,
        enrollment_id,
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    db.delete(enrollment)
    db.commit()

    return None