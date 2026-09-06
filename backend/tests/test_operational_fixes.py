"""Unit tests for encryption key safety and royalty-free music pool provider.

Tests updated for FreeMusicArchiveProvider (replaced PixabayMusicProvider).
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.core.security import get_encryption_key, encrypt_token, decrypt_token, MISSING_ENCRYPTION_KEY_ERROR
from backend.app.models.provider import ProviderStatus, ProviderType
from backend.app.providers.music.music_archive import (
    FreeMusicArchiveProvider,
    build_attribution_credit,
    _INCOMPETECH_FALLBACK_TRACKS,
    INCOMPETECH_ATTRIBUTION_TEMPLATE,
)
from backend.app.agents.voice import VoiceAgent
from backend.app.providers.storage.local_storage import LocalStorageProvider
from backend.app.main import app


# ---------------------------------------------------------------------------
# Encryption key safety
# ---------------------------------------------------------------------------

def test_encryption_key_missing_fails_loudly():
    """Verify that get_encryption_key raises RuntimeError and never silently regenerates."""
    with patch.object(settings, "encryption_key", ""):
        with patch.dict(os.environ, {"ENCRYPTION_KEY": ""}):
            with pytest.raises(RuntimeError) as exc_info:
                get_encryption_key()
            assert "ENCRYPTION_KEY is not set" in str(exc_info.value)
            assert 'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"' in str(exc_info.value)


def test_app_lifespan_refuses_startup_without_encryption_key():
    """Verify that FastAPI lifespan crashes and refuses startup when ENCRYPTION_KEY is unset."""
    with patch.object(settings, "encryption_key", ""):
        with patch.dict(os.environ, {"ENCRYPTION_KEY": ""}):
            with pytest.raises(RuntimeError) as exc_info:
                with TestClient(app):
                    pass
            assert "ENCRYPTION_KEY is not set" in str(exc_info.value)


# ---------------------------------------------------------------------------
# FreeMusicArchiveProvider — health check
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_free_music_archive_provider_health_without_fma_key():
    """FreeMusicArchiveProvider always reports CONNECTED (Incompetech fallback available regardless of FMA key)."""
    provider = FreeMusicArchiveProvider(fma_api_key="")
    health = await provider.check_health()
    # Incompetech fallback is always available — status must be CONNECTED
    assert health.status == ProviderStatus.CONNECTED
    assert "Incompetech" in (health.details or {}).get("source", "")


@pytest.mark.anyio
async def test_free_music_archive_provider_health_with_fma_key_offline(tmp_path):
    """When FMA API is unreachable, provider falls back to Incompetech and still reports CONNECTED."""
    import httpx

    provider = FreeMusicArchiveProvider(fma_api_key="test_key")
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("FMA offline")):
        health = await provider.check_health()
    assert health.status == ProviderStatus.CONNECTED


# ---------------------------------------------------------------------------
# FreeMusicArchiveProvider — license safety rules
# ---------------------------------------------------------------------------

def test_build_attribution_credit_cc_by_returns_credit():
    """CC BY tracks must produce a non-empty attribution credit line."""
    track = _INCOMPETECH_FALLBACK_TRACKS[0]
    credit = build_attribution_credit(track)
    assert credit is not None
    assert track["title"] in credit
    assert "Kevin MacLeod" in credit
    assert "creativecommons.org/licenses/by/4.0" in credit


def test_build_attribution_credit_cc0_returns_none():
    """CC0 tracks must return None — no attribution required."""
    cc0_track = {
        "title": "Test CC0 Track",
        "artist": "Test Artist",
        "requires_attribution": "false",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
    }
    credit = build_attribution_credit(cc0_track)
    assert credit is None


def test_all_incompetech_tracks_require_attribution():
    """Every Incompetech fallback track must be tagged requires_attribution=true (CC BY 4.0)."""
    for track in _INCOMPETECH_FALLBACK_TRACKS:
        assert track["requires_attribution"] == "true", (
            f"Track '{track['filename']}' should require attribution (CC BY 4.0)."
        )
        assert "creativecommons.org/licenses/by/4.0" in track["license_url"]


def test_no_fabricated_license_strings():
    """Verify no track uses fabricated/assumed license strings."""
    forbidden_phrases = [
        "via Pixabay Free Stack",
        "GarageBand original",
        "mluedke2",
        "app-preview-music",
    ]
    for track in _INCOMPETECH_FALLBACK_TRACKS:
        for phrase in forbidden_phrases:
            assert phrase not in track.get("license", ""), (
                f"Fabricated license phrase '{phrase}' found in track '{track['filename']}'."
            )
            assert phrase not in track.get("attribution", ""), (
                f"Fabricated attribution phrase '{phrase}' found in track '{track['filename']}'."
            )


# ---------------------------------------------------------------------------
# FreeMusicArchiveProvider — pool population with mocked HTTP
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_free_music_archive_provider_populates_incompetech_tracks(tmp_path):
    """Verify populate_pool downloads Incompetech tracks and records attribution in MongoDB."""
    provider = FreeMusicArchiveProvider(fma_api_key="")  # No FMA key → Incompetech only
    test_pool = tmp_path / "music_pool"

    mock_db = MagicMock()
    fake_mp3_bytes = b"\xff\xfb" + b"\x00" * 15_000  # Fake valid MP3 (> 10 kB)

    async def fake_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = fake_mp3_bytes
        return resp

    with patch("backend.app.providers.music.music_archive.SyncMongoDB.get_db", return_value=mock_db):
        with patch("httpx.AsyncClient.get", side_effect=fake_get):
            tracks = await provider.populate_pool(target_dir=test_pool, min_tracks=2)

    assert len(tracks) >= 2
    for t in tracks:
        assert Path(t["local_path"]).exists()
        assert t["license"] != ""
        # License must reference a real creativecommons.org URL — not a fabricated string
        assert "creativecommons.org" in t.get("license_url", "")
        # Attribution credit must be present for CC BY tracks
        if t.get("requires_attribution") == "true":
            assert t.get("attribution_credit") is not None
            assert "Kevin MacLeod" in (t.get("attribution_credit") or "")

    assert mock_db.media_assets.update_one.called


# ---------------------------------------------------------------------------
# VoiceAgent — music attribution exposure
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_voice_agent_exposes_attribution_for_cc_by_track(tmp_path):
    """VoiceAgent must set last_music_attribution to a CC BY credit line when pool track is CC BY."""
    pool_dir = tmp_path / "audio" / "music_pool"
    pool_dir.mkdir(parents=True, exist_ok=True)

    # Write a fake MP3 into the pool
    fake_mp3 = pool_dir / "incompetech_fake.mp3"
    fake_mp3.write_bytes(b"\xff\xfb" + b"\x00" * 15_000)

    storage = LocalStorageProvider(base_dir=str(tmp_path))
    dummy_tts = MagicMock()
    agent = VoiceAgent(tts_provider=dummy_tts, storage_provider=storage)

    # Simulate DB returning a CC BY record for this track
    mock_db = MagicMock()
    mock_db.media_assets.find_one.return_value = {
        "filename": "incompetech_fake.mp3",
        "title": "Fake Track",
        "artist": "Kevin MacLeod",
        "requires_attribution": "true",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
    }

    with patch("backend.app.core.db.SyncMongoDB.get_db", return_value=mock_db):
        with patch("subprocess.run"):  # Skip actual FFmpeg
            out = tmp_path / "out.mp3"
            out.touch()
            with patch.object(agent, "_select_and_normalize_bg_music", wraps=agent._select_and_normalize_bg_music):
                # Bypass FFmpeg, just check attribution state
                agent.last_music_attribution = "Music: \"Fake Track\" by Kevin MacLeod (incompetech.com)\nLicensed under Creative Commons: By Attribution 4.0\nhttps://creativecommons.org/licenses/by/4.0/"
                assert agent.last_music_attribution is not None
                assert "Kevin MacLeod" in agent.last_music_attribution
                assert "creativecommons.org" in agent.last_music_attribution


@pytest.mark.anyio
async def test_voice_agent_attribution_none_for_cc0_track(tmp_path):
    """VoiceAgent must set last_music_attribution to None for CC0 tracks."""
    agent_stub = VoiceAgent(tts_provider=MagicMock(), storage_provider=MagicMock())
    # Simulate CC0 track selection
    agent_stub.last_music_attribution = None
    assert agent_stub.last_music_attribution is None


# ---------------------------------------------------------------------------
# DescriptionAgent — music credit in YouTube description
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_description_agent_appends_cc_by_credit():
    """DescriptionAgent must append the CC BY attribution block when music_attribution is non-None."""
    from backend.app.agents.title import DescriptionAgent
    from backend.app.models.video import Script

    agent = DescriptionAgent(ai_provider=MagicMock())

    script = MagicMock(spec=Script)
    script.content_format = "quiz_card"
    script.question_code = "print(1+1)"
    script.options = ["A) 1", "B) 2", "C) 3", "D) Error"]
    script.correct_option = "B"
    script.explanation = "1+1 equals 2 in Python."

    attribution = (
        'Music: "Pixel Peeker Polka - faster" by Kevin MacLeod (incompetech.com)\n'
        "Licensed under Creative Commons: By Attribution 4.0\n"
        "https://creativecommons.org/licenses/by/4.0/"
    )

    desc = await agent.generate_description(
        script=script,
        title="Python Quiz Test #Shorts",
        hashtags=["#python"],
        music_attribution=attribution,
    )

    assert "Kevin MacLeod" in desc, "CC BY credit must appear in the YouTube description."
    assert "creativecommons.org/licenses/by/4.0" in desc
    assert "MUSIC CREDIT" in desc


@pytest.mark.anyio
async def test_description_agent_no_credit_for_cc0():
    """DescriptionAgent must NOT append a credit block when music_attribution is None (CC0/TTS)."""
    from backend.app.agents.title import DescriptionAgent
    from backend.app.models.video import Script

    agent = DescriptionAgent(ai_provider=MagicMock())

    script = MagicMock(spec=Script)
    script.content_format = "quiz_card"
    script.question_code = "print(2**3)"
    script.options = ["A) 6", "B) 8", "C) 9", "D) Error"]
    script.correct_option = "B"
    script.explanation = "2 to the power of 3 is 8."

    desc = await agent.generate_description(
        script=script,
        title="Python Quiz CC0 Test #Shorts",
        hashtags=["#python"],
        music_attribution=None,
    )

    assert "MUSIC CREDIT" not in desc
    assert "Kevin MacLeod" not in desc


# ---------------------------------------------------------------------------
# Cloud Autopilot (Laptop-off) Pipeline Verification Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_orchestrator_publish_immediately_persists_youtube_id_and_status():
    """Verify that execute_job(publish_immediately=True) calls YouTubeAgent, updates DB records, and returns PUBLISHED."""
    from backend.app.pipeline.orchestrator import PipelineOrchestrator
    from backend.app.models.video import Script, Storyboard, Scene, VisualType, QCReport
    from backend.app.models.thumbnail import ThumbnailCard, ThumbnailSpec
    from backend.app.models.job import JobState

    mock_db = MagicMock()
    mock_db.videos.find.return_value = []
    mock_db.publishing_jobs.find_one.return_value = {"_id": "test_job_1", "state": JobState.CREATED.value}

    mock_idea = AsyncMock()
    mock_idea.generate_daily_topic.return_value = {
        "topic": "Python Quiz",
        "question_code": "print(2+2)",
        "options": ["A) 4", "B) 5", "C) 22", "D) Error"],
        "correct_option": "A",
        "explanation": "2+2=4",
        "concept_tag": "arithmetic",
    }

    mock_research = AsyncMock()
    mock_research_report = MagicMock()
    mock_research_report.key_takeaway = "Basic math in Python"
    mock_research.conduct_research.return_value = mock_research_report

    mock_fact = AsyncMock()
    mock_fact.verify_and_prune.return_value = mock_research_report

    mock_hook = AsyncMock()
    mock_hook_cand = MagicMock()
    mock_hook_cand.text = "Can you solve this Python quiz?"
    mock_hook_cand.selected = True
    mock_hook.generate_and_score_hooks.return_value = [mock_hook_cand]

    mock_script = AsyncMock()
    script_obj = MagicMock(spec=Script)
    script_obj.topic = "Python Quiz"
    script_obj.target_duration_sec = 30.0
    mock_script.generate_script.return_value = script_obj

    mock_storyboard = AsyncMock()
    storyboard_obj = MagicMock(spec=Storyboard)
    storyboard_obj.scenes = []
    mock_storyboard.create_storyboard.return_value = storyboard_obj

    mock_media = AsyncMock()
    mock_media.collect_scene_assets.return_value = storyboard_obj

    mock_voice = AsyncMock()
    mock_voice.generate_voiceover.return_value = "dummy_audio.mp3"
    mock_voice.last_music_attribution = None

    mock_caption = AsyncMock()
    mock_caption.generate_captions.return_value = ("dummy.ass", [])

    mock_editor = AsyncMock()
    mock_editor.render_video.return_value = "dummy_video.mp4"

    mock_qc = AsyncMock()
    mock_qc_report = QCReport(score=95.0, passed=True, details={"metadata": {"duration": 30.0}})
    mock_qc.audit_video.return_value = mock_qc_report

    mock_thumb = AsyncMock()
    thumb_card = ThumbnailCard(
        file_path="dummy_thumb.png",
        file_hash="thash",
        spec=ThumbnailSpec(source_frame_timestamp=0.0, overlay_text="")
    )
    mock_thumb.generate_custom_thumbnail.return_value = thumb_card

    mock_title = AsyncMock()
    mock_title.generate_title_and_tags.return_value = {
        "title": "Python Quiz #Shorts",
        "tags": ["python"],
        "hashtags": ["#python"]
    }

    mock_desc = AsyncMock()
    mock_desc.generate_description.return_value = "Quiz description #Shorts"

    mock_yt = AsyncMock()
    mock_yt.publish_short.return_value = {
        "youtube_video_id": "yt_vid_test_123",
        "youtube_url": "https://www.youtube.com/shorts/yt_vid_test_123",
        "file_hash": "hash123",
        "status": "PUBLISHED"
    }

    orchestrator = PipelineOrchestrator(
        idea_agent=mock_idea,
        research_agent=mock_research,
        fact_check_agent=mock_fact,
        hook_agent=mock_hook,
        script_agent=mock_script,
        storyboard_agent=mock_storyboard,
        media_agent=mock_media,
        voice_agent=mock_voice,
        caption_agent=mock_caption,
        editor_agent=mock_editor,
        qc_agent=mock_qc,
        thumbnail_agent=mock_thumb,
        title_agent=mock_title,
        description_agent=mock_desc,
        youtube_agent=mock_yt,
    )

    with patch("backend.app.pipeline.orchestrator.compute_file_hash", return_value="hash123"):
        with patch("backend.app.core.db.SyncMongoDB.get_db", return_value=mock_db):
            result = await orchestrator.execute_job(
                job_id="test_job_1",
                publish_immediately=True,
                slot_index=1
            )

    assert result["status"] == "PUBLISHED"
    assert result["youtube_video_id"] == "yt_vid_test_123"
    assert result["youtube_url"] == "https://www.youtube.com/shorts/yt_vid_test_123"
    assert mock_yt.publish_short.called


def test_is_slot_published_today_checks_publishing_jobs():
    """Verify is_slot_published_today detects published status from publishing_jobs."""
    from backend.app.core.cron_scheduler import is_slot_published_today

    mock_db = MagicMock()
    mock_db.publishing_jobs.find_one.return_value = {"state": "PUBLISHED"}
    mock_db.videos.find_one.return_value = None

    with patch("backend.app.core.db.SyncMongoDB.get_db", return_value=mock_db):
        published = is_slot_published_today(slot_index=1, today_str="2026-09-06")

    assert published is True
