from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.course import Course
from app.models.exam import Exam
from app.models.user import User
from app.schemas.exam import (
    ExamCreate,
    ExamResponse,
    ExamUpdate,
)


router = APIRouter(
    prefix="/api/exams",
    tags=["Exams"],
)


@router.post(
    "",
    response_model=ExamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_exam(
    exam_data: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    course = db.get(Course, exam_data.course_id)

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    exam = Exam(
        course_id=exam_data.course_id,
        exam_type=exam_data.exam_type,
        exam_date=exam_data.exam_date,
        room=exam_data.room,
    )

    db.add(exam)
    db.commit()
    db.refresh(exam)

    return exam


@router.get(
    "",
    response_model=list[ExamResponse],
)
def get_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Exam).order_by(Exam.exam_date)
    ).all()


@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = db.get(Exam, exam_id)

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    return exam


@router.put(
    "/{exam_id}",
    response_model=ExamResponse,
)
def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    exam = db.get(Exam, exam_id)

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    update_data = exam_data.model_dump(exclude_unset=True)

    if "course_id" in update_data:
        course = db.get(Course, update_data["course_id"])

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found.",
            )

    for field, value in update_data.items():
        setattr(exam, field, value)

    db.commit()
    db.refresh(exam)

    return exam


@router.delete(
    "/{exam_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    exam = db.get(Exam, exam_id)

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found.",
        )

    db.delete(exam)
    db.commit()

    return None