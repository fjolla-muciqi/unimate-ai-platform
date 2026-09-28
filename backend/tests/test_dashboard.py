"""Dashboard-i i studentit.

Kërkesa e temës është që faqja kryesore të tregojë të dhëna reale,
jo placeholder. Këto teste e mbajnë atë premtim: numrat vijnë nga
regjistrimet e vërteta të studentit të kyçur.
"""

from datetime import time, timedelta

import pytest
from sqlalchemy import select

from app.models.deadline import Deadline
from app.models.document import Document, DocumentStatus
from app.models.enrollment import Enrollment
from app.models.notification import Notification
from app.models.schedule import Schedule
from tests.conftest import auth_headers, login
from app.core.clock import utcnow


@pytest.fixture
def dashboard(client, student_user, academic_data):
    token = login(client, "arta@test.edu", "Student123!")

    response = client.get(
        "/api/student/me/dashboard",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    return response.json()


def test_dashboard_reports_the_students_own_courses(dashboard):
    assert dashboard["active_courses"] == 2
    assert dashboard["student_number"] == "2024-CS-001"
    assert dashboard["program_name"] == "Shkenca Kompjuterike"
    assert dashboard["full_name"] == "Arta Krasniqi"


def test_dashboard_lists_only_upcoming_exams(dashboard):
    """Provimi i kaluar i `academic_data` nuk duhet të shfaqet."""

    exams = dashboard["upcoming_exams"]

    assert len(exams) == 1
    assert exams[0]["course_code"] == "CS201"
    assert exams[0]["days_until"] >= 0


def test_dashboard_progress_counts_only_completed_courses(
    client,
    db_session,
    student_user,
    academic_data,
):
    """Lëndët aktive nuk janë kredite të fituara."""

    token = login(client, "arta@test.edu", "Student123!")

    before = client.get(
        "/api/student/me/dashboard",
        headers=auth_headers(token),
    ).json()["progress"]

    assert before["earned_ects"] == 0
    assert before["in_progress_ects"] == 13
    assert before["required_ects"] == 180
    assert before["percent"] == 0.0

    enrollment = db_session.scalar(
        select(Enrollment).where(
            Enrollment.course_id == academic_data["algorithms"].id
        )
    )

    enrollment.status = "COMPLETED"
    db_session.commit()

    after = client.get(
        "/api/student/me/dashboard",
        headers=auth_headers(token),
    ).json()

    assert after["progress"]["earned_ects"] == 7
    assert after["progress"]["percent"] == round(7 / 180 * 100, 1)

    # Lënda e përfunduar del nga lëndët aktive.
    assert after["active_courses"] == 1


def test_dashboard_shows_todays_schedule_only(
    client,
    db_session,
    student_user,
    academic_data,
):
    today = utcnow().strftime("%A")

    db_session.add(
        Schedule(
            course_id=academic_data["algorithms"].id,
            day_of_week=today,
            start_time=time(16, 0),
            end_time=time(17, 30),
            room="C-303",
        )
    )

    db_session.commit()

    token = login(client, "arta@test.edu", "Student123!")

    body = client.get(
        "/api/student/me/dashboard",
        headers=auth_headers(token),
    ).json()

    assert body["today"] == today

    rooms = {slot["room"] for slot in body["today_schedule"]}

    assert "C-303" in rooms


def test_dashboard_counts_deadlines_notifications_and_documents(
    client,
    db_session,
    admin_user,
    student_user,
    academic_data,
):
    program_id = academic_data["program"].id

    db_session.add_all(
        [
            Deadline(
                title="Regjistrimi i lëndëve",
                deadline_type="REGISTRATION",
                due_date=utcnow() + timedelta(days=10),
                program_id=program_id,
            ),
            # E kaluar: nuk duhet numëruar.
            Deadline(
                title="Afat i skaduar",
                deadline_type="PAYMENT",
                due_date=utcnow() - timedelta(days=3),
                program_id=None,
            ),
            Notification(
                title="Njoftim i përgjithshëm",
                body="Vlen për të gjithë.",
                severity="INFO",
                created_by=admin_user.id,
                program_id=None,
            ),
            # Joaktiv: nuk duhet numëruar.
            Notification(
                title="Njoftim i mbyllur",
                body="Nuk vlen më.",
                severity="INFO",
                created_by=admin_user.id,
                program_id=None,
                is_active=False,
            ),
            Document(
                title="Rregullorja",
                file_name="rregullorja.pdf",
                file_path="uploads/documents/rregullorja.pdf",
                document_type="REGULATION",
                uploaded_by=admin_user.id,
                status=DocumentStatus.INDEXED,
            ),
            # Ende në përpunim: nuk i përgjigjet dot pyetjeve.
            Document(
                title="Syllabusi i ri",
                file_name="syllabus.pdf",
                file_path="uploads/documents/syllabus.pdf",
                document_type="SYLLABUS",
                uploaded_by=admin_user.id,
                status=DocumentStatus.PROCESSING,
            ),
        ]
    )

    db_session.commit()

    token = login(client, "arta@test.edu", "Student123!")

    body = client.get(
        "/api/student/me/dashboard",
        headers=auth_headers(token),
    ).json()

    assert body["upcoming_deadlines"] == 1
    assert body["active_notifications"] == 1
    assert body["available_documents"] == 1


def test_admin_has_no_student_dashboard(client, admin_user):
    token = login(client, "admin@test.edu", "Admin123!")

    response = client.get(
        "/api/student/me/dashboard",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
