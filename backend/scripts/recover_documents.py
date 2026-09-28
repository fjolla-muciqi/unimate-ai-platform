"""Rikuperon dokumentet që një rinisje i la në mes të ingestimit.

Ekzekutohet nga `docker-entrypoint.sh` para nisjes së API-t:

    python -m scripts.recover_documents
"""

from app.ai.rag.ingestion import recover_interrupted_documents
from app.core.database import SessionLocal


def main() -> None:
    db = SessionLocal()

    try:
        recovered = recover_interrupted_documents(db)
    finally:
        db.close()

    print(f"Dokumente të ndërprera të shënuara FAILED: {recovered}")


if __name__ == "__main__":
    main()
