"""FFmpeg and FFprobe system locator and diagnostic utilities."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from backend.app.core.logging import logger
from backend.app.core.errors import ProviderError


def get_ffmpeg_binary() -> str:
    """Return path to executable FFmpeg binary."""
    sys_path = shutil.which("ffmpeg")
    if sys_path:
        return sys_path

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def get_ffprobe_binary() -> str:
    """Return path to executable FFprobe binary if available."""
    sys_path = shutil.which("ffprobe")
    if sys_path:
        return sys_path
    # Fallback to ffmpeg binary
    return get_ffmpeg_binary()


def probe_video_metadata(video_path: str) -> dict[str, Any]:
    """Inspect video container, dimensions, duration, and codecs using FFmpeg."""
    v_path = Path(video_path).resolve()
    if not v_path.exists():
        raise FileNotFoundError(f"Media file does not exist: {video_path}")

    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [ffmpeg_bin, "-hide_banner", "-i", str(v_path)]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stderr_output = result.stderr

    duration = 0.0
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_output)
    if dur_match:
        hrs, mins, secs = dur_match.groups()
        duration = int(hrs) * 3600 + int(mins) * 60 + float(secs)

    width, height, fps = 0, 0, 30.0
    video_codec = ""
    # Stream #0:0: Video: h264 (High), yuv420p, 1080x1920 [SAR 1:1 DAR 9:16], 30 fps
    video_match = re.search(r"Stream.*Video:\s*([a-zA-Z0-9_\-]+).*?(\d{3,4})x(\d{3,4})", stderr_output)
    if video_match:
        video_codec = video_match.group(1).lower()
        width = int(video_match.group(2))
        height = int(video_match.group(3))

    audio_codec = ""
    audio_present = False
    audio_match = re.search(r"Stream.*Audio:\s*([a-zA-Z0-9_\-]+)", stderr_output)
    if audio_match:
        audio_codec = audio_match.group(1).lower()
        audio_present = True

    return {
        "file_path": str(v_path),
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "video_codec": video_codec,
        "audio_codec": audio_codec,
        "audio_present": audio_present,
        "raw_stderr": stderr_output
    }


def audit_video_defects(video_path: str) -> dict[str, Any]:
    """Run black frame, freeze, and silence detection filters."""
    ffmpeg_bin = get_ffmpeg_binary()
    v_path = Path(video_path).resolve()

    cmd = [
        ffmpeg_bin, "-hide_banner",
        "-i", str(v_path),
        "-vf", "blackdetect=d=1.5:pic_th=0.98,freezedetect=n=0.003:d=3.0",
        "-af", "silencedetect=n=-45dB:d=2.5,volumedetect",
        "-f", "null", "-"
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out = result.stderr

    has_black = "black_start" in out
    has_freeze = "freeze_start" in out
    has_prolonged_silence = "silence_start" in out

    max_volume = 0.0
    vol_match = re.search(r"max_volume:\s*(-?[\d\.]+)\s*dB", out)
    if vol_match:
        max_volume = float(vol_match.group(1))

    return {
        "has_black_frames": has_black,
        "has_frozen_frames": has_freeze,
        "has_prolonged_silence": has_prolonged_silence,
        "max_volume_db": max_volume,
        "is_clipping": max_volume >= 0.0
    }
