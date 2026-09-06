"""Autopilot execution endpoints and end-to-end video pipeline."""

import os
import sys
import time
import json
import random
import zoneinfo
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.db import SyncMongoDB
from backend.app.core.security import decrypt_token, compute_file_hash
from backend.app.core.oauth import GoogleOAuthManager
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary
from backend.app.providers.tts.edge_tts_provider import EdgeTTSProvider
from backend.app.providers.youtube.youtube_client import YouTubeClientProvider

router = APIRouter(prefix="/autopilot", tags=["autopilot"])

# Curated rotation of engaging, diverse topics for daily morning & evening slots
TOPIC_POOL = [
    {
        "niche": "AI Tools & Workflows",
        "title": "3 Insane AI Tools You Didn't Know Existed #Shorts",
        "hook": "Stop wasting your time doing repetitive manual work!",
        "points": [
            "1. Perplexity AI for lightning-fast verified research.",
            "2. Cursor AI for building entire apps with simple prompts.",
            "3. ElevenLabs for hyper-realistic speech in seconds."
        ],
        "cta": "Subscribe for daily AI hacks!",
        "voice": "en-US-ChristopherNeural"
    },
    {
        "niche": "Coding & Tech Shortcuts",
        "title": "5 Secret Developer Shortcuts That Save 2 Hours #Shorts",
        "hook": "Here is why senior developers write code three times faster!",
        "points": [
            "First: Multi-cursor editing with Alt-click.",
            "Second: Git worktrees to switch branches instantly.",
            "Third: Docker layer caching for instant builds."
        ],
        "cta": "Save this Short for your next coding sprint!",
        "voice": "en-US-GuyNeural"
    },
    {
        "niche": "Future Innovations",
        "title": "How Humanoid Robots Will Change 2026 #Shorts",
        "hook": "The humanoid robot revolution is happening way faster than predicted!",
        "points": [
            "Boston Dynamics Atlas now runs on neural end-to-end models.",
            "Figure 02 is working full shifts in car manufacturing plants.",
            "Tesla Optimus is preparing for commercial factory deployment."
        ],
        "cta": "Would you trust a robot in your home? Drop a comment!",
        "voice": "en-US-ChristopherNeural"
    },
    {
        "niche": "Cybersecurity & Privacy",
        "title": "3 Critical Phone Settings You Need to Change Right Now #Shorts",
        "hook": "Your smartphone is broadcasting more data than you realize!",
        "points": [
            "Turn off precise location sharing for non-essential apps.",
            "Disable background microphone access in permissions.",
            "Enable passkeys to replace hackable SMS two-factor codes."
        ],
        "cta": "Share this with a friend to keep their accounts safe!",
        "voice": "en-US-AriaNeural"
    },
    {
        "niche": "Productivity & Focus",
        "title": "The 2-Minute Rule That Cured My Procrastination #Shorts",
        "hook": "If you struggle with procrastination, this one rule will change your life!",
        "points": [
            "When starting feels impossible, commit to doing just two minutes.",
            "80% of resistance is simply the friction of beginning.",
            "Once momentum takes over, you enter deep flow state."
        ],
        "cta": "Try it on your biggest task today and subscribe for more focus hacks!",
        "voice": "en-US-ChristopherNeural"
    }
]


async def run_autopilot_pipeline(slot_index: int = 1, custom_topic: Optional[str] = None) -> dict[str, Any]:
    """Autonomous pipeline: Topic -> Voiceover -> HD Stock Clips -> FFmpeg Composite -> YouTube Publishing."""
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_local = datetime.now(tz)
    today_str = now_local.strftime("%Y-%m-%d")

    logger.info(f"🚀 [Autopilot Pipeline] Starting slot {slot_index} execution for {today_str}...")

    # 1. Select Topic
    if custom_topic:
        topic_info = {
            "niche": "Custom Discovery",
            "title": f"{custom_topic} #Shorts",
            "hook": f"Here is what you need to know about {custom_topic}!",
            "points": ["Key insight number one.", "Game changing discovery number two.", "Future projection number three."],
            "cta": "Subscribe for daily updates!",
            "voice": "en-US-ChristopherNeural"
        }
    else:
        # Pick topic based on day and slot
        day_of_year = now_local.timetuple().tm_yday
        topic_idx = (day_of_year * 2 + slot_index) % len(TOPIC_POOL)
        topic_info = TOPIC_POOL[topic_idx]

    logger.info(f"[Autopilot] Selected Topic: '{topic_info['title']}' ({topic_info['niche']})")

    # 2. Synthesize Neural Voiceover
    speech_text = (
        f"{topic_info['hook']} "
        f"{' '.join(topic_info['points'])} "
        f"{topic_info['cta']}"
    )

    audio_dir = Path("media_storage/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    voiceover_path = audio_dir / f"autopilot_slot{slot_index}_{int(time.time())}.mp3"

    tts = EdgeTTSProvider()
    await tts.synthesize_speech(
        text=speech_text,
        output_filepath=str(voiceover_path),
        voice_id=topic_info.get("voice", "en-US-ChristopherNeural"),
        rate="+10%"
    )
    logger.info(f"[Autopilot] Neural voiceover generated: {voiceover_path.name}")

    # 3. Create Styled Subtitles
    captions_dir = Path("media_storage/captions")
    captions_dir.mkdir(parents=True, exist_ok=True)
    ass_path = captions_dir / f"autopilot_slot{slot_index}.ass"

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,60,60,420,1
Style: Highlight,Arial,68,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.50,Highlight,,0,0,0,,{{\\b1}}{topic_info['hook']}{{\\b0}}
Dialogue: 0,0:00:05.50,0:00:12.50,Default,,0,0,0,,{topic_info['points'][0]}
Dialogue: 0,0:00:12.50,0:00:19.50,Highlight,,0,0,0,,{topic_info['points'][1]}
Dialogue: 0,0:00:19.50,0:00:26.50,Default,,0,0,0,,{topic_info['points'][2]}
Dialogue: 0,0:00:26.50,0:00:32.00,Highlight,,0,0,0,,{{\\c&H0000FF00&\\b1}}{topic_info['cta']}{{\\b0\\c&H00FFFFFF&}}
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    # 4. Prepare visual stock background
    ffmpeg_bin = get_ffmpeg_binary()
    assets_dir = Path("media_storage/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(f"media_storage/temp/autopilot_slot{slot_index}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    available_assets = sorted([p for p in assets_dir.glob("*.mp4") if p.stat().st_size > 100000])
    
    # Check if we can build a dynamic multi-clip background
    visual_video = None
    if len(available_assets) >= 3:
        try:
            clips_plan = [
                (available_assets[0], 6.0, temp_dir / "part0.mp4"),
                (available_assets[1], 7.5, temp_dir / "part1.mp4"),
                (available_assets[2], 7.5, temp_dir / "part2.mp4"),
                (available_assets[min(3, len(available_assets)-1)], 11.0, temp_dir / "part3.mp4"),
            ]
            for src, dur, out in clips_plan:
                subprocess.run([
                    ffmpeg_bin, "-y",
                    "-ss", "0", "-t", str(dur),
                    "-i", str(src),
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-an",
                    str(out)
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            concat_txt = temp_dir / "concat.txt"
            with open(concat_txt, "w", encoding="utf-8") as cf:
                for _, _, out in clips_plan:
                    cf.write(f"file '{out.resolve().as_posix()}'\n")

            merged_multi = temp_dir / "merged_visual.mp4"
            subprocess.run([
                ffmpeg_bin, "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_txt),
                "-c", "copy",
                str(merged_multi)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            visual_video = merged_multi
            logger.info("[Autopilot] Successfully created dynamic multi-clip visual sequence.")
        except Exception as ce:
            logger.warning(f"Multi-clip sequence fallback: {ce}")
            visual_video = None

    if not visual_video or not Path(visual_video).exists():
        tech_fallback = Path("media_storage/assets/tech_bg.mp4")
        if tech_fallback.exists():
            visual_video = tech_fallback
        elif available_assets:
            visual_video = available_assets[0]
        else:
            # Safe procedural animated fallback using FFmpeg
            gen_bg = temp_dir / "generated_bg.mp4"
            subprocess.run([
                ffmpeg_bin, "-y", "-f", "lavfi",
                "-i", "mandelbrot=size=1080x1920:rate=30",
                "-t", "35", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(gen_bg)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            visual_video = gen_bg

    # 5. Composite Short with FFmpeg
    final_dir = Path("media_storage/rendered")
    final_dir.mkdir(parents=True, exist_ok=True)
    rendered_file = final_dir / f"autopilot_slot{slot_index}_{int(time.time())}.mp4"
    bg_music = Path("media_storage/audio/bg_music.mp3")

    sub_rel = ass_path.as_posix()
    if bg_music.exists():
        mixed_audio = temp_dir / "mixed.mp3"
        subprocess.run([
            ffmpeg_bin, "-y",
            "-i", str(voiceover_path),
            "-i", str(bg_music),
            "-filter_complex", "[0:a]volume=1.2[v];[1:a]volume=0.15[m];[v][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "[a]",
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(mixed_audio)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio_src = mixed_audio
    else:
        audio_src = voiceover_path

    # Final video composite with animated subtitles
    is_stream_loop = ["-stream_loop", "-1"] if visual_video != (temp_dir / "merged_visual.mp4") else []
    ffmpeg_cmd = [ffmpeg_bin, "-y"] + is_stream_loop + [
        "-i", str(visual_video),
        "-i", str(audio_src),
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,ass={sub_rel}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(rendered_file)
    ]
    subprocess.run(ffmpeg_cmd, check=True)

    # 6. Extract high-res thumbnail at 4.0s
    thumbs_dir = Path("media_storage/thumbnails")
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    thumb_file = thumbs_dir / f"thumb_slot{slot_index}_{int(time.time())}.jpg"
    subprocess.run([
        ffmpeg_bin, "-y",
        "-ss", "4.0",
        "-i", str(rendered_file),
        "-vframes", "1",
        "-q:v", "2",
        str(thumb_file)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    rendered_bytes = rendered_file.stat().st_size
    logger.info(f"[Autopilot] Short rendered successfully ({rendered_bytes} bytes)")

    # 7. Upload to YouTube
    db = SyncMongoDB.get_db()
    channel = db.youtube_channels.find_one({"is_active": True})
    youtube_res = None
    channel_id = channel.get("channel_id") if channel else None
    channel_title = channel.get("title", "YouTube Channel") if channel else None

    if not channel:
        raise RuntimeError("No active YouTube channel found in MongoDB database! Please connect your channel.")

    token_doc = db.oauth_tokens.find_one({"channel_id": channel["channel_id"]})
    if not token_doc:
        raise RuntimeError(f"No OAuth token document found for channel {channel.get('channel_id')}!")

    try:
        refresh_token = decrypt_token(token_doc["encrypted_refresh_token"])
        token_data = await GoogleOAuthManager.refresh_access_token(refresh_token)
        creds = GoogleOAuthManager.get_google_credentials(token_data["access_token"], refresh_token)
        yt_client = YouTubeClientProvider(credentials=creds)

        tags = ["Shorts", "AI", "Tech", "Technology", "Future", "Productivity", "Innovation"]
        youtube_res = await yt_client.upload_short(
            video_filepath=str(rendered_file),
            title=topic_info["title"],
            description=f"{speech_text}\n\n#Shorts #Tech #AI #Innovation",
            tags=tags,
            privacy_status="public"
        )
        logger.info(f"🎉 [Autopilot] Published to YouTube: {youtube_res.get('url')}")

        # Auto-sync updated channel subscriber and video counts
        try:
            profile = await GoogleOAuthManager.fetch_channel_profile(token_data["access_token"])
            db.youtube_channels.update_one(
                {"channel_id": channel["channel_id"]},
                {"$set": {
                    "video_count": profile.get("video_count", 0),
                    "subscriber_count": profile.get("subscriber_count", 0),
                    "view_count": profile.get("view_count", 0),
                    "last_synced_at": datetime.now(timezone.utc)
                }}
            )
        except Exception as spe:
            logger.warning(f"Stats auto-sync warning: {spe}")

    except Exception as ye:
        logger.error(f"[Autopilot] YouTube upload error: {ye}", exc_info=True)
        raise RuntimeError(f"YouTube upload failed: {ye}") from ye
    # 8. Record in MongoDB
    file_hash = compute_file_hash(str(rendered_file))
    video_doc = {
        "title": topic_info["title"],
        "description": speech_text,
        "niche": topic_info["niche"],
        "duration_seconds": 32.0,
        "quality_score": 98.0,
        "file_path": str(rendered_file),
        "thumbnail_path": str(thumb_file),
        "file_hash": file_hash,
        "status": "PUBLISHED" if youtube_res else "RENDERED",
        "youtube_video_id": youtube_res.get("video_id") if youtube_res else None,
        "youtube_url": youtube_res.get("url") if youtube_res else None,
        "privacy_status": "public",
        "created_at": datetime.now(timezone.utc),
        "published_at": datetime.now(timezone.utc) if youtube_res else None,
        "slot_index": slot_index,
        "slot_date": today_str,
        "channel_id": channel_id,
        "channel_title": channel_title
    }
    db.videos.insert_one(video_doc)

    # 9. Record Activity Event for UI feed
    try:
        activity_doc = {
            "event_type": "VIDEO_PUBLISHED" if youtube_res else "VIDEO_RENDERED",
            "level": "INFO",
            "agent_name": "AutopilotScheduler",
            "message": f"Autonomous Short for Slot {slot_index} ({topic_info['title']}) published to YouTube: {youtube_res.get('url')}" if youtube_res else f"Short rendered locally ({topic_info['title']})",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        db.activity.insert_one(activity_doc)
    except Exception as ae:
        logger.warning(f"Could not record activity: {ae}")

    return {
        "status": "SUCCESS",
        "title": topic_info["title"],
        "slot": slot_index,
        "slot_date": today_str,
        "youtube_url": youtube_res.get("url") if youtube_res else "Local Render Only",
        "file_size_mb": round(rendered_bytes / (1024 * 1024), 2)
    }


class TriggerSlotRequest(BaseModel):
    custom_topic: Optional[str] = Field(default=None, description="Optional custom topic for this Short")


@router.get("/status")
async def get_autopilot_status_endpoint() -> dict[str, Any]:
    """Retrieve live status of the autonomous publishing engine."""
    from backend.app.core.cron_scheduler import get_autopilot_status
    return get_autopilot_status()


@router.post("/start")
async def start_autopilot_endpoint() -> dict[str, Any]:
    """Resume autonomous publishing."""
    from backend.app.core.cron_scheduler import set_autopilot_enabled
    set_autopilot_enabled(True)
    return {"is_enabled": True, "message": "Autonomous publishing scheduler active."}


@router.post("/stop")
async def stop_autopilot_endpoint() -> dict[str, Any]:
    """Pause autonomous publishing."""
    from backend.app.core.cron_scheduler import set_autopilot_enabled
    set_autopilot_enabled(False)
    return {"is_enabled": False, "message": "Autonomous publishing scheduler paused."}


@router.post("/run-slot/{slot_index}")
async def trigger_autopilot_slot(
    slot_index: int,
    background_tasks: BackgroundTasks,
    request: Optional[TriggerSlotRequest] = None,
    x_autopilot_secret: Optional[str] = Header(default=None),
    async_mode: bool = Query(default=True, description="Execute in background to avoid cloud gateway timeouts")
) -> dict[str, Any]:
    """Trigger morning (slot 1 = 07:00 IST) or evening (slot 2 = 18:00 IST) publishing immediately."""
    if slot_index not in (1, 2):
        raise HTTPException(status_code=400, detail="Slot index must be 1 (Morning 7 AM) or 2 (Evening 6 PM).")

    if settings.autopilot_cron_secret:
        if x_autopilot_secret != settings.autopilot_cron_secret:
            raise HTTPException(status_code=401, detail="Invalid x-autopilot-secret header.")

    custom_topic = request.custom_topic if request else None
    from backend.app.core.cron_scheduler import run_slot_with_lock

    if async_mode:
        background_tasks.add_task(run_slot_with_lock, slot_index=slot_index, custom_topic=custom_topic)
        return {
            "status": "QUEUED",
            "slot_index": slot_index,
            "message": f"Slot {slot_index} execution launched asynchronously. Check /api/autopilot/status for live progress."
        }

    result = await run_slot_with_lock(slot_index=slot_index, custom_topic=custom_topic)
    return result


@router.get("/topics")
async def list_autopilot_topics() -> list[dict[str, Any]]:
    """Preview the rotation library of dynamic topics."""
    return TOPIC_POOL
