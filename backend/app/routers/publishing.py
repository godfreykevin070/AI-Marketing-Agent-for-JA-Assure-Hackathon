"""Project 2 — The Hands API surface."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import AssetStatus
from app.models import ContentAsset, PostResult
from app.schemas import AssetOut, PostResultOut
from app.workers.publish_worker import pull_analytics, publish_approved

router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.get("/queue", response_model=list[AssetOut])
def approved_queue(db: Session = Depends(get_db)) -> list[AssetOut]:
    """Assets the human approved, waiting for the worker."""
    rows = list(
        db.execute(
            select(ContentAsset)
            .where(ContentAsset.status == AssetStatus.approved.value)
            .order_by(desc(ContentAsset.updated_at))
        )
        .scalars()
        .all()
    )
    return [AssetOut.model_validate(a) for a in rows]


@router.post("/run")
def run_worker(
    db: Session = Depends(get_db), limit: int = Query(default=25, ge=1, le=100)
) -> dict:
    """Trigger the publish worker once (useful for demos and CI)."""
    return publish_approved(db)


@router.post("/pull-analytics")
def run_analytics(db: Session = Depends(get_db)) -> dict:
    return pull_analytics(db)


@router.get("/results", response_model=list[PostResultOut])
def results(
    db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)
) -> list[PostResultOut]:
    rows = list(
        db.execute(select(PostResult).order_by(desc(PostResult.created_at)).limit(limit))
        .scalars()
        .all()
    )
    return [PostResultOut.model_validate(r) for r in rows]