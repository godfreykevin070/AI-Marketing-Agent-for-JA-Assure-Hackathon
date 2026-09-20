from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import PostResult
from app.schemas import PostResultOut
from app.services import analytics as analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    return analytics_service.overview(db)


@router.get("/feedback-trend")
def feedback_trend(db: Session = Depends(get_db), weeks: int = Query(default=8, ge=1, le=52)) -> list[dict]:
    return analytics_service.feedback_trend(db, weeks)


@router.get("/reason-tags")
def reason_tags(db: Session = Depends(get_db)) -> list[dict]:
    return analytics_service.reason_tag_breakdown(db)


@router.get("/engagement")
def engagement(db: Session = Depends(get_db)) -> dict:
    return analytics_service.engagement_summary(db)


@router.get("/posts", response_model=list[PostResultOut])
def posts(
    db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)
) -> list[PostResultOut]:
    rows = list(
        db.execute(select(PostResult).order_by(desc(PostResult.created_at)).limit(limit))
        .scalars()
        .all()
    )
    return [PostResultOut.model_validate(r) for r in rows]