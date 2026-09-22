"""Project 2 — posting APIs. dry_run by default so the demo always works."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

BUFFER_GRAPHQL = "https://api.buffer.com"
AYRSHARE_POST = "https://app.ayrshare.com/api/post"


class PublisherError(RuntimeError):
    pass


def _media_type(url: str) -> str | None:
    """Return 'image' or 'video' for a URL, ignoring query params."""
    path = urlparse(str(url)).path.lower()
    if path.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return "image"
    if path.endswith((".mp4", ".mov", ".webm")):
        return "video"
    return None


# ---------------------------------------------------------------------------
# Image sourcing (used as last-resort fallback for platforms that require media)
# ---------------------------------------------------------------------------
def fetch_relevant_image(
    brand: str,
    title: str,
    topic: str | None = None,
) -> str | None:
    """Find an existing stock image for the asset. Pexels first, Tavily fallback."""
    query_parts = [brand.replace("_", " ")]
    if topic:
        query_parts.append(topic)
    elif title:
        query_parts.append(title)
    query = " ".join(p for p in query_parts if p)[:120]

    url = _pexels_image(query)
    if url:
        logger.info("using Pexels image: %s", url)
        return url

    url = _tavily_image(query)
    if url:
        logger.info("using Tavily image: %s", url)
        return url

    logger.warning("no image found for query: %s", query)
    return None


def _pexels_image(query: str) -> str | None:
    settings = get_settings()
    if not getattr(settings, "pexels_api_key", ""):
        return None
    try:
        response = httpx.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": settings.pexels_api_key},
            params={"query": query, "per_page": 5, "orientation": "square"},
            timeout=20.0,
        )
        response.raise_for_status()
        for p in response.json().get("photos", []):
            src = p.get("src", {})
            url = src.get("medium") or src.get("large") or src.get("original")
            if url:
                return url
    except Exception as exc:
        logger.warning("pexels search failed: %s", exc)
    return None


def _tavily_image(query: str) -> str | None:
    from app.services.search import web_search
    try:
        results = web_search(query, max_results=5, include_images=True)
    except Exception as exc:
        logger.warning("tavily image search failed: %s", exc)
        return None

    for hit in results:
        for img in hit.get("images") or []:
            url = img if isinstance(img, str) else (img.get("url") if isinstance(img, dict) else None)
            if url and url.startswith("http") and not _looks_hotlink_protected(url):
                return url
    return None


def _looks_hotlink_protected(url: str) -> bool:
    blocked = (
        "blogspot.", "wordpress.com", "wixstatic.com/static",
        "instagram.com", "facebook.com", "pinterest.",
    )
    lowered = url.lower()
    return any(b in lowered for b in blocked)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class BasePublisher:
    name = "base"

    def publish(self, asset_row: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def fetch_analytics(self, external_post_id: str) -> dict[str, Any]:
        return {}


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------
class DryRunPublisher(BasePublisher):
    """Simulates a real post. Used for demos and CI."""

    name = "dry_run"

    def publish(self, asset_row: dict[str, Any]) -> dict[str, Any]:
        fake_id = f"dryrun_{uuid.uuid4().hex[:14]}"
        logger.info(
            "[dry-run] would publish %s to %s: %s",
            asset_row.get("id"),
            asset_row.get("platform"),
            (asset_row.get("title") or "")[:60],
        )
        return {
            "external_post_id": fake_id,
            "permalink": f"https://example.invalid/{asset_row.get('platform')}/{fake_id}",
            "scheduled_for": datetime.now(timezone.utc).isoformat(),
            "status": "scheduled",
        }

    def fetch_analytics(self, external_post_id: str) -> dict[str, Any]:
        seed = abs(hash(external_post_id)) % 1000
        return {
            "impressions": 400 + seed,
            "likes": 12 + seed // 20,
            "comments": 1 + seed // 120,
            "shares": seed // 90,
            "clicks": 5 + seed // 60,
            "source": "dry_run_simulated",
        }


# ---------------------------------------------------------------------------
# Buffer
# ---------------------------------------------------------------------------
class BufferPublisher(BasePublisher):
    """Buffer GraphQL createPost. Posts to your own connected accounts."""

    name = "buffer"

    _MUTATION = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess { post { id } }
        ... on MutationError { message }
      }
    }
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def publish(self, asset_row: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.buffer_api_key:
            raise PublisherError("BUFFER_API_KEY is not configured")

        platform = asset_row.get("platform", "linkedin")
        profile_id = self.settings.buffer_profiles.get(platform)
        if not profile_id:
            raise PublisherError(f"No Buffer profile id configured for '{platform}'")

        text = self._compose_text(asset_row)

        # Media is resolved during generation; build the assets array.
        assets = []
        for url in asset_row.get("media_urls") or []:
            kind = _media_type(url)
            if kind == "image":
                assets.append({"image": {"url": url}})
            elif kind == "video":
                assets.append({"video": {"url": url}})

        # Instagram requires an explicit post type. Determine it from the
        # assets: a video asset means a Reel, otherwise a standard Post.
        metadata = {}
        if platform == "instagram":
            has_video = any(
                _media_type(url) == "video" for url in asset_row.get("media_urls") or []
            )
            metadata["instagram"] = {
                "type": "reel" if has_video else "post",
                "shouldShareToFeed": True,
            }

        variables = {
            "input": {
                "text": text,
                "channelId": profile_id,
                "schedulingType": "automatic",
                "mode": "shareNow",
                "assets": assets,
            }
        }

        if metadata:
            variables["input"]["metadata"] = metadata

        response = httpx.post(
            BUFFER_GRAPHQL,
            headers={
                "Authorization": f"Bearer {self.settings.buffer_api_key}",
                "Content-Type": "application/json",
            },
            json={"query": self._MUTATION, "variables": variables},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()

        if "errors" in payload:
            raise PublisherError(str(payload["errors"]))

        data = (payload.get("data") or {}).get("createPost") or {}
        if "message" in data:
            raise PublisherError(data["message"])

        post_id = (data.get("post") or {}).get("id")
        return {
            "external_post_id": post_id,
            "permalink": None,
            "scheduled_for": datetime.now(timezone.utc).isoformat(),
            "status": "scheduled",
        }

    def fetch_analytics(self, external_post_id: str) -> dict[str, Any]:
        return {"source": "buffer", "note": "analytics endpoint not polled in prototype"}

    @staticmethod
    def _compose_text(asset_row: dict[str, Any]) -> str:
        parts = [
            asset_row.get("hook") or "",
            asset_row.get("body") or "",
            asset_row.get("cta") or "",
            " ".join(asset_row.get("hashtags") or []),
        ]
        return "\n\n".join(p for p in parts if p).strip()


# ---------------------------------------------------------------------------
# Ayrshare
# ---------------------------------------------------------------------------
class AyrsharePublisher(BasePublisher):
    name = "ayrshare"

    def __init__(self) -> None:
        self.settings = get_settings()

    def publish(self, asset_row: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.ayrshare_api_key:
            raise PublisherError("AYRSHARE_API_KEY is not configured")

        platform = asset_row.get("platform", "linkedin")
        media_urls = list(asset_row.get("media_urls") or [])

        if platform in ("instagram", "tiktok") and not media_urls:
            found = fetch_relevant_image(
                brand=str(asset_row.get("brand") or "ja_assure"),
                title=str(asset_row.get("title") or ""),
                topic=asset_row.get("source_topic"),
            )
            if found:
                media_urls = [found]

        response = httpx.post(
            AYRSHARE_POST,
            headers={
                "Authorization": f"Bearer {self.settings.ayrshare_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "post": BufferPublisher._compose_text(asset_row),
                "platforms": [platform],
                "mediaUrls": media_urls,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "external_post_id": data.get("id") or (data.get("postIds") or [None])[0],
            "permalink": None,
            "scheduled_for": datetime.now(timezone.utc).isoformat(),
            "status": "scheduled",
        }


def get_publisher() -> BasePublisher:
    backend = get_settings().publisher_backend.lower()
    if backend == "buffer":
        return BufferPublisher()
    if backend == "ayrshare":
        return AyrsharePublisher()
    return DryRunPublisher()