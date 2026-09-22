"""Web search abstraction — Tavily first, then Serper, then empty."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _tavily(query: str, max_results: int, include_images: bool = False) -> list[dict[str, Any]]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily_api_key)
        data = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
            include_images=include_images,
        )
        results = []
        for r in data.get("results", []):
            entry = {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),
                "source": "tavily",
            }
            if include_images and r.get("images"):
                entry["images"] = r["images"]  # list of image URLs
            results.append(entry)
        return results
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


def web_search(
    query: str,
    max_results: int = 5,
    include_images: bool = False,
) -> list[dict[str, Any]]:
    """Search the public web. Returns [] when no provider is configured."""
    results = _tavily(query, max_results, include_images=include_images)
    if not results:
        results = _serper(query, max_results)
    return results

def search_images_serper(query: str, num: int = 5) -> list[str]:
    """Return image URLs from Google Images via Serper."""
    settings = get_settings()
    if not settings.serper_api_key:
        return []
    try:
        response = httpx.post(
            "https://google.serper.dev/images",
            headers={
                "X-API-KEY": settings.serper_api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": num},
            timeout=25.0,
        )
        response.raise_for_status()
        data = response.json()
        return [
            r.get("imageUrl")
            for r in data.get("images", [])
            if r.get("imageUrl")
        ]
    except Exception as exc:
        logger.warning("serper image search failed: %s", exc)
        return []