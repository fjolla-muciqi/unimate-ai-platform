"""Periudhat akademike dhe ndarja e katër koncepteve.

Viti i studimit (1-3), semestri i kurrikulës (1-6), viti akademik
("2026/2027") dhe periudha (dimërore/verore) janë fusha të ndara.
"""

from datetime import date

from sqlalchemy import select

from app.core.periods import period_for_semester, study_year_for_semester
from app.models.academic_period import SUMMER, WINTER, AcademicPeriod
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.program import Program
from tests.conftest import auth_headers, login


def add_year(db_session, academic_year="2026/2027", current_term=WINTER):
    start = int(academic_year[:4])
    periods = {
        WINTER: AcademicPeriod(
            academic_year=academic_year,
            term=WINTER,
            start_date=date(start, 10, 1),
            end_date=date(start + 1, 1, 31),
            is_current=current_term == WINTER,
        ),
        SUMMER: AcademicPeriod(
            academic_year=academic_year,
            term=SUMMER,
            start_date=date(start + 1, 2, 22),
            end_date=date(start + 1, 6, 30),
            is_current=current_term == SUMMER,
        ),
    }

    db_session.add_all(periods.values())
    db_session.commit()

    return periods


def test_study_year_follows_curriculum_semester():
    assert [study_year_for_semester(n) for n in range(1, 7)] == [
        1, 1, 2, 2, 3, 3,
    ]


def test_odd_semesters_fall_in_winter_even_in_summer(db_session):
    periods = add_year(db_session)

    assert period_for_semester(3, db_session).id == periods[WINTER].id
    assert period_for_semester(4, db_session).id == periods[SUMMER].id


def test_no_current_period_means_no_period(db_session):
    assert period_for_semester(3, db_session) is None


def test_admin_creates_period_and_only_one_is_current(
    client, db_session, admin_user
):
    periods = add_year(db_session)
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = client.post(
        "/api/academic-periods",
        json={
            "academic_year": "2027/2028",
            "term": "WINTER",
            "start_date": "2027-10-01",
            "end_date": "2028-01-31",
            "is_current": True,
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["label"] == "2027/2028, periudha dimërore"

    db_session.expire_all()
    current = db_session.scalars(
        select(AcademicPeriod).where(AcademicPeriod.is_current.is_(True))
    ).all()

    assert [period.academic_year for period in current] == ["2027/2028"]
    assert db_session.get(AcademicPeriod, periods[WINTER].id).is_current is False


def test_period_validation(client, admin_user):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    not_consecutive = client.post(
        "/api/academic-periods",
        json={
            "academic_year": "2026/2028",
            "term": "WINTER",
            "start_date": "2026-10-01",
            "end_date": "2027-01-31",
        },
        headers=headers,
    )
    ends_before_start = client.post(
        "/api/academic-periods",
        json={
            "academic_year": "2026/2027",
            "term": "SUMMER",
            "start_date": "2027-06-30",
            "end_date": "2027-02-01",
        },
        headers=headers,
    )

    assert not_consecutive.status_code == 422
    assert ends_before_start.status_code == 422


def test_duplicate_period_conflicts(client, db_session, admin_user):
    add_year(db_session)
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = client.post(
        "/api/academic-periods",
        json={
            "academic_year": "2026/2027",
            "term": "WINTER",
            "start_date": "2026-10-01",
            "end_date": "2027-01-31",
        },
        headers=headers,
    )

    assert response.status_code == 409


def test_student_reads_but_cannot_create_periods(
    client, db_session, student_user
):
    add_year(db_session)
    headers = auth_headers(login(client, student_user.email, "Student123!"))

    assert len(client.get("/api/academic-periods", headers=headers).json()) == 2

    response = client.post(
        "/api/academic-periods",
        json={
            "academic_year": "2030/2031",
            "term": "WINTER",
            "start_date": "2030-10-01",
            "end_date": "2031-01-31",
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_enrollment_gets_the_period_of_its_semester(
    client, db_session, admin_user, academic_data
):
    periods = add_year(db_session)
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    summer_course = Course(
        code="CS204",
        name="Rrjetat",
        ects=5,
        semester=4,
        program_id=academic_data["program"].id,
    )
    db_session.add(summer_course)
    db_session.commit()

    response = client.post(
        "/api/enrollments",
        json={
            "student_profile_id": academic_data["profile"].id,
            "course_id": summer_course.id,
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["period_id"] == periods[SUMMER].id


def test_enrollment_rejects_unknown_period(
    client, db_session, admin_user, academic_data
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = client.post(
        "/api/enrollments",
        json={
            "student_profile_id": academic_data["profile"].id,
            "course_id": academic_data["unenrolled"].id,
            "period_id": 999,
        },
        headers=headers,
    )

    assert response.status_code == 400


def test_onboarding_enrolls_in_the_period_and_profile_shows_it(
    client, db_session, student_user
):
    periods = add_year(db_session)
    program = Program(
        name="Shkenca Kompjuterike dhe Inxhinieri",
        degree_level="BACHELOR",
        total_ects=180,
        duration_years=3,
    )
    db_session.add(program)
    db_session.flush()
    db_session.add(
        Course(
            code="SKI-301", name="Shkenca Kompjuterike 2",
            ects=5, semester=3, program_id=program.id,
        )
    )
    db_session.commit()

    headers = auth_headers(login(client, student_user.email, "Student123!"))

    response = client.post(
        "/api/student/me/profile",
        json={"program_id": program.id, "study_year": 2, "semester": 3},
        headers=headers,
    )

    assert response.status_code == 201, response.text

    profile = response.json()

    assert profile["study_year"] == 2
    assert profile["semester"] == 3
    assert profile["academic_year"] == "2026/2027"
    assert profile["period_label"] == "2026/2027, periudha dimërore"
    assert profile["ects_is_official"] is False

    enrollment = db_session.scalar(select(Enrollment))

    assert enrollment.period_id == periods[WINTER].id

    dashboard = client.get("/api/student/me/dashboard", headers=headers).json()

    assert dashboard["period_label"] == "2026/2027, periudha dimërore"
