"""Real unit tests for Phase 7: Full provider abstraction layer."""

import pytest
import os
from pathlib import Path
from PIL import Image
from unittest.mock import MagicMock, patch

from backend.app.providers.storage.local_storage import LocalStorageProvider
from backend.app.providers.search.ddg_search import DuckDuckGoSearchProvider
from backend.app.providers.tts.edge_tts_provider import EdgeTTSProvider
from backend.app.providers.tts.pyttsx3_provider import PyTTSx3Provider
from backend.app.providers.stt.whisper_provider import WhisperProvider
from backend.app.providers.media.stock_media import StockMediaEngine
from backend.app.providers.thumbnail.thumbnail_engine import ThumbnailEngine
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider
from backend.app.models.thumbnail import ThumbnailSpec
from backend.app.models.provider import ProviderStatus


def test_local_storage_provider(tmp_path):
    """Verify storage provider directory structure and path mapping."""
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    audio_file = storage.get_path("audio", "speech_01.mp3")
    assert "audio" in audio_file
    assert Path(audio_file).parent.exists()

    rendered_file = storage.get_path("rendered", "short_final.mp4")
    assert "rendered" in rendered_file


@pytest.mark.anyio
async def test_search_provider_fact_discovery():
    """Verify DuckDuckGo and Wikipedia search provides factual items with citations."""
    provider = DuckDuckGoSearchProvider()
    results = await provider.search_topic_facts("Artificial Intelligence", max_results=3)
    assert len(results) >= 1
    for item in results:
        assert item.fact != ""
        assert item.source != ""
        assert item.verified is True


@pytest.mark.anyio
async def test_edge_tts_speech_synthesis(tmp_path):
    """Verify Edge TTS synthesizes speech file with genuine audio bytes."""
    tts = EdgeTTSProvider()
    voices = await tts.get_available_voices()
    assert len(voices) > 0
    assert any(v["voice_id"] == "en-US-ChristopherNeural" for v in voices)

    output_file = str(tmp_path / "test_narration.mp3")
    result_path = await tts.synthesize_speech(
        text="Welcome to the AI YouTube Shorts Autopilot. Zero-cost automated creation.",
        output_filepath=output_file,
        voice_id="en-US-ChristopherNeural"
    )

    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 5000  # Genuine audio file with non-trivial size


@pytest.mark.anyio
async def test_stock_media_procedural_card_generator(tmp_path):
    """Verify procedural motion graphics generates real 1080x1920 vertical card."""
    engine = StockMediaEngine(media_dir=str(tmp_path / "assets"))
    scene = await engine.search_and_acquire(
        query="5 Breakthrough AI Tools Every Student Must Know",
        duration_sec=3.0,
        target_dir=str(tmp_path / "scenes")
    )

    assert scene.asset_local_path is not None
    assert Path(scene.asset_local_path).exists()

    # Verify real image dimensions are exactly 1080x1920
    with Image.open(scene.asset_local_path) as img:
        assert img.width == 1080
        assert img.height == 1920


@pytest.mark.anyio
async def test_thumbnail_engine_card_generation(tmp_path):
    """Verify custom high-CTR thumbnail card generator produces 1080x1920 output."""
    engine = ThumbnailEngine()
    spec = ThumbnailSpec(
        source_frame_timestamp=1.5,
        overlay_text="5 INSANE AI TOOLS",
        output_width=1080,
        output_height=1920
    )

    out_file = str(tmp_path / "thumb_001.jpg")
    card = await engine.generate_thumbnail(
        video_filepath="nonexistent_mock_video.mp4",
        spec=spec,
        output_filepath=out_file
    )

    assert Path(card.file_path).exists()
    assert len(card.file_hash) == 64

    # Verify dimensions
    with Image.open(card.file_path) as img:
        assert img.width == 1080
        assert img.height == 1920


@pytest.mark.anyio
async def test_youtube_client_analytics_not_available_handling():
    """Verify YouTube client returns NOT AVAILABLE when metrics are missing."""
    mock_service = MagicMock()
    mock_service.videos().list().execute.return_value = {"items": []}

    yt = YouTubeClientProvider(credentials=MagicMock())
    yt._service = mock_service

    analytics = await yt.get_video_analytics("mock_video_id_123")
    assert analytics["views"] == "NOT AVAILABLE"
    assert analytics["likes"] == "NOT AVAILABLE"
