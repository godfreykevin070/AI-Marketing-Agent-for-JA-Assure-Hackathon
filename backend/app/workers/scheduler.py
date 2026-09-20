"""APScheduler wiring — a real background worker, not a no-code tool."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.workers.publish_worker import publish_approved, pull_analytics

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _publish_job() -> None:
    try:
        result = publish_approved()
        if result["count"]:
            logger.info("publish job: %s asset(s) scheduled", result["count"])
    except Exception:  # pragma: no cover
        logger.exception("publish job crashed")


def _analytics_job() -> None:
    try:
        result = pull_analytics()
        if result["updated"]:
            logger.info("analytics job: %s post(s) updated", result["updated"])
    except Exception:  # pragma: no cover
        logger.exception("analytics job crashed")


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    settings = get_settings()
    if not settings.enable_scheduler:
        logger.info("scheduler disabled via ENABLE_SCHEDULER=false")
        return None
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _publish_job,
        "interval",
        seconds=settings.publish_poll_seconds,
        id="publish_approved",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        _analytics_job,
        "interval",
        seconds=settings.analytics_poll_seconds,
        id="pull_analytics",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info(
        "scheduler started (publish every %ss, analytics every %ss)",
        settings.publish_poll_seconds,
        settings.analytics_poll_seconds,
    )
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("scheduler stopped")