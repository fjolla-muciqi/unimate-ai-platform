import re
import unicodedata
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


# Sa kandidatë merren nga Qdrant për çdo fragment që kthehet, që
# rirenditja leksikore të ketë nga çfarë të zgjedhë.
CANDIDATE_POOL = 4

# Fjalë që s'mbajnë kuptim për kërkimin, në shqip dhe anglisht.
STOPWORDS = {
    "dhe", "per", "nje", "qe", "nga", "tek", "te", "me", "ne", "se", "si",
    "sa", "ka", "kam", "jam", "eshte", "jane", "cfare", "cila", "cilat",
    "cili", "kush", "kur", "ku", "mund", "duhet", "sipas", "mua", "tim",
    "time", "tende", "the", "and", "for", "what", "how", "when", "where",
    "which", "who", "can", "does", "are", "with", "from", "that", "this",
    "your", "have",
}


def _stems(text: str) -> set[str]:
    """Rrënjët e fjalëve, që "bursë", "bursa" dhe "bursat" të përputhen.

    Shqipja e shpreh rasën dhe shumësin me mbaresa, prandaj krahasohen
    katër shkronjat e para, pa ë/ç dhe pa fjalët boshe.
    """

    normalized = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )

    return {
        word[:4]
        for word in re.findall(r"[a-z0-9]+", ascii_text)
        if len(word) >= 4 and word not in STOPWORDS
    }


def keyword_overlap(query: str, content: str) -> float:
    """Pjesa e rrënjëve të pyetjes që gjenden në fragment (0 deri 1)."""

    query_stems = _stems(query)

    if not query_stems:
        return 0.0

    return len(query_stems & _stems(content)) / len(query_stems)


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

    weight = settings.rag_keyword_weight

    matches = semantic_search(
        query=query,
        limit=limit * CANDIDATE_POOL if weight else limit,
        document_id=document_id,
    )

    # Kërkim hibrid: modeli i embeddings nuk e lidh gjithmonë një fjalë
    # të pyetjes ("literatura", "bursë") me fragmentin ku ajo shkruhet
    # tekstualisht. Pragu mbetet mbi ngjashmërinë semantike.
    ranked = sorted(
        (
            match
            for match in matches
            if match["score"] is not None
            and match["score"] >= min_score
        ),
        key=lambda match: match["score"]
        + weight * keyword_overlap(query, match["content"] or ""),
        reverse=True,
    )

    relevant = ranked[:limit]

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
