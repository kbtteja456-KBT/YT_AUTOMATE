"""Autonomous Daily Publishing Scheduler for 7:00 AM and 6:00 PM (Asia/Kolkata)."""

import asyncio
from datetime import datetime, timezone
import zoneinfo
from typing import Optional

from backend.app.config import settings
from backend.app.core.logging import logger

_scheduler_task: Optional[asyncio.Task] = None
_last_triggered_date_slot: set[str] = set()

async def execute_slot_pipeline(slot_index: int, custom_topic: Optional[str] = None) -> dict:
    """Execute full end-to-end Short generation and YouTube publishing for a slot."""
    from backend.app.api.routes_autopilot import run_autopilot_pipeline
    return await run_autopilot_pipeline(slot_index=slot_index, custom_topic=custom_topic)

async def _scheduler_loop():
    """Continuous background loop checking for 07:00 and 18:00 IST trigger windows."""
    logger.info(f"Starting in-process Autopilot Scheduler: 07:00 & 18:00 ({settings.timezone})")
    tz = zoneinfo.ZoneInfo(settings.timezone)

    while True:
        try:
            now = datetime.now(tz)
            today_str = now.strftime("%Y-%m-%d")
            hour = now.hour
            minute = now.minute

            # Morning Slot: 07:00 IST (allow trigger between 07:00 and 07:05)
            slot1_key = f"{today_str}_slot_1"
            if hour == 7 and 0 <= minute <= 5 and slot1_key not in _last_triggered_date_slot:
                _last_triggered_date_slot.add(slot1_key)
                logger.info(f"⏰ [Autopilot Scheduler] Triggering 07:00 AM Morning Short Publishing (Slot 1)...")
                asyncio.create_task(execute_slot_pipeline(1))

            # Evening Slot: 18:00 IST (allow trigger between 18:00 and 18:05)
            slot2_key = f"{today_str}_slot_2"
            if hour == 18 and 0 <= minute <= 5 and slot2_key not in _last_triggered_date_slot:
                _last_triggered_date_slot.add(slot2_key)
                logger.info(f"⏰ [Autopilot Scheduler] Triggering 06:00 PM Evening Short Publishing (Slot 2)...")
                asyncio.create_task(execute_slot_pipeline(2))

            # Sleep 30 seconds before next check
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.info("Autopilot Scheduler loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Autopilot Scheduler error: {e}")
            await asyncio.sleep(60)

def start_autopilot_scheduler():
    """Start the background scheduler task inside the FastAPI event loop."""
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())
        logger.info("Autonomous daily scheduler initialized.")

def stop_autopilot_scheduler():
    """Stop the background scheduler task gracefully."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("Autonomous daily scheduler stopped.")
