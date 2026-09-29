"""Profesorët dhe llogaritë e tyre të kyçjes.

Administratori krijon profesorin dhe, me një fjalëkalim, edhe llogarinë
me rol PROFESSOR. Të dhënat e profesorit dhe llogaria mbahen në
përputhje (emri, email-i), dhe fshirja e profesorit e çaktivizon
llogarinë në vend që ta fshijë: dokumentet që ka ngarkuar dhe regjistri
i sigurisë i referohen ende.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, hash_password, require_admin
from app.models.course import Course
from app.models.course_group import CourseGroup
from app.models.faculty import Faculty
from app.models.professor import Professor
from app.models.user import User, UserRole
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


def to_response(
    professor: Professor, db: Session, include_account: bool = True
) -> ProfessorResponse:
    """Gjendja e llogarisë i tregohet vetëm administratorit."""

    account = (
        db.get(User, professor.user_id)
        if professor.user_id and include_account
        else None
    )

    return ProfessorResponse(
        id=professor.id,
        first_name=professor.first_name,
        last_name=professor.last_name,
        full_name=professor.full_name,
        title=professor.title,
        email=professor.email,
        office=professor.office,
        consultation_hours=professor.consultation_hours,
        faculty_id=professor.faculty_id,
        user_id=professor.user_id if include_account else None,
        has_account=account is not None,
        account_active=account.is_active if account else None,
    )


def ensure_faculty_exists(faculty_id: int | None, db: Session) -> None:
    if faculty_id is not None and db.get(Faculty, faculty_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fakulteti nuk u gjet.",
        )


def ensure_email_free(email: str, db: Session, except_user_id: int | None) -> None:
    """Email-i i llogarisë është unik te të gjithë përdoruesit."""

    owner = db.scalar(select(User).where(User.email == email))

    if owner is not None and owner.id != except_user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ky email përdoret nga një llogari tjetër.",
        )


def set_account(professor: Professor, password: str, db: Session) -> None:
    """Krijon llogarinë e kyçjes, ose ia rivendos fjalëkalimin."""

    if professor.user_id is not None:
        account = db.get(User, professor.user_id)
        account.password_hash = hash_password(password)
        account.is_active = True

        return

    if not professor.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Për llogarinë e kyçjes duhet email-i i profesorit.",
        )

    ensure_email_free(professor.email, db, except_user_id=None)

    account = User(
        first_name=professor.first_name,
        last_name=professor.last_name,
        email=professor.email,
        password_hash=hash_password(password),
        role=UserRole.PROFESSOR,
    )

    db.add(account)
    db.flush()

    professor.user_id = account.id


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
    data = payload.model_dump(exclude={"password"})

    if data.get("email") is not None:
        data["email"] = str(data["email"])

    ensure_faculty_exists(data.get("faculty_id"), db)

    professor = Professor(**data)
    db.add(professor)
    db.flush()

    if payload.password:
        set_account(professor, payload.password, db)

    db.commit()
    db.refresh(professor)

    return to_response(professor, db)


@router.get("", response_model=list[ProfessorResponse])
def list_professors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    professors = db.scalars(
        select(Professor).order_by(
            Professor.last_name,
            Professor.first_name,
        )
    ).all()

    is_admin = current_user.role == UserRole.ADMIN

    return [to_response(professor, db, is_admin) for professor in professors]


@router.get("/{professor_id}", response_model=ProfessorResponse)
def get_professor(
    professor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return to_response(
        get_professor_or_404(professor_id, db),
        db,
        current_user.role == UserRole.ADMIN,
    )


@router.put("/{professor_id}", response_model=ProfessorResponse)
def update_professor(
    professor_id: int,
    payload: ProfessorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    professor = get_professor_or_404(professor_id, db)
    data = payload.model_dump(exclude_unset=True, exclude={"password"})

    if data.get("email") is not None:
        data["email"] = str(data["email"])

    if "faculty_id" in data:
        ensure_faculty_exists(data["faculty_id"], db)

    for field, value in data.items():
        setattr(professor, field, value)

    # Llogaria ndjek emrin dhe email-in e profesorit.
    if professor.user_id is not None:
        account = db.get(User, professor.user_id)

        if professor.email and professor.email != account.email:
            ensure_email_free(professor.email, db, except_user_id=account.id)
            account.email = professor.email

        account.first_name = professor.first_name
        account.last_name = professor.last_name

    if payload.password:
        set_account(professor, payload.password, db)

    db.commit()
    db.refresh(professor)

    return to_response(professor, db)


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

    # Lëndët dhe grupet mbeten pa profesor. Eksplicite, jo vetëm përmes
    # çelësave të huaj, që sjellja të jetë e njëjtë edhe në SQLite.
    db.execute(
        update(Course)
        .where(Course.professor_id == professor.id)
        .values(professor_id=None)
    )
    db.execute(
        update(CourseGroup)
        .where(CourseGroup.professor_id == professor.id)
        .values(professor_id=None)
    )

    if professor.user_id is not None:
        account = db.get(User, professor.user_id)

        if account is not None:
            account.is_active = False

    db.delete(professor)
    db.commit()

    return None
