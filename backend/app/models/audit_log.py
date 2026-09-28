from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.clock import utcnow


class AuditEvent(str):
    """Llojet e ngjarjeve që regjistrohen.

    Nuk është Enum në bazë të të dhënave sepse lista pritet të rritet
    me kohë dhe një migrim për çdo lloj të ri do të ishte i tepërt.
    """

    GUARDRAIL_BLOCK = "guardrail_block"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    OUTPUT_BLOCKED = "output_blocked"


class AuditLog(Base):
    """Gjurma e ngjarjeve të sigurisë.

    Çdo bllokim nga Guardrail Agent-i lë një rresht këtu, që
    administratori të shohë se kush provoi çfarë dhe kur. Pa këtë,
    guardrail-i do të ishte i padukshëm dhe i pamatshëm.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Nullable sepse një tentativë mund të vijë edhe para se
    # përdoruesi të identifikohet.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    detail: Mapped[str] = mapped_column(Text, nullable=False)

    # Cila rregull e guardrail-it u aktivizua (p.sh. "instruction_override").
    rule: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
        index=True,
    )

    user = relationship("User")
