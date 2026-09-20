"""Localisation agent — transcreation, not literal translation."""
from __future__ import annotations

import logging

from app.agents.prompts import brand_block, platform_block
from app.enums import LANGUAGE_NAMES, Language
from app.llm import chat_json, is_available
from app.schemas import ContentBatch

logger = logging.getLogger(__name__)

LOCALIZATION_SYSTEM = (
    "You are a transcreation specialist for Southeast Asian and Greater China "
    "markets. You do NOT translate literally: you rewrite so the copy lands "
    "naturally with local business audiences, preserving brand voice, compliance "
    "qualifications and disclaimers. Regulatory disclaimers must remain intact and "
    "accurate in the target language."
)


def localize_drafts(
    brand: str, drafts: list[dict], target_languages: list[str]
) -> list[dict]:
    """Return additional localised copies (originals are kept)."""
    if not target_languages or not is_available():
        return []

    outputs: list[dict] = []
    for lang in target_languages:
        lang_name = LANGUAGE_NAMES.get(lang, lang)
        batch_payload = [
            {
                "platform": d["platform"],
                "format": d["format"],
                "variant_label": d.get("variant_label"),
                "title": d["title"],
                "hook": d.get("hook", ""),
                "body": d["body"],
                "cta": d.get("cta", ""),
                "hashtags": d.get("hashtags", []),
            }
            for d in drafts
        ]
        prompt = (
            f"{brand_block(brand)}\n"
            f"TARGET LANGUAGE: {lang_name} ({lang})\n\n"
            "Transcreate each of the following assets into the target language. "
            "Keep the same platform, format and variant_label for each. "
            "Adapt idioms, examples and currency references to the local market. "
            "Keep compliance disclaimers present and accurate.\n\n"
            f"ASSETS (JSON):\n{batch_payload}\n\n"
            "Return all localised assets in the `assets` array as JSON."
        )
        try:
            batch: ContentBatch = chat_json(
                LOCALIZATION_SYSTEM, prompt, ContentBatch, temperature=0.5
            )
        except Exception as exc:
            logger.warning("localisation failed for %s: %s", lang, exc)
            continue

        for i, asset in enumerate(batch.assets):
            out = asset.model_dump(mode="json")
            out["language"] = lang
            # Preserve structural fields the model may have dropped.
            if i < len(drafts):
                out["platform"] = drafts[i]["platform"]
                out["format"] = drafts[i]["format"]
                out["variant_label"] = drafts[i].get("variant_label")
                out["visual_prompt"] = drafts[i].get("visual_prompt", "")
                out["video_script"] = drafts[i].get("video_script")
            outputs.append(out)

    return outputs


def localization_node(state: dict) -> dict:
    """LangGraph node: add localised variants for non-primary languages."""
    drafts = state.get("drafts", [])
    languages = state.get("languages") or ["en"]
    primary = languages[0]
    targets = [l for l in languages if l != primary]

    if not targets:
        return {"drafts": drafts}

    extra = localize_drafts(state["brand"], drafts, targets)
    if not extra:
        # Graceful degradation: mark originals so the pipeline still completes.
        return {"drafts": drafts}

    return {"drafts": drafts + extra}