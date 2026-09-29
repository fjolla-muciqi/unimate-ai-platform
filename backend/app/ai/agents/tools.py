"""Tools që i vihen në dispozicion modelit.

Çdo tool i përket një agjenti të vetëm (shih registry.py), kështu që
nga tools e thirrura dimë cilët agjentë e trajtuan pyetjen. Burimet e
dokumenteve mblidhen në SourceRegistry, që numrat e citimeve [1], [2]
të mbeten të njëjtë edhe kur retrieval-i thirret disa herë brenda një
pyetjeje të vetme.
"""

import json
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agents.academic_agent import (
    DAY_ORDER,
    answer_course_catalog,
    answer_course_details,
    answer_courses,
    answer_deadlines,
    answer_exams,
    answer_notifications,
    answer_profile,
    answer_schedule,
)
from app.ai.agents.registry import AgentName, agent_for_tool
from app.ai.agents import professor_agent, tutor_agent
from app.ai.rag.retriever import RetrievedChunk, retrieve_context
from app.models.course import Course
from app.models.document import Document
from app.models.professor import Professor
from app.models.student_profile import StudentProfile
from app.models.user import User


# Tools që varen nga profili i studentit të kyçur.
PERSONAL_TOOLS = {
    "get_my_courses",
    "get_my_schedule",
    "get_my_exams",
    "get_my_profile",
    "get_my_students",
}

NO_STUDENTS_MESSAGE = (
    "Vetëm profesorët kanë studentë të caktuar. Ky përdorues është "
    "student, prandaj kjo listë nuk ekziston për të."
)

NO_PROFILE_MESSAGE = (
    "Ky përdorues nuk ka profil studenti, prandaj të dhënat "
    "personale akademike nuk janë të disponueshme. Përgjigju "
    "vetëm nga dokumentet e universitetit."
)

DEADLINE_TYPES = [
    "REGISTRATION",
    "PAYMENT",
    "APPLICATION",
    "GRADUATION",
    "EVENT",
    "OTHER",
]


class SourceRegistry:
    """Numëron chunks unike sipas radhës së parë të shfaqjes."""

    def __init__(self) -> None:
        self._numbers: dict[tuple, int] = {}
        self.chunks: list[RetrievedChunk] = []

    def register(self, chunk: RetrievedChunk) -> int:
        key = (chunk.chunk_id, chunk.document_id, chunk.chunk_index)

        if key in self._numbers:
            return self._numbers[key]

        number = len(self.chunks) + 1

        self._numbers[key] = number
        self.chunks.append(chunk)

        return number


@dataclass
class ToolContext:
    """Gjithçka që tools-at kanë nevojë për ta ekzekutuar një
    kërkesë, e lidhur me përdoruesin që bëri pyetjen."""

    db: Session
    user: User
    profile: StudentProfile | None

    # Vetëm njëra nga `profile` dhe `professor` mbushet, sipas rolit
    # te JWT-ja. Tools personale e zgjedhin degën prej saj.
    professor: Professor | None = None

    sources: SourceRegistry = field(default_factory=SourceRegistry)
    document_id: int | None = None

    # Dokumentet që i lejohen përdoruesit (`rag/scope.py`); None = të gjitha.
    document_ids: list[int] | None = None

    # Agjentët e aktivizuar, në radhën e parë të përdorimit.
    agents_used: list[AgentName] = field(default_factory=list)

    # Përmbajtja e strukturuar (quiz, flashcards) që frontend-i e
    # shfaq si komponentë, jo si tekst brenda përgjigjes.
    artifacts: list[dict] = field(default_factory=list)

    def record_agent(self, tool_name: str) -> None:
        agent = agent_for_tool(tool_name)

        if agent is not None and agent not in self.agents_used:
            self.agents_used.append(agent)


TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "search_university_documents",
        "description": (
            "Kërko në dokumentet e universitetit (rregullore, syllabuse, "
            "udhëzues, njoftime) dhe në materialet e lëndëve (ligjërata "
            "dhe ushtrime javore) me kërkim semantik. Përdore për çdo "
            "pyetje mbi rregulla, procedura, afate, kushte, përmbajtje "
            "lëndësh ose tema mësimore. Kthen fragmente të numëruara "
            "[1], [2] që duhen cituar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Pyetja ose fjalët kyçe për kërkim, "
                        "në gjuhën e dokumenteve."
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "description": "Sa fragmente të kthehen (1-10).",
                    "minimum": 1,
                    "maximum": 10,
                },
                "course_code": {
                    "type": "string",
                    "description": (
                        "Kufizo te materialet e një lënde (p.sh. CS201), "
                        "kur pyetja është për një lëndë të caktuar."
                    ),
                },
                "week": {
                    "type": "integer",
                    "description": (
                        "Kufizo te materialet e një jave (1-15), kur "
                        "pyetja përmend javën."
                    ),
                    "minimum": 1,
                    "maximum": 15,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_courses",
        "description": (
            "Lëndët e përdoruesit aktual, me kodin, semestrin dhe "
            "ECTS. Për një student: lëndët ku është i regjistruar. "
            "Për një profesor: lëndët që ligjëron, me numrin e "
            "studentëve. Sistemi e zgjedh vetë sipas rolit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_course_details",
        "description": (
            "Detajet e plota të një lënde: profesori dhe konsultimet, "
            "parakushtet, syllabus-i, ECTS dhe orari i ligjëratave. "
            "Përdore kur pyetja është për një lëndë të caktuar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "course_code": {
                    "type": "string",
                    "description": "Kodi i lëndës, p.sh. CS201.",
                },
            },
            "required": ["course_code"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_course_catalog",
        "description": (
            "Kërko në katalogun e plotë të lëndëve të universitetit, "
            "përfshirë lëndë ku studenti nuk është i regjistruar. "
            "Përdore për të gjetur kodin e një lënde nga emri, ose "
            "për të parë lëndët e një semestri."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Pjesë e emrit të lëndës.",
                },
                "semester": {
                    "type": "integer",
                    "description": "Numri i semestrit (1-8).",
                    "minimum": 1,
                    "maximum": 8,
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_schedule",
        "description": (
            "Orari javor i përdoruesit aktual: dita, ora, salla dhe "
            "lënda. Për një student, ligjëratat që ndjek; për një "
            "profesor, ato që jep. Filtro sipas ditës kur pyetja "
            "është për një ditë të caktuar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "day_of_week": {
                    "type": "string",
                    "description": "Dita në anglisht, p.sh. Monday.",
                    "enum": DAY_ORDER,
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_exams",
        "description": (
            "Provimet e përdoruesit aktual me datë, orë, sallë dhe "
            "lloj. Për një student, provimet që jep; për një profesor, "
            "provimet e lëndëve të tij me numrin e kandidatëve. "
            "Si parazgjedhje kthen vetëm provimet e ardhshme."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "only_upcoming": {
                    "type": "boolean",
                    "description": (
                        "true = vetëm provimet e ardhshme (parazgjedhje), "
                        "false = i gjithë historiku."
                    ),
                },
                "course_code": {
                    "type": "string",
                    "description": (
                        "Kodi i lëndës, p.sh. CS201, kur pyetja është "
                        "për një lëndë të vetme."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_deadlines",
        "description": (
            "Afatet administrative dhe eventet: regjistrime, pagesa, "
            "aplikime, diplomim. Përdore për pyetje si 'kur mbyllet "
            "afati i regjistrimit' ose 'sa kohë kam për pagesën'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "deadline_type": {
                    "type": "string",
                    "description": "Filtro sipas llojit të afatit.",
                    "enum": DEADLINE_TYPES,
                },
                "only_upcoming": {
                    "type": "boolean",
                    "description": (
                        "true = vetëm afatet e ardhshme (parazgjedhje)."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_profile",
        "description": (
            "Profili i përdoruesit aktual. Për një student: numri, "
            "programi, viti dhe semestri. Për një profesor: fakulteti, "
            "zyra dhe orari i konsultimeve. Përdore kur përgjigjja "
            "varet nga programi, viti ose pozita."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_students",
        "description": (
            "Studentët e regjistruar në lëndët që ligjëron profesori "
            "aktual, të grupuar sipas lëndës. Vetëm për profesorë — "
            "për një student nuk kthen asgjë. Sistemi e kufizon "
            "gjithmonë te lëndët e vetë profesorit, edhe nëse kërkohet "
            "një kod tjetër."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "course_code": {
                    "type": "string",
                    "description": (
                        "Kufizo te një lëndë e vetme, p.sh. CS201."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_notifications",
        "description": (
            "Njoftimet aktive të publikuara nga administrata për "
            "studentin aktual."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "explain_topic",
        "description": (
            "Shpjegon një temë mësimore bazuar në syllabus-in e lëndës "
            "dhe dokumentet e universitetit. Përdore kur studenti "
            "kërkon të kuptojë diçka, jo thjesht të gjejë një fakt. "
            "Mund të japë edhe përmbledhje materiali."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Tema që duhet shpjeguar.",
                },
                "course_code": {
                    "type": "string",
                    "description": "Kodi i lëndës, nëse dihet.",
                },
                "level": {
                    "type": "string",
                    "description": (
                        "Niveli i shpjegimit. Jepe vetëm kur studenti "
                        "e kërkon shprehimisht (p.sh. 'shpjegoma thjesht'); "
                        "përndryshe përcaktohet nga viti i tij akademik."
                    ),
                    "enum": ["beginner", "intermediate", "advanced"],
                },
                "summarize": {
                    "type": "boolean",
                    "description": (
                        "true për përmbledhje në pika, false për "
                        "shpjegim të plotë (parazgjedhje)."
                    ),
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
    {
        "name": "generate_quiz",
        "description": (
            "Gjeneron një quiz me pyetje me zgjedhje të shumëfishta "
            "mbi një temë, bazuar në materialin e lëndës. Përdore kur "
            "studenti kërkon të testojë njohuritë ose të ushtrohet."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Tema e quiz-it.",
                },
                "course_code": {
                    "type": "string",
                    "description": "Kodi i lëndës, nëse dihet.",
                },
                "question_count": {
                    "type": "integer",
                    "description": "Sa pyetje (1-10).",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
    {
        "name": "generate_flashcards",
        "description": (
            "Gjeneron flashcards (term në njërën anë, shpjegim në "
            "tjetrën) mbi një temë, për përsëritje të shpejtë."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Tema e flashcards.",
                },
                "course_code": {
                    "type": "string",
                    "description": "Kodi i lëndës, nëse dihet.",
                },
                "card_count": {
                    "type": "integer",
                    "description": "Sa karta (1-20).",
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
]


def _run_document_search(
    tool_input: dict,
    context: ToolContext,
) -> str:
    query = (tool_input.get("query") or "").strip()

    if not query:
        return "Gabim: parametri 'query' është bosh."

    document_ids = context.document_ids
    course_code = (tool_input.get("course_code") or "").strip().upper()
    week = tool_input.get("week")

    # Filtri i lëndës dhe javës ngushton dokumentet e lejuara, kurrë nuk
    # i zgjeron: modeli nuk mund të arrijë materiale jashtë qasjes.
    if course_code or week:
        narrowed = select(Document.id).where(Document.is_active.is_(True))

        if course_code:
            narrowed = narrowed.join(
                Course, Course.id == Document.course_id
            ).where(Course.code == course_code)

        if week:
            narrowed = narrowed.where(Document.week == week)

        candidates = set(context.db.scalars(narrowed))

        if document_ids is not None:
            candidates &= set(document_ids)

        if not candidates:
            label = " ".join(
                part
                for part in (course_code, f"java {week}" if week else "")
                if part
            )

            return (
                f"Nuk ka materiale të disponueshme për {label}. Provo "
                "kërkimin pa kufizimin e lëndës ose të javës."
            )

        document_ids = sorted(candidates)

    chunks = retrieve_context(
        query=query,
        db=context.db,
        limit=tool_input.get("top_k"),
        document_id=context.document_id,
        document_ids=document_ids,
    )

    if not chunks:
        return (
            "Nuk u gjet asnjë fragment relevant në dokumentet e "
            "universitetit për këtë kërkim."
        )

    parts: list[str] = []

    for chunk in chunks:
        number = context.sources.register(chunk)

        label = chunk.document_title or chunk.file_name or "Dokument"

        if chunk.page_number is not None:
            label = f"{label}, faqe {chunk.page_number}"

        parts.append(f"[{number}] {label}\n{chunk.content}")

    return "\n\n---\n\n".join(parts)


def _run_tutor_explain(
    tool_input: dict,
    context: ToolContext,
) -> str:
    topic = tool_input["topic"]
    course_code = tool_input.get("course_code")

    if tool_input.get("summarize"):
        return tutor_agent.summarize_material(
            topic=topic,
            db=context.db,
            course_code=course_code,
            document_ids=context.document_ids,
        )

    return tutor_agent.explain_topic(
        topic=topic,
        db=context.db,
        course_code=course_code,
        level=(
            tool_input.get("level")
            or tutor_agent.level_for_student(context.profile)
        ),
        document_ids=context.document_ids,
    )


def _run_generate_quiz(
    tool_input: dict,
    context: ToolContext,
) -> str:
    quiz = tutor_agent.generate_quiz(
        topic=tool_input["topic"],
        db=context.db,
        course_code=tool_input.get("course_code"),
        question_count=tool_input.get("question_count", 5),
        document_ids=context.document_ids,
    )

    if quiz is None:
        return (
            "Nuk gjeta material të mjaftueshëm për ta gjeneruar "
            "quiz-in mbi këtë temë."
        )

    context.artifacts.append(
        {"type": "quiz", "data": quiz.model_dump()}
    )

    # Modelit i mjafton përmbledhja: quiz-i i plotë shkon te
    # frontend-i si artifact, jo brenda tekstit të përgjigjes.
    return (
        f"Quiz-i u gjenerua me {len(quiz.questions)} pyetje mbi "
        f"'{quiz.topic}' dhe i është shfaqur studentit. Njoftoje "
        "shkurt dhe mos i rilisto pyetjet."
    )


def _run_generate_flashcards(
    tool_input: dict,
    context: ToolContext,
) -> str:
    cards = tutor_agent.generate_flashcards(
        topic=tool_input["topic"],
        db=context.db,
        course_code=tool_input.get("course_code"),
        card_count=tool_input.get("card_count", 8),
        document_ids=context.document_ids,
    )

    if cards is None:
        return (
            "Nuk gjeta material të mjaftueshëm për ta gjeneruar "
            "flashcards mbi këtë temë."
        )

    context.artifacts.append(
        {"type": "flashcards", "data": cards.model_dump()}
    )

    return (
        f"U gjeneruan {len(cards.cards)} flashcards mbi "
        f"'{cards.topic}' dhe i janë shfaqur studentit. Njoftoje "
        "shkurt dhe mos i rilisto kartat."
    )


def execute_tool(
    name: str,
    tool_input: dict,
    context: ToolContext,
) -> str:
    """Ekzekuton një tool dhe kthen rezultatin si tekst."""

    if agent_for_tool(name) is None:
        return f"Gabim: tool i panjohur '{name}'."

    context.record_agent(name)

    if name == "search_university_documents":
        return _run_document_search(tool_input, context)

    if name == "search_course_catalog":
        return answer_course_catalog(
            db=context.db,
            query_text=tool_input.get("query"),
            semester=tool_input.get("semester"),
        )

    if name == "get_course_details":
        return answer_course_details(
            db=context.db,
            course_code=tool_input["course_code"],
        )

    if name == "get_deadlines":
        return answer_deadlines(
            db=context.db,
            profile=context.profile,
            only_upcoming=tool_input.get("only_upcoming", True),
            deadline_type=tool_input.get("deadline_type"),
        )

    if name == "get_my_notifications":
        return answer_notifications(
            db=context.db,
            profile=context.profile,
        )

    if name == "explain_topic":
        return _run_tutor_explain(tool_input, context)

    if name == "generate_quiz":
        return _run_generate_quiz(tool_input, context)

    if name == "generate_flashcards":
        return _run_generate_flashcards(tool_input, context)

    # Nga këtu poshtë janë tools personale. Cili grup funksionesh
    # ekzekutohet varet nga roli i vërtetuar te JWT-ja, kurrë nga
    # ndonjë parametër që e zgjedh modeli.
    professor = context.professor

    if professor is not None:
        if name == "get_my_students":
            return professor_agent.answer_students(
                professor,
                context.db,
                course_code=tool_input.get("course_code"),
            )

        if name == "get_my_courses":
            return professor_agent.answer_courses(professor, context.db)

        if name == "get_my_schedule":
            return professor_agent.answer_schedule(
                professor,
                context.db,
                day_of_week=tool_input.get("day_of_week"),
            )

        if name == "get_my_exams":
            return professor_agent.answer_exams(
                professor,
                context.db,
                only_upcoming=tool_input.get("only_upcoming", True),
                course_code=tool_input.get("course_code"),
            )

        return professor_agent.answer_profile(professor, context.db)

    profile = context.profile

    if profile is None:
        return NO_PROFILE_MESSAGE

    if name == "get_my_students":
        return NO_STUDENTS_MESSAGE

    if name == "get_my_courses":
        return answer_courses(profile, context.db)

    if name == "get_my_schedule":
        return answer_schedule(
            profile,
            context.db,
            day_of_week=tool_input.get("day_of_week"),
        )

    if name == "get_my_exams":
        return answer_exams(
            profile,
            context.db,
            only_upcoming=tool_input.get("only_upcoming", True),
            course_code=tool_input.get("course_code"),
        )

    return answer_profile(profile, context.db)


def describe_tool_call(name: str, tool_input: dict) -> str:
    """Përfaqësim i shkurtër i një thirrjeje, për logim."""

    return f"{name}({json.dumps(tool_input, ensure_ascii=False)})"
