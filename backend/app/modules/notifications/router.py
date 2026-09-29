from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.notification import Notification
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.academic import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)


router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


def get_notification_or_404(
    notification_id: int,
    db: Session,
) -> Notification:
    notification = db.get(Notification, notification_id)

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    return notification


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    notification = Notification(
        **payload.model_dump(),
        created_by=current_user.id,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Notification)

    if current_user.role == UserRole.STUDENT:
        query = query.where(Notification.is_active.is_(True))

        profile = db.scalar(
            select(StudentProfile).where(
                StudentProfile.user_id == current_user.id
            )
        )

        if profile is not None:
            query = query.where(
                or_(
                    Notification.program_id.is_(None),
                    Notification.program_id == profile.program_id,
                )
            )

    return db.scalars(
        query.order_by(Notification.created_at.desc())
    ).all()


@router.put(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def update_notification(
    notification_id: int,
    payload: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    notification = get_notification_or_404(notification_id, db)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(notification, field, value)

    db.commit()
    db.refresh(notification)

    return notification


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    notification = get_notification_or_404(notification_id, db)

    # Fshirje e vërtetë, si te afatet dhe provimet. Për ta fshehur
    # përkohësisht, admini vendos `is_active=False` me PUT.
    db.delete(notification)

    db.commit()

    return None
