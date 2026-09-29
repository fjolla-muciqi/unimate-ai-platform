"""Administratori krijon profesorë me llogari kyçjeje."""

from sqlalchemy import select

from app.models.course_group import CourseGroup
from app.models.user import User, UserRole
from tests.conftest import auth_headers, login


def admin_headers(client, admin_user):
    return auth_headers(login(client, admin_user.email, "Admin123!"))


def create(client, headers, **fields):
    payload = {
        "first_name": "Drita",
        "last_name": "Hasani",
        "title": "Prof. Dr.",
        "email": "drita.hasani@test.edu",
        **fields,
    }

    return client.post("/api/professors", json=payload, headers=headers)


def test_professor_created_with_password_can_log_in(client, admin_user):
    response = create(client, admin_headers(client, admin_user), password="Profesor123!")

    assert response.status_code == 201
    assert response.json()["has_account"] is True

    headers = auth_headers(login(client, "drita.hasani@test.edu", "Profesor123!"))
    me = client.get("/api/auth/me", headers=headers).json()

    assert me["role"] == UserRole.PROFESSOR.value
    assert client.get("/api/professor/me/courses", headers=headers).status_code == 200


def test_professor_without_password_has_no_account(client, admin_user):
    response = create(client, admin_headers(client, admin_user))

    assert response.status_code == 201
    assert response.json()["has_account"] is False


def test_account_needs_an_email_that_is_not_taken(client, admin_user, student_user):
    headers = admin_headers(client, admin_user)

    without_email = create(client, headers, email=None, password="Profesor123!")
    assert without_email.status_code == 400

    taken = create(client, headers, email=student_user.email, password="Profesor123!")
    assert taken.status_code == 409


def test_password_on_update_creates_or_resets_the_account(client, admin_user):
    headers = admin_headers(client, admin_user)
    professor = create(client, headers).json()

    created = client.put(
        f"/api/professors/{professor['id']}",
        json={"password": "Fillestar123!"},
        headers=headers,
    )
    assert created.json()["has_account"] is True
    assert login(client, "drita.hasani@test.edu", "Fillestar123!")

    client.put(
        f"/api/professors/{professor['id']}",
        json={"password": "IRi456789!"},
        headers=headers,
    )
    assert login(client, "drita.hasani@test.edu", "IRi456789!")


def test_email_change_follows_to_the_account(client, db_session, admin_user):
    headers = admin_headers(client, admin_user)
    professor = create(client, headers, password="Profesor123!").json()

    client.put(
        f"/api/professors/{professor['id']}",
        json={"email": "d.hasani@test.edu", "last_name": "Hasani-Krasniqi"},
        headers=headers,
    )

    account = db_session.get(User, professor["user_id"])
    db_session.refresh(account)

    assert account.email == "d.hasani@test.edu"
    assert account.last_name == "Hasani-Krasniqi"


def test_deleting_a_professor_deactivates_the_account_and_frees_groups(
    client, db_session, admin_user, academic_data
):
    headers = admin_headers(client, admin_user)
    professor = create(client, headers, password="Profesor123!").json()

    group = CourseGroup(
        course_id=academic_data["algorithms"].id,
        name="Grupi C",
        professor_id=professor["id"],
    )
    db_session.add(group)
    db_session.commit()

    response = client.delete(f"/api/professors/{professor['id']}", headers=headers)
    assert response.status_code == 204

    db_session.refresh(group)
    account = db_session.get(User, professor["user_id"])
    db_session.refresh(account)

    assert group.professor_id is None
    assert account.is_active is False

    blocked = client.post(
        "/api/auth/login",
        data={"username": "drita.hasani@test.edu", "password": "Profesor123!"},
    )
    assert blocked.status_code == 403


def test_students_do_not_see_account_details(client, admin_user, student_user):
    create(client, admin_headers(client, admin_user), password="Profesor123!")

    headers = auth_headers(login(client, student_user.email, "Student123!"))
    professors = client.get("/api/professors", headers=headers).json()

    assert professors[0]["has_account"] is False
    assert professors[0]["user_id"] is None


def test_only_admins_create_professors(client, student_user, db_session):
    headers = auth_headers(login(client, student_user.email, "Student123!"))

    assert create(client, headers, password="Profesor123!").status_code == 403
    assert db_session.scalar(
        select(User).where(User.email == "drita.hasani@test.edu")
    ) is None
