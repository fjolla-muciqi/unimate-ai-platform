"""Si ndikon pesha e përputhjes së fjalëve te kërkimi hibrid.

Mat retrieval-in për disa vlera të `rag_keyword_weight` mbi të njëjtin
indeks. Pesha 0 është kërkimi vetëm me vektorë. Pa LLM, pa kosto.

    python -m evaluation.hybrid_ablation

Kujdes në interpretim: pesha zgjidhet mbi të njëjtat 22 pyetje që e
matin, prandaj rezultati i zgjedhur është optimist për pyetje të reja.
"""

import json
from datetime import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from evaluation.run_retrieval import RESULTS_DIR, evaluate


WEIGHTS = [0.0, 0.1, 0.2, 0.3, 0.5, 0.8]


def main() -> None:
    production = settings.rag_keyword_weight
    results = []

    db = SessionLocal()

    try:
        for weight in WEIGHTS:
            settings.rag_keyword_weight = weight
            summary = evaluate(db)["summary"]

            results.append(
                {
                    "keyword_weight": weight,
                    "document": summary["document"],
                    "page": summary["page"],
                }
            )

            print(
                f"w={weight:<4} faqja Hit@1 {summary['page']['hit@1']:.0%}  "
                f"Hit@3 {summary['page']['hit@3']:.0%}  "
                f"Hit@5 {summary['page']['hit@5']:.0%}  "
                f"MRR {summary['page']['mrr']:.3f}"
            )
    finally:
        settings.rag_keyword_weight = production
        db.close()

    RESULTS_DIR.mkdir(exist_ok=True)
    output = RESULTS_DIR / "hybrid_ablation.json"
    output.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "production_keyword_weight": production,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"U ruajt te {output}")


if __name__ == "__main__":
    main()
