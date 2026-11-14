"""Educational Visual Animation Generator.
Concept: Episode 2 - The 4 Fundamental Python Data Types (int, float, str, bool)
Style: Pitch black background, yellow stickman, laptop interactions, physical container props,
syntax-highlighted floating code editor, live terminal output, synchronized Foley sound design.
"""

import os
import sys
import math
import subprocess
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary

FFMPEG = get_ffmpeg_binary()
WORKSPACE_DIR = Path(os.getcwd())
STORAGE = WORKSPACE_DIR / "media_storage"
TEMP_DIR = STORAGE / "temp" / "educational_ep2"
FRAMES_DIR = TEMP_DIR / "frames"
RENDERED_DIR = STORAGE / "rendered"
THUMBNAILS_DIR = STORAGE / "thumbnails"
SFX_DIR = STORAGE / "assets" / "sfx"

FRAMES_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_SECONDS = 51.98
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Color Palette
BG_DARK = (10, 12, 16)
STICK_YELLOW = (255, 215, 0)
STICK_OUTLINE = (235, 195, 0)
CYAN_ACCENT = (56, 189, 248)
EMERALD_GREEN = (34, 197, 94)
GOLD_VAL = (250, 204, 21)
PURPLE_STR = (192, 132, 252)
RED_BOOL = (248, 113, 113)
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
font_code = get_font("mono", 40)
font_term = get_font("mono", 40)
font_prop_title = get_font("bold", 36)
font_prop_val = get_font("mono", 44)
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

    # Limbs based on action
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
        draw.line([(x + 50, y - h_torso * 0.8), (x + 120, y - h_torso * 0.9)], fill=STICK_YELLOW, width=lw)
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


def draw_floating_code_editor(draw: ImageDraw.ImageDraw, lines: list, highlights: list):
    x0, y0 = 60, 220
    x1, y1 = WIDTH - 60, 580
    draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=PANEL_BG, outline=PANEL_BORDER, width=3)
    draw.rounded_rectangle([x0, y0, x1, y0 + 55], radius=20, fill=(24, 30, 42))
    draw.rectangle([x0, y0 + 35, x1, y0 + 55], fill=(24, 30, 42))
    draw.ellipse([x0 + 25, y0 + 18, x0 + 43, y0 + 36], fill=(239, 68, 68))
    draw.ellipse([x0 + 55, y0 + 18, x0 + 73, y0 + 36], fill=(250, 204, 21))
    draw.ellipse([x0 + 85, y0 + 18, x0 + 103, y0 + 36], fill=(34, 197, 94))
    draw.text((x0 + (x1 - x0) // 2, y0 + 28), "lesson_2_datatypes.py — Python", fill=MUTED_GRAY, font=font_sub, anchor="mm")

    cy = y0 + 80
    for idx, (code_text, is_hl) in enumerate(zip(lines, highlights)):
        line_num = f"{idx + 1:2d}  "
        draw.text((x0 + 30, cy), line_num, fill=(80, 95, 120), font=font_code)

        if is_hl:
            draw.rounded_rectangle([x0 + 95, cy - 6, x1 - 30, cy + 48], radius=8, fill=(38, 52, 75))

        # Basic syntax color matching
        if "#" in code_text:
            parts = code_text.split("#")
            draw.text((x0 + 110, cy), parts[0], fill=WHITE, font=font_code)
            w_code = draw.textlength(parts[0], font=font_code)
            draw.text((x0 + 110 + w_code, cy), "#" + parts[1], fill=(110, 130, 160), font=font_code)
        elif "print" in code_text:
            draw.text((x0 + 110, cy), "print", fill=CYAN_ACCENT, font=font_code)
            rest = code_text[5:]
            draw.text((x0 + 110 + draw.textlength("print", font=font_code), cy), rest, fill=WHITE, font=font_code)
        else:
            draw.text((x0 + 110, cy), code_text, fill=WHITE, font=font_code)

        cy += 58


def draw_terminal_output(draw: ImageDraw.ImageDraw, output_lines: list):
    x0, y0 = 60, 610
    x1, y1 = WIDTH - 60, 770
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(14, 18, 24), outline=PANEL_BORDER, width=2)
    draw.text((x0 + 30, y0 + 28), "Terminal Output", fill=MUTED_GRAY, font=get_font("bold", 24), anchor="lm")
    draw.line([(x0, y0 + 46), (x1, y0 + 46)], fill=(30, 38, 50), width=1)

    cy = y0 + 72
    for l in output_lines:
        draw.text((x0 + 30, cy), ">>> ", fill=(100, 115, 140), font=font_term)
        draw.text((x0 + 130, cy), l, fill=EMERALD_GREEN, font=font_term)
        cy += 48


# -------------------------------------------------------------
# PHYSICAL DATA TYPE PROPS (RIGHT COLUMN)
# -------------------------------------------------------------
def draw_datatype_props(draw: ImageDraw.ImageDraw, active_type: str, anim_p: float):
    """Draws visual conceptual containers for the 4 core data types."""
    px = 750
    py_int = 900
    py_flt = 1060
    py_str = 1220
    py_bol = 1380
    w_card = 280
    h_card = 120

    # 1. INT CONTAINER (Solid Integer Block)
    is_sel = (active_type == "int")
    bd_color = CYAN_ACCENT if is_sel else PANEL_BORDER
    bg_color = (25, 45, 65) if is_sel else PANEL_BG
    draw.rounded_rectangle([px - w_card // 2, py_int - h_card // 2, px + w_card // 2, py_int + h_card // 2], radius=14, fill=bg_color, outline=bd_color, width=3 if is_sel else 1)
    draw.text((px, py_int - 25), "int (Integer)", fill=CYAN_ACCENT if is_sel else MUTED_GRAY, font=font_prop_title, anchor="mm")
    draw.text((px, py_int + 22), "age = 25", fill=WHITE, font=font_prop_val, anchor="mm")
    if is_sel:
        # Highlight glow indicator
        draw.ellipse([px + w_card // 2 - 24, py_int - h_card // 2 + 12, px + w_card // 2 - 10, py_int - h_card // 2 + 26], fill=CYAN_ACCENT)

    # 2. FLOAT CONTAINER (Decimal Precision Beaker)
    is_sel = (active_type == "float")
    bd_color = EMERALD_GREEN if is_sel else PANEL_BORDER
    bg_color = (20, 50, 40) if is_sel else PANEL_BG
    draw.rounded_rectangle([px - w_card // 2, py_flt - h_card // 2, px + w_card // 2, py_flt + h_card // 2], radius=14, fill=bg_color, outline=bd_color, width=3 if is_sel else 1)
    draw.text((px, py_flt - 25), "float (Decimal)", fill=EMERALD_GREEN if is_sel else MUTED_GRAY, font=font_prop_title, anchor="mm")
    draw.text((px, py_flt + 22), "price = 19.99", fill=WHITE, font=font_prop_val, anchor="mm")
    if is_sel:
        draw.ellipse([px + w_card // 2 - 24, py_flt - h_card // 2 + 12, px + w_card // 2 - 10, py_flt - h_card // 2 + 26], fill=EMERALD_GREEN)

    # 3. STR CONTAINER (Quoted Text Ribbon)
    is_sel = (active_type == "str")
    bd_color = PURPLE_STR if is_sel else PANEL_BORDER
    bg_color = (45, 30, 65) if is_sel else PANEL_BG
    draw.rounded_rectangle([px - w_card // 2, py_str - h_card // 2, px + w_card // 2, py_str + h_card // 2], radius=14, fill=bg_color, outline=bd_color, width=3 if is_sel else 1)
    draw.text((px, py_str - 25), "str (String)", fill=PURPLE_STR if is_sel else MUTED_GRAY, font=font_prop_title, anchor="mm")
    draw.text((px, py_str + 22), 'name = "Dev"', fill=WHITE, font=font_prop_val, anchor="mm")
    if is_sel:
        draw.ellipse([px + w_card // 2 - 24, py_str - h_card // 2 + 12, px + w_card // 2 - 10, py_str - h_card // 2 + 26], fill=PURPLE_STR)

    # 4. BOOL CONTAINER (Power Toggle Switch)
    is_sel = (active_type == "bool")
    bd_color = GOLD_VAL if is_sel else PANEL_BORDER
    bg_color = (55, 45, 20) if is_sel else PANEL_BG
    draw.rounded_rectangle([px - w_card // 2, py_bol - h_card // 2, px + w_card // 2, py_bol + h_card // 2], radius=14, fill=bg_color, outline=bd_color, width=3 if is_sel else 1)
    draw.text((px, py_bol - 25), "bool (Boolean)", fill=GOLD_VAL if is_sel else MUTED_GRAY, font=font_prop_title, anchor="mm")
    draw.text((px, py_bol + 22), "is_coder = True", fill=WHITE, font=font_prop_val, anchor="mm")
    if is_sel:
        draw.ellipse([px + w_card // 2 - 24, py_bol - h_card // 2 + 12, px + w_card // 2 - 10, py_bol - h_card // 2 + 26], fill=GOLD_VAL)


def draw_callout_banner(draw: ImageDraw.ImageDraw, step_text: str, explanation: str):
    by = 1620
    draw.rounded_rectangle([50, by, WIDTH - 50, by + 230], radius=22, fill=PANEL_BG, outline=CYAN_ACCENT, width=3)
    draw.rounded_rectangle([80, by + 20, 500, by + 75], radius=12, fill=(30, 48, 75))
    draw.text((95, by + 47), step_text, fill=GOLD_VAL, font=font_sub, anchor="lm")
    draw.text((80, by + 115), explanation[:44], fill=WHITE, font=font_callout)
    if len(explanation) > 44:
        draw.text((80, by + 165), explanation[44:90], fill=MUTED_GRAY, font=font_sub)


# -------------------------------------------------------------
# MAIN COMPOSITING LOOP
# -------------------------------------------------------------
def render_episode_2():
    print(f"\n==================================================================")
    print(f"🎬 RENDERING EDUCATIONAL EPISODE 2: PYTHON DATA TYPES")
    print(f"Total Duration: {TOTAL_SECONDS:.2f}s | FPS: {FPS} | Total Frames: {TOTAL_FRAMES}")
    print(f"==================================================================")

    desk_x, desk_y = 100, 1380
    narration_audio = STORAGE / "temp" / "ep2_audio.mp3"

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Dark blueprint grid
        for gy in range(0, HEIGHT, 100):
            draw.line([(0, gy), (WIDTH, gy)], fill=(16, 20, 28), width=1)
        for gx in range(0, WIDTH, 100):
            draw.line([(gx, 0), (gx, HEIGHT)], fill=(16, 20, 28), width=1)

        # Floor line
        draw.line([(0, 1580), (WIDTH, 1580)], fill=(35, 45, 60), width=4)

        # Top Header Pill
        draw.rounded_rectangle([60, 45, WIDTH - 60, 175], radius=20, fill=PANEL_BG, outline=PANEL_BORDER, width=2)
        draw.text((WIDTH // 2, 85), "PYTHON FOR BEGINNERS • LESSON 2", fill=STICK_YELLOW, font=font_header, anchor="mm")
        draw.text((WIDTH // 2, 135), "The 4 Fundamental Data Types (int, float, str, bool)", fill=WHITE, font=font_sub, anchor="mm")

        # -------------------------------------------------------------
        # SYNCHRONIZED TIMELINE (51.98s total)
        # -------------------------------------------------------------

        # --- BEAT 1: 0.0s - 7.0s ("Welcome to Lesson 2! In Python, every piece of data has a specific type...") ---
        if t < 7.0:
            lines = ["# The 4 Core Python Data Types", "# int, float, str, bool"]
            draw_floating_code_editor(draw, lines, [False, False])
            draw_datatype_props(draw, active_type="none", anim_p=0.0)

            if t < 3.0:
                walk_p = t / 3.0
                sm_x = int(-100 + (desk_x + 280 + 100) * walk_p)
                draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=0.0)
                draw_yellow_stickman(draw, sm_x, 1540, action="walk", param=walk_p, face="smile")
            else:
                open_p = min(1.0, (t - 3.0) / 1.5)
                draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=open_p)
                draw_yellow_stickman(draw, desk_x + 280, 1420, action="typing_at_laptop", param=t, face="happy")

            draw_callout_banner(draw, "STEP 1: INTRODUCTION", "Every value in Python belongs to a type that defines what it can do!")

        # --- BEAT 2: 7.0s - 14.5s ("First, we have Integers: whole numbers without any decimal points...") ---
        elif t < 14.5:
            lines = ["age = 25          # int (whole number)"]
            draw_floating_code_editor(draw, lines, [True])
            draw_datatype_props(draw, active_type="int", anim_p=min(1.0, (t - 7.0) / 1.0))
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_yellow_stickman(draw, desk_x + 360, 1540, action="point_right", face="smile")

            # Beam pointing to int box
            draw.line([(desk_x + 480, 1400), (610, 900)], fill=CYAN_ACCENT, width=3)
            draw_callout_banner(draw, "TYPE 1: INTEGER (int)", "Whole numbers without decimals. Used for counting, age, and indexing!")

        # --- BEAT 3: 14.5s - 22.0s ("Second, Floats: numbers with decimals, like price equals 19.99...") ---
        elif t < 22.0:
            lines = [
                "age = 25          # int",
                "price = 19.99     # float (decimal)"
            ]
            draw_floating_code_editor(draw, lines, [False, True])
            draw_datatype_props(draw, active_type="float", anim_p=min(1.0, (t - 14.5) / 1.0))
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_yellow_stickman(draw, desk_x + 360, 1540, action="point_right", face="curious")

            # Beam pointing to float box
            draw.line([(desk_x + 480, 1400), (610, 1060)], fill=EMERALD_GREEN, width=3)
            draw_callout_banner(draw, "TYPE 2: FLOAT (float)", "Numbers with decimal precision. Used for money, measurements, and scientific calculations!")

        # --- BEAT 4: 22.0s - 29.5s ("Third, Strings: text wrapped inside quotes, like name equals Dev...") ---
        elif t < 29.5:
            lines = [
                "age = 25          # int",
                "price = 19.99     # float",
                'name = "Dev"      # str (text in quotes)'
            ]
            draw_floating_code_editor(draw, lines, [False, False, True])
            draw_datatype_props(draw, active_type="str", anim_p=min(1.0, (t - 22.0) / 1.0))
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_yellow_stickman(draw, desk_x + 360, 1540, action="point_right", face="smile")

            # Beam pointing to str box
            draw.line([(desk_x + 480, 1400), (610, 1220)], fill=PURPLE_STR, width=3)
            draw_callout_banner(draw, "TYPE 3: STRING (str)", "Text wrapped in quotes! Quotes distinguish string text from code identifiers.")

        # --- BEAT 5: 29.5s - 37.0s ("And fourth, Booleans: which can only be True or False...") ---
        elif t < 37.0:
            lines = [
                "age = 25          # int",
                "price = 19.99     # float",
                'name = "Dev"      # str',
                "is_coder = True   # bool (True/False)"
            ]
            draw_floating_code_editor(draw, lines, [False, False, False, True])
            draw_datatype_props(draw, active_type="bool", anim_p=min(1.0, (t - 29.5) / 1.0))
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_yellow_stickman(draw, desk_x + 360, 1540, action="point_right", face="happy")

            # Beam pointing to bool box
            draw.line([(desk_x + 480, 1400), (610, 1380)], fill=GOLD_VAL, width=3)
            draw_callout_banner(draw, "TYPE 4: BOOLEAN (bool)", "Strict binary state: True or False. Powers every conditional if-else check!")

        # --- BEAT 6: 37.0s - 45.0s ("You can check any variable's type using Python's built-in type function...") ---
        elif t < 45.0:
            lines = [
                "age = 25",
                'name = "Dev"',
                "print(type(age))",
                "print(type(name))"
            ]
            draw_floating_code_editor(draw, lines, [False, False, True, True])
            draw_datatype_props(draw, active_type="all", anim_p=1.0)

            # Terminal execution
            draw_terminal_output(draw, ["<class 'int'>", "<class 'str'>"])

            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_yellow_stickman(draw, desk_x + 280, 1420, action="typing_at_laptop", param=t, face="happy")

            draw_callout_banner(draw, "THE type() INSPECTOR", "Calling type(x) reveals the underlying class: <class 'int'> or <class 'str'>!")

        # --- BEAT 7: 45.0s - 51.98s ("Subscribe now, and follow for Lesson 3 where we master user input...") ---
        else:
            lines = [
                "age = 25",
                'name = "Dev"',
                "print(type(age))",
                "print(type(name))"
            ]
            draw_floating_code_editor(draw, lines, [False, False, False, False])
            draw_terminal_output(draw, ["<class 'int'>", "<class 'str'>"])
            draw_datatype_props(draw, active_type="all", anim_p=1.0)

            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            # Stickman celebration & thumbs up
            draw_yellow_stickman(draw, 520, 1540, action="thumbs_up", face="happy")

            # Next Episode Teaser Banner
            draw.rounded_rectangle([60, 1450, WIDTH - 60, 1565], radius=18, fill=STICK_YELLOW)
            draw.text((WIDTH // 2, 1507), "FOLLOW FOR LESSON 3: TAKING USER INPUT! 🚀", fill=(20, 20, 20), font=get_font("bold", 34), anchor="mm")

            draw_callout_banner(draw, "LESSON 2 COMPLETE!", "Next up: Interactive programs with input() and type conversion!")

        frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
        img.save(frame_path, format="PNG")

        if frame % 150 == 0:
            print(f"  Frame {frame}/{TOTAL_FRAMES} rendered ({t:.1f}s / {TOTAL_SECONDS:.1f}s)")

    print(f"✅ All {TOTAL_FRAMES} frames successfully rendered!")

    # Composite with FFmpeg and Foley SFX
    final_video = RENDERED_DIR / "educational_python_ep2.mp4"
    ultimate_video = RENDERED_DIR / "alan_becker_python_ep2_ultimate.mp4"

    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(narration_audio),
        "-i", str(SFX_DIR / "whoosh.wav"),
        "-i", str(SFX_DIR / "pop.wav"),
        "-i", str(SFX_DIR / "zap.wav"),
        "-i", str(SFX_DIR / "keyboard.wav"),
        "-i", str(SFX_DIR / "success_ding.wav"),
        "-i", str(SFX_DIR / "chime.wav"),
        "-t", str(TOTAL_SECONDS),
        "-filter_complex",
        (
            "[0:v]fps=30,format=yuv420p[v];"
            "[1:a]volume=1.0[narr];"
            "[2:a]adelay=3000|3000,volume=0.35[s_open];"
            "[3:a]adelay=7200|7200,volume=0.4[s_pop1];"
            "[4:a]adelay=29800|29800,volume=0.35[s_zap];"
            "[5:a]adelay=37200|37200,volume=0.3[s_key];"
            "[6:a]adelay=39500|39500,volume=0.5[s_ding];"
            "[7:a]adelay=45200|45200,volume=0.4[s_chime];"
            "[narr][s_open][s_pop1][s_zap][s_key][s_ding][s_chime]amix=inputs=7:duration=first:dropout_transition=0[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]

    print(f"\nEncoding final video with FFmpeg...")
    subprocess.run(cmd, check=True)
    print(f"🎉 Final Video saved to: {final_video}")

    # Also save as alan_becker_python_ep2_ultimate.mp4 for backward-compatibility with orchestrator
    import shutil
    shutil.copy2(str(final_video), str(ultimate_video))
    print(f"🎉 Copied to: {ultimate_video}")

    # Generate custom high-CTR thumbnail for Episode 2
    thumb_path = THUMBNAILS_DIR / "educational_ep2.jpg"
    thumb_ultimate = THUMBNAILS_DIR / "alan_becker_ultimate_ep2.jpg"
    # Select frame around 38s where terminal and all types are active
    thumb_frame_path = FRAMES_DIR / f"frame_{int(38.5 * FPS):04d}.png"
    if thumb_frame_path.exists():
        thumb_img = Image.open(thumb_frame_path).convert("RGB")
        thumb_img.save(thumb_path, "JPEG", quality=95)
        thumb_img.save(thumb_ultimate, "JPEG", quality=95)
        print(f"📸 Thumbnail saved to: {thumb_path}")


if __name__ == "__main__":
    render_episode_2()

