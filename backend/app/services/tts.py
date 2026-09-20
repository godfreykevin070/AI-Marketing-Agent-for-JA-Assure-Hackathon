"""Text-to-speech. gTTS by default, pluggable for ElevenLabs/other."""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)


def media_root() -> Path:
    root = Path(get_settings().media_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def synthesize(text: str, language: str = "en") -> str | None:
    """Return a path to a generated audio file, or None if TTS is unavailable."""
    if not text.strip():
        return None

    out_dir = media_root() / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"vo_{uuid.uuid4().hex[:12]}.mp3"

    try:
        from gtts import gTTS

        tts = gTTS(text=text[:4800], lang=language if language != "zh" else "zh-CN")
        tts.save(str(out_path))
        return str(out_path)
    except Exception as exc:  # pragma: no cover - network dependency
        logger.warning("TTS unavailable (%s); rendering silent video", exc)
        return None