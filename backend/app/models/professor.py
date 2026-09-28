from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Professor(Base):
    __tablename__ = "professors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    title: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    office: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Orari i konsultimeve si tekst i lirë, p.sh.
    # "E martë 12:00-14:00, zyra B-210".
    consultation_hours: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    faculty_id: Mapped[int | None] = mapped_column(
        ForeignKey("faculties.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Lidhja me llogarinë e përdoruesit është opsionale: një profesor
    # mund të ekzistojë në katalog pa pasur ende llogari në sistem.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    faculty = relationship("Faculty", back_populates="professors")

    courses = relationship("Course", back_populates="professor")

    @property
    def full_name(self) -> str:
        parts = [self.title, self.first_name, self.last_name]

        return " ".join(part for part in parts if part)
