
import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agents.orchestrator import handle_chat_message
from app.ai.llm.client import LLMNotConfiguredError
from app.ai.rag.retriever import RetrievedChunk, retrieve_context
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationResponse,
    FeedbackRequest,
    SearchRequest,
    SearchResponse,
    SearchResult,
    Source,
)
from app.core.clock import utcnow


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


HISTORY_LIMIT = 20
TITLE_MAX_LENGTH = 60


def build_sources(
    chunks: list[RetrievedChunk],
) -> list[Source]:
    sources: list[Source] = []

    for position, chunk in enumerate(chunks, start=1):
        sources.append(
            Source(
                number=position,
                document_id=chunk.document_id,
                title=chunk.document_title,
                file_name=chunk.file_name,
                document_type=chunk.document_type,
                page_number=chunk.page_number,
                score=chunk.score,
            )
        )

    return sources


def get_owned_conversation(
    conversation_id: int,
    user: User,
    db: Session,
) -> Conversation:
    conversation = db.get(Conversation, conversation_id)

    if (
        conversation is None
        or not conversation.is_active
        or conversation.user_id != user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return conversation


def load_history(
    conversation: Conversation,
    db: Session,
) -> list[dict]:
    """Mesazhet e fundit të bisedës në formatin që pret modeli."""

    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
    ).all()

    return [
        {"role": message.role, "content": message.content}
        for message in reversed(messages)
    ]


def build_title(message: str) -> str:
    title = " ".join(message.split())

    if len(title) <= TITLE_MAX_LENGTH:
        return title

    return f"{title[:TITLE_MAX_LENGTH].rstrip()}…"


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pyetje -> Orchestrator Agent (tools) -> përgjigje me burime."""

    conversation: Conversation | None = None
    history: list[dict]

    if payload.conversation_id is not None:
        conversation = get_owned_conversation(
            payload.conversation_id,
            current_user,
            db,
        )
        history = load_history(conversation, db)

    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=build_title(payload.message),
        )

        db.add(conversation)
        db.flush()

        history = [
            message.model_dump()
            for message in payload.history
        ]

    try:
        result = handle_chat_message(
            message=payload.message,
            user=current_user,
            db=db,
            history=history,
            document_id=payload.document_id,
        )

    except LLMNotConfiguredError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    except anthropic.RateLimitError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests to the AI model. Try again shortly.",
        )

    except anthropic.APIConnectionError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Could not reach the AI model.",
        )

    except anthropic.APIStatusError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI model error: {exc.message}",
        )

    sources = build_sources(result.chunks)

    db.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=payload.message,
        )
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result.answer,
        sources=[source.model_dump() for source in sources],
        agents_used=result.agents_used,
        artifacts=result.artifacts,
        latency_ms=result.latency_ms,
        is_unanswered=result.is_unanswered,
        blocked_by=result.blocked_by,
    )

    db.add(assistant_message)

    # Bisedat renditen sipas aktivitetit të fundit.
    conversation.updated_at = utcnow()

    db.commit()
    db.refresh(conversation)
    db.refresh(assistant_message)

    return ChatResponse(
        answer=result.answer,
        sources=sources,
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        agents_used=result.agents_used,
        artifacts=result.artifacts,
        is_unanswered=result.is_unanswered,
        blocked_by=result.blocked_by,
    )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Conversation)
        .where(
            Conversation.user_id == current_user.id,
            Conversation.is_active.is_(True),
        )
        .order_by(Conversation.updated_at.desc())
    ).all()


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_conversation(conversation_id, current_user, db)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = get_owned_conversation(
        conversation_id,
        current_user,
        db,
    )

    conversation.is_active = False

    db.commit()

    return None


@router.post(
    "/messages/{message_id}/feedback",
    status_code=status.HTTP_204_NO_CONTENT,
)
def rate_message(
    message_id: int,
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Vlerësimi i studentit për një përgjigje të asistentit."""

    message = db.get(Message, message_id)

    if message is None or message.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found.",
        )

    conversation = db.get(Conversation, message.conversation_id)

    if conversation is None or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found.",
        )

    message.rating = payload.rating or None

    db.commit()

    return None


@router.post(
    "/search",
    response_model=SearchResponse,
)
def search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieval i pastër, pa LLM.
    Shërben për debug dhe për matjen e retrieval accuracy."""

    chunks = retrieve_context(
        query=payload.query,
        db=db,
        limit=payload.limit,
        document_id=payload.document_id,
    )

    return SearchResponse(
        query=payload.query,
        results=[
            SearchResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                score=chunk.score,
                content=chunk.content,
            )
            for chunk in chunks
        ],
    )
