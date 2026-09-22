"""Project 2 — The Hands.

Polls `content_assets` for rows the human approved, publishes them through the
configured posting API, stores the external post id, and flips status to
`scheduled`. A second job pulls engagement analytics back into the database.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.enums import AssetStatus, PostStatus
from app.models import ContentAsset, PostResult
from app.services.publisher import PublisherError, get_publisher

logger = logging.getLogger(__name__)


def _asset_to_row(asset: ContentAsset) -> dict:
    return {
        "id": asset.id,
        "brand": asset.brand,
        "platform": asset.platform,
        "title": asset.title,
        "hook": asset.hook,
        "body": asset.body,
        "cta": asset.cta,
        "hashtags": asset.hashtags or [],
        "media_urls": asset.media_urls or [],
        "source_topic": asset.source_topic,
    }


def publish_approved(db: Session | None = None) -> dict:
    """Publish every approved asset that has not yet been handed to the API."""
    owns_session = db is None
    db = db or SessionLocal()
    publisher = get_publisher()

    published, failed = [], []

    try:
        already_queued = select(PostResult.asset_id)
        candidates = list(
            db.execute(
                select(ContentAsset)
                .where(
                    ContentAsset.status == AssetStatus.approved.value,
                    ContentAsset.id.notin_(already_queued),
                )
                .order_by(ContentAsset.updated_at.asc())
                .limit(25)
            )
            .scalars()
            .all()
        )

        if candidates:
            logger.info(
                "publish job: %d approved asset(s) to process via %s",
                len(candidates),
                publisher.name,
            )

        for asset in candidates:
            row = _asset_to_row(asset)
            result = PostResult(
                asset_id=asset.id,
                platform=asset.platform,
                publisher=publisher.name,
                status=PostStatus.pending.value,
            )
            db.add(result)
            db.flush()

            try:
                response = publisher.publish(row)
                result.external_post_id = response.get("external_post_id")
                result.permalink = response.get("permalink")
                result.status = response.get("status", PostStatus.scheduled.value)
                result.scheduled_for = datetime.now(timezone.utc)
                asset.status = AssetStatus.scheduled.value
                published.append(asset.id)
                logger.info(
                    "publish ok: %s → %s (%s)",
                    asset.id,
                    asset.platform,
                    result.external_post_id or "no-id",
                )
            except PublisherError as exc:
                # Business-rule rejection from the publisher. This used to be
                # silent — keep the log line.
                result.status = PostStatus.failed.value
                result.error = str(exc)
                asset.status = AssetStatus.failed.value
                failed.append({"asset_id": asset.id, "error": str(exc)})
                logger.error(
                    "publish rejected for %s (%s): %s",
                    asset.id,
                    asset.platform,
                    exc,
                )
            except Exception as exc:
                logger.exception("publish failed for %s", asset.id)
                result.status = PostStatus.failed.value
                result.error = str(exc)
                asset.status = AssetStatus.failed.value
                failed.append({"asset_id": asset.id, "error": str(exc)})

        db.commit()
    finally:
        if owns_session:
            db.close()

    return {"published": published, "failed": failed, "count": len(published)}


def pull_analytics(db: Session | None = None) -> dict:
    """Fetch engagement for scheduled/published posts and write it back."""
    owns_session = db is None
    db = db or SessionLocal()
    publisher = get_publisher()

    updated = 0
    try:
        results = list(
            db.execute(
                select(PostResult).where(
                    PostResult.status.in_(
                        [PostStatus.scheduled.value, PostStatus.published.value]
                    ),
                    PostResult.external_post_id.isnot(None),
                )
            )
            .scalars()
            .all()
        )

        for result in results:
            try:
                analytics = publisher.fetch_analytics(result.external_post_id or "")
            except Exception as exc:
                logger.debug("analytics fetch failed: %s", exc)
                continue
            if not analytics:
                continue
            result.analytics = analytics
            result.analytics_fetched_at = datetime.now(timezone.utc)
            if result.status == PostStatus.scheduled.value:
                result.status = PostStatus.published.value
                result.posted_at = result.posted_at or datetime.now(timezone.utc)
            updated += 1

        db.commit()
    finally:
        if owns_session:
            db.close()

    return {"updated": updated}


def mark_published(asset_ids: list[str], db: Session | None = None) -> int:
    """Utility: flip scheduled assets to published."""
    owns_session = db is None
    db = db or SessionLocal()
    count = 0
    try:
        for asset in db.execute(
            select(ContentAsset).where(ContentAsset.id.in_(asset_ids))
        ).scalars():
            asset.status = AssetStatus.published.value
            count += 1
        db.commit()
    finally:
        if owns_session:
            db.close()
    return count