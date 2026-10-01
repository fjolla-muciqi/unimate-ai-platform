from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.academic_period import AcademicPeriod
from app.models.user import User
from app.schemas.academic_period import (
    AcademicPeriodCreate,
    AcademicPeriodResponse,
    AcademicPeriodUpdate,
)


router = APIRouter(
    prefix="/api/academic-periods",
    tags=["Academic periods"],
)


def get_period_or_404(period_id: int, db: Session) -> AcademicPeriod:
    period = db.get(AcademicPeriod, period_id)

    if period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic period not found.",
        )

    return period


def clear_current(db: Session, keep_id: int | None = None) -> None:
    """Vetëm një periudhë mund të jetë aktuale."""

    query = update(AcademicPeriod).values(is_current=False)

    if keep_id is not None:
        query = query.where(AcademicPeriod.id != keep_id)

    db.execute(query)


@router.post(
    "",
    response_model=AcademicPeriodResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_period(
    payload: AcademicPeriodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if payload.is_current:
        clear_current(db)

    period = AcademicPeriod(**payload.model_dump())
    db.add(period)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kjo periudhë ekziston tashmë.",
        )

    db.refresh(period)

    return period


@router.get("", response_model=list[AcademicPeriodResponse])
def list_periods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(AcademicPeriod).order_by(
            AcademicPeriod.academic_year.desc(),
            AcademicPeriod.start_date.desc(),
        )
    ).all()


@router.put("/{period_id}", response_model=AcademicPeriodResponse)
def update_period(
    period_id: int,
    payload: AcademicPeriodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    period = get_period_or_404(period_id, db)
    data = payload.model_dump(exclude_unset=True)

    if data.get("is_current"):
        clear_current(db, keep_id=period.id)

    for field, value in data.items():
        setattr(period, field, value)

    if period.end_date <= period.start_date:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data e mbarimit duhet të jetë pas fillimit.",
        )

    start, end = period.academic_year.split("/")

    if int(end) != int(start) + 1:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Viti akademik duhet të jetë si 2026/2027.",
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kjo periudhë ekziston tashmë.",
        )

    db.refresh(period)

    return period


@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Regjistrimet mbeten; vetëm humbasin lidhjen me periudhën.
    db.delete(get_period_or_404(period_id, db))
    db.commit()

    return None
