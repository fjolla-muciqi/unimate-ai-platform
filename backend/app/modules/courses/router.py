from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.course import Course
from app.models.program import Program
from app.models.user import User
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