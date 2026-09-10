"""Skemat e panelit të analitikës së administratorit."""

from datetime import datetime

from pydantic import BaseModel


class AgentUsage(BaseModel):
    agent: str
    label: str
    count: int
    share: float


class FrequentQuestion(BaseModel):
    question: str
    count: int


class UnansweredQuestion(BaseModel):
    message_id: int
    question: str
    created_at: datetime


class RatingBreakdown(BaseModel):
    positive: int
    negative: int
    unrated: int
    satisfaction: float | None


class AnalyticsOverview(BaseModel):
    total_conversations: int
    total_questions: int
    total_answers: int

    unanswered_count: int
    unanswered_rate: float

    average_latency_ms: int | None
    median_latency_ms: int | None

    answers_with_sources: int
    citation_rate: float

    ratings: RatingBreakdown
    agent_usage: list[AgentUsage]
    multi_agent_answers: int
    multi_agent_rate: float

    frequent_questions: list[FrequentQuestion]
    recent_unanswered: list[UnansweredQuestion]
