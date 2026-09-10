"""Tools akademike: lexojnë vetëm nga baza, pa LLM."""

from app.ai.agents.tools import (
    NO_PROFILE_MESSAGE,
    SourceRegistry,
    ToolContext,
    execute_tool,
)
from app.ai.rag.retriever import RetrievedChunk


def make_context(db, user, profile=None) -> ToolContext:
    return ToolContext(
        db=db,
        user=user,
        profile=profile,
        sources=SourceRegistry(),
    )


def test_get_my_courses_lists_only_active_enrollments(
    db_session, student_user, academic_data
):
    context = make_context(
        db_session, student_user, academic_data["profile"]
    )

    result = execute_tool("get_my_courses", {}, context)

    assert "CS201" in result
    assert "CS202" in result
    assert "CS301" not in result
    assert "13 ECTS" in result


def test_get_my_schedule_filters_by_day(
    db_session, student_user, academic_data
):
    context = make_context(
        db_session, student_user, academic_data["profile"]
    )

    monday = execute_tool(
        "get_my_schedule", {"day_of_week": "Monday"}, context
    )

    assert "09:00-10:30" in monday
    assert "A-201" in monday
    assert "Lab-2" not in monday

    empty = execute_tool(
        "get_my_schedule", {"day_of_week": "Sunday"}, context
    )

    assert "E diel" in empty


def test_get_my_exams_defaults_to_upcoming_only(
    db_session, student_user, academic_data
):
    context = make_context(
        db_session, student_user, academic_data["profile"]
    )

    upcoming = execute_tool("get_my_exams", {}, context)

    assert "CS201" in upcoming
    assert "CS202" not in upcoming

    everything = execute_tool(
        "get_my_exams", {"only_upcoming": False}, context
    )

    assert "CS201" in everything
    assert "CS202" in everything


def test_get_my_exams_filters_by_course_code(
    db_session, student_user, academic_data
):
    context = make_context(
        db_session, student_user, academic_data["profile"]
    )

    result = execute_tool(
        "get_my_exams",
        {"only_upcoming": False, "course_code": "cs202"},
        context,
    )

    assert "CS202" in result
    assert "CS201" not in result


def test_course_catalog_includes_unenrolled_courses(
    db_session, student_user, academic_data
):
    context = make_context(
        db_session, student_user, academic_data["profile"]
    )

    result = execute_tool(
        "search_course_catalog", {"semester": 5}, context
    )

    assert "CS301" in result


def test_personal_tools_report_missing_profile(db_session, admin_user):
    context = make_context(db_session, admin_user, profile=None)

    assert execute_tool("get_my_exams", {}, context) == NO_PROFILE_MESSAGE
    assert execute_tool("get_my_courses", {}, context) == NO_PROFILE_MESSAGE


def test_unknown_tool_returns_error_text(db_session, student_user):
    context = make_context(db_session, student_user)

    assert "tool i panjohur" in execute_tool("nope", {}, context)


def test_document_search_numbers_sources_consistently(
    db_session, student_user, monkeypatch
):
    """I njëjti chunk i kthyer dy herë mban të njëjtin numër citimi."""

    chunk_a = RetrievedChunk(
        chunk_id=1,
        document_id=10,
        document_title="Rregullorja e Studimeve",
        document_type="REGULATION",
        file_name="rregullore.pdf",
        page_number=4,
        chunk_index=0,
        section=None,
        content="Studenti duhet të ndjekë 70% të ligjëratave.",
        score=0.81,
    )

    chunk_b = RetrievedChunk(
        chunk_id=2,
        document_id=10,
        document_title="Rregullorja e Studimeve",
        document_type="REGULATION",
        file_name="rregullore.pdf",
        page_number=5,
        chunk_index=1,
        section=None,
        content="Provimi riparues mbahet në shtator.",
        score=0.74,
    )

    calls = {"n": 0}

    def fake_retrieve(query, db, limit=None, min_score=None, document_id=None):
        calls["n"] += 1

        return [chunk_a] if calls["n"] == 1 else [chunk_b, chunk_a]

    monkeypatch.setattr(
        "app.ai.agents.tools.retrieve_context", fake_retrieve
    )

    context = make_context(db_session, student_user)

    first = execute_tool(
        "search_university_documents", {"query": "mungesat"}, context
    )
    second = execute_tool(
        "search_university_documents", {"query": "provimi riparues"}, context
    )

    assert "[1] Rregullorja e Studimeve, faqe 4" in first
    assert "[2] Rregullorja e Studimeve, faqe 5" in second

    # Chunk-u i parë ripërdoret dhe mban numrin 1, jo 3.
    assert "[1] Rregullorja e Studimeve, faqe 4" in second

    assert [chunk.chunk_id for chunk in context.sources.chunks] == [1, 2]


def test_document_search_reports_no_results(
    db_session, student_user, monkeypatch
):
    monkeypatch.setattr(
        "app.ai.agents.tools.retrieve_context",
        lambda **kwargs: [],
    )

    context = make_context(db_session, student_user)

    result = execute_tool(
        "search_university_documents", {"query": "asgjë"}, context
    )

    assert "Nuk u gjet" in result
    assert context.sources.chunks == []
