"""Lead generation agent: discover → enrich → score → draft outreach."""
from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.agents.prompts import brand_block
from app.enums import LeadCategory, LeadStatus
from app.llm import chat_json, is_available
from app.models import Lead, OutreachDraft
from app.schemas import LeadBatch, OutreachEmail, ScoredLead
from app.services.scraper import extract_emails, fetch_text
from app.services.search import web_search

logger = logging.getLogger(__name__)

CATEGORY_QUERIES: dict[str, str] = {
    "jeweller": "jewellery retailer {city} {country} contact",
    "clinic": "medical clinic {city} {country} contact email",
    "doctor": "specialist doctor practice {city} {country} contact",
    "sme": "SME manufacturer {city} {country} contact",
    "courier": "courier company {city} {country} contact",
    "logistics": "freight forwarder {city} {country} contact",
}

CATEGORY_TO_BRAND: dict[str, str] = {
    "jeweller": "jade",
    "clinic": "doctorshield",
    "doctor": "doctorshield",
    "courier": "jaguar_transit",
    "logistics": "jaguar_transit",
    "sme": "ja_assure",
}

LEAD_SYSTEM = (
    "You are a B2B lead researcher for a specialist InsurTech group in Southeast "
    "Asia. You only work with publicly available business information. You never "
    "invent contact details: if an email is not present in the supplied sources, "
    "you leave it null. You score fit honestly."
)


def discover_candidates(
    category: str, country: str, city: str | None, limit: int
) -> list[dict[str, Any]]:
    """Find public business listings via search."""
    query = CATEGORY_QUERIES.get(category, "{category} {city} {country}").format(
        category=category, city=city or "", country=country
    )
    hits = web_search(query, max_results=min(limit * 2, 20))

    candidates: list[dict[str, Any]] = []
    for hit in hits:
        url = hit.get("url") or ""
        candidates.append(
            {
                "company_name": (hit.get("title") or url)[:220],
                "website": url,
                "source_url": url,
                "snippet": (hit.get("content") or "")[:800],
                "source": hit.get("source", "search"),
            }
        )
    return candidates[: max(limit * 2, limit)]


def enrich_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Fetch the company page and pull contact signals."""
    url = candidate.get("website")
    enriched = dict(candidate)
    if not url:
        return enriched
    try:
        text = fetch_text(url)
        emails = extract_emails(text)
        if emails:
            enriched["contact_email"] = emails[0]
            enriched["all_emails"] = emails[:3]
        # Cheap heuristic for a contact person's name in the page text.
        match = re.search(
            r"(?:contact|founder|director|manager|partner)[^\n]{0,40}?\b([A-Z][a-z]+ [A-Z][a-z]+)\b",
            text,
        )
        if match:
            enriched["contact_name"] = match.group(1)
        enriched["page_excerpt"] = text[:1500]
    except Exception as exc:  # pragma: no cover - network
        logger.debug("enrichment failed for %s: %s", url, exc)
    return enriched


def score_candidates(
    brand: str, category: str, candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Use the LLM to score fit; fall back to a deterministic heuristic."""
    if not candidates:
        return []

    if not is_available():
        return _heuristic_score(brand, category, candidates)

    payload = [
        {
            "company_name": c.get("company_name"),
            "website": c.get("website"),
            "contact_email": c.get("contact_email"),
            "contact_name": c.get("contact_name"),
            "snippet": (c.get("snippet") or c.get("page_excerpt") or "")[:400],
        }
        for c in candidates
    ]

    prompt = (
        f"{brand_block(brand)}\n"
        f"TARGET CATEGORY: {category}\n\n"
        "Score each prospect 0-100 on how well they fit this brand's ideal customer. "
        "Consider: relevance of the category, size signals, geography, and whether a "
        "reachable contact exists. Provide 2-4 short score_reasons per lead. "
        "Never invent an email address — only pass through what is in the source data.\n\n"
        f"PROSPECTS:\n{payload}\n\nRespond as JSON with a `leads` array."
    )

    try:
        batch: LeadBatch = chat_json(LEAD_SYSTEM, prompt, LeadBatch, temperature=0.3)
        scored = [l.model_dump(mode="json") for l in batch.leads]
    except Exception as exc:
        logger.warning("lead scoring LLM failed: %s", exc)
        return _heuristic_score(brand, category, candidates)

    # Merge back any fields the model dropped.
    for i, s in enumerate(scored):
        if i < len(candidates):
            s["website"] = s.get("website") or candidates[i].get("website")
            s["source_url"] = s.get("source_url") or candidates[i].get("source_url")
            s["contact_email"] = s.get("contact_email") or candidates[i].get("contact_email")
            s["contact_name"] = s.get("contact_name") or candidates[i].get("contact_name")
    return scored


def _heuristic_score(
    brand: str, category: str, candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    expected_brand = CATEGORY_TO_BRAND.get(category)
    out = []
    for c in candidates:
        score = 40.0
        reasons: list[str] = []
        if expected_brand == brand:
            score += 25
            reasons.append(f"Category '{category}' matches {brand}'s core segment.")
        if c.get("contact_email"):
            score += 20
            reasons.append("Public contact email found — outreach is possible.")
        if c.get("website"):
            score += 10
            reasons.append("Company website available for qualification.")
        if c.get("contact_name"):
            score += 5
            reasons.append("Named contact identified.")
        out.append(
            {
                "company_name": c.get("company_name") or "Unknown",
                "category": category,
                "country": None,
                "city": None,
                "website": c.get("website"),
                "contact_name": c.get("contact_name"),
                "contact_email": c.get("contact_email"),
                "contact_role": None,
                "source_url": c.get("source_url") or c.get("website"),
                "fit_score": min(score, 100.0),
                "score_reasons": reasons or ["Insufficient public signals."],
            }
        )
    return out


def persist_leads(db: Session, brand: str, scored: list[dict[str, Any]]) -> list[Lead]:
    """Upsert scored prospects into the database."""
    saved: list[Lead] = []
    for s in scored:
        website = s.get("website")
        email = s.get("contact_email")

        existing = None
        if website:
            existing = db.query(Lead).filter(Lead.website == website).first()
        if not existing and email:
            existing = db.query(Lead).filter(Lead.contact_email == email).first()

        if existing:
            existing.fit_score = float(s.get("fit_score", existing.fit_score))
            existing.score_reasons = s.get("score_reasons", existing.score_reasons)
            existing.brand_fit = brand
            if existing.status == LeadStatus.new.value:
                existing.status = LeadStatus.scored.value
            saved.append(existing)
            continue

        lead = Lead(
            company_name=str(s.get("company_name") or "Unknown")[:240],
            category=str(s.get("category") or "other"),
            country=s.get("country"),
            city=s.get("city"),
            website=website,
            contact_name=s.get("contact_name"),
            contact_email=email,
            contact_role=s.get("contact_role"),
            source_url=s.get("source_url"),
            source="search+scrape",
            brand_fit=brand,
            fit_score=float(s.get("fit_score", 0.0)),
            score_reasons=s.get("score_reasons", []),
            status=LeadStatus.scored.value,
        )
        db.add(lead)
        saved.append(lead)

    db.commit()
    for lead in saved:
        db.refresh(lead)
    return saved


def draft_outreach(
    db: Session, lead: Lead, brand: str, language: str = "en", channel: str = "email"
) -> OutreachDraft:
    """Draft a personalised, compliant first-touch message."""
    from app.agents.prompts import brand_block as _bb

    if is_available():
        prompt = (
            f"{_bb(brand)}\n"
            f"LANGUAGE: {language}\nCHANNEL: {channel}\n\n"
            f"PROSPECT:\n"
            f"- Company: {lead.company_name}\n"
            f"- Category: {lead.category}\n"
            f"- Location: {lead.city or ''} {lead.country or ''}\n"
            f"- Contact: {lead.contact_name or 'unknown'}\n"
            f"- Website: {lead.website or 'unknown'}\n"
            f"- Fit reasons: {lead.score_reasons}\n\n"
            "Write a SHORT, specific, non-salesy first-touch message (under 130 words). "
            "Lead with one concrete observation about their business or sector. "
            "Offer a specific, low-commitment value exchange. "
            "No guarantees, no pricing promises, no superlatives. "
            "Include a soft CTA. Respond as JSON with subject, body and cta."
        )
        try:
            email: OutreachEmail = chat_json(
                "You write concise, credible B2B outreach for a specialist insurer.",
                prompt,
                OutreachEmail,
                temperature=0.6,
            )
            subject, body, cta = email.subject, email.body, email.cta
        except Exception as exc:
            logger.warning("outreach LLM failed: %s", exc)
            subject, body, cta = _fallback_outreach(lead, brand)
    else:
        subject, body, cta = _fallback_outreach(lead, brand)

    draft = OutreachDraft(
        lead_id=lead.id,
        channel=channel,
        language=language,
        subject=subject,
        body=body,
        status="pending_review",
    )
    db.add(draft)
    lead.status = LeadStatus.outreach_drafted.value
    db.commit()
    db.refresh(draft)
    return draft


def _fallback_outreach(lead: Lead, brand: str) -> tuple[str, str, str]:
    brand_label = brand.replace("_", " ").title()
    subject = f"Question about {lead.company_name}'s cover"
    body = (
        f"Hi {lead.contact_name or 'there'},\n\n"
        f"I noticed {lead.company_name} operates in the {lead.category} space"
        + (f" in {lead.city}" if lead.city else "")
        + ".\n\n"
        f"We work with similar businesses on specialist cover through {brand_label}. "
        "Most teams we speak to find one or two gaps when they review limits and "
        "transit exposure side by side.\n\n"
        "Would a short 15-minute review of your current position be useful? "
        "No obligation, and we'll share the checklist we use either way.\n\n"
        "Best regards,\nJA Assure Team\n\n"
        "Cover is subject to policy terms and underwriting."
    )
    return subject, body, "Reply to book a 15-minute cover review."


# ---------------------------------------------------------------------------
# LangGraph nodes
# ---------------------------------------------------------------------------
def lead_discovery_node(state: dict) -> dict:
    try:
        candidates = discover_candidates(
            state["category"], state["country"], state.get("city"), int(state["limit"])
        )
        return {"raw_candidates": candidates}
    except Exception as exc:
        logger.exception("discovery failed")
        return {"raw_candidates": [], "errors": list(state.get("errors", [])) + [str(exc)]}


def lead_enrichment_node(state: dict) -> dict:
    enriched = [enrich_candidate(c) for c in state.get("raw_candidates", [])]
    return {"enriched": enriched}


def lead_scoring_node(state: dict) -> dict:
    scored = score_candidates(
        state["brand"], state["category"], state.get("enriched", [])
    )
    return {"scored": scored}


def lead_persist_node(state: dict) -> dict:
    from app.db import SessionLocal

    with SessionLocal() as db:
        leads = persist_leads(db, state["brand"], state.get("scored", []))
        return {"lead_ids": [l.id for l in leads]}