"""Paneli i administratorit.

Numrat bazë të platformës dhe regjistri i ngjarjeve të sigurisë.
Metrikat e asistentit (agjentët, latenca, pyetjet pa përgjigje) vijnë
nga `/api/analytics/overview`; këtu qëndron ajo që ka të bëjë me
gjendjen e platformës dhe me Guardrail Agent-in.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core.database import get_db
from app.core.teaching import teacher_of_enrollment
from app.core.security import require_admin
from app.models.audit_log import AuditEvent, AuditLog, BLOCKING_EVENTS
from app.models.course import Course
from app.models.document import Document, DocumentStatus
from app.models.enrollment import Enrollment
from app.models.course_group import CourseGroup
from app.models.document_chunk import DocumentChunk
from app.models.message import Message
from app.models.program import Program
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminOverview,
    AdminStudentCourse,
    AdminStudentDetail,
    AdminStudentRow,
    AdminUserResponse,
    AdminUserUpdate,
    AuditLogResponse,
    AuditSummaryItem,
)
from app.core.clock import utcnow


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
    since = utcnow() - timedelta(days=ACTIVITY_WINDOW_DAYS)

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
        .where(
            AuditLog.created_at >= since,
            AuditLog.event_type.in_(BLOCKING_EVENTS),
        )
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


@router.get(
    "/users",
    response_model=list[AdminUserResponse],
)
def list_users(
    role: UserRole | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = select(User)

    if role is not None:
        query = query.where(User.role == role)

    if search:
        pattern = f"%{search.strip()}%"

        query = query.where(
            or_(
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
            )
        )

    return db.scalars(
        query.order_by(User.role, User.last_name, User.first_name)
    ).all()


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserResponse,
)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Përdoruesi nuk u gjet.",
        )

    # Një admin që çaktivizon veten mbyllet jashtë sistemit, dhe nëse
    # është i vetmi, askush nuk mund ta rikthejë nga paneli.
    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nuk mund ta çaktivizosh llogarinë tënde.",
        )

    if user.is_active != payload.is_active:
        user.is_active = payload.is_active

        record_event(
            db,
            user_id=current_user.id,
            event_type=AuditEvent.USER_STATUS_CHANGED,
            detail=(
                f"{user.email} u "
                f"{'aktivizua' if payload.is_active else 'çaktivizua'}."
            ),
        )

        db.commit()
        db.refresh(user)

    return user


def student_row(
    user: User,
    profile: StudentProfile | None,
    program: Program | None,
    db: Session,
) -> AdminStudentRow:
    course_count = (
        db.scalar(
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.student_profile_id == profile.id,
                Enrollment.status == "ACTIVE",
            )
        )
        if profile
        else 0
    )

    return AdminStudentRow(
        user_id=user.id,
        full_name=f"{user.first_name} {user.last_name}",
        email=user.email,
        is_active=user.is_active,
        student_profile_id=profile.id if profile else None,
        student_number=profile.student_number if profile else None,
        program_id=profile.program_id if profile else None,
        program_name=program.name if program else None,
        study_year=profile.study_year if profile else None,
        semester=profile.semester if profile else None,
        course_count=course_count or 0,
    )


@router.get(
    "/students",
    response_model=list[AdminStudentRow],
)
def list_students(
    search: str | None = Query(default=None, max_length=100),
    program_id: int | None = Query(default=None),
    study_year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = (
        select(User, StudentProfile, Program)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .outerjoin(Program, Program.id == StudentProfile.program_id)
        .where(User.role == UserRole.STUDENT)
    )

    if search:
        pattern = f"%{search.strip()}%"

        query = query.where(
            or_(
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                StudentProfile.student_number.ilike(pattern),
            )
        )

    if program_id is not None:
        query = query.where(StudentProfile.program_id == program_id)

    if study_year is not None:
        query = query.where(StudentProfile.study_year == study_year)

    rows = db.execute(query.order_by(User.last_name, User.first_name)).all()

    return [student_row(user, profile, program, db) for user, profile, program in rows]


@router.get(
    "/students/{user_id}",
    response_model=AdminStudentDetail,
)
def get_student(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.get(User, user_id)

    if user is None or user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studenti nuk u gjet.",
        )

    profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    program = db.get(Program, profile.program_id) if profile else None

    courses = []

    if profile is not None:
        rows = db.execute(
            select(Enrollment, Course)
            .join(Course, Course.id == Enrollment.course_id)
            .where(Enrollment.student_profile_id == profile.id)
            .order_by(Course.semester, Course.code)
        ).all()

        for enrollment, course in rows:
            group = (
                db.get(CourseGroup, enrollment.group_id)
                if enrollment.group_id
                else None
            )
            teacher = teacher_of_enrollment(enrollment, course, db)

            courses.append(
                AdminStudentCourse(
                    enrollment_id=enrollment.id,
                    course_id=course.id,
                    code=course.code,
                    name=course.name,
                    semester=course.semester,
                    ects=course.ects,
                    group_id=enrollment.group_id,
                    group_name=group.name if group else None,
                    teacher_name=teacher.full_name if teacher else None,
                    status=enrollment.status,
                    period_label=(
                        enrollment.period.label if enrollment.period else None
                    ),
                )
            )

    return AdminStudentDetail(
        **student_row(user, profile, program, db).model_dump(),
        courses=courses,
    )
