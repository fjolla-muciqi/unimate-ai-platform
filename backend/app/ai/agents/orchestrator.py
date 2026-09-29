"""Orchestrator Agent.

Router Agent-i është implicit: modeli vendos vetë cilat tools të
thërrasë, dhe meqë çdo tool i përket një agjenti të vetëm (registry.py),
nga tools e thirrura dimë saktësisht cilët agjentë e trajtuan pyetjen.
Kjo ruhet me çdo përgjigje dhe bëhet metrika e routing-ut.

Përparësia ndaj një router-i që zgjedh një agjent të vetëm: një pyetje
si "Kur e kam provimin e AI dhe çfarë duhet të mësoj?" aktivizon
Schedule Agent, Academic Agent dhe Tutor Agent brenda së njëjtës
përgjigje — pikërisht Multi-Agent Collaboration që kërkon tema.
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.agents import guardrail_agent
from app.ai.agents.registry import AgentName
from app.ai.agents.tools import (
    TOOL_DEFINITIONS,
    SourceRegistry,
    ToolContext,
    execute_tool,
)
from app.ai.agents.validator_agent import (
    NO_INFO_SENTENCE,
    validate_answer,
)
from app.ai.llm.client import get_anthropic_client
from app.ai.rag.scope import accessible_document_ids
from app.ai.rag.retriever import RetrievedChunk
from app.core.audit import record_event
from app.core.config import settings
from app.models.professor import Professor
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = f"""\
Ti je UniMate, asistenti AI i universitetit.

Ke tools nga katër agjentë të specializuar:
- Academic Knowledge Agent: search_university_documents,
  search_course_catalog, get_course_details, get_my_courses.
- Schedule and Deadline Agent: get_my_schedule, get_my_exams,
  get_deadlines.
- AI Tutor Agent: explain_topic, generate_quiz, generate_flashcards.
- Student Services Agent: get_my_profile, get_my_notifications,
  get_my_students.

Rregullat e tua:
- Mos u përgjigj kurrë nga njohuritë e tua të përgjithshme për gjëra
  specifike të këtij universiteti. Përdor tools.
- Thirr sa tools të nevojiten, edhe nga agjentë të ndryshëm. Nëse
  pyetja ka nevojë edhe për rregullore edhe për të dhëna personale,
  merri të dyja.
- Tools me parashtesën "get_my_" i kthejnë gjithmonë të dhënat e
  përdoruesit që bëri pyetjen, të filtruara nga sistemi sipas rolit
  të tij. Ti nuk mund ta ndryshosh se të kujt janë ato të dhëna, dhe
  nuk duhet ta premtosh kurrë një gjë të tillë.
- Kur nuk e di kodin e një lënde, gjeje me search_course_catalog para
  se të thërrasësh tools që kërkojnë kod.
- Kur informacioni vjen nga search_university_documents, cito burimin
  me numrin e tij në kllapa, p.sh. [1], menjëherë pas informacionit.
  Mos përdor kurrë një numër që nuk të është kthyer nga ai tool.
- Të dhënat akademike (orari, provimet, lëndët, afatet) nuk citohen —
  ato vijnë direkt nga sistemi.
- Nëse tools nuk e kthejnë përgjigjen, shkruaj saktësisht këtë fjali
  dhe pastaj sugjero ku mund ta kërkojë përdoruesi:
  "{NO_INFO_SENTENCE}"
- Përgjigju gjithmonë në gjuhën në të cilën u bë pyetja.
- Ji i shkurtër, konkret dhe miqësor. Përdor lista kur informacioni ka
  disa pika. Datat shkruaji si dd.mm.vvvv.
"""


# Konteksti i rolit shtohet në fund të system prompt-it. Kjo prodhon
# një prefiks të veçantë cache-i për secilin rol, gjë e pashmangshme
# dhe e dëshiruar: bisedat e një studenti dhe të një profesori nuk
# kanë pse ta ndajnë të njëjtin prefiks.
ROLE_CONTEXT: dict[UserRole, str] = {
    UserRole.STUDENT: (
        "Përdoruesi aktual është STUDENT. Tools 'get_my_' i kthejnë "
        "lëndët ku është i regjistruar, orarin që ndjek dhe provimet "
        "që do të japë. Tool-i get_my_students nuk vlen për të."
    ),
    UserRole.PROFESSOR: (
        "Përdoruesi aktual është PROFESOR. Tools 'get_my_' i kthejnë "
        "lëndët që ligjëron, orarin e ligjëratave të tij dhe provimet "
        "e lëndëve të tij. Me get_my_students sheh studentët e "
        "regjistruar në ato lëndë — dhe vetëm në ato."
    ),
    UserRole.ADMIN: (
        "Përdoruesi aktual është ADMINISTRATOR dhe nuk ka lëndë të "
        "vetat. Tools 'get_my_' nuk kthejnë të dhëna personale për të; "
        "përgjigju nga dokumentet e universitetit dhe nga katalogu."
    ),
}


FALLBACK_ANSWER = (
    f"{NO_INFO_SENTENCE} Provo ta riformulosh pyetjen ose kontakto "
    "zyrën e studentëve."
)

REFUSAL_ANSWER = (
    "Nuk mund të përgjigjem për këtë kërkesë. "
    "Provo ta riformulosh pyetjen."
)


@dataclass
class AgentResult:
    """Gjithçka që një raund i chat-it prodhon."""

    answer: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    agents_used: list[str] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    latency_ms: int = 0
    is_unanswered: bool = False

    # Bllokimi nga Guardrail Agent-i: cila rregull u aktivizua.
    blocked_by: str | None = None

    @property
    def is_blocked(self) -> bool:
        return self.blocked_by is not None


def get_student_profile(
    user: User,
    db: Session,
) -> StudentProfile | None:
    if user.role != UserRole.STUDENT:
        return None

    return db.scalar(
        select(StudentProfile).where(
            StudentProfile.user_id == user.id
        )
    )


def get_professor_record(
    user: User,
    db: Session,
) -> Professor | None:
    """Profesori i lidhur me këtë llogari, nëse ekziston.

    Lidhja `Professor.user_id` është opsionale: një profesor mund të
    figurojë në katalog pa pasur llogari. Pa këtë rresht, një llogari
    me rol PROFESSOR nuk merr dot asnjë të dhënë të vetën.
    """

    if user.role != UserRole.PROFESSOR:
        return None

    return db.scalar(
        select(Professor).where(Professor.user_id == user.id)
    )


def build_system_prompt(role: UserRole | None = None) -> str:
    """Data e sotme i duhet modelit për të dalluar provimet dhe
    afatet e ardhshme nga ato të kaluara.

    Data ndryshon një herë në ditë, jo për çdo kërkesë, prandaj nuk e
    prish cache-in brenda një sesioni — shih `build_system_blocks`.
    """

    parts = [SYSTEM_PROMPT]

    if role is not None and role in ROLE_CONTEXT:
        parts.append(ROLE_CONTEXT[role])

    parts.append(
        f"Data e sotme është {date.today().strftime('%d.%m.%Y')}."
    )

    return "\n".join(parts)


def build_system_blocks(role: UserRole | None = None) -> list[dict]:
    """System prompt-i si bllok i vetëm, i shënuar për cache.

    Renditja e renderimit është tools -> system -> messages, prandaj
    një breakpoint mbi bllokun e fundit të system-it e ruan në cache
    edhe përkufizimin e 13 tools bashkë me të: rreth 3600 tokena që
    përndryshe paguhen plot në secilin nga 6 iteracionet e ciklit
    agentik. Leximi nga cache kushton 10% të çmimit normal.

    Minimumi i kërkuar për Sonnet 5 është 1024 tokena; prefiksi ynë e
    kalon me shumicë. Nëse dikush e zvogëlon system prompt-in ose heq
    tools nën atë prag, caching-u pushon pa dhënë asnjë gabim — prandaj
    `test_caching.py` e mbron këtë sjellje.
    """

    return [
        {
            "type": "text",
            "text": build_system_prompt(role),
            "cache_control": {"type": "ephemeral"},
        }
    ]


def record_usage(response) -> None:
    """Logon sa tokena u lexuan nga cache dhe sa u paguan plot.

    Dështimi i caching-ut është i heshtur: kërkesat vazhdojnë të
    kthejnë përgjigje të sakta, thjesht fatura rritet. Këta tre numra
    janë e vetmja dëshmi se prefiksi po ripërdoret. Nëse
    `cache_read` mbetet 0 nëpër kërkesa të njëpasnjëshme, diçka para
    breakpoint-it po ndryshon në çdo kërkesë.
    """

    usage = getattr(response, "usage", None)

    if usage is None:
        return

    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    fresh = getattr(usage, "input_tokens", 0) or 0

    logger.info(
        "LLM tokens: cache_read=%s cache_write=%s fresh=%s output=%s",
        cache_read,
        cache_write,
        fresh,
        getattr(usage, "output_tokens", 0) or 0,
    )


def extract_text(content: list) -> str:
    return "".join(
        block.text
        for block in content
        if block.type == "text"
    ).strip()


def run_tool_calls(
    content: list,
    context: ToolContext,
) -> list[dict]:
    """Ekzekuton të gjitha tool_use blocks të një përgjigjeje dhe
    i kthen si tool_result në një mesazh të vetëm."""

    results: list[dict] = []

    for block in content:
        if block.type != "tool_use":
            continue

        try:
            output = execute_tool(
                name=block.name,
                tool_input=dict(block.input),
                context=context,
            )
            is_error = False

        except Exception as exc:  # noqa: BLE001
            # Gabimi i kthehet modelit që ta provojë ndryshe,
            # në vend që t'i prishet e gjithë përgjigjja studentit.
            output = f"Tool-i dështoi: {exc}"
            is_error = True

        results.append(
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
                "is_error": is_error,
            }
        )

    return results


def run_agent(
    question: str,
    context: ToolContext,
    history: list[dict] | None = None,
) -> str:
    """Cikli agentik: pyetje -> tools -> përgjigje përfundimtare."""

    client = get_anthropic_client()

    messages: list[dict] = list(history or [])
    messages.append({"role": "user", "content": question})

    response = None

    for _ in range(settings.agent_max_iterations):
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            system=build_system_blocks(context.user.role),
            # Breakpoint automatik mbi bllokun e fundit të bisedës:
            # historiku rritet me çdo iteracion, dhe kështu secili
            # iteracion lexon nga cache gjithçka që shtoi i mëparshmi.
            cache_control={"type": "ephemeral"},
            output_config={"effort": settings.llm_effort},
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        record_usage(response)

        if response.stop_reason == "refusal":
            return REFUSAL_ANSWER

        if response.stop_reason != "tool_use":
            break

        messages.append(
            {"role": "assistant", "content": response.content}
        )

        messages.append(
            {
                "role": "user",
                "content": run_tool_calls(response.content, context),
            }
        )

    else:
        # Kufiri i iteracioneve u shterua pa përgjigje finale:
        # kërkojmë një përgjigje të fundit pa tools.
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            system=build_system_blocks(context.user.role),
            cache_control={"type": "ephemeral"},
            output_config={"effort": settings.llm_effort},
            messages=messages
            + [
                {
                    "role": "user",
                    "content": (
                        "Përmblidh përgjigjen përfundimtare për "
                        "studentin vetëm me informacionin që ke "
                        "mbledhur deri tani."
                    ),
                }
            ],
        )

        record_usage(response)

    if response is None:
        return FALLBACK_ANSWER

    return extract_text(response.content) or FALLBACK_ANSWER


def handle_chat_message(
    message: str,
    user: User,
    db: Session,
    history: list[dict] | None = None,
    document_id: int | None = None,
) -> AgentResult:
    """Pika hyrëse e chat-it.

    Guardrail (hyrje) -> Router -> agjentë -> validator ->
    Guardrail (dalje). Guardrail-i është unaza e jashtme: asnjë pyetje
    nuk hyn dhe asnjë përgjigje nuk del pa kaluar prej tij.
    """

    started = perf_counter()

    verdict = guardrail_agent.check_request(message)

    if verdict.blocked:
        record_event(
            db=db,
            user_id=user.id,
            event_type=verdict.event_type,
            detail=(
                f"Kërkesa u bllokua para orkestrimit. "
                f"U kap: {verdict.matched}"
            ),
            rule=verdict.rule,
        )

        return AgentResult(
            answer=verdict.message or guardrail_agent.DEFAULT_REFUSAL,
            agents_used=[AgentName.GUARDRAIL.value],
            latency_ms=int((perf_counter() - started) * 1000),
            blocked_by=verdict.rule,
        )

    context = ToolContext(
        db=db,
        user=user,
        profile=get_student_profile(user, db),
        professor=get_professor_record(user, db),
        sources=SourceRegistry(),
        document_id=document_id,
        document_ids=accessible_document_ids(user, db),
    )

    answer = run_agent(
        question=message,
        context=context,
        history=history,
    )

    validation = validate_answer(
        answer=answer,
        source_count=len(context.sources.chunks),
        used_any_agent=bool(context.agents_used),
    )

    final_answer = validation.answer or FALLBACK_ANSWER

    agents_used = [
        agent.value if isinstance(agent, AgentName) else str(agent)
        for agent in context.agents_used
    ]

    output_verdict = guardrail_agent.check_response(
        answer=final_answer,
        system_prompt=build_system_prompt(user.role),
    )

    if output_verdict.blocked:
        record_event(
            db=db,
            user_id=user.id,
            event_type=output_verdict.event_type,
            detail=(
                f"Përgjigjja u bllokua para dërgimit. "
                f"U kap: {output_verdict.matched}"
            ),
            rule=output_verdict.rule,
        )

        # Burimet dhe artifacts hidhen bashkë me përgjigjen: nëse
        # përmbajtja nuk lejohet, as gjurmët e saj nuk duhen dërguar.
        return AgentResult(
            answer=output_verdict.message
            or guardrail_agent.OUTPUT_REFUSAL,
            agents_used=agents_used + [AgentName.GUARDRAIL.value],
            latency_ms=int((perf_counter() - started) * 1000),
            blocked_by=output_verdict.rule,
        )

    return AgentResult(
        answer=final_answer,
        chunks=context.sources.chunks,
        agents_used=agents_used,
        artifacts=context.artifacts,
        latency_ms=int((perf_counter() - started) * 1000),
        is_unanswered=validation.is_unanswered,
    )


__all__ = [
    "AgentResult",
    "handle_chat_message",
    "run_agent",
    "get_student_profile",
    "get_professor_record",
    "FALLBACK_ANSWER",
    "REFUSAL_ANSWER",
]
