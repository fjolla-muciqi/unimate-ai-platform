"""Chunking dhe retrieval, pa Qdrant dhe pa embeddings reale."""

import pytest

from app.ai.rag.chunking import split_text_into_chunks
from app.ai.rag.ingestion import (
    INTERRUPTED_DETAIL,
    create_content_hash,
    recover_interrupted_documents,
)
from app.ai.rag import retriever
from app.models.document import Document, DocumentStatus


def test_empty_text_produces_no_chunks():
    assert split_text_into_chunks("") == []
    assert split_text_into_chunks("   \n  ") == []


def test_short_text_stays_one_chunk():
    chunks = split_text_into_chunks("Teksti i shkurtër.")

    assert chunks == ["Teksti i shkurtër."]


def test_long_text_is_split_with_overlap():
    text = "a" * 2500

    chunks = split_text_into_chunks(text, chunk_size=1000, overlap=150)

    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)
    # Të gjithë tekstin e mbulojnë, dhe mbivendosja e rrit totalin.
    assert sum(len(chunk) for chunk in chunks) > len(text)


def test_chunking_covers_the_whole_text():
    text = " ".join(f"fjala{i}" for i in range(500))

    chunks = split_text_into_chunks(text)

    assert chunks[0].startswith("fjala0")
    assert chunks[-1].endswith("fjala499")


def test_content_hash_is_stable_and_distinct():
    assert create_content_hash("abc") == create_content_hash("abc")
    assert create_content_hash("abc") != create_content_hash("abd")


def _match(document_id: int, score: float, chunk_id: int = 1) -> dict:
    return {
        "vector_id": "v",
        "score": score,
        "chunk_id": chunk_id,
        "document_id": document_id,
        "page_number": 1,
        "chunk_index": 0,
        "section": None,
        "content": "Përmbajtje",
    }


def _add_document(db_session, admin_user, is_active: bool) -> Document:
    document = Document(
        title="Rregullore",
        file_name="rregullore.pdf",
        file_path="uploads/documents/x.pdf",
        document_type="REGULATION",
        uploaded_by=admin_user.id,
        is_active=is_active,
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    return document


def test_low_scoring_matches_are_dropped(
    db_session, admin_user, monkeypatch
):
    document = _add_document(db_session, admin_user, is_active=True)

    monkeypatch.setattr(
        retriever,
        "semantic_search",
        lambda **kwargs: [
            _match(document.id, 0.9, chunk_id=1),
            _match(document.id, 0.05, chunk_id=2),
        ],
    )

    results = retriever.retrieve_context(
        query="mungesat", db=db_session, min_score=0.25
    )

    assert [chunk.chunk_id for chunk in results] == [1]


def test_chunks_of_deleted_documents_are_filtered_out(
    db_session, admin_user, monkeypatch
):
    """Dokumentet e fshira mbeten në Qdrant, prandaj filtri i vërtetë
    është në PostgreSQL."""

    document = _add_document(db_session, admin_user, is_active=False)

    monkeypatch.setattr(
        retriever,
        "semantic_search",
        lambda **kwargs: [_match(document.id, 0.9)],
    )

    assert retriever.retrieve_context(query="x", db=db_session) == []


def test_blank_query_skips_the_vector_store(db_session, monkeypatch):
    def fail(**kwargs):
        raise AssertionError("semantic_search nuk duhej thirrur")

    monkeypatch.setattr(retriever, "semantic_search", fail)

    assert retriever.retrieve_context(query="   ", db=db_session) == []


def test_retrieved_chunk_carries_document_metadata(
    db_session, admin_user, monkeypatch
):
    document = _add_document(db_session, admin_user, is_active=True)

    monkeypatch.setattr(
        retriever,
        "semantic_search",
        lambda **kwargs: [_match(document.id, 0.77)],
    )

    chunk = retriever.retrieve_context(query="x", db=db_session)[0]

    assert chunk.document_title == "Rregullore"
    assert chunk.file_name == "rregullore.pdf"
    assert chunk.document_type == "REGULATION"
    assert chunk.score == 0.77


def test_interrupted_documents_are_marked_failed(db_session, admin_user):
    """Një rinisje gjatë ingestimit nuk duhet ta lërë dokumentin
    përgjithmonë "në përpunim"."""

    def make(title, status, is_active=True):
        document = Document(
            title=title,
            file_name=f"{title}.pdf",
            file_path=f"uploads/documents/{title}.pdf",
            document_type="REGULATION",
            uploaded_by=admin_user.id,
            status=status,
            is_active=is_active,
        )
        db_session.add(document)
        return document

    pending = make("pending", DocumentStatus.PENDING)
    processing = make("processing", DocumentStatus.PROCESSING)
    indexed = make("indexed", DocumentStatus.INDEXED)
    deleted = make("deleted", DocumentStatus.PENDING, is_active=False)
    db_session.commit()

    assert recover_interrupted_documents(db_session) == 2

    assert pending.status == DocumentStatus.FAILED
    assert processing.status == DocumentStatus.FAILED
    assert pending.status_detail == INTERRUPTED_DETAIL
    assert indexed.status == DocumentStatus.INDEXED
    # Dokumentet e fshira nuk shfaqen askund, s'ka pse të preken.
    assert deleted.status == DocumentStatus.PENDING


def test_chunks_keep_sentences_whole():
    text = (
        "Biblioteka hapet në 08:00. Studenti huazon deri në pesë libra. "
        "Afati është 21 ditë. Bursa kërkon notën 8.5 dhe 50 kredite."
    )

    chunks = split_text_into_chunks(text, chunk_size=70, overlap=0)

    # Çdo fragment mbaron me fund fjalie, dhe "8.5" nuk ndahet.
    assert all(chunk.endswith(".") for chunk in chunks)
    assert any("8.5 dhe 50 kredite" in chunk for chunk in chunks)
    assert all(len(chunk) <= 70 for chunk in chunks)


def test_last_sentence_is_repeated_as_overlap():
    text = "Fjalia e parë. Fjalia e dytë. Fjalia e tretë. Fjalia e katërt."

    chunks = split_text_into_chunks(text, chunk_size=35, overlap=20)

    assert len(chunks) > 1
    # Fjalia e fundit e një fragmenti hap fragmentin pasardhës.
    for previous, following in zip(chunks, chunks[1:]):
        assert following.startswith(previous.split(". ")[-1].rstrip("."))


def test_pdf_line_breaks_are_not_paragraphs():
    chunks = split_text_into_chunks("e hënë deri\ne premte, 09:00-13:00.")

    assert chunks == ["e hënë deri e premte, 09:00-13:00."]


def test_keyword_overlap_matches_albanian_inflections():
    overlap = retriever.keyword_overlap(
        "Cilat janë kushtet për bursë akademike?",
        "Bursat. Aplikimi për bursën akademike hapet më 1 nëntor.",
    )

    # "kushtet" mungon; "bursë" dhe "akademike" përputhen.
    assert overlap == pytest.approx(2 / 3)
    assert retriever.keyword_overlap("çfarë kur ku", "çfarëdo") == 0.0


def test_keyword_match_can_outrank_a_closer_vector(
    db_session, admin_user, monkeypatch
):
    document = _add_document(db_session, admin_user, is_active=True)

    unrelated = _match(document.id, 0.60, chunk_id=1)
    literature = _match(document.id, 0.50, chunk_id=2)
    literature["content"] = "Literatura: Cormen, Introduction to Algorithms."

    monkeypatch.setattr(
        retriever,
        "semantic_search",
        lambda **kwargs: [unrelated, literature],
    )

    def top_chunk(weight: float) -> int:
        monkeypatch.setattr(retriever.settings, "rag_keyword_weight", weight)

        return retriever.retrieve_context(
            query="Cila është literatura?", db=db_session, limit=1, min_score=0.25
        )[0].chunk_id

    assert top_chunk(0.0) == 1
    assert top_chunk(0.3) == 2
