"""FastAPI backend application entrypoint for AI YouTube Shorts Autopilot."""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Any

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.resources import resource_guard
from backend.app.core.db import AsyncMongoDB
from backend.app.api import api_router
from backend.app.api.routes_providers import check_all_providers_health


from backend.app.core.cron_scheduler import start_autopilot_scheduler, stop_autopilot_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle hooks."""
    logger.info("Initializing AI YouTube Shorts Autopilot backend...")
    # Verify ENCRYPTION_KEY is set and valid; fail loudly if missing
    from backend.app.core.security import get_encryption_key
    get_encryption_key()

    # Ensure storage paths exist
    settings.storage_path
    settings.temp_path

    # Connect to MongoDB
    await AsyncMongoDB.connect()

    # Populate royalty-free music pool (Incompetech CC BY 4.0 / FMA CC0)
    try:
        from backend.app.providers.music.pixabay_music import FreeMusicArchiveProvider
        music_provider = FreeMusicArchiveProvider()
        pool_dir = Path(settings.media_storage_dir) / "audio" / "music_pool"
        await music_provider.populate_pool(pool_dir)
    except Exception as e:
        logger.warning(f"Music pool startup note: {e}")

    # Check host resources
    safe, warnings = resource_guard.verify_safe_to_render()
    if not safe:
        logger.warning(f"Resource safeguard warning: {', '.join(warnings)}")
    else:
        logger.info("System resources verified safe for rendering.")

    logger.info(f"Zero-Cost Hard Mode: {'ACTIVE' if settings.zero_cost_mode else 'DISABLED'}")
    logger.info(f"Publishing Schedule: 07:00 & 18:00 ({settings.timezone})")

    # Start autonomous daily scheduler
    start_autopilot_scheduler()

    yield
    logger.info("Shutting down AI YouTube Shorts Autopilot backend...")
    stop_autopilot_scheduler()
    await AsyncMongoDB.disconnect()


app = FastAPI(
    title="AI YouTube Shorts Autopilot API",
    description="Autonomous, local-first, zero-cost-by-default video publishing engine",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local React/Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main API routes
app.include_router(api_router)

# Mount local media directory for serving thumbnails and rendered MP4s
_media_dir = Path(settings.media_storage_dir).resolve()
_media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media_dir)), name="media")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Primary system health check returning real hardware and operational stats."""
    metrics = resource_guard.get_system_metrics()
    return {
        "status": "HEALTHY",
        "app": "AI YouTube Shorts Autopilot",
        "version": "1.0.0",
        "zero_cost_mode": settings.zero_cost_mode,
        "timezone": settings.timezone,
        "daily_video_limit": settings.daily_video_limit,
        "system_resources": metrics,
        "timestamp": time.time()
    }


@app.get("/providers/health")
async def providers_health_alias() -> dict[str, Any]:
    """Direct alias for provider health check."""
    return await check_all_providers_health()
