"""Cikli agentik, me një klient Claude të simuluar.

Verifikon se tool_use ekzekutohet, se rezultatet i kthehen modelit
në formatin e duhur dhe se cikli nuk shkon pafundësisht.
"""

from types import SimpleNamespace

import pytest

from app.ai.agents import orchestrator
from app.ai.agents.tools import SourceRegistry, ToolContext


class FakeBlock(SimpleNamespace):
    pass


def text_block(text: str) -> FakeBlock:
    return FakeBlock(type="text", text=text)


def tool_use_block(block_id: str, name: str, tool_input: dict) -> FakeBlock:
    return FakeBlock(
        type="tool_use",
        id=block_id,
        name=name,
        input=tool_input,
    )


class FakeResponse(SimpleNamespace):
    pass


class FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def create(self, **kwargs):
        # Orkestruesi e zgjeron të njëjtën listë `messages` nga një
        # iteracion në tjetrin. Klienti real e serializon atë në
        # momentin e thirrjes, prandaj edhe ky fake ruan një kopje —
        # përndryshe të gjitha kërkesat e regjistruara do të tregonin
        # te e njëjta listë përfundimtare.
        self.requests.append(
            {**kwargs, "messages": list(kwargs.get("messages", []))}
        )

        if not self._responses:
            raise AssertionError("Klienti u thirr më shumë herë se pritej.")

        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)


@pytest.fixture
def context(db_session, student_user, academic_data):
    return ToolContext(
        db=db_session,
        user=student_user,
        profile=academic_data["profile"],
        sources=SourceRegistry(),
    )


def use_client(monkeypatch, responses) -> FakeClient:
    client = FakeClient(responses)

    monkeypatch.setattr(
        orchestrator, "get_anthropic_client", lambda: client
    )

    return client


def test_answer_without_tools_is_returned_directly(
    monkeypatch, context
):
    use_client(
        monkeypatch,
        [
            FakeResponse(
                stop_reason="end_turn",
                content=[text_block("Përshëndetje!")],
            )
        ],
    )

    assert orchestrator.run_agent("Tungjatjeta", context) == "Përshëndetje!"


def test_tool_result_is_fed_back_to_the_model(monkeypatch, context):
    client = use_client(
        monkeypatch,
        [
            FakeResponse(
                stop_reason="tool_use",
                content=[
                    tool_use_block("t1", "get_my_exams", {}),
                ],
            ),
            FakeResponse(
                stop_reason="end_turn",
                content=[
                    text_block("Provimi i Algoritmeve është më 21 ditë.")
                ],
            ),
        ],
    )

    answer = orchestrator.run_agent("Kur e kam provimin?", context)

    assert "Algoritmeve" in answer

    second_request = client.messages.requests[1]
    tool_message = second_request["messages"][-1]

    assert tool_message["role"] == "user"

    result = tool_message["content"][0]

    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == "t1"
    assert result["is_error"] is False
    assert "CS201" in result["content"]


def test_parallel_tool_calls_return_one_user_message(
    monkeypatch, context
):
    client = use_client(
        monkeypatch,
        [
            FakeResponse(
                stop_reason="tool_use",
                content=[
                    tool_use_block("t1", "get_my_courses", {}),
                    tool_use_block("t2", "get_my_schedule", {}),
                ],
            ),
            FakeResponse(
                stop_reason="end_turn",
                content=[text_block("Ja ku i ke.")],
            ),
        ],
    )

    orchestrator.run_agent("Lëndët dhe orari im?", context)

    tool_message = client.messages.requests[1]["messages"][-1]

    assert len(tool_message["content"]) == 2
    assert [r["tool_use_id"] for r in tool_message["content"]] == ["t1", "t2"]


def test_failing_tool_is_reported_as_error_not_crash(
    monkeypatch, context
):
    def boom(**kwargs):
        raise RuntimeError("Qdrant nuk përgjigjet")

    monkeypatch.setattr(orchestrator, "execute_tool", boom)

    client = use_client(
        monkeypatch,
        [
            FakeResponse(
                stop_reason="tool_use",
                content=[
                    tool_use_block(
                        "t1",
                        "search_university_documents",
                        {"query": "mungesat"},
                    )
                ],
            ),
            FakeResponse(
                stop_reason="end_turn",
                content=[text_block("Nuk arrita ta kontrolloj tani.")],
            ),
        ],
    )

    answer = orchestrator.run_agent("Sa mungesa lejohen?", context)

    result = client.messages.requests[1]["messages"][-1]["content"][0]

    assert result["is_error"] is True
    assert "Qdrant nuk përgjigjet" in result["content"]
    assert answer == "Nuk arrita ta kontrolloj tani."


def test_refusal_returns_safe_message(monkeypatch, context):
    use_client(
        monkeypatch,
        [FakeResponse(stop_reason="refusal", content=[])],
    )

    assert (
        orchestrator.run_agent("...", context)
        == orchestrator.REFUSAL_ANSWER
    )


def test_iteration_limit_forces_a_final_answer(monkeypatch, context):
    """Nëse modeli thërret tools pa pushim, cikli ndalet dhe kërkohet
    një përgjigje përmbledhëse pa tools."""

    monkeypatch.setattr(
        orchestrator.settings, "agent_max_iterations", 3
    )

    looping = [
        FakeResponse(
            stop_reason="tool_use",
            content=[tool_use_block(f"t{i}", "get_my_courses", {})],
        )
        for i in range(3)
    ]

    client = use_client(
        monkeypatch,
        looping
        + [
            FakeResponse(
                stop_reason="end_turn",
                content=[text_block("Përmbledhje.")],
            )
        ],
    )

    answer = orchestrator.run_agent("Pyetje e ndërlikuar", context)

    assert answer == "Përmbledhje."
    assert len(client.messages.requests) == 4
    assert "tools" not in client.messages.requests[-1]


def test_empty_answer_falls_back(monkeypatch, context):
    use_client(
        monkeypatch,
        [FakeResponse(stop_reason="end_turn", content=[])],
    )

    assert (
        orchestrator.run_agent("...", context)
        == orchestrator.FALLBACK_ANSWER
    )


def test_history_precedes_the_new_question(monkeypatch, context):
    client = use_client(
        monkeypatch,
        [
            FakeResponse(
                stop_reason="end_turn",
                content=[text_block("Po.")],
            )
        ],
    )

    orchestrator.run_agent(
        "Po e martë?",
        context,
        history=[
            {"role": "user", "content": "A kam ligjëratë të hënën?"},
            {"role": "assistant", "content": "Po, në orën 09:00."},
        ],
    )

    messages = client.messages.requests[0]["messages"]

    assert len(messages) == 3
    assert messages[0]["content"] == "A kam ligjëratë të hënën?"
    assert messages[-1] == {"role": "user", "content": "Po e martë?"}


def test_handle_chat_message_returns_cited_chunks(
    monkeypatch, db_session, student_user, academic_data
):
    from app.ai.rag.retriever import RetrievedChunk

    chunk = RetrievedChunk(
        chunk_id=7,
        document_id=3,
        document_title="Rregullorja",
        document_type="REGULATION",
        file_name="rregullore.pdf",
        page_number=2,
        chunk_index=0,
        section=None,
        content="Afati i regjistrimit mbyllet më 30 shtator.",
        score=0.9,
    )

    monkeypatch.setattr(
        "app.ai.agents.tools.retrieve_context",
        lambda **kwargs: [chunk],
    )

    use_client(
        monkeypatch,
        [
            FakeResponse(
                stop_reason="tool_use",
                content=[
                    tool_use_block(
                        "t1",
                        "search_university_documents",
                        {"query": "afati i regjistrimit"},
                    )
                ],
            ),
            FakeResponse(
                stop_reason="end_turn",
                content=[text_block("Afati mbyllet më 30.09 [1].")],
            ),
        ],
    )

    result = orchestrator.handle_chat_message(
        message="Kur mbyllet afati i regjistrimit?",
        user=student_user,
        db=db_session,
    )

    assert "[1]" in result.answer
    assert len(result.chunks) == 1
    assert result.chunks[0].chunk_id == 7
    assert result.agents_used == ["academic"]
    assert result.is_unanswered is False
    assert result.latency_ms >= 0
