"""Skemat e panelit të administratorit."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminOverview(BaseModel):
    """Numrat bazë të platformës për faqen /admin."""

    total_students: int
    total_professors: int
    total_admins: int

    total_programs: int
    total_courses: int

    total_documents: int
    indexed_documents: int
    failed_documents: int
    pending_documents: int

    total_chunks: int

    # Aktiviteti i asistentit gjatë 30 ditëve të fundit.
    questions_last_30_days: int
    blocked_last_30_days: int


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    user_email: str | None = None
    event_type: str
    rule: str | None
    detail: str
    created_at: datetime


class AuditSummaryItem(BaseModel):
    event_type: str
    count: int
