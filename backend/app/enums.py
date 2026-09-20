"""Domain enums shared by models, schemas and agents."""
from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover
        return self.value


class Brand(StrEnum):
    ja_assure = "ja_assure"
    jade = "jade"
    jaguar_transit = "jaguar_transit"
    doctorshield = "doctorshield"


class Platform(StrEnum):
    linkedin = "linkedin"
    instagram = "instagram"
    x = "x"
    tiktok = "tiktok"
    blog = "blog"


class Language(StrEnum):
    en = "en"   # English
    ms = "ms"   # Bahasa Malaysia
    id = "id"   # Bahasa Indonesia
    th = "th"   # Thai
    zh = "zh"   # Chinese


class AssetFormat(StrEnum):
    post = "post"
    caption = "caption"
    carousel = "carousel"
    blog = "blog"
    thread = "thread"
    reel = "reel"


class AssetStatus(StrEnum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


class ComplianceStatus(StrEnum):
    pass_ = "pass"
    needs_revision = "needs_revision"
    fail = "fail"
    unchecked = "unchecked"


class ReasonTag(StrEnum):
    too_salesy = "too_salesy"
    inaccurate_claim = "inaccurate_claim"
    off_brand_tone = "off_brand_tone"
    wrong_cta = "wrong_cta"
    compliance_risk = "compliance_risk"
    too_long = "too_long"
    poor_visual = "poor_visual"
    not_localised = "not_localised"
    weak_hook = "weak_hook"
    other = "other"


class LeadCategory(StrEnum):
    jeweller = "jeweller"
    clinic = "clinic"
    doctor = "doctor"
    sme = "sme"
    courier = "courier"
    logistics = "logistics"
    other = "other"


class LeadStatus(StrEnum):
    new = "new"
    scored = "scored"
    outreach_drafted = "outreach_drafted"
    outreach_approved = "outreach_approved"
    outreach_sent = "outreach_sent"
    rejected = "rejected"


class PostStatus(StrEnum):
    pending = "pending"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "ms": "Bahasa Malaysia",
    "id": "Bahasa Indonesia",
    "th": "Thai",
    "zh": "Chinese (Simplified)",
}