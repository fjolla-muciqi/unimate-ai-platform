"""Skemat e dashboard-it të studentit.

Një përgjigje e vetme për të gjithë faqen. Frontend-i më parë
bashkonte pesë kërkesa dhe e llogariste progresin vetë; llogaritja e
kreditave i takon backend-it, i cili i ka rregullat e programit.
"""

from datetime import datetime, time

from pydantic import BaseModel


class DashboardExam(BaseModel):
    course_code: str
    course_name: str
    exam_type: str
    exam_date: datetime
    room: str | None

    # Ditë deri te provimi; negativja nuk ndodh sepse kthehen
    # vetëm provimet e ardhshme.
    days_until: int


class DashboardSlot(BaseModel):
    course_code: str
    course_name: str
    start_time: time
    end_time: time
    room: str | None


class DashboardProgress(BaseModel):
    """Progresi në kredite ECTS."""

    earned_ects: int
    in_progress_ects: int
    required_ects: int

    # Përqindja e programit e përfunduar, 0-100 me një presje.
    percent: float


class DashboardResponse(BaseModel):
    full_name: str
    student_number: str
    program_name: str
    academic_year: int
    semester: int

    active_courses: int

    # Dita e sotme në anglisht, si te `Schedule.day_of_week`.
    today: str
    today_schedule: list[DashboardSlot]

    upcoming_exams: list[DashboardExam]

    upcoming_deadlines: int
    active_notifications: int
    available_documents: int

    progress: DashboardProgress


class ProfessorCourse(BaseModel):
    """Një lëndë që ligjëron profesori, me ngarkesën e saj."""

    id: int
    code: str
    name: str
    ects: int
    semester: int
    enrolled_students: int


class ProfessorStudent(BaseModel):
    student_profile_id: int
    full_name: str
    email: str
    student_number: str
    academic_year: int
    course_code: str
    course_name: str


class ProfessorDashboard(BaseModel):
    """Faqja kryesore e profesorit.

    Pasqyra e `DashboardResponse`, por e ndërtuar mbi lëndët që
    profesori ligjëron, jo mbi regjistrimet e tij.
    """

    full_name: str
    title: str | None
    faculty_name: str | None
    office: str | None
    consultation_hours: str | None

    courses_taught: int
    total_students: int

    today: str
    today_schedule: list[DashboardSlot]
    upcoming_exams: list[DashboardExam]

    # Dokumentet që ka ngarkuar vetë ky profesor.
    my_documents: int
