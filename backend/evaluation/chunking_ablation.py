"""Si ndikon ndarja e tekstit në saktësinë e retrieval-it.

Ri-indekson tre PDF-të demo me disa konfigurime, mat retrieval-in për
secilin, dhe në fund e rikthen indeksin te konfigurimi i prodhimit
(`settings.rag_chunk_size`). Pa LLM, pra pa kosto.

    python -m evaluation.chunking_ablation

Konfigurimi i parë riprodhon ndarjen e vjetër sipas karaktereve
(1000/150), që numrat "para" dhe "pas" të vijnë nga e njëjta matje.
"""

import json
from datetime import datetime

from sqlalchemy import select

from app.ai.rag import chunking, ingestion
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from evaluation.run_retrieval import RESULTS_DIR, evaluate
from scripts.demo_documents import DEMO_DOCUMENTS


def legacy_splitter(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Ndarja para ndryshimit: karaktere, pa kufij fjalish."""

    return chunking._split_by_characters(text.strip(), 1000, 150)


def sentence_splitter(size: int, size_overlap: int):
    # Nënshkrimi i njëjtë me `split_text_into_chunks`, sepse ingestimi
    # e thërret me emra (`chunk_size=`, `overlap=`); vlerat e
    # konfigurimit zëvendësojnë ato të prodhimit.
    def split(text: str, chunk_size: int, overlap: int) -> list[str]:
        return chunking.split_text_into_chunks(text, size, size_overlap)

    return split


CONFIGURATIONS = [
    ("Karaktere 1000/150 (ndarja e vjetër)", legacy_splitter),
    ("Fjali 1000/150", sentence_splitter(1000, 150)),
    ("Fjali 700/150", sentence_splitter(700, 150)),
    ("Fjali 500/120", sentence_splitter(500, 120)),
    ("Fjali 350/80", sentence_splitter(350, 80)),
    ("Fjali 250/60", sentence_splitter(250, 60)),
]


def demo_document_ids() -> list[int]:
    names = [spec["file_name"] for spec in DEMO_DOCUMENTS]

    db = SessionLocal()

    try:
        return list(
            db.scalars(
                select(Document.id).where(Document.file_name.in_(names))
            ).all()
        )
    finally:
        db.close()


def reindex(document_ids: list[int], splitter) -> int:
    ingestion.split_text_into_chunks = splitter

    for document_id in document_ids:
        ingestion.ingest_document_in_background(document_id)

    db = SessionLocal()

    try:
        documents = [db.get(Document, document_id) for document_id in document_ids]

        # Një ingestim i dështuar i lë fragmentet e vjetra në indeks:
        # matja do të dukej e suksesshme, por do të matte konfigurimin
        # e mëparshëm.
        failed = [
            f"{document.file_name}: {document.status_detail}"
            for document in documents
            if document.status != DocumentStatus.INDEXED
        ]

        if failed:
            raise RuntimeError("Ri-indeksimi dështoi: " + "; ".join(failed))

        return sum(document.chunk_count for document in documents)
    finally:
        db.close()


def main() -> None:
    document_ids = demo_document_ids()
    production_splitter = chunking.split_text_into_chunks

    results = []

    try:
        for label, splitter in CONFIGURATIONS:
            chunk_count = reindex(document_ids, splitter)

            db = SessionLocal()

            try:
                summary = evaluate(db)["summary"]
            finally:
                db.close()

            results.append(
                {
                    "configuration": label,
                    "chunks": chunk_count,
                    "document": summary["document"],
                    "page": summary["page"],
                    "top_score_above_threshold": summary[
                        "top_score_above_threshold"
                    ],
                }
            )

            print(
                f"{label:<38} fragmente {chunk_count:>3}  "
                f"faqja Hit@1 {summary['page']['hit@1']:.0%}  "
                f"Hit@3 {summary['page']['hit@3']:.0%}  "
                f"MRR {summary['page']['mrr']:.3f}"
            )
    finally:
        # Indeksi mbetet gjithmonë në konfigurimin e prodhimit.
        reindex(document_ids, production_splitter)

    RESULTS_DIR.mkdir(exist_ok=True)
    output = RESULTS_DIR / "chunking_ablation.json"
    output.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "production": {
                    "chunk_size": settings.rag_chunk_size,
                    "chunk_overlap": settings.rag_chunk_overlap,
                },
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Indeksi u rikthye te {settings.rag_chunk_size}/"
        f"{settings.rag_chunk_overlap}. U ruajt te {output}"
    )


if __name__ == "__main__":
    main()
