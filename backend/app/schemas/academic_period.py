from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Term = Literal["WINTER", "SUMMER"]

ACADEMIC_YEAR_PATTERN = r"^\d{4}/\d{4}$"


class AcademicPeriodCreate(BaseModel):
    academic_year: str = Field(pattern=ACADEMIC_YEAR_PATTERN)
    term: Term
    start_date: date
    end_date: date
    is_current: bool = False

    @model_validator(mode="after")
    def check_dates(self):
        start, end = self.academic_year.split("/")

        if int(end) != int(start) + 1:
            raise ValueError("Viti akademik duhet të jetë si 2026/2027.")

        if self.end_date <= self.start_date:
            raise ValueError("Data e mbarimit duhet të jetë pas fillimit.")

        return self


class AcademicPeriodUpdate(BaseModel):
    academic_year: str | None = Field(default=None, pattern=ACADEMIC_YEAR_PATTERN)
    term: Term | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class AcademicPeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_year: str
    term: Term
    start_date: date
    end_date: date
    is_current: bool
    label: str
