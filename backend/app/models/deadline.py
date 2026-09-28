from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Deadline(Base):
    """Afate dhe evente akademike: regjistrime, pagesa, aplikime,
    diplomim. Kur `program_id` është bosh, vlen për të gjithë."""

    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # REGISTRATION, PAYMENT, APPLICATION, GRADUATION, EVENT, OTHER
    deadline_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OTHER",
    )

    due_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    program_id: Mapped[int | None] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=True,
    )

    program = relationship("Program")
