"""Panel i analitikës dhe feedback-u i studentëve."""

from sqlalchemy import select

from app.ai.agents.registry import AgentName
from app.models.conversation import Conversation
from app.models.message import Message
from tests.conftest import auth_headers, login


def seed_chat_history(db_session, student_user):
    """Dy biseda me katër përgjigje: një e pavlerësuar, një pozitive,
    një negative dhe një pa përgjigje."""

    conversation = Conversation(
        user_id=student_user.id,
        title="Bisedë testi",
    )

    db_session.add(conversation)
    db_session.flush()

    rows = [
        ("user", "Kur e kam provimin?", None, None, None, False),
        (
            "assistant",
            "Më 21.09 [1].",
            ["schedule"],
            1200,
            1,
            False,
        ),
        ("user", "Sa mungesa lejohen?", None, None, None, False),
        (
            "assistant",
            "Sipas rregullores, 30% [1].",
            ["academic", "schedule"],
            800,
            -1,
            False,
        ),
        ("user", "Kur e kam provimin?", None, None, None, False),
        (
            "assistant",
            "Nuk gjeta informacion të verifikueshëm.",
            [],
            400,
            None,
            True,
        ),
        ("user", "Krijo një quiz", None, None, None, False),
        (
            "assistant",
            "Quiz-i u gjenerua.",
            ["tutor"],
            2000,
            None,
            False,
        ),
    ]

    for role, content, agents, latency, rating, unanswered in rows:
        db_session.add(
            Message(
                conversation_id=conversation.id,
                role=role,
                content=content,
                sources=[{"number": 1}] if role == "assistant" else None,
                agents_used=agents,
                latency_ms=latency,
                rating=rating,
                is_unanswered=unanswered,
            )
        )

    db_session.commit()

    return conversation


def first_assistant_message_id(db_session, conversation) -> int:
    message = db_session.scalars(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.role == "assistant",
        )
        .order_by(Message.id)
    ).first()

    return message.id


def test_analytics_requires_admin(client, student_user):
    token = login(client, student_user.email, "Student123!")

    response = client.get(
        "/api/analytics/overview",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_overview_reports_the_thesis_metrics(
    client, db_session, admin_user, student_user
):
    seed_chat_history(db_session, student_user)

    token = login(client, admin_user.email, "Admin123!")

    body = client.get(
        "/api/analytics/overview",
        headers=auth_headers(token),
    ).json()

    assert body["total_conversations"] == 1
    assert body["total_questions"] == 4
    assert body["total_answers"] == 4

    # Pyetjet pa përgjigje.
    assert body["unanswered_count"] == 1
    assert body["unanswered_rate"] == 0.25
    assert body["recent_unanswered"][0]["question"] == (
        "Kur e kam provimin?"
    )

    # Koha e përgjigjes.
    assert body["average_latency_ms"] == 1100
    assert body["median_latency_ms"] == 1000

    # Vlerësimet e studentëve.
    assert body["ratings"]["positive"] == 1
    assert body["ratings"]["negative"] == 1
    assert body["ratings"]["unrated"] == 2
    assert body["ratings"]["satisfaction"] == 0.5


def test_overview_reports_agent_usage_and_collaboration(
    client, db_session, admin_user, student_user
):
    seed_chat_history(db_session, student_user)

    token = login(client, admin_user.email, "Admin123!")

    body = client.get(
        "/api/analytics/overview",
        headers=auth_headers(token),
    ).json()

    usage = {row["agent"]: row["count"] for row in body["agent_usage"]}

    assert usage["schedule"] == 2
    assert usage["academic"] == 1
    assert usage["tutor"] == 1

    # Agjentët e papërdorur shfaqen me zero, jo mungojnë.
    assert usage["student_services"] == 0

    labels = {row["agent"]: row["label"] for row in body["agent_usage"]}
    assert labels["tutor"] == "AI Tutor Agent"

    # Vetëm një përgjigje përfshiu më shumë se një agjent.
    assert body["multi_agent_answers"] == 1
    assert body["multi_agent_rate"] == 0.25


def test_frequent_questions_group_case_and_punctuation(
    client, db_session, admin_user, student_user
):
    seed_chat_history(db_session, student_user)

    token = login(client, admin_user.email, "Admin123!")

    body = client.get(
        "/api/analytics/overview",
        headers=auth_headers(token),
    ).json()

    top = body["frequent_questions"][0]

    assert top["question"] == "kur e kam provimin"
    assert top["count"] == 2


def test_overview_on_empty_database_returns_zeros(client, admin_user):
    token = login(client, admin_user.email, "Admin123!")

    body = client.get(
        "/api/analytics/overview",
        headers=auth_headers(token),
    ).json()

    assert body["total_answers"] == 0
    assert body["unanswered_rate"] == 0.0
    assert body["average_latency_ms"] is None
    assert body["ratings"]["satisfaction"] is None

    # Të pesë agjentët shfaqen me zero, përfshirë Guardrail-in:
    # një agjent që nuk thirret kurrë duhet të duket në panel.
    assert len(body["agent_usage"]) == len(AgentName)


def test_student_can_rate_an_answer(
    client, db_session, student_user
):
    conversation = seed_chat_history(db_session, student_user)

    message_id = first_assistant_message_id(db_session, conversation)

    token = login(client, student_user.email, "Student123!")

    response = client.post(
        f"/api/chat/messages/{message_id}/feedback",
        json={"rating": -1},
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    db_session.expire_all()

    assert db_session.get(Message, message_id).rating == -1


def test_rating_someone_elses_message_is_rejected(
    client, db_session, student_user, admin_user
):
    conversation = seed_chat_history(db_session, student_user)

    message_id = first_assistant_message_id(db_session, conversation)

    token = login(client, admin_user.email, "Admin123!")

    response = client.post(
        f"/api/chat/messages/{message_id}/feedback",
        json={"rating": 1},
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_rating_zero_clears_the_rating(
    client, db_session, student_user
):
    conversation = seed_chat_history(db_session, student_user)

    message_id = first_assistant_message_id(db_session, conversation)

    token = login(client, student_user.email, "Student123!")

    client.post(
        f"/api/chat/messages/{message_id}/feedback",
        json={"rating": 0},
        headers=auth_headers(token),
    )

    db_session.expire_all()

    assert db_session.get(Message, message_id).rating is None
