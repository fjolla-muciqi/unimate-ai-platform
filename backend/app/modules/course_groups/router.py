"""Grupet (paralelet) e lëndëve: e njëjta lëndë, profesorë të ndryshëm."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.course import Course
from app.models.course_group import CourseGroup
from app.models.enrollment import Enrollment
from app.models.professor import Professor
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.course_group import (
    CourseGroupCreate,
    CourseGroupResponse,
    CourseGroupUpdate,
)


router = APIRouter(
    prefix="/api/course-groups",
    tags=["Course groups"],
)


def to_response(group: CourseGroup, db: Session) -> CourseGroupResponse:
    course = db.get(Course, group.course_id)
    professor = (
        db.get(Professor, group.professor_id) if group.professor_id else None
    )

    return CourseGroupResponse(
        id=group.id,
        course_id=group.course_id,
        name=group.name,
        professor_id=group.professor_id,
        capacity=group.capacity,
        course_code=course.code if course else None,
        professor_name=professor.full_name if professor else None,
        student_count=db.scalar(
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.group_id == group.id,
                Enrollment.status == "ACTIVE",
            )
        )
        or 0,
    )


def get_group_or_404(group_id: int, db: Session) -> CourseGroup:
    group = db.get(CourseGroup, group_id)

    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupi nuk u gjet.",
        )

    return group


def ensure_professor_exists(professor_id: int | None, db: Session) -> None:
    if professor_id is not None and db.get(Professor, professor_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profesori nuk u gjet.",
        )


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kjo lëndë ka tashmë një grup me këtë emër.",
        )


@router.get("", response_model=list[CourseGroupResponse])
def list_groups(
    course_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(CourseGroup).join(Course, Course.id == CourseGroup.course_id)

    if course_id is not None:
        query = query.where(CourseGroup.course_id == course_id)

    groups = db.scalars(query.order_by(Course.code, CourseGroup.name)).all()

    return [to_response(group, db) for group in groups]


@router.post(
    "",
    response_model=CourseGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    payload: CourseGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if db.get(Course, payload.course_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lënda nuk u gjet.",
        )

    ensure_professor_exists(payload.professor_id, db)

    group = CourseGroup(
        course_id=payload.course_id,
        name=payload.name.strip(),
        professor_id=payload.professor_id,
        capacity=payload.capacity,
    )

    db.add(group)
    commit_or_conflict(db)
    db.refresh(group)

    return to_response(group, db)


@router.put("/{group_id}", response_model=CourseGroupResponse)
def update_group(
    group_id: int,
    payload: CourseGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    group = get_group_or_404(group_id, db)
    update_data = payload.model_dump(exclude_unset=True)

    ensure_professor_exists(update_data.get("professor_id"), db)

    for field, value in update_data.items():
        setattr(group, field, value.strip() if field == "name" else value)

    commit_or_conflict(db)
    db.refresh(group)

    return to_response(group, db)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Studentët e grupit mbeten të regjistruar në lëndë, pa grup;
    orari i veçantë i grupit fshihet bashkë me të."""

    group = get_group_or_404(group_id, db)

    # Eksplicite, jo vetëm përmes çelësave të huaj të bazës, që sjellja
    # të jetë e njëjtë edhe aty ku ata nuk zbatohen (SQLite).
    db.execute(
        update(Enrollment)
        .where(Enrollment.group_id == group.id)
        .values(group_id=None)
    )
    db.execute(delete(Schedule).where(Schedule.group_id == group.id))

    db.delete(group)
    db.commit()

    return None
