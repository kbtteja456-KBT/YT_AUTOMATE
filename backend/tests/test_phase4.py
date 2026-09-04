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
    """Verify that when a video is READY, it transitions to PUBLISHING."""
    mock_mongo = mongomock.MongoClient()["youtube_autopilot"]

    with patch("backend.app.celery_app.tasks.SyncMongoDB.get_db", return_value=mock_mongo):
        # Pre-seed a ready job
        from backend.app.core.security import compute_content_hash
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        idemp = compute_content_hash(f"autopilot_{date_str}_slot2")

        mock_mongo.publishing_jobs.insert_one({
            "slot_index": 2,
            "scheduled_at": now,
            "state": JobState.READY.value,
            "idempotency_key": idemp,
            "created_at": now,
            "updated_at": now
        })

        res = publish_slot_task(slot_index=2)
        assert res["status"] == "PUBLISHING"

        # Check DB update
        updated = mock_mongo.publishing_jobs.find_one({"idempotency_key": idemp})
        assert updated["state"] == JobState.PUBLISHING.value
