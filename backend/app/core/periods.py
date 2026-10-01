"""Rregullat e periudhave akademike, në një vend.

Katër koncepte që nuk duhen ngatërruar:

- viti i studimit (StudentProfile.study_year): 1, 2 ose 3;
- semestri i kurrikulës (Course.semester): 1-6, ku viti N ka 2N-1 dhe 2N;
- viti akademik: kalendarik, p.sh. "2026/2027";
- periudha akademike (AcademicPeriod): viti akademik + dimërore/verore,
  kur lënda ofrohet dhe ndiqet.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic_period import AcademicPeriod, term_for_semester


def current_period(db: Session) -> AcademicPeriod | None:
    return db.scalar(
        select(AcademicPeriod).where(AcademicPeriod.is_current.is_(True))
    )


def period_for_semester(semester: int, db: Session) -> AcademicPeriod | None:
    """Periudha e vitit akademik aktual kur mbahet ky semestër i kurrikulës.

    Semestrat tek bien në dimërore, çiftet në verore.
    """

    current = current_period(db)

    if current is None:
        return None

    return db.scalar(
        select(AcademicPeriod).where(
            AcademicPeriod.academic_year == current.academic_year,
            AcademicPeriod.term == term_for_semester(semester),
        )
    )


def ensure_period_exists(period_id: int | None, db: Session) -> None:
    if period_id is not None and db.get(AcademicPeriod, period_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Periudha akademike nuk ekziston.",
        )


def study_year_for_semester(semester: int) -> int:
    return (semester + 1) // 2
