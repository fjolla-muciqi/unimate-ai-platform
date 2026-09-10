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
from app.core.database import get_db
from app.core.security import (
    get_current_user,
    require_staff,
)
from app.models.audit_log import AuditEvent
from app.models.document import Document, DocumentStatus
from app.models.user import User, UserRole
from app.schemas.document import DocumentResponse
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
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
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
        file_path=str(file_path),
        document_type=document_type,
        academic_year=academic_year,
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