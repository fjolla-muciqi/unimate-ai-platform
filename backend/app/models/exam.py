from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )

    exam_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    exam_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    room: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    course = relationship(
        "Course",
        back_populates="exams",
    )