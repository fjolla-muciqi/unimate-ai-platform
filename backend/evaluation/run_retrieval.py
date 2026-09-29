"""Saktësia e retrieval-it (RAG), pa asnjë thirrje te LLM.

A e gjen kërkimi semantik dokumentin dhe faqen ku ndodhet përgjigjja?
Matet me Hit@k (përgjigjja është mes k rezultateve të para) dhe MRR
(sa lart renditet rezultati i parë i saktë).

    python -m evaluation.run_retrieval
"""

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.ai.rag.retriever import retrieve_context
from app.core.config import settings
from app.core.database import SessionLocal
from app.ai.rag.scope import accessible_document_ids
from app.models.document import Document, DocumentStatus
from app.models.user import User
from evaluation.dataset import retrieval_items
from evaluation.scoring import hit_rate, mean_reciprocal_rank, source_rank
from scripts.seed import STUDENT_EMAIL


RESULTS_DIR = Path(__file__).parent / "results"

# Më shumë rezultate se `rag_top_k`, që të shihet edhe renditja e
# rezultateve që pragu i prodhimit do t'i priste.
TOP_K = 5


def student_scope(db) -> list[int] | None:
    """Dokumentet që i lejohen studentes demo, si te chat-i në prodhim.

    Pa këtë, dokumentet e fakulteteve të tjera do të dilnin si
    shpërqendrues që studentja nuk i sheh kurrë.
    """

    student = db.scalar(select(User).where(User.email == STUDENT_EMAIL))

    return accessible_document_ids(student, db)


def evaluate(db) -> dict:
    """Ekzekuton pyetjet e retrieval-it dhe kthen përmbledhjen dhe rreshtat."""

    scope = student_scope(db)

    indexed = db.scalars(
        select(Document.file_name).where(
            Document.is_active.is_(True),
            Document.status == DocumentStatus.INDEXED,
            Document.id.in_(scope) if scope is not None else True,
        )
    ).all()

    rows = []

    for item in retrieval_items():
        chunks = retrieve_context(
            query=item["question"],
            db=db,
            limit=TOP_K,
            min_score=0.0,
            document_ids=scope,
        )

        hits = [
            {
                "file_name": chunk.file_name,
                "page_number": chunk.page_number,
                "score": round(chunk.score, 4),
            }
            for chunk in chunks
        ]

        file_name, pages = item["source"]
        document_rank, page_rank = source_rank(hits, file_name, pages)

        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "expected": {"file_name": file_name, "pages": pages},
                "document_rank": document_rank,
                "page_rank": page_rank,
                "top_score": hits[0]["score"] if hits else None,
                "hits": hits,
            }
        )

    document_ranks = [row["document_rank"] for row in rows]
    page_ranks = [row["page_rank"] for row in rows]

    # Sa pyetje e kalojnë pragun e prodhimit me rezultatin e parë.
    above_threshold = sum(
        1
        for row in rows
        if row["top_score"] is not None
        and row["top_score"] >= settings.rag_min_score
    )

    summary = {
        "questions": len(rows),
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.rag_chunk_size,
        "chunk_overlap": settings.rag_chunk_overlap,
        "top_k": TOP_K,
        "min_score_in_production": settings.rag_min_score,
        "indexed_documents": sorted(indexed),
        "document": {
            "hit@1": hit_rate(document_ranks, 1),
            "hit@3": hit_rate(document_ranks, 3),
            "hit@5": hit_rate(document_ranks, 5),
            "mrr": mean_reciprocal_rank(document_ranks),
        },
        "page": {
            "hit@1": hit_rate(page_ranks, 1),
            "hit@3": hit_rate(page_ranks, 3),
            "hit@5": hit_rate(page_ranks, 5),
            "mrr": mean_reciprocal_rank(page_ranks),
        },
        "top_score_above_threshold": above_threshold / len(rows),
    }

    return {"summary": summary, "rows": rows}


def main() -> None:
    db = SessionLocal()

    try:
        result = evaluate(db)
    finally:
        db.close()

    summary = result["summary"]
    rows = result["rows"]
    indexed = summary["indexed_documents"]

    RESULTS_DIR.mkdir(exist_ok=True)
    output = RESULTS_DIR / "retrieval.json"
    output.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "summary": summary,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Pyetje: {len(rows)}   Dokumente të indeksuara: {len(indexed)}")
    print(
        "Dokumenti  Hit@1 {hit@1:.0%}  Hit@3 {hit@3:.0%}  "
        "Hit@5 {hit@5:.0%}  MRR {mrr:.3f}".format(**summary["document"])
    )
    print(
        "Faqja      Hit@1 {hit@1:.0%}  Hit@3 {hit@3:.0%}  "
        "Hit@5 {hit@5:.0%}  MRR {mrr:.3f}".format(**summary["page"])
    )

    for row in rows:
        if row["page_rank"] != 1:
            print(
                f"  {row['id']}: faqja e duhur në pozicionin "
                f"{row['page_rank'] or '—'} — {row['question']}"
            )

    print(f"U ruajt te {output}")


if __name__ == "__main__":
    main()
