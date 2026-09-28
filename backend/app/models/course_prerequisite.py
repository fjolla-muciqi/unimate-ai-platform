from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CoursePrerequisite(Base):
    """Lënda `course_id` kërkon si parakusht `prerequisite_id`."""

    __tablename__ = "course_prerequisites"

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "prerequisite_id",
            name="uq_course_prerequisite",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prerequisite_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )

    course = relationship(
        "Course",
        foreign_keys=[course_id],
        back_populates="prerequisites",
    )

    prerequisite = relationship(
        "Course",
        foreign_keys=[prerequisite_id],
    )
