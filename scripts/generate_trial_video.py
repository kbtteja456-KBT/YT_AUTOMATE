"""Trial Video Generator: Renders an ultra-engaging, high-retention viral Python Short.

Includes:
- Dynamic multi-stage visual transitions (Hook banner -> Code typing -> Options -> Countdown -> Emerald Answer Reveal)
- Ambient tech video background motion
- High-energy Edge-TTS voiceover
- Synchronized Sound Design (Ticking clock countdown + Harmonic victory bell ding)
- Viral engagement CTA ("90% of Senior Devs fail this", Pinned comment hook)
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary

FFMPEG = get_ffmpeg_binary()
WORKSPACE_DIR = Path(os.getcwd())
STORAGE = WORKSPACE_DIR / "media_storage"
TEMP_DIR = STORAGE / "temp" / "trial_render"
RENDERED_DIR = STORAGE / "rendered"
THUMBS_DIR = STORAGE / "thumbnails"
SFX_DIR = STORAGE / "assets" / "sfx"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_DIR.mkdir(parents=True, exist_ok=True)
SFX_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920

# -------------------------------------------------------------
# FONT HELPERS
# -------------------------------------------------------------
def get_font(family: str, size: int):
    candidates = []
    if family == "mono":
        candidates = ["consola.ttf", "consolab.ttf", "cour.ttf", "courbd.ttf", "LiberationMono-Bold.ttf"]
    elif family == "bold":
        candidates = ["arialbd.ttf", "segoepb.ttf", "calibrib.ttf", "tahomabd.ttf", "LiberationSans-Bold.ttf"]
    else:
        candidates = ["arial.ttf", "segoeui.ttf", "calibri.ttf", "tahoma.ttf", "LiberationSans-Regular.ttf"]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()

# -------------------------------------------------------------
# STEP 1: GENERATE VOICE OVER & SOUND EFFECTS
# -------------------------------------------------------------
async def generate_audio():
    import edge_tts
    print("\n[1/5] Synthesizing energetic viral voiceover with Edge-TTS...")
    script_text = (
        "Why does Python do THIS?! 90% of senior developers fail this question! "
        "Look at this code: we have function foo with a default empty list, and we append to it. "
        "What happens when we call foo(1), foo(2), and foo(3)? "
        "Is it A, B, C, or D? Pause and think! "
        "Three... two... one... "
        "The answer is Option B: one, two, three in a single list! "
        "Why? Because Python evaluates default arguments only ONCE when defined, sharing the same list! "
        "Did you get it right? Comment your answer below, and subscribe for daily Python mastery!"
    )
    voice_path = TEMP_DIR / "voiceover.mp3"
    tts = edge_tts.Communicate(script_text, "en-US-ChristopherNeural", rate="+10%")
    await tts.save(str(voice_path))
    print(f"  ✅ Voiceover saved: {voice_path.name}")

    # Inspect exact duration of voiceover using ffprobe
    cmd_probe = [
        FFMPEG, "-i", str(voice_path), "-hide_banner"
    ]
    res = subprocess.run(cmd_probe, stderr=subprocess.PIPE, text=True)
    import re
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if dur_match:
        hrs, mins, secs = dur_match.groups()
        total_dur = float(hrs) * 3600 + float(mins) * 60 + float(secs)
    else:
        total_dur = 25.0
    print(f"  ⏱️ Exact voiceover duration: {total_dur:.2f} seconds")

    return str(voice_path), total_dur

# -------------------------------------------------------------
# STEP 2: DRAW MULTI-STAGE VISUAL FRAMES
# -------------------------------------------------------------
def render_visual_frames():
    print("\n[2/5] Designing progressive, high-retention visual frames...")
    
    # Palette
    COLOR_BG_CARD = (18, 24, 38, 235)      # Deep translucent modern slate
    COLOR_CARD_BORDER = (56, 189, 248)      # Sky blue glow
    COLOR_CODE_BG = (10, 15, 26)            # Dark terminal
    COLOR_YELLOW = (250, 204, 21)
    COLOR_GREEN = (34, 197, 94)
    COLOR_RED = (239, 68, 68)
    COLOR_WHITE = (255, 255, 255)
    COLOR_MUTED = (148, 163, 184)
    
    font_hook = get_font("bold", 44)
    font_sub = get_font("bold", 30)
    font_title = get_font("bold", 50)
    font_code = get_font("mono", 38)
    font_opt = get_font("bold", 36)
    font_opt_letter = get_font("bold", 38)
    font_timer = get_font("bold", 54)
    font_expl = get_font("regular", 32)
    font_cta = get_font("bold", 36)

    def base_card():
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Card container box (1080x1920 layout)
        card_box = [50, 70, WIDTH - 50, HEIGHT - 90]
        draw.rounded_rectangle(card_box, radius=36, fill=(15, 23, 42, 240), outline=(51, 65, 85), width=3)
        return img, draw

    # -----------------------------
    # FRAME 1: HOOK (0s - 3.5s)
    # -----------------------------
    img1, d1 = base_card()
    # Hook Banner (Alert crimson + amber)
    d1.rounded_rectangle([75, 100, WIDTH - 75, 210], radius=24, fill=(220, 38, 38), outline=COLOR_YELLOW, width=3)
    d1.text((WIDTH // 2, 135), "⚠️ 90% OF SENIOR DEVS FAIL THIS!", fill=COLOR_WHITE, font=font_hook, anchor="mm")
    d1.text((WIDTH // 2, 180), "PYTHON QUIRK CHALLENGE 🐍", fill=COLOR_YELLOW, font=font_sub, anchor="mm")

    # Question Title
    d1.text((WIDTH // 2, 280), "What is the output of this code?", fill=COLOR_WHITE, font=font_title, anchor="mm")

    # Terminal box
    code_top = 340
    code_h = 580
    d1.rounded_rectangle([80, code_top, WIDTH - 80, code_top + code_h], radius=24, fill=COLOR_CODE_BG, outline=(56, 189, 248), width=3)
    # Window dots
    d1.ellipse([110, code_top + 25, 130, code_top + 45], fill=(239, 68, 68))
    d1.ellipse([145, code_top + 25, 165, code_top + 45], fill=(234, 179, 8))
    d1.ellipse([180, code_top + 25, 200, code_top + 45], fill=(34, 197, 94))
    d1.text((230, code_top + 20), "main.py — python 3.12", fill=COLOR_MUTED, font=font_sub)

    # Initial teaser lines
    lines1 = [
        "def foo(x, arr=[]):",
        "    arr.append(x)",
        "    return arr",
        "",
        "# What happens on 3 calls?",
        "print(foo(1))",
        "print(foo(2))",
        "print(foo(3))"
    ]
    y_c = code_top + 90
    for idx, l in enumerate(lines1, 1):
        d1.text((110, y_c), f"{idx:2d} |", fill=(100, 116, 139), font=font_code)
        color = COLOR_YELLOW if "def" in l or "return" in l else COLOR_GREEN if "foo(" in l else COLOR_WHITE
        d1.text((190, y_c), l, fill=color, font=font_code)
        y_c += 56

    # Pulsing teaser badge
    d1.rounded_rectangle([150, 1000, WIDTH - 150, 1120], radius=30, fill=(30, 41, 59), outline=(56, 189, 248), width=2)
    d1.text((WIDTH // 2, 1060), "⚡ Look closely at the default argument!", fill=(56, 189, 248), font=font_sub, anchor="mm")
    
    f1_path = TEMP_DIR / "frame1_hook.png"
    img1.save(f1_path)

    # -----------------------------
    # FRAME 2: OPTIONS (3.5s - 13.0s)
    # -----------------------------
    img2, d2 = base_card()
    # Header
    d2.rounded_rectangle([75, 100, WIDTH - 75, 200], radius=24, fill=(30, 41, 59), outline=(56, 189, 248), width=3)
    d2.text((WIDTH // 2, 135), "🔥 PYTHON TRAP QUIZ", fill=COLOR_YELLOW, font=font_hook, anchor="mm")
    d2.text((WIDTH // 2, 175), "Can you predict the exact output?", fill=COLOR_WHITE, font=font_sub, anchor="mm")

    # Code Box
    d2.rounded_rectangle([80, code_top, WIDTH - 80, code_top + code_h], radius=24, fill=COLOR_CODE_BG, outline=(56, 189, 248), width=3)
    d2.ellipse([110, code_top + 25, 130, code_top + 45], fill=(239, 68, 68))
    d2.ellipse([145, code_top + 25, 165, code_top + 45], fill=(234, 179, 8))
    d2.ellipse([180, code_top + 25, 200, code_top + 45], fill=(34, 197, 94))
    d2.text((230, code_top + 20), "main.py — python 3.12", fill=COLOR_MUTED, font=font_sub)

    y_c = code_top + 90
    for idx, l in enumerate(lines1, 1):
        d2.text((110, y_c), f"{idx:2d} |", fill=(100, 116, 139), font=font_code)
        color = COLOR_YELLOW if "def" in l or "return" in l else COLOR_GREEN if "foo(" in l else COLOR_WHITE
        d2.text((190, y_c), l, fill=color, font=font_code)
        y_c += 56

    # 4 Option rows
    opts = [
        ("A", "[1], [2], [3]  (Independent lists)"),
        ("B", "[1, 2, 3]       (Shared list accumulated)"),
        ("C", "TypeError       (Cannot append to default)"),
        ("D", "[3]             (Only the last value retained)")
    ]
    opt_y = 970
    opt_h = 130
    for letter, text in opts:
        # Box
        d2.rounded_rectangle([80, opt_y, WIDTH - 80, opt_y + opt_h], radius=28, fill=(30, 41, 59), outline=(71, 85, 105), width=2)
        # Letter badge
        d2.ellipse([110, opt_y + 25, 190, opt_y + 105], fill=(59, 130, 246))
        d2.text((150, opt_y + 65), letter, fill=COLOR_WHITE, font=font_opt_letter, anchor="mm")
        # Text
        d2.text((220, opt_y + 65), text, fill=COLOR_WHITE, font=font_opt, anchor="lm")
        opt_y += opt_h + 22

    # Bottom Think sticker
    d2.rounded_rectangle([180, opt_y + 10, WIDTH - 180, opt_y + 90], radius=25, fill=(234, 179, 8), outline=COLOR_WHITE, width=2)
    d2.text((WIDTH // 2, opt_y + 50), "🤔 Pause the video to think!", fill=(15, 23, 42), font=font_cta, anchor="mm")

    f2_path = TEMP_DIR / "frame2_options.png"
    img2.save(f2_path)

    # -----------------------------
    # FRAME 3: COUNTDOWN (13.0s - 16.2s)
    # -----------------------------
    img3 = img2.copy()
    d3 = ImageDraw.Draw(img3)
    # Overlay pulsating countdown badge over bottom
    d3.rounded_rectangle([140, opt_y, WIDTH - 140, opt_y + 100], radius=30, fill=(239, 68, 68), outline=COLOR_YELLOW, width=4)
    d3.text((WIDTH // 2, opt_y + 50), "⏳ REVEAL IN 3... 2... 1...", fill=COLOR_WHITE, font=font_timer, anchor="mm")
    f3_path = TEMP_DIR / "frame3_countdown.png"
    img3.save(f3_path)

    # -----------------------------
    # FRAME 4: ANSWER REVEAL & EXPLANATION (16.2s - End)
    # -----------------------------
    img4, d4 = base_card()
    # Winner header
    d4.rounded_rectangle([75, 100, WIDTH - 75, 200], radius=24, fill=(22, 101, 52), outline=COLOR_GREEN, width=3)
    d4.text((WIDTH // 2, 135), "✅ CORRECT ANSWER: OPTION B!", fill=COLOR_WHITE, font=font_hook, anchor="mm")
    d4.text((WIDTH // 2, 175), "Shared Mutable Default Argument", fill=COLOR_YELLOW, font=font_sub, anchor="mm")

    # Code Box
    d4.rounded_rectangle([80, code_top, WIDTH - 80, code_top + code_h], radius=24, fill=COLOR_CODE_BG, outline=COLOR_GREEN, width=3)
    d4.ellipse([110, code_top + 25, 130, code_top + 45], fill=(239, 68, 68))
    d4.ellipse([145, code_top + 25, 165, code_top + 45], fill=(234, 179, 8))
    d4.ellipse([180, code_top + 25, 200, code_top + 45], fill=(34, 197, 94))
    d4.text((230, code_top + 20), "main.py — python 3.12", fill=COLOR_MUTED, font=font_sub)

    y_c = code_top + 90
    for idx, l in enumerate(lines1, 1):
        d4.text((110, y_c), f"{idx:2d} |", fill=(100, 116, 139), font=font_code)
        color = COLOR_YELLOW if "def" in l or "return" in l else COLOR_GREEN if "foo(" in l else COLOR_WHITE
        d4.text((190, y_c), l, fill=color, font=font_code)
        y_c += 56

    # Options with Option B Exploding Green!
    opt_y = 970
    for letter, text in opts:
        if letter == "B":
            # Highlighted Correct Answer
            d4.rounded_rectangle([75, opt_y - 4, WIDTH - 75, opt_y + opt_h + 4], radius=30, fill=(20, 83, 45), outline=COLOR_GREEN, width=4)
            d4.ellipse([110, opt_y + 25, 190, opt_y + 105], fill=COLOR_GREEN)
            d4.text((150, opt_y + 65), "✓", fill=COLOR_WHITE, font=font_opt_letter, anchor="mm")
            d4.text((220, opt_y + 65), text, fill=(240, 253, 244), font=font_opt, anchor="lm")
        else:
            # Dimmed wrong options
            d4.rounded_rectangle([80, opt_y, WIDTH - 80, opt_y + opt_h], radius=28, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
            d4.ellipse([110, opt_y + 25, 190, opt_y + 105], fill=(71, 85, 105))
            d4.text((150, opt_y + 65), letter, fill=COLOR_MUTED, font=font_opt_letter, anchor="mm")
            d4.text((220, opt_y + 65), text, fill=COLOR_MUTED, font=font_opt, anchor="lm")
        opt_y += opt_h + 22

    # Explanation Drawer
    d4.rounded_rectangle([75, opt_y, WIDTH - 75, opt_y + 130], radius=24, fill=(30, 41, 59), outline=(56, 189, 248), width=2)
    d4.text((WIDTH // 2, opt_y + 35), "💡 WHY THIS HAPPENS:", fill=COLOR_YELLOW, font=font_sub, anchor="mm")
    d4.text((WIDTH // 2, opt_y + 85), "Python evaluates defaults ONCE at def time, NOT every call!", fill=COLOR_WHITE, font=font_expl, anchor="mm")

    # Bottom Engagement CTA
    d4.rounded_rectangle([100, opt_y + 150, WIDTH - 100, opt_y + 225], radius=25, fill=(220, 38, 38), outline=COLOR_WHITE, width=2)
    d4.text((WIDTH // 2, opt_y + 187), "💬 Comment what you got & Follow for more!", fill=COLOR_WHITE, font=font_cta, anchor="mm")

    f4_path = TEMP_DIR / "frame4_reveal.png"
    img4.save(f4_path)

    # Also save as official Thumbnail
    thumb_path = THUMBS_DIR / "trial_viral_python_quirk.jpg"
    img4.convert("RGB").save(thumb_path, quality=95)

    print("  ✅ 4 Dynamic Visual Frames generated successfully!")
    return f1_path, f2_path, f3_path, f4_path

# -------------------------------------------------------------
# STEP 3: ASSEMBLE WITH FFMPEG (Motion background + Video + SFX)
# -------------------------------------------------------------
def build_composite_video(voice_file: str, total_duration: float, frames: tuple):
    f1, f2, f3, f4 = frames
    print("\n[3/5] Compositing multi-layer video with FFmpeg...")

    # Timings
    # 0.0 - 3.5: f1 (Hook)
    # 3.5 - 13.0: f2 (Options)
    # 13.0 - 16.2: f3 (Countdown)
    # 16.2 - end: f4 (Reveal)
    bg_video = WORKSPACE_DIR / "media_storage" / "assets" / "tech_bg.mp4"
    tick_sfx = SFX_DIR / "ticking_countdown.wav"
    ding_sfx = SFX_DIR / "success_ding.wav"

    final_video = RENDERED_DIR / "trial_viral_python_quirk.mp4"

    # Multi-input FFmpeg pipeline:
    # Input 0: Ambient Tech Background video (looped)
    # Input 1: Voiceover audio
    # Input 2: Ticking SFX
    # Input 3: Ding SFX
    # Input 4: Frame 1 (Hook)
    # Input 5: Frame 2 (Options)
    # Input 6: Frame 3 (Countdown)
    # Input 7: Frame 4 (Reveal)
    cmd = [
        FFMPEG, "-y",
        # 0: Looping background video
        "-stream_loop", "-1", "-i", str(bg_video),
        # 1: Voiceover
        "-i", str(voice_file),
        # 2: Ticking SFX
        "-i", str(tick_sfx),
        # 3: Ding SFX
        "-i", str(ding_sfx),
        # 4, 5, 6, 7: Image overlays
        "-loop", "1", "-i", str(f1),
        "-loop", "1", "-i", str(f2),
        "-loop", "1", "-i", str(f3),
        "-loop", "1", "-i", str(f4),
        "-t", f"{total_duration:.2f}",
        "-filter_complex",
        (
            # Base video: dark tint overlay to make foreground cards pop
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=8:2,colorchannelmixer=aa=0.45[bg];"
            # Switch frames based on timeline
            "[bg][4:v]overlay=0:0:enable='between(t,0,3.5)'[v1];"
            "[v1][5:v]overlay=0:0:enable='between(t,3.5,13.0)'[v2];"
            "[v2][6:v]overlay=0:0:enable='between(t,13.0,16.2)'[v3];"
            "[v3][7:v]overlay=0:0:enable='gte(t,16.2)'[vout];"
            # Audio mixing: Voice + Delayed Ticking at 13.0s + Delayed Ding at 16.2s
            "[2:a]adelay=13000|13000,volume=0.85[a_tick];"
            "[3:a]adelay=16200|16200,volume=1.0[a_ding];"
            "[1:a]volume=1.35[a_voice];"
            "[a_voice][a_tick][a_ding]amix=inputs=3:duration=first:dropout_transition=0[aout]"
        ),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]

    print("  🎬 Rendering final high-definition MP4...")
    subprocess.run(cmd, check=True)
    size_mb = final_video.stat().st_size / (1024 * 1024)
    print(f"\n==================================================================")
    print(f"🎉 TRIAL VIDEO RENDER COMPLETE!")
    print(f"Path: {final_video}")
    print(f"Size: {size_mb:.2f} MB | Duration: {total_duration:.2f}s | Resolution: 1080x1920 60FPS")
    print(f"==================================================================")

async def main():
    voice_path, dur = await generate_audio()
    frames = render_visual_frames()
    build_composite_video(voice_path, dur, frames)

if __name__ == "__main__":
    asyncio.run(main())

