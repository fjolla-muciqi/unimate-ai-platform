"""Response Validator: citimet e shpikura dhe pyetjet pa përgjigje."""

from app.ai.agents.validator_agent import (
    NO_INFO_SENTENCE,
    validate_answer,
)


def test_valid_citations_are_kept():
    result = validate_answer(
        "Afati mbyllet më 30.09 [1] dhe pagesa më 15.10 [2].",
        source_count=2,
        used_any_agent=True,
    )

    assert result.answer == (
        "Afati mbyllet më 30.09 [1] dhe pagesa më 15.10 [2]."
    )
    assert result.removed_citations == []
    assert result.is_unanswered is False


def test_invented_citation_is_removed():
    """Modeli citoi [3] kur ekzistonin vetëm dy burime."""

    result = validate_answer(
        "Rregullorja e lejon këtë [3].",
        source_count=2,
        used_any_agent=True,
    )

    assert "[3]" not in result.answer
    assert result.answer == "Rregullorja e lejon këtë."
    assert result.removed_citations == [3]


def test_all_citations_removed_when_there_are_no_sources():
    result = validate_answer(
        "Provimi është më 21.09 [1].",
        source_count=0,
        used_any_agent=True,
    )

    assert result.answer == "Provimi është më 21.09."
    assert result.removed_citations == [1]


def test_no_info_sentence_marks_the_answer_unanswered():
    result = validate_answer(
        f"{NO_INFO_SENTENCE} Kontakto zyrën e studentëve.",
        source_count=0,
        used_any_agent=True,
    )

    assert result.is_unanswered is True


def test_greeting_without_agents_is_not_unanswered():
    result = validate_answer(
        "Përshëndetje! Si mund të të ndihmoj?",
        source_count=0,
        used_any_agent=False,
    )

    assert result.is_unanswered is False


def test_empty_answer_without_agents_is_unanswered():
    result = validate_answer(
        "",
        source_count=0,
        used_any_agent=False,
    )

    assert result.is_unanswered is True
