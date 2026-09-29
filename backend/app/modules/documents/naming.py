"""Java dhe lloji i një materiali, nga emri i skedarit.

Kur ngarkohen shumë ligjërata njëherësh, emri i skedarit është i vetmi
burim për javën: "Java03_Ligjerata.pdf", "Ligjerata 3.pdf",
"Week_03_Lecture.pdf" dhe "03 - Ushtrime.pdf" japin të gjitha javën 3.
"""

import re
import unicodedata
from pathlib import Path

MAX_WEEK = 15

MATERIAL_LABELS = {
    "LECTURE": "Ligjëratë",
    "EXERCISE": "Ushtrime",
    "OTHER": "Material",
}

# Fjalë që paraprijnë numrin e javës.
# `(?<![a-z])`: prefiksi fillon një fjalë, që "w" në mes të një fjale
# ("news2") të mos lexohet si javë.
_WEEK_PREFIX = re.compile(
    r"(?<![a-z])(?:java|jav|week|wk|w|ligjerata|ligjerate|leksioni|leksion|lecture"
    r"|ushtrimet|ushtrime|ushtrimi|exercise|lab|tutorial)"
    r"[\s_\-.]*0*(\d{1,2})(?!\d)"
)

# Numri në fillim të emrit: "03 - Hash tabelat.pdf".
_LEADING_NUMBER = re.compile(r"^0*(\d{1,2})(?!\d)")

_EXERCISE = re.compile(r"ushtrim|exercise|lab|tutorial|detyr")
_LECTURE = re.compile(r"ligjerat|leksion|lecture|slides|prezantim")


def _normalize(file_name: str) -> str:
    text = unicodedata.normalize("NFKD", Path(file_name).stem.lower())

    return "".join(char for char in text if not unicodedata.combining(char))


def parse_week(file_name: str) -> int | None:
    text = _normalize(file_name)

    for pattern in (_WEEK_PREFIX, _LEADING_NUMBER):
        match = pattern.search(text)

        if match:
            week = int(match.group(1))

            return week if 1 <= week <= MAX_WEEK else None

    return None


def parse_material_type(file_name: str) -> str | None:
    text = _normalize(file_name)

    # Ushtrimet kontrollohen të parat: "Ligjerata me ushtrime" janë ushtrime.
    if _EXERCISE.search(text):
        return "EXERCISE"

    if _LECTURE.search(text):
        return "LECTURE"

    return None


def material_title(
    course_code: str,
    week: int | None,
    material_type: str | None,
    group_name: str | None,
    file_name: str,
) -> str:
    """"CS201 · Java 4 · Ligjëratë · Grupi A", që citimet të jenë të qarta."""

    if week is None:
        return Path(file_name).stem

    parts = [course_code, f"Java {week}"]

    if material_type:
        parts.append(MATERIAL_LABELS[material_type])

    if group_name:
        parts.append(group_name)

    return " · ".join(parts)
