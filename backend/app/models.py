"""ORM models. `content_assets` is the contract between Project 1 and 2."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import (
    AssetFormat,
    AssetStatus,
    ComplianceStatus,
    LeadStatus,
    PostStatus,
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
class ContentAsset(Base, TimestampMixin):
    """A single publishable unit. Status drives the whole pipeline."""

    __tablename__ = "content_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str | None] = mapped_column(String(36), index=True)

    brand: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str] = mapped_column(String(24), index=True)
    language: Mapped[str] = mapped_column(String(8), default="en", index=True)
    format: Mapped[str] = mapped_column(String(24), default=AssetFormat.post.value)

    title: Mapped[str] = mapped_column(String(300), default="")
    hook: Mapped[str | None] = mapped_column(Text())
    body: Mapped[str] = mapped_column(Text(), default="")
    cta: Mapped[str | None] = mapped_column(Text())
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)

    media_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    visual_prompt: Mapped[str | None] = mapped_column(Text())
    video_script: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # A/B
    variant_label: Mapped[str | None] = mapped_column(String(8))
    parent_asset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("content_assets.id", ondelete="SET NULL")
    )

    # Workflow
    status: Mapped[str] = mapped_column(
        String(24), default=AssetStatus.pending_review.value, index=True
    )
    compliance_status: Mapped[str] = mapped_column(
        String(24), default=ComplianceStatus.unchecked.value
    )
    compliance_score: Mapped[float | None] = mapped_column(Float)
    compliance_report: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    source_topic: Mapped[str | None] = mapped_column(Text())
    run_id: Mapped[str | None] = mapped_column(String(36), index=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    post_results: Mapped[list["PostResult"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_assets_status_platform", "status", "platform"),
        Index("ix_assets_brand_status", "brand", "status"),
    )


class Feedback(Base):
    """Every human decision on an asset — the raw material of the learning loop."""

    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_assets.id", ondelete="CASCADE"), index=True
    )
    decision: Mapped[str] = mapped_column(String(16))  # approved | edited | rejected
    reason_tag: Mapped[str | None] = mapped_column(String(32), index=True)
    note: Mapped[str | None] = mapped_column(Text)
    editor: Mapped[str] = mapped_column(String(120), default="reviewer")

    original_body: Mapped[str | None] = mapped_column(Text)
    edited_body: Mapped[str | None] = mapped_column(Text)
    edit_ratio: Mapped[float | None] = mapped_column(Float)

    brand: Mapped[str | None] = mapped_column(String(32), index=True)
    platform: Mapped[str | None] = mapped_column(String(24), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    asset: Mapped[ContentAsset] = relationship(back_populates="feedback")


class Lesson(Base, TimestampMixin):
    """Distilled guidance fed back into the content agent (few-shot memory)."""

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str | None] = mapped_column(String(24), index=True)
    reason_tag: Mapped[str | None] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(Text)
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------
class CompetitorSnapshot(Base):
    __tablename__ = "competitor_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand: Mapped[str] = mapped_column(String(32), index=True)
    competitor: Mapped[str] = mapped_column(String(160), index=True)
    url: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    changed: Mapped[bool] = mapped_column(Boolean, default=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ResearchDigest(Base):
    __tablename__ = "research_digests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand: Mapped[str] = mapped_column(String(32), index=True)
    topic: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    changes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------
class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    company_name: Mapped[str] = mapped_column(String(240), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    country: Mapped[str | None] = mapped_column(String(64), index=True)
    city: Mapped[str | None] = mapped_column(String(120))
    website: Mapped[str | None] = mapped_column(Text)
    contact_name: Mapped[str | None] = mapped_column(String(160))
    contact_email: Mapped[str | None] = mapped_column(String(240))
    contact_role: Mapped[str | None] = mapped_column(String(160))
    source_url: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(64))

    brand_fit: Mapped[str | None] = mapped_column(String(32), index=True)
    fit_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    score_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(
        String(32), default=LeadStatus.new.value, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    outreach: Mapped[list["OutreachDraft"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )


class OutreachDraft(Base, TimestampMixin):
    __tablename__ = "outreach_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lead_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(24), default="email")
    language: Mapped[str] = mapped_column(String(8), default="en")
    subject: Mapped[str | None] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default="pending_review")
    compliance_status: Mapped[str] = mapped_column(String(24), default="unchecked")
    compliance_report: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    lead: Mapped[Lead] = relationship(back_populates="outreach")


# ---------------------------------------------------------------------------
# Publishing / analytics (Project 2)
# ---------------------------------------------------------------------------
class PostResult(Base, TimestampMixin):
    __tablename__ = "post_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_assets.id", ondelete="CASCADE"), index=True
    )
    platform: Mapped[str] = mapped_column(String(24), index=True)
    publisher: Mapped[str] = mapped_column(String(32), default="dry_run")
    external_post_id: Mapped[str | None] = mapped_column(String(240), index=True)
    permalink: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(24), default=PostStatus.pending.value, index=True
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)

    analytics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    analytics_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    asset: Mapped[ContentAsset] = relationship(back_populates="post_results")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(48), index=True)
    status: Mapped[str] = mapped_column(String(24), default="running", index=True)
    brand: Mapped[str | None] = mapped_column(String(32))
    input: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))