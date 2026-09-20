from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.agents.feedback_agent import feedback_stats, record_feedback
from app.db import get_db
from app.enums import AssetStatus
from app.models import ContentAsset, Feedback, Lesson
from app.schemas import AssetOut, FeedbackOut, LessonOut, ReviewDecisionRequest

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue", response_model=list[AssetOut])
def review_queue(
    db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)
) -> list[AssetOut]:
    """Everything waiting on a human decision."""
    assets = list(
        db.execute(
            select(ContentAsset)
            .where(ContentAsset.status == AssetStatus.pending_review.value)
            .order_by(desc(ContentAsset.created_at))
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [AssetOut.model_validate(a) for a in assets]


@router.post("/{asset_id}/decision", response_model=AssetOut)
def decide(
    asset_id: str, payload: ReviewDecisionRequest, db: Session = Depends(get_db)
) -> AssetOut:
    """The mandatory human-in-the-loop gate. Approve, edit, or reject.

    Rejections and edits are distilled into reusable lessons and fed back into
    the content agent on the next run.
    """
    asset = db.get(ContentAsset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.status != AssetStatus.pending_review.value:
        raise HTTPException(
            status_code=409,
            detail=f"Asset is '{asset.status}', not pending review",
        )

    if payload.decision in ("reject", "edit") and not (payload.reason_tag or payload.note):
        raise HTTPException(
            status_code=422,
            detail="A reason tag or note is required when rejecting or editing.",
        )

    record_feedback(
        db=db,
        asset=asset,
        decision=payload.decision,
        editor=payload.editor,
        reason_tag=payload.reason_tag.value if payload.reason_tag else None,
        note=payload.note,
        edited_title=payload.edited_title,
        edited_body=payload.edited_body,
        edited_cta=payload.edited_cta,
    )
    db.refresh(asset)
    return AssetOut.model_validate(asset)


@router.get("/feedback", response_model=list[FeedbackOut])
def list_feedback(
    db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)
) -> list[FeedbackOut]:
    rows = list(
        db.execute(select(Feedback).order_by(desc(Feedback.created_at)).limit(limit))
        .scalars()
        .all()
    )
    return [FeedbackOut.model_validate(r) for r in rows]


@router.get("/lessons", response_model=list[LessonOut])
def list_lessons(
    db: Session = Depends(get_db),
    brand: str | None = Query(default=None),
    active_only: bool = Query(default=True),
) -> list[LessonOut]:
    stmt = select(Lesson).order_by(desc(Lesson.occurrences), desc(Lesson.updated_at))
    if brand:
        stmt = stmt.where(Lesson.brand == brand)
    if active_only:
        stmt = stmt.where(Lesson.active.is_(True))
    rows = list(db.execute(stmt).scalars().all())
    return [LessonOut.model_validate(r) for r in rows]


@router.get("/stats")
def stats(db: Session = Depends(get_db), brand: str | None = Query(default=None)) -> dict:
    return feedback_stats(db, brand)