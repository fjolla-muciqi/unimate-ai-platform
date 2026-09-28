from typing import Literal

from pydantic import BaseModel, Field


class StudentProfileCreate(BaseModel):
    user_id: int = Field(ge=1)
    student_number: str = Field(min_length=2, max_length=50)
    program_id: int = Field(ge=1)
    academic_year: int = Field(ge=1, le=10)
    semester: int = Field(ge=1, le=12)
    preferred_language: str = Field(default="sq", min_length=2, max_length=10)


class StudentProfileUpdate(BaseModel):
    student_number: str | None = Field(default=None, min_length=2, max_length=50)
    program_id: int | None = Field(default=None, ge=1)
    academic_year: int | None = Field(default=None, ge=1, le=10)
    semester: int | None = Field(default=None, ge=1, le=12)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=10)


class StudentProfileResponse(BaseModel):
    id: int
    user_id: int
    student_number: str
    program_id: int
    academic_year: int
    semester: int
    preferred_language: str

    model_config = {
        "from_attributes": True
    }

class MyProfileResponse(BaseModel):
    """Profili akademik siç e sheh vetë studenti."""

    full_name: str
    email: str
    student_number: str
    program_name: str | None
    academic_year: int
    semester: int
    preferred_language: str


class MyProfileUpdate(BaseModel):
    """Studenti ndryshon vetëm gjuhën. Numrin, programin dhe vitin
    i menaxhon administrata, sepse prekin regjistrimet zyrtare."""

    preferred_language: Literal["sq", "en"]

    model_config = {"extra": "forbid"}
