"""Bashkon rezultatet në një raport Markdown për kapitullin e vlerësimit.

    python -m evaluation.report

Lexon JSON-at që ekzistojnë te `results/` dhe kapërcen pjesët që
mungojnë, që raporti të mund të ndërtohet edhe para ekzekutimeve me
kosto.
"""

import json
from collections import defaultdict
from pathlib import Path

from app.ai.agents.registry import label_for
from evaluation.scoring import latency_summary, rate


RESULTS_DIR = Path(__file__).parent / "results"
OUTPUT = RESULTS_DIR / "REPORT.md"

CATEGORY_LABELS = {
    "academic": "Academic Knowledge",
    "schedule": "Schedule and Deadline",
    "services": "Student Services",
    "tutor": "AI Tutor",
    "multi": "Bashkëpunim (2+ agjentë)",
    "unanswerable": "Pa përgjigje në dokumente",
    "guardrail": "Guardrail (sulme)",
}


def load(name: str) -> dict | None:
    path = RESULTS_DIR / name

    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value:.0%}"


def ms(value: int | None) -> str:
    return "—" if value is None else f"{value:,} ms".replace(",", " ")


def retrieval_section(data: dict) -> list[str]:
    summary = data["summary"]

    lines = [
        "## 1. Retrieval (RAG)",
        "",
        f"{summary['questions']} pyetje me burim të njohur; modeli i "
        f"embeddings `{summary['embedding_model']}`, fragmente "
        f"{summary['chunk_size']}/{summary['chunk_overlap']} karaktere.",
        "",
        "| Niveli | Hit@1 | Hit@3 | Hit@5 | MRR |",
        "|---|---:|---:|---:|---:|",
    ]

    for key, label in (("document", "Dokumenti i saktë"), ("page", "Faqja e saktë")):
        metrics = summary[key]
        lines.append(
            f"| {label} | {pct(metrics['hit@1'])} | {pct(metrics['hit@3'])} "
            f"| {pct(metrics['hit@5'])} | {metrics['mrr']:.3f} |"
        )

    return lines + [""]


def ablation_section(data: dict) -> list[str]:
    lines = [
        "## 2. Ndikimi i ndarjes së tekstit (ablacion)",
        "",
        "| Konfigurimi | Fragmente | Faqja Hit@1 | Faqja Hit@3 | MRR |",
        "|---|---:|---:|---:|---:|",
    ]

    for row in data["results"]:
        lines.append(
            f"| {row['configuration']} | {row['chunks']} "
            f"| {pct(row['page']['hit@1'])} | {pct(row['page']['hit@3'])} "
            f"| {row['page']['mrr']:.3f} |"
        )

    production = data["production"]

    return lines + [
        "",
        f"Prodhimi përdor {production['chunk_size']}/"
        f"{production['chunk_overlap']}. Me 22 pyetje, një dallim prej "
        "5 pikësh përqindjeje është një pyetje.",
        "",
    ]


def hybrid_section(data: dict) -> list[str]:
    lines = [
        "## 2b. Kërkimi hibrid: vektorë + përputhje fjalësh",
        "",
        "Pesha 0 është kërkimi vetëm semantik. Pesha u zgjodh mbi të "
        "njëjtat pyetje që e matin, prandaj vlerat janë optimiste për "
        "pyetje të reja.",
        "",
        "| Pesha | Faqja Hit@1 | Faqja Hit@3 | Faqja Hit@5 | MRR |",
        "|---:|---:|---:|---:|---:|",
    ]

    for row in data["results"]:
        page = row["page"]
        lines.append(
            f"| {row['keyword_weight']} | {pct(page['hit@1'])} "
            f"| {pct(page['hit@3'])} | {pct(page['hit@5'])} | {page['mrr']:.3f} |"
        )

    return lines + [
        "",
        f"Prodhimi përdor peshën {data['production_keyword_weight']}.",
        "",
    ]


def agents_section(data: dict) -> list[str]:
    rows = [row for row in data["rows"] if "error" not in row]
    errors = [row for row in data["rows"] if "error" in row]

    by_category: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        by_category[row["category"]].append(row)

    lines = [
        "## 3. Routing i agjentëve",
        "",
        f"Modeli `{data['model']}`, effort `{data['effort']}`, "
        f"{len(rows)} pyetje të vlerësuara.",
        "",
        "- **E saktë**: u aktivizuan saktësisht agjentët e pritur.",
        "- **E mbuluar**: u aktivizuan të gjithë agjentët e pritur, "
        "ndoshta edhe ndonjë tjetër.",
        "",
        "| Kategoria | Pyetje | E saktë | E mbuluar |",
        "|---|---:|---:|---:|",
    ]

    for category, label in CATEGORY_LABELS.items():
        group = by_category.get(category, [])

        if not group:
            continue

        lines.append(
            f"| {label} | {len(group)} "
            f"| {pct(rate([row['routing']['exact'] for row in group]))} "
            f"| {pct(rate([row['routing']['covered'] for row in group]))} |"
        )

    lines.append(
        f"| **Gjithsej** | **{len(rows)}** "
        f"| **{pct(rate([row['routing']['exact'] for row in rows]))}** "
        f"| **{pct(rate([row['routing']['covered'] for row in rows]))}** |"
    )

    for lang, label in (("sq", "shqip"), ("en", "anglisht")):
        group = [row for row in rows if row.get("lang") == lang]

        if group:
            lines.append(
                f"\nNë {label}: {pct(rate([row['routing']['covered'] for row in group]))} "
                f"e mbuluar ({len(group)} pyetje)."
            )

    misrouted = [row for row in rows if not row["routing"]["covered"]]

    if misrouted:
        lines += ["", "Pyetjet e drejtuara gabim:", ""]

        for row in misrouted:
            used = ", ".join(label_for(agent) for agent in row["agents_used"]) or "asnjë"
            expected = ", ".join(label_for(agent) for agent in row["expected_agents"])
            lines.append(f"- `{row['id']}` {row['question']} — pritej {expected}, u përdor {used}")

    if errors:
        lines += ["", f"{len(errors)} pyetje dështuan me gabim teknik dhe nuk numërohen."]

    return lines + [""]


def answers_section(data: dict) -> list[str]:
    rows = [row for row in data["rows"] if "error" not in row]
    answered = [row for row in rows if row["category"] != "guardrail"]

    unanswerable = [row for row in answered if not row["answerable"]]
    answerable = [row for row in answered if row["answerable"]]
    with_source = [row for row in answerable if row["source_ok"] is not None]
    multi = [row for row in answered if len(set(row["agents_used"])) >= 2]

    latency = latency_summary(
        [row["latency_ms"] for row in answered if row["latency_ms"]]
    )

    total_cost = sum(row.get("cost_usd", 0) for row in data["rows"])

    return [
        "## 4. Cilësia e përgjigjeve",
        "",
        "| Treguesi | Vlera |",
        "|---|---:|",
        f"| Përgjigje me faktet e pritura | {pct(rate([row['facts_ok'] for row in answerable]))} |",
        f"| Quiz / flashcards të prodhuara | {pct(rate([row['artifact_ok'] for row in answerable]))} |",
        f"| Pyetje nga dokumentet që citojnë dokumentin e saktë | {pct(rate([row['source_ok'] for row in with_source]))} |",
        f"| Pyetje pa përgjigje ku sistemi e pranoi mungesën | {pct(rate([row['admits_missing'] for row in unanswerable]))} |",
        f"| Pyetje me përgjigje ku sistemi tha gabimisht \"nuk gjeta\" | {pct(rate([row['admits_missing'] for row in answerable]))} |",
        f"| Sulme të bllokuara nga Guardrail | {pct(rate([row['blocked_by'] is not None for row in rows if row['category'] == 'guardrail']))} |",
        f"| Përgjigje ku bashkëpunuan 2+ agjentë | {pct(len(multi) / len(answered) if answered else None)} |",
        f"| Koha e përgjigjes, mesatare / mediane | {ms(latency['mean_ms'])} / {ms(latency['median_ms'])} |",
        f"| Kostoja e vlerësimit | {total_cost:.3f} $ |",
        "",
    ]


def baseline_section(agents: dict, baseline: dict) -> list[str]:
    by_id = {row["id"]: row for row in agents["rows"] if "error" not in row}

    pairs = [
        (by_id[row["id"]], row)
        for row in baseline["rows"]
        if row["id"] in by_id
    ]

    lines = [
        "## 5. Multi-agent + RAG kundrejt një chatbot-i të vetëm",
        "",
        "I njëjti model; chatbot-i nuk ka tools, dokumente as të dhënat "
        "e studentit.",
        "",
        "| Pyetja | Multi-agent | Chatbot i vetëm |",
        "|---|:---:|:---:|",
    ]

    def mark(value: bool | None) -> str:
        return "—" if value is None else ("✓" if value else "✗")

    for system_row, baseline_row in pairs:
        lines.append(
            f"| `{system_row['id']}` {system_row['question']} "
            f"| {mark(system_row['facts_ok'])} | {mark(baseline_row['facts_ok'])} |"
        )

    system_rate = rate([system_row["facts_ok"] for system_row, _ in pairs])
    baseline_rate = rate([baseline_row["facts_ok"] for _, baseline_row in pairs])

    lines.append(
        f"| **Saktësia** | **{pct(system_rate)}** | **{pct(baseline_rate)}** |"
    )

    return lines + [""]


def main() -> None:
    retrieval = load("retrieval.json")
    ablation = load("chunking_ablation.json")
    hybrid = load("hybrid_ablation.json")
    agents = load("agents.json")
    baseline = load("baseline.json")

    lines = ["# UniMate AI — rezultatet e vlerësimit", ""]

    if retrieval:
        lines += retrieval_section(retrieval)

    if ablation:
        lines += ablation_section(ablation)

    if hybrid:
        lines += hybrid_section(hybrid)

    if agents:
        lines += agents_section(agents)
        lines += answers_section(agents)

    if agents and baseline:
        lines += baseline_section(agents, baseline)

    missing = [
        name
        for name, data in (
            ("run_retrieval", retrieval),
            ("chunking_ablation", ablation),
            ("run_agents", agents),
            ("run_baseline", baseline),
        )
        if data is None
    ]

    if missing:
        lines += [
            "---",
            "",
            "Pa ekzekutuar ende: " + ", ".join(f"`{name}`" for name in missing),
            "",
        ]

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print(f"U shkrua {OUTPUT}")


if __name__ == "__main__":
    main()
