"""Krahasimi: një chatbot i vetëm, pa agjentë, pa tools dhe pa RAG.

I njëjti model dhe i njëjti nivel arsyetimi si sistemi multi-agent,
por pa qasje te dokumentet ose te të dhënat e studentit. Dallimi në
saktësi mes këtij dhe `run_agents` është kontributi i arkitekturës.

    python -m evaluation.run_baseline --max-cost 0.2
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter

from app.ai.llm.client import get_anthropic_client
from app.core.config import settings
from evaluation.budget import BudgetedClient, BudgetExceeded
from evaluation.dataset import baseline_items
from evaluation.scoring import admits_missing_information, facts_present


RESULTS_DIR = Path(__file__).parent / "results"
OUTPUT = RESULTS_DIR / "baseline.json"

BASELINE_SYSTEM = (
    "Ti je asistent virtual i një universiteti. Përgjigju shkurt "
    "pyetjeve të studentëve në gjuhën e pyetjes. Nëse nuk e di "
    "përgjigjen, thuaje sinqerisht."
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-cost", type=float, default=0.2)
    args = parser.parse_args()

    client = BudgetedClient(
        client=get_anthropic_client(),
        model=settings.llm_model,
        max_cost=args.max_cost,
    )

    rows = []

    for item in baseline_items():
        spent_before = client.spent
        started = perf_counter()

        try:
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=2000,
                system=BASELINE_SYSTEM,
                output_config={"effort": settings.llm_effort},
                messages=[{"role": "user", "content": item["question"]}],
            )
        except BudgetExceeded as exc:
            print(f"Ndalem: {exc}")
            break

        answer = "".join(
            block.text for block in response.content if block.type == "text"
        )

        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "category": item["category"],
                "facts_ok": facts_present(answer, item.get("facts")),
                "admits_missing": admits_missing_information(answer, False),
                "latency_ms": int((perf_counter() - started) * 1000),
                "cost_usd": round(client.spent - spent_before, 6),
                "answer": answer,
            }
        )

        print(f"{item['id']}: fakte {'OK' if rows[-1]['facts_ok'] else 'JO'}")

    RESULTS_DIR.mkdir(exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "model": settings.llm_model,
                "system": BASELINE_SYSTEM,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n{client.calls} thirrje, {client.spent:.4f} $. U ruajt te {OUTPUT}")


if __name__ == "__main__":
    main()
