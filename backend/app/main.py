"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.db import init_db
from app.routers import (
    analytics,
    content,
    health,
    leads,
    publishing,
    research,
    review,
    auth,
    users
)
from app.seed import ensure_default_admin
from app.workers.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s :: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    ensure_default_admin()
    Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
    scheduler = start_scheduler()
    logger.info("%s v%s started (%s)", settings.app_name, __version__, settings.environment)
    try:
        yield
    finally:
        if scheduler is not None:
            stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Agentic AI marketing system for JA Assure. Project 1 (The Brain) produces "
        "approved, ready-to-publish assets; Project 2 (The Hands) publishes them."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated media (images, reels) at a public URL for the posting APIs.
_media_path = Path(settings.media_dir)
_media_path.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media_path)), name="media")

# Routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(content.router, prefix=settings.api_prefix)
app.include_router(review.router, prefix=settings.api_prefix)
app.include_router(research.router, prefix=settings.api_prefix)
app.include_router(leads.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)
app.include_router(publishing.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "api": settings.api_prefix,
    }