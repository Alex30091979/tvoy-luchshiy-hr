"""Application configuration via environment (see .env.example)."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic import AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = Field(default="SEO AI Agent", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_json: bool = Field(default=False, description="Structured JSON logs (env: LOG_JSON)")
    dry_run: bool = Field(default=True, description="Generate but do not publish")

    # Publish mode: auto | semi (env: MODE or PUBLISH_MODE)
    publish_mode: Literal["auto", "semi"] = Field(
        default="semi", description="auto=direct publish, semi=draft+approval",
        validation_alias=AliasChoices("MODE", "PUBLISH_MODE"),
    )

    # MVP limits (overridable from admin / DB)
    articles_per_day: int = Field(default=1, description="Max articles per day")
    moscow_share: float = Field(default=0.7, ge=0, le=1, description="Share of Moscow vs RF")

    # Database (DB_URL or DATABASE_URL)
    database_url: str = Field(
        default="postgresql+asyncpg://seo:seo@localhost:5432/seo_agent",
        description="PostgreSQL async URL (env: DB_URL or DATABASE_URL)",
    )
    database_url_sync: str = Field(
        default="postgresql://seo:seo@localhost:5432/seo_agent",
        description="PostgreSQL sync URL (alembic, RQ workers)",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL (env: REDIS_URL)")

    # Rate limiting
    daily_token_quota: int = Field(default=100_000, description="Max tokens per day (env or settings)")

    # Optional API keys (stubs work without them)
    serp_api_key: str | None = Field(default=None, description="SERP API key (env: SERP_API_KEY)")
    llm_api_key: str | None = Field(default=None, description="LLM API key (env: LLM_API_KEY)")
    anti_plagiat_api_key: str | None = Field(default=None, description="Anti-plagiarism API (env: ANTI_PLAGIAT_API_KEY)")
    tilda_public_key: str | None = Field(default=None, description="Tilda public key (env: TILDA_PUBLIC_KEY)")
    tilda_secret_key: str | None = Field(default=None, description="Tilda secret key (env: TILDA_SECRET_KEY)")
    tilda_project_id: str | None = Field(default=None, description="Tilda project ID (env: TILDA_PROJECT_ID)")

    # Service URLs (for orchestrator calling other services)
    serp_intel_url: str = Field(default="http://serp-intel:8000", description="SERP Intel service")
    content_gen_url: str = Field(default="http://content-gen:8000", description="Content Gen service")
    seo_optimizer_url: str = Field(default="http://seo-optimizer:8000", description="SEO Optimizer service")
    quality_gate_url: str = Field(default="http://quality-gate:8000", description="Quality Gate service")
    publisher_tilda_url: str = Field(default="http://publisher-tilda:8000", description="Publisher Tilda service")
    indexer_url: str = Field(default="http://indexer:8000", description="Indexer service")
    analytics_tracker_url: str = Field(default="http://analytics-tracker:8000", description="Analytics Tracker service")
    linkbuilding_url: str = Field(default="http://linkbuilding:8000", description="Linkbuilding service")
    cases_gen_url: str = Field(default="http://cases-gen:8000", description="Cases Gen service")


@lru_cache
def get_settings() -> Settings:
    return Settings()
