"""Response Validator.

Komponenti i fundit i diagramit të arkitekturës. Nuk thërret modelin —
kontrollon përgjigjen e gatshme kundrejt burimeve që u përdorën vërtet:

1. Citimet e shpikura: nëse përgjigjja citon [3] kur u regjistruan
   vetëm dy burime, citimi hiqet. Kjo është mbrojtja konkrete kundër
   përgjigjeve të pavërteta.
2. Pyetjet pa përgjigje: kur modeli përdor fjalinë standarde të
   mungesës së informacionit, përgjigjja shënohet si e pazgjidhur dhe
   del në panelin e administratorit.
"""

import re
from dataclasses import dataclass


NO_INFO_SENTENCE = (
    "Nuk gjeta informacion të verifikueshëm në dokumentet universitare."
)

CITATION_PATTERN = re.compile(r"\[(\d{1,2})\]")


@dataclass
class ValidationResult:
    answer: str
    is_unanswered: bool
    removed_citations: list[int]


def validate_answer(
    answer: str,
    source_count: int,
    used_any_agent: bool,
) -> ValidationResult:
    removed: list[int] = []

    def replace(match: re.Match) -> str:
        number = int(match.group(1))

        if 1 <= number <= source_count:
            return match.group(0)

        removed.append(number)

        return ""

    cleaned = CITATION_PATTERN.sub(replace, answer)

    # Heqja e citimeve lë hapësira të dyfishta pas vetes.
    if removed:
        cleaned = re.sub(r" {2,}", " ", cleaned)
        cleaned = re.sub(r" +([.,;:])", r"\1", cleaned)

    cleaned = cleaned.strip()

    # Një përshëndetje nuk ka nevojë për agjentë, prandaj mungesa e
    # tyre nuk e bën përgjigjen "pa përgjigje". I vetmi sinjal i
    # besueshëm është fjalia standarde që e kërkon system prompt-i.
    is_unanswered = NO_INFO_SENTENCE in cleaned

    if not used_any_agent and not cleaned:
        is_unanswered = True

    return ValidationResult(
        answer=cleaned,
        is_unanswered=is_unanswered,
        removed_citations=removed,
    )
