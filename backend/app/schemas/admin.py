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


class AdminUserResponse(BaseModel):
    """Një llogari te lista e përdoruesve të administratorit."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class AdminUserUpdate(BaseModel):
    """Administratori mund vetëm ta aktivizojë ose çaktivizojë një llogari.

    Roli mungon me qëllim: ai lidhet me të dhënat akademike
    (`StudentProfile` për studentin, `Professor` për profesorin), dhe
    një ndryshim i thjeshtë roli do t'i linte ato të paqëndrueshme.
    """

    is_active: bool

    model_config = ConfigDict(extra="forbid")
