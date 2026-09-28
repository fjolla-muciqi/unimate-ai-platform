"""Funksionet e vlerësimit: të pastra, pa bazë dhe pa rrjet."""

from statistics import mean, median


UNANSWERED_MARKERS = (
    "nuk gjeta informacion të verifikueshëm",
    "could not find verifiable information",
    "couldn't find verifiable information",
)


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def facts_present(answer: str, facts: list[list[str]] | None) -> bool | None:
    """Çdo grup duhet të ketë të paktën një fjalë në përgjigje.

    Kthen None kur pyetja nuk ka fakte për t'u kontrolluar, që ajo
    të mos numërohet as si e saktë as si e gabuar.
    """

    if not facts:
        return None

    text = normalize(answer)

    return all(
        any(normalize(option) in text for option in group)
        for group in facts
    )


def admits_missing_information(answer: str, is_unanswered: bool) -> bool:
    """Sistemi e pranon që informacioni mungon, në vend që ta shpikë."""

    text = normalize(answer)

    return is_unanswered or any(marker in text for marker in UNANSWERED_MARKERS)


def routing_scores(used: list[str], expected: list[str]) -> dict:
    """Tri mënyra për ta parë routing-un, nga më e rrepta te më e buta.

    - exact: u aktivizuan saktësisht agjentët e pritur.
    - covered: u aktivizuan të gjithë agjentët e pritur, ndoshta edhe
      të tjerë (p.sh. Academic për të gjetur kodin e lëndës).
    - primary: agjenti i parë i pritur është mes të aktivizuarve.
    """

    used_set = set(used)
    expected_set = set(expected)

    return {
        "exact": used_set == expected_set,
        "covered": expected_set <= used_set,
        "primary": bool(expected) and expected[0] in used_set,
    }


def source_rank(
    hits: list[dict],
    file_name: str,
    pages: list[int],
) -> tuple[int | None, int | None]:
    """Pozicioni (1-based) i dokumentit dhe i faqes së duhur te rezultatet.

    Kthen (rank_dokumenti, rank_faqja); None kur nuk u gjet fare.
    """

    document_rank = None
    page_rank = None

    for position, hit in enumerate(hits, start=1):
        if hit["file_name"] != file_name:
            continue

        if document_rank is None:
            document_rank = position

        if page_rank is None and hit["page_number"] in pages:
            page_rank = position

    return document_rank, page_rank


def hit_rate(ranks: list[int | None], k: int) -> float:
    if not ranks:
        return 0.0

    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks)


def mean_reciprocal_rank(ranks: list[int | None]) -> float:
    if not ranks:
        return 0.0

    return mean(1 / rank if rank else 0.0 for rank in ranks)


def rate(values: list[bool | None]) -> float | None:
    """Përqindja e True mes vlerave që nuk janë None."""

    counted = [value for value in values if value is not None]

    if not counted:
        return None

    return sum(1 for value in counted if value) / len(counted)


def latency_summary(values: list[int]) -> dict:
    if not values:
        return {"mean_ms": None, "median_ms": None}

    return {"mean_ms": round(mean(values)), "median_ms": round(median(values))}
