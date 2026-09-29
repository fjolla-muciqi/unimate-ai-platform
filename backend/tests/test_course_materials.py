"""Materialet e lëndëve: ligjërata javore sipas grupit (profesorit)."""

import pytest
from sqlalchemy import select

from app.ai.agents import tools
from app.ai.agents.tools import SourceRegistry, ToolContext, execute_tool
from app.ai.rag.scope import accessible_document_ids
from app.models.document import Document
from app.models.user import User
from app.modules.documents import router as documents_router
from tests.conftest import auth_headers, login
from tests.test_groups import groups  # noqa: F401
from tests.test_professor import faculty, teaching  # noqa: F401


@pytest.fixture(autouse=True)
def isolated_uploads(monkeypatch, tmp_path):
    """Skedarët shkojnë te një dosje e përkohshme, dhe ingestimi në sfond
    (që hap sesionin e bazës reale) nuk niset gjatë testeve."""

    monkeypatch.setattr(documents_router, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        documents_router, "ingest_document_in_background", lambda document_id: None
    )


def upload_materials(client, headers, course_id, group_id=None, names=()):
    data = {"course_id": str(course_id)}

    if group_id is not None:
        data["group_id"] = str(group_id)

    return client.post(
        "/api/documents/upload-materials",
        data=data,
        files=[("files", (name, b"Pemet binare dhe AVL.", "text/plain")) for name in names],
        headers=headers,
    )


def test_bulk_upload_reads_week_and_type_from_file_names(
    client, admin_user, groups, academic_data
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = upload_materials(
        client,
        headers,
        academic_data["algorithms"].id,
        groups["a"].id,
        ["Java02_Ushtrime.txt", "Java01_Ligjerata.txt"],
    )

    assert response.status_code == 201
    documents = response.json()

    # Të renditura sipas javës, me titull, javë, lloj dhe grup.
    assert [d["title"] for d in documents] == [
        "CS201 · Java 1 · Ligjëratë · Grupi A",
        "CS201 · Java 2 · Ushtrime · Grupi A",
    ]
    assert [d["week"] for d in documents] == [1, 2]
    assert {d["group_id"] for d in documents} == {groups["a"].id}


def test_one_bad_file_rejects_the_whole_upload(
    client, db_session, admin_user, academic_data
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))

    response = upload_materials(
        client,
        headers,
        academic_data["algorithms"].id,
        names=["Java01_Ligjerata.txt", "virus.exe"],
    )

    assert response.status_code == 400
    assert db_session.scalars(select(Document)).all() == []


def test_students_use_only_their_own_groups_materials(
    client, db_session, admin_user, groups, academic_data, student_user
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))
    algorithms = academic_data["algorithms"].id

    group_a = upload_materials(client, headers, algorithms, groups["a"].id, ["Java01_Ligjerata.txt"]).json()
    group_b = upload_materials(client, headers, algorithms, groups["b"].id, ["Java01_Ligjerata.txt"]).json()
    shared = upload_materials(client, headers, algorithms, None, ["Java01_Ushtrime.txt"]).json()

    arta = set(accessible_document_ids(student_user, db_session))
    blerta = set(accessible_document_ids(groups["blerta"], db_session))

    # Arta është te Grupi A, Blerta te B; materiali pa grup është për të dyja.
    assert group_a[0]["id"] in arta and group_b[0]["id"] not in arta
    assert group_b[0]["id"] in blerta and group_a[0]["id"] not in blerta
    assert shared[0]["id"] in arta and shared[0]["id"] in blerta

    # Edhe lista e dokumenteve ndjek të njëjtin rregull.
    listed = {
        document["id"]
        for document in client.get(
            "/api/documents",
            headers=auth_headers(login(client, student_user.email, "Student123!")),
        ).json()
    }
    assert group_b[0]["id"] not in listed


def test_professor_uploads_only_to_groups_they_may_teach(
    client, groups, academic_data, teaching
):
    algorithms = academic_data["algorithms"].id
    elira = auth_headers(login(client, "elira@test.edu", "Professor123!"))
    arben = auth_headers(login(client, "arben@test.edu", "Professor123!"))

    # Elira jep Grupin B, jo A.
    assert upload_materials(client, elira, algorithms, groups["b"].id, ["Java01.txt"]).status_code == 201
    assert upload_materials(client, elira, algorithms, groups["a"].id, ["Java01.txt"]).status_code == 403

    # Arbeni koordinon CS201, prandaj mund të ngarkojë edhe te Grupi B.
    assert upload_materials(client, arben, algorithms, groups["b"].id, ["Java01.txt"]).status_code == 201


def test_search_by_course_and_week_never_leaves_the_users_scope(
    monkeypatch, client, db_session, admin_user, groups, academic_data, student_user
):
    headers = auth_headers(login(client, admin_user.email, "Admin123!"))
    algorithms = academic_data["algorithms"].id

    week_three_a = upload_materials(client, headers, algorithms, groups["a"].id, ["Java03_Ligjerata.txt"]).json()[0]
    upload_materials(client, headers, algorithms, groups["b"].id, ["Java03_Ligjerata.txt"])
    upload_materials(client, headers, algorithms, groups["a"].id, ["Java04_Ligjerata.txt"])

    seen = {}

    def fake_retrieve(**kwargs):
        seen["document_ids"] = kwargs["document_ids"]
        return []

    monkeypatch.setattr(tools, "retrieve_context", fake_retrieve)

    context = ToolContext(
        db=db_session,
        user=db_session.get(User, student_user.id),
        profile=academic_data["profile"],
        sources=SourceRegistry(),
        document_ids=accessible_document_ids(student_user, db_session),
    )

    execute_tool(
        "search_university_documents",
        {"query": "pemët", "course_code": "cs201", "week": 3},
        context,
    )

    # Vetëm java 3 e Grupit A: jo java 4, jo java 3 e Grupit B.
    assert seen["document_ids"] == [week_three_a["id"]]

    empty = execute_tool(
        "search_university_documents",
        {"query": "pemët", "course_code": "CS201", "week": 9},
        context,
    )

    assert "Nuk ka materiale" in empty
