"""Guardrail Agent.

Kontrolli i sigurisë që rrethon çdo bisedë: një herë para se pyetja
t'u kalojë agjentëve dhe një herë para se përgjigjja t'i shkojë
studentit.

Pse rregulla determinist dhe jo një thirrje te modeli: guardrail-i
duhet të jetë i shpejtë, i parashikueshëm dhe i testueshëm. Një model
që vendos vetë nëse një kërkesë është e sigurt mund të bindet me
prompt-in e radhës — pikërisht sulmin që po mbron.

Kjo është shtresa e parë. Garancia e vërtetë që një student nuk lexon
të dhënat e një tjetri nuk qëndron këtu, por te `tools.py`: çdo tool
personal merr `StudentProfile`-in e nxjerrë nga JWT-ja e kërkesës, dhe
asnjë tool nuk pranon një id studenti nga modeli. Guardrail-i e ndalon
tentativën herët dhe e regjistron; kodi e bën atë të pamundur.
"""

import re
from dataclasses import dataclass

from app.models.audit_log import AuditEvent


@dataclass(frozen=True)
class GuardrailRule:
    """Një rregull i vetëm: emri, ngjarja që logohet dhe pattern-i."""

    name: str
    event_type: str
    pattern: re.Pattern


def _rule(name: str, event_type: str, *patterns: str) -> GuardrailRule:
    return GuardrailRule(
        name=name,
        event_type=event_type,
        pattern=re.compile("|".join(patterns), re.IGNORECASE),
    )


# Tentativa për të mbishkruar udhëzimet e sistemit.
INSTRUCTION_OVERRIDE = _rule(
    "instruction_override",
    AuditEvent.PROMPT_INJECTION_DETECTED,
    r"ignore\s+(all\s+|any\s+)?(the\s+|your\s+)?"
    r"(previous|prior|above|earlier|system)\s+"
    r"(instruction|prompt|rule|message|direction)",
    r"disregard\s+(all\s+|any\s+)?(the\s+|your\s+)?"
    r"(previous|prior|above|earlier|system)",
    r"forget\s+(all\s+|everything\s+|your\s+)?"
    r"(previous\s+)?(instruction|rule|prompt)",
    r"(injoro|shp[eë]rfill|harro)\s+(t[eë]\s+gjitha\s+)?"
    r"(udh[eë]zimet|rregullat|instruksionet|prompt)",
    r"you\s+are\s+now\s+(a|an|the)\b",
    r"\bDAN\s+mode\b",
    r"\bdeveloper\s+mode\b",
    r"pretend\s+(that\s+)?you\s+(are|have|can)",
    r"act\s+as\s+(if\s+you\s+are\s+)?(an?\s+)?"
    r"(admin|administrator|root|system|dev)",
    r"(b[eë]hu|sillu)\s+sikur",
    r"override\s+(your\s+)?(instruction|rule|restriction|guard)",
    r"bypass\s+(your\s+)?"
    r"(restriction|rule|security|filter|guardrail)",
    r"new\s+(system\s+)?(instructions?|prompt)\s*:",
)


# Tentativa për të nxjerrë system prompt-in ose konfigurimin.
SYSTEM_PROMPT_EXTRACTION = _rule(
    "system_prompt_extraction",
    AuditEvent.PROMPT_INJECTION_DETECTED,
    r"(reveal|show|print|repeat|output|display|tell\s+me)\s+"
    r"(me\s+)?(your|the)\s+(full\s+|entire\s+|exact\s+)?"
    r"(system\s+)?(prompt|instruction|rule|configuration|config)",
    r"what\s+(is|are)\s+your\s+(system\s+)?(prompt|instruction)",
    r"repeat\s+everything\s+(above|before)",
    r"(trego|shfaq|printo|p[eë]rs[eë]rit|jep)\s+(m[eë]\s+)?"
    r"(system\s+prompt|prompt-?in|udh[eë]zimet\s+e\s+tua|"
    r"instruksionet\s+e\s+tua|rregullat\s+e\s+tua)",
)


# Kërkesë për të dhënat personale të një personi tjetër.
FOREIGN_STUDENT_DATA = _rule(
    "foreign_student_data",
    AuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
    r"(notat|oraret?|orarin|provimet|l[eë]nd[eë]t|profilin|"
    r"t[eë]\s+dh[eë]nat|numrin\s+personal|adres[eë]n|emailin)\s+"
    r"(e|t[eë])\s+(studentit|studentes|student[eë]ve|kolegut|"
    r"koleges|shokut|shoqes|p[eë]rdoruesit|p[eë]rdoruesve)",
    r"\b(grades?|schedule|exams?|courses?|profile|records?|"
    r"data|email|address)\s+(of|for|belonging\s+to)\s+"
    r"(another\s+|other\s+|the\s+)?(student|user|classmate|person)",
    r"(student|studenti|studentja)\s+(me\s+)?"
    r"(numrin|id-?n?[eë]?|email(in)?)\s",
    r"(notat|provimet|orarin|profilin|t[eë]\s+dh[eë]nat)\s+"
    r"e\s+[A-ZÇË][a-zçë]+",
)


# Kërkesë për të listuar ose eksportuar të dhëna masive.
DATA_ENUMERATION = _rule(
    "data_enumeration",
    AuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
    r"\b(list|show|give|dump|export|print)\s+(me\s+)?"
    r"(all|every|the\s+full)\s+(the\s+)?"
    r"(users?|students?|accounts?|emails?|passwords?|records?)",
    r"\b(listo|trego|nxirr|jep|eksporto)\s+"
    r"(t[eë]\s+gjith[eë]|t[eë]\s+gjitha)\s+"
    r"(p[eë]rdoruesit|student[eë]t|llogarit[eë]|emailet|"
    r"fjal[eë]kalimet)",
    r"\bselect\s+.*\bfrom\s+\w+",
    r"\b(drop|truncate)\s+table\b",
    r"\bdelete\s+from\b",
    r"\b(union\s+select|or\s+1\s*=\s*1)\b",
)


# Kërkesë për sekrete: hash fjalëkalimesh, çelësa, tokena.
CREDENTIAL_REQUEST = _rule(
    "credential_request",
    AuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
    r"\bpassword_hash\b",
    r"\b(passwords?|fjal[eë]kalim\w*)\s+(e|t[eë]|of|for)\s+\w",
    r"\b(api[_\s-]?key|anthropic[_\s-]?key|jwt[_\s-]?secret|"
    r"secret[_\s-]?key|[cç]el[eë]s\w*\s+api)\b",
    r"\b(connection\s+string|database[_\s-]?url|env\s+file)\b",
)


# Tentativë për të pretenduar një rol më të lartë.
ROLE_ESCALATION = _rule(
    "role_escalation",
    AuditEvent.UNAUTHORIZED_ACCESS_ATTEMPT,
    r"\b(i\s*am|i'm)\s+(an?\s+)?(admin|administrator|"
    r"the\s+dean|a\s+professor\s+now)",
    r"\b(jam|un[eë]\s+jam)\s+(admin(istrator)?|dekani)\b",
    r"(give|grant)\s+me\s+(admin|root|full)\s*(access|rights)?",
    r"(m[eë]\s+jep|m[eë]\s+jepni)\s+(akses|t[eë]\s+drejta)\s+"
    r"(admin|t[eë]\s+plot[eë])",
)


INPUT_RULES: list[GuardrailRule] = [
    INSTRUCTION_OVERRIDE,
    SYSTEM_PROMPT_EXTRACTION,
    FOREIGN_STUDENT_DATA,
    DATA_ENUMERATION,
    CREDENTIAL_REQUEST,
    ROLE_ESCALATION,
]


# Sekrete që nuk guxojnë të dalin kurrë në një përgjigje.
SECRET_LEAK = _rule(
    "secret_leak",
    AuditEvent.OUTPUT_BLOCKED,
    r"\$(2[aby]|argon2[a-z0-9]*)\$",
    r"\bsk-ant-[A-Za-z0-9_\-]{10,}",
    r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.",
    r"\bpassword_hash\b",
    r"postgresql(\+\w+)?://[^\s]+:[^\s]+@",
)


# Struktura e brendshme e sistemit nuk i intereson studentit dhe
# ndihmon sulmuesin.
INTERNAL_LEAK = _rule(
    "internal_leak",
    AuditEvent.OUTPUT_BLOCKED,
    r"\bselect\s+.*\bfrom\s+(users|student_profiles|audit_logs)\b",
)


OUTPUT_RULES: list[GuardrailRule] = [
    SECRET_LEAK,
    INTERNAL_LEAK,
]


# Përgjigjet që i kthehen studentit. Të ndara sipas rregullit, që
# refuzimi të mos duket i rastësishëm.
REFUSAL_MESSAGES: dict[str, str] = {
    "instruction_override": (
        "Nuk mund ta ndjek këtë kërkesë. Unë përgjigjem vetëm për "
        "studimet e tua në këtë universitet dhe udhëzimet e mia nuk "
        "ndryshohen nga një mesazh. Pyetmë për orarin, provimet, "
        "lëndët ose rregulloret."
    ),
    "system_prompt_extraction": (
        "Konfigurimi i brendshëm i asistentit nuk është publik. "
        "Mund të të ndihmoj me orarin, provimet, lëndët ose "
        "rregulloret e universitetit."
    ),
    "foreign_student_data": (
        "Të dhënat personale të një studenti tjetër janë të mbrojtura "
        "dhe nuk mund t'i shoh as unë. Të dhënat e tua akademike i "
        "kam dhe mund të t'i tregoj menjëherë."
    ),
    "data_enumeration": (
        "Nuk mund të listoj përdorues apo të dhëna të sistemit. "
        "Pyetmë për informacionin tënd akademik ose për rregulloret "
        "e universitetit."
    ),
    "credential_request": (
        "Fjalëkalimet, çelësat dhe të dhënat e konfigurimit nuk janë "
        "të aksesueshme përmes asistentit."
    ),
    "role_escalation": (
        "Rolet caktohen nga sistemi pas kyçjes, jo nga biseda. Po të "
        "duhet akses tjetër, kontakto administratën."
    ),
}


DEFAULT_REFUSAL = (
    "Nuk mund të përgjigjem për këtë kërkesë. Provo ta riformulosh "
    "si pyetje mbi studimet e tua."
)

OUTPUT_REFUSAL = (
    "Përgjigjja u bllokua nga kontrolli i sigurisë sepse përmbante "
    "informacion jashtë fushës sate të lejuar. Provo ta riformulosh "
    "pyetjen."
)


@dataclass
class GuardrailVerdict:
    """Rezultati i një kontrolli guardrail."""

    allowed: bool
    rule: str | None = None
    event_type: str | None = None
    message: str | None = None
    matched: str | None = None

    @property
    def blocked(self) -> bool:
        return not self.allowed


ALLOWED = GuardrailVerdict(allowed=True)

# Sa karakterë të tekstit që u kap ruhen në AuditLog. Mesazhi i plotë
# mund të jetë i gjatë; për hetim mjafton fragmenti.
MATCH_SNIPPET_LIMIT = 200


def _snippet(text: str) -> str:
    text = " ".join(text.split())

    if len(text) <= MATCH_SNIPPET_LIMIT:
        return text

    return f"{text[:MATCH_SNIPPET_LIMIT]}…"


def check_request(message: str) -> GuardrailVerdict:
    """Guardrail-i hyrës: a lejohet kjo pyetje t'u kalojë agjentëve?"""

    for rule in INPUT_RULES:
        match = rule.pattern.search(message)

        if match is None:
            continue

        return GuardrailVerdict(
            allowed=False,
            rule=rule.name,
            event_type=rule.event_type,
            message=REFUSAL_MESSAGES.get(rule.name, DEFAULT_REFUSAL),
            matched=_snippet(match.group(0)),
        )

    return ALLOWED


# Rreshtat e system prompt-it nën këtë gjatësi janë tepër të
# përgjithshëm për t'u përdorur si gjurmë rrjedhjeje.
PROMPT_MARKER_MIN_LENGTH = 40


def check_response(
    answer: str,
    system_prompt: str | None = None,
) -> GuardrailVerdict:
    """Guardrail-i dalës: a lejohet kjo përgjigje t'i shkojë studentit?

    `system_prompt` jepet që të kapim rastin kur modeli e riprodhon
    udhëzimet e veta fjalë për fjalë, pa i dublikuar ato këtu.
    """

    for rule in OUTPUT_RULES:
        match = rule.pattern.search(answer)

        if match is None:
            continue

        return GuardrailVerdict(
            allowed=False,
            rule=rule.name,
            event_type=rule.event_type,
            message=OUTPUT_REFUSAL,
            matched=_snippet(match.group(0)),
        )

    if system_prompt:
        for line in system_prompt.splitlines():
            line = line.strip()

            if len(line) < PROMPT_MARKER_MIN_LENGTH:
                continue

            if line in answer:
                return GuardrailVerdict(
                    allowed=False,
                    rule="system_prompt_leak",
                    event_type=AuditEvent.OUTPUT_BLOCKED,
                    message=OUTPUT_REFUSAL,
                    matched=_snippet(line),
                )

    return ALLOWED


__all__ = [
    "GuardrailVerdict",
    "check_request",
    "check_response",
    "INPUT_RULES",
    "OUTPUT_RULES",
    "REFUSAL_MESSAGES",
    "DEFAULT_REFUSAL",
    "OUTPUT_REFUSAL",
]
