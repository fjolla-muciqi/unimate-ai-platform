import hashlib

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.ai.rag.chunking import split_text_into_chunks
from app.ai.rag.extractor import extract_document_text
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def create_content_hash(content: str) -> str:
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def ingest_document(
    document: Document,
    db: Session,
) -> int:
    pages = extract_document_text(
        document.file_path
    )

    # Nëse dokumenti ri-ingestohet,
    # largojmë chunks e vjetër.
    db.execute(
        delete(DocumentChunk).where(
            DocumentChunk.document_id == document.id
        )
    )

    total_chunks = 0

    for page in pages:
        page_number = page["page_number"]
        text = page["text"]

        chunks = split_text_into_chunks(text)

        for chunk_index, content in enumerate(chunks):
            db_chunk = DocumentChunk(
                document_id=document.id,
                page_number=page_number,
                chunk_index=chunk_index,
                content=content,
                content_hash=create_content_hash(content),
                vector_id=None,
            )

            db.add(db_chunk)

            total_chunks += 1

    db.commit()

    return total_chunks