from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.professor import Professor
from app.models.user import User
from app.schemas.academic import (
    ProfessorCreate,
    ProfessorResponse,
    ProfessorUpdate,
)


router = APIRouter(
    prefix="/api/professors",
    tags=["Professors"],
)


def get_professor_or_404(professor_id: int, db: Session) -> Professor:
    professor = db.get(Professor, professor_id)

    if professor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor not found.",
        )

    return professor


@router.post(
    "",
    response_model=ProfessorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_professor(
    payload: ProfessorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    data = payload.model_dump()

    if data.get("email") is not None:
        data["email"] = str(data["email"])

    professor = Professor(**data)

    db.add(professor)
    db.commit()
    db.refresh(professor)

    return professor


@router.get("", response_model=list[ProfessorResponse])
def list_professors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Professor).order_by(
            Professor.last_name,
            Professor.first_name,
        )
    ).all()


@router.get("/{professor_id}", response_model=ProfessorResponse)
def get_professor(
    professor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_professor_or_404(professor_id, db)


@router.put("/{professor_id}", response_model=ProfessorResponse)
def update_professor(
    professor_id: int,
    payload: ProfessorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    professor = get_professor_or_404(professor_id, db)

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "email" and value is not None:
            value = str(value)

        setattr(professor, field, value)

    db.commit()
    db.refresh(professor)

    return professor


@router.delete(
    "/{professor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_professor(
    professor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    professor = get_professor_or_404(professor_id, db)

    db.delete(professor)
    db.commit()

    return None
