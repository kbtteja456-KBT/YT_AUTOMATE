"""Real unit tests for Phase 22: Failure recovery, server restart, and missed-slot reconciliation."""

import pytest
from datetime import datetime, timezone, timedelta
from mongomock_motor import AsyncMongoMockClient

from backend.app.models.job import PublishingJob, JobState
from backend.app.core.repositories import JobRepository
from backend.app.pipeline.reconciliation import JobReconciler


@pytest.fixture
def mock_db():
    client = AsyncMongoMockClient()
    return client["test_reconciliation_db"]


@pytest.mark.anyio
async def test_reconciler_marks_expired_slot_missed(mock_db):
    """Verify that a job interrupted and left uncompleted past the grace period is marked MISSED."""
    repo = JobRepository(mock_db)
    reconciler = JobReconciler(job_repository=repo, grace_period_minutes=30)

    # Job was scheduled 2 hours ago and crashed while RENDERING
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    crashed_job = PublishingJob(
        slot_index=1,
        scheduled_at=two_hours_ago,
        state=JobState.RENDERING,
        idempotency_key="reconcile_expired_test_01"
    )
    saved = await repo.create_job(crashed_job)

    # Run reconciliation audit
    summary = await reconciler.reconcile_crashed_and_missed_jobs()
    assert summary["missed_count"] == 1

    # Verify state in database
    reconciled_job = await repo.get_job_by_id(saved.id)
    assert reconciled_job.state == JobState.MISSED
    assert "Missed Slot" in reconciled_job.error_message


@pytest.mark.anyio
async def test_reconciler_resumes_job_within_grace_window(mock_db):
    """Verify that a job within the grace window is kept eligible to resume."""
    repo = JobRepository(mock_db)
    reconciler = JobReconciler(job_repository=repo, grace_period_minutes=30)

    # Job was scheduled 10 minutes ago (well within 30 min grace period)
    ten_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
    running_job = PublishingJob(
        slot_index=2,
        scheduled_at=ten_mins_ago,
        state=JobState.SCRIPTING,
        idempotency_key="reconcile_window_test_02"
    )
    saved = await repo.create_job(running_job)

    summary = await reconciler.reconcile_crashed_and_missed_jobs()
    assert summary["resumed_count"] == 1
    assert summary["missed_count"] == 0

    reconciled_job = await repo.get_job_by_id(saved.id)
    assert reconciled_job.state == JobState.SCRIPTING
