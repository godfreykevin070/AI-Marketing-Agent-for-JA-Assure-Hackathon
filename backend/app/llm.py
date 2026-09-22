"""Thin LLM wrapper with multi-key rotation across Groq organizations.

Rotates to the next API key on HTTP 429, honouring the `retry-after` header
and the "try again in Xm Ys" message Groq embeds in daily-limit errors.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Type, TypeVar

import openai
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_RETRY_AFTER_BODY_RE = re.compile(
    r"try again in\s+(?:(\d+)m)?\s*([\d.]+)s", re.IGNORECASE
)


class LLMUnavailable(RuntimeError):
    """Raised when no LLM credentials are configured."""


# ---------------------------------------------------------------------------
# Key pool
# ---------------------------------------------------------------------------
@dataclass
class _KeySlot:
    label: str
    api_key: str
    client: OpenAI | None = None
    cooldown_until: float = 0.0
    failures: int = 0

    def client_for(self, base_url: str, timeout: float) -> OpenAI:
        if self.client is None:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=base_url,
                timeout=timeout,
                max_retries=0,  # rotation is handled here, not by the SDK
            )
        return self.client

    @property
    def available(self) -> bool:
        return time.monotonic() >= self.cooldown_until


class _KeyPool:
    """Thread-safe, cooldown-aware rotation across API keys."""

    def __init__(self, keys: list[tuple[str, str]]) -> None:
        self._slots = [_KeySlot(label=label, api_key=key) for label, key in keys]
        self._lock = threading.Lock()
        self._index = 0

    def __bool__(self) -> bool:
        return bool(self._slots)

    def labels(self) -> list[str]:
        return [s.label for s in self._slots]

    def acquire(self) -> _KeySlot:
        """Return the next ready slot, waiting if every key is cooling down."""
        while True:
            with self._lock:
                ready = [s for s in self._slots if s.available]
                if ready:
                    slot = ready[self._index % len(ready)]
                    self._index = (self._index + 1) % max(len(self._slots), 1)
                    return slot
                wait = min(s.cooldown_until for s in self._slots) - time.monotonic()

            if wait > 0:
                logger.info("all Groq keys cooling down — sleeping %.1fs", wait)
                time.sleep(min(wait, 60.0))

    def penalise(self, slot: _KeySlot, seconds: float) -> None:
        with self._lock:
            slot.cooldown_until = max(
                slot.cooldown_until, time.monotonic() + seconds
            )
            slot.failures += 1
        logger.warning(
            "key '%s' cooling down for %.1fs (failure #%d)",
            slot.label,
            seconds,
            slot.failures,
        )


_pool: _KeyPool | None = None
_pool_lock = threading.Lock()


def _get_pool() -> _KeyPool:
    global _pool
    with _pool_lock:
        if _pool is None:
            settings = get_settings()
            keys: list[tuple[str, str]] = []
            if settings.groq_api_key:
                keys.append(("primary", settings.groq_api_key))
            if settings.groq_api_key_secondary:
                keys.append(("secondary", settings.groq_api_key_secondary))
            if not keys:
                raise LLMUnavailable("No GROQ_API_KEY configured")
            _pool = _KeyPool(keys)
            logger.info(
                "Groq key pool initialised with: %s", ", ".join(_pool.labels())
            )
        return _pool


def is_available() -> bool:
    return get_settings().llm_enabled


# ---------------------------------------------------------------------------
# Retry-delay parsing
# ---------------------------------------------------------------------------
def _parse_retry_after(exc: openai.RateLimitError) -> float:
    """Seconds to wait, from the header or the Groq error body."""
    response = getattr(exc, "response", None)
    if response is not None:
        header = response.headers.get("retry-after") if response.headers else None
        if header:
            try:
                return float(header)
            except ValueError:
                pass

    # Groq's tokens-per-day 429 omits the header but embeds the delay in the body.
    match = _RETRY_AFTER_BODY_RE.search(str(exc))
    if match:
        minutes = float(match.group(1) or 0)
        seconds = float(match.group(2))
        return minutes * 60 + seconds

    return 30.0  # conservative default


def _log_headers(response: Any) -> None:
    if response is None or not getattr(response, "headers", None):
        return
    headers = response.headers
    logger.debug(
        "groq rate-limit: remaining_tokens=%s remaining_requests=%s retry_after=%s",
        headers.get("x-ratelimit-remaining-tokens"),
        headers.get("x-ratelimit-remaining-requests"),
        headers.get("retry-after"),
    )


# ---------------------------------------------------------------------------
# Core call with rotation
# ---------------------------------------------------------------------------
def _create_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, str] | None = None,
    max_attempts: int = 6,
) -> str:
    """Issue a chat completion, rotating keys on 429."""
    settings = get_settings()
    pool = _get_pool()

    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        slot = pool.acquire()
        client = slot.client_for(settings.groq_base_url, timeout=180.0)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = client.chat.completions.create(**kwargs)
            _log_headers(getattr(response, "response", None))
            return response.choices[0].message.content or "{}"
        except openai.RateLimitError as exc:
            last_exc = exc
            delay = _parse_retry_after(exc)
            # Cap the penalty so a daily-limit 429 doesn't stall the demo.
            pool.penalise(slot, min(delay, 90.0))
            logger.info(
                "429 from key '%s' (attempt %d/%d) — rotating (server asked for %.0fs)",
                slot.label,
                attempt,
                max_attempts,
                delay,
            )
            continue
        except openai.APIStatusError as exc:
            if exc.status_code >= 500:
                last_exc = exc
                logger.warning("upstream %s — retrying", exc.status_code)
                time.sleep(min(2 ** attempt, 20))
                continue
            raise
        except openai.APIConnectionError as exc:
            last_exc = exc
            logger.warning("connection error — retrying")
            time.sleep(min(2 ** attempt, 20))
            continue

    raise last_exc or RuntimeError("LLM call failed after all retries")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def _strip_fences(text: str) -> str:
    text = text.strip()
    text = _FENCE_RE.sub("", text).strip()
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
    return _create_completion(
        model=model or settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=settings.llm_temperature if temperature is None else temperature,
        max_tokens=max_tokens or settings.llm_max_tokens,
    ).strip()


def chat_json(
    system: str,
    user: str,
    schema: Type[T],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> T:
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
        return _create_completion(
            model=model or settings.llm_model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=settings.llm_temperature if temperature is None else temperature,
            max_tokens=max_tokens or settings.llm_max_tokens,
            response_format={"type": "json_object"},
        )

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
    except Exception:
        return default