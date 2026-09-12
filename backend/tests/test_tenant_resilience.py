"""Targeted unit tests verifying tenant publishing resilience and error prevention."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from backend.app.agents.research import FactCheckAgent
from backend.app.models.video import ResearchReport, ResearchItem
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider
from backend.app.core.errors import YouTubeAPIError
from backend.app.core.cron_scheduler import reconcile_stuck_in_progress_jobs
from backend.app.models.job import JobState
from google.auth.exceptions import RefreshError


class DummyAI:
    pass


@pytest.mark.anyio
async def test_fact_check_agent_informational_content_without_syntax_error():
    """Verify that general/documentary and non-code items do NOT get passed to python ast.parse."""
    agent = FactCheckAgent(ai_provider=DummyAI())
    report = ResearchReport(
        topic="An informational video about tech and latest AI news",
        niche="AI & Productivity",
        content_format="general",
        items=[
            ResearchItem(
                fact="Artificial intelligence tools are transforming developer workflows worldwide.",
                source="Tech Radar",
                interpretation="Adoption is speeding up.",
                verified=False
            )
        ],
        key_takeaway="AI tools are transforming workflows",
        question_code=None
    )

    verified = await agent.verify_and_prune(report)
    assert verified.verified_output == "Verified Information"
    assert verified.items[0].verified is True


@pytest.mark.anyio
async def test_fact_check_agent_self_heals_syntax_error_snippet():
    """Verify that an AI-generated quiz snippet with syntax error self-heals from the curated pool instead of crashing."""
    agent = FactCheckAgent(ai_provider=DummyAI())
    report = ResearchReport(
        topic="Python Syntax Test",
        niche="Python Programming",
        content_format="quiz_card",
        question_code="def broken(x: invalid syntax here !!!",
        options=["A) 1", "B) [1, 2, 3]", "C) 3", "D) Error"],
        correct_option="B",
        explanation="Self heal test."
    )

    verified = await agent.verify_and_prune(report)
    assert verified.correct_option is not None
    assert verified.verified_output is not None


def test_sanitize_youtube_text():
    """Verify that angle brackets (< and >) and backticks are cleaned so YouTube v3 does not reject them."""
    raw = "Here is C code:\n```c\n#include <stdio.h>\n```\nCheck it out <here>!"
    cleaned = YouTubeClientProvider.sanitize_youtube_text(raw)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "```" not in cleaned
    assert "[stdio.h]" in cleaned
    assert "[here]" in cleaned


def test_reconcile_stuck_jobs_refunds_quota():
    """Verify that reconcile_stuck_in_progress_jobs marks stale jobs FAILED and refunds quota."""
    mock_db = MagicMock()
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=30)
    fake_job = {
        "_id": ObjectId(),
        "state": JobState.SCRIPTING.value,
        "workspace_id": "fake_ws_123",
        "updated_at": old_time
    }
    mock_db.publishing_jobs.find.return_value = [fake_job]
    mock_db.videos.find_one.return_value = None  # No rendered file on disk

    with patch("backend.app.core.db.SyncMongoDB.get_db", return_value=mock_db), \
         patch("backend.app.core.ledger.refund_trial_quota_atomic_sync") as mock_refund:
        reconcile_stuck_in_progress_jobs()

        mock_db.publishing_jobs.update_one.assert_called_once()
        mock_refund.assert_called_once_with("fake_ws_123")


@pytest.mark.anyio
async def test_youtube_upload_expired_token_handling():
    """Verify that RefreshError during upload raises a clean YouTubeAPIError."""
    provider = YouTubeClientProvider(credentials=MagicMock())
    mock_service = MagicMock()
    mock_insert = MagicMock()
    mock_insert.next_chunk.side_effect = RefreshError("invalid_grant: Token has been expired or revoked.")
    mock_service.videos.return_value.insert.return_value = mock_insert
    provider._service = mock_service

    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.resolve", return_value=MagicMock(exists=lambda: True, name="test.mp4")), \
         patch("backend.app.providers.youtube.youtube_client.compute_file_hash", return_value="abc1234"), \
         patch("backend.app.providers.youtube.youtube_client.MediaFileUpload"):
        with pytest.raises(YouTubeAPIError) as exc_info:
            await provider.upload_short(
                video_filepath="test.mp4",
                title="Test Video",
                description="Test Description",
                tags=["Shorts"]
            )
        assert "token expired or revoked" in str(exc_info.value).lower()


def test_java_programming_niche_detection():
    """Verify that 'java  Programming' (with double spaces) strictly maps to code_quiz with Java profile."""
    from backend.app.core.language_detector import detect_content_archetype, detect_language_from_niche
    arch = detect_content_archetype("java  Programming")
    assert arch.archetype == "code_quiz"
    assert arch.header_title == "JAVA QUIZ"
    assert arch.default_hashtag == "#java"

    lang_prof = detect_language_from_niche("java  Programming")
    assert lang_prof.slug == "java"
    assert lang_prof.header_badge == "JAVA QUIZ"

