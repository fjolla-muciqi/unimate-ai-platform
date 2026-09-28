from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.clock import utcnow


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Burimet e cituara ruhen bashkë me përgjigjen, që historiku
    # i bisedës të mund të rihapet me citimet e sakta edhe pasi
    # dokumenti të jetë fshirë ose ri-indeksuar.
    sources: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Cilët agjentë e trajtuan pyetjen, sipas tools të thirrura.
    # Baza e metrikave të routing-ut dhe e panelit të analitikës.
    agents_used: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Përmbajtje e strukturuar nga Tutor Agent (quiz, flashcards),
    # që frontend-i e shfaq si komponentë interaktivë.
    artifacts: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Koha e përgjigjes në milisekonda (vetëm mesazhet e asistentit).
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Vlerësimi i studentit: 1 pozitiv, -1 negativ, None pa vlerësim.
    rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # True kur asistenti nuk gjeti informacion — "pyetjet pa përgjigje"
    # në panelin e administratorit.
    is_unanswered: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Rregulla e Guardrail Agent-it që e bllokoi kërkesën ose
    # përgjigjen; bosh kur mesazhi kaloi normalisht. Detajet e plota
    # ruhen te `audit_logs`.
    blocked_by: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )
