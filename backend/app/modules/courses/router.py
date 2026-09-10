from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.course import Course
from app.models.course_prerequisite import CoursePrerequisite
from app.models.program import Program
from app.models.user import User
from app.schemas.academic import (
    PrerequisiteCreate,
    PrerequisiteResponse,
)
from app.schemas.course import (
    CourseCreate,
    CourseResponse,
    CourseUpdate,
)


router = APIRouter(
    prefix="/api/courses",
    tags=["Courses"],
)


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    program = db.get(Program, course_data.program_id)

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found.",
        )

    existing_course = db.scalar(
        select(Course).where(Course.code == course_data.code)
    )

    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this code already exists.",
        )

    course = Course(
        code=course_data.code,
        name=course_data.name,
        description=course_data.description,
        ects=course_data.ects,
        semester=course_data.semester,
        program_id=course_data.program_id,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return course


@router.get(
    "",
    response_model=list[CourseResponse],
)
def get_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Course).order_by(Course.semester, Course.name)
    ).all()


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.get(Course, course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    return course


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    course = db.get(Course, course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    update_data = course_data.model_dump(exclude_unset=True)

    if "program_id" in update_data:
        program = db.get(Program, update_data["program_id"])

        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found.",
            )

    if "code" in update_data:
        existing_course = db.scalar(
            select(Course).where(
                Course.code == update_data["code"],
                Course.id != course_id,
            )
        )

        if existing_course:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A course with this code already exists.",
            )

    for field, value in update_data.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)

    return course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    course = db.get(Course, course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    db.delete(course)
    db.commit()

    return None

@router.get(
    "/{course_id}/prerequisites",
    response_model=list[PrerequisiteResponse],
)
def list_prerequisites(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(CoursePrerequisite).where(
            CoursePrerequisite.course_id == course_id
        )
    ).all()


@router.post(
    "/{course_id}/prerequisites",
    response_model=PrerequisiteResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_prerequisite(
    course_id: int,
    payload: PrerequisiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if payload.prerequisite_id == course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A course cannot be its own prerequisite.",
        )

    for identifier in (course_id, payload.prerequisite_id):
        if db.get(Course, identifier) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found.",
            )

    existing = db.scalar(
        select(CoursePrerequisite).where(
            CoursePrerequisite.course_id == course_id,
            CoursePrerequisite.prerequisite_id == payload.prerequisite_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This prerequisite is already set.",
        )

    link = CoursePrerequisite(
        course_id=course_id,
        prerequisite_id=payload.prerequisite_id,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return link


@router.delete(
    "/{course_id}/prerequisites/{prerequisite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_prerequisite(
    course_id: int,
    prerequisite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    link = db.scalar(
        select(CoursePrerequisite).where(
            CoursePrerequisite.course_id == course_id,
            CoursePrerequisite.prerequisite_id == prerequisite_id,
        )
    )

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prerequisite not found.",
        )

    db.delete(link)
    db.commit()

    return None
