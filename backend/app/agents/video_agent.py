"""Video / Reels agent — script, voiceover, captions, assembled clip."""
from __future__ import annotations

import logging
from typing import Any

from app.agents.prompts import brand_block
from app.llm import chat_json, is_available
from app.schemas import VideoScript
from app.services.media import assemble_reel
from app.services.tts import synthesize

logger = logging.getLogger(__name__)

VIDEO_SYSTEM = (
    "You are a short-form video director for B2B insurance content. You write "
    "tight, watchable 20-45 second vertical scripts. The first 3 seconds must earn "
    "attention. No guarantees, no hype, no fear-mongering."
)


def _fallback_script(brand: str, topic: str, language: str = "en") -> dict[str, Any]:
    return {
        "title": f"{topic} — 30 second explainer",
        "hook": f"Three things about {topic} most operators miss.",
        "total_seconds": 30,
        "aspect_ratio": "9:16",
        "scenes": [
            {
                "index": 1,
                "duration_seconds": 4,
                "on_screen_text": topic,
                "voiceover": f"Here are three things about {topic} most operators miss.",
                "visual_direction": "Bold text card over a slow zoom of a professional workspace.",
            },
            {
                "index": 2,
                "duration_seconds": 8,
                "on_screen_text": "1. Limits drift",
                "voiceover": "First, your declared limits may no longer match today's values.",
                "visual_direction": "Simple animated counter rising.",
            },
            {
                "index": 3,
                "duration_seconds": 8,
                "on_screen_text": "2. Transit exposure",
                "voiceover": "Second, off-site and transit exposure is often the gap.",
                "visual_direction": "Map line animating between two points.",
            },
            {
                "index": 4,
                "duration_seconds": 6,
                "on_screen_text": "3. Claim documentation",
                "voiceover": "Third, documentation at claim time decides everything.",
                "visual_direction": "Checklist ticking off.",
            },
            {
                "index": 5,
                "duration_seconds": 4,
                "on_screen_text": "Review your cover",
                "voiceover": "Cover is subject to policy terms. Talk to a specialist.",
                "visual_direction": "Logo card with CTA.",
            },
        ],
        "caption": f"{topic} — what to review this quarter. Cover subject to policy terms.",
        "hashtags": ["#Insurance", "#RiskManagement", "#InsurTech"],
    }


def generate_script(brand: str, topic: str, brief: str | None, language: str) -> VideoScript:
    if not is_available():
        return VideoScript.model_validate(_fallback_script(brand, topic, language))

    prompt = (
        f"{brand_block(brand)}\n"
        f"LANGUAGE: {language}\n"
        f"TOPIC: {topic}\n"
        f"BRIEF: {brief or 'none'}\n\n"
        "Write a vertical short-form video script (9:16, 20-45 seconds). "
        "Include 4-6 scenes with precise durations, on-screen text (max 8 words), "
        "voiceover lines, and visual direction. "
        "End with a compliance-safe CTA. Respond as JSON."
    )
    try:
        return chat_json(VIDEO_SYSTEM, prompt, VideoScript, temperature=0.7)
    except Exception as exc:
        logger.warning("video script LLM failed: %s", exc)
        return VideoScript.model_validate(_fallback_script(brand, topic, language))


def video_node(state: dict) -> dict:
    """LangGraph node: attach video scripts and render Reels for reel-format drafts."""
    from app.config import get_settings

    settings = get_settings()
    drafts = state.get("drafts", [])
    if not state.get("include_video", True):
        return {"drafts": drafts}

    brand = state["brand"]
    topic = state["topic"]
    brief = state.get("brief")
    errors = list(state.get("errors", []))

    # One script shared across reel-format variants (they differ in copy, not video).
    reel_indices = [i for i, d in enumerate(drafts) if d.get("format") == "reel"]
    if not reel_indices:
        return {"drafts": drafts, "errors": errors}

    language = drafts[reel_indices[0]].get("language", "en")
    try:
        script = generate_script(brand, topic, brief, language)
    except Exception as exc:
        errors.append(f"video_script: {exc}")
        return {"drafts": drafts, "errors": errors}

    script_dict = script.model_dump(mode="json")

    rendered_urls: list[str] = []
    if settings.enable_video_render:
        try:
            audio_path = synthesize(script.hook + " " + " ".join(s.voiceover for s in script.scenes))
            rendered_urls = assemble_reel(
                scenes=[s.model_dump() for s in script.scenes],
                title=script.title,
                audio_path=audio_path,
            )
        except Exception as exc:
            logger.warning("reel render failed: %s", exc)
            errors.append(f"video_render: {exc}")

    for i in reel_indices:
        drafts[i]["video_script"] = script_dict
        if rendered_urls:
            drafts[i]["media_urls"] = rendered_urls
        if not drafts[i].get("hook"):
            drafts[i]["hook"] = script.hook

    return {"drafts": drafts, "errors": errors}