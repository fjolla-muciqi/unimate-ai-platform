"""Grupet e lëndëve: e njëjta lëndë, profesorë të ndryshëm."""

from datetime import time

import pytest
from sqlalchemy import select

from app.ai.agents import academic_agent
from app.ai.rag.scope import accessible_document_ids
from app.core.security import hash_password
from app.models.course_group import CourseGroup
from app.models.document import Document
from app.models.enrollment import Enrollment
from app.models.schedule import Schedule
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from tests.conftest import auth_headers, login
from tests.test_professor import faculty, teaching  # noqa: F401


@pytest.fixture
def groups(db_session, teaching, academic_data):
    """CS201 në dy grupe: A me Arbenin, B me Elirën.

    Studenti demo është te Grupi A; Blerta te Grupi B. Secili grup ka
    edhe ushtrimet e veta, përveç ligjëratës së përbashkët të hënën.
    """

    algorithms = academic_data["algorithms"]

    group_a = CourseGroup(
        course_id=algorithms.id, name="Grupi A", professor_id=teaching["mine"].id
    )
    group_b = CourseGroup(
        course_id=algorithms.id, name="Grupi B", professor_id=teaching["other"].id
    )
    db_session.add_all([group_a, group_b])
    db_session.flush()

    demo_enrollment = db_session.scalar(
        select(Enrollment).where(
            Enrollment.student_profile_id == academic_data["profile"].id,
            Enrollment.course_id == algorithms.id,
        )
    )
    demo_enrollment.group_id = group_a.id

    blerta = User(
        first_name="Blerta",
        last_name="Gashi",
        email="blerta@test.edu",
        password_hash=hash_password("Student123!"),
        role=UserRole.STUDENT,
    )
    db_session.add(blerta)
    db_session.flush()

    blerta_profile = StudentProfile(
        user_id=blerta.id,
        student_number="2024-CS-002",
        program_id=academic_data["program"].id,
        academic_year=2,
        semester=3,
    )
    db_session.add(blerta_profile)
    db_session.flush()

    db_session.add(
        Enrollment(
            student_profile_id=blerta_profile.id,
            course_id=algorithms.id,
            group_id=group_b.id,
        )
    )

    db_session.add_all(
        [
            Schedule(
                course_id=algorithms.id, group_id=group_a.id,
                day_of_week="Tuesday", start_time=time(11, 0),
                end_time=time(12, 30), room="Lab-1",
            ),
            Schedule(
                course_id=algorithms.id, group_id=group_b.id,
                day_of_week="Wednesday", start_time=time(13, 0),
                end_time=time(14, 30), room="Lab-2",
            ),
        ]
    )
    db_session.commit()

    return {"a": group_a, "b": group_b, "blerta": blerta}


def admin_headers(client, admin_user):
    return auth_headers(login(client, admin_user.email, "Admin123!"))


# --- Profesori -----------------------------------------------------


def test_each_professor_sees_only_the_students_of_their_group(client, groups):
    arben = auth_headers(login(client, "arben@test.edu", "Professor123!"))
    elira = auth_headers(login(client, "elira@test.edu", "Professor123!"))

    arben_students = client.get(
        "/api/professor/me/students", params={"course_code": "CS201"}, headers=arben
    ).json()
    elira_students = client.get(
        "/api/professor/me/students", params={"course_code": "CS201"}, headers=elira
    ).json()

    assert [s["full_name"] for s in arben_students] == ["Arta Krasniqi"]
    assert [s["group_name"] for s in arben_students] == ["Grupi A"]
    assert [s["full_name"] for s in elira_students] == ["Blerta Gashi"]


def test_a_group_professor_teaches_the_course(client, groups):
    elira = auth_headers(login(client, "elira@test.edu", "Professor123!"))

    courses = client.get("/api/professor/me/courses", headers=elira).json()
    by_code = {course["code"]: course for course in courses}

    # CS202 e koordinon; CS201 e jep vetëm te Grupi B, me një studente.
    assert set(by_code) == {"CS201", "CS202"}
    assert by_code["CS201"]["enrolled_students"] == 1


def test_professor_schedule_skips_the_colleagues_group(client, groups):
    arben = auth_headers(login(client, "arben@test.edu", "Professor123!"))

    days = {
        slot["day_of_week"]
        for slot in client.get("/api/professor/me/schedule", headers=arben).json()
    }

    # E hëna e përbashkët dhe e marta e Grupit A, jo e mërkura e Grupit B.
    assert days == {"Monday", "Tuesday"}


def test_group_professor_searches_course_documents(
    db_session, groups, teaching, academic_data, admin_user
):
    syllabus = Document(
        title="Syllabus CS201",
        file_name="cs201.pdf",
        file_path="uploads/documents/cs201.pdf",
        document_type="SYLLABUS",
        uploaded_by=admin_user.id,
        course_id=academic_data["algorithms"].id,
    )
    db_session.add(syllabus)
    db_session.commit()

    elira = db_session.get(User, teaching["other"].user_id)

    assert syllabus.id in accessible_document_ids(elira, db_session)


# --- Studenti ------------------------------------------------------


def test_student_sees_the_teacher_and_schedule_of_their_group(client, groups):
    headers = auth_headers(login(client, "blerta@test.edu", "Student123!"))

    courses = client.get("/api/student/me/courses", headers=headers).json()
    assert courses[0]["group_name"] == "Grupi B"
    assert courses[0]["teacher_name"].endswith("Elira Berisha")

    days = {
        slot["day_of_week"]
        for slot in client.get("/api/student/me/schedule", headers=headers).json()
    }
    assert days == {"Monday", "Wednesday"}


def test_assistant_names_the_teacher_of_the_students_group(
    db_session, groups, academic_data
):
    answer = academic_agent.answer_courses(academic_data["profile"], db_session)

    assert "Grupi A" in answer
    assert "Arben Hoxha" in answer
    assert "Elira" not in answer.split("CS201")[1].split("\n")[0]


# --- Administratori ------------------------------------------------


def test_admin_manages_groups(client, admin_user, groups, academic_data, teaching):
    headers = admin_headers(client, admin_user)
    algorithms = academic_data["algorithms"]

    listed = client.get(
        "/api/course-groups", params={"course_id": algorithms.id}, headers=headers
    ).json()
    assert [(g["name"], g["student_count"]) for g in listed] == [
        ("Grupi A", 1),
        ("Grupi B", 1),
    ]

    created = client.post(
        "/api/course-groups",
        json={"course_id": algorithms.id, "name": "Grupi C", "professor_id": teaching["mine"].id},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["professor_name"].endswith("Arben Hoxha")

    duplicate = client.post(
        "/api/course-groups",
        json={"course_id": algorithms.id, "name": "Grupi C"},
        headers=headers,
    )
    assert duplicate.status_code == 409


def test_deleting_a_group_keeps_the_enrollment_without_group(
    client, db_session, admin_user, groups
):
    headers = admin_headers(client, admin_user)

    response = client.delete(f"/api/course-groups/{groups['b'].id}", headers=headers)
    assert response.status_code == 204

    enrollment = db_session.scalar(
        select(Enrollment).join(StudentProfile).where(
            StudentProfile.user_id == groups["blerta"].id
        )
    )
    db_session.refresh(enrollment)

    assert enrollment.group_id is None
    # Orari i veçantë i grupit shkoi me të.
    assert db_session.scalar(
        select(Schedule).where(Schedule.day_of_week == "Wednesday")
    ) is None


def test_enrollment_group_must_belong_to_the_course(
    client, admin_user, groups, academic_data
):
    headers = admin_headers(client, admin_user)
    blerta_profile_id = client.get(
        f"/api/admin/students/{groups['blerta'].id}", headers=headers
    ).json()["student_profile_id"]

    wrong = client.post(
        "/api/enrollments",
        json={
            "student_profile_id": blerta_profile_id,
            "course_id": academic_data["databases"].id,
            "group_id": groups["a"].id,
        },
        headers=headers,
    )
    assert wrong.status_code == 400


def test_enrollment_without_group_goes_to_the_least_filled_group(
    client, db_session, admin_user, groups, academic_data
):
    headers = admin_headers(client, admin_user)
    algorithms = academic_data["algorithms"]

    # A dhe B kanë nga një student; C s'ka vend (kapaciteti 0).
    extra = CourseGroup(course_id=algorithms.id, name="Grupi C", capacity=0)
    db_session.add(extra)
    db_session.commit()

    newcomer = client.post(
        "/api/auth/register",
        json={"first_name": "Dren", "last_name": "Hoti", "email": "dren@test.edu", "password": "Student123!"},
    )
    assert newcomer.status_code in (200, 201)

    student_headers = auth_headers(login(client, "dren@test.edu", "Student123!"))
    client.post(
        "/api/student/me/profile",
        json={"program_id": academic_data["program"].id, "academic_year": 1, "semester": 1},
        headers=student_headers,
    )

    detail = client.get(
        f"/api/admin/students/{newcomer.json()['id']}", headers=headers
    ).json()

    enrolled = client.post(
        "/api/enrollments",
        json={"student_profile_id": detail["student_profile_id"], "course_id": algorithms.id},
        headers=headers,
    )

    assert enrolled.status_code == 201
    # Barazim mes A dhe B: fiton i pari sipas emrit.
    assert enrolled.json()["group_id"] == groups["a"].id


def test_admin_lists_students_including_those_without_profile(
    client, admin_user, groups, student_user
):
    headers = admin_headers(client, admin_user)

    client.post(
        "/api/auth/register",
        json={"first_name": "Pa", "last_name": "Profil", "email": "pa.profil@test.edu", "password": "Student123!"},
    )

    rows = {row["email"]: row for row in client.get("/api/admin/students", headers=headers).json()}

    assert rows[student_user.email]["course_count"] == 2
    assert rows["pa.profil@test.edu"]["student_profile_id"] is None

    found = client.get("/api/admin/students", params={"search": "2024-CS-002"}, headers=headers).json()
    assert [row["email"] for row in found] == ["blerta@test.edu"]


def test_admin_student_detail_shows_group_and_teacher(
    client, admin_user, groups, student_user
):
    headers = admin_headers(client, admin_user)

    detail = client.get(f"/api/admin/students/{student_user.id}", headers=headers).json()
    by_code = {course["code"]: course for course in detail["courses"]}

    assert by_code["CS201"]["group_name"] == "Grupi A"
    assert by_code["CS201"]["teacher_name"].endswith("Arben Hoxha")


def test_students_endpoints_are_admin_only(client, student_user):
    headers = auth_headers(login(client, student_user.email, "Student123!"))

    assert client.get("/api/admin/students", headers=headers).status_code == 403
    assert client.post(
        "/api/course-groups", json={"course_id": 1, "name": "X"}, headers=headers
    ).status_code == 403


def test_onboarding_balances_new_students_across_groups(
    client, db_session, groups, academic_data
):
    # CS201 është në semestrin 3; A dhe B kanë nga një student.
    for name in ["Ema", "Fisnik"]:
        email = f"{name.lower()}@test.edu"
        client.post(
            "/api/auth/register",
            json={"first_name": name, "last_name": "Test", "email": email, "password": "Student123!"},
        )
        client.post(
            "/api/student/me/profile",
            json={"program_id": academic_data["program"].id, "academic_year": 2, "semester": 3},
            headers=auth_headers(login(client, email, "Student123!")),
        )

    sizes = [
        len(db_session.scalars(select(Enrollment).where(Enrollment.group_id == group.id)).all())
        for group in (groups["a"], groups["b"])
    ]

    # Dy të rinjtë shpërndahen, një në secilin grup.
    assert sizes == [2, 2]
