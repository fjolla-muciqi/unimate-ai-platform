"""Menaxhimi i llogarive: përdoruesit nga admini, fjalëkalimi, profili."""

from sqlalchemy import select

from app.models.audit_log import AuditEvent, AuditLog
from tests.conftest import auth_headers, login


# --- Përdoruesit (admin) -------------------------------------------


def test_admin_lists_users_with_role_filter_and_search(
    client, admin_user, student_user
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    everyone = client.get("/api/admin/users", headers=headers)
    assert everyone.status_code == 200
    assert {user["email"] for user in everyone.json()} == {
        admin_user.email,
        student_user.email,
    }

    students = client.get(
        "/api/admin/users", params={"role": "STUDENT"}, headers=headers
    )
    assert [user["email"] for user in students.json()] == [
        student_user.email
    ]

    # Kërkimi nuk dallon shkronjat e mëdha nga të voglat.
    found = client.get(
        "/api/admin/users", params={"search": "krasn"}, headers=headers
    )
    assert [user["email"] for user in found.json()] == [student_user.email]


def test_student_cannot_list_users(client, student_user):
    headers = auth_headers(
        login(client, student_user.email, "Student123!")
    )

    assert client.get("/api/admin/users", headers=headers).status_code == 403


def test_deactivated_user_can_no_longer_log_in(
    client, db_session, admin_user, student_user
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = client.patch(
        f"/api/admin/users/{student_user.id}",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    blocked = client.post(
        "/api/auth/login",
        data={"username": student_user.email, "password": "Student123!"},
    )
    assert blocked.status_code == 403

    # Veprimi gjurmohet, por nuk numërohet si kërkesë e bllokuar.
    event = db_session.scalar(
        select(AuditLog).where(
            AuditLog.event_type == AuditEvent.USER_STATUS_CHANGED
        )
    )
    assert event is not None
    assert student_user.email in event.detail

    overview = client.get("/api/admin/overview", headers=headers).json()
    assert overview["blocked_last_30_days"] == 0

    client.patch(
        f"/api/admin/users/{student_user.id}",
        json={"is_active": True},
        headers=headers,
    )
    assert login(client, student_user.email, "Student123!")


def test_admin_cannot_deactivate_themselves(client, admin_user):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = client.patch(
        f"/api/admin/users/{admin_user.id}",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 400


def test_role_cannot_be_changed_through_user_update(
    client, admin_user, student_user
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = client.patch(
        f"/api/admin/users/{student_user.id}",
        json={"is_active": True, "role": "ADMIN"},
        headers=headers,
    )

    assert response.status_code == 422


# --- Fjalëkalimi ---------------------------------------------------


def test_change_password_replaces_the_old_one(client, student_user):
    headers = auth_headers(
        login(client, student_user.email, "Student123!")
    )

    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "Student123!",
            "new_password": "NewStudent456!",
        },
        headers=headers,
    )

    assert response.status_code == 204

    old = client.post(
        "/api/auth/login",
        data={"username": student_user.email, "password": "Student123!"},
    )
    assert old.status_code == 401
    assert login(client, student_user.email, "NewStudent456!")


def test_change_password_requires_the_current_password(
    client, student_user
):
    headers = auth_headers(
        login(client, student_user.email, "Student123!")
    )

    wrong = client.post(
        "/api/auth/change-password",
        json={"current_password": "Gabim123!", "new_password": "NewPass456!"},
        headers=headers,
    )
    assert wrong.status_code == 400

    same = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "Student123!",
            "new_password": "Student123!",
        },
        headers=headers,
    )
    assert same.status_code == 400

    short = client.post(
        "/api/auth/change-password",
        json={"current_password": "Student123!", "new_password": "short"},
        headers=headers,
    )
    assert short.status_code == 422


# --- Profili i studentit -------------------------------------------


def test_student_reads_and_updates_their_language(
    client, student_user, academic_data
):
    headers = auth_headers(
        login(client, student_user.email, "Student123!")
    )

    profile = client.get("/api/student/me/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["program_name"] == "Shkenca Kompjuterike"

    updated = client.patch(
        "/api/student/me/profile",
        json={"preferred_language": "en"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["preferred_language"] == "en"


def test_student_cannot_change_official_profile_fields(
    client, student_user, academic_data
):
    headers = auth_headers(
        login(client, student_user.email, "Student123!")
    )

    unsupported = client.patch(
        "/api/student/me/profile",
        json={"preferred_language": "de"},
        headers=headers,
    )
    assert unsupported.status_code == 422

    official = client.patch(
        "/api/student/me/profile",
        json={"preferred_language": "en", "semester": 8},
        headers=headers,
    )
    assert official.status_code == 422


def test_profile_endpoint_is_for_students_only(client, admin_user):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    assert (
        client.get("/api/student/me/profile", headers=headers).status_code
        == 403
    )


# --- Plotësimi i profilit pas regjistrimit -------------------------


def register_student(client) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Blerta",
            "last_name": "Gashi",
            "email": "blerta@test.edu",
            "password": "Student123!",
        },
    )
    assert response.status_code in (200, 201), response.text

    return auth_headers(login(client, "blerta@test.edu", "Student123!"))


def test_new_student_completes_profile_and_is_enrolled(
    client, academic_data
):
    headers = register_student(client)
    program_id = academic_data["profile"].program_id

    # Para profilit, faqet e studentit nuk kanë të dhëna.
    assert (
        client.get("/api/student/me/profile", headers=headers).status_code
        == 404
    )

    created = client.post(
        "/api/student/me/profile",
        json={"program_id": program_id, "academic_year": 2, "semester": 3},
        headers=headers,
    )

    assert created.status_code == 201, created.text
    assert created.json()["preferred_language"] == "sq"

    # Regjistrohet vetë në lëndët e semestrit 3 (CS201, CS202), jo në CS301.
    courses = client.get("/api/student/me/courses", headers=headers).json()
    assert sorted(course["code"] for course in courses) == ["CS201", "CS202"]

    assert (
        client.get("/api/student/me/dashboard", headers=headers).status_code
        == 200
    )


def test_profile_can_be_completed_only_once(client, academic_data):
    headers = register_student(client)
    payload = {
        "program_id": academic_data["profile"].program_id,
        "academic_year": 1,
        "semester": 1,
    }

    assert (
        client.post("/api/student/me/profile", json=payload, headers=headers).status_code
        == 201
    )
    assert (
        client.post("/api/student/me/profile", json=payload, headers=headers).status_code
        == 409
    )


def test_profile_rejects_impossible_year_and_semester(client, academic_data):
    headers = register_student(client)
    program_id = academic_data["profile"].program_id

    wrong_semester = client.post(
        "/api/student/me/profile",
        json={"program_id": program_id, "academic_year": 1, "semester": 5},
        headers=headers,
    )
    assert wrong_semester.status_code == 400

    # Programi i fixture-it zgjat tre vite.
    too_late = client.post(
        "/api/student/me/profile",
        json={"program_id": program_id, "academic_year": 4, "semester": 7},
        headers=headers,
    )
    assert too_late.status_code == 400

    chosen_number = client.post(
        "/api/student/me/profile",
        json={
            "program_id": program_id,
            "academic_year": 1,
            "semester": 1,
            "student_number": "2024-CS-001",
        },
        headers=headers,
    )
    assert chosen_number.status_code == 422


def test_deleting_a_notification_removes_it_from_the_admin_list(
    client, admin_user
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    created = client.post(
        "/api/notifications",
        json={"title": "Njoftim prove", "body": "Tekst"},
        headers=headers,
    ).json()

    assert (
        client.delete(
            f"/api/notifications/{created['id']}", headers=headers
        ).status_code
        == 204
    )

    remaining = client.get("/api/notifications", headers=headers).json()
    assert created["id"] not in [item["id"] for item in remaining]
