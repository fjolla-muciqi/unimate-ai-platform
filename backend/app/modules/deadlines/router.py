from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.deadline import Deadline
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.academic import (
    DeadlineCreate,
    DeadlineResponse,
    DeadlineUpdate,
)


router = APIRouter(
    prefix="/api/deadlines",
    tags=["Deadlines"],
)


def get_deadline_or_404(deadline_id: int, db: Session) -> Deadline:
    deadline = db.get(Deadline, deadline_id)

    if deadline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deadline not found.",
        )

    return deadline


@router.post(
    "",
    response_model=DeadlineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deadline(
    payload: DeadlineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    deadline = Deadline(**payload.model_dump())

    db.add(deadline)
    db.commit()
    db.refresh(deadline)

    return deadline


@router.get("", response_model=list[DeadlineResponse])
def list_deadlines(
    only_upcoming: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Studentët shohin afatet e programit të tyre plus ato të
    përgjithshme; administratori i sheh të gjitha."""

    query = select(Deadline)

    if current_user.role == UserRole.STUDENT:
        profile = db.scalar(
            select(StudentProfile).where(
                StudentProfile.user_id == current_user.id
            )
        )

        if profile is not None:
            query = query.where(
                or_(
                    Deadline.program_id.is_(None),
                    Deadline.program_id == profile.program_id,
                )
            )

    if only_upcoming:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        query = query.where(Deadline.due_date >= now)

    return db.scalars(query.order_by(Deadline.due_date)).all()


@router.put("/{deadline_id}", response_model=DeadlineResponse)
def update_deadline(
    deadline_id: int,
    payload: DeadlineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    deadline = get_deadline_or_404(deadline_id, db)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(deadline, field, value)

    db.commit()
    db.refresh(deadline)

    return deadline


@router.delete(
    "/{deadline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    deadline = get_deadline_or_404(deadline_id, db)

    db.delete(deadline)
    db.commit()

    return None
