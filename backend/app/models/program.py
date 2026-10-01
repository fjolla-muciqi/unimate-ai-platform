from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    degree_level: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    specialization: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    total_ects: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=180,
    )

    # False: shpërndarja e ECTS-ve nëpër lëndë është demonstrative, jo
    # zyrtare. Ndërfaqja dhe asistenti e shënojnë qartë.
    ects_is_official: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    duration_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    graduation_requirements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    faculty_id: Mapped[int | None] = mapped_column(
        ForeignKey("faculties.id", ondelete="SET NULL"),
        nullable=True,
    )

    faculty = relationship(
        "Faculty",
        back_populates="programs",
    )

    students = relationship(
        "StudentProfile",
        back_populates="program",
    )
    courses = relationship(
    "Course",
    back_populates="program",
    cascade="all, delete-orphan",
)