from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    student_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    program_id: Mapped[int] = mapped_column(
        ForeignKey("programs.id"),
        nullable=False,
    )

    academic_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    preferred_language: Mapped[str] = mapped_column(
        String(10),
        default="sq",
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="student_profile",
    )

    program = relationship(
        "Program",
        back_populates="students",
    )
    
    enrollments = relationship(
    "Enrollment",
    back_populates="student",
    cascade="all, delete-orphan",
)