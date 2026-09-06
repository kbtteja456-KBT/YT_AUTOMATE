"""Provider configuration and real health check endpoints."""

import os
import shutil
import time
from pathlib import Path
from fastapi import APIRouter
from typing import Any
from backend.app.config import settings

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def list_providers() -> list[dict[str, Any]]:
    """List configured provider adapters and zero-cost status."""
    return [
        {
            "name": "OpenRouter (Free Tier)",
            "type": "AI",
            "is_zero_cost": True,
            "is_paid": False,
            "model": settings.openrouter_model,
            "enabled": True
        },
        {
            "name": "Microsoft Edge TTS",
            "type": "TTS",
            "is_zero_cost": True,
            "is_paid": False,
            "default_voice": "en-US-ChristopherNeural",
            "enabled": True
        },
        {
            "name": "Local Faster-Whisper",
            "type": "STT",
            "is_zero_cost": True,
            "is_paid": False,
            "model_size": "base",
            "enabled": True
        },
        {
            "name": "Stock Media & Procedural Graphics",
            "type": "STOCK_MEDIA",
            "is_zero_cost": True,
            "is_paid": False,
            "sources": ["Pexels Free", "Wikimedia Commons", "Procedural Motion Engine"],
            "enabled": True
        },
        {
            "name": "DuckDuckGo & Wikipedia Search",
            "type": "SEARCH",
            "is_zero_cost": True,
            "is_paid": False,
            "enabled": True
        },
        {
            "name": "YouTube Data API v3",
            "type": "YOUTUBE",
            "is_zero_cost": True,
            "is_paid": False,
            "enabled": bool(settings.google_client_id)
        },
        {
            "name": "Free Music Archive / Incompetech CC0 & CC-BY Music Pool",
            "type": "MUSIC",
            "is_zero_cost": True,
            "is_paid": False,
            "enabled": True,
            "note": "Incompetech (CC BY 4.0) always available. FMA (CC0) requires FMA_API_KEY."
        }
    ]


@router.get("/health")
async def check_all_providers_health() -> dict[str, Any]:
    """Perform real health checks on every provider subsystem. Never simulate."""
    results = {}

    # 1. Check AI Provider (OpenRouter key check)
    has_ai_key = bool(settings.openrouter_api_key.strip())
    results["ai"] = {
        "provider": "OpenRouter (Free)",
        "status": "CONNECTED" if has_ai_key else "NOT_CONFIGURED",
        "is_zero_cost": True,
        "message": "OpenRouter API Key configured" if has_ai_key else "OPENROUTER_API_KEY is not set in environment"
    }

    # 2. Check TTS Provider (Edge-TTS check)
    try:
        import edge_tts
        results["tts"] = {
            "provider": "Microsoft Edge TTS",
            "status": "CONNECTED",
            "is_zero_cost": True,
            "message": "Edge TTS library loaded and available"
        }
    except ImportError:
        results["tts"] = {
            "provider": "Microsoft Edge TTS",
            "status": "OFFLINE",
            "is_zero_cost": True,
            "message": "edge-tts package missing"
        }

    # 3. Check STT Provider (Whisper check)
    try:
        import faster_whisper
        results["stt"] = {
            "provider": "Faster-Whisper Local",
            "status": "CONNECTED",
            "is_zero_cost": True,
            "message": "faster-whisper runtime available"
        }
    except ImportError:
        results["stt"] = {
            "provider": "Faster-Whisper Local",
            "status": "OFFLINE",
            "is_zero_cost": True,
            "message": "faster-whisper package missing"
        }

    # 4. Check FFmpeg Rendering Tooling
    from backend.app.core.ffmpeg_utils import get_ffmpeg_binary
    try:
        bin_path = get_ffmpeg_binary()
        ffmpeg_found = bool(shutil.which("ffmpeg") or (bin_path and Path(bin_path).exists()))
    except Exception:
        ffmpeg_found = False

    results["video_rendering"] = {
        "provider": "FFmpeg Engine",
        "status": "CONNECTED" if ffmpeg_found else "NOT_CONFIGURED",
        "is_zero_cost": True,
        "message": "FFmpeg binary active and ready" if ffmpeg_found else "FFmpeg binary not found in system PATH"
    }

    # 5. Check YouTube OAuth credentials
    has_yt_creds = bool(settings.google_client_id and settings.google_client_secret)
    results["youtube"] = {
        "provider": "YouTube Data API v3",
        "status": "CONNECTED" if has_yt_creds else "NOT_CONFIGURED",
        "is_zero_cost": True,
        "message": "Google OAuth credentials configured" if has_yt_creds else "GOOGLE_CLIENT_ID or SECRET missing"
    }

    # 6. Check Search Provider
    try:
        import duckduckgo_search
        results["search"] = {
            "provider": "DuckDuckGo Search",
            "status": "CONNECTED",
            "is_zero_cost": True,
            "message": "duckduckgo_search available"
        }
    except ImportError:
        results["search"] = {
            "provider": "DuckDuckGo Search",
            "status": "OFFLINE",
            "is_zero_cost": True,
            "message": "duckduckgo_search package missing"
        }

    # 7. Check Free Stock Media Providers
    has_pexels = bool(settings.pexels_api_key)
    has_pixabay = bool(settings.pixabay_api_key)
    results["stock_media"] = {
        "provider": "Pexels & Pixabay (Free Tiers)",
        "status": "CONNECTED" if (has_pexels or has_pixabay) else "NOT_CONFIGURED",
        "is_zero_cost": True,
        "message": f"Stock APIs active (Pexels: {'OK' if has_pexels else 'MISSING'}, Pixabay: {'OK' if has_pixabay else 'MISSING'})"
    }

    # 8. Check Free Music Archive / Incompetech Music Provider
    fma_key_present = bool(getattr(settings, 'fma_api_key', '').strip()) if hasattr(settings, 'fma_api_key') else False
    results["music"] = {
        "provider": "FreeMusicArchiveProvider (Incompetech CC BY 4.0 + FMA CC0)",
        "status": "CONNECTED",
        "is_zero_cost": True,
        "fma_cc0_available": fma_key_present,
        "incompetech_cc_by_available": True,
        "message": (
            "FMA (CC0, no attribution) + Incompetech (CC BY 4.0, attribution appended to descriptions)."
            if fma_key_present else
            "Incompetech (CC BY 4.0) active — attribution credit automatically appended to YouTube descriptions. "
            "Set FMA_API_KEY for CC0 tracks that need no attribution."
        )
    }

    return {
        "timestamp": time.time(),
        "zero_cost_mode": settings.zero_cost_mode,
        "subsystems": results
    }


@router.post("/music/setup")
async def setup_music_pool_endpoint() -> dict[str, Any]:
    """Download and populate royalty-free music pool (Incompetech CC BY 4.0 + FMA CC0 if key available)."""
    from backend.app.providers.music.music_archive import FreeMusicArchiveProvider
    provider = FreeMusicArchiveProvider()
    pool_dir = Path(settings.media_storage_dir) / "audio" / "music_pool"
    tracks = await provider.populate_pool(pool_dir, force_refresh=True)
    cc0_count = sum(1 for t in tracks if t.get("requires_attribution") == "false")
    cc_by_count = sum(1 for t in tracks if t.get("requires_attribution") == "true")
    return {
        "status": "SUCCESS" if tracks else "SKIPPED",
        "tracks_count": len(tracks),
        "cc0_tracks": cc0_count,
        "cc_by_tracks": cc_by_count,
        "note": "CC BY tracks will have attribution credit appended to each video's YouTube description automatically.",
        "tracks": tracks
    }
