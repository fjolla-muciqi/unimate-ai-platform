"""Admin Analytics.

Metrikat që kërkon tema: pyetjet më të shpeshta, agjentët më të
përdorur, pyetjet pa përgjigje, koha mesatare e përgjigjes dhe
vlerësimet e studentëve.
"""

from collections import Counter
from statistics import median

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.agents.registry import AgentName, label_for
from app.core.database import get_db
from app.core.security import require_admin
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.analytics import (
    AgentUsage,
    AnalyticsOverview,
    FrequentQuestion,
    RatingBreakdown,
    UnansweredQuestion,
)


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


def normalize_question(text: str) -> str:
    """Grupon pyetje pothuajse identike duke hequr shenjat dhe
    ndryshimet e shkronjave të mëdha."""

    cleaned = " ".join(text.split()).strip().lower()

    return cleaned.rstrip("?!. ")


def rate(part: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round(part / total, 4)


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
)
def analytics_overview(
    frequent_limit: int = Query(default=10, ge=1, le=50),
    unanswered_limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total_conversations = db.scalar(
        select(func.count()).select_from(Conversation)
    ) or 0

    assistant_messages = db.scalars(
        select(Message).where(Message.role == "assistant")
    ).all()

    user_messages = db.scalars(
        select(Message).where(Message.role == "user")
    ).all()

    total_answers = len(assistant_messages)

    unanswered = [m for m in assistant_messages if m.is_unanswered]

    latencies = [
        m.latency_ms
        for m in assistant_messages
        if m.latency_ms is not None
    ]

    with_sources = [m for m in assistant_messages if m.sources]

    positive = sum(1 for m in assistant_messages if m.rating == 1)
    negative = sum(1 for m in assistant_messages if m.rating == -1)
    unrated = total_answers - positive - negative

    rated = positive + negative

    # Sa agjentë u aktivizuan, dhe sa përgjigje përfshinë më shumë se
    # një agjent — dëshmia sasiore e Multi-Agent Collaboration.
    agent_counter: Counter[str] = Counter()
    multi_agent = 0

    for message in assistant_messages:
        agents = message.agents_used or []

        agent_counter.update(agents)

        if len(agents) > 1:
            multi_agent += 1

    agent_total = sum(agent_counter.values())

    agent_usage = [
        AgentUsage(
            agent=agent,
            label=label_for(agent),
            count=count,
            share=rate(count, agent_total),
        )
        for agent, count in agent_counter.most_common()
    ]

    # Agjentët pa asnjë përdorim shfaqen me zero, që paneli të mos
    # fshehë një agjent që nuk po thirret kurrë.
    seen = {usage.agent for usage in agent_usage}

    for agent in AgentName:
        if agent.value not in seen:
            agent_usage.append(
                AgentUsage(
                    agent=agent.value,
                    label=label_for(agent),
                    count=0,
                    share=0.0,
                )
            )

    question_counter: Counter[str] = Counter(
        normalize_question(m.content)
        for m in user_messages
        if m.content.strip()
    )

    frequent = [
        FrequentQuestion(question=question, count=count)
        for question, count in question_counter.most_common(
            frequent_limit
        )
    ]

    recent_unanswered = [
        UnansweredQuestion(
            message_id=message.id,
            question=find_question_for(message, db),
            created_at=message.created_at,
        )
        for message in sorted(
            unanswered,
            key=lambda m: m.id,
            reverse=True,
        )[:unanswered_limit]
    ]

    return AnalyticsOverview(
        total_conversations=total_conversations,
        total_questions=len(user_messages),
        total_answers=total_answers,
        unanswered_count=len(unanswered),
        unanswered_rate=rate(len(unanswered), total_answers),
        average_latency_ms=(
            int(sum(latencies) / len(latencies)) if latencies else None
        ),
        median_latency_ms=(
            int(median(latencies)) if latencies else None
        ),
        answers_with_sources=len(with_sources),
        citation_rate=rate(len(with_sources), total_answers),
        ratings=RatingBreakdown(
            positive=positive,
            negative=negative,
            unrated=unrated,
            satisfaction=(
                round(positive / rated, 4) if rated else None
            ),
        ),
        agent_usage=agent_usage,
        multi_agent_answers=multi_agent,
        multi_agent_rate=rate(multi_agent, total_answers),
        frequent_questions=frequent,
        recent_unanswered=recent_unanswered,
    )


def find_question_for(message: Message, db: Session) -> str:
    """Pyetja e studentit që i parapriu kësaj përgjigjeje."""

    question = db.scalar(
        select(Message)
        .where(
            Message.conversation_id == message.conversation_id,
            Message.role == "user",
            Message.id < message.id,
        )
        .order_by(Message.id.desc())
        .limit(1)
    )

    return question.content if question else ""
