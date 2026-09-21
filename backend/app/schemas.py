"""Pydantic request/response schemas + structured LLM output contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.enums import (
    AssetFormat,
    AssetStatus,
    Brand,
    Language,
    LeadCategory,
    Platform,
    ReasonTag,
    UserRole
)


# ---------------------------------------------------------------------------
# LLM structured outputs
# ---------------------------------------------------------------------------
class VideoScene(BaseModel):
    index: int
    duration_seconds: float = Field(ge=1, le=20)
    on_screen_text: str
    voiceover: str
    visual_direction: str


class VideoScript(BaseModel):
    title: str
    hook: str
    total_seconds: float = 30
    aspect_ratio: str = "9:16"
    scenes: list[VideoScene]
    caption: str
    hashtags: list[str] = Field(default_factory=list)


class DraftAsset(BaseModel):
    """One generated asset returned by the content agent."""

    platform: Platform
    format: AssetFormat = AssetFormat.post
    language: Language = Language.en
    title: str
    hook: str = ""
    body: str
    cta: str = ""
    hashtags: list[str] = Field(default_factory=list)
    visual_prompt: str = ""
    variant_label: str = "A"
    video_script: VideoScript | None = None


class ContentBatch(BaseModel):
    assets: list[DraftAsset]


class LocalizedBatch(BaseModel):
    assets: list[DraftAsset]


class ComplianceVerdict(BaseModel):
    asset_index: int
    status: str  # pass | needs_revision | fail
    score: float = Field(ge=0, le=1)
    failed_rules: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    offending_spans: list[str] = Field(default_factory=list)
    suggested_fix: str = ""


class ComplianceReport(BaseModel):
    verdicts: list[ComplianceVerdict]


class ResearchFindings(BaseModel):
    summary: str
    changes: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    angles: list[str] = Field(default_factory=list)


class ScoredLead(BaseModel):
    company_name: str
    category: LeadCategory = LeadCategory.other
    country: str | None = None
    city: str | None = None
    website: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_role: str | None = None
    source_url: str | None = None
    fit_score: float = Field(ge=0, le=100, default=50)
    score_reasons: list[str] = Field(default_factory=list)


class LeadBatch(BaseModel):
    leads: list[ScoredLead]


class OutreachEmail(BaseModel):
    subject: str
    body: str
    cta: str = ""


# ---------------------------------------------------------------------------
# API request models
# ---------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    brand: Brand
    topic: str = Field(min_length=3)
    brief: str | None = None
    platforms: list[Platform] = Field(
        default_factory=lambda: [Platform.linkedin, Platform.instagram]
    )
    languages: list[Language] = Field(default_factory=lambda: [Language.en])
    variants: int = Field(default=2, ge=1, le=3)
    include_video: bool = True
    auto_compliance: bool = True


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|edit|reject)$")
    editor: str = "reviewer"
    reason_tag: ReasonTag | None = None
    note: str | None = None
    edited_title: str | None = None
    edited_body: str | None = None
    edited_cta: str | None = None


class LeadDiscoveryRequest(BaseModel):
    brand: Brand
    category: LeadCategory
    country: str = "Singapore"
    city: str | None = None
    limit: int = Field(default=8, ge=1, le=25)


class OutreachRequest(BaseModel):
    lead_id: str
    language: Language = Language.en
    channel: str = "email"


class ResearchRequest(BaseModel):
    brand: Brand
    competitors: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    topic: str | None = None


# ---------------------------------------------------------------------------
# API response models
# ---------------------------------------------------------------------------
class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str | None
    brand: str
    platform: str
    language: str
    format: str
    title: str
    hook: str | None
    body: str
    cta: str | None
    hashtags: list[str]
    media_urls: list[str]
    visual_prompt: str | None
    video_script: dict[str, Any] | None
    variant_label: str | None
    status: str
    compliance_status: str
    compliance_score: float | None
    compliance_report: dict[str, Any] | None
    source_topic: str | None
    created_at: datetime
    updated_at: datetime


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    decision: str
    reason_tag: str | None
    note: str | None
    editor: str
    edit_ratio: float | None
    created_at: datetime


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    brand: str
    platform: str | None
    reason_tag: str | None
    text: str
    occurrences: int
    active: bool


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_name: str
    category: str
    country: str | None
    city: str | None
    website: str | None
    contact_name: str | None
    contact_email: str | None
    contact_role: str | None
    source_url: str | None
    brand_fit: str | None
    fit_score: float
    score_reasons: list[str]
    status: str
    created_at: datetime


class OutreachOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lead_id: str
    channel: str
    language: str
    subject: str | None
    body: str
    status: str
    compliance_status: str
    created_at: datetime


class DigestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    brand: str
    topic: str | None
    summary: str
    changes: list[Any]
    recommendations: list[Any]
    sources: list[Any]
    created_at: datetime


class PostResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    platform: str
    publisher: str
    external_post_id: str | None
    permalink: str | None
    status: str
    scheduled_for: datetime | None
    posted_at: datetime | None
    error: str | None
    analytics: dict[str, Any]
    created_at: datetime


class GenerateResponse(BaseModel):
    run_id: str
    assets: list[AssetOut]
    research: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class CreateUserRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str = ""
    role: UserRole = UserRole.viewer


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)