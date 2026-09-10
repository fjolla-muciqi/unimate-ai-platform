"""Paneli i administratorit.

Numrat bazë të platformës dhe regjistri i ngjarjeve të sigurisë.
Metrikat e asistentit (agjentët, latenca, pyetjet pa përgjigje) vijnë
nga `/api/analytics/overview`; këtu qëndron ajo që ka të bëjë me
gjendjen e platformës dhe me Guardrail Agent-in.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.message import Message
from app.models.program import Program
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminOverview,
    AuditLogResponse,
    AuditSummaryItem,
)


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
)


ACTIVITY_WINDOW_DAYS = 30


def count_users(db: Session, role: UserRole) -> int:
    return db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.role == role)
    ) or 0


def count_documents(db: Session, status: str | None = None) -> int:
    query = (
        select(func.count())
        .select_from(Document)
        .where(Document.is_active.is_(True))
    )

    if status is not None:
        query = query.where(Document.status == status)

    return db.scalar(query) or 0


@router.get(
    "/overview",
    response_model=AdminOverview,
)
def admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    since = datetime.utcnow() - timedelta(days=ACTIVITY_WINDOW_DAYS)

    questions = db.scalar(
        select(func.count())
        .select_from(Message)
        .where(
            Message.role == "user",
            Message.created_at >= since,
        )
    ) or 0

    blocked = db.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.created_at >= since)
    ) or 0

    return AdminOverview(
        total_students=count_users(db, UserRole.STUDENT),
        total_professors=count_users(db, UserRole.PROFESSOR),
        total_admins=count_users(db, UserRole.ADMIN),
        total_programs=db.scalar(
            select(func.count()).select_from(Program)
        ) or 0,
        total_courses=db.scalar(
            select(func.count()).select_from(Course)
        ) or 0,
        total_documents=count_documents(db),
        indexed_documents=count_documents(
            db, DocumentStatus.INDEXED
        ),
        failed_documents=count_documents(db, DocumentStatus.FAILED),
        pending_documents=(
            count_documents(db, DocumentStatus.PENDING)
            + count_documents(db, DocumentStatus.PROCESSING)
        ),
        total_chunks=db.scalar(
            select(func.count()).select_from(DocumentChunk)
        ) or 0,
        questions_last_30_days=questions,
        blocked_last_30_days=blocked,
    )


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
)
def list_audit_logs(
    event_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Ngjarjet e fundit të sigurisë, më e reja e para."""

    query = (
        select(AuditLog, User.email)
        .outerjoin(User, User.id == AuditLog.user_id)
        .order_by(AuditLog.id.desc())
        .limit(limit)
    )

    if event_type is not None:
        query = query.where(AuditLog.event_type == event_type)

    return [
        AuditLogResponse(
            id=entry.id,
            user_id=entry.user_id,
            user_email=email,
            event_type=entry.event_type,
            rule=entry.rule,
            detail=entry.detail,
            created_at=entry.created_at,
        )
        for entry, email in db.execute(query).all()
    ]


@router.get(
    "/audit-logs/summary",
    response_model=list[AuditSummaryItem],
)
def audit_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Sa herë u aktivizua secili lloj ngjarjeje."""

    rows = db.execute(
        select(AuditLog.event_type, func.count())
        .group_by(AuditLog.event_type)
        .order_by(func.count().desc())
    ).all()

    return [
        AuditSummaryItem(event_type=event_type, count=count)
        for event_type, count in rows
    ]
