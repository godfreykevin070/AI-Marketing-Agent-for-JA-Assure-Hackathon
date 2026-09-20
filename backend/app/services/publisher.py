"""Project 2 — posting APIs. dry_run by default so the demo always works."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

BUFFER_GRAPHQL = "https://api.bufferapp.com/1/graphql"
AYRSHARE_POST = "https://app.ayrshare.com/api/post"


class PublisherError(RuntimeError):
    pass


class BasePublisher:
    name = "base"

    def publish(self, asset_row: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def fetch_analytics(self, external_post_id: str) -> dict[str, Any]:
        return {}


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
        # Deterministic pseudo-metrics so the analytics loop is demonstrable.
        seed = abs(hash(external_post_id)) % 1000
        return {
            "impressions": 400 + seed,
            "likes": 12 + seed // 20,
            "comments": 1 + seed // 120,
            "shares": seed // 90,
            "clicks": 5 + seed // 60,
            "source": "dry_run_simulated",
        }


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
        variables = {
            "input": {
                "text": text,
                "channelId": profile_id,
                "schedulingType": "automatic",
                "mode": "shareNow",
                "assets": [
                    {"type": "image", "url": url}
                    for url in (asset_row.get("media_urls") or [])
                    if str(url).lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
                ],
            }
        }

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
        # Buffer exposes read endpoints; scaffolded for extension.
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


class AyrsharePublisher(BasePublisher):
    name = "ayrshare"

    def __init__(self) -> None:
        self.settings = get_settings()

    def publish(self, asset_row: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.ayrshare_api_key:
            raise PublisherError("AYRSHARE_API_KEY is not configured")

        response = httpx.post(
            AYRSHARE_POST,
            headers={
                "Authorization": f"Bearer {self.settings.ayrshare_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "post": BufferPublisher._compose_text(asset_row),
                "platforms": [asset_row.get("platform", "linkedin")],
                "mediaUrls": asset_row.get("media_urls") or [],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "external_post_id": data.get("id") or data.get("postIds", [None])[0],
            "permalink": (data.get("postIds") or {}).get("status") if isinstance(data.get("postIds"), dict) else None,
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