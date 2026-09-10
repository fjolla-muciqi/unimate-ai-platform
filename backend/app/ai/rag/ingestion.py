import hashlib
import logging
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.ai.rag.chunking import split_text_into_chunks
from app.ai.rag.extractor import extract_document_text
from app.ai.rag.vector_store import index_document_chunks
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk


logger = logging.getLogger(__name__)

# Sa karaktere të gabimit ruhen te `status_detail`. Traceback-u i
# plotë shkon te log-et; administratorit i mjafton shkaku.
STATUS_DETAIL_LIMIT = 1000


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

    # Chunks ruhen fillimisht në PostgreSQL,
    # që të gjenerohen ID-të e tyre.
    db.commit()

    indexed_chunks = index_document_chunks(
        document_id=document.id,
        db=db,
    )

    if indexed_chunks != total_chunks:
        raise RuntimeError(
            "Numri i chunks të indeksuara në Qdrant "
            "nuk përputhet me chunks në PostgreSQL."
        )

    return total_chunks


def ingest_document_in_background(document_id: int) -> None:
    """Ingestimi që nis pas ngarkimit të dokumentit.

    Hap sesionin e vet sepse ekzekutohet pasi kërkesa HTTP ka
    mbaruar dhe sesioni i saj është mbyllur. Statusi i dokumentit
    është e vetmja gjë që frontend-i ndjek: PROCESSING derisa
    pipeline-i punon, pastaj INDEXED ose FAILED me arsyen.
    """

    db: Session = SessionLocal()

    try:
        document = db.get(Document, document_id)

        if document is None or not document.is_active:
            return

        document.status = DocumentStatus.PROCESSING
        document.status_detail = None

        db.commit()

        try:
            total_chunks = ingest_document(document=document, db=db)

        except Exception as exc:  # noqa: BLE001
            # Çdo dështim — skedar i dëmtuar, Qdrant i palidhur,
            # model embeddings që s'shkarkohet — duhet të përfundojë
            # si FAILED i dukshëm, jo si dokument përgjithmonë
            # "në përpunim".
            logger.exception(
                "Ingestimi i dokumentit %s dështoi", document_id
            )

            db.rollback()

            document = db.get(Document, document_id)

            if document is not None:
                document.status = DocumentStatus.FAILED
                document.status_detail = str(exc)[:STATUS_DETAIL_LIMIT]

                db.commit()

            return

        document.status = DocumentStatus.INDEXED
        document.status_detail = None
        document.chunk_count = total_chunks
        document.indexed_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()