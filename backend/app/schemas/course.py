from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    ects: int = Field(ge=1, le=30)
    semester: int = Field(ge=1, le=12)
    program_id: int = Field(ge=1)
    syllabus: str | None = None
    professor_id: int | None = None


class CourseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    ects: int | None = Field(default=None, ge=1, le=30)
    semester: int | None = Field(default=None, ge=1, le=12)
    program_id: int | None = Field(default=None, ge=1)
    syllabus: str | None = None
    professor_id: int | None = None


class CourseResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    ects: int
    semester: int
    program_id: int
    syllabus: str | None
    professor_id: int | None

    model_config = {
        "from_attributes": True
    }


class StudentCourseResponse(CourseResponse):
    """Lënda siç e sheh studenti: me grupin dhe profesorin e grupit."""

    group_id: int | None = None
    group_name: str | None = None
    teacher_name: str | None = None
