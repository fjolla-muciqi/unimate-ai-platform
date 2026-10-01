from typing import Literal

from pydantic import BaseModel, Field


class StudentProfileCreate(BaseModel):
    user_id: int = Field(ge=1)
    student_number: str = Field(min_length=2, max_length=50)
    program_id: int = Field(ge=1)
    study_year: int = Field(ge=1, le=10)
    semester: int = Field(ge=1, le=12)
    preferred_language: str = Field(default="sq", min_length=2, max_length=10)


class StudentProfileUpdate(BaseModel):
    student_number: str | None = Field(default=None, min_length=2, max_length=50)
    program_id: int | None = Field(default=None, ge=1)
    study_year: int | None = Field(default=None, ge=1, le=10)
    semester: int | None = Field(default=None, ge=1, le=12)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=10)


class StudentProfileResponse(BaseModel):
    id: int
    user_id: int
    student_number: str
    program_id: int
    study_year: int
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
    study_year: int
    semester: int
    preferred_language: str

    # Katër koncepte të ndara: viti i studimit (1-3), semestri i
    # kurrikulës (1-6), viti akademik ("2026/2027") dhe periudha.
    faculty_name: str | None = None
    degree_level: str | None = None
    academic_year: str | None = None
    period_label: str | None = None

    # False: ECTS-të e lëndëve janë demonstrative, jo zyrtare.
    ects_is_official: bool = False


class MyProfileUpdate(BaseModel):
    """Studenti ndryshon vetëm gjuhën. Numrin, programin dhe vitin
    i menaxhon administrata, sepse prekin regjistrimet zyrtare."""

    preferred_language: Literal["sq", "en"]

    model_config = {"extra": "forbid"}


class MyProfileCreate(BaseModel):
    """Plotësimi i profilit nga vetë studenti, një herë pas regjistrimit.

    Numri i studentit nuk vjen nga studenti: e cakton sistemi, që të
    mos mund të zgjidhet numri i dikujt tjetër.
    """

    program_id: int = Field(ge=1)
    study_year: int = Field(ge=1, le=10)
    semester: int = Field(ge=1, le=12)
    preferred_language: Literal["sq", "en"] = "sq"

    model_config = {"extra": "forbid"}
