from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    title: str
    description: str | None
    file_name: str
    file_path: str
    document_type: str
    academic_year: str | None
    uploaded_by: int
    uploaded_at: datetime
    is_active: bool

    model_config = {
        "from_attributes": True
    }