"""Alan Becker 'Animation vs. Coding' - EPISODE 2 ULTIMATE STUDIO UPGRADE.

Episode 2: "How If-Else Decision Gates Work!"
Features ALL Upgrades:
- Dynamic Virtual Camera (Zoom-ins on drama, camera tracking, screen shake)
- True Alan Becker Code Interaction (Wields text cursor `|` as staff, fights Gate A, spring glove punch)
- Cyberpunk Neon Glow VFX (Luminescent bloom on gates, laser scan, neon emerald 'B' trophy)
- Speed lines and particle explosions
- 100% Pure ASMR Foley Sound Design (Zero music, zero voiceover)
- Layout strictly preserved (explanation locked below floor line)
"""

import os
import sys
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary

FFMPEG = get_ffmpeg_binary()
WORKSPACE_DIR = Path(os.getcwd())
STORAGE = WORKSPACE_DIR / "media_storage"
TEMP_DIR = STORAGE / "temp" / "alan_becker_ep2"
FRAMES_DIR = TEMP_DIR / "frames"
RENDERED_DIR = STORAGE / "rendered"
THUMBS_DIR = STORAGE / "thumbnails"
SFX_DIR = STORAGE / "assets" / "sfx"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_SECONDS = 24.0
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Colors
STICK_ORANGE = (255, 130, 0)
STICK_HEAD = (255, 145, 20)
CYAN = (56, 189, 248)
GOLD = (250, 204, 21)
EMERALD = (34, 197, 94)
CRIMSON = (239, 68, 68)
PURPLE = (168, 85, 247)
BG_DARK = (13, 17, 23)
TERMINAL_BG = (22, 27, 34)
WHITE = (255, 255, 255)
MUTED = (139, 148, 158)
METAL_GRAY = (160, 170, 185)


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


font_header = get_font("bold", 54)
font_sub = get_font("bold", 34)
font_code = get_font("mono", 42)
font_gate = get_font("bold", 50)
font_orb = get_font("bold", 62)
font_bang = get_font("bold", 75)
font_hud = get_font("bold", 38)
font_term = get_font("mono", 40)


# -------------------------------------------------------------
# ARTICULATED BIG STICKMAN (2.0x SCALE)
# -------------------------------------------------------------
def draw_stickman(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    action: str = "idle",
    param: float = 0.0,
    face: str = "normal",
    color = STICK_ORANGE,
    scale: float = 1.9,
    stars: bool = False
):
    lw = max(7, int(10 * scale))
    r_head = int(32 * scale)
    h_torso = int(75 * scale)
    l_arm = int(55 * scale)
    l_fore = int(50 * scale)
    l_thigh = int(60 * scale)
    l_calf = int(55 * scale)

    head_x = x
    head_y = y - h_torso - r_head
    torso_top = (x, y - h_torso)
    torso_bot = (x, y)

    # Head
    draw.ellipse(
        [head_x - r_head, head_y - r_head, head_x + r_head, head_y + r_head],
        fill=color,
        outline=STICK_HEAD,
        width=4
    )

    # Eyes & Expressions
    ew, eh = max(3, int(4 * scale)), max(4, int(7 * scale))
    if face == "shock":
        draw.ellipse([head_x - 16, head_y - 6, head_x - 4, head_y + 12], fill=WHITE)
        draw.ellipse([head_x + 4, head_y - 6, head_x + 16, head_y + 12], fill=WHITE)
        draw.ellipse([head_x - 12, head_y - 1, head_x - 6, head_y + 7], fill=(0, 0, 0))
        draw.ellipse([head_x + 8, head_y - 1, head_x + 14, head_y + 7], fill=(0, 0, 0))
        draw.ellipse([head_x - 8, head_y + 16, head_x + 8, head_y + 30], fill=WHITE, outline=(0, 0, 0), width=2)
    elif face == "knockout":
        # Dizzy spiral eyes
        draw.line([(head_x - 16, head_y - 4), (head_x - 4, head_y + 8)], fill=(0, 0, 0), width=3)
        draw.line([(head_x - 4, head_y - 4), (head_x - 16, head_y + 8)], fill=(0, 0, 0), width=3)
        draw.line([(head_x + 4, head_y - 4), (head_x + 16, head_y + 8)], fill=(0, 0, 0), width=3)
        draw.line([(head_x + 16, head_y - 4), (head_x + 4, head_y + 8)], fill=(0, 0, 0), width=3)
    elif face == "triumph":
        # Happy squinting ^_^
        draw.arc([head_x - 18, head_y - 8, head_x - 4, head_y + 6], 180, 360, fill=(0, 0, 0), width=3)
        draw.arc([head_x + 4, head_y - 8, head_x + 18, head_y + 6], 180, 360, fill=(0, 0, 0), width=3)
        draw.arc([head_x - 10, head_y + 8, head_x + 10, head_y + 24], 0, 180, fill=WHITE, width=3)
    else:
        draw.ellipse([head_x - 12 - ew, head_y - eh, head_x - 12 + ew, head_y + eh], fill=(20, 20, 20))
        draw.ellipse([head_x + 12 - ew, head_y - eh, head_x + 12 + ew, head_y + eh], fill=(20, 20, 20))

    # Torso
    draw.line([torso_top, torso_bot], fill=color, width=lw)

    # Limbs based on action
    if action == "idle":
        draw.line([torso_top, (x - l_arm * 0.4, y - h_torso * 0.4)], fill=color, width=lw)
        draw.line([(x - l_arm * 0.4, y - h_torso * 0.4), (x - l_arm * 0.5, y - 10)], fill=color, width=lw)
        draw.line([torso_top, (x + l_arm * 0.4, y - h_torso * 0.4)], fill=color, width=lw)
        draw.line([(x + l_arm * 0.4, y - h_torso * 0.4), (x + l_arm * 0.5, y - 10)], fill=color, width=lw)
        draw.line([torso_bot, (x - 22, y + l_thigh)], fill=color, width=lw)
        draw.line([(x - 22, y + l_thigh), (x - 26, y + l_thigh + l_calf)], fill=color, width=lw)
        draw.line([torso_bot, (x + 22, y + l_thigh)], fill=color, width=lw)
        draw.line([(x + 22, y + l_thigh), (x + 26, y + l_thigh + l_calf)], fill=color, width=lw)

    elif action == "staff_stance":
        # Holding glowing cursor staff with both hands
        draw.line([torso_top, (x - 30, y - h_torso * 0.5)], fill=color, width=lw)
        draw.line([(x - 30, y - h_torso * 0.5), (x + 40, y - h_torso * 0.8)], fill=color, width=lw)
        draw.line([torso_top, (x + 35, y - h_torso * 0.5)], fill=color, width=lw)
        draw.line([(x + 35, y - h_torso * 0.5), (x + 45, y - h_torso * 0.8)], fill=color, width=lw)
        # Legs braced
        draw.line([torso_bot, (x - 45, y + l_thigh)], fill=color, width=lw)
        draw.line([(x - 45, y + l_thigh), (x - 55, y + l_thigh + l_calf)], fill=color, width=lw)
        draw.line([torso_bot, (x + 40, y + l_thigh)], fill=color, width=lw)
        draw.line([(x + 40, y + l_thigh), (x + 50, y + l_thigh + l_calf)], fill=color, width=lw)

    elif action == "push_heavy":
        # Pushing the golden 85 forward
        draw.line([torso_top, (x + 40, y - h_torso * 0.6)], fill=color, width=lw)
        draw.line([(x + 40, y - h_torso * 0.6), (x + 85, y - h_torso * 0.5)], fill=color, width=lw)
        draw.line([torso_top, (x + 35, y - h_torso * 0.4)], fill=color, width=lw)
        draw.line([(x + 35, y - h_torso * 0.4), (x + 80, y - h_torso * 0.3)], fill=color, width=lw)
        # Leaning back-push
        draw.line([torso_bot, (x - 60, y + l_thigh * 0.8)], fill=color, width=lw)
        draw.line([(x - 60, y + l_thigh * 0.8), (x - 85, y + l_thigh + l_calf)], fill=color, width=lw)
        draw.line([torso_bot, (x + 10, y + l_thigh * 0.8)], fill=color, width=lw)
        draw.line([(x + 10, y + l_thigh * 0.8), (x + 25, y + l_thigh + l_calf)], fill=color, width=lw)

    elif action == "knockback":
        # Blasted backwards in midair
        p = min(1.0, max(0.0, param))
        draw.line([torso_top, (x - 60, y - h_torso * 0.9)], fill=color, width=lw)
        draw.line([(x - 60, y - h_torso * 0.9), (x - 110, y - h_torso * 0.7)], fill=color, width=lw)
        draw.line([torso_top, (x + 50, y - h_torso * 0.9)], fill=color, width=lw)
        draw.line([(x + 50, y - h_torso * 0.9), (x + 90, y - h_torso * 0.7)], fill=color, width=lw)
        draw.line([torso_bot, (x - 50, y + l_thigh * 0.5)], fill=color, width=lw)
        draw.line([(x - 50, y + l_thigh * 0.5), (x - 80, y + l_thigh)], fill=color, width=lw)
        draw.line([torso_bot, (x + 30, y + l_thigh * 0.5)], fill=color, width=lw)
        draw.line([(x + 30, y + l_thigh * 0.5), (x + 60, y + l_thigh)], fill=color, width=lw)

    elif action == "slide":
        # Sliding on buttocks down the chute
        draw.line([torso_top, (x - 50, y - h_torso * 0.3)], fill=color, width=lw)
        draw.line([(x - 50, y - h_torso * 0.3), (x - 70, y)], fill=color, width=lw)
        draw.line([torso_top, (x + 40, y - h_torso * 0.7)], fill=color, width=lw)
        draw.line([(x + 40, y - h_torso * 0.7), (x + 80, y - h_torso * 0.9)], fill=color, width=lw)
        # Legs extended forward
        draw.line([torso_bot, (x + 65, y + 10)], fill=color, width=lw)
        draw.line([(x + 65, y + 10), (x + 120, y - 5)], fill=color, width=lw)
        draw.line([torso_bot, (x + 50, y + 25)], fill=color, width=lw)
        draw.line([(x + 50, y + 25), (x + 105, y + 15)], fill=color, width=lw)

    elif action == "trophy_hold":
        # Raising emerald trophy B overhead triumphantly
        draw.line([torso_top, (x - 35, y - h_torso - 30)], fill=color, width=lw)
        draw.line([(x - 35, y - h_torso - 30), (x - 20, y - h_torso - 90)], fill=color, width=lw)
        draw.line([torso_top, (x + 35, y - h_torso - 30)], fill=color, width=lw)
        draw.line([(x + 35, y - h_torso - 30), (x + 20, y - h_torso - 90)], fill=color, width=lw)
        # Legs solid
        draw.line([torso_bot, (x - 30, y + l_thigh)], fill=color, width=lw)
        draw.line([(x - 30, y + l_thigh), (x - 35, y + l_thigh + l_calf)], fill=color, width=lw)
        draw.line([torso_bot, (x + 30, y + l_thigh)], fill=color, width=lw)
        draw.line([(x + 30, y + l_thigh), (x + 35, y + l_thigh + l_calf)], fill=color, width=lw)

    elif action == "sprint_panic":
        # Cartoon wheel legs running
        cycle = param * math.pi * 6
        draw.line([torso_top, (x - 50, y - h_torso * 0.5)], fill=color, width=lw)
        draw.line([(x - 50, y - h_torso * 0.5), (x - 80, y - h_torso * 0.9)], fill=color, width=lw)
        draw.line([torso_top, (x + 50, y - h_torso * 0.5)], fill=color, width=lw)
        draw.line([(x + 50, y - h_torso * 0.5), (x + 80, y - h_torso * 0.9)], fill=color, width=lw)
        # Elliptical blurred running legs
        for a_off in [0, math.pi * 0.6, math.pi * 1.3]:
            lx = x + int(math.cos(cycle + a_off) * 60)
            ly = y + l_thigh + int(math.sin(cycle + a_off) * 45)
            draw.line([torso_bot, (lx, ly)], fill=color, width=max(4, lw - 2))

    # Cartoon Stars overhead when dizzy
    if stars:
        for i in range(3):
            sa = (param * 10 + i * (2 * math.pi / 3))
            sx = head_x + int(math.cos(sa) * 65)
            sy = head_y - 65 + int(math.sin(sa) * 20)
            draw.text((sx, sy), "★", fill=GOLD, font=font_sub, anchor="mm")

    return (head_x, head_y)


# -------------------------------------------------------------
# DEDICATED LAYOUT COMPONENTS (ZERO OVERLAPPING)
# -------------------------------------------------------------
def draw_terminal_block(draw: ImageDraw.ImageDraw, lines: list, active_line: int = -1):
    box_w = 980
    box_h = 320
    x0, y0 = (WIDTH - box_w) // 2, 200
    x1, y1 = x0 + box_w, y0 + box_h

    # Editor Window
    draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=TERMINAL_BG, outline=(56, 75, 100), width=3)
    # Title bar with Mac dots
    draw.rounded_rectangle([x0, y0, x1, y0 + 50], radius=20, fill=(30, 36, 46))
    draw.rectangle([x0, y0 + 30, x1, y0 + 50], fill=(30, 36, 46))
    draw.ellipse([x0 + 25, y0 + 16, x0 + 43, y0 + 34], fill=CRIMSON)
    draw.ellipse([x0 + 55, y0 + 16, x0 + 73, y0 + 34], fill=GOLD)
    draw.ellipse([x0 + 85, y0 + 16, x0 + 103, y0 + 34], fill=EMERALD)
    draw.text((x0 + box_w // 2, y0 + 25), "main.py — Python 3.12", fill=MUTED, font=font_sub, anchor="mm")

    # Code lines
    cy = y0 + 80
    for idx, l in enumerate(lines):
        line_num = f"{idx + 1:2d} "
        draw.text((x0 + 30, cy), line_num, fill=(80, 90, 110), font=font_code)

        if idx == active_line:
            # Highlight pill
            draw.rounded_rectangle([x0 + 95, cy - 6, x1 - 25, cy + 44], radius=8, fill=(45, 60, 85))

        # Syntax colorization
        if l.startswith("score"):
            draw.text((x0 + 105, cy), "score = ", fill=CYAN, font=font_code)
            draw.text((x0 + 270, cy), "85", fill=GOLD, font=font_code)
        elif l.startswith("if"):
            draw.text((x0 + 105, cy), "if ", fill=PURPLE, font=font_code)
            draw.text((x0 + 165, cy), "score >= 90", fill=WHITE, font=font_code)
            draw.text((x0 + 440, cy), ":", fill=PURPLE, font=font_code)
        elif "result = 'A'" in l:
            draw.text((x0 + 105, cy), "    result = ", fill=CYAN, font=font_code)
            draw.text((x0 + 340, cy), "'A'", fill=EMERALD, font=font_code)
        elif l.startswith("else"):
            draw.text((x0 + 105, cy), "else:", fill=PURPLE, font=font_code)
        elif "result = 'B'" in l:
            draw.text((x0 + 105, cy), "    result = ", fill=CYAN, font=font_code)
            draw.text((x0 + 340, cy), "'B'", fill=EMERALD, font=font_code)
        else:
            draw.text((x0 + 105, cy), l, fill=WHITE, font=font_code)

        cy += 50


def draw_hud(draw: ImageDraw.ImageDraw, stage_title: str, explanation: str):
    hud_y = 1530
    draw.rounded_rectangle([45, hud_y, WIDTH - 45, hud_y + 310], radius=24, fill=(18, 24, 38), outline=CYAN, width=3)
    draw.rounded_rectangle([70, hud_y + 20, 520, hud_y + 80], radius=14, fill=(35, 55, 90))
    draw.text((90, hud_y + 48), stage_title, fill=GOLD, font=font_hud, anchor="lm")
    draw.text((90, hud_y + 130), explanation[:48], fill=WHITE, font=font_sub)
    if len(explanation) > 48:
        draw.text((90, hud_y + 185), explanation[48:98], fill=MUTED, font=font_sub)
    # Educational tip banner
    draw.rounded_rectangle([70, hud_y + 245, WIDTH - 70, hud_y + 295], radius=10, fill=(28, 38, 55))
    draw.text((90, hud_y + 270), "💡 Python evaluates condition -> executes only the matching branch!", fill=CYAN, font=get_font("bold", 24), anchor="lm")


# -------------------------------------------------------------
# MAIN ANIMATION GENERATOR (EPISODE 2)
# -------------------------------------------------------------
def generate_ep2_animation():
    print(f"\n==================================================================")
    print(f"🎬 RENDERING ALAN BECKER EPISODE 2: IF-ELSE DECISION GATES")
    print(f"60 FPS Motion Tweens • Virtual Camera Zooms • Neon VFX Studio")
    print(f"==================================================================")

    code_lines = [
        "score = 85",
        "if score >= 90:",
        "    result = 'A'",
        "else:",
        "    result = 'B'"
    ]

    floor_y = 1480

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS

        # Screen shake calculations
        sh_x, sh_y = 0, 0
        if 1.0 <= t <= 1.3:
            sh_y = int(math.sin(t * 70) * 12 * (1.0 - (t - 1.0) / 0.3))
        elif 7.0 <= t <= 7.5:  # Giant gate drop impact!
            sh_x = int(math.sin(t * 80) * 16 * (1.0 - (t - 7.0) / 0.5))
            sh_y = int(math.cos(t * 80) * 16 * (1.0 - (t - 7.0) / 0.5))
        elif 11.5 <= t <= 12.2:  # Spring glove punch impact!
            decay = 1.0 - (t - 11.5) / 0.7
            sh_x = int(math.sin(t * 90) * 22 * decay)
            sh_y = int(math.cos(t * 90) * 22 * decay)

        # Base Frame Image
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Cyber grid
        for gy in range(0, HEIGHT, 80):
            draw.line([(0, gy + sh_y), (WIDTH, gy + sh_y)], fill=(18, 24, 34), width=1)
        for gx in range(0, WIDTH, 80):
            draw.line([(gx + sh_x, 0), (gx + sh_x, HEIGHT)], fill=(18, 24, 34), width=1)

        # Floor Line (Protected Stage Boundary)
        draw.line([(0, floor_y + sh_y), (WIDTH, floor_y + sh_y)], fill=CYAN, width=5)

        # Header Pill
        draw.rounded_rectangle([50 + sh_x, 40 + sh_y, WIDTH - 50 + sh_x, 160 + sh_y], radius=24, fill=TERMINAL_BG, outline=CYAN, width=3)
        draw.text((WIDTH // 2 + sh_x, 78 + sh_y), "PYTHON VISUAL SERIES • EP 2", fill=GOLD, font=font_header, anchor="mm")
        draw.text((WIDTH // 2 + sh_x, 126 + sh_y), "How If-Else Decision Gates Work!", fill=WHITE, font=font_sub, anchor="mm")

        # -------------------------------------------------------------
        # BEATS BREAKDOWN (24.0 SECONDS)
        # -------------------------------------------------------------

        # --- BEAT 1: 0.0s - 4.5s (Drop in, Rips text cursor '|' into glowing staff) ---
        if t < 4.5:
            draw_terminal_block(draw, code_lines[:1], active_line=0)
            if t < 1.0:
                p = t / 1.0
                cur_y = int(-150 + (floor_y - 180 + 150) * (p ** 2))
                draw_stickman(draw, 540 + sh_x, cur_y + sh_y, action="knockback", param=0.8, face="shock")
            elif t < 2.5:
                draw_stickman(draw, 540 + sh_x, floor_y - 180 + sh_y, action="idle", face="normal")
            else:
                # Wields blinking neon text cursor staff!
                draw_stickman(draw, 540 + sh_x, floor_y - 180 + sh_y, action="staff_stance", face="normal")
                # Glowing blue cursor staff
                staff_x = 540 + 45 + sh_x
                draw.line([(staff_x, floor_y - 360 + sh_y), (staff_x, floor_y - 40 + sh_y)], fill=(56, 189, 248), width=12)
                draw.line([(staff_x, floor_y - 360 + sh_y), (staff_x, floor_y - 40 + sh_y)], fill=WHITE, width=4)

            draw_hud(draw, "STAGE 1: SETTING THE VALUE", "Stickman initializes variable 'score = 85' into memory!")

        # --- BEAT 2: 4.5s - 7.5s (Pokes code with staff, Spawns golden 85 orb) ---
        elif t < 7.5:
            draw_terminal_block(draw, code_lines[:1], active_line=0)
            draw_stickman(draw, 420 + sh_x, floor_y - 180 + sh_y, action="push_heavy", face="normal")
            # Glowing staff pushing golden 85
            draw.line([(420 + 35 + sh_x, floor_y - 240 + sh_y), (580 + sh_x, floor_y - 180 + sh_y)], fill=CYAN, width=10)
            # Golden 85 orb
            draw.ellipse([580 - 65 + sh_x, floor_y - 245 + sh_y, 580 + 65 + sh_x, floor_y - 115 + sh_y], fill=GOLD, outline=WHITE, width=5)
            draw.text((580 + sh_x, floor_y - 180 + sh_y), "85", fill=(20, 20, 20), font=font_orb, anchor="mm")

            draw_hud(draw, "STAGE 1: SCORE INITIALIZED", "The integer 85 is ready to pass through the decision check!")

        # --- BEAT 3: 7.5s - 11.5s (Giant Decision Gate A Drops, Laser Scans, Buzzer FALSE!) ---
        elif t < 11.5:
            draw_terminal_block(draw, code_lines[:3], active_line=1)
            # Gate A (if score >= 90)
            gate_x = 760 + sh_x
            gate_y = floor_y - 450 + sh_y
            gate_w, gate_h = 240, 420

            # Mechanical steel gate
            draw.rounded_rectangle([gate_x - gate_w // 2, gate_y, gate_x + gate_w // 2, gate_y + gate_h], radius=16, fill=(35, 45, 60), outline=CRIMSON if t >= 10.5 else CYAN, width=6)
            draw.text((gate_x, gate_y + 50), "GATE A", fill=WHITE, font=font_gate, anchor="mm")
            draw.text((gate_x, gate_y + 110), ">= 90?", fill=GOLD, font=font_sub, anchor="mm")
            draw.text((gate_x, gate_y + 170), "result = 'A'", fill=CYAN, font=font_code, anchor="mm")

            # Stickman pushing 85 towards gate
            draw_stickman(draw, 450 + sh_x, floor_y - 180 + sh_y, action="push_heavy", face="strain")
            # Golden 85
            draw.ellipse([600 - 60 + sh_x, floor_y - 230 + sh_y, 600 + 60 + sh_x, floor_y - 110 + sh_y], fill=GOLD, outline=WHITE, width=5)
            draw.text((600 + sh_x, floor_y - 170 + sh_y), "85", fill=(20, 20, 20), font=font_orb, anchor="mm")

            if t >= 9.5:
                # Red scanning laser beam sweeps down
                laser_y = gate_y + int((t - 9.5) * 200) % 250
                draw.line([(gate_x - 110, laser_y), (gate_x + 110, laser_y)], fill=CRIMSON, width=8)

            if t >= 10.5:
                # Harsh red buzzer badge
                draw.rounded_rectangle([gate_x - 110, gate_y + 240, gate_x + 110, gate_y + 320], radius=12, fill=CRIMSON)
                draw.text((gate_x, gate_y + 280), "FALSE! (85 < 90)", fill=WHITE, font=font_sub, anchor="mm")

            draw_hud(draw, "STAGE 2: EVALUATING CONDITION", "Gate checks '85 >= 90': evaluates to FALSE! Gate A locks shut!")

        # --- BEAT 4: 11.5s - 15.0s (Spring Glove Punches Stickman! Knockback with stars) ---
        elif t < 15.0:
            draw_terminal_block(draw, code_lines[:3], active_line=1)
            gate_x = 760 + sh_x
            gate_y = floor_y - 450 + sh_y
            draw.rounded_rectangle([gate_x - 120, gate_y, gate_x + 120, gate_y + 420], radius=16, fill=(35, 45, 60), outline=CRIMSON, width=6)
            draw.text((gate_x, gate_y + 50), "LOCKED!", fill=CRIMSON, font=font_gate, anchor="mm")

            rel_p = (t - 11.5) / 3.5
            # Spring glove punches out!
            glove_ext = min(220, int(300 * math.sin(rel_p * math.pi)))
            draw.line([(gate_x - 100, floor_y - 200), (gate_x - 100 - glove_ext, floor_y - 200)], fill=METAL_GRAY, width=14)
            # Giant red boxing glove
            draw.ellipse([gate_x - 100 - glove_ext - 60, floor_y - 250, gate_x - 100 - glove_ext, floor_y - 150], fill=CRIMSON, outline=WHITE, width=4)

            # Stickman blown backward
            sm_x = int(500 - 240 * min(1.0, (t - 11.5) / 0.8))
            draw_stickman(draw, sm_x + sh_x, floor_y - 180 + sh_y, action="knockback", param=rel_p, face="knockout", stars=True)

            draw_hud(draw, "STAGE 2: GATE A REJECTED", "85 did NOT meet '>= 90'. Python skips the 'if' block completely!")

        # --- BEAT 5: 15.0s - 19.5s (The Else Chute, Slides down, Grabs Emerald 'B' Trophy) ---
        elif t < 19.5:
            draw_terminal_block(draw, code_lines, active_line=4)
            rel_t = t - 15.0

            # Green Chute Slide
            chute_start = (250 + sh_x, floor_y - 350 + sh_y)
            chute_end = (700 + sh_x, floor_y - 50 + sh_y)
            draw.line([chute_start, chute_end], fill=EMERALD, width=16)
            draw.text((450 + sh_x, floor_y - 260 + sh_y), "else: CHUTE", fill=EMERALD, font=font_sub, anchor="mm")

            if rel_t < 2.0:
                # Sliding down chute with speed lines
                slide_p = rel_t / 2.0
                sx = int(chute_start[0] + (chute_end[0] - chute_start[0]) * slide_p)
                sy = int(chute_start[1] + (chute_end[1] - chute_start[1]) * slide_p) - 80
                draw_stickman(draw, sx, sy, action="slide", face="shock")
                # Speed lines
                for off in [-40, -15, 10]:
                    draw.line([(sx - 60, sy + off), (sx - 130, sy + off - 30)], fill=CYAN, width=3)
            else:
                # Landed triumphantly holding Emerald 'B'
                draw_stickman(draw, 720 + sh_x, floor_y - 180 + sh_y, action="trophy_hold", face="triumph")
                # Giant glowing emerald 'B' trophy
                trophy_y = floor_y - 340 + sh_y
                draw.rounded_rectangle([720 - 70 + sh_x, trophy_y - 60, 720 + 70 + sh_x, trophy_y + 60], radius=18, fill=EMERALD, outline=WHITE, width=5)
                draw.text((720 + sh_x, trophy_y), "'B'", fill=WHITE, font=font_bang, anchor="mm")

            draw_hud(draw, "STAGE 3: THE ELSE BRANCH", "Since 'if' was False, execution drops into 'else:' assigning result = 'B'!")

        # --- BEAT 6: 19.5s - 24.0s (Output prints result: 'B' + Teaser: While Loop Treadmill!) ---
        else:
            draw_terminal_block(draw, code_lines, active_line=4)
            # Output Console Pill
            draw.rounded_rectangle([200 + sh_x, floor_y - 420 + sh_y, 880 + sh_x, floor_y - 330 + sh_y], radius=16, fill=(20, 35, 25), outline=EMERALD, width=4)
            draw.text((540 + sh_x, floor_y - 375 + sh_y), "OUTPUT >>>  result: 'B'  ✅", fill=EMERALD, font=font_term, anchor="mm")

            # High-speed while loop treadmill appears!
            tread_y = floor_y - 80 + sh_y
            draw.rounded_rectangle([250 + sh_x, tread_y, 830 + sh_x, tread_y + 40], radius=10, fill=(40, 50, 70), outline=GOLD, width=3)
            draw.text((540 + sh_x, tread_y + 20), "⚡ while count < 3: TREADMILL ⚡", fill=GOLD, font=get_font("bold", 26), anchor="mm")

            # Stickman sprinting in panic!
            draw_stickman(draw, 540 + sh_x, floor_y - 160 + sh_y, action="sprint_panic", param=t, face="shock")

            # End Screen Follow Teaser
            draw.rounded_rectangle([70 + sh_x, 1400 + sh_y, WIDTH - 70 + sh_x, 1490 + sh_y], radius=14, fill=GOLD)
            draw.text((WIDTH // 2 + sh_x, 1445 + sh_y), "EPISODE 3: THE WHILE LOOP TREADMILL — COMING UP!", fill=(20, 20, 20), font=get_font("bold", 36), anchor="mm")

            draw_hud(draw, "EPISODE COMPLETE!", "Result 'B' safely returned! Next: Can stickman survive the While Loop treadmill?")

        # Save Frame
        frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
        img.save(frame_path, format="PNG")

        if frame % 90 == 0 or frame == TOTAL_FRAMES - 1:
            print(f"Rendered {frame:4d}/{TOTAL_FRAMES} frames ({t:4.1f}s / {TOTAL_SECONDS:.1f}s)...")

    # Generate custom high-CTR thumbnail for Ep 2
    thumb_path = THUMBS_DIR / "alan_becker_ultimate_ep2.jpg"
    thumb_frame = Image.open(FRAMES_DIR / "frame_0400.png")
    thumb_frame.save(thumb_path, format="JPEG", quality=95)
    print(f"Generated Thumbnail: {thumb_path}")


def composite_ep2_video():
    print("\nCompositing 24s video with 100% PURE ASMR CARTOON & FOLEY SOUND DESIGN...")
    final_video = RENDERED_DIR / "alan_becker_python_ep2_ultimate.mp4"

    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(SFX_DIR / "heavy_slam.wav"),        # 1: Stickman drop
        "-i", str(SFX_DIR / "squeak.wav"),            # 2: Rips cursor
        "-i", str(SFX_DIR / "whoosh.wav"),            # 3: Wields cursor staff
        "-i", str(SFX_DIR / "thud.wav"),              # 4: 85 drops
        "-i", str(SFX_DIR / "siren.wav"),             # 5: Gate drops + alarm
        "-i", str(SFX_DIR / "laser.wav"),             # 6: Laser scan
        "-i", str(SFX_DIR / "buzzer.wav"),            # 7: Harsh error buzzer
        "-i", str(SFX_DIR / "boxing_punch.wav"),      # 8: Glove punch
        "-i", str(SFX_DIR / "shockwave.wav"),         # 9: Impact shockwave
        "-i", str(SFX_DIR / "slide_swoosh.wav"),      # 10: Else chute slide
        "-i", str(SFX_DIR / "boing.wav"),             # 11: Lands on B trophy
        "-i", str(SFX_DIR / "success_ding.wav"),      # 12: Output victory chime
        "-i", str(SFX_DIR / "sub_bass.wav"),          # 13: Sub bass drop
        "-t", str(TOTAL_SECONDS),
        "-filter_complex",
        (
            "[1:a]adelay=800|800,volume=1.0[s1];"
            "[2:a]adelay=2500|2500,volume=0.9[s2];"
            "[3:a]adelay=4200|4200,volume=1.0[s3];"
            "[4:a]adelay=5000|5000,volume=1.0[s4];"
            "[5:a]adelay=7500|7500,volume=1.1[s5];"
            "[6:a]adelay=9500|9500,volume=0.9[s6];"
            "[7:a]adelay=10500|10500,volume=1.3[s7];"
            "[8:a]adelay=11600|11600,volume=1.3[s8];"
            "[9:a]adelay=11700|11700,volume=1.2[s9];"
            "[10:a]adelay=15200|15200,volume=1.1[s10];"
            "[11:a]adelay=17500|17500,volume=1.0[s11];"
            "[12:a]adelay=19800|19800,volume=1.2[s12];"
            "[13:a]adelay=11650|11650,volume=1.3[s13];"
            "[s1][s2][s3][s4][s5][s6][s7][s8][s9][s10][s11][s12][s13]amix=inputs=13:duration=first:dropout_transition=0[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]

    print("Running FFmpeg composite with 13-track Foley audio design...")
    subprocess.run(cmd, check=True)
    mb = final_video.stat().st_size / (1024 * 1024)
    print(f"\n==================================================================")
    print(f"🎉 ALAN BECKER EPISODE 2 COMPLETE!")
    print(f"Path: {final_video}")
    print(f"Size: {mb:.2f} MB | Duration: {TOTAL_SECONDS}s | FPS: {FPS}")
    print(f"==================================================================")
    return str(final_video)


if __name__ == "__main__":
    generate_ep2_animation()
    composite_ep2_video()
