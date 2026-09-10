from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ects: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    syllabus: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    program_id: Mapped[int] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )

    professor_id: Mapped[int | None] = mapped_column(
        ForeignKey("professors.id", ondelete="SET NULL"),
        nullable=True,
    )

    professor = relationship(
        "Professor",
        back_populates="courses",
    )

    prerequisites = relationship(
        "CoursePrerequisite",
        foreign_keys="CoursePrerequisite.course_id",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    program = relationship(
        "Program",
        back_populates="courses",
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    schedules = relationship(
        "Schedule",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    exams = relationship(
        "Exam",
        back_populates="course",
        cascade="all, delete-orphan",
    )