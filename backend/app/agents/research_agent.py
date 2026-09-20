"""Competitor intelligence + trend research."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.agents.prompts import brand_block
from app.llm import chat_json, is_available
from app.models import CompetitorSnapshot, ResearchDigest
from app.schemas import ResearchFindings
from app.services.scraper import fetch_text
from app.services.search import web_search

logger = logging.getLogger(__name__)

COMPETITOR_SEEDS: dict[str, list[str]] = {
    "jade": [
        "jewellers block insurance Singapore",
        "pawnbroker insurance Malaysia",
        "precious metals dealer insurance Hong Kong",
    ],
    "jaguar_transit": [
        "goods in transit insurance Singapore",
        "high value cargo insurance Southeast Asia",
        "courier liability insurance Malaysia",
    ],
    "doctorshield": [
        "medical indemnity insurance Singapore",
        "professional indemnity doctors Malaysia",
        "clinic malpractice cover Hong Kong",
    ],
    "ja_assure": [
        "insurtech Singapore specialist insurance",
        "niche commercial insurance Southeast Asia",
    ],
}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def gather_web_context(brand: str, topic: str | None = None, extra_queries: list[str] | None = None) -> list[dict[str, Any]]:
    """Search the public web for competitor / market context."""
    queries = list(extra_queries or [])
    if topic:
        queries.insert(0, f"{brand} {topic}")
    queries.extend(COMPETITOR_SEEDS.get(brand, [])[:2])

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for q in queries[:4]:
        for hit in web_search(q, max_results=5):
            url = hit.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            results.append(hit)
    return results


def snapshot_competitors(
    db: Session, brand: str, competitors: list[str], urls: list[str]
) -> list[dict[str, Any]]:
    """Fetch competitor pages, diff against last snapshot, persist changes."""
    targets: list[tuple[str, str]] = []
    for url in urls:
        targets.append((url, url))
    for name in competitors:
        hits = web_search(f"{name} insurance", max_results=2)
        for hit in hits:
            if hit.get("url"):
                targets.append((name, hit["url"]))
                break

    changes: list[dict[str, Any]] = []
    for name, url in targets[:8]:
        try:
            text = fetch_text(url)
        except Exception as exc:  # pragma: no cover - network
            logger.warning("snapshot fetch failed for %s: %s", url, exc)
            continue

        digest = _hash(text)
        previous = (
            db.query(CompetitorSnapshot)
            .filter(CompetitorSnapshot.url == url)
            .order_by(desc(CompetitorSnapshot.captured_at))
            .first()
        )
        changed = bool(previous and previous.content_hash != digest)

        snapshot = CompetitorSnapshot(
            brand=brand,
            competitor=name,
            url=url,
            content_hash=digest,
            changed=changed,
            snapshot={
                "excerpt": text[:1500],
                "length": len(text),
                "captured_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(snapshot)
        if changed:
            changes.append(
                {
                    "competitor": name,
                    "url": url,
                    "previous_length": (previous.snapshot or {}).get("length") if previous else None,
                    "current_length": len(text),
                }
            )
    db.commit()
    return changes


def build_digest(
    db: Session,
    brand: str,
    topic: str | None,
    web_context: list[dict[str, Any]],
    changes: list[dict[str, Any]],
) -> ResearchDigest:
    """Produce a human-readable digest with recommended actions."""
    sources = [
        {"title": c.get("title"), "url": c.get("url"), "snippet": (c.get("content") or "")[:400]}
        for c in web_context[:10]
    ]

    if is_available():
        user_prompt = (
            f"{brand_block(brand)}\n"
            f"TOPIC FOCUS: {topic or 'general market movement'}\n\n"
            "WEB RESULTS (public sources):\n"
            + "\n".join(f"- {s['title']} :: {s['snippet']}" for s in sources)
            + "\n\nDETECTED COMPETITOR PAGE CHANGES:\n"
            + ("\n".join(f"- {c}" for c in changes) if changes else "- none detected")
            + "\n\nProduce a competitor intelligence digest as JSON."
        )
        try:
            findings: ResearchFindings = chat_json(
                "You are a competitive intelligence analyst for an InsurTech group. "
                "Be factual, cite only what the sources support, and never invent numbers.",
                user_prompt,
                ResearchFindings,
                temperature=0.3,
            )
            summary, change_list, recs = (
                findings.summary,
                findings.changes,
                findings.recommendations,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("digest LLM failed: %s", exc)
            summary, change_list, recs = _fallback_digest(brand, sources, changes)
    else:
        summary, change_list, recs = _fallback_digest(brand, sources, changes)

    digest = ResearchDigest(
        brand=brand,
        topic=topic,
        summary=summary,
        changes=change_list,
        recommendations=recs,
        sources=sources,
    )
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest


def _fallback_digest(brand, sources, changes):
    summary = (
        f"Collected {len(sources)} public sources relevant to {brand}. "
        f"{len(changes)} competitor page change(s) detected since the last sweep."
    )
    change_list = [f"{c['competitor']} page content changed ({c['url']})" for c in changes] or [
        "No competitor page changes detected in this sweep."
    ]
    recs = [
        "Refresh the highest-performing evergreen post with current market context.",
        "Publish one educational asset addressing the most-searched question in this niche.",
    ]
    return summary, change_list, recs


def research_node(state: dict) -> dict:
    """LangGraph node: gather research context for the content agent."""
    from app.db import SessionLocal

    brand = state["brand"]
    topic = state.get("topic")
    errors = list(state.get("errors", []))

    with SessionLocal() as db:
        try:
            context = gather_web_context(brand, topic)
            changes = snapshot_competitors(db, brand, competitors=[], urls=[])
            digest = build_digest(db, brand, topic, context, changes)
            research = {
                "summary": digest.summary,
                "changes": digest.changes,
                "recommendations": digest.recommendations,
                "digest_id": digest.id,
                "sources": digest.sources,
            }
        except Exception as exc:
            logger.exception("research node failed")
            errors.append(f"research: {exc}")
            research = {"summary": "", "changes": [], "recommendations": [], "sources": []}

    return {"research": research, "errors": errors}