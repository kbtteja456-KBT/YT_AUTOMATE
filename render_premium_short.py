import subprocess
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary

ffmpeg_bin = get_ffmpeg_binary()
temp_dir = Path("media_storage/temp/render_premium")
temp_dir.mkdir(parents=True, exist_ok=True)

# 1. Prepare 4 high quality 1080x1920 scene clips (No glitchy code!)
clips_plan = [
    ("media_storage/assets/tech_bg.mp4", 8.5, temp_dir / "part0.mp4"),
    ("media_storage/assets/clip2.mp4", 11.0, temp_dir / "part1.mp4"),
    ("media_storage/assets/clip3.mp4", 10.5, temp_dir / "part2.mp4"),
    ("media_storage/assets/clip4_clean.mp4", 7.0, temp_dir / "part3.mp4"),
]

for src, dur, out in clips_plan:
    cmd = [
        ffmpeg_bin, "-y",
        "-ss", "0", "-t", str(dur),
        "-i", str(src),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-an",
        str(out)
    ]
    subprocess.run(cmd, check=True)
    print(f"Rendered segment: {out.name}")

# 2. Concat segments together
concat_txt = temp_dir / "concat.txt"
with open(concat_txt, "w", encoding="utf-8") as f:
    for _, _, out in clips_plan:
        f.write(f"file '{out.resolve().as_posix()}'\n")

merged_video = temp_dir / "merged.mp4"
cmd_concat = [
    ffmpeg_bin, "-y",
    "-f", "concat", "-safe", "0",
    "-i", str(concat_txt),
    "-c", "copy",
    str(merged_video)
]
subprocess.run(cmd_concat, check=True)
print("Merged 4 visual segments!")

# 3. Composite audio: Voiceover + Lo-Fi Background Music
mixed_audio = temp_dir / "mixed_audio.mp3"
cmd_audio = [
    ffmpeg_bin, "-y",
    "-i", "media_storage/audio/short_voiceover.mp3",
    "-i", "media_storage/audio/bg_music.mp3",
    "-filter_complex", "[0:a]volume=1.2[v];[1:a]volume=0.15[m];[v][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
    "-map", "[a]",
    "-c:a", "libmp3lame", "-b:a", "192k",
    str(mixed_audio)
]
subprocess.run(cmd_audio, check=True)
print("Mixed voiceover with background music!")

# 4. Final render with burned-in animated subtitles & mixed audio
final_video = Path("media_storage/rendered/short_rendered.mp4")
sub_rel = "media_storage/captions/subtitles.ass"

cmd_final = [
    ffmpeg_bin, "-y",
    "-i", str(merged_video),
    "-i", str(mixed_audio),
    "-vf", f"ass={sub_rel}",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k",
    "-shortest",
    str(final_video)
]
print("Running final composite with animated subtitles & mixed audio...")
subprocess.run(cmd_final, check=True)
print(f"PREMIUM VIDEO RENDERED! Final size: {final_video.stat().st_size} bytes")

# 5. Extract vibrant thumbnail at 10.5s (Robot + Hologram + Title)
thumb_file = Path("media_storage/thumbnails/thumb_test.jpg")
cmd_thumb = [
    ffmpeg_bin, "-y",
    "-ss", "10.5",
    "-i", str(final_video),
    "-vframes", "1",
    "-q:v", "2",
    str(thumb_file)
]
subprocess.run(cmd_thumb, check=True)
print(f"PREMIUM THUMBNAIL EXTRACTED! Size: {thumb_file.stat().st_size} bytes")
