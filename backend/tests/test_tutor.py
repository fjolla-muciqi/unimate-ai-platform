"""AI Tutor Agent, me klient Claude të simuluar."""

from types import SimpleNamespace

import pytest

from app.ai.agents import tutor_agent
from app.ai.agents.tools import (
    SourceRegistry,
    ToolContext,
    execute_tool,
)
from app.ai.agents.tutor_agent import Flashcard, FlashcardSet, Quiz, QuizQuestion


class FakeClient:
    def __init__(self, text: str = "", parsed=None):
        self._text = text
        self._parsed = parsed
        self.create_calls = []
        self.parse_calls = []

        self.messages = SimpleNamespace(
            create=self._create,
            parse=self._parse,
        )

    def _create(self, **kwargs):
        self.create_calls.append(kwargs)

        return SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text=self._text)],
        )

    def _parse(self, **kwargs):
        self.parse_calls.append(kwargs)

        return SimpleNamespace(parsed_output=self._parsed)


@pytest.fixture
def context(db_session, student_user, academic_data):
    return ToolContext(
        db=db_session,
        user=student_user,
        profile=academic_data["profile"],
        sources=SourceRegistry(),
    )


@pytest.fixture
def no_documents(monkeypatch):
    """Tutori nuk duhet të varet nga Qdrant në teste."""

    monkeypatch.setattr(
        tutor_agent, "retrieve_context", lambda **kwargs: []
    )


def use_client(monkeypatch, client: FakeClient) -> FakeClient:
    monkeypatch.setattr(
        tutor_agent, "get_anthropic_client", lambda: client
    )

    return client


def test_material_includes_the_course_syllabus(
    db_session, academic_data, no_documents
):
    course = academic_data["algorithms"]
    course.syllabus = "Java 1: Kompleksiteti. Java 2: Pemët."
    db_session.commit()

    material = tutor_agent.collect_material(
        topic="pemët binare",
        db=db_session,
        course_code="CS201",
    )

    assert "Java 2: Pemët" in material
    assert "CS201" in material


def test_material_is_empty_without_syllabus_or_documents(
    db_session, no_documents
):
    assert tutor_agent.collect_material("çfarëdo", db_session) == ""


def test_explain_without_material_does_not_call_the_model(
    monkeypatch, db_session, no_documents
):
    client = use_client(monkeypatch, FakeClient("nuk duhet thirrur"))

    answer = tutor_agent.explain_topic("tema e panjohur", db_session)

    assert "Nuk gjeta material" in answer
    assert client.create_calls == []


def test_explain_passes_the_requested_level(
    monkeypatch, db_session, academic_data, no_documents
):
    academic_data["algorithms"].syllabus = "Pemët binare dhe AVL."
    db_session.commit()

    client = use_client(monkeypatch, FakeClient("Shpjegim i thjeshtë."))

    answer = tutor_agent.explain_topic(
        topic="pemët",
        db=db_session,
        course_code="CS201",
        level="beginner",
    )

    assert answer == "Shpjegim i thjeshtë."

    prompt = client.create_calls[0]["messages"][0]["content"]

    assert "beginner" in prompt
    assert "Pemët binare dhe AVL" in prompt


def test_quiz_returns_structured_output(
    monkeypatch, db_session, academic_data, no_documents
):
    academic_data["algorithms"].syllabus = "Renditja dhe kërkimi."
    db_session.commit()

    quiz = Quiz(
        topic="Renditja",
        questions=[
            QuizQuestion(
                question="Sa është kompleksiteti i quicksort mesatarisht?",
                options=["O(n)", "O(n log n)", "O(n^2)", "O(1)"],
                correct_index=1,
                explanation="Quicksort ndan listën përgjysmë mesatarisht.",
            )
        ],
    )

    use_client(monkeypatch, FakeClient(parsed=quiz))

    result = tutor_agent.generate_quiz(
        topic="renditja",
        db=db_session,
        course_code="CS201",
    )

    assert result is not None
    assert result.questions[0].correct_index == 1


def test_quiz_tool_stores_an_artifact_and_reports_briefly(
    monkeypatch, db_session, academic_data, context, no_documents
):
    academic_data["algorithms"].syllabus = "Renditja dhe kërkimi."
    db_session.commit()

    quiz = Quiz(
        topic="Renditja",
        questions=[
            QuizQuestion(
                question="Pyetje?",
                options=["a", "b"],
                correct_index=0,
                explanation="Sepse po.",
            )
        ],
    )

    use_client(monkeypatch, FakeClient(parsed=quiz))

    result = execute_tool(
        "generate_quiz",
        {"topic": "renditja", "course_code": "CS201"},
        context,
    )

    # Modelit i kthehet vetëm një përmbledhje; quiz-i shkon si artifact.
    assert "1 pyetje" in result
    assert "Pyetje?" not in result

    assert len(context.artifacts) == 1
    assert context.artifacts[0]["type"] == "quiz"
    assert context.artifacts[0]["data"]["questions"][0]["correct_index"] == 0


def test_flashcards_tool_stores_an_artifact(
    monkeypatch, db_session, academic_data, context, no_documents
):
    academic_data["databases"].syllabus = "Normalizimi dhe format normale."
    db_session.commit()

    cards = FlashcardSet(
        topic="Normalizimi",
        cards=[Flashcard(front="1NF", back="Vlera atomike.")],
    )

    use_client(monkeypatch, FakeClient(parsed=cards))

    result = execute_tool(
        "generate_flashcards",
        {"topic": "normalizimi", "course_code": "CS202"},
        context,
    )

    assert "1 flashcards" in result
    assert context.artifacts[0]["type"] == "flashcards"
    assert context.artifacts[0]["data"]["cards"][0]["front"] == "1NF"


def test_tutor_tools_report_missing_material_without_artifact(
    monkeypatch, db_session, context, no_documents
):
    use_client(monkeypatch, FakeClient(parsed=None))

    result = execute_tool(
        "generate_quiz",
        {"topic": "temë që nuk ekziston"},
        context,
    )

    assert "Nuk gjeta material" in result
    assert context.artifacts == []


@pytest.mark.parametrize(
    ("academic_year", "expected"),
    [(1, "beginner"), (2, "intermediate"), (3, "advanced"), (4, "advanced")],
)
def test_level_follows_the_academic_year(academic_year, expected):
    profile = SimpleNamespace(academic_year=academic_year)

    assert tutor_agent.level_for_student(profile) == expected


def test_level_without_a_student_profile_is_intermediate():
    assert tutor_agent.level_for_student(None) == "intermediate"


def test_explain_tool_adapts_to_the_student_unless_asked_otherwise(
    monkeypatch, context
):
    levels = []

    monkeypatch.setattr(
        tutor_agent,
        "explain_topic",
        lambda **kwargs: levels.append(kwargs["level"]) or "ok",
    )

    # Studenti i fixture-it është në vitin e dytë.
    context.profile.academic_year = 1
    execute_tool("explain_topic", {"topic": "pemët"}, context)

    execute_tool(
        "explain_topic", {"topic": "pemët", "level": "advanced"}, context
    )

    assert levels == ["beginner", "advanced"]
