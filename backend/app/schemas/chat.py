from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

    # Kur jepet conversation_id, historiku merret nga baza e të
    # dhënave dhe fusha history injorohet.
    conversation_id: int | None = None

    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
    )

    document_id: int | None = None


class Source(BaseModel):
    """Burimi i një pjese të përgjigjes.
    Numri përputhet me citimet [1], [2] në answer."""

    number: int
    document_id: int | None
    title: str | None
    file_name: str | None
    document_type: str | None
    page_number: int | None
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    conversation_id: int | None = None

    # Id e mesazhit të asistentit, e nevojshme për të dërguar feedback.
    message_id: int | None = None

    agents_used: list[str] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)
    is_unanswered: bool = False

    # Rregulla e Guardrail Agent-it kur kërkesa u bllokua.
    blocked_by: str | None = None


class FeedbackRequest(BaseModel):
    # 1 = e dobishme, -1 = jo e dobishme, 0 = hiq vlerësimin.
    rating: Literal[-1, 0, 1]


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: list[Source] | None
    agents_used: list[str] | None
    artifacts: list[dict] | None
    rating: int | None
    is_unanswered: bool
    blocked_by: str | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)
    document_id: int | None = None


class SearchResult(BaseModel):
    chunk_id: int | None
    document_id: int | None
    document_title: str | None
    page_number: int | None
    chunk_index: int | None
    score: float
    content: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
