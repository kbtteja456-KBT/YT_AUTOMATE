"""Professional Educational Visual Animation Generator.
Concept: Python Variables (Lesson 1)
Style Reference: Dark minimalist background, yellow stickman, laptop interaction, physical variable box, synchronized code execution & educational narration.
"""

import os
import sys
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary

FFMPEG = get_ffmpeg_binary()
WORKSPACE_DIR = Path(os.getcwd())
STORAGE = WORKSPACE_DIR / "media_storage"
TEMP_DIR = STORAGE / "temp" / "educational_trial"
FRAMES_DIR = TEMP_DIR / "frames"
RENDERED_DIR = STORAGE / "rendered"
SFX_DIR = STORAGE / "assets" / "sfx"

FRAMES_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_SECONDS = 48.2
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Colors matching the reference video:
BG_DARK = (10, 12, 16)
STICK_YELLOW = (255, 215, 0)       # Vibrant reference yellow
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
font_box_label = get_font("bold", 56)
font_val = get_font("bold", 64)
font_callout = get_font("bold", 34)


# -------------------------------------------------------------
# ARTICULATED YELLOW STICKMAN (MATCHING REFERENCE VIDEO)
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

    # Head (Solid Vibrant Yellow)
    draw.ellipse(
        [head_x - r_head, head_y - r_head, head_x + r_head, head_y + r_head],
        fill=STICK_YELLOW,
        outline=STICK_OUTLINE,
        width=3
    )

    # Eyes
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

    # Actions & Limbs
    if action == "walk":
        cycle = param * math.pi * 4
        # Arms swinging
        a1 = math.sin(cycle) * 35
        a2 = -math.sin(cycle) * 35
        draw.line([torso_top, (x + a1, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + a1, y - h_torso * 0.4), (x + a1 * 1.3, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + a2, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + a2, y - h_torso * 0.4), (x + a2 * 1.3, y - 5)], fill=STICK_YELLOW, width=lw)
        # Legs walking
        l1 = math.sin(cycle) * 45
        l2 = -math.sin(cycle) * 45
        draw.line([torso_bot, (x + l1, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + l1, y + l_thigh), (x + l1 * 1.2, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + l2, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + l2, y + l_thigh), (x + l2 * 1.2, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    elif action == "typing_at_laptop":
        # Sitting at desk typing on laptop
        t_off = math.sin(param * 18) * 4
        # Arms bent towards laptop keyboard
        draw.line([torso_top, (x - 35, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 35, y - h_torso * 0.5), (x - 70, y - h_torso * 0.3 + t_off)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x - 20, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 20, y - h_torso * 0.4), (x - 55, y - h_torso * 0.2 - t_off)], fill=STICK_YELLOW, width=lw)
        # Sitting legs
        draw.line([torso_bot, (x - 45, y + 25)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 45, y + 25), (x - 50, y + 105)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 25, y + 35)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y + 35), (x - 30, y + 115)], fill=STICK_YELLOW, width=lw)

    elif action == "point_right":
        # Right arm pointing to variable box
        draw.line([torso_top, (x - 25, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y - h_torso * 0.5), (x - 25, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + 50, y - h_torso * 0.8)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 50, y - h_torso * 0.8), (x + 115, y - h_torso * 0.85)], fill=STICK_YELLOW, width=lw)
        # Legs standing
        draw.line([torso_bot, (x - 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y + l_thigh), (x - 28, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 25, y + l_thigh), (x + 28, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    elif action == "place_in_box":
        # Hands carrying and lowering value into box
        p = min(1.0, max(0.0, param))
        reach_y = int(-h_torso * 0.7 + p * 30)
        draw.line([torso_top, (x + 40, y + reach_y)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 40, y + reach_y), (x + 85, y + reach_y + 20)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + 20, y + reach_y + 10)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 20, y + reach_y + 10), (x + 75, y + reach_y + 35)], fill=STICK_YELLOW, width=lw)
        # Legs
        draw.line([torso_bot, (x - 20, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 20, y + l_thigh), (x - 25, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + 30, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 30, y + l_thigh), (x + 35, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    elif action == "thumbs_up":
        # Left hand on hip, right hand giving thumbs up
        draw.line([torso_top, (x - 35, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 35, y - h_torso * 0.5), (x - 15, y - 5)], fill=STICK_YELLOW, width=lw)
        # Right arm bent upward with thumb
        draw.line([torso_top, (x + 45, y - h_torso * 0.6)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 45, y - h_torso * 0.6), (x + 55, y - h_torso - 25)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 55, y - h_torso - 25), (x + 55, y - h_torso - 45)], fill=STICK_YELLOW, width=lw)
        # Legs
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
# ENVIRONMENT OBJECTS: DESK, LAPTOP, VARIABLE BOX
# -------------------------------------------------------------
def draw_desk_and_laptop(draw: ImageDraw.ImageDraw, desk_x: float, desk_y: float, laptop_open: float = 1.0):
    # Minimalist Desk
    draw.rounded_rectangle([desk_x, desk_y, desk_x + 360, desk_y + 24], radius=6, fill=DESK_COLOR)
    # Desk legs
    draw.rectangle([desk_x + 30, desk_y + 24, desk_x + 44, desk_y + 260], fill=(22, 28, 38))
    draw.rectangle([desk_x + 316, desk_y + 24, desk_x + 330, desk_y + 260], fill=(22, 28, 38))

    # Laptop Base
    lap_x, lap_y = desk_x + 80, desk_y - 12
    draw.rounded_rectangle([lap_x, lap_y, lap_x + 180, lap_y + 12], radius=4, fill=LAPTOP_SILVER)

    # Laptop Screen Lid (Opens smoothly based on laptop_open: 0.0 to 1.0)
    angle = 1.25 * laptop_open  # radians
    lid_len = 120
    screen_top_x = lap_x + 40 - int(math.cos(angle) * lid_len)
    screen_top_y = lap_y - int(math.sin(angle) * lid_len)
    draw.line([(lap_x + 40, lap_y), (screen_top_x, screen_top_y)], fill=LAPTOP_SILVER, width=8)

    # Screen Glow
    if laptop_open > 0.3:
        glow_alpha = int(laptop_open * 120)
        draw.polygon(
            [(lap_x + 40, lap_y), (screen_top_x, screen_top_y), (lap_x + 140, screen_top_y - 20), (lap_x + 120, lap_y)],
            fill=(40, 60, 90)
        )


def draw_variable_box(draw: ImageDraw.ImageDraw, x: float, y: float, label: str, value: str = "", fill_color = None):
    # Physical 3D-styled acrylic storage box
    w, h = 260, 240
    # Outer box border with glowing cyan outline
    draw.rounded_rectangle([x - w // 2, y - h // 2, x + w // 2, y + h // 2], radius=18, fill=PANEL_BG, outline=CYAN_ACCENT, width=4)
    # Open top rim
    draw.ellipse([x - w // 2 + 10, y - h // 2 - 20, x + w // 2 - 10, y - h // 2 + 20], outline=CYAN_ACCENT, width=3)

    # Memory Address Badge
    draw.rounded_rectangle([x - 90, y - h // 2 + 16, x + 90, y - h // 2 + 54], radius=8, fill=(28, 36, 50))
    draw.text((x, y - h // 2 + 35), "MEMORY BOX", fill=MUTED_GRAY, font=get_font("bold", 20), anchor="mm")

    # Front Variable Name Label
    draw.text((x, y + 20), label, fill=CYAN_ACCENT, font=font_box_label, anchor="mm")

    # Value inside box (if present)
    if value:
        col = fill_color or GOLD_VAL
        draw.rounded_rectangle([x - 75, y - 75, x + 75, y - 5], radius=14, fill=col, outline=WHITE, width=3)
        draw.text((x, y - 40), value, fill=(20, 20, 20), font=font_val, anchor="mm")


def draw_floating_code_editor(draw: ImageDraw.ImageDraw, active_lines: list, highlights: list):
    # Clean, beautiful IDE window centered above the scene
    x0, y0 = 60, 220
    x1, y1 = WIDTH - 60, 560
    draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=PANEL_BG, outline=PANEL_BORDER, width=3)
    # Title bar
    draw.rounded_rectangle([x0, y0, x1, y0 + 55], radius=20, fill=(24, 30, 42))
    draw.rectangle([x0, y0 + 35, x1, y0 + 55], fill=(24, 30, 42))
    draw.ellipse([x0 + 25, y0 + 18, x0 + 43, y0 + 36], fill=(239, 68, 68))
    draw.ellipse([x0 + 55, y0 + 18, x0 + 73, y0 + 36], fill=(250, 204, 21))
    draw.ellipse([x0 + 85, y0 + 18, x0 + 103, y0 + 36], fill=(34, 197, 94))
    draw.text((x0 + (x1 - x0) // 2, y0 + 28), "variables_demo.py — Python", fill=MUTED_GRAY, font=font_sub, anchor="mm")

    # Code lines
    cy = y0 + 85
    for idx, (code_text, is_hl) in enumerate(zip(active_lines, highlights)):
        line_num = f"{idx + 1:2d}  "
        draw.text((x0 + 35, cy), line_num, fill=(80, 95, 120), font=font_code)

        if is_hl:
            # Subtle highlight bar
            draw.rounded_rectangle([x0 + 100, cy - 6, x1 - 35, cy + 50], radius=10, fill=(38, 52, 75))

        # Syntax colorization
        if "x = 10" in code_text:
            draw.text((x0 + 120, cy), "x", fill=CYAN_ACCENT, font=font_code)
            draw.text((x0 + 160, cy), " = ", fill=WHITE, font=font_code)
            draw.text((x0 + 230, cy), "10", fill=GOLD_VAL, font=font_code)
        elif "print(x)" in code_text:
            draw.text((x0 + 120, cy), "print", fill=PURPLE_KEYWORD, font=font_code)
            draw.text((x0 + 250, cy), "(", fill=WHITE, font=font_code)
            draw.text((x0 + 275, cy), "x", fill=CYAN_ACCENT, font=font_code)
            draw.text((x0 + 305, cy), ")", fill=WHITE, font=font_code)
        elif "x = 25" in code_text:
            draw.text((x0 + 120, cy), "x", fill=CYAN_ACCENT, font=font_code)
            draw.text((x0 + 160, cy), " = ", fill=WHITE, font=font_code)
            draw.text((x0 + 230, cy), "25", fill=EMERALD_GREEN, font=font_code)
        else:
            draw.text((x0 + 120, cy), code_text, fill=WHITE, font=font_code)

        cy += 65


def draw_terminal_output(draw: ImageDraw.ImageDraw, output_lines: list):
    # Terminal console output window below code editor
    x0, y0 = 60, 600
    x1, y1 = WIDTH - 60, 760
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(14, 18, 24), outline=PANEL_BORDER, width=2)
    # Console header
    draw.text((x0 + 30, y0 + 30), "Terminal Output", fill=MUTED_GRAY, font=get_font("bold", 24), anchor="lm")
    draw.line([(x0, y0 + 50), (x1, y0 + 50)], fill=(30, 38, 50), width=1)

    cy = y0 + 80
    for l in output_lines:
        draw.text((x0 + 30, cy), ">>> ", fill=(100, 115, 140), font=font_term)
        draw.text((x0 + 130, cy), l, fill=EMERALD_GREEN, font=font_term)
        cy += 50


def draw_callout_banner(draw: ImageDraw.ImageDraw, step_text: str, explanation: str):
    # Educational guide banner locked cleanly at the bottom
    by = 1620
    draw.rounded_rectangle([50, by, WIDTH - 50, by + 230], radius=22, fill=PANEL_BG, outline=CYAN_ACCENT, width=3)
    draw.rounded_rectangle([80, by + 20, 480, by + 75], radius=12, fill=(30, 48, 75))
    draw.text((95, by + 47), step_text, fill=GOLD_VAL, font=font_sub, anchor="lm")
    draw.text((80, by + 115), explanation[:44], fill=WHITE, font=font_callout)
    if len(explanation) > 44:
        draw.text((80, by + 165), explanation[44:90], fill=MUTED_GRAY, font=font_sub)


# -------------------------------------------------------------
# MAIN TRIAL COMPOSITING ENGINE
# -------------------------------------------------------------
def render_trial_frames():
    print(f"\n==================================================================")
    print(f"🎬 RENDERING EDUCATIONAL TRIAL VIDEO: PYTHON VARIABLES")
    print(f"Total Duration: {TOTAL_SECONDS:.2f}s | FPS: {FPS} | Total Frames: {TOTAL_FRAMES}")
    print(f"==================================================================")

    desk_x, desk_y = 120, 1380
    box_x, box_y = 800, 1260

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Subtle dark blueprint grid
        for gy in range(0, HEIGHT, 100):
            draw.line([(0, gy), (WIDTH, gy)], fill=(16, 20, 28), width=1)
        for gx in range(0, WIDTH, 100):
            draw.line([(gx, 0), (gx, HEIGHT)], fill=(16, 20, 28), width=1)

        # Floor surface
        draw.line([(0, 1580), (WIDTH, 1580)], fill=(35, 45, 60), width=4)

        # Top Header Pill
        draw.rounded_rectangle([60, 45, WIDTH - 60, 175], radius=20, fill=PANEL_BG, outline=PANEL_BORDER, width=2)
        draw.text((WIDTH // 2, 85), "PYTHON FOR BEGINNERS • LESSON 1", fill=STICK_YELLOW, font=font_header, anchor="mm")
        draw.text((WIDTH // 2, 135), "What is a Variable? (Memory & Storage Explained)", fill=WHITE, font=font_sub, anchor="mm")

        # -------------------------------------------------------------
        # SYNCHRONIZED TIMELINE (0.0s to 48.2s)
        # -------------------------------------------------------------

        # --- BEAT 1: 0.0s - 5.6s ("Imagine you need to store data... In Python, that's a variable!") ---
        if t < 5.6:
            draw_floating_code_editor(draw, ["# Python Variables Demo"], [False])
            # Stickman enters scene, walks to desk, opens laptop
            if t < 2.5:
                # Walking in from left to desk
                walk_p = t / 2.5
                sm_x = int(-100 + (desk_x + 280 + 100) * walk_p)
                draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=0.0)
                draw_yellow_stickman(draw, sm_x, 1540, action="walk", param=walk_p, face="smile")
            else:
                # Sits at laptop and opens it
                open_p = min(1.0, (t - 2.5) / 1.5)
                draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=open_p)
                draw_yellow_stickman(draw, desk_x + 280, 1420, action="typing_at_laptop", param=t, face="happy")

            draw_callout_banner(draw, "STEP 1: INTRODUCTION", "A variable is like a storage container for data in your code!")

        # --- BEAT 2: 5.6s - 9.8s ("Think of a variable as a labeled storage box in memory...") ---
        elif t < 9.8:
            draw_floating_code_editor(draw, ["# Variable = Storage Box"], [False])
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            # Stickman stands up and gestures toward empty box x
            draw_yellow_stickman(draw, desk_x + 360, 1540, action="point_right", face="smile")

            # Physical box x appears floating smoothly into place
            box_appear_p = min(1.0, (t - 5.6) / 1.2)
            cur_box_y = int(1450 - (1450 - box_y) * (box_appear_p ** 1.5))
            draw_variable_box(draw, box_x, cur_box_y, label="x", value="")

            draw_callout_banner(draw, "STEP 2: THE MEMORY BOX", "Variable 'x' reserves a labeled compartment in the computer's memory!")

        # --- BEAT 3: 9.8s - 17.4s ("When we write x = 10, Python creates 10 and places it in box x...") ---
        elif t < 17.4:
            draw_floating_code_editor(draw, ["x = 10"], [True])
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_variable_box(draw, box_x, box_y, label="x", value="")

            rel_t = t - 9.8
            if rel_t < 2.5:
                # Stickman typing x = 10 on laptop
                draw_yellow_stickman(draw, desk_x + 280, 1420, action="typing_at_laptop", param=t, face="curious")
                # Golden 10 orb appears above laptop
                orb_p = rel_t / 2.5
                draw.rounded_rectangle([desk_x + 130, int(1150 - 80 * orb_p), desk_x + 270, int(1230 - 80 * orb_p)], radius=14, fill=GOLD_VAL, outline=WHITE, width=3)
                draw.text((desk_x + 200, int(1190 - 80 * orb_p)), "10", fill=(20, 20, 20), font=font_val, anchor="mm")
            elif rel_t < 5.0:
                # Stickman carries 10 over to box x
                carry_p = (rel_t - 2.5) / 2.5
                cx = int((desk_x + 320) + (box_x - 120 - (desk_x + 320)) * carry_p)
                draw_yellow_stickman(draw, cx, 1540, action="place_in_box", param=carry_p, face="happy")
                # Carrying 10
                draw.rounded_rectangle([cx + 40, 1340, cx + 160, 1420], radius=14, fill=GOLD_VAL, outline=WHITE, width=3)
                draw.text((cx + 100, 1380), "10", fill=(20, 20, 20), font=font_val, anchor="mm")
            else:
                # Placed inside box x!
                draw_yellow_stickman(draw, box_x - 130, 1540, action="thumbs_up", face="happy")
                draw_variable_box(draw, box_x, box_y, label="x", value="10", fill_color=GOLD_VAL)

            draw_callout_banner(draw, "STEP 3: ASSIGNMENT (x = 10)", "Value 10 is placed directly inside box x using the '=' assignment operator!")

        # --- BEAT 4: 17.4s - 22.5s ("Whenever your program mentions x, Python looks right inside that box...") ---
        elif t < 22.5:
            draw_floating_code_editor(draw, ["x = 10", "print(x)"], [False, True])
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_variable_box(draw, box_x, box_y, label="x", value="10", fill_color=GOLD_VAL)

            # Stickman points directly into box x
            draw_yellow_stickman(draw, box_x - 140, 1540, action="point_right", face="smile")
            # Glowing scan beam looking into box x
            draw.line([(box_x - 50, 1370), (box_x, 1220)], fill=CYAN_ACCENT, width=4)

            draw_callout_banner(draw, "STEP 4: READING MEMORY", "Referencing 'x' tells Python: go to box x and retrieve whatever is inside!")

        # --- BEAT 5: 22.5s - 28.3s ("And when we run print(x), it immediately displays: 10!") ---
        elif t < 28.3:
            draw_floating_code_editor(draw, ["x = 10", "print(x)"], [False, True])
            draw_terminal_output(draw, ["10"])
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_variable_box(draw, box_x, box_y, label="x", value="10", fill_color=GOLD_VAL)

            # Stickman gives enthusiastic thumbs up
            draw_yellow_stickman(draw, box_x - 140, 1540, action="thumbs_up", face="happy")

            # Green checkmark badge over terminal
            draw.rounded_rectangle([WIDTH - 280, 680, WIDTH - 80, 740], radius=10, fill=EMERALD_GREEN)
            draw.text((WIDTH - 180, 710), "OUTPUT: 10", fill=WHITE, font=get_font("bold", 24), anchor="mm")

            draw_callout_banner(draw, "STEP 5: CONSOLE OUTPUT", "print(x) looks inside box x, finds 10, and prints 10 to the console screen!")

        # --- BEAT 6: 28.3s - 36.6s ("Need to change it? Variables can vary! If we set x = 25...") ---
        elif t < 36.6:
            draw_floating_code_editor(draw, ["x = 10", "print(x)", "x = 25"], [False, False, True])
            draw_terminal_output(draw, ["10"])
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)

            rel_t = t - 28.3
            if rel_t < 3.5:
                # Old 10 lifts out of box
                out_p = rel_t / 3.5
                draw_variable_box(draw, box_x, box_y, label="x", value="")
                # 10 lifting out fading
                draw.rounded_rectangle([box_x - 60, int(1200 - 150 * out_p), box_x + 60, int(1270 - 150 * out_p)], radius=12, fill=(180, 150, 40))
                draw.text((box_x, int(1235 - 150 * out_p)), "10", fill=(20, 20, 20), font=font_val, anchor="mm")
                draw_yellow_stickman(draw, box_x - 140, 1540, action="idle", face="curious")
            else:
                # Fresh emerald 25 placed in box x!
                draw_variable_box(draw, box_x, box_y, label="x", value="25", fill_color=EMERALD_GREEN)
                draw_yellow_stickman(draw, box_x - 140, 1540, action="thumbs_up", face="happy")

            draw_callout_banner(draw, "STEP 6: REASSIGNMENT (x = 25)", "Variables can vary! Placing 25 in box x replaces the old value 10!")

        # --- BEAT 7: 36.6s - 43.8s ("Run print(x) again, and the output is now 25...") ---
        elif t < 43.8:
            draw_floating_code_editor(draw, ["x = 10", "print(x)", "x = 25", "print(x)"], [False, False, False, True])
            draw_terminal_output(draw, ["10", "25"])
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_variable_box(draw, box_x, box_y, label="x", value="25", fill_color=EMERALD_GREEN)

            # Stickman points at the updated output 25
            draw_yellow_stickman(draw, box_x - 140, 1540, action="thumbs_up", face="happy")

            draw_callout_banner(draw, "STEP 7: NEW VALUE PRINTED", "The second print(x) checks box x again, displaying the updated 25!")

        # --- BEAT 8: 43.8s - 48.2s ("Follow for episode 2 where we explore Python Data Types!") ---
        else:
            draw_floating_code_editor(draw, ["x = 10", "print(x)", "x = 25", "print(x)"], [False, False, False, False])
            draw_terminal_output(draw, ["10", "25"])
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_variable_box(draw, box_x, box_y, label="x", value="25", fill_color=EMERALD_GREEN)

            # Stickman waves enthusiastically at viewer
            wave_param = (t - 43.8) * 8
            draw_yellow_stickman(draw, 540, 1540, action="thumbs_up", param=wave_param, face="happy")

            # Next Episode Follow Banner
            draw.rounded_rectangle([70, 1460, WIDTH - 70, 1560], radius=16, fill=STICK_YELLOW)
            draw.text((WIDTH // 2, 1510), "FOLLOW FOR LESSON 2: PYTHON DATA TYPES! 🚀", fill=(20, 20, 20), font=get_font("bold", 34), anchor="mm")

            draw_callout_banner(draw, "LESSON COMPLETE!", "You just mastered how Python variables store and update values in memory!")

        # Save Frame
        frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
        img.save(frame_path, format="PNG")

        if frame % 150 == 0 or frame == TOTAL_FRAMES - 1:
            print(f"Rendered {frame:4d}/{TOTAL_FRAMES} frames ({t:4.1f}s / {TOTAL_SECONDS:.1f}s)...")


def composite_trial_video():
    print("\nCompositing educational trial video with synchronized narration & Foley...")
    narration_audio = TEMP_DIR / "narration.mp3"
    final_video = RENDERED_DIR / "educational_trial_python_variables.mp4"

    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(narration_audio),
        "-i", str(SFX_DIR / "whoosh.wav"),            # 2: Laptop open
        "-i", str(SFX_DIR / "keyboard.wav"),          # 3: Typing code
        "-i", str(SFX_DIR / "pop.wav"),               # 4: Box x appears
        "-i", str(SFX_DIR / "glass_tap.wav"),         # 5: 10 placed in box
        "-i", str(SFX_DIR / "success_ding.wav"),      # 6: Output 10 prints
        "-i", str(SFX_DIR / "chime.wav"),             # 7: Output 25 prints
        "-t", str(TOTAL_SECONDS),
        "-filter_complex",
        (
            "[0:v]fps=30,format=yuv420p[v];"
            "[1:a]volume=1.0[narr];"
            "[2:a]adelay=2500|2500,volume=0.3[s_open];"
            "[3:a]adelay=9800|9800,volume=0.25[s_type];"
            "[4:a]adelay=6000|6000,volume=0.4[s_box];"
            "[5:a]adelay=14800|14800,volume=0.4[s_drop];"
            "[6:a]adelay=23000|23000,volume=0.5[s_ding1];"
            "[7:a]adelay=37000|37000,volume=0.5[s_ding2];"
            "[narr][s_open][s_type][s_box][s_drop][s_ding1][s_ding2]amix=inputs=7:duration=first:dropout_transition=0[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]

    print("Running FFmpeg composite...")
    subprocess.run(cmd, check=True)
    mb = final_video.stat().st_size / (1024 * 1024)
    print(f"\n==================================================================")
    print(f"🎉 TRIAL EDUCATIONAL VIDEO READY FOR REVIEW!")
    print(f"Path: {final_video}")
    print(f"Size: {mb:.2f} MB | Duration: {TOTAL_SECONDS}s")
    print(f"==================================================================")
    return str(final_video)


if __name__ == "__main__":
    render_trial_frames()
    composite_trial_video()

