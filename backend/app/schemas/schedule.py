from datetime import time

from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    course_id: int = Field(ge=1)
    # Bosh: ligjëratë e përbashkët për gjithë lëndën.
    group_id: int | None = None
    day_of_week: str = Field(min_length=2, max_length=20)
    start_time: time
    end_time: time
    room: str | None = Field(default=None, max_length=100)


class ScheduleUpdate(BaseModel):
    course_id: int | None = Field(default=None, ge=1)
    group_id: int | None = None
    day_of_week: str | None = Field(default=None, min_length=2, max_length=20)
    start_time: time | None = None
    end_time: time | None = None
    room: str | None = Field(default=None, max_length=100)


class ScheduleResponse(BaseModel):
    id: int
    course_id: int
    group_id: int | None = None
    day_of_week: str
    start_time: time
    end_time: time
    room: str | None

    model_config = {
        "from_attributes": True
    }