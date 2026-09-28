"""Vlerësimi i sistemit të plotë multi-agent, me thirrje reale te Claude.

Çdo pyetje kalon nëpër të njëjtën rrugë si chat-i i vërtetë
(`handle_chat_message`): Guardrail -> agjentët -> validator. Për secilën
ruhet cilët agjentë u aktivizuan, nëse përgjigjja përmban faktet e
pritura, çfarë burimesh citoi, sa zgjati dhe sa kushtoi.

    python -m evaluation.run_agents --max-cost 1.2
    python -m evaluation.run_agents --only G01,G02      # falas: guardrail

Rezultatet ruhen pas çdo pyetjeje. Një ekzekutim i ndërprerë (kufiri i
buxhetit, rrjeti) vazhdon aty ku mbeti pa i ripaguar pyetjet e kryera;
`--fresh` i fillon nga e para.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.ai.agents import orchestrator, tutor_agent
from app.ai.llm.client import get_anthropic_client
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from evaluation.budget import BudgetedClient, BudgetExceeded
from evaluation.dataset import QUESTIONS
from evaluation.scoring import (
    admits_missing_information,
    facts_present,
    routing_scores,
)
from scripts.seed import STUDENT_EMAIL


RESULTS_DIR = Path(__file__).parent / "results"
OUTPUT = RESULTS_DIR / "agents.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-cost",
        type=float,
        default=1.2,
        help="Kufiri i shpenzimeve në USD për këtë ekzekutim.",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Vetëm këto id, të ndara me presje (p.sh. A01,S01).",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Injoro rezultatet e mëparshme dhe fillo nga e para.",
    )

    return parser.parse_args()


def load_previous(fresh: bool) -> dict[str, dict]:
    if fresh or not OUTPUT.exists():
        return {}

    data = json.loads(OUTPUT.read_text(encoding="utf-8"))

    return {row["id"]: row for row in data["rows"]}


def save(rows: dict[str, dict]) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)

    order = {item["id"]: index for index, item in enumerate(QUESTIONS)}

    OUTPUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "model": settings.llm_model,
                "effort": settings.llm_effort,
                "rows": sorted(rows.values(), key=lambda row: order[row["id"]]),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def score(item: dict, result) -> dict:
    sources = [
        {"file_name": chunk.file_name, "page_number": chunk.page_number}
        for chunk in result.chunks
    ]

    expected_source = item.get("source")
    artifact = item.get("artifact")
    answerable = item.get("answerable", True)

    return {
        "agents_used": result.agents_used,
        "routing": routing_scores(result.agents_used, item["agents"]),
        "facts_ok": facts_present(result.answer, item.get("facts")),
        "artifact_ok": (
            any(entry["type"] == artifact for entry in result.artifacts)
            if artifact
            else None
        ),
        # Pyetja pa përgjigje është e saktë vetëm kur sistemi e pranon
        # mungesën; pyetja me përgjigje, kur nuk e pranon.
        "admits_missing": admits_missing_information(
            result.answer, result.is_unanswered
        ),
        "answerable": answerable,
        "blocked_by": result.blocked_by,
        "sources": sources,
        "cited": bool(sources),
        "source_ok": (
            any(
                source["file_name"] == expected_source[0]
                for source in sources
            )
            if expected_source
            else None
        ),
        "latency_ms": result.latency_ms,
        "answer": result.answer,
    }


def main() -> None:
    args = parse_args()

    selected = QUESTIONS

    if args.only:
        wanted = {value.strip() for value in args.only.split(",")}
        selected = [item for item in QUESTIONS if item["id"] in wanted]

    rows = load_previous(args.fresh)

    client = BudgetedClient(
        client=get_anthropic_client(),
        model=settings.llm_model,
        max_cost=args.max_cost,
    )

    # Agjentët e marrin klientin përmes këtyre emrave; kështu çdo
    # thirrje, edhe ajo e Tutor-it, kalon nga kufiri i buxhetit.
    orchestrator.get_anthropic_client = lambda: client
    tutor_agent.get_anthropic_client = lambda: client

    for item in selected:
        previous = rows.get(item["id"])

        if previous and "error" not in previous:
            continue

        db = SessionLocal()
        spent_before = client.spent
        calls_before = client.calls

        try:
            user = db.scalar(select(User).where(User.email == STUDENT_EMAIL))

            result = orchestrator.handle_chat_message(
                message=item["question"],
                user=user,
                db=db,
            )

            row = {
                "id": item["id"],
                "question": item["question"],
                "lang": item["lang"],
                "category": item["category"],
                "expected_agents": item["agents"],
                **score(item, result),
            }

        except BudgetExceeded as exc:
            print(f"Ndalem: {exc}")
            break

        except Exception as exc:  # noqa: BLE001
            # Një pyetje që dështon nuk duhet ta ndalë të gjithë vlerësimin;
            # ruhet gabimi dhe provohet sërish në ekzekutimin e radhës.
            row = {"id": item["id"], "question": item["question"], "error": repr(exc)}

        finally:
            # Vlerësimi nuk lë gjurmë te baza (p.sh. ngjarje audit-i).
            db.rollback()
            db.close()

        row["cost_usd"] = round(client.spent - spent_before, 6)
        row["llm_calls"] = client.calls - calls_before

        rows[item["id"]] = row
        save(rows)

        status = "GABIM" if "error" in row else (
            "routing OK" if row["routing"]["covered"] else "routing GABIM"
        )
        print(
            f"{item['id']}: {status}  "
            f"{row.get('agents_used', '')}  "
            f"{row['cost_usd']:.4f} $"
        )

    print(
        f"\nKy ekzekutim: {client.calls} thirrje, {client.spent:.4f} $ "
        f"(kufiri {args.max_cost:.2f} $). U ruajt te {OUTPUT}"
    )


if __name__ == "__main__":
    main()
