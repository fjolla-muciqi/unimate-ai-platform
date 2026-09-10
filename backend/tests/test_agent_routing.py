"""Routing i agjentëve.

Tema e mat saktësinë e Router Agent-it. Meqë çdo tool i përket një
agjenti të vetëm, routing-u është i vëzhgueshëm nga tools e thirrura:
këto teste fiksojnë atë hartë dhe verifikojnë se bashkëpunimi mes
agjentëve regjistrohet vërtet.
"""

import pytest

from app.ai.agents.registry import (
    AGENT_LABELS,
    TOOL_OWNERS,
    AgentName,
    agent_for_tool,
    label_for,
)
from app.ai.agents.tools import (
    TOOL_DEFINITIONS,
    SourceRegistry,
    ToolContext,
    execute_tool,
)


@pytest.fixture
def context(db_session, student_user, academic_data):
    return ToolContext(
        db=db_session,
        user=student_user,
        profile=academic_data["profile"],
        sources=SourceRegistry(),
    )


def test_every_declared_tool_has_an_owning_agent():
    for definition in TOOL_DEFINITIONS:
        assert agent_for_tool(definition["name"]) is not None, (
            f"Tool-i {definition['name']} nuk i përket asnjë agjenti."
        )


def test_every_agent_has_a_human_label():
    for agent in AgentName:
        assert AGENT_LABELS[agent]
        assert label_for(agent) == AGENT_LABELS[agent]


def test_every_tool_owning_agent_owns_at_least_one_tool():
    """Guardrail-i është përjashtimi i vetëm i pritur.

    Ai nuk i përgjigjet pyetjeve: rrethon orkestrimin dhe shënohet
    te `agents_used` vetëm kur bllokon një kërkesë ose përgjigje.
    Çdo agjent tjetër pa tools do të ishte agjent i vdekur.
    """

    owned = set(TOOL_OWNERS.values())

    for agent in AgentName:
        if agent is AgentName.GUARDRAIL:
            assert agent not in owned, (
                "Guardrail-i nuk duhet të zotërojë tools."
            )
            continue

        assert agent in owned, f"Agjenti {agent} nuk ka asnjë tool."


def test_unknown_agent_label_falls_back_to_the_raw_value():
    assert label_for("i_panjohur") == "i_panjohur"


@pytest.mark.parametrize(
    ("tool_name", "expected"),
    [
        ("get_my_exams", AgentName.SCHEDULE),
        ("get_my_schedule", AgentName.SCHEDULE),
        ("get_deadlines", AgentName.SCHEDULE),
        ("get_my_courses", AgentName.ACADEMIC),
        ("search_university_documents", AgentName.ACADEMIC),
        ("get_course_details", AgentName.ACADEMIC),
        ("generate_quiz", AgentName.TUTOR),
        ("explain_topic", AgentName.TUTOR),
        ("get_my_profile", AgentName.STUDENT_SERVICES),
    ],
)
def test_tools_route_to_the_expected_agent(tool_name, expected):
    assert agent_for_tool(tool_name) is expected


def test_executing_a_tool_records_its_agent(context):
    execute_tool("get_my_exams", {}, context)

    assert context.agents_used == [AgentName.SCHEDULE]


def test_agents_are_recorded_once_and_in_order(context):
    """Multi-Agent Collaboration: një pyetje e vetme mund të
    aktivizojë disa agjentë, secilin një herë."""

    execute_tool("get_my_exams", {}, context)
    execute_tool("get_my_courses", {}, context)
    execute_tool("get_my_schedule", {}, context)
    execute_tool("get_my_profile", {}, context)

    assert context.agents_used == [
        AgentName.SCHEDULE,
        AgentName.ACADEMIC,
        AgentName.STUDENT_SERVICES,
    ]


def test_unknown_tool_records_no_agent(context):
    result = execute_tool("nuk_ekziston", {}, context)

    assert "tool i panjohur" in result
    assert context.agents_used == []
