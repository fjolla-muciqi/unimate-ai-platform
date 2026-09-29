from pydantic import BaseModel, ConfigDict, Field


class CourseGroupCreate(BaseModel):
    course_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=50)
    professor_id: int | None = None
    capacity: int | None = Field(default=None, ge=1)


class CourseGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    professor_id: int | None = None
    capacity: int | None = Field(default=None, ge=1)


class CourseGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    name: str
    professor_id: int | None
    capacity: int | None

    # Për tabelën e adminit, pa kërkesa shtesë.
    course_code: str | None = None
    professor_name: str | None = None
    student_count: int = 0
