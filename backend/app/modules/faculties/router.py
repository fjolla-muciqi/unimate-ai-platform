from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.faculty import Faculty
from app.models.user import User
from app.schemas.academic import (
    FacultyCreate,
    FacultyResponse,
    FacultyUpdate,
)


router = APIRouter(
    prefix="/api/faculties",
    tags=["Faculties"],
)


def get_faculty_or_404(faculty_id: int, db: Session) -> Faculty:
    faculty = db.get(Faculty, faculty_id)

    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found.",
        )

    return faculty


@router.post(
    "",
    response_model=FacultyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_faculty(
    payload: FacultyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.scalar(
        select(Faculty).where(Faculty.name == payload.name)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A faculty with this name already exists.",
        )

    faculty = Faculty(**payload.model_dump())

    db.add(faculty)
    db.commit()
    db.refresh(faculty)

    return faculty


@router.get("", response_model=list[FacultyResponse])
def list_faculties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Faculty).order_by(Faculty.name)
    ).all()


@router.get("/{faculty_id}", response_model=FacultyResponse)
def get_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_faculty_or_404(faculty_id, db)


@router.put("/{faculty_id}", response_model=FacultyResponse)
def update_faculty(
    faculty_id: int,
    payload: FacultyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    faculty = get_faculty_or_404(faculty_id, db)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(faculty, field, value)

    db.commit()
    db.refresh(faculty)

    return faculty


@router.delete(
    "/{faculty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    faculty = get_faculty_or_404(faculty_id, db)

    db.delete(faculty)
    db.commit()

    return None
