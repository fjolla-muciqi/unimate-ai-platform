"""AI Tutor Agent.

Ndryshe nga agjentët e tjerë, ky nuk lexon vetëm nga baza — ai
gjeneron përmbajtje mësimore. Prandaj ka thirrjen e vet te modeli,
me prompt të veçantë dhe dalje të strukturuar me Pydantic, kështu që
frontend-i mund t'i shfaqë quiz-et dhe flashcards si komponentë të
vërtetë e jo si tekst i lirë.

Materiali vjen nga syllabus-i i lëndës dhe nga dokumentet e
universitetit, që tutori të mos shpikë përmbajtje jashtë programit.
"""

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.llm.client import get_anthropic_client
from app.ai.rag.retriever import retrieve_context
from app.core.config import settings
from app.models.course import Course


MAX_MATERIAL_CHARS = 12000


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: int
    explanation: str


class Quiz(BaseModel):
    topic: str
    questions: list[QuizQuestion]


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardSet(BaseModel):
    topic: str
    cards: list[Flashcard]


TUTOR_SYSTEM_PROMPT = """\
Ti je AI Tutor i UniMate, që ndihmon studentët universitarë.

- Bazohu vetëm në materialin e dhënë. Mos shto përmbajtje që nuk
  gjendet aty.
- Nëse materiali është i pamjaftueshëm, thuaje qartë në vend që të
  shpikësh.
- Përshtate nivelin e shpjegimit sipas nivelit të kërkuar.
- Shkruaj në gjuhën e kërkesës së studentit.
"""


def collect_material(
    topic: str,
    db: Session,
    course_code: str | None = None,
) -> str:
    """Mbledh syllabus-in e lëndës dhe fragmentet relevante nga
    dokumentet, si bazë faktike për tutorin."""

    parts: list[str] = []

    if course_code:
        course = db.scalar(
            select(Course).where(Course.code == course_code.upper())
        )

        if course is not None:
            parts.append(
                f"Lënda: {course.name} ({course.code}), "
                f"{course.ects} ECTS, semestri {course.semester}."
            )

            if course.description:
                parts.append(f"Përshkrimi: {course.description}")

            if course.syllabus:
                parts.append(f"Syllabus:\n{course.syllabus}")

    chunks = retrieve_context(
        query=topic,
        db=db,
        limit=6,
    )

    for chunk in chunks:
        label = chunk.document_title or chunk.file_name or "Dokument"
        parts.append(f"Nga {label}:\n{chunk.content}")

    material = "\n\n".join(parts)

    return material[:MAX_MATERIAL_CHARS]


def _call_model(prompt: str, max_tokens: int | None = None) -> str:
    client = get_anthropic_client()

    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=max_tokens or settings.llm_max_tokens,
        system=TUTOR_SYSTEM_PROMPT,
        output_config={"effort": settings.llm_effort},
        messages=[{"role": "user", "content": prompt}],
    )

    if response.stop_reason == "refusal":
        return "Nuk mund ta gjeneroj këtë material."

    return "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()


def _parse_model(prompt: str, output_format: type[BaseModel]):
    client = get_anthropic_client()

    response = client.messages.parse(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        system=TUTOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        output_format=output_format,
    )

    return response.parsed_output


def explain_topic(
    topic: str,
    db: Session,
    course_code: str | None = None,
    level: str = "intermediate",
) -> str:
    material = collect_material(topic, db, course_code)

    if not material:
        return (
            f"Nuk gjeta material mbi '{topic}' në syllabus-et apo "
            "dokumentet e universitetit."
        )

    answer = _call_model(
        "Shpjego temën më poshtë për një student në nivelin "
        f"'{level}'. Përdor shembuj konkretë dhe mbaje nën 400 fjalë.\n\n"
        f"Tema: {topic}\n\nMateriali:\n{material}"
    )

    return answer


def summarize_material(
    topic: str,
    db: Session,
    course_code: str | None = None,
) -> str:
    material = collect_material(topic, db, course_code)

    if not material:
        return f"Nuk gjeta material mbi '{topic}' për ta përmbledhur."

    return _call_model(
        "Përmblidh materialin më poshtë në pika kryesore, maksimum "
        f"10 pika.\n\nTema: {topic}\n\nMateriali:\n{material}"
    )


def generate_quiz(
    topic: str,
    db: Session,
    course_code: str | None = None,
    question_count: int = 5,
) -> Quiz | None:
    material = collect_material(topic, db, course_code)

    if not material:
        return None

    question_count = max(1, min(question_count, 10))

    return _parse_model(
        f"Krijo {question_count} pyetje me zgjedhje të shumëfishta mbi "
        "materialin më poshtë. Secila pyetje ka 4 opsione, vetëm një e "
        "saktë, dhe një shpjegim të shkurtër pse ajo është e saktë. "
        "correct_index është indeksi nga 0 i opsionit të saktë.\n\n"
        f"Tema: {topic}\n\nMateriali:\n{material}",
        Quiz,
    )


def generate_flashcards(
    topic: str,
    db: Session,
    course_code: str | None = None,
    card_count: int = 8,
) -> FlashcardSet | None:
    material = collect_material(topic, db, course_code)

    if not material:
        return None

    card_count = max(1, min(card_count, 20))

    return _parse_model(
        f"Krijo {card_count} flashcards nga materiali më poshtë. "
        "Pjesa 'front' është një term ose pyetje e shkurtër, 'back' "
        "është përgjigjja e saktë dhe koncize.\n\n"
        f"Tema: {topic}\n\nMateriali:\n{material}",
        FlashcardSet,
    )
