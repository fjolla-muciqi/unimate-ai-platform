"""Skemat për entitetet akademike të shtuara sipas temës:
fakultete, profesorë, parakushte, afate dhe njoftime."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FacultyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None


class FacultyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None


class FacultyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


class ProfessorCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    title: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    office: str | None = Field(default=None, max_length=100)
    consultation_hours: str | None = None
    faculty_id: int | None = None

    # Me fjalëkalim krijohet edhe llogaria e kyçjes (kërkon email).
    password: str | None = Field(default=None, min_length=8, max_length=128)


class ProfessorUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    title: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    office: str | None = Field(default=None, max_length=100)
    consultation_hours: str | None = None
    faculty_id: int | None = None

    # Krijon llogarinë nëse mungon, përndryshe e rivendos fjalëkalimin.
    password: str | None = Field(default=None, min_length=8, max_length=128)


class ProfessorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    full_name: str
    title: str | None
    email: str | None
    office: str | None
    consultation_hours: str | None
    faculty_id: int | None
    user_id: int | None = None
    has_account: bool = False
    account_active: bool | None = None


class PrerequisiteCreate(BaseModel):
    prerequisite_id: int = Field(ge=1)


class PrerequisiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    prerequisite_id: int


class DeadlineCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    deadline_type: str = Field(default="OTHER", max_length=50)
    due_date: datetime
    program_id: int | None = None


class DeadlineUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    deadline_type: str | None = Field(default=None, max_length=50)
    due_date: datetime | None = None
    program_id: int | None = None


class DeadlineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    deadline_type: str
    due_date: datetime
    program_id: int | None


class NotificationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    body: str = Field(min_length=1)
    severity: str = Field(default="INFO", max_length=20)
    program_id: int | None = None


class NotificationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    body: str | None = None
    severity: str | None = Field(default=None, max_length=20)
    program_id: int | None = None
    is_active: bool | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    severity: str
    program_id: int | None
    created_at: datetime
    is_active: bool
