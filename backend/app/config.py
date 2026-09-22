"""Central configuration. All secrets come from environment variables."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "JA Assure AI Marketing Agent"
    environment: str = "development"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Database ---
    database_url: str = "sqlite:///./ja_assure.db"

    # --- Auth ---
    jwt_secret_key: str = "change-me-in-production-please-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    default_admin_email: str = "admin@jaassure.com"
    default_admin_password: str = "admin@123"
    default_admin_name: str = "JA Assure Admin"

    # --- LLM ---
    groq_api_key: str = ""
    groq_api_key_secondary: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-120b"
    llm_fast_model: str = "openai/gpt-oss-20b"
    llm_temperature: float = 0.6
    llm_max_tokens: int = 1500

    # --- Research / media ---
    tavily_api_key: str = ""
    serper_api_key: str = ""
    pexels_api_key: str = ""

    # --- Publishing (Project 2) ---
    publisher_backend: str = "dry_run"  # dry_run | buffer | ayrshare
    buffer_api_key: str = ""
    buffer_profile_ids: str = "{}"
    ayrshare_api_key: str = ""

    # --- Media ---
    media_dir: str = "./media"
    public_media_base_url: str = "http://localhost:8000/media"
    enable_video_render: bool = True

    # --- Worker ---
    enable_scheduler: bool = True
    publish_poll_seconds: int = 60
    analytics_poll_seconds: int = 600
    max_compliance_retries: int = 2

    # ------------------------------------------------------------------
    @field_validator("database_url")
    @classmethod
    def _normalise_db_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def buffer_profiles(self) -> dict[str, str]:
        try:
            data: Any = json.loads(self.buffer_profile_ids or "{}")
            return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @property
    def llm_enabled(self) -> bool:
        return bool(self.groq_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()