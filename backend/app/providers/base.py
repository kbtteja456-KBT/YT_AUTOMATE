"""Base provider abstractions and Zero-Cost Mode enforcement."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from backend.app.core.errors import ZeroCostModeViolationError
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.models.video import CaptionSegment, ResearchItem, Scene
from backend.app.models.thumbnail import ThumbnailCard, ThumbnailSpec


class BaseProvider(ABC):
    """Abstract base class for all provider subsystems."""

    name: str = "base_provider"
    provider_type: ProviderType
    is_zero_cost: bool = True
    is_paid: bool = False

    def verify_zero_cost_compliance(
        self,
        zero_cost_mode: bool = True,
        paid_providers_enabled: bool = False,
        allowed_paid_providers: Optional[list[str]] = None
    ) -> None:
        """Enforces hard Zero-Cost Mode gate before any provider invocation."""
        if self.is_paid:
            if zero_cost_mode:
                raise ZeroCostModeViolationError(
                    f"Paid provider blocked by Zero-Cost Mode. Provider '{self.name}' cannot be used."
                )
            if not paid_providers_enabled:
                raise ZeroCostModeViolationError(
                    f"Paid provider '{self.name}' requested but paid providers are not enabled in Settings."
                )
            if allowed_paid_providers and self.name not in allowed_paid_providers:
                raise ZeroCostModeViolationError(
                    f"Paid provider '{self.name}' is not in allowed paid providers list."
                )

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Perform real connection/availability check. Never simulate."""
        pass


class AIProvider(BaseProvider):
    """Abstract interface for LLM text reasoning and structured JSON output."""
    provider_type = ProviderType.AI

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> str:
        """Generate unstructured text response."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.5
    ) -> dict[str, Any]:
        """Generate guaranteed JSON output validated against response_schema with recovery."""
        pass


class TTSProvider(BaseProvider):
    """Abstract interface for Text-to-Speech synthesis."""
    provider_type = ProviderType.TTS

    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        output_filepath: str,
        voice_id: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> str:
        """Synthesize narration audio file (.wav or .mp3) and return absolute path."""
        pass

    @abstractmethod
    async def get_available_voices(self) -> list[dict[str, Any]]:
        """List real available voices from engine."""
        pass


class STTProvider(BaseProvider):
    """Abstract interface for Speech-to-Text transcription with word-level timestamps."""
    provider_type = ProviderType.STT

    @abstractmethod
    async def transcribe_audio(self, audio_filepath: str) -> list[CaptionSegment]:
        """Extract word-level and sentence-level timestamps from audio."""
        pass


class StockMediaProvider(BaseProvider):
    """Abstract interface for acquiring licensed/free visual assets."""
    provider_type = ProviderType.STOCK_MEDIA

    @abstractmethod
    async def search_and_acquire(
        self,
        query: str,
        duration_sec: float,
        target_dir: str,
        visual_type: str = "motion_graphic"
    ) -> Scene:
        """Find or generate valid visual scene asset with license metadata."""
        pass


class SearchProvider(BaseProvider):
    """Abstract interface for web research and factual grounding."""
    provider_type = ProviderType.SEARCH

    @abstractmethod
    async def search_topic_facts(self, topic: str, max_results: int = 5) -> list[ResearchItem]:
        """Fetch verifiable facts with source citations."""
        pass


class StorageProvider(BaseProvider):
    """Abstract interface for disk storage management."""
    provider_type = ProviderType.STORAGE

    @abstractmethod
    def get_path(self, category: str, filename: str) -> str:
        """Get absolute path for given category (temp, media, audio, captions, rendered)."""
        pass

    @abstractmethod
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """Clean up orphaned temporary render artifacts."""
        pass


class YouTubeProvider(BaseProvider):
    """Abstract interface for YouTube Data API v3 and Analytics API."""
    provider_type = ProviderType.YOUTUBE

    @abstractmethod
    async def get_channel_info(self, channel_id: Optional[str] = None) -> dict[str, Any]:
        """Retrieve real channel statistics from YouTube Data API."""
        pass

    @abstractmethod
    async def upload_short(
        self,
        video_filepath: str,
        title: str,
        description: str,
        tags: list[str],
        privacy_status: str = "public"
    ) -> dict[str, Any]:
        """Upload video via resumable upload and return YouTube video ID."""
        pass

    @abstractmethod
    async def get_video_analytics(self, youtube_video_id: str) -> dict[str, Any]:
        """Query real analytics metrics for a published video."""
        pass


class ThumbnailProvider(BaseProvider):
    """Abstract interface for generating custom high-CTR thumbnail cards."""
    provider_type = ProviderType.THUMBNAIL

    @abstractmethod
    async def generate_thumbnail(
        self,
        video_filepath: str,
        spec: ThumbnailSpec,
        output_filepath: str
    ) -> ThumbnailCard:
        """Extract frame, apply color enhancements and text overlays."""
        pass
