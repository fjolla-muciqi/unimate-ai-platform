"""Regjistrimi i ngjarjeve të sigurisë.

Një funksion i vetëm, që Guardrail Agent-i dhe endpoint-et e mbrojtura
ta thërrasin njësoj. Rreshti shtohet në të njëjtin session si pjesa
tjetër e kërkesës dhe commit-ohet bashkë me të.
"""

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_event(
    db: Session,
    user_id: int | None,
    event_type: str,
    detail: str,
    rule: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        event_type=event_type,
        detail=detail,
        rule=rule,
    )

    db.add(entry)

    return entry


__all__ = ["record_event"]
