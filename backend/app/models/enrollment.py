from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.clock import utcnow


class Enrollment(Base):
    __tablename__ = "enrollments"

    __table_args__ = (
        UniqueConstraint(
            "student_profile_id",
            "course_id",
            name="uq_student_course",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    student_profile_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Grupi i lëndës ku studenti ndjek mësimin, dhe kështu profesori i
    # tij. Bosh kur lënda nuk ka grupe.
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("course_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Periudha akademike kur studenti e ndjek lëndën (p.sh. 2026/2027
    # dimërore). Bosh për regjistrimet pa periudhë të caktuar.
    period_id: Mapped[int | None] = mapped_column(
        ForeignKey("academic_periods.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        nullable=False,
    )

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    student = relationship(
        "StudentProfile",
        back_populates="enrollments",
    )

    course = relationship(
        "Course",
        back_populates="enrollments",
    )

    period = relationship("AcademicPeriod")