from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.agents.research_agent import (
    build_digest,
    gather_web_context,
    snapshot_competitors,
)
from app.db import get_db
from app.models import CompetitorSnapshot, ResearchDigest
from app.schemas import DigestOut, ResearchRequest

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/competitors", response_model=DigestOut)
def competitor_digest(payload: ResearchRequest, db: Session = Depends(get_db)) -> DigestOut:
    """Scrape competitor pages, diff against the last snapshot, and produce a digest."""
    context = gather_web_context(payload.brand.value, payload.topic)
    changes = snapshot_competitors(
        db, payload.brand.value, payload.competitors, payload.urls
    )
    digest = build_digest(db, payload.brand.value, payload.topic, context, changes)
    return DigestOut.model_validate(digest)


@router.get("/digests", response_model=list[DigestOut])
def list_digests(
    db: Session = Depends(get_db),
    brand: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[DigestOut]:
    stmt = select(ResearchDigest).order_by(desc(ResearchDigest.created_at)).limit(limit)
    if brand:
        stmt = stmt.where(ResearchDigest.brand == brand)
    rows = list(db.execute(stmt).scalars().all())
    return [DigestOut.model_validate(r) for r in rows]


@router.get("/snapshots")
def list_snapshots(
    db: Session = Depends(get_db),
    brand: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    stmt = (
        select(CompetitorSnapshot)
        .order_by(desc(CompetitorSnapshot.captured_at))
        .limit(limit)
    )
    if brand:
        stmt = stmt.where(CompetitorSnapshot.brand == brand)
    rows = list(db.execute(stmt).scalars().all())
    return [
        {
            "id": r.id,
            "brand": r.brand,
            "competitor": r.competitor,
            "url": r.url,
            "changed": r.changed,
            "captured_at": r.captured_at.isoformat(),
        }
        for r in rows
    ]