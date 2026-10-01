from dataclasses import dataclass
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
from sqlalchemy import or_, select
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
from app.models.course_group import CourseGroup
from app.models.document import Document, DocumentStatus
from app.models.faculty import Faculty
from app.models.professor import Professor
from app.models.program import Program
from app.models.user import User, UserRole
from app.schemas.document import (
    DocumentResponse,
    DocumentScopeUpdate,
    MaterialType,
)
from app.ai.rag.scope import accessible_document_ids
from app.modules.documents.naming import (
    MAX_WEEK,
    material_title,
    parse_material_type,
    parse_week,
)
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


@dataclass
class Scope:
    """Kujt i përket një dokument. Të gjitha bosh: gjithë universitetit."""

    faculty_id: int | None = None
    course_id: int | None = None
    group_id: int | None = None


def resolve_scope(
    faculty_id: int | None,
    course_id: int | None,
    current_user: User,
    db: Session,
    group_id: int | None = None,
) -> Scope:
    """Fakulteti, lënda dhe grupi i dokumentit, të kontrolluar.

    Grupi përcakton lëndën, dhe lënda fakultetin, që të mos bien ndesh.
    Profesori mund t'ia caktojë dokumentin vetëm një lënde që ligjëron,
    grupit të vet (ose çdo grupi të lëndës që koordinon), ose fakultetit
    të vet; pa këtë, do të mund të vendoste materiale te kolegët.
    """

    group = None

    if group_id is not None:
        group = db.get(CourseGroup, group_id)

        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grupi nuk u gjet.",
            )

        if course_id is not None and course_id != group.course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grupi nuk i përket lëndës së zgjedhur.",
            )

        course_id = group.course_id

    course = None

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
        faculty_id is not None or course is not None
    ):
        professor = db.scalar(
            select(Professor).where(Professor.user_id == current_user.id)
        )

        if professor is None:
            allowed = False
        elif group is not None:
            allowed = professor.id in (group.professor_id, course.professor_id)
        elif course is not None:
            allowed = teaches_course(professor, course.id, db)
        else:
            allowed = faculty_id == professor.faculty_id

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Mund të vendosësh dokumente vetëm në lëndët dhe "
                    "grupet që ligjëron, ose në fakultetin tënd."
                ),
            )

    return Scope(faculty_id=faculty_id, course_id=course_id, group_id=group_id)


def teaches_course(professor: Professor, course_id: int, db: Session) -> bool:
    """Koordinatori ose profesori i një grupi të lëndës."""

    return db.scalar(
        select(Course.id).where(
            Course.id == course_id,
            teaching.teaches_course(professor.id),
        )
    ) is not None


def store_upload(
    file: UploadFile,
    *,
    title: str,
    document_type: str,
    scope: Scope,
    current_user: User,
    db: Session,
    description: str | None = None,
    academic_year: str | None = None,
    week: int | None = None,
    material_type: str | None = None,
) -> Document:
    """Ruan skedarin dhe krijon rreshtin; ingestimi niset nga thirrësi."""

    original_name = file.filename or "document"
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{original_name}: lejohen vetëm PDF, DOCX dhe TXT.",
        )

    file_path = UPLOAD_DIR / f"{uuid.uuid4()}{extension}"

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
        faculty_id=scope.faculty_id,
        course_id=scope.course_id,
        group_id=scope.group_id,
        week=week,
        material_type=material_type,
        uploaded_by=current_user.id,
    )

    db.add(document)

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
    faculty_id: int | None = Form(None),
    course_id: int | None = Form(None),
    group_id: int | None = Form(None),
    week: int | None = Form(None, ge=1, le=MAX_WEEK),
    material_type: MaterialType | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    # Kontrollohet para ruajtjes së skedarit, që një kërkesë e refuzuar
    # të mos lërë skedar jetim në disk.
    scope = resolve_scope(faculty_id, course_id, current_user, db, group_id)

    document = store_upload(
        file,
        title=title,
        document_type=document_type,
        scope=scope,
        current_user=current_user,
        db=db,
        description=description,
        academic_year=academic_year,
        week=week,
        material_type=material_type,
    )

    db.commit()
    db.refresh(document)

    # Ekstraktimi, chunking-u dhe embeddings zgjatin shumë sekonda:
    # ngarkuesi e merr përgjigjen menjëherë dhe ndjek statusin.
    background_tasks.add_task(ingest_document_in_background, document.id)

    return document


@router.post(
    "/upload-materials",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
def upload_materials(
    background_tasks: BackgroundTasks,
    course_id: int = Form(...),
    group_id: int | None = Form(None),
    material_type: MaterialType | None = Form(None),
    academic_year: str | None = Form(None),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    """Ngarkon materialet e një lënde njëherësh, p.sh. 10 javë ligjërata.

    Java dhe lloji lexohen nga emri i çdo skedari ("Java03_Ligjerata.pdf");
    `material_type` i dhënë këtu vlen për skedarët ku emri s'e tregon.
    Titulli ndërtohet si "SKI-305 · Java 3 · Ligjëratë · Grupi A".
    """

    scope = resolve_scope(None, course_id, current_user, db, group_id)
    course = db.get(Course, scope.course_id)
    group = db.get(CourseGroup, group_id) if group_id else None

    # Të gjithë skedarët kontrollohen para se të ruhet ndonjëri.
    for file in files:
        if Path(file.filename or "").suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file.filename}: lejohen vetëm PDF, DOCX dhe TXT.",
            )

    documents = []

    for file in files:
        name = file.filename or "material"
        week = parse_week(name)
        kind = parse_material_type(name) or material_type

        documents.append(
            store_upload(
                file,
                title=material_title(
                    course.code, week, kind, group.name if group else None, name
                ),
                document_type="COURSE_MATERIAL",
                scope=scope,
                current_user=current_user,
                db=db,
                academic_year=academic_year,
                week=week,
                material_type=kind,
            )
        )

    db.commit()

    for document in documents:
        db.refresh(document)
        background_tasks.add_task(ingest_document_in_background, document.id)

    return sorted(
        documents, key=lambda document: (document.week or 99, document.title)
    )


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
    """Dokumentet që përdoruesi mund t'i përdorë te asistenti.

    Studenti sheh ato të universitetit, të fakultetit dhe të lëndëve të
    programit të vet, dhe materialet e grupeve të tij; profesori ato të
    fakultetit dhe të lëndëve që jep, plus çdo dokument që ka ngarkuar
    vetë; administratori të gjitha.
    """

    query = select(Document).where(Document.is_active.is_(True))
    allowed = accessible_document_ids(current_user, db)

    if allowed is not None:
        query = query.where(
            or_(
                Document.id.in_(allowed),
                Document.uploaded_by == current_user.id,
            )
        )

    return db.scalars(query.order_by(Document.uploaded_at.desc())).all()


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

    scope = resolve_scope(
        payload.faculty_id,
        payload.course_id,
        current_user,
        db,
        payload.group_id,
    )

    document.faculty_id = scope.faculty_id
    document.course_id = scope.course_id
    document.group_id = scope.group_id
    document.week = payload.week
    document.material_type = payload.material_type

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