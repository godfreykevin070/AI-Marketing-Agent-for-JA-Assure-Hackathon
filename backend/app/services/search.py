"""Web search abstraction — Tavily first, then Serper, then empty."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _tavily(query: str, max_results: int) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily_api_key)
        data = client.search(query=query, max_results=max_results, search_depth="basic")
        return [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),
                "source": "tavily",
            }
            for r in data.get("results", [])
        ]
    except Exception as exc:
        logger.warning("tavily search failed: %s", exc)
        return []


def _serper(query: str, max_results: int) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.serper_api_key:
        return []
    try:
        response = httpx.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": settings.serper_api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": max_results},
            timeout=25.0,
        )
        response.raise_for_status()
        data = response.json()
        return [
            {
                "title": r.get("title"),
                "url": r.get("link"),
                "content": r.get("snippet"),
                "source": "serper",
            }
            for r in data.get("organic", [])
        ]
    except Exception as exc:
        logger.warning("serper search failed: %s", exc)
        return []


def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the public web. Returns [] when no provider is configured."""
    results = _tavily(query, max_results)
    if not results:
        results = _serper(query, max_results)
    if not results:
        logger.info("no search provider configured or no results for: %s", query)
    return results