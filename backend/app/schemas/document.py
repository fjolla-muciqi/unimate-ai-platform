from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    title: str
    description: str | None
    file_name: str
    document_type: str
    academic_year: str | None
    uploaded_by: int
    uploaded_at: datetime

    # Bosh = gjithë universitetit.
    faculty_id: int | None = None
    course_id: int | None = None
    is_active: bool

    # Gjendja e pipeline-it RAG: PENDING, PROCESSING, INDEXED, FAILED.
    status: str
    status_detail: str | None = None
    chunk_count: int = 0
    indexed_at: datetime | None = None

    model_config = {
        "from_attributes": True
    }


class DocumentScopeUpdate(BaseModel):
    """Kujt i përket dokumenti. Të dyja bosh: gjithë universitetit."""

    faculty_id: int | None = None
    course_id: int | None = None

    model_config = {"extra": "forbid"}
