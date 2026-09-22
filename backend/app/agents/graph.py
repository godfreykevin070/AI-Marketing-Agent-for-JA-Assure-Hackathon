"""LangGraph wiring: one graph for content, one for leads."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents.compliance_agent import compliance_node, summarize_verdicts
from app.agents.content_agent import content_node, revise_node
from app.agents.lead_agent import (
    lead_discovery_node,
    lead_enrichment_node,
    lead_persist_node,
    lead_scoring_node,
)
from app.agents.localization_agent import localization_node
from app.agents.research_agent import research_node
from app.agents.state import ContentState, LeadState
from app.agents.video_agent import media_node
from app.config import get_settings
from app.enums import AssetStatus, ComplianceStatus
from app.models import AgentRun, ContentAsset
from app.schemas import GenerateRequest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Content graph
# ---------------------------------------------------------------------------
def _route_after_compliance(state: ContentState) -> str:
    settings = get_settings()
    attempts = int(state.get("attempts", 0))
    compliance = state.get("compliance") or {}
    has_failures = any(v.get("status") != "pass" for v in compliance.values())

    if has_failures and attempts < settings.max_compliance_retries:
        return "revise"
    return "persist"


def persist_node(state: ContentState) -> dict:
    """Write all drafts into the shared approved-content queue as pending review."""
    from app.db import SessionLocal

    drafts = state.get("drafts", [])
    compliance = state.get("compliance") or {}
    run_id = state.get("run_id") or str(uuid.uuid4())

    asset_ids: list[str] = []
    with SessionLocal() as db:
        for i, draft in enumerate(drafts):
            verdicts_for_asset = {str(i): compliance.get(str(i), {})} if compliance.get(str(i)) else {}
            status, score = summarize_verdicts(verdicts_for_asset)

            asset = ContentAsset(
                campaign_id=state.get("campaign_id") or run_id,
                brand=state["brand"],
                platform=draft["platform"],
                language=draft.get("language", "en"),
                format=draft.get("format", "post"),
                title=draft.get("title", "")[:300],
                hook=draft.get("hook"),
                body=draft.get("body", ""),
                cta=draft.get("cta"),
                hashtags=draft.get("hashtags") or [],
                media_urls=draft.get("media_urls") or [],
                visual_prompt=draft.get("visual_prompt"),
                video_script=draft.get("video_script"),
                variant_label=draft.get("variant_label"),
                status=AssetStatus.pending_review.value,
                compliance_status=status,
                compliance_score=score,
                compliance_report=compliance.get(str(i)),
                source_topic=state.get("topic"),
                run_id=run_id,
            )
            db.add(asset)
            asset_ids.append(asset.id)
        db.commit()

    return {"asset_ids": asset_ids, "run_id": run_id}


def build_content_graph():
    graph = StateGraph(ContentState)
    graph.add_node("do_research", research_node)
    graph.add_node("draft_content", content_node)
    graph.add_node("localize_content", localization_node)
    graph.add_node("resolve_media", media_node)      # ← renamed
    graph.add_node("check_compliance", compliance_node)
    graph.add_node("revise_content", revise_node)
    graph.add_node("persist_assets", persist_node)

    graph.set_entry_point("do_research")
    graph.add_edge("do_research", "draft_content")
    graph.add_edge("draft_content", "localize_content")
    graph.add_edge("localize_content", "resolve_media")     # ← renamed
    graph.add_edge("resolve_media", "check_compliance")     # ← renamed
    graph.add_conditional_edges(
        "check_compliance",
        _route_after_compliance,
        {"revise": "revise_content", "persist": "persist_assets"},
    )
    graph.add_edge("revise_content", "check_compliance")
    graph.add_edge("persist_assets", END)
    return graph.compile()


_CONTENT_GRAPH = None


def get_content_graph():
    global _CONTENT_GRAPH
    if _CONTENT_GRAPH is None:
        _CONTENT_GRAPH = build_content_graph()
    return _CONTENT_GRAPH


def run_content_pipeline(db: Session, request: GenerateRequest) -> dict[str, Any]:
    """Entry point used by the API. Returns run metadata + created asset ids."""
    run_id = str(uuid.uuid4())
    run = AgentRun(
        id=run_id,
        kind="content_pipeline",
        status="running",
        brand=request.brand.value,
        input=request.model_dump(mode="json"),
    )
    db.add(run)
    db.commit()

    initial: ContentState = {
        "run_id": run_id,
        "campaign_id": run_id,
        "brand": request.brand.value,
        "topic": request.topic,
        "brief": request.brief or "",
        "platforms": [p.value for p in request.platforms],
        "languages": [l.value for l in request.languages],
        "variants": request.variants,
        "media_mode": request.media_mode,      # ← was include_video
        "auto_compliance": request.auto_compliance,
        "attempts": 0,
        "errors": [],
    }

    try:
        final = get_content_graph().invoke(initial, {"recursion_limit": 40})
        run.status = "completed"
        run.output = {
            "asset_ids": final.get("asset_ids", []),
            "research": final.get("research", {}),
            "errors": final.get("errors", []),
        }
    except Exception as exc:
        logger.exception("content pipeline failed")
        run.status = "failed"
        run.error = str(exc)
        final = {"asset_ids": [], "errors": [str(exc)], "research": {}}

    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    return final


# ---------------------------------------------------------------------------
# Lead graph
# ---------------------------------------------------------------------------
def build_lead_graph():
    graph = StateGraph(LeadState)
    graph.add_node("discover", lead_discovery_node)
    graph.add_node("enrich", lead_enrichment_node)
    graph.add_node("score", lead_scoring_node)
    graph.add_node("persist", lead_persist_node)

    graph.set_entry_point("discover")
    graph.add_edge("discover", "enrich")
    graph.add_edge("enrich", "score")
    graph.add_edge("score", "persist")
    graph.add_edge("persist", END)
    return graph.compile()


_LEAD_GRAPH = None


def get_lead_graph():
    global _LEAD_GRAPH
    if _LEAD_GRAPH is None:
        _LEAD_GRAPH = build_lead_graph()
    return _LEAD_GRAPH


def run_lead_pipeline(db: Session, brand: str, category: str, country: str, city: str | None, limit: int) -> dict:
    run_id = str(uuid.uuid4())
    run = AgentRun(
        id=run_id,
        kind="lead_pipeline",
        status="running",
        brand=brand,
        input={"category": category, "country": country, "city": city, "limit": limit},
    )
    db.add(run)
    db.commit()

    initial: LeadState = {
        "run_id": run_id,
        "brand": brand,
        "category": category,
        "country": country,
        "city": city,
        "limit": limit,
        "errors": [],
    }

    try:
        final = get_lead_graph().invoke(initial, {"recursion_limit": 25})
        run.status = "completed"
        run.output = {"lead_ids": final.get("lead_ids", [])}
    except Exception as exc:
        logger.exception("lead pipeline failed")
        run.status = "failed"
        run.error = str(exc)
        final = {"lead_ids": [], "errors": [str(exc)]}

    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    return final