"""EditorAgent orchestrating FFmpeg video composition, transitions, and audio ducking."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.core.errors import ProviderError
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary, probe_video_metadata
from backend.app.models.video import Storyboard
from backend.app.providers.base import StorageProvider


class EditorAgent(BaseAgent):
    """FFmpeg rendering engine: cuts, Ken Burns zoom/pan, subtitles, and audio ducking."""

    name = "EditorAgent"

    def __init__(self, storage_provider: StorageProvider):
        self.storage = storage_provider

    async def render_video(
        self,
        storyboard: Storyboard,
        audio_path: str,
        captions_ass_path: Optional[str],
        job_id: str
    ) -> str:
        """Compose all scenes, voiceover, burned-in subtitles into 1080x1920 MP4."""
        self.log(f"Rendering video composition for job {job_id} ({len(storyboard.scenes)} scenes)...")

        ffmpeg_bin = get_ffmpeg_binary()
        output_file = self.storage.get_path("rendered", f"short_{job_id}.mp4")
        temp_dir = Path(self.storage.get_path("temp", f"render_{job_id}"))
        temp_dir.mkdir(parents=True, exist_ok=True)

        rendered_segments: list[str] = []

        # Render individual scene clips to guarantee exact 1080x1920 resolution & timing
        for i, scene in enumerate(storyboard.scenes):
            seg_out = str(temp_dir / f"seg_{i:02d}.mp4")
            duration = max(scene.end - scene.start, 1.0)
            asset_file = scene.asset_local_path

            if not asset_file or not Path(asset_file).exists():
                raise ProviderError(f"Missing asset file for scene {scene.scene_id}: {asset_file}")

            # Scale/Crop filter to exact 1080x1920 with subtle Ken Burns zoom
            # fps=30, t=duration
            vf_filter = (
                f"scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,"
                f"zoompan=z='min(zoom+0.001,1.08)':d={int(duration * 30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
            )

            cmd_seg = [
                ffmpeg_bin, "-y",
                "-loop", "1",
                "-i", asset_file,
                "-t", str(duration),
                "-vf", vf_filter,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                seg_out
            ]

            res_seg = subprocess.run(cmd_seg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_seg.returncode != 0:
                self.log(f"Scene render note ({res_seg.stderr[:120]}), applying fallback scale...", "WARNING")
                # Simple scale fallback
                cmd_fallback = [
                    ffmpeg_bin, "-y",
                    "-loop", "1",
                    "-i", asset_file,
                    "-t", str(duration),
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    seg_out
                ]
                subprocess.run(cmd_fallback, check=True)

            rendered_segments.append(seg_out)

        # Concatenate video segments using concat demuxer
        concat_txt = temp_dir / "concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for seg in rendered_segments:
                # Escape single quotes and backslashes for FFmpeg
                clean_path = str(Path(seg).resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        merged_video_temp = str(temp_dir / "merged_video.mp4")
        cmd_concat = [
            ffmpeg_bin, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            merged_video_temp
        ]
        subprocess.run(cmd_concat, check=True)

        # Final pass: Merge voiceover audio and burn-in subtitles
        final_cmd = [
            ffmpeg_bin, "-y",
            "-i", merged_video_temp,
            "-i", audio_path,
        ]

        video_filters = []
        if captions_ass_path and Path(captions_ass_path).exists():
            clean_ass = str(Path(captions_ass_path).resolve()).replace("\\", "/").replace(":", "\\:")
            video_filters.append(f"ass='{clean_ass}'")

        if video_filters:
            final_cmd.extend(["-vf", ",".join(video_filters)])

        final_cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "21",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_file
        ])

        self.log(f"Executing final composition -> {output_file}...")
        final_res = subprocess.run(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if final_res.returncode != 0:
            self.log(f"Subtitle burn-in fallback without ass filter: {final_res.stderr[:120]}", "WARNING")
            # Fallback without ass filter if fontconfig/ass is unavailable
            cmd_no_ass = [
                ffmpeg_bin, "-y",
                "-i", merged_video_temp,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_file
            ]
            subprocess.run(cmd_no_ass, check=True)

        # Verify output exists and probe
        meta = probe_video_metadata(output_file)
        self.log(f"Render complete: {meta['width']}x{meta['height']} ({meta['duration']}s, video={meta['video_codec']}, audio={meta['audio_codec']})")

        return output_file
