from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.program import Program
from app.models.user import User
from app.schemas.program import (
    ProgramCreate,
    ProgramResponse,
    ProgramUpdate,
)


router = APIRouter(
    prefix="/api/programs",
    tags=["Programs"],
)


@router.post(
    "",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_program(
    program_data: ProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    program = Program(
        name=program_data.name,
        degree_level=program_data.degree_level,
        specialization=program_data.specialization,
        total_ects=program_data.total_ects,
        duration_years=program_data.duration_years,
        description=program_data.description,
    )

    db.add(program)
    db.commit()
    db.refresh(program)

    return program


@router.get(
    "",
    response_model=list[ProgramResponse],
)
def get_programs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    programs = db.scalars(
        select(Program).order_by(Program.id)
    ).all()

    return programs


@router.get(
    "/{program_id}",
    response_model=ProgramResponse,
)
def get_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    program = db.get(Program, program_id)

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found.",
        )

    return program


@router.put(
    "/{program_id}",
    response_model=ProgramResponse,
)
def update_program(
    program_id: int,
    program_data: ProgramUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    program = db.get(Program, program_id)

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found.",
        )

    update_data = program_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(program, field, value)

    db.commit()
    db.refresh(program)

    return program


@router.delete(
    "/{program_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    program = db.get(Program, program_id)

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found.",
        )

    db.delete(program)
    db.commit()

    return None