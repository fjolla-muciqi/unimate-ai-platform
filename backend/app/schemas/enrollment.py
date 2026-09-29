from datetime import datetime

from pydantic import BaseModel, Field


class EnrollmentCreate(BaseModel):
    student_profile_id: int = Field(ge=1)
    course_id: int = Field(ge=1)
    # Bosh: grupi me më pak studentë, nëse lënda ka grupe.
    group_id: int | None = None
    status: str = Field(default="ACTIVE", min_length=2, max_length=50)


class EnrollmentUpdate(BaseModel):
    group_id: int | None = None
    status: str | None = Field(default=None, min_length=2, max_length=50)


class EnrollmentResponse(BaseModel):
    id: int
    student_profile_id: int
    course_id: int
    group_id: int | None = None
    status: str
    enrolled_at: datetime

    model_config = {
        "from_attributes": True
    }