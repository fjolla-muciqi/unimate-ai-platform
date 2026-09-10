"""Roli i profesorit.

Deri para kësaj, `UserRole.PROFESSOR` ekzistonte në enum por asnjë
endpoint nuk e njihte: një profesor trajtohej saktësisht si student.
Këto teste mbrojnë të tri gjërat që e bëjnë rolin real —
1. profesori sheh lëndët që ligjëron, jo ato ku është i regjistruar,
2. nuk sheh studentët e një kolegu,
3. tools e chat-it degëzohen sipas rolit te JWT-ja, jo sipas asaj që
   kërkon modeli.
"""

import pytest
from sqlalchemy import select

from app.ai.agents.tools import SourceRegistry, ToolContext, execute_tool
from app.core.security import hash_password
from app.models.audit_log import AuditEvent, AuditLog
from app.models.course import Course
from app.models.document import Document, DocumentStatus
from app.models.faculty import Faculty
from app.models.professor import Professor
from app.models.user import User, UserRole
from tests.conftest import auth_headers, login


@pytest.fixture
def faculty(db_session) -> Faculty:
    record = Faculty(name="Fakulteti i Inxhinierisë Kompjuterike")

    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    return record


def make_professor(
    db_session,
    faculty,
    first_name: str,
    last_name: str,
    email: str,
) -> Professor:
    account = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=hash_password("Professor123!"),
        role=UserRole.PROFESSOR,
    )

    db_session.add(account)
    db_session.flush()

    professor = Professor(
        first_name=first_name,
        last_name=last_name,
        title="Prof. Dr.",
        email=email,
        office="B-210",
        consultation_hours="E martë 12:00-14:00",
        faculty_id=faculty.id,
        user_id=account.id,
    )

    db_session.add(professor)
    db_session.commit()
    db_session.refresh(professor)

    return professor


@pytest.fixture
def teaching(db_session, faculty, academic_data):
    """Dy profesorë, secili me lëndën e vet dhe studentët e vet.

    Kolegu ekziston që testet e izolimit të kenë përballë të dhëna
    reale të një profesori tjetër, jo një bazë bosh.
    """

    mine = make_professor(
        db_session,
        faculty,
        "Arben",
        "Hoxha",
        "arben@test.edu",
    )

    other = make_professor(
        db_session,
        faculty,
        "Elira",
        "Berisha",
        "elira@test.edu",
    )

    # Algoritmet i ligjëron Arbeni; studenti demo është i regjistruar.
    algorithms = academic_data["algorithms"]
    algorithms.professor_id = mine.id

    # Bazat e të Dhënave i ligjëron Elira.
    databases = academic_data["databases"]
    databases.professor_id = other.id

    # Orari dhe provimet vijnë nga `academic_data`: CS201 ka një
    # ligjëratë të hënën dhe një provim final pas tri javësh. Nuk i
    # dyfishojmë këtu, që numërimet të mbeten të parashikueshme.
    db_session.commit()

    return {"mine": mine, "other": other}


def professor_token(client) -> str:
    return login(client, "arben@test.edu", "Professor123!")


# --------------------------------------------------------------
# 1. Profesori sheh lëndët që ligjëron
# --------------------------------------------------------------


def test_professor_sees_the_courses_they_teach(
    client,
    teaching,
    academic_data,
):
    token = professor_token(client)

    response = client.get(
        "/api/professor/me/courses",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    courses = response.json()
    codes = {course["code"] for course in courses}

    assert codes == {"CS201"}
    assert courses[0]["enrolled_students"] == 1


def test_professor_dashboard_counts_their_own_load(
    client,
    teaching,
    academic_data,
):
    token = professor_token(client)

    body = client.get(
        "/api/professor/me/dashboard",
        headers=auth_headers(token),
    ).json()

    assert body["full_name"] == "Prof. Dr. Arben Hoxha"
    assert body["courses_taught"] == 1
    assert body["total_students"] == 1
    assert body["office"] == "B-210"
    assert len(body["upcoming_exams"]) == 1
    assert body["upcoming_exams"][0]["course_code"] == "CS201"


def test_professor_sees_students_of_their_courses(
    client,
    teaching,
    academic_data,
):
    token = professor_token(client)

    students = client.get(
        "/api/professor/me/students",
        headers=auth_headers(token),
    ).json()

    assert len(students) == 1
    assert students[0]["student_number"] == "2024-CS-001"
    assert students[0]["course_code"] == "CS201"


# --------------------------------------------------------------
# 2. Izolimi mes profesorëve
# --------------------------------------------------------------


def test_professor_cannot_see_a_colleagues_students(
    client,
    teaching,
    academic_data,
):
    """Kodi i lëndës vjen nga klienti; filtri i pronësisë rri sipër.

    CS202 e ligjëron kolegia, dhe studenti demo është i regjistruar
    edhe aty — pra të dhënat ekzistojnë. Duhet të kthehet listë bosh,
    jo studenti i tjetrit.
    """

    token = professor_token(client)

    students = client.get(
        "/api/professor/me/students?course_code=CS202",
        headers=auth_headers(token),
    ).json()

    assert students == []


def test_professor_endpoints_reject_students(
    client,
    student_user,
    academic_data,
):
    token = login(client, "arta@test.edu", "Student123!")

    for path in (
        "/api/professor/me/dashboard",
        "/api/professor/me/courses",
        "/api/professor/me/students",
    ):
        response = client.get(path, headers=auth_headers(token))

        assert response.status_code == 403, path


def test_student_endpoints_reject_professors(
    client,
    teaching,
    academic_data,
):
    token = professor_token(client)

    response = client.get(
        "/api/student/me/dashboard",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_professor_account_without_a_record_gets_a_clear_error(
    client,
    db_session,
    academic_data,
):
    """Roli pa rekord `Professor` duhet të thotë pse, jo të heshtë."""

    db_session.add(
        User(
            first_name="Pa",
            last_name="Rekord",
            email="orphan@test.edu",
            password_hash=hash_password("Professor123!"),
            role=UserRole.PROFESSOR,
        )
    )

    db_session.commit()

    token = login(client, "orphan@test.edu", "Professor123!")

    response = client.get(
        "/api/professor/me/courses",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert "professor record" in response.json()["detail"]


# --------------------------------------------------------------
# 3. Dokumentet: stafi ngarkon, secili menaxhon të vetat
# --------------------------------------------------------------


def test_professor_cannot_delete_a_document_they_did_not_upload(
    client,
    db_session,
    admin_user,
    teaching,
    academic_data,
):
    document = Document(
        title="Rregullorja e Studimeve",
        file_name="rregullorja.pdf",
        file_path="uploads/documents/rregullorja.pdf",
        document_type="REGULATION",
        uploaded_by=admin_user.id,
        status=DocumentStatus.INDEXED,
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    token = professor_token(client)

    response = client.delete(
        f"/api/documents/{document.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403

    db_session.refresh(document)
    assert document.is_active is True

    logged = db_session.scalars(
        select(AuditLog).where(
            AuditLog.event_type
            == AuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT
        )
    ).all()

    assert len(logged) == 1
    assert logged[0].rule == "document_ownership"


def test_professor_can_delete_their_own_document(
    client,
    db_session,
    teaching,
    academic_data,
):
    account = db_session.scalar(
        select(User).where(User.email == "arben@test.edu")
    )

    document = Document(
        title="Sllajdet e ligjëratës 1",
        file_name="ligjerata1.pdf",
        file_path="uploads/documents/ligjerata1.pdf",
        document_type="OTHER",
        uploaded_by=account.id,
        status=DocumentStatus.INDEXED,
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    token = professor_token(client)

    response = client.delete(
        f"/api/documents/{document.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    db_session.refresh(document)
    assert document.is_active is False


def test_students_still_cannot_upload_documents(
    client,
    student_user,
    academic_data,
):
    token = login(client, "arta@test.edu", "Student123!")

    response = client.post(
        "/api/documents/upload",
        headers=auth_headers(token),
        data={"title": "Provë", "document_type": "OTHER"},
        files={"file": ("prove.txt", b"tekst", "text/plain")},
    )

    assert response.status_code == 403


# --------------------------------------------------------------
# 4. Tools e chat-it degëzohen sipas rolit
# --------------------------------------------------------------


def professor_context(db_session, teaching):
    account = db_session.scalar(
        select(User).where(User.email == "arben@test.edu")
    )

    return ToolContext(
        db=db_session,
        user=account,
        profile=None,
        professor=teaching["mine"],
        sources=SourceRegistry(),
    )


def test_get_my_courses_returns_taught_courses_for_a_professor(
    db_session,
    teaching,
    academic_data,
):
    context = professor_context(db_session, teaching)

    answer = execute_tool("get_my_courses", {}, context)

    assert "ligjëron" in answer
    assert "CS201" in answer
    assert "CS202" not in answer


def test_get_my_students_is_scoped_to_the_professors_courses(
    db_session,
    teaching,
    academic_data,
):
    context = professor_context(db_session, teaching)

    answer = execute_tool(
        "get_my_students",
        {"course_code": "CS202"},
        context,
    )

    # CS202 i takon kolegies: as me kod të dhënë shprehimisht nuk del.
    assert "Arta" not in answer
    assert "CS202" in answer


def test_get_my_students_is_empty_for_a_student(
    db_session,
    student_user,
    academic_data,
):
    context = ToolContext(
        db=db_session,
        user=student_user,
        profile=academic_data["profile"],
        sources=SourceRegistry(),
    )

    answer = execute_tool("get_my_students", {}, context)

    assert "Vetëm profesorët" in answer


def test_a_professor_never_reaches_student_tool_branches(
    db_session,
    teaching,
    academic_data,
):
    """I njëjti emër tool-i, burim tjetër të dhënash.

    Ky është argumenti i sigurisë: modeli thërret `get_my_schedule`
    pa e ditur rolin, dhe sistemi e zgjedh degën.
    """

    context = professor_context(db_session, teaching)

    answer = execute_tool("get_my_schedule", {}, context)

    assert "ligjëratave të këtij profesori" in answer
    assert "studentit" not in answer
