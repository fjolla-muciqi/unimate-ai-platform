"""Prompt caching.

Dështimi i caching-ut është i heshtur: kërkesat vazhdojnë të kthejnë
përgjigje të sakta, thjesht fatura rritet. Asnjë gabim nuk ngrihet,
prandaj vetëm një test e kap kur dikush e prish pa e vënë re.

Këto teste nuk thërrasin Claude-in; ato verifikojnë **formën e
kërkesës** që del nga orkestruesi — shënuesit e cache-it, dhe faktin
që prefiksi mbetet identik nëpër iteracione.
"""

from types import SimpleNamespace

import pytest

from app.ai.agents import orchestrator
from app.ai.agents.tools import (
    TOOL_DEFINITIONS,
    SourceRegistry,
    ToolContext,
)
from tests.test_agent_loop import (
    FakeClient,
    FakeResponse,
    text_block,
    tool_use_block,
)


# Minimumi i tokenave për të cilin Sonnet 5 pranon të krijojë cache.
# Nën këtë prag shënuesi injorohet pa asnjë gabim.
SONNET_5_CACHE_MINIMUM = 1024

# Sa karaktere zë mesatarisht një token në tekst latin. Përafrim i
# qëllimshëm: testi kërkon vetëm siguri se nuk jemi afër pragut.
CHARS_PER_TOKEN = 4


@pytest.fixture
def context(db_session, student_user, academic_data):
    """I njëjti kontekst si te testet e ciklit agentik."""

    return ToolContext(
        db=db_session,
        user=student_user,
        profile=academic_data["profile"],
        sources=SourceRegistry(),
    )


@pytest.fixture
def single_answer_client(monkeypatch):
    """Klient që përgjigjet menjëherë, pa thirrur tools."""

    client = FakeClient(
        [FakeResponse(stop_reason="end_turn", content=[text_block("Përshëndetje.")])]
    )

    monkeypatch.setattr(
        orchestrator,
        "get_anthropic_client",
        lambda: client,
    )

    return client


def test_system_prompt_is_sent_as_a_cacheable_block(
    single_answer_client,
    context,
):
    """System-i duhet të jetë listë blloqesh, jo varg i thjeshtë.

    Një varg i thjeshtë nuk mban dot `cache_control`, prandaj kthimi
    te `system=build_system_prompt()` do ta çaktivizonte caching-un pa
    prishur asgjë tjetër.
    """

    orchestrator.run_agent("Përshëndetje", context)

    request = single_answer_client.messages.requests[0]
    system = request["system"]

    assert isinstance(system, list), "system duhet të jetë listë blloqesh"
    assert len(system) == 1

    block = system[0]

    assert block["type"] == "text"
    assert block["cache_control"] == {"type": "ephemeral"}
    assert block["text"].startswith("Ti je UniMate")


def test_conversation_tail_uses_automatic_caching(
    single_answer_client,
    context,
):
    """Breakpoint-i automatik mbulon historikun që rritet."""

    orchestrator.run_agent("Përshëndetje", context)

    request = single_answer_client.messages.requests[0]

    assert request["cache_control"] == {"type": "ephemeral"}


def test_cached_prefix_is_identical_across_iterations(context, monkeypatch):
    """Prefiksi nuk guxon të ndryshojë mes iteracioneve.

    Caching-u është përputhje prefiksi: një byte i vetëm i ndryshuar
    para breakpoint-it e zeron ripërdorimin. Ky është testi që kap një
    timestamp ose një id të rastësishëm të futur në system prompt.
    """

    client = FakeClient(
        [
            FakeResponse(
                stop_reason="tool_use",
                content=[tool_use_block("t1", "get_my_exams", {})],
            ),
            FakeResponse(
                stop_reason="end_turn",
                content=[text_block("Provimi yt është më 15.01.2026.")],
            ),
        ]
    )

    monkeypatch.setattr(
        orchestrator,
        "get_anthropic_client",
        lambda: client,
    )

    orchestrator.run_agent("Kur e kam provimin?", context)

    requests = client.messages.requests

    assert len(requests) == 2, "priteshin dy iteracione"

    first, second = requests

    assert first["system"] == second["system"]
    assert first["tools"] == second["tools"]
    assert first["model"] == second["model"]

    # Historiku duhet të rritet, përndryshe testi i mësipërm nuk
    # provon asgjë: prefiksi do të ishte identik sepse asgjë s'u shtua.
    assert len(second["messages"]) > len(first["messages"])

    # Dhe rritja duhet të jetë shtesë në fund, jo rishkrim i historikut.
    assert second["messages"][: len(first["messages"])] == first["messages"]


def test_cacheable_prefix_stays_above_the_model_minimum():
    """Prefiksi duhet të mbetet mjaftueshëm i madh për t'u ruajtur.

    Nëse dikush shkurton system prompt-in ose heq tools, caching-u
    ndalet pa dhënë asnjë sinjal. Ky test e bën heshtjen të zhurmshme.
    """

    system_chars = len(orchestrator.build_system_prompt())

    tools_chars = sum(
        len(tool["name"])
        + len(tool["description"])
        + len(str(tool["input_schema"]))
        for tool in TOOL_DEFINITIONS
    )

    estimated_tokens = (system_chars + tools_chars) / CHARS_PER_TOKEN

    assert estimated_tokens > SONNET_5_CACHE_MINIMUM, (
        f"Prefiksi i ruajtshëm zbriti te ~{estimated_tokens:.0f} tokena, "
        f"nën minimumin {SONNET_5_CACHE_MINIMUM} të Sonnet 5. "
        "Caching-u është çaktivizuar në heshtje."
    )


def test_record_usage_survives_a_response_without_usage():
    """Klientët e simuluar nuk kanë `usage`; logimi s'duhet të pengojë."""

    orchestrator.record_usage(SimpleNamespace())
    orchestrator.record_usage(SimpleNamespace(usage=None))


def test_record_usage_logs_the_three_token_counts(caplog):
    response = SimpleNamespace(
        usage=SimpleNamespace(
            cache_read_input_tokens=3600,
            cache_creation_input_tokens=0,
            input_tokens=120,
            output_tokens=210,
        )
    )

    with caplog.at_level("INFO"):
        orchestrator.record_usage(response)

    assert "cache_read=3600" in caplog.text
    assert "cache_write=0" in caplog.text
    assert "fresh=120" in caplog.text
