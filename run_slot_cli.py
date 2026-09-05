"""Standalone CLI runner for autonomous YouTube Shorts publishing.
Can be executed directly by Windows Task Scheduler or cron without needing FastAPI running.
"""

import sys
import os
import argparse
import asyncio
from datetime import datetime, timezone
import zoneinfo

# Ensure workspace root is on sys.path
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_DIR)

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.cron_scheduler import is_slot_published_today
from backend.app.api.routes_autopilot import run_autopilot_pipeline


def log_run(message: str):
    """Log to stdout and persistent file."""
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{now_str}] {message}"
    print(line)
    log_file = os.path.join(WORKSPACE_DIR, "media_storage", "autopilot_scheduler.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


async def main():
    parser = argparse.ArgumentParser(description="Autonomous YouTube Shorts CLI Runner")
    parser.add_argument("--slot", type=int, default=0, choices=[0, 1, 2], help="Slot index: 1 (Morning 07:00 IST), 2 (Evening 18:00 IST), 0=Auto-detect by IST")
    parser.add_argument("--force", action="store_true", help="Force execution even if already published today")
    parser.add_argument("--topic", type=str, default=None, help="Optional custom topic override")
    args = parser.parse_args()

    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_local = datetime.now(tz)
    today_str = now_local.strftime("%Y-%m-%d")

    slot = args.slot
    if slot == 0:
        slot = 1 if now_local.hour < 13 else 2
        log_run(f"🕒 Auto-detected slot based on current time ({now_local.strftime('%H:%M')} IST): Slot {slot}")

    slot_name = "Morning Slot 1 (07:00 AM)" if slot == 1 else "Evening Slot 2 (06:00 PM)"
    log_run(f"🔔 Task triggered for {slot_name}")

    # Check if already published today
    if not args.force and is_slot_published_today(slot, today_str):
        log_run(f"✅ {slot_name} has ALREADY been published today ({today_str}). Skipping redundant run.")
        return

    log_run(f"🚀 Starting autonomous generation & YouTube publishing for {slot_name}...")
    try:
        result = await run_autopilot_pipeline(slot_index=slot, custom_topic=args.topic)
        yt_url = result.get("youtube_url")
        if not yt_url or yt_url == "Local Render Only":
            raise RuntimeError(f"Video render completed, but YouTube upload failed to produce a live URL: {result}")
        log_run(f"🎉 Successfully published to YouTube! URL: {yt_url}")
    except Exception as e:
        log_run(f"❌ Pipeline failed with error: {e}")
        logger.exception("CLI Pipeline Error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
