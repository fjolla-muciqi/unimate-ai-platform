from datetime import datetime

from pydantic import BaseModel, Field


class ExamCreate(BaseModel):
    course_id: int = Field(ge=1)
    exam_type: str = Field(min_length=2, max_length=50)
    exam_date: datetime
    room: str | None = Field(default=None, max_length=100)


class ExamUpdate(BaseModel):
    course_id: int | None = Field(default=None, ge=1)
    exam_type: str | None = Field(default=None, min_length=2, max_length=50)
    exam_date: datetime | None = None
    room: str | None = Field(default=None, max_length=100)


class ExamResponse(BaseModel):
    id: int
    course_id: int
    exam_type: str
    exam_date: datetime
    room: str | None

    model_config = {
        "from_attributes": True
    }