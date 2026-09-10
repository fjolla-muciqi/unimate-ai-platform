from functools import lru_cache

import anthropic

from app.core.config import settings


class LLMNotConfiguredError(RuntimeError):
    """Ngrihet kur mungon ANTHROPIC_API_KEY në .env."""


@lru_cache
def get_anthropic_client() -> anthropic.Anthropic:
    if not settings.anthropic_api_key:
        raise LLMNotConfiguredError(
            "ANTHROPIC_API_KEY nuk është vendosur në .env."
        )

    return anthropic.Anthropic(
        api_key=settings.anthropic_api_key,
    )
