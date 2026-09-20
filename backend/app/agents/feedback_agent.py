"""Closed-loop learning: every human decision becomes reusable guidance."""
from __future__ import annotations

import difflib
import logging

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.enums import AssetStatus, ReasonTag
from app.llm import chat_text, is_available
from app.models import ContentAsset, Feedback, Lesson

logger = logging.getLogger(__name__)


def _similarity(a: str, b: str) -> float:
    return round(difflib.SequenceMatcher(None, a or "", b or "").ratio(), 4)


def get_relevant_lessons(
    db: Session, brand: str, platform: str | None = None, limit: int = 8
) -> list[dict]:
    """Fetch the most impactful past corrections for this brand/platform."""
    stmt = (
        select(Lesson)
        .where(Lesson.brand == brand, Lesson.active.is_(True))
        .order_by(desc(Lesson.occurrences), desc(Lesson.updated_at))
        .limit(limit * 2)
    )
    lessons = list(db.execute(stmt).scalars().all())

    # Prefer platform-specific lessons, then brand-wide ones.
    platform_specific = [l for l in lessons if l.platform == platform]
    brand_wide = [l for l in lessons if l.platform is None]
    ordered = platform_specific + brand_wide
    if not ordered:
        ordered = lessons

    return [
        {
            "text": l.text,
            "reason_tag": l.reason_tag,
            "platform": l.platform,
            "occurrences": l.occurrences,
        }
        for l in ordered[:limit]
    ]


def distill_lesson(
    db: Session,
    brand: str,
    platform: str,
    reason_tag: str | None,
    note: str | None,
    original: str,
    edited: str | None,
) -> Lesson | None:
    """Turn one human correction into (or merge into) a reusable lesson."""
    if is_available():
        prompt = (
            f"Brand: {brand}\nPlatform: {platform}\n"
            f"Reviewer reason tag: {reason_tag or 'unspecified'}\n"
            f"Reviewer note: {note or 'none'}\n\n"
            f"ORIGINAL COPY:\n{original[:1500]}\n\n"
            f"REVIEWER'S EDITED COPY:\n{(edited or '(rejected outright)')[:1500]}\n\n"
            "Write ONE short, generalisable instruction (max 25 words) that the "
            "content agent should follow in future to avoid this mistake. "
            "Write it as an imperative, e.g. 'Open with a specific risk scenario, "
            "not a product feature.' Reply with the instruction only, no quotes."
        )
        try:
            text = chat_text(
                "You extract concise, reusable writing rules from editorial feedback.",
                prompt,
                temperature=0.2,
                max_tokens=120,
            ).strip().strip('"')
        except Exception as exc:  # pragma: no cover
            logger.warning("lesson distillation failed: %s", exc)
            text = _fallback_lesson(reason_tag, note)
    else:
        text = _fallback_lesson(reason_tag, note)

    if not text:
        return None

    existing = db.execute(
        select(Lesson).where(
            Lesson.brand == brand,
            Lesson.platform == platform,
            Lesson.text == text,
        )
    ).scalar_one_or_none()

    if existing:
        existing.occurrences += 1
        existing.active = True
        db.commit()
        db.refresh(existing)
        return existing

    lesson = Lesson(
        brand=brand,
        platform=platform,
        reason_tag=reason_tag,
        text=text,
        occurrences=1,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def _fallback_lesson(reason_tag: str | None, note: str | None) -> str:
    mapping = {
        ReasonTag.too_salesy.value: "Keep the tone advisory; never pitch the product directly.",
        ReasonTag.inaccurate_claim.value: "Qualify every cover statement with policy terms.",
        ReasonTag.off_brand_tone.value: "Match the brand's understated, expert tone.",
        ReasonTag.wrong_cta.value: "Use a soft, consultative CTA instead of a hard sell.",
        ReasonTag.compliance_risk.value: "Remove all guarantees, absolutes and superlatives.",
        ReasonTag.too_long.value: "Cut the copy by roughly a third; lead with the insight.",
        ReasonTag.poor_visual.value: "Choose a more concrete, less generic visual concept.",
        ReasonTag.not_localised.value: "Adapt examples and references to the local market.",
        ReasonTag.weak_hook.value: "Open with a specific, concrete situation, not a generic claim.",
    }
    if reason_tag and reason_tag in mapping:
        return mapping[reason_tag]
    if note:
        return note.strip()[:200]
    return "Follow reviewer guidance more closely on the next revision."


def record_feedback(
    db: Session,
    asset: ContentAsset,
    decision: str,
    editor: str,
    reason_tag: str | None = None,
    note: str | None = None,
    edited_title: str | None = None,
    edited_body: str | None = None,
    edited_cta: str | None = None,
) -> Feedback:
    """Persist the decision, apply edits, and grow the lessons memory."""
    original_body = asset.body
    original_title = asset.title
    original_cta = asset.cta

    edit_ratio = None
    if decision == "edit" and edited_body is not None:
        edit_ratio = _similarity(original_body, edited_body)
        asset.body = edited_body
        if edited_title is not None:
            asset.title = edited_title
        if edited_cta is not None:
            asset.cta = edited_cta
        asset.extra = {**(asset.extra or {}), "was_edited": True}

    feedback = Feedback(
        asset_id=asset.id,
        decision=decision,
        reason_tag=reason_tag,
        note=note,
        editor=editor,
        original_body=original_body,
        edited_body=edited_body if decision == "edit" else None,
        edit_ratio=edit_ratio,
        brand=asset.brand,
        platform=asset.platform,
    )
    db.add(feedback)

    if decision == "approve":
        asset.status = AssetStatus.approved.value
    elif decision == "reject":
        asset.status = AssetStatus.rejected.value
    else:  # edit
        asset.status = AssetStatus.approved.value

    db.commit()
    db.refresh(asset)
    db.refresh(feedback)

    # Grow the lessons memory. Approvals with no note teach nothing new.
    if decision in ("reject", "edit") and (reason_tag or note or edited_body):
        try:
            distill_lesson(
                db,
                brand=asset.brand,
                platform=asset.platform,
                reason_tag=reason_tag,
                note=note,
                original=original_body,
                edited=edited_body or edited_title or edited_cta,
            )
        except Exception:  # pragma: no cover
            logger.exception("failed to distil lesson")

    return feedback


def feedback_stats(db: Session, brand: str | None = None) -> dict:
    """Metrics proving the loop is working."""
    from sqlalchemy import func

    stmt = select(Feedback)
    if brand:
        stmt = stmt.where(Feedback.brand == brand)
    rows = list(db.execute(stmt).scalars().all())

    total = len(rows)
    rejects = sum(1 for r in rows if r.decision == "reject")
    edits = sum(1 for r in rows if r.decision == "edit")
    approves = sum(1 for r in rows if r.decision == "approve")

    tag_counts: dict[str, int] = {}
    for r in rows:
        if r.reason_tag:
            tag_counts[r.reason_tag] = tag_counts.get(r.reason_tag, 0) + 1

    edit_ratios = [r.edit_ratio for r in rows if r.edit_ratio is not None]
    avg_edit = round(sum(edit_ratios) / len(edit_ratios), 4) if edit_ratios else None

    return {
        "total_reviews": total,
        "approved": approves,
        "edited": edits,
        "rejected": rejects,
        "rejection_rate": round(rejects / total, 4) if total else 0.0,
        "edit_rate": round(edits / total, 4) if total else 0.0,
        "avg_edit_similarity": avg_edit,
        "top_reason_tags": sorted(tag_counts.items(), key=lambda x: -x[1])[:8],
    }