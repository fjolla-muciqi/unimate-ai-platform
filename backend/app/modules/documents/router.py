from pathlib import Path
import shutil
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core import teaching
from app.core.database import get_db
from app.core.security import (
    get_current_user,
    require_staff,
)
from app.models.audit_log import AuditEvent
from app.models.course import Course
from app.models.document import Document, DocumentStatus
from app.models.faculty import Faculty
from app.models.professor import Professor
from app.models.program import Program
from app.models.user import User, UserRole
from app.schemas.document import DocumentResponse, DocumentScopeUpdate
from app.ai.rag.ingestion import ingest_document_in_background


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)


UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}


def owned_document(
    document_id: int,
    current_user: User,
    db: Session,
) -> Document:
    """Dokumenti, nëse ky përdorues ka të drejtë ta menaxhojë.

    Administratori i menaxhon të gjitha. Profesori vetëm ato që ka
    ngarkuar vetë — përndryshe, sapo ngarkimi u hap për stafin, çdo
    profesor do të mund të fshinte rregulloret e universitetit.
    """

    document = db.get(Document, document_id)

    if document is None or not document.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if current_user.role == UserRole.ADMIN:
        return document

    if document.uploaded_by != current_user.id:
        record_event(
            db=db,
            user_id=current_user.id,
            event_type=AuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
            detail=(
                f"Tentativë menaxhimi e dokumentit {document_id} "
                "të ngarkuar nga një përdorues tjetër."
            ),
            rule="document_ownership",
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage documents you uploaded.",
        )

    return document


def resolve_scope(
    faculty_id: int | None,
    course_id: int | None,
    current_user: User,
    db: Session,
) -> tuple[int | None, int | None]:
    """Kujt i përket dokumenti: (fakulteti, lënda).

    Me lëndë, fakulteti merret nga programi i saj, që të dy të mos
    bien ndesh. Profesori mund t'ia caktojë dokumentin vetëm një lënde
    që ligjëron ose fakultetit të vet; pa këtë, do të mund të vendoste
    materiale në lëndët e kolegëve.
    """

    if course_id is not None:
        course = db.get(Course, course_id)

        if course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lënda nuk u gjet.",
            )

        program = db.get(Program, course.program_id)
        course_faculty = program.faculty_id if program else None

        if faculty_id is not None and faculty_id != course_faculty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lënda nuk i përket fakultetit të zgjedhur.",
            )

        faculty_id = course_faculty

    elif faculty_id is not None and db.get(Faculty, faculty_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fakulteti nuk u gjet.",
        )

    if current_user.role == UserRole.PROFESSOR and (
        faculty_id is not None or course_id is not None
    ):
        professor = db.scalar(
            select(Professor).where(Professor.user_id == current_user.id)
        )

        allowed = professor is not None and (
            teaches_course(professor, course_id, db)
            if course_id is not None
            else faculty_id == professor.faculty_id
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Mund të vendosësh dokumente vetëm në lëndët që "
                    "ligjëron ose në fakultetin tënd."
                ),
            )

    return faculty_id, course_id


def teaches_course(professor: Professor, course_id: int, db: Session) -> bool:
    """Koordinatori ose profesori i një grupi të lëndës."""

    return db.scalar(
        select(Course.id).where(
            Course.id == course_id,
            teaching.teaches_course(professor.id),
        )
    ) is not None


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    document_type: str = Form(...),
    description: str | None = Form(None),
    academic_year: str | None = Form(None),
    faculty_id: int | None = Form(None),
    course_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    # Kontrollohet para ruajtjes së skedarit, që një kërkesë e refuzuar
    # të mos lërë skedar jetim në disk.
    faculty_id, course_id = resolve_scope(
        faculty_id, course_id, current_user, db
    )

    original_name = file.filename or "document"

    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOCX and TXT files are allowed.",
        )

    unique_name = f"{uuid.uuid4()}{extension}"

    file_path = UPLOAD_DIR / unique_name

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    finally:
        file.file.close()

    document = Document(
        title=title,
        description=description,
        file_name=original_name,
        # Gjithmonë me "/": një shteg Windows-i nuk hapet në Linux,
        # dhe API-ja mund të ekzekutohet në të dyja.
        file_path=file_path.as_posix(),
        document_type=document_type,
        academic_year=academic_year,
        faculty_id=faculty_id,
        course_id=course_id,
        uploaded_by=current_user.id,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Ekstraktimi, chunking-u dhe embeddings zgjatin shumë sekonda:
    # ngarkuesi e merr përgjigjen menjëherë dhe ndjek statusin.
    background_tasks.add_task(
        ingest_document_in_background,
        document.id,
    )

    return document


@router.post(
    "/{document_id}/reindex",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def reindex_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Ri-indekson një dokument: chunks e vjetër zëvendësohen.

    Përdoret kur një ingestim ka dështuar ose kur skedari është
    zëvendësuar. Profesori mund të ri-indeksojë vetëm dokumentet e
    veta; administratori të gjitha.
    """

    document = owned_document(document_id, current_user, db)

    document.status = DocumentStatus.PENDING
    document.status_detail = None

    db.commit()
    db.refresh(document)

    background_tasks.add_task(
        ingest_document_in_background,
        document.id,
    )

    return document


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Document)
        .where(Document.is_active.is_(True))
        .order_by(Document.uploaded_at.desc())
    ).all()


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)

    if not document or not document.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
)
def update_document_scope(
    document_id: int,
    payload: DocumentScopeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Ndryshon kujt i përket dokumenti, pa ri-indeksim.

    Filtri i kërkimit lexon fakultetin dhe lëndën nga PostgreSQL në
    çdo pyetje, prandaj vektorët në Qdrant mbeten të vlefshëm.
    """

    document = owned_document(document_id, current_user, db)

    document.faculty_id, document.course_id = resolve_scope(
        payload.faculty_id, payload.course_id, current_user, db
    )

    db.commit()
    db.refresh(document)

    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Fshirje e butë. Profesori vetëm të vetat, admini të gjitha."""

    document = owned_document(document_id, current_user, db)

    document.is_active = False

    db.commit()

    return None