"""Shared LangGraph state definitions."""
from __future__ import annotations

from typing import Any, TypedDict


class ContentState(TypedDict, total=False):
    run_id: str
    campaign_id: str
    brand: str
    topic: str
    brief: str
    platforms: list[str]
    languages: list[str]
    variants: int
    media_mode: str          # ← was include_video: bool
    auto_compliance: bool

    research: dict[str, Any]
    lessons: list[dict[str, Any]]
    drafts: list[dict[str, Any]]
    compliance: dict[str, dict[str, Any]]
    attempts: int
    errors: list[str]
    asset_ids: list[str]


class LeadState(TypedDict, total=False):
    run_id: str
    brand: str
    category: str
    country: str
    city: str | None
    limit: int
    raw_candidates: list[dict[str, Any]]
    enriched: list[dict[str, Any]]
    scored: list[dict[str, Any]]
    lead_ids: list[str]
    errors: list[str]