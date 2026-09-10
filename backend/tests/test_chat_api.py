"""Endpoint-et e chat-it dhe ruajtja e bisedave."""

import pytest

from app.ai.agents.orchestrator import AgentResult
from app.modules.chat import router as chat_router
from tests.conftest import auth_headers, login


@pytest.fixture
def fake_agent(monkeypatch):
    """Zëvendëson orchestrator-in me një përgjigje fikse dhe
    regjistron historikun që i kalohet."""

    calls = []

    def fake_handle(message, user, db, history=None, document_id=None):
        calls.append(
            {
                "message": message,
                "history": history or [],
                "document_id": document_id,
            }
        )

        return AgentResult(
            answer=f"Përgjigje për: {message}",
            agents_used=["academic"],
            latency_ms=42,
        )

    monkeypatch.setattr(chat_router, "handle_chat_message", fake_handle)

    return calls


def test_chat_requires_authentication(client):
    response = client.post("/api/chat", json={"message": "Përshëndetje"})

    assert response.status_code == 401


def test_chat_creates_conversation_and_persists_messages(
    client, student_user, fake_agent
):
    token = login(client, student_user.email, "Student123!")

    response = client.post(
        "/api/chat",
        json={"message": "Kur e kam provimin e Algoritmeve?"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    body = response.json()
    conversation_id = body["conversation_id"]

    assert conversation_id is not None
    assert body["answer"].startswith("Përgjigje për:")

    detail = client.get(
        f"/api/chat/conversations/{conversation_id}",
        headers=auth_headers(token),
    ).json()

    assert detail["title"] == "Kur e kam provimin e Algoritmeve?"
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
    assert detail["messages"][0]["content"] == (
        "Kur e kam provimin e Algoritmeve?"
    )


def test_follow_up_reuses_history_from_the_database(
    client, student_user, fake_agent
):
    token = login(client, student_user.email, "Student123!")

    first = client.post(
        "/api/chat",
        json={"message": "Cilat lëndë kam?"},
        headers=auth_headers(token),
    ).json()

    client.post(
        "/api/chat",
        json={
            "message": "Po orari?",
            "conversation_id": first["conversation_id"],
        },
        headers=auth_headers(token),
    )

    # Thirrja e dytë e sheh bisedën e parë si histori.
    second_call_history = fake_agent[1]["history"]

    assert len(second_call_history) == 2
    assert second_call_history[0]["content"] == "Cilat lëndë kam?"
    assert second_call_history[1]["role"] == "assistant"


def test_long_first_message_produces_truncated_title(
    client, student_user, fake_agent
):
    token = login(client, student_user.email, "Student123!")

    long_message = "Përshëndetje, " + "pyetje shumë e gjatë " * 10

    body = client.post(
        "/api/chat",
        json={"message": long_message},
        headers=auth_headers(token),
    ).json()

    detail = client.get(
        f"/api/chat/conversations/{body['conversation_id']}",
        headers=auth_headers(token),
    ).json()

    assert len(detail["title"]) <= 61
    assert detail["title"].endswith("…")


def test_conversations_are_private_to_their_owner(
    client, student_user, admin_user, fake_agent
):
    student_token = login(client, student_user.email, "Student123!")

    body = client.post(
        "/api/chat",
        json={"message": "Bisedë private"},
        headers=auth_headers(student_token),
    ).json()

    admin_token = login(client, admin_user.email, "Admin123!")

    response = client.get(
        f"/api/chat/conversations/{body['conversation_id']}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404

    listing = client.get(
        "/api/chat/conversations",
        headers=auth_headers(admin_token),
    ).json()

    assert listing == []


def test_deleted_conversation_disappears_from_listing(
    client, student_user, fake_agent
):
    token = login(client, student_user.email, "Student123!")

    body = client.post(
        "/api/chat",
        json={"message": "Për fshirje"},
        headers=auth_headers(token),
    ).json()

    conversation_id = body["conversation_id"]

    delete = client.delete(
        f"/api/chat/conversations/{conversation_id}",
        headers=auth_headers(token),
    )

    assert delete.status_code == 204

    listing = client.get(
        "/api/chat/conversations",
        headers=auth_headers(token),
    ).json()

    assert listing == []

    detail = client.get(
        f"/api/chat/conversations/{conversation_id}",
        headers=auth_headers(token),
    )

    assert detail.status_code == 404


def test_chat_on_unknown_conversation_returns_404(
    client, student_user, fake_agent
):
    token = login(client, student_user.email, "Student123!")

    response = client.post(
        "/api/chat",
        json={"message": "Ku jam?", "conversation_id": 9999},
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_empty_message_is_rejected(client, student_user, fake_agent):
    token = login(client, student_user.email, "Student123!")

    response = client.post(
        "/api/chat",
        json={"message": ""},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_missing_api_key_returns_503(client, student_user, monkeypatch):
    from app.ai.llm.client import LLMNotConfiguredError

    def raise_not_configured(**kwargs):
        raise LLMNotConfiguredError("ANTHROPIC_API_KEY mungon.")

    monkeypatch.setattr(
        chat_router, "handle_chat_message", raise_not_configured
    )

    token = login(client, student_user.email, "Student123!")

    response = client.post(
        "/api/chat",
        json={"message": "Përshëndetje"},
        headers=auth_headers(token),
    )

    assert response.status_code == 503
