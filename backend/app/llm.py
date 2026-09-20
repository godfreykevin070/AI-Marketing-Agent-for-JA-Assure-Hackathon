"""Thin, provider-agnostic LLM wrapper (GroqCloud / OpenAI-compatible)."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMUnavailable(RuntimeError):
    """Raised when no LLM credentials are configured."""


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    settings = get_settings()
    if not settings.groq_api_key:
        raise LLMUnavailable("GROQ_API_KEY is not configured")
    if _client is None:
        _client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            timeout=120.0,
            max_retries=2,
        )
    return _client


def is_available() -> bool:
    return get_settings().llm_enabled


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = _FENCE_RE.sub("", text).strip()
    # Keep only the outermost JSON object if the model added prose.
    if not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    return text


def chat_text(
    system: str,
    user: str,
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    settings = get_settings()
    response = _get_client().chat.completions.create(
        model=model or settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=settings.llm_temperature if temperature is None else temperature,
        max_tokens=max_tokens or settings.llm_max_tokens,
    )
    return (response.choices[0].message.content or "").strip()


def chat_json(
    system: str,
    user: str,
    schema: Type[T],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> T:
    """Call the model in JSON mode and validate against a Pydantic schema."""
    settings = get_settings()
    schema_json = json.dumps(schema.model_json_schema())
    system_prompt = (
        f"{system}\n\n"
        "Respond with a SINGLE valid JSON object and nothing else. "
        "Do not wrap it in markdown fences. Do not add commentary. "
        "The JSON must validate against this schema:\n"
        f"{schema_json}"
    )

    def _call(sys_prompt: str, user_prompt: str) -> str:
        response = _get_client().chat.completions.create(
            model=model or settings.llm_model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=settings.llm_temperature if temperature is None else temperature,
            max_tokens=max_tokens or settings.llm_max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"

    raw = _call(system_prompt, user)
    try:
        return schema.model_validate_json(_strip_fences(raw))
    except (ValidationError, ValueError) as exc:
        logger.warning("LLM JSON validation failed, retrying once: %s", exc)
        repair_prompt = (
            f"{user}\n\nYour previous answer was invalid JSON for the schema.\n"
            f"Error: {exc}\nPrevious answer:\n{raw}\n\n"
            "Return ONLY a corrected JSON object."
        )
        raw2 = _call(system_prompt, repair_prompt)
        return schema.model_validate_json(_strip_fences(raw2))


def safe_json_loads(text: str, default: Any = None) -> Any:
    try:
        return json.loads(_strip_fences(text))
    except Exception:  # pragma: no cover - defensive
        return default