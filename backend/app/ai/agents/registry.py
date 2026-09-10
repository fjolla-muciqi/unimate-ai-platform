"""Regjistri i agjentëve.

Tema e diplomës kërkon agjentë të emërtuar dhe matje të saktësisë së
routing-ut. Modeli i zgjedh tools vetë (Router Agent implicit), por çdo
tool i përket një agjenti të vetëm, kështu që nga tools e thirrura dimë
gjithmonë cilët agjentë e trajtuan pyetjen. Kjo ruhet me çdo përgjigje
dhe ushqen panelin e analitikës.
"""

from enum import Enum


class AgentName(str, Enum):
    """Agjentët e specifikuar në temë."""

    ACADEMIC = "academic"
    SCHEDULE = "schedule"
    TUTOR = "tutor"
    STUDENT_SERVICES = "student_services"

    # Guardrail-i nuk zotëron tools: ai rrethon orkestrimin dhe
    # shënohet te `agents_used` vetëm kur bllokon diçka.
    GUARDRAIL = "guardrail"


AGENT_LABELS: dict[AgentName, str] = {
    AgentName.ACADEMIC: "Academic Knowledge Agent",
    AgentName.SCHEDULE: "Schedule and Deadline Agent",
    AgentName.TUTOR: "AI Tutor Agent",
    AgentName.STUDENT_SERVICES: "Student Services Agent",
    AgentName.GUARDRAIL: "Guardrail Agent",
}


# Cili agjent e zotëron secilin tool.
TOOL_OWNERS: dict[str, AgentName] = {
    "search_university_documents": AgentName.ACADEMIC,
    "search_course_catalog": AgentName.ACADEMIC,
    "get_my_courses": AgentName.ACADEMIC,
    "get_course_details": AgentName.ACADEMIC,
    "get_my_schedule": AgentName.SCHEDULE,
    "get_my_exams": AgentName.SCHEDULE,
    "get_deadlines": AgentName.SCHEDULE,
    "explain_topic": AgentName.TUTOR,
    "generate_quiz": AgentName.TUTOR,
    "generate_flashcards": AgentName.TUTOR,
    "get_my_profile": AgentName.STUDENT_SERVICES,
    "get_my_notifications": AgentName.STUDENT_SERVICES,
    "get_my_students": AgentName.STUDENT_SERVICES,
}


def agent_for_tool(tool_name: str) -> AgentName | None:
    return TOOL_OWNERS.get(tool_name)


def label_for(agent: AgentName | str) -> str:
    try:
        return AGENT_LABELS[AgentName(agent)]
    except ValueError:
        return str(agent)
