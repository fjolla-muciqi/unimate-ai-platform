"""Analiza e studimit pilot të përdorshmërisë (SUS + besimi te citimet).

Lexon eksportin CSV të Google Forms dhe fletën e vëzhgimit, të
përshkruara te `docs/usability-study/`:

    results/usability/pergjigjet.csv    nga Google Forms
    results/usability/vezhgimet.csv     fleta e vëzhgimit (opsionale)

    python -m evaluation.usability_analysis

Kolonat e Google Forms lexohen sipas pozicionit: e para është koha e
plotësimit, pastaj pyetjet në renditjen e `2-pyetesori.md`.
"""

import csv
import json
from pathlib import Path
from statistics import mean, median, stdev


RESULTS_DIR = Path(__file__).parent / "results" / "usability"

# Pozicionet në CSV (0 = koha e plotësimit nga Google Forms).
CODE, CONSENT, STATUS, AI_USE = 1, 2, 3, 4
SUS_COLUMNS = range(5, 15)
TRUST_COLUMNS = range(15, 20)
LIKED, IMPROVE = 20, 21

TRUST_LABELS = [
    "Përgjigjet më dukeshin të besueshme",
    "Burimet (dokumenti, faqja) ma rritën besimin",
    "\"Nuk e gjeta\" ma rriti besimin te sistemi",
    "Do ta kontrolloja burimin për vendime të rëndësishme",
    "Do ta preferoja mbi kërkimin manual",
]

TASKS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]


def sus_score(answers: list[int]) -> float:
    """Rezultati SUS 0–100 (Brooke, 1996).

    Pyetjet tek (1, 3, 5, 7, 9) janë pozitive: vlera − 1. Pyetjet çift
    janë negative: 5 − vlera. Shuma shumëzohet me 2.5.
    """

    if len(answers) != 10 or not all(1 <= value <= 5 for value in answers):
        raise ValueError("SUS kërkon 10 përgjigje nga 1 deri 5.")

    total = sum(
        value - 1 if index % 2 == 0 else 5 - value
        for index, value in enumerate(answers)
    )

    return total * 2.5


def sus_adjective(score: float) -> str:
    """Përshkrimi sipas shkallës së Bangor, Kortum & Miller (2009)."""

    if score >= 85.5:
        return "shkëlqyeshëm"
    if score >= 71.4:
        return "mirë"
    if score >= 50.9:
        return "në rregull"
    if score >= 35.7:
        return "dobët"
    return "shumë dobët"


def describe(values: list[float]) -> dict:
    return {
        "n": len(values),
        "mean": round(mean(values), 1),
        "sd": round(stdev(values), 1) if len(values) > 1 else None,
        "median": round(median(values), 1),
        "min": min(values),
        "max": max(values),
    }


def read_responses(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))[1:]

    participants = []

    for row in rows:
        # Pa pëlqim, përgjigjja nuk përdoret (shih `3-pelqimi.md`).
        if not row[CONSENT].strip():
            continue

        participants.append(
            {
                "code": row[CODE].strip(),
                "status": row[STATUS].strip(),
                "ai_use": row[AI_USE].strip(),
                "sus": [int(row[index]) for index in SUS_COLUMNS],
                "trust": [int(row[index]) for index in TRUST_COLUMNS],
                "liked": row[LIKED].strip() if len(row) > LIKED else "",
                "improve": row[IMPROVE].strip() if len(row) > IMPROVE else "",
            }
        )

    return participants


def read_observations(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def analyse(participants: list[dict], observations: list[dict]) -> dict:
    scores = [sus_score(item["sus"]) for item in participants]

    trust = []

    for index, label in enumerate(TRUST_LABELS):
        values = [item["trust"][index] for item in participants]
        trust.append(
            {
                "statement": label,
                **describe(values),
                # Pajtohem ose pajtohem plotësisht (4–5).
                "agree_share": sum(value >= 4 for value in values) / len(values),
            }
        )

    tasks = {}

    for task in TASKS:
        marks = [row.get(task, "").strip().upper() for row in observations]
        marks = [mark for mark in marks if mark]

        if marks:
            tasks[task] = {
                "n": len(marks),
                "alone": marks.count("S") / len(marks),
                "with_help": marks.count("ME") / len(marks),
                "failed": marks.count("D") / len(marks),
            }

    source_seen = [
        row.get("D3: e pa burimin?", "").strip().lower() for row in observations
    ]
    source_seen = [value for value in source_seen if value]

    return {
        "participants": len(participants),
        "sus": {
            **describe(scores),
            "adjective": sus_adjective(mean(scores)),
            "per_participant": {
                item["code"]: score for item, score in zip(participants, scores)
            },
        },
        "trust": trust,
        "tasks": tasks,
        "saw_sources_share": (
            sum(value == "po" for value in source_seen) / len(source_seen)
            if source_seen
            else None
        ),
        "ai_use": {
            value: sum(item["ai_use"] == value for item in participants)
            for value in sorted({item["ai_use"] for item in participants})
        },
        "comments": {
            "liked": [item["liked"] for item in participants if item["liked"]],
            "improve": [item["improve"] for item in participants if item["improve"]],
        },
    }


def report(result: dict) -> str:
    sus = result["sus"]

    lines = [
        "# Studimi pilot i përdorshmërisë",
        "",
        f"Pjesëmarrës: **{result['participants']}**",
        "",
        "## SUS",
        "",
        "| Mesatarja | SD | Mediana | Min | Max | Përshkrimi |",
        "|---:|---:|---:|---:|---:|---|",
        f"| {sus['mean']} | {sus['sd']} | {sus['median']} | {sus['min']} "
        f"| {sus['max']} | {sus['adjective']} |",
        "",
        "Pika krahasuese e zakonshme: mesatarja e SUS nëpër studime është "
        "rreth 68.",
        "",
        "## Besimi dhe burimet (1–5)",
        "",
        "| Pohimi | Mesatarja | SD | Pajtohen (4–5) |",
        "|---|---:|---:|---:|",
    ]

    for item in result["trust"]:
        lines.append(
            f"| {item['statement']} | {item['mean']} | {item['sd']} "
            f"| {item['agree_share']:.0%} |"
        )

    if result["tasks"]:
        lines += [
            "",
            "## Detyrat",
            "",
            "| Detyra | Vetë | Me ndihmë | Dështoi |",
            "|---|---:|---:|---:|",
        ]

        for task, values in result["tasks"].items():
            lines.append(
                f"| {task} | {values['alone']:.0%} | {values['with_help']:.0%} "
                f"| {values['failed']:.0%} |"
            )

    if result["saw_sources_share"] is not None:
        lines += [
            "",
            f"Te D3, {result['saw_sources_share']:.0%} e pjesëmarrësve i panë "
            "burimet poshtë përgjigjes.",
        ]

    for title, key in (("Çfarë u pëlqeu", "liked"), ("Çfarë do të përmirësonin", "improve")):
        if result["comments"][key]:
            lines += ["", f"## {title}", ""]
            lines += [f"- \"{comment}\"" for comment in result["comments"][key]]

    return "\n".join(lines) + "\n"


def main() -> None:
    responses = RESULTS_DIR / "pergjigjet.csv"

    if not responses.exists():
        raise SystemExit(
            f"Mungon {responses}. Shkarko përgjigjet nga Google Forms "
            "(Responses → Download .csv) dhe ruaji aty."
        )

    result = analyse(
        read_responses(responses),
        read_observations(RESULTS_DIR / "vezhgimet.csv"),
    )

    (RESULTS_DIR / "usability.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (RESULTS_DIR / "REPORT.md").write_text(report(result), encoding="utf-8")

    print(
        f"{result['participants']} pjesëmarrës, SUS {result['sus']['mean']} "
        f"({result['sus']['adjective']}). U shkrua {RESULTS_DIR / 'REPORT.md'}"
    )


if __name__ == "__main__":
    main()
