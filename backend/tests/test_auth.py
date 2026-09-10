from tests.conftest import auth_headers, login


def test_register_creates_student_by_default(client):
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Blerim",
            "last_name": "Gashi",
            "email": "blerim@test.edu",
            "password": "Password123!",
        },
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["email"] == "blerim@test.edu"
    assert body["role"] == "STUDENT"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client, student_user):
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Dikush",
            "last_name": "Tjeter",
            "email": student_user.email,
            "password": "Password123!",
        },
    )

    assert response.status_code == 409


def test_login_returns_token_and_me_returns_user(client, student_user):
    token = login(client, student_user.email, "Student123!")

    response = client.get("/api/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["email"] == student_user.email


def test_login_rejects_wrong_password(client, student_user):
    response = client.post(
        "/api/auth/login",
        data={"username": student_user.email, "password": "gabim"},
    )

    assert response.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_admin_route_blocks_student(client, student_user):
    token = login(client, student_user.email, "Student123!")

    response = client.get(
        "/api/auth/admin-test",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_admin_route_allows_admin(client, admin_user):
    token = login(client, admin_user.email, "Admin123!")

    response = client.get(
        "/api/auth/admin-test",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
