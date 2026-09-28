"""Vlerësimi: metrikat, kufiri i buxhetit dhe integriteti i dataset-it."""

from types import SimpleNamespace

import pytest

from app.ai.agents.orchestrator import AgentResult
from app.ai.agents.registry import AgentName
from app.ai.rag.retriever import RetrievedChunk
from evaluation.budget import BudgetedClient, BudgetExceeded, cost_of
from evaluation.dataset import QUESTIONS, baseline_items, retrieval_items
from evaluation.run_agents import score
from evaluation.scoring import (
    admits_missing_information,
    facts_present,
    hit_rate,
    mean_reciprocal_rank,
    rate,
    routing_scores,
    source_rank,
)
from scripts.demo_documents import DEMO_DOCUMENTS


# --- Metrikat ------------------------------------------------------


def test_facts_need_one_option_from_every_group():
    facts = [["katër", "4"], ["herë"]]

    assert facts_present("Mund ta japësh 4 herë.", facts) is True
    assert facts_present("Mund ta japësh KATËR herë.", facts) is True
    assert facts_present("Mund ta japësh katër.", facts) is False
    assert facts_present("çfarëdo", None) is None


def test_routing_distinguishes_exact_from_covered():
    assert routing_scores(["schedule"], ["schedule"]) == {
        "exact": True,
        "covered": True,
        "primary": True,
    }

    extra = routing_scores(["schedule", "academic"], ["schedule"])
    assert extra["exact"] is False
    assert extra["covered"] is True

    missing = routing_scores(["schedule"], ["schedule", "academic"])
    assert missing["covered"] is False
    assert missing["primary"] is True


def test_source_rank_finds_document_and_page_separately():
    hits = [
        {"file_name": "a.pdf", "page_number": 1},
        {"file_name": "b.pdf", "page_number": 2},
        {"file_name": "b.pdf", "page_number": 3},
    ]

    assert source_rank(hits, "b.pdf", [3]) == (2, 3)
    assert source_rank(hits, "c.pdf", [1]) == (None, None)


def test_hit_rate_and_mrr():
    ranks = [1, 3, None, 2]

    assert hit_rate(ranks, 1) == 0.25
    assert hit_rate(ranks, 3) == 0.75
    assert mean_reciprocal_rank(ranks) == pytest.approx((1 + 1 / 3 + 0 + 1 / 2) / 4)


def test_rate_ignores_questions_without_a_check():
    assert rate([True, False, None]) == 0.5
    assert rate([None]) is None


def test_missing_information_is_recognised_in_both_languages():
    assert admits_missing_information(
        "Nuk gjeta informacion të verifikueshëm në dokumentet universitare.",
        False,
    )
    assert admits_missing_information("I could not find verifiable information.", False)
    assert admits_missing_information("çfarëdo", True)
    assert not admits_missing_information("Provimi është më 10 tetor.", False)


# --- Kufiri i buxhetit ---------------------------------------------


class FakeMessages:
    def __init__(self, usage):
        self.usage = usage
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(usage=self.usage, content=[])

    parse = create


def usage(**tokens):
    return SimpleNamespace(**tokens)


def test_cost_uses_every_token_category():
    cost = cost_of(
        usage(
            input_tokens=1_000_000,
            cache_creation_input_tokens=1_000_000,
            cache_read_input_tokens=1_000_000,
            output_tokens=1_000_000,
        ),
        "claude-sonnet-5",
    )

    assert cost == pytest.approx(2.00 + 2.50 + 0.20 + 10.00)


def test_budget_refuses_the_call_after_the_limit_is_reached():
    # Çdo thirrje kushton 0.01 $: 5 000 tokena input me 2 $/1M.
    messages = FakeMessages(usage(input_tokens=5_000))
    client = BudgetedClient(
        client=SimpleNamespace(messages=messages),
        model="claude-sonnet-5",
        max_cost=0.025,
    )

    client.messages.create()
    client.messages.create()
    client.messages.create()

    with pytest.raises(BudgetExceeded):
        client.messages.create()

    # Thirrja e refuzuar nuk arriti te API-ja.
    assert messages.calls == 3
    assert client.spent == pytest.approx(0.03)


def test_budget_rejects_a_model_without_prices():
    with pytest.raises(ValueError):
        BudgetedClient(
            client=SimpleNamespace(messages=FakeMessages(usage())),
            model="model-i-panjohur",
            max_cost=1,
        )


# --- Vlerësimi i një përgjigjeje -----------------------------------


def chunk(file_name: str, page: int) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=1,
        document_id=1,
        document_title="x",
        document_type="REGULATION",
        file_name=file_name,
        page_number=page,
        chunk_index=0,
        section=None,
        content="...",
        score=0.9,
    )


def test_score_reads_routing_facts_and_sources_from_the_result():
    item = next(item for item in QUESTIONS if item["id"] == "A01")

    result = AgentResult(
        answer="Sipas Nenit 4, një lëndë jepet maksimalisht katër herë [1].",
        chunks=[chunk("rregullorja-e-studimeve-bachelor.pdf", 2)],
        agents_used=[AgentName.ACADEMIC.value],
        latency_ms=1200,
    )

    scored = score(item, result)

    assert scored["routing"]["exact"] is True
    assert scored["facts_ok"] is True
    assert scored["source_ok"] is True
    assert scored["admits_missing"] is False


# --- Integriteti i dataset-it --------------------------------------


def test_question_ids_are_unique():
    for items in (QUESTIONS, retrieval_items()):
        ids = [item["id"] for item in items]

        assert len(ids) == len(set(ids))


def test_expected_agents_exist():
    names = {agent.value for agent in AgentName}

    for item in QUESTIONS:
        assert set(item["agents"]) <= names, item["id"]


def test_expected_sources_point_to_real_demo_pages():
    pages = {spec["file_name"]: len(spec["pages"]) for spec in DEMO_DOCUMENTS}

    for item in retrieval_items():
        file_name, expected_pages = item["source"]

        assert file_name in pages, item["id"]
        assert all(1 <= page <= pages[file_name] for page in expected_pages), item["id"]


def test_every_question_has_something_to_check():
    for item in QUESTIONS:
        checks = (
            item.get("facts")
            or item.get("artifact")
            or item.get("answerable") is False
            or item["category"] == "guardrail"
        )

        assert checks, item["id"]


def test_baseline_questions_have_facts():
    assert baseline_items()
    assert all(item.get("facts") for item in baseline_items())
