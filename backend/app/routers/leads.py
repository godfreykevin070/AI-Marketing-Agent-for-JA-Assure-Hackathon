from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.agents.graph import run_lead_pipeline
from app.agents.lead_agent import draft_outreach
from app.db import get_db
from app.enums import LeadStatus
from app.models import Lead, OutreachDraft
from app.schemas import LeadDiscoveryRequest, LeadOut, OutreachOut, OutreachRequest

from app.deps import require_editor

router = APIRouter(prefix="/leads", tags=["leads"], dependencies=[Depends(require_editor)])


@router.post("/discover", response_model=list[LeadOut])
def discover(payload: LeadDiscoveryRequest, db: Session = Depends(get_db)) -> list[LeadOut]:
    """Run the lead agent: discover → enrich → score → persist."""
    result = run_lead_pipeline(
        db,
        brand=payload.brand.value,
        category=payload.category.value,
        country=payload.country,
        city=payload.city,
        limit=payload.limit,
    )
    ids = result.get("lead_ids", [])
    if not ids:
        return []
    leads = list(db.execute(select(Lead).where(Lead.id.in_(ids))).scalars().all())
    order = {lid: i for i, lid in enumerate(ids)}
    leads.sort(key=lambda l: order.get(l.id, 0))
    return [LeadOut.model_validate(l) for l in leads]


@router.get("", response_model=list[LeadOut])
def list_leads(
    db: Session = Depends(get_db),
    brand: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_score: float = Query(default=0, ge=0, le=100),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[LeadOut]:
    stmt = (
        select(Lead)
        .where(Lead.fit_score >= min_score)
        .order_by(desc(Lead.fit_score))
        .limit(limit)
    )
    if brand:
        stmt = stmt.where(Lead.brand_fit == brand)
    if category:
        stmt = stmt.where(Lead.category == category)
    rows = list(db.execute(stmt).scalars().all())
    return [LeadOut.model_validate(l) for l in rows]


@router.post("/outreach", response_model=OutreachOut)
def create_outreach(payload: OutreachRequest, db: Session = Depends(get_db)) -> OutreachOut:
    lead = db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    draft = draft_outreach(
        db,
        lead=lead,
        brand=lead.brand_fit or "ja_assure",
        language=payload.language.value,
        channel=payload.channel,
    )

    # Run the same compliance gate as content assets.
    from app.agents.compliance_agent import evaluate_assets
    from app.enums import ComplianceStatus

    verdicts = evaluate_assets(
        lead.brand_fit or "ja_assure",
        [{"title": draft.subject, "body": draft.body, "cta": "", "platform": "email"}],
    )
    verdict = verdicts.get(0)
    if verdict:
        draft.compliance_report = verdict
        draft.compliance_status = verdict.get("status", ComplianceStatus.unchecked.value)
        db.commit()
        db.refresh(draft)

    return OutreachOut.model_validate(draft)


@router.get("/outreach", response_model=list[OutreachOut])
def list_outreach(
    db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)
) -> list[OutreachOut]:
    rows = list(
        db.execute(
            select(OutreachDraft).order_by(desc(OutreachDraft.created_at)).limit(limit)
        )
        .scalars()
        .all()
    )
    return [OutreachOut.model_validate(r) for r in rows]


@router.post("/outreach/{draft_id}/decision", response_model=OutreachOut)
def decide_outreach(
    draft_id: str,
    decision: str = Query(pattern="^(approve|reject)$"),
    db: Session = Depends(get_db),
) -> OutreachOut:
    draft = db.get(OutreachDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Outreach draft not found")

    draft.status = "approved" if decision == "approve" else "rejected"
    lead = db.get(Lead, draft.lead_id)
    if lead:
        lead.status = (
            LeadStatus.outreach_approved.value
            if decision == "approve"
            else LeadStatus.rejected.value
        )
    db.commit()
    db.refresh(draft)
    return OutreachOut.model_validate(draft)