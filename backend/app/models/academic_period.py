from datetime import date

from sqlalchemy import Boolean, Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# Semestrat tek (1, 3, 5) mbahen në periudhën dimërore, çiftet në verore.
WINTER = "WINTER"
SUMMER = "SUMMER"
TERMS = (WINTER, SUMMER)


def term_for_semester(semester: int) -> str:
    return WINTER if semester % 2 == 1 else SUMMER


class AcademicPeriod(Base):
    """Periudha kur ofrohet dhe ndiqet një lëndë, p.sh. 2026/2027 dimërore.

    Ndryshe nga semestri i kurrikulës (Course.semester, 1-6) dhe viti i
    studimit (StudentProfile.study_year, 1-3), kjo është kalendarike.
    """

    __tablename__ = "academic_periods"

    __table_args__ = (
        UniqueConstraint(
            "academic_year",
            "term",
            name="uq_academic_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Formati "2026/2027".
    academic_year: Mapped[str] = mapped_column(
        String(9),
        nullable=False,
    )

    term: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Vetëm një periudhë është aktuale; e ruan router-i.
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    @property
    def label(self) -> str:
        term = "dimërore" if self.term == WINTER else "verore"

        return f"{self.academic_year}, periudha {term}"
