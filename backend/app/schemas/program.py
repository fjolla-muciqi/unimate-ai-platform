from pydantic import BaseModel, Field


class ProgramCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    degree_level: str = Field(min_length=2, max_length=100)
    specialization: str | None = Field(default=None, max_length=200)
    total_ects: int = Field(default=180, ge=1)
    ects_is_official: bool = False
    duration_years: int = Field(default=3, ge=1)
    description: str | None = None
    faculty_id: int | None = None


class ProgramUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    degree_level: str | None = Field(default=None, min_length=2, max_length=100)
    specialization: str | None = Field(default=None, max_length=200)
    total_ects: int | None = Field(default=None, ge=1)
    ects_is_official: bool | None = None
    duration_years: int | None = Field(default=None, ge=1)
    description: str | None = None
    faculty_id: int | None = None


class ProgramResponse(BaseModel):
    id: int
    name: str
    degree_level: str
    specialization: str | None
    total_ects: int
    ects_is_official: bool
    duration_years: int
    description: str | None
    faculty_id: int | None

    model_config = {
        "from_attributes": True
    }