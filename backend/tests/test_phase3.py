"""Real tests for Phase 3: MongoDB integration, repositories, and persistence."""

import pytest
from datetime import datetime, timezone
from mongomock_motor import AsyncMongoMockClient

from backend.app.models.job import PublishingJob, JobState, JobStageLog
from backend.app.models.video import Video
from backend.app.models.settings import ChannelSettings
from backend.app.models.activity import ActivityEvent
from backend.app.models.style_profile import StyleProfile
from backend.app.core.repositories import (
    JobRepository, VideoRepository, SettingsRepository,
    ActivityRepository, StyleProfileRepository
)


@pytest.fixture
def mock_db():
    """Create isolated in-memory Async Mongo database for real repository testing."""
    client = AsyncMongoMockClient()
    return client["test_youtube_autopilot"]


@pytest.mark.anyio
async def test_job_repository_crud_and_state(mock_db):
    """Test full PublishingJob lifecycle in MongoDB."""
    repo = JobRepository(mock_db)

    scheduled = datetime(2026, 9, 4, 7, 0, tzinfo=timezone.utc)
    job = PublishingJob(
        slot_index=1,
        scheduled_at=scheduled,
        idempotency_key="idemp_test_phase3_001",
        state=JobState.CREATED
    )

    # 1. Insert
    saved = await repo.create_job(job)
    assert saved.id is not None

    # 2. Fetch by ID
    fetched = await repo.get_job_by_id(saved.id)
    assert fetched is not None
    assert fetched.idempotency_key == "idemp_test_phase3_001"
    assert fetched.state == JobState.CREATED

    # 3. Fetch by Idempotency Key
    by_key = await repo.get_job_by_idempotency_key("idemp_test_phase3_001")
    assert by_key is not None
    assert by_key.id == saved.id

    # 4. Update State to RESEARCHING
    await repo.update_job_state(saved.id, JobState.RESEARCHING)
    updated = await repo.get_job_by_id(saved.id)
    assert updated.state == JobState.RESEARCHING

    # 5. Append Stage Log
    log = JobStageLog(
        stage=JobState.RESEARCHING,
        started_at=datetime.now(timezone.utc),
        status="COMPLETED",
        duration_ms=520
    )
    await repo.append_stage_log(saved.id, log)
    with_logs = await repo.get_job_by_id(saved.id)
    assert len(with_logs.stage_logs) == 1
    assert with_logs.last_completed_stage == JobState.RESEARCHING

    # 6. In-progress jobs query
    in_progress = await repo.get_in_progress_jobs()
    assert len(in_progress) == 1
    assert in_progress[0].id == saved.id


@pytest.mark.anyio
async def test_video_repository_and_hash_deduplication(mock_db):
    """Test Video creation and SHA-256 hash deduplication lookup."""
    repo = VideoRepository(mock_db)

    video = Video(
        title="5 AI Tools Every Student Must Know",
        description="Save hours on assignments.",
        file_hash="sha256_mock_video_hash_999",
        duration_seconds=44.2,
        quality_score=94.0
    )

    created = await repo.create_video(video)
    assert created.id is not None

    # Look up by hash
    found = await repo.get_video_by_hash("sha256_mock_video_hash_999")
    assert found is not None
    assert found.title == "5 AI Tools Every Student Must Know"

    # List recent
    all_videos = await repo.list_recent_videos()
    assert len(all_videos) == 1


@pytest.mark.anyio
async def test_settings_repository(mock_db):
    """Test ChannelSettings retrieval, default seeding, and updating."""
    repo = SettingsRepository(mock_db)

    # First fetch should seed defaults
    current = await repo.get_settings()
    assert current.zero_cost_mode is True
    assert current.schedule.daily_video_limit == 2

    # Update niche
    current.niche = "Deep Learning & Robotics"
    await repo.save_settings(current)

    reloaded = await repo.get_settings()
    assert reloaded.niche == "Deep Learning & Robotics"


@pytest.mark.anyio
async def test_activity_repository_feed(mock_db):
    """Test logging ActivityEvent and retrieving sorted feed."""
    repo = ActivityRepository(mock_db)

    ev1 = ActivityEvent(
        event_type="SCRIPT_GENERATED",
        level="INFO",
        agent_name="ScriptAgent",
        message="Narration script drafted successfully.",
        timestamp=datetime(2026, 9, 4, 10, 0, 0, tzinfo=timezone.utc)
    )
    ev2 = ActivityEvent(
        event_type="QC_PASSED",
        level="SUCCESS",
        agent_name="QCAgent",
        message="Quality score: 95/100. Video approved.",
        timestamp=datetime(2026, 9, 4, 10, 0, 5, tzinfo=timezone.utc)
    )

    await repo.log_event(ev1)
    await repo.log_event(ev2)

    events = await repo.get_recent_events()
    assert len(events) == 2
    assert events[0].event_type == "QC_PASSED"  # latest first


@pytest.mark.anyio
async def test_style_profile_repository(mock_db):
    """Test StyleProfile active blueprint persistence."""
    repo = StyleProfileRepository(mock_db)

    profile = await repo.get_active_profile()
    assert profile.real_footage_ratio == 0.28
    assert profile.screen_recording_ratio == 0.72

    profile.cut_frequency_sec = 1.9
    await repo.save_profile(profile)

    updated = await repo.get_active_profile()
    assert updated.cut_frequency_sec == 1.9
