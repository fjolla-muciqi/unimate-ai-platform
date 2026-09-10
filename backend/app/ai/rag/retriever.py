from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.rag.vector_store import semantic_search
from app.core.config import settings
from app.models.document import Document


@dataclass
class RetrievedChunk:
    """Një chunk i gjetur në Qdrant, i pasuruar
    me metadata të dokumentit nga PostgreSQL."""

    chunk_id: int | None
    document_id: int | None
    document_title: str | None
    document_type: str | None
    file_name: str | None
    page_number: int | None
    chunk_index: int | None
    section: str | None
    content: str
    score: float


def load_documents_by_id(
    document_ids: list[int],
    db: Session,
) -> dict[int, Document]:
    if not document_ids:
        return {}

    documents = db.scalars(
        select(Document).where(
            Document.id.in_(document_ids),
            Document.is_active.is_(True),
        )
    ).all()

    return {document.id: document for document in documents}


def retrieve_context(
    query: str,
    db: Session,
    limit: int | None = None,
    min_score: float | None = None,
    document_id: int | None = None,
) -> list[RetrievedChunk]:
    """Pyetja e studentit -> embedding -> Qdrant search
    -> chunks relevante me burimin e tyre."""

    query = query.strip()

    if not query:
        return []

    if limit is None:
        limit = settings.rag_top_k

    if min_score is None:
        min_score = settings.rag_min_score

    matches = semantic_search(
        query=query,
        limit=limit,
        document_id=document_id,
    )

    relevant = [
        match
        for match in matches
        if match["score"] is not None
        and match["score"] >= min_score
    ]

    if not relevant:
        return []

    document_ids = {
        match["document_id"]
        for match in relevant
        if match["document_id"] is not None
    }

    documents = load_documents_by_id(
        list(document_ids),
        db,
    )

    results: list[RetrievedChunk] = []

    for match in relevant:
        document = documents.get(match["document_id"])

        # Dokumentet e fshira (is_active = False) mbeten
        # ende në Qdrant, prandaj i filtrojmë këtu.
        if document is None:
            continue

        results.append(
            RetrievedChunk(
                chunk_id=match["chunk_id"],
                document_id=match["document_id"],
                document_title=document.title,
                document_type=document.document_type,
                file_name=document.file_name,
                page_number=match["page_number"],
                chunk_index=match["chunk_index"],
                section=match["section"],
                content=match["content"] or "",
                score=match["score"],
            )
        )

    return results
