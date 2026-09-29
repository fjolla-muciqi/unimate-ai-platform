"""Dokumentet sipas fakultetit dhe lëndës, dhe kufizimi i kërkimit."""

import pytest

from app.ai.rag import retriever
from app.ai.rag.scope import accessible_document_ids
from app.models.course import Course
from app.models.document import Document
from app.models.faculty import Faculty
from app.models.program import Program
from app.models.user import User
from tests.conftest import auth_headers, login
# Fixture-t e profesorëve, që testet e izolimit të kenë të dhëna reale.
from tests.test_professor import faculty, teaching  # noqa: F401


@pytest.fixture
def library(db_session, admin_user, faculty, teaching, academic_data):
    """Dokumente në të gjitha nivelet, për dy fakultete.

    Programi i studentit demo i përket `faculty`; `law` është një
    fakultet tjetër me programin dhe lëndën e vet.
    """

    academic_data["profile"].program.faculty_id = faculty.id

    law = Faculty(name="Fakulteti Juridik")
    db_session.add(law)
    db_session.flush()

    law_program = Program(
        name="Drejtësi",
        degree_level="BACHELOR",
        faculty_id=law.id,
    )
    db_session.add(law_program)
    db_session.flush()

    criminal_law = Course(
        code="LAW101",
        name="E drejta penale",
        ects=6,
        semester=1,
        program_id=law_program.id,
    )
    db_session.add(criminal_law)
    db_session.flush()

    def document(title, faculty_id=None, course_id=None):
        record = Document(
            title=title,
            file_name=f"{title}.pdf",
            file_path=f"uploads/documents/{title}.pdf",
            document_type="REGULATION",
            uploaded_by=admin_user.id,
            faculty_id=faculty_id,
            course_id=course_id,
        )
        db_session.add(record)
        return record

    docs = {
        "university": document("universiteti"),
        "my_faculty": document("fakulteti-im", faculty_id=faculty.id),
        "my_course": document(
            "syllabus-cs201",
            faculty_id=faculty.id,
            course_id=academic_data["algorithms"].id,
        ),
        "other_course_in_my_program": document(
            "syllabus-cs202",
            faculty_id=faculty.id,
            course_id=academic_data["databases"].id,
        ),
        "law_faculty": document("rregullorja-juridik", faculty_id=law.id),
        "law_course": document(
            "syllabus-law101", faculty_id=law.id, course_id=criminal_law.id
        ),
    }
    db_session.commit()

    return {"docs": docs, "law": law, "law_course": criminal_law}


def ids(library, *names):
    return {library["docs"][name].id for name in names}


# --- Kush çfarë mund të kërkojë ------------------------------------


def test_student_searches_university_own_faculty_and_program_courses(
    db_session, student_user, library
):
    allowed = set(accessible_document_ids(student_user, db_session))

    assert allowed == ids(
        library,
        "university",
        "my_faculty",
        "my_course",
        "other_course_in_my_program",
    )


def test_professor_searches_own_faculty_and_own_courses(
    db_session, library, teaching
):
    professor_account = db_session.get(User, teaching["mine"].user_id)

    allowed = set(accessible_document_ids(professor_account, db_session))

    # CS202 e ligjëron kolegia, prandaj syllabus-i i saj nuk përfshihet.
    assert allowed == ids(library, "university", "my_faculty", "my_course")


def test_admin_searches_everything(db_session, admin_user, library):
    assert accessible_document_ids(admin_user, db_session) is None


def test_empty_scope_returns_nothing_without_searching(
    db_session, monkeypatch
):
    def fail(**kwargs):
        raise AssertionError("Qdrant nuk duhej thirrur")

    monkeypatch.setattr(retriever, "semantic_search", fail)

    assert retriever.retrieve_context("rregullorja", db_session, document_ids=[]) == []


# --- Caktimi i fakultetit dhe lëndës -------------------------------


def test_course_sets_the_faculty_automatically(client, admin_user, library):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))
    document = library["docs"]["university"]

    response = client.patch(
        f"/api/documents/{document.id}",
        json={"course_id": library["law_course"].id},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["course_id"] == library["law_course"].id
    assert response.json()["faculty_id"] == library["law"].id


def test_course_and_faculty_must_agree(client, admin_user, library, faculty):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = client.patch(
        f"/api/documents/{library['docs']['university'].id}",
        json={"faculty_id": faculty.id, "course_id": library["law_course"].id},
        headers=headers,
    )

    assert response.status_code == 400


def test_professor_cannot_attach_documents_to_a_colleagues_course(
    client, db_session, library, teaching, academic_data
):
    headers = auth_headers(login(client, "arben@test.edu", "Professor123!"))

    own = client.post(
        "/api/documents/upload",
        data={
            "title": "Ushtrime",
            "document_type": "OTHER",
            "course_id": str(academic_data["databases"].id),
        },
        files={"file": ("ushtrime.txt", b"Ushtrime", "text/plain")},
        headers=headers,
    )

    # CS202 i përket kolegies: refuzohet para se skedari të ruhet.
    assert own.status_code == 403

    other_faculty = client.post(
        "/api/documents/upload",
        data={
            "title": "Ushtrime",
            "document_type": "OTHER",
            "faculty_id": str(library["law"].id),
        },
        files={"file": ("ushtrime.txt", b"Ushtrime", "text/plain")},
        headers=headers,
    )

    assert other_faculty.status_code == 403


def test_program_rejects_an_unknown_faculty(client, admin_user):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = client.post(
        "/api/programs",
        json={"name": "Program", "degree_level": "BACHELOR", "faculty_id": 999},
        headers=headers,
    )

    assert response.status_code == 404
