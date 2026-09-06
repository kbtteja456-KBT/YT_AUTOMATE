"""Real unit tests for Phase 4: Redis, Celery tasks, and Celery Beat schedules."""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import mongomock

from backend.app.celery_app.celery import celery_app
from backend.app.celery_app.tasks import pregenerate_slot_task, publish_slot_task, run_pipeline_task
from backend.app.models.job import JobState


def test_celery_configuration():
    """Verify Celery app configuration, late acknowledgments, and fair prefetch."""
    assert celery_app.conf.timezone == "Asia/Kolkata"
    assert celery_app.conf.enable_utc is True
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert "default" in [q.name for q in celery_app.conf.task_queues]
    assert "video_rendering" in [q.name for q in celery_app.conf.task_queues]


def test_celery_beat_schedule_entries():
    """Verify crontab schedules for 07:00 and 18:00 daily publishing and pre-gen windows."""
    schedule = celery_app.conf.beat_schedule
    assert "pregenerate-morning-short" in schedule
    assert "publish-morning-short" in schedule
    assert "pregenerate-evening-short" in schedule
    assert "publish-evening-short" in schedule
    assert "periodic-system-reconciliation" in schedule

    # Verify hour configs
    assert schedule["pregenerate-morning-short"]["schedule"].hour == {1}
    assert schedule["publish-morning-short"]["schedule"].hour == {7}
    assert schedule["pregenerate-evening-short"]["schedule"].hour == {12}
    assert schedule["publish-evening-short"]["schedule"].hour == {18}


def test_pregenerate_slot_task_idempotency():
    """Verify that pregenerate_slot_task creates job once and does not duplicate."""
    mock_mongo = mongomock.MongoClient()["youtube_autopilot"]

    with patch("backend.app.celery_app.tasks.SyncMongoDB.get_db", return_value=mock_mongo), \
         patch("backend.app.celery_app.tasks.run_pipeline_task.delay") as mock_delay:

        # 1. First execution creates job
        res1 = pregenerate_slot_task(slot_index=1)
        assert res1["status"] == "QUEUED"
        assert "job_id" in res1
        mock_delay.assert_called_once()

        # 2. Second execution for the same slot on the same day detects existing job
        res2 = pregenerate_slot_task(slot_index=1)
        assert res2["status"] == "ALREADY_EXISTS"
        assert res2["job_id"] == res1["job_id"]
        # Delay should NOT have been called a second time
        assert mock_delay.call_count == 1


def test_publish_slot_task_missed_slot_rule():
    """Verify that if a video is not READY at publish time, it is marked MISSED, never faked."""
    mock_mongo = mongomock.MongoClient()["youtube_autopilot"]

    with patch("backend.app.celery_app.tasks.SyncMongoDB.get_db", return_value=mock_mongo):
        # 1. Slot with no pre-generated video -> Marks MISSED
        res = publish_slot_task(slot_index=1)
        assert res["status"] == "MISSED"

        # Check DB record
        doc = mock_mongo.publishing_jobs.find_one({"slot_index": 1})
        assert doc is not None
        assert doc["state"] == JobState.MISSED.value
        assert "Slot missed" in doc["error_message"]


def test_publish_slot_task_advances_ready_video():
    """Verify that when a video is READY, publish_slot_task calls YouTube publish and transitions to PUBLISHED."""
    mock_mongo = mongomock.MongoClient()["youtube_autopilot"]

    with patch("backend.app.celery_app.tasks.SyncMongoDB.get_db", return_value=mock_mongo), \
         patch("backend.app.agents.youtube.YouTubeAgent.publish_short", return_value={
             "youtube_video_id": "test_yt_video_123",
             "youtube_url": "https://www.youtube.com/shorts/test_yt_video_123",
             "status": "PUBLISHED"
         }) as mock_publish:
        from backend.app.core.security import compute_content_hash
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        idemp = compute_content_hash(f"autopilot_{date_str}_slot2")
        job_id = "job_ready_test_slot2"

        mock_mongo.publishing_jobs.insert_one({
            "_id": job_id,
            "slot_index": 2,
            "scheduled_at": now,
            "state": JobState.READY.value,
            "idempotency_key": idemp,
            "created_at": now,
            "updated_at": now
        })
        mock_mongo.videos.insert_one({
            "job_id": job_id,
            "title": "Python Quiz #Shorts",
            "description": "Quiz description",
            "file_path": "media_storage/rendered/test.mp4",
            "tags": ["Python"],
            "thumbnail_path": "media_storage/thumbnails/test.jpg"
        })

        res = publish_slot_task(slot_index=2)
        assert res["status"] == "PUBLISHED"
        assert res["youtube_video_id"] == "test_yt_video_123"
        mock_publish.assert_called_once()
        call_kwargs = mock_publish.call_args.kwargs
        assert call_kwargs["video_filepath"] == "media_storage/rendered/test.mp4"
        assert call_kwargs["title"] == "Python Quiz #Shorts"
        assert call_kwargs["description"] == "Quiz description"
        assert call_kwargs["tags"] == ["Python"]
        assert call_kwargs["privacy_status"] == "public"
        assert call_kwargs["thumbnail"] is not None

        # Check DB update
        updated_job = mock_mongo.publishing_jobs.find_one({"idempotency_key": idemp})
        assert updated_job["state"] == JobState.PUBLISHED.value
        assert updated_job["youtube_video_id"] == "test_yt_video_123"

        updated_video = mock_mongo.videos.find_one({"job_id": job_id})
        assert updated_video["youtube_video_id"] == "test_yt_video_123"
        assert updated_video["youtube_url"] == "https://www.youtube.com/shorts/test_yt_video_123"


def test_publish_slot_task_fails_cleanly_on_upload_error():
    """Verify that if YouTube upload fails, the job transitions to FAILED and never PUBLISHED."""
    mock_mongo = mongomock.MongoClient()["youtube_autopilot"]

    with patch("backend.app.celery_app.tasks.SyncMongoDB.get_db", return_value=mock_mongo), \
         patch("backend.app.agents.youtube.YouTubeAgent.publish_short", side_effect=RuntimeError("Upload rejected")):
        from backend.app.core.security import compute_content_hash
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        idemp = compute_content_hash(f"autopilot_{date_str}_slot2")
        job_id = "job_failed_test_slot2"

        mock_mongo.publishing_jobs.insert_one({
            "_id": job_id,
            "slot_index": 2,
            "scheduled_at": now,
            "state": JobState.READY.value,
            "idempotency_key": idemp,
            "created_at": now,
            "updated_at": now
        })
        mock_mongo.videos.insert_one({
            "job_id": job_id,
            "title": "Python Quiz #Shorts",
            "file_path": "media_storage/rendered/test.mp4"
        })

        res = publish_slot_task(slot_index=2)
        assert res["status"] == "FAILED"

        updated_job = mock_mongo.publishing_jobs.find_one({"idempotency_key": idemp})
        assert updated_job["state"] == JobState.FAILED.value
        assert "YouTube publishing failed" in updated_job["error_message"]
