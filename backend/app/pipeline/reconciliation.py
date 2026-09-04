"""Startup and periodic job reconciliation for power loss, reboot, and sleep recovery."""

from datetime import datetime, timezone, timedelta
from typing import Any
from backend.app.core.logging import logger
from backend.app.models.job import JobState, PublishingJob
from backend.app.core.repositories import JobRepository


class JobReconciler:
    """Detects and recovers jobs interrupted by server restart, sleep, or power failures."""

    def __init__(self, job_repository: JobRepository, grace_period_minutes: int = 30):
        self.repo = job_repository
        self.grace_period = timedelta(minutes=grace_period_minutes)

    async def reconcile_crashed_and_missed_jobs(self) -> dict[str, int]:
        """Scan MongoDB for incomplete jobs and reconcile them honestly."""
        logger.info("[Reconciliation] Scanning for interrupted or uncompleted jobs...")

        in_progress_jobs = await self.repo.get_in_progress_jobs()
        now = datetime.now(timezone.utc)

        missed_count = 0
        resumed_count = 0

        for job in in_progress_jobs:
            scheduled_at = job.scheduled_at
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

            cutoff = scheduled_at + self.grace_period

            if now > cutoff:
                # Slot has passed beyond grace period! Mark MISSED. Never fake publish!
                logger.warning(
                    f"[Reconciliation] Slot {job.slot_index} (scheduled for {scheduled_at.isoformat()}) "
                    f"has passed the grace period. Marking job {job.id} as MISSED."
                )
                await self.repo.update_job_state(
                    job.id,
                    JobState.MISSED,
                    error_message=f"Missed Slot: Machine was offline/asleep during scheduled window. Reconciled at {now.isoformat()}."
                )
                missed_count += 1
            else:
                # Within pre-generation window or within grace period: eligible for resumption
                logger.info(
                    f"[Reconciliation] Job {job.id} is within window (scheduled: {scheduled_at.isoformat()}). "
                    f"Resuming from checkpoint '{job.last_completed_stage or 'START'}'."
                )
                resumed_count += 1

        logger.info(f"[Reconciliation] Reconciliation complete: {missed_count} marked MISSED, {resumed_count} eligible to resume.")
        return {
            "missed_count": missed_count,
            "resumed_count": resumed_count
        }
