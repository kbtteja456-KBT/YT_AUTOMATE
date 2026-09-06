"""Unit tests for encryption key safety and real royalty-free music pool provider."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.core.security import get_encryption_key, encrypt_token, decrypt_token, MISSING_ENCRYPTION_KEY_ERROR
from backend.app.models.provider import ProviderStatus, ProviderType
from backend.app.providers.music.pixabay_music import PixabayMusicProvider, CURATED_ROYALTY_FREE_TRACKS
from backend.app.agents.voice import VoiceAgent
from backend.app.providers.storage.local_storage import LocalStorageProvider
from backend.app.main import app


def test_encryption_key_missing_fails_loudly():
    """Verify that get_encryption_key raises RuntimeError and never silently regenerates."""
    with patch.object(settings, "encryption_key", ""):
        with patch.dict(os.environ, {"ENCRYPTION_KEY": ""}):
            with pytest.raises(RuntimeError) as exc_info:
                get_encryption_key()
            assert "ENCRYPTION_KEY is not set" in str(exc_info.value)
            assert "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"" in str(exc_info.value)


def test_app_lifespan_refuses_startup_without_encryption_key():
    """Verify that FastAPI lifespan crashes and refuses startup when ENCRYPTION_KEY is unset."""
    with patch.object(settings, "encryption_key", ""):
        with patch.dict(os.environ, {"ENCRYPTION_KEY": ""}):
            with pytest.raises(RuntimeError) as exc_info:
                with TestClient(app):
                    pass
            assert "ENCRYPTION_KEY is not set" in str(exc_info.value)


@pytest.mark.anyio
async def test_pixabay_music_provider_not_configured_when_key_empty():
    """Verify health and populate_pool behavior when PIXABAY_API_KEY is empty."""
    provider = PixabayMusicProvider(api_key="")
    health = await provider.check_health()
    assert health.status == ProviderStatus.NOT_CONFIGURED
    assert "PIXABAY_API_KEY is not configured" in (health.error_message or "")

    with patch.object(settings, "pixabay_api_key", ""):
        tracks = await provider.populate_pool(target_dir=Path("./media_storage/audio/music_pool_test"))
        assert tracks == []


@pytest.mark.anyio
async def test_pixabay_music_provider_populates_real_tracks(tmp_path):
    """Verify populate_pool downloads real tracks and records them in MongoDB media_assets."""
    provider = PixabayMusicProvider(api_key="test_pixabay_key")
    test_pool = tmp_path / "music_pool"
    
    mock_db = MagicMock()
    with patch("backend.app.providers.music.pixabay_music.SyncMongoDB.get_db", return_value=mock_db):
        tracks = await provider.populate_pool(target_dir=test_pool, min_tracks=2)
        assert len(tracks) >= 2
        for t in tracks:
            assert Path(t["local_path"]).exists()
            assert t["license"] != ""
            assert t["source_url"].startswith("http")
        assert mock_db.media_assets.update_one.called


@pytest.mark.anyio
async def test_voice_agent_rotates_distinct_tracks(tmp_path):
    """Verify VoiceAgent rotates across distinct tracks in the music pool."""
    pool_dir = tmp_path / "audio" / "music_pool"
    pool_dir.mkdir(parents=True, exist_ok=True)

    # Copy at least 2 real tracks into test pool
    real_pool = Path("./media_storage/audio/music_pool")
    real_files = list(real_pool.glob("*.mp3"))
    assert len(real_files) >= 2, "Real music pool should have been pre-populated"

    (pool_dir / "track_a.mp3").write_bytes(real_files[0].read_bytes())
    (pool_dir / "track_b.mp3").write_bytes(real_files[1].read_bytes())

    storage = LocalStorageProvider(base_dir=str(tmp_path))
    dummy_tts = MagicMock()
    agent = VoiceAgent(tts_provider=dummy_tts, storage_provider=storage)

    out1 = str(tmp_path / "out1.mp3")
    out2 = str(tmp_path / "out2.mp3")

    res1 = await agent._select_and_normalize_bg_music(5.0, out1, "job1")
    res2 = await agent._select_and_normalize_bg_music(5.0, out2, "job2")

    assert Path(res1).exists()
    assert Path(res2).exists()
