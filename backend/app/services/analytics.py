"""Aggregate analytics for the dashboard and the content feedback loop."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ContentAsset, Feedback, PostResult


def overview(db: Session) -> dict:
    total_assets = db.scalar(select(func.count()).select_from(ContentAsset)) or 0

    by_status: dict[str, int] = defaultdict(int)
    for status, count in db.execute(
        select(ContentAsset.status, func.count()).group_by(ContentAsset.status)
    ):
        by_status[status] = count

    by_brand: dict[str, int] = defaultdict(int)
    for brand, count in db.execute(
        select(ContentAsset.brand, func.count()).group_by(ContentAsset.brand)
    ):
        by_brand[brand] = count

    by_platform: dict[str, int] = defaultdict(int)
    for platform, count in db.execute(
        select(ContentAsset.platform, func.count()).group_by(ContentAsset.platform)
    ):
        by_platform[platform] = count

    total_reviews = db.scalar(select(func.count()).select_from(Feedback)) or 0
    rejected = (
        db.scalar(
            select(func.count()).select_from(Feedback).where(Feedback.decision == "reject")
        )
        or 0
    )

    posts_published = (
        db.scalar(
            select(func.count())
            .select_from(PostResult)
            .where(PostResult.status.in_(["published", "scheduled"]))
        )
        or 0
    )

    return {
        "total_assets": total_assets,
        "by_status": dict(by_status),
        "by_brand": dict(by_brand),
        "by_platform": dict(by_platform),
        "total_reviews": total_reviews,
        "rejection_rate": round(rejected / total_reviews, 4) if total_reviews else 0.0,
        "posts_published": posts_published,
    }


def feedback_trend(db: Session, weeks: int = 8) -> list[dict]:
    """Rejection rate + average edit similarity per ISO week — proves learning."""
    since = datetime.now(timezone.utc) - timedelta(weeks=weeks)
    rows = list(
        db.execute(select(Feedback).where(Feedback.created_at >= since)).scalars().all()
    )

    buckets: dict[str, dict] = defaultdict(
        lambda: {"reviews": 0, "rejects": 0, "edits": 0, "ratios": []}
    )
    for row in rows:
        created = row.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        key = created.strftime("%G-W%V")
        bucket = buckets[key]
        bucket["reviews"] += 1
        if row.decision == "reject":
            bucket["rejects"] += 1
        if row.decision == "edit":
            bucket["edits"] += 1
        if row.edit_ratio is not None:
            bucket["ratios"].append(row.edit_ratio)

    out = []
    for key in sorted(buckets):
        b = buckets[key]
        out.append(
            {
                "week": key,
                "reviews": b["reviews"],
                "rejection_rate": round(b["rejects"] / b["reviews"], 4) if b["reviews"] else 0,
                "edit_rate": round(b["edits"] / b["reviews"], 4) if b["reviews"] else 0,
                "avg_edit_similarity": (
                    round(sum(b["ratios"]) / len(b["ratios"]), 4) if b["ratios"] else None
                ),
            }
        )
    return out


def reason_tag_breakdown(db: Session) -> list[dict]:
    rows = db.execute(
        select(Feedback.reason_tag, func.count())
        .where(Feedback.reason_tag.isnot(None))
        .group_by(Feedback.reason_tag)
        .order_by(func.count().desc())
    ).all()
    return [{"reason_tag": tag, "count": count} for tag, count in rows]


def engagement_summary(db: Session) -> dict:
    results = list(db.execute(select(PostResult)).scalars().all())
    totals = defaultdict(int)
    for r in results:
        for key in ("impressions", "likes", "comments", "shares", "clicks"):
            totals[key] += int((r.analytics or {}).get(key, 0) or 0)
    count = len(results)
    return {
        "posts_tracked": count,
        "totals": dict(totals),
        "averages": {k: round(v / count, 2) for k, v in totals.items()} if count else {},
    }