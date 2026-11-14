"""Professional Educational Visual Animation Studio for YouTube Shorts & Long-form.

Inspired by the approved reference style:
- Pitch-black minimalist canvas
- Vibrant yellow stickman character interacting with laptops, physical concept props, and code
- Floating high-contrast syntax-highlighted IDE window
- Live terminal output
- Synchronized educational narration + subtle Foley ASMR sound design
- Sequential episodic linking: Episode N always teases Episode N+1, which executes next
"""

import os
import sys
import math
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary
from backend.app.core.logging import logger
import edge_tts

FFMPEG = get_ffmpeg_binary()
WORKSPACE_DIR = Path(os.getcwd())
STORAGE = WORKSPACE_DIR / "media_storage"
TEMP_DIR = STORAGE / "temp" / "educational_studio"
FRAMES_DIR = TEMP_DIR / "frames"
RENDERED_DIR = STORAGE / "rendered"
SFX_DIR = STORAGE / "assets" / "sfx"

FRAMES_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Reference Palette
BG_DARK = (10, 12, 16)
STICK_YELLOW = (255, 215, 0)
STICK_OUTLINE = (235, 195, 0)
CYAN_ACCENT = (56, 189, 248)
EMERALD_GREEN = (34, 197, 94)
GOLD_VAL = (250, 204, 21)
PURPLE_KEYWORD = (168, 85, 247)
WHITE = (255, 255, 255)
MUTED_GRAY = (148, 163, 184)
PANEL_BG = (18, 22, 30)
PANEL_BORDER = (40, 48, 65)
LAPTOP_SILVER = (190, 200, 215)
DESK_COLOR = (28, 34, 46)


def get_font(family: str, size: int):
    candidates = []
    if family == "mono":
        candidates = ["consola.ttf", "consolab.ttf", "cour.ttf", "courbd.ttf", "LiberationMono-Bold.ttf"]
    elif family == "bold":
        candidates = ["segoepb.ttf", "arialbd.ttf", "calibrib.ttf", "tahomabd.ttf", "LiberationSans-Bold.ttf"]
    else:
        candidates = ["segoeui.ttf", "arial.ttf", "calibri.ttf", "tahoma.ttf", "LiberationSans-Regular.ttf"]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


font_header = get_font("bold", 44)
font_sub = get_font("bold", 28)
font_code = get_font("mono", 46)
font_term = get_font("mono", 42)
font_box_label = get_font("bold", 52)
font_val = get_font("bold", 58)
font_callout = get_font("bold", 34)


# -------------------------------------------------------------
# ARTICULATED YELLOW STICKMAN RIG
# -------------------------------------------------------------
def draw_yellow_stickman(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    action: str = "idle",
    param: float = 0.0,
    face: str = "smile",
    scale: float = 1.75
):
    lw = max(6, int(8 * scale))
    r_head = int(28 * scale)
    h_torso = int(68 * scale)
    l_arm = int(52 * scale)
    l_thigh = int(55 * scale)
    l_calf = int(52 * scale)

    head_x = x
    head_y = y - h_torso - r_head
    torso_top = (x, y - h_torso)
    torso_bot = (x, y)

    # Head
    draw.ellipse(
        [head_x - r_head, head_y - r_head, head_x + r_head, head_y + r_head],
        fill=STICK_YELLOW,
        outline=STICK_OUTLINE,
        width=3
    )

    # Face Expressions
    ew, eh = 4, 6
    if face == "blink":
        draw.line([(head_x - 14, head_y), (head_x - 4, head_y)], fill=(20, 20, 20), width=3)
        draw.line([(head_x + 4, head_y), (head_x + 14, head_y)], fill=(20, 20, 20), width=3)
    elif face == "happy":
        draw.arc([head_x - 16, head_y - 6, head_x - 2, head_y + 8], 180, 360, fill=(20, 20, 20), width=3)
        draw.arc([head_x + 2, head_y - 6, head_x + 16, head_y + 8], 180, 360, fill=(20, 20, 20), width=3)
        draw.arc([head_x - 10, head_y + 6, head_x + 10, head_y + 20], 0, 180, fill=(20, 20, 20), width=3)
    elif face == "curious":
        draw.ellipse([head_x - 14, head_y - 6, head_x - 4, head_y + 6], fill=(20, 20, 20))
        draw.ellipse([head_x + 4, head_y - 10, head_x + 16, head_y + 6], fill=(20, 20, 20))
        draw.arc([head_x - 6, head_y + 8, head_x + 8, head_y + 18], 0, 180, fill=(20, 20, 20), width=2)
    else:  # smile
        draw.ellipse([head_x - 12 - ew, head_y - eh, head_x - 12 + ew, head_y + eh], fill=(20, 20, 20))
        draw.ellipse([head_x + 12 - ew, head_y - eh, head_x + 12 + ew, head_y + eh], fill=(20, 20, 20))
        draw.arc([head_x - 8, head_y + 6, head_x + 8, head_y + 18], 0, 180, fill=(20, 20, 20), width=3)

    # Torso
    draw.line([torso_top, torso_bot], fill=STICK_YELLOW, width=lw)

    # Limbs
    if action == "walk":
        cycle = param * math.pi * 4
        a1, a2 = math.sin(cycle) * 35, -math.sin(cycle) * 35
        draw.line([torso_top, (x + a1, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + a1, y - h_torso * 0.4), (x + a1 * 1.3, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + a2, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + a2, y - h_torso * 0.4), (x + a2 * 1.3, y - 5)], fill=STICK_YELLOW, width=lw)
        l1, l2 = math.sin(cycle) * 45, -math.sin(cycle) * 45
        draw.line([torso_bot, (x + l1, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + l1, y + l_thigh), (x + l1 * 1.2, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + l2, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + l2, y + l_thigh), (x + l2 * 1.2, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    elif action == "typing_at_laptop":
        t_off = math.sin(param * 18) * 4
        draw.line([torso_top, (x - 35, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 35, y - h_torso * 0.5), (x - 70, y - h_torso * 0.3 + t_off)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x - 20, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 20, y - h_torso * 0.4), (x - 55, y - h_torso * 0.2 - t_off)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 45, y + 25)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 45, y + 25), (x - 50, y + 105)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 25, y + 35)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y + 35), (x - 30, y + 115)], fill=STICK_YELLOW, width=lw)

    elif action == "point_right":
        draw.line([torso_top, (x - 25, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y - h_torso * 0.5), (x - 25, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + 50, y - h_torso * 0.8)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 50, y - h_torso * 0.8), (x + 115, y - h_torso * 0.85)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y + l_thigh), (x - 28, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 25, y + l_thigh), (x + 28, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    elif action == "thumbs_up":
        draw.line([torso_top, (x - 35, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 35, y - h_torso * 0.5), (x - 15, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + 45, y - h_torso * 0.6)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 45, y - h_torso * 0.6), (x + 55, y - h_torso - 25)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 55, y - h_torso - 25), (x + 55, y - h_torso - 45)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y + l_thigh), (x - 28, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 25, y + l_thigh), (x + 28, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    else:  # standing idle
        draw.line([torso_top, (x - 25, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y - h_torso * 0.5), (x - 28, y - 10)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + 25, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 25, y - h_torso * 0.5), (x + 28, y - 10)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y + l_thigh), (x - 28, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 25, y + l_thigh), (x + 28, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    return (head_x, head_y)


# -------------------------------------------------------------
# ENVIRONMENT OBJECTS
# -------------------------------------------------------------
def draw_desk_and_laptop(draw: ImageDraw.ImageDraw, desk_x: float, desk_y: float, laptop_open: float = 1.0):
    draw.rounded_rectangle([desk_x, desk_y, desk_x + 360, desk_y + 24], radius=6, fill=DESK_COLOR)
    draw.rectangle([desk_x + 30, desk_y + 24, desk_x + 44, desk_y + 260], fill=(22, 28, 38))
    draw.rectangle([desk_x + 316, desk_y + 24, desk_x + 330, desk_y + 260], fill=(22, 28, 38))

    lap_x, lap_y = desk_x + 80, desk_y - 12
    draw.rounded_rectangle([lap_x, lap_y, lap_x + 180, lap_y + 12], radius=4, fill=LAPTOP_SILVER)

    angle = 1.25 * laptop_open
    lid_len = 120
    screen_top_x = lap_x + 40 - int(math.cos(angle) * lid_len)
    screen_top_y = lap_y - int(math.sin(angle) * lid_len)
    draw.line([(lap_x + 40, lap_y), (screen_top_x, screen_top_y)], fill=LAPTOP_SILVER, width=8)

    if laptop_open > 0.3:
        draw.polygon(
            [(lap_x + 40, lap_y), (screen_top_x, screen_top_y), (lap_x + 140, screen_top_y - 20), (lap_x + 120, lap_y)],
            fill=(40, 60, 90)
        )


def draw_floating_code_editor(draw: ImageDraw.ImageDraw, filename: str, lines: list, highlights: list):
    x0, y0 = 60, 220
    x1, y1 = WIDTH - 60, 560
    draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=PANEL_BG, outline=PANEL_BORDER, width=3)
    draw.rounded_rectangle([x0, y0, x1, y0 + 55], radius=20, fill=(24, 30, 42))
    draw.rectangle([x0, y0 + 35, x1, y0 + 55], fill=(24, 30, 42))
    draw.ellipse([x0 + 25, y0 + 18, x0 + 43, y0 + 36], fill=(239, 68, 68))
    draw.ellipse([x0 + 55, y0 + 18, x0 + 73, y0 + 36], fill=(250, 204, 21))
    draw.ellipse([x0 + 85, y0 + 18, x0 + 103, y0 + 36], fill=(34, 197, 94))
    draw.text((x0 + (x1 - x0) // 2, y0 + 28), f"{filename} — Python", fill=MUTED_GRAY, font=font_sub, anchor="mm")

    cy = y0 + 85
    for idx, (code_text, is_hl) in enumerate(zip(lines, highlights)):
        line_num = f"{idx + 1:2d}  "
        draw.text((x0 + 35, cy), line_num, fill=(80, 95, 120), font=font_code)

        if is_hl:
            draw.rounded_rectangle([x0 + 100, cy - 6, x1 - 35, cy + 50], radius=10, fill=(38, 52, 75))

        draw.text((x0 + 120, cy), code_text, fill=WHITE, font=font_code)
        cy += 65


def draw_terminal_output(draw: ImageDraw.ImageDraw, output_lines: list):
    x0, y0 = 60, 600
    x1, y1 = WIDTH - 60, 760
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(14, 18, 24), outline=PANEL_BORDER, width=2)
    draw.text((x0 + 30, y0 + 30), "Terminal Output", fill=MUTED_GRAY, font=get_font("bold", 24), anchor="lm")
    draw.line([(x0, y0 + 50), (x1, y0 + 50)], fill=(30, 38, 50), width=1)

    cy = y0 + 80
    for l in output_lines:
        draw.text((x0 + 30, cy), ">>> ", fill=(100, 115, 140), font=font_term)
        draw.text((x0 + 130, cy), l, fill=EMERALD_GREEN, font=font_term)
        cy += 50


def draw_callout_banner(draw: ImageDraw.ImageDraw, step_text: str, explanation: str):
    by = 1620
    draw.rounded_rectangle([50, by, WIDTH - 50, by + 230], radius=22, fill=PANEL_BG, outline=CYAN_ACCENT, width=3)
    draw.rounded_rectangle([80, by + 20, 480, by + 75], radius=12, fill=(30, 48, 75))
    draw.text((95, by + 47), step_text, fill=GOLD_VAL, font=font_sub, anchor="lm")
    draw.text((80, by + 115), explanation[:44], fill=WHITE, font=font_callout)
    if len(explanation) > 44:
        draw.text((80, by + 165), explanation[44:90], fill=MUTED_GRAY, font=font_sub)


# -------------------------------------------------------------
# DYNAMIC EDUCATIONAL EPISODE RENDERER
# -------------------------------------------------------------
async def synthesize_narration(text: str, out_path: Path):
    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-AndrewMultilingualNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])


def render_educational_episode(ep_data: Dict[str, Any]) -> str:
    """Master generation function for any curriculum episode (1 to 10,000)."""
    ep_num = ep_data.get("episode", 1)
    title = ep_data.get("title", f"Python Lesson {ep_num}")
    narration_text = ep_data.get("narration_text", "")
    code_lines = ep_data.get("code_lines", [])
    output_lines = ep_data.get("output_lines", [])
    next_teaser = ep_data.get("next_teaser", f"Episode {ep_num + 1}")

    ep_dir = TEMP_DIR / f"ep_{ep_num}"
    ep_frames = ep_dir / "frames"
    ep_frames.mkdir(parents=True, exist_ok=True)
    narration_audio = ep_dir / "narration.mp3"

    print(f"\n==================================================================")
    print(f"🎬 RENDERING EDUCATIONAL EPISODE {ep_num}: {title.upper()}")
    print(f"==================================================================")

    # 1. Synthesize Narration Audio
    if not narration_audio.exists():
        asyncio.run(synthesize_narration(narration_text, narration_audio))

    # 2. Measure Duration
    res = subprocess.run([FFMPEG, "-i", str(narration_audio)], stderr=subprocess.PIPE, text=True)
    duration_sec = 45.0
    for l in res.stderr.splitlines():
        if "Duration" in l:
            try:
                parts = l.split("Duration:")[1].split(",")[0].strip().split(":")
                duration_sec = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            except Exception:
                pass

    total_frames = int(FPS * duration_sec)
    desk_x, desk_y = 120, 1380
    box_x, box_y = 800, 1260

    # 3. Render Frames
    for frame in range(total_frames):
        t = frame / FPS
        p_overall = t / duration_sec

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Subtle dark blueprint grid
        for gy in range(0, HEIGHT, 100):
            draw.line([(0, gy), (WIDTH, gy)], fill=(16, 20, 28), width=1)
        for gx in range(0, WIDTH, 100):
            draw.line([(gx, 0), (gx, HEIGHT)], fill=(16, 20, 28), width=1)

        draw.line([(0, 1580), (WIDTH, 1580)], fill=(35, 45, 60), width=4)

        # Header Pill
        draw.rounded_rectangle([60, 45, WIDTH - 60, 175], radius=20, fill=PANEL_BG, outline=PANEL_BORDER, width=2)
        draw.text((WIDTH // 2, 85), f"PYTHON MASTERCLASS • EPISODE {ep_num}", fill=STICK_YELLOW, font=font_header, anchor="mm")
        draw.text((WIDTH // 2, 135), title[:52], fill=WHITE, font=font_sub, anchor="mm")

        # Code Editor
        hl_idx = min(len(code_lines) - 1, int(p_overall * len(code_lines)))
        highlights = [i == hl_idx for i in range(len(code_lines))]
        draw_floating_code_editor(draw, f"lesson_{ep_num}.py", code_lines, highlights)

        # Terminal Output
        if p_overall > 0.45:
            draw_terminal_output(draw, output_lines)

        # Desk & Laptop
        lap_open = min(1.0, t / 2.0)
        draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=lap_open)

        # Stickman action based on timeline
        if p_overall < 0.2:
            walk_p = min(1.0, t / 3.0)
            sm_x = int(-100 + (desk_x + 280 + 100) * walk_p)
            draw_yellow_stickman(draw, sm_x, 1540, action="walk", param=walk_p, face="smile")
        elif p_overall < 0.5:
            draw_yellow_stickman(draw, desk_x + 280, 1420, action="typing_at_laptop", param=t, face="curious")
        elif p_overall < 0.8:
            draw_yellow_stickman(draw, desk_x + 360, 1540, action="point_right", face="smile")
        else:
            wave_param = (t - duration_sec * 0.8) * 8
            draw_yellow_stickman(draw, 540, 1540, action="thumbs_up", param=wave_param, face="happy")

        # Physical concept prop
        draw.rounded_rectangle([box_x - 120, box_y - 100, box_x + 120, box_y + 100], radius=18, fill=PANEL_BG, outline=CYAN_ACCENT, width=4)
        draw.text((box_x, box_y), f"CONCEPT {ep_num}", fill=CYAN_ACCENT, font=font_box_label, anchor="mm")

        # Next Teaser Banner in last 5 seconds
        if duration_sec - t < 5.0:
            draw.rounded_rectangle([70, 1460, WIDTH - 70, 1560], radius=16, fill=STICK_YELLOW)
            draw.text((WIDTH // 2, 1510), f"FOLLOW FOR {next_teaser.upper()}! 🚀", fill=(20, 20, 20), font=get_font("bold", 32), anchor="mm")

        draw_callout_banner(draw, f"EPISODE {ep_num}", title)

        frame_path = ep_frames / f"frame_{frame:04d}.png"
        img.save(frame_path, format="PNG")

    # 4. Composite Video with FFmpeg
    final_video = RENDERED_DIR / f"educational_python_ep{ep_num}.mp4"
    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", str(ep_frames / "frame_%04d.png"),
        "-i", str(narration_audio),
        "-i", str(SFX_DIR / "whoosh.wav"),
        "-i", str(SFX_DIR / "keyboard.wav"),
        "-i", str(SFX_DIR / "pop.wav"),
        "-i", str(SFX_DIR / "success_ding.wav"),
        "-t", str(duration_sec),
        "-filter_complex",
        (
            "[0:v]fps=30,format=yuv420p[v];"
            "[1:a]volume=1.0[narr];"
            "[2:a]adelay=1500|1500,volume=0.3[s_open];"
            "[3:a]adelay=6000|6000,volume=0.25[s_type];"
            "[4:a]adelay=12000|12000,volume=0.4[s_pop];"
            "[5:a]adelay=20000|20000,volume=0.5[s_ding];"
            "[narr][s_open][s_type][s_pop][s_ding]amix=inputs=5:duration=first:dropout_transition=0[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]
    subprocess.run(cmd, check=True)
    return str(final_video)

