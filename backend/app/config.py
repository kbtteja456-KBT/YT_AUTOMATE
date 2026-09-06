"""Application configuration management with Pydantic settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices


class Settings(BaseSettings):
    """Runtime configuration for AI YouTube Shorts Autopilot."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database & Message Broker
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("MONGODB_URI", "MONGO_URI", "mongodb_uri")
    )
    mongodb_db_name: str = Field(default="youtube_autopilot")
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Cron / Webhook Secret for Cloud Schedulers
    autopilot_cron_secret: str = Field(
        default="",
        validation_alias=AliasChoices("AUTOPILOT_CRON_SECRET", "autopilot_cron_secret")
    )

    # Zero-Cost Hard Mode
    zero_cost_mode: bool = Field(default=True, description="Strictly block any paid provider calls")
    paid_providers_enabled: bool = Field(default=False)

    # OpenRouter Free Tier
    openrouter_api_key: str = Field(default="")
    openrouter_model: str = Field(default="meta-llama/llama-3.3-70b-instruct:free")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")

    # Google / YouTube OAuth 2.0
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    youtube_redirect_uri: str = Field(default="http://localhost:8000/api/auth/youtube/callback")

    # Stock Media APIs (Free Tiers)
    pexels_api_key: str = Field(default="")
    pixabay_api_key: str = Field(default="")
    fma_api_key: str = Field(default="", validation_alias=AliasChoices("FMA_API_KEY", "fma_api_key"))

    # Security
    encryption_key: str = Field(default="")

    # Schedule & Location
    timezone: str = Field(default="Asia/Kolkata")
    daily_video_limit: int = Field(default=2)

    # Local Storage Paths
    media_storage_dir: str = Field(default="./media_storage")
    temp_dir: str = Field(default="./media_storage/temp")

    @property
    def storage_path(self) -> Path:
        p = Path(self.media_storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def temp_path(self) -> Path:
        p = Path(self.temp_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
