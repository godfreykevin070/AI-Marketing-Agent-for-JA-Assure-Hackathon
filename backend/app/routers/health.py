from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.config import get_settings
from app.llm import is_available

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.environment,
        "llm_enabled": is_available(),
        "publisher_backend": settings.publisher_backend,
        "search_enabled": bool(settings.tavily_api_key or settings.serper_api_key),
    }