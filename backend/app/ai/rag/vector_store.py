from functools import lru_cache
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document_chunk import DocumentChunk


VECTOR_SIZE = 384


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def create_collection_if_not_exists() -> None:
    client = get_qdrant_client()

    if client.collection_exists(settings.qdrant_collection):
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )


def create_vector_id(chunk: DocumentChunk) -> str:
    value = (
        f"document:{chunk.document_id}:"
        f"chunk:{chunk.id}:"
        f"hash:{chunk.content_hash}"
    )

    return str(uuid5(NAMESPACE_URL, value))


def delete_document_vectors(document_id: int) -> None:
    client = get_qdrant_client()

    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )
        ),
    )


def index_document_chunks(
    document_id: int,
    db: Session,
) -> int:
    create_collection_if_not_exists()

    result = db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(
            DocumentChunk.page_number,
            DocumentChunk.chunk_index,
        )
    )

    chunks = list(result.scalars().all())

    if not chunks:
        return 0

    contents = [chunk.content for chunk in chunks]

    model = get_embedding_model()

    embeddings = model.encode(
        contents,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    points: list[PointStruct] = []

    for chunk, embedding in zip(chunks, embeddings):
        vector_id = create_vector_id(chunk)

        points.append(
            PointStruct(
                id=vector_id,
                vector=embedding.tolist(),
                payload={
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                },
            )
        )

        chunk.vector_id = vector_id

    delete_document_vectors(document_id)

    client = get_qdrant_client()

    client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
        wait=True,
    )

    db.commit()

    return len(points)


def semantic_search(
    query: str,
    limit: int = 5,
    document_id: int | None = None,
) -> list[dict]:
    create_collection_if_not_exists()

    model = get_embedding_model()
    client = get_qdrant_client()

    query_vector = model.encode(
        query,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()

    query_filter = None

    if document_id is not None:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )

    result = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )

    matches: list[dict] = []

    for point in result.points:
        payload = point.payload or {}

        matches.append(
            {
                "vector_id": str(point.id),
                "score": point.score,
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "page_number": payload.get("page_number"),
                "chunk_index": payload.get("chunk_index"),
                "section": payload.get("section"),
                "content": payload.get("content"),
            }
        )

    return matches