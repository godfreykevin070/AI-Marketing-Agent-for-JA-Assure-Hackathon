"""Content generation agent — brand voice x platform x A/B variants."""
from __future__ import annotations

import logging
from typing import Any
import time

from app.agents.prompts import (
    brand_block,
    lessons_block,
    platform_block,
)
from app.enums import AssetFormat, Language, Platform
from app.llm import chat_json, is_available
from app.schemas import ContentBatch, DraftAsset

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are the lead content strategist for a specialist InsurTech group in "
    "Southeast Asia. You write copy that is accurate, brand-appropriate and "
    "compliant with insurance advertising standards. You never make guarantees, "
    "never use unsubstantiated superlatives, and always qualify cover statements. "
    "You write like a domain expert, not a marketer."
)


def _fallback_drafts(
    brand: str,
    platform: str,
    topic: str,
    brief: str | None,
    variants: int,
    language: str,
) -> list[DraftAsset]:
    """Deterministic fallback so the pipeline runs without LLM credentials."""
    fmt = AssetFormat(Platform(platform) and {
        "instagram": AssetFormat.caption,
        "tiktok": AssetFormat.reel,
        "blog": AssetFormat.blog,
        "x": AssetFormat.post,
    }.get(platform, AssetFormat.post))
    drafts: list[DraftAsset] = []
    for i in range(variants):
        label = chr(ord("A") + i)
        angle = "risk exposure" if i == 0 else "operational resilience"
        body = (
            f"{topic} is reshaping how specialists think about {angle}.\n\n"
            f"At {brand.replace('_', ' ').title()}, we work with operators who need cover "
            "that matches how they actually run their business — not a generic policy.\n\n"
            "Three things worth reviewing this quarter:\n"
            "1. Whether your current limits still reflect today's values.\n"
            "2. How transit and off-site exposure is treated.\n"
            "3. What documentation you'd need at claim time.\n\n"
            "Cover is subject to policy terms and underwriting. "
            "Speak to your broker or our team to review your position."
        )
        if brief:
            body = f"{brief}\n\n{body}"
        drafts.append(
            DraftAsset(
                platform=Platform(platform),
                format=fmt,
                language=Language(language),
                title=f"{topic} — {angle}",
                hook=f"What {topic} means for your {angle}.",
                body=body,
                cta="Review your cover with a specialist.",
                hashtags=["#Insurance", "#InsurTech", "#RiskManagement"],
                visual_prompt=f"Editorial image representing {topic} in a professional setting.",
                variant_label=label,
            )
        )
    return drafts


def generate_for_platform(
    brand: str,
    platform: str,
    topic: str,
    brief: str | None,
    variants: int,
    language: str,
    research: dict[str, Any] | None,
    lessons: list[dict[str, Any]],
) -> list[DraftAsset]:
    """Generate A/B variants for a single platform."""
    if not is_available():
        return _fallback_drafts(brand, platform, topic, brief, variants, language)

    research_text = ""
    if research:
        research_text = (
            f"\nMARKET CONTEXT (use only if relevant, do not quote verbatim):\n"
            f"{research.get('summary', '')}\n"
            + "\n".join(f"- {c}" for c in research.get("changes", [])[:5])
        )

    user_prompt = (
        f"{brand_block(brand)}\n"
        f"{platform_block(platform)}\n"
        f"{lessons_block(lessons)}"
        f"{research_text}\n\n"
        f"TOPIC / IDEA: {topic}\n"
        f"EXTRA BRIEF: {brief or 'none'}\n"
        f"OUTPUT LANGUAGE: {language}\n\n"
        f"Produce exactly {variants} distinct A/B variants for this platform. "
        "Variants must differ meaningfully in angle or hook — not just wording. "
        "Each variant needs: a title, a scroll-stopping hook, the full body copy "
        "written for this platform's structure and character limit, a clear CTA, "
        "hashtags, and a visual prompt describing the accompanying image or carousel.\n"
        "If the platform is tiktok or the format is reel, also include a "
        "`video_script` with 3-6 scenes, each with on-screen text, voiceover and "
        "visual direction, plus a total duration under 45 seconds.\n"
        "Every asset must end with a compliance-safe disclaimer or a pointer to "
        "policy terms. Respond as JSON."
    )

    try:
        batch: ContentBatch = chat_json(
            SYSTEM_PROMPT, user_prompt, ContentBatch, temperature=0.75
        )
        drafts = batch.assets or []
    except Exception as exc:
        logger.warning("content LLM failed for %s/%s: %s", brand, platform, exc)
        return _fallback_drafts(brand, platform, topic, brief, variants, language)

    # Force metadata consistency — the model sometimes drifts.
    for d in drafts:
        d.platform = Platform(platform)
        d.language = Language(language)

    if not drafts:
        return _fallback_drafts(brand, platform, topic, brief, variants, language)
    return drafts


def content_node(state: dict) -> dict:
    """LangGraph node: generate drafts for every requested platform."""
    from app.agents.feedback_agent import get_relevant_lessons
    from app.db import SessionLocal

    brand = state["brand"]
    topic = state["topic"]
    brief = state.get("brief")
    variants = int(state.get("variants", 2))
    platforms = state.get("platforms") or ["linkedin"]
    language = (state.get("languages") or ["en"])[0]
    research = state.get("research")
    errors = list(state.get("errors", []))

    drafts: list[dict] = []
    with SessionLocal() as db:
        for platform in platforms:
            lessons = get_relevant_lessons(db, brand, platform, limit=8)
            try:
                generated = generate_for_platform(
                    brand=brand,
                    platform=platform,
                    topic=topic,
                    brief=brief,
                    variants=variants,
                    language=language,
                    research=research,
                    lessons=lessons,
                )
            except Exception as exc:
                logger.exception("content generation failed for %s", platform)
                errors.append(f"content[{platform}]: {exc}")
                continue
            for d in generated:
                drafts.append(d.model_dump(mode="json"))
            time.sleep(8.0)

    return {"drafts": drafts, "errors": errors, "attempts": state.get("attempts", 0)}


def revise_node(state: dict) -> dict:
    """LangGraph node: repair drafts that failed compliance."""
    from app.llm import chat_json as _chat_json
    from app.schemas import ContentBatch as _ContentBatch

    drafts = state.get("drafts", [])
    compliance = state.get("compliance", {})
    attempts = int(state.get("attempts", 0)) + 1
    errors = list(state.get("errors", []))

    if not is_available():
        return {"attempts": attempts, "errors": errors}

    failed = {
        idx: verdict
        for idx, verdict in compliance.items()
        if verdict.get("status") != "pass"
    }
    if not failed:
        return {"attempts": attempts}

    revised = list(drafts)
    for key, verdict in failed.items():
        try:
            idx = int(key)
            draft = revised[idx]
        except (ValueError, IndexError):
            continue

        issues = verdict.get("reasons", []) + verdict.get("offending_spans", [])
        prompt = (
            f"{brand_block(state['brand'])}\n"
            f"{platform_block(draft['platform'])}\n\n"
            "The following asset FAILED our compliance gate. Rewrite it so that it "
            "passes, preserving the core idea but removing every problem.\n\n"
            f"ASSET:\nTitle: {draft['title']}\nBody:\n{draft['body']}\n"
            f"CTA: {draft.get('cta')}\n\n"
            f"COMPLIANCE FAILURES:\n" + "\n".join(f"- {i}" for i in issues) + "\n"
            f"SUGGESTED FIX: {verdict.get('suggested_fix', '')}\n\n"
            "Return exactly one asset in the `assets` array, same platform, format, "
            "language and variant label. Respond as JSON."
        )
        
        try:
            batch: _ContentBatch = _chat_json(
                SYSTEM_PROMPT, prompt, _ContentBatch, temperature=0.5
            )
            if batch.assets:
                fixed = batch.assets[0].model_dump(mode="json")
                fixed["platform"] = draft["platform"]
                fixed["format"] = draft["format"]
                fixed["language"] = draft["language"]
                fixed["variant_label"] = draft.get("variant_label")
                # Preserve media and structural fields — the LLM only
                # returns copy, so anything we attached earlier must be
                # carried across the revision.
                fixed["media_urls"] = draft.get("media_urls", [])
                fixed["video_script"] = draft.get("video_script")
                fixed["visual_prompt"] = draft.get("visual_prompt", "")
                revised[idx] = fixed
        except Exception as exc:
            logger.warning("revision failed for asset %s: %s", idx, exc)
            errors.append(f"revision[{idx}]: {exc}")

    return {"drafts": revised, "attempts": attempts, "errors": errors}