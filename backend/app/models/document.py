from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.clock import utcnow


class DocumentStatus(str):
    """Faza e dokumentit në pipeline-in RAG."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    academic_year: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # Kujt i përket dokumenti. Të dyja bosh: gjithë universitetit.
    # Me lëndë, fakulteti plotësohet nga programi i lëndës, që kërkimi
    # të mund të filtrojë vetëm sipas fakultetit.
    faculty_id: Mapped[int | None] = mapped_column(
        ForeignKey("faculties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Materialet e një profesori: vetëm studentët e grupit të tij i
    # përdorin te kërkimi. Bosh: materiali vlen për gjithë lëndën.
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("course_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Java e semestrit (1-15) dhe lloji, për materialet e lëndëve:
    # asistenti citon "Java 4 · Ligjëratë" dhe mund të kërkojë sipas javës.
    week: Mapped[int | None] = mapped_column(Integer, nullable=True)

    material_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # PENDING -> PROCESSING -> INDEXED ose FAILED.
    # Statusi është gjendja e vetme që frontend-i duhet të lexojë
    # për të ditur nëse dokumenti është gati për pyetje.
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Arsyeja e dështimit, kur statusi është FAILED.
    status_detail: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )