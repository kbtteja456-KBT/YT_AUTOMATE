"""Real unit tests for Phase 17: Title, Description, Thumbnail, and YouTube publishing."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from backend.app.agents.title import TitleAgent, DescriptionAgent
from backend.app.agents.thumbnail import ThumbnailAgent
from backend.app.agents.youtube import YouTubeAgent
from backend.app.models.video import Script
from backend.app.models.thumbnail import ThumbnailCard, ThumbnailSpec
from backend.app.core.errors import DuplicateUploadPreventedError
from backend.app.providers.storage.local_storage import LocalStorageProvider


@pytest.mark.anyio
async def test_title_and_description_agents():
    """Verify TitleAgent and DescriptionAgent format high-CTR metadata."""
    mock_ai = MagicMock()
    mock_ai.generate_structured = AsyncMock(return_value={
        "title": "5 Secret AI Tools for Students (Save 10 Hours)",
        "hashtags": ["#Shorts", "#AI", "#Productivity"],
        "tags": ["AI Tools", "Students", "Homework", "Productivity"]
    })

    title_agent = TitleAgent(ai_provider=mock_ai)
    script = Script(
        topic="5 Secret AI Tools",
        hook="Stop scrolling.",
        problem="Research is hard.",
        value="These tools automate everything.",
        payoff="Done in seconds.",
        cta="Follow for more.",
        full_narration="Full text.",
        target_duration_sec=45.0
    )

    meta = await title_agent.generate_title_and_tags(script)
    assert meta["title"] == "5 Secret AI Tools for Students (Save 10 Hours)"
    assert len(meta["title"]) < 60
    assert len(meta["hashtags"]) == 3

    desc_agent = DescriptionAgent(ai_provider=mock_ai)
    desc = await desc_agent.generate_description(script, meta["title"], meta["hashtags"])
    assert meta["title"] in desc
    assert "#Shorts" in desc


@pytest.mark.anyio
async def test_thumbnail_agent_custom_overlay(tmp_path):
    """Verify ThumbnailAgent produces custom high-CTR card rather than auto-frame."""
    storage = LocalStorageProvider(base_dir=str(tmp_path))
    mock_ai = MagicMock()
    mock_ai.generate_structured = AsyncMock(return_value={"overlay_text": "DON'T MISS THIS"})

    mock_engine = MagicMock()
    spec_expected = ThumbnailSpec(source_frame_timestamp=2.0, overlay_text="DON'T MISS THIS")
    card_expected = ThumbnailCard(
        file_path=str(tmp_path / "thumbnails" / "thumb_job_99.jpg"),
        file_hash="sha256_mock_hash",
        spec=spec_expected
    )
    mock_engine.generate_thumbnail = AsyncMock(return_value=card_expected)

    agent = ThumbnailAgent(
        ai_provider=mock_ai,
        thumbnail_provider=mock_engine,
        storage_provider=storage
    )

    script = Script(
        topic="5 Secret AI Tools",
        hook="Stop scrolling right now.",
        problem="Don't waste time.",
        value="Use these tools.",
        payoff="Done.",
        cta="Follow.",
        full_narration="Full narration text."
    )

    card = await agent.generate_custom_thumbnail("mock_video.mp4", script, job_id="job_99")
    assert card.spec.overlay_text == "DON'T MISS THIS"
    assert "thumb_job_99" in card.file_path


@pytest.mark.anyio
async def test_youtube_agent_duplicate_prevention(tmp_path):
    """Verify YouTubeAgent blocks duplicate uploads matching an existing content hash."""
    test_video = tmp_path / "duplicate_test.mp4"
    test_video.write_bytes(b"dummy video data 12345")

    from backend.app.core.security import compute_file_hash
    video_hash = compute_file_hash(str(test_video))

    mock_yt_provider = MagicMock()
    agent = YouTubeAgent(youtube_provider=mock_yt_provider)

    # Already existing hashes contains video_hash
    with pytest.raises(DuplicateUploadPreventedError) as exc_info:
        await agent.publish_short(
            video_filepath=str(test_video),
            title="Duplicate Title",
            description="Description",
            tags=["AI"],
            existing_hashes=[video_hash]
        )
    assert "Duplicate upload blocked" in str(exc_info.value)
