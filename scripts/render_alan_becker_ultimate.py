"""Alan Becker 'Animation vs. Coding' ULTIMATE Edition.

Improvements applied:
- NO background music (100% pure ASMR cartoon & foley sound effects)
- Dedicated Layout: Explanation text locked strictly BELOW the floor (Zero overlapping with animation)
- 2x Bigger visual scale (Character scale 2.0x, huge 360x320 variable boxes, massive golden orbs)
- Extended 24-second story pacing (lets every comedic and educational beat breathe)
- Advanced comedy & cartoon physics:
  * Giant hammer mallet with motion swing arc
  * Screen shake + radial shockwave + spark explosion
  * Jumper cable with electric crackles + cartoon skeleton zap gag
  * Footstep ASMR, glass tap clinks, hammer swoosh, boing jumps
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
TEMP_DIR = STORAGE / "temp" / "alan_becker_ultimate"
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
WOOD_BROWN = (180, 100, 40)
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
font_code = get_font("mono", 44)
font_box = get_font("bold", 48)
font_orb = get_font("bold", 60)
font_term = get_font("mono", 40)
font_bang = get_font("bold", 75)
font_hud = get_font("bold", 38)

# -------------------------------------------------------------
# ADVANCED ARTICULATED STICKMAN RIG (BIGGER 2.0x SCALE)
# -------------------------------------------------------------
def draw_big_stickman(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    action: str = "idle",
    param: float = 0.0,
    face: str = "normal",
    color = STICK_ORANGE,
    scale: float = 1.9,
    skeleton_flash: bool = False
):
    lw = max(7, int(10 * scale))
    r_head = int(32 * scale)

    # Squash and stretch
    sq_x, sq_y = 1.0, 1.0
    if action == "land_squash":
        sq_y = max(0.5, 1.0 - param * 0.5)
        sq_x = min(1.45, 1.0 + param * 0.45)
    elif action == "jump_stretch":
        sq_y = min(1.4, 1.0 + param * 0.4)
        sq_x = max(0.7, 1.0 - param * 0.3)

    torso_h = int(100 * scale * sq_y)
    r_head_eff = int(r_head * ((sq_x + sq_y) / 2))

    hip_x, hip_y = x, y
    neck_x, neck_y = x, y - torso_h
    head_cx, head_cy = x, neck_y - r_head_eff

    arm_seg = 45 * scale
    leg_seg = 52 * scale

    # Default limbs
    l_elbow = (neck_x - arm_seg * 0.6, neck_y + arm_seg * 0.7)
    l_hand = (l_elbow[0] - arm_seg * 0.4, l_elbow[1] + arm_seg * 0.7)
    r_elbow = (neck_x + arm_seg * 0.6, neck_y + arm_seg * 0.7)
    r_hand = (r_elbow[0] + arm_seg * 0.4, r_elbow[1] + arm_seg * 0.7)

    l_knee = (hip_x - leg_seg * 0.4, hip_y + leg_seg * 0.9 * sq_y)
    l_foot = (l_knee[0] - leg_seg * 0.2, l_knee[1] + leg_seg * 0.9 * sq_y)
    r_knee = (hip_x + leg_seg * 0.4, hip_y + leg_seg * 0.9 * sq_y)
    r_foot = (r_knee[0] + leg_seg * 0.2, r_knee[1] + leg_seg * 0.9 * sq_y)

    if action == "run":
        phase = (param * 6 * math.pi)
        l_knee = (hip_x + math.sin(phase) * leg_seg * 0.8, hip_y + leg_seg * 0.7)
        l_foot = (l_knee[0] + math.sin(phase - 0.5) * leg_seg * 0.8, hip_y + leg_seg * 1.5)
        r_knee = (hip_x - math.sin(phase) * leg_seg * 0.8, hip_y + leg_seg * 0.7)
        r_foot = (r_knee[0] - math.sin(phase - 0.5) * leg_seg * 0.8, hip_y + leg_seg * 1.5)
        l_elbow = (neck_x - math.sin(phase) * arm_seg * 0.9, neck_y + arm_seg * 0.4)
        l_hand = (l_elbow[0] - math.sin(phase) * arm_seg * 0.7, l_elbow[1] + arm_seg * 0.6)
        r_elbow = (neck_x + math.sin(phase) * arm_seg * 0.9, neck_y + arm_seg * 0.4)
        r_hand = (r_elbow[0] + math.sin(phase) * arm_seg * 0.7, r_elbow[1] + arm_seg * 0.6)

    elif action == "carry_heavy":
        wobble = math.sin(param * 12) * 5
        l_elbow = (neck_x - arm_seg * 0.9 + wobble, neck_y - arm_seg * 0.9)
        l_hand = (neck_x - 40 + wobble, neck_y - arm_seg * 1.8)
        r_elbow = (neck_x + arm_seg * 0.9 + wobble, neck_y - arm_seg * 0.9)
        r_hand = (neck_x + 40 + wobble, neck_y - arm_seg * 1.8)

    elif action == "swing_hammer":
        swing_p = param
        if swing_p < 0.5:
            # Raising massive hammer over head
            r_elbow = (neck_x + arm_seg * 1.3, neck_y - arm_seg * 1.4)
            r_hand = (neck_x + arm_seg * 1.8, neck_y - arm_seg * 2.2)
            l_elbow = (neck_x - arm_seg * 0.4, neck_y - arm_seg * 0.8)
            l_hand = (r_hand[0] - 25, r_hand[1] + 10)
        else:
            # Slamming down
            r_elbow = (neck_x + arm_seg * 0.8, neck_y + arm_seg * 0.7)
            r_hand = (neck_x + arm_seg * 1.8, hip_y + 20)
            l_elbow = (neck_x + arm_seg * 0.3, neck_y + arm_seg * 0.7)
            l_hand = (r_hand[0] - 25, r_hand[1])

    elif action == "pointing":
        r_elbow = (neck_x + arm_seg * 0.9, neck_y - arm_seg * 0.7)
        r_hand = (neck_x + arm_seg * 2.0, neck_y - arm_seg * 1.6)

    elif action == "celebrate":
        hop = abs(math.sin(param * 10)) * 50
        head_cy -= hop
        neck_y -= hop
        hip_y -= hop
        l_elbow = (neck_x - arm_seg * 1.2, neck_y - arm_seg * 1.4)
        l_hand = (neck_x - arm_seg * 1.8, neck_y - arm_seg * 2.2)
        r_elbow = (neck_x + arm_seg * 1.2, neck_y - arm_seg * 1.4)
        r_hand = (neck_x + arm_seg * 1.8, neck_y - arm_seg * 2.2)
        l_knee = (hip_x - leg_seg * 0.6, hip_y + leg_seg * 0.4)
        l_foot = (l_knee[0] - leg_seg * 0.4, l_knee[1] + leg_seg * 0.4)
        r_knee = (hip_x + leg_seg * 0.6, hip_y + leg_seg * 0.4)
        r_foot = (r_knee[0] + leg_seg * 0.4, r_knee[1] + leg_seg * 0.4)

    # X-Ray skeleton flash gag when zapped
    draw_col = WHITE if skeleton_flash else color

    # Draw limbs
    draw.line([(neck_x, neck_y), (hip_x, hip_y)], fill=draw_col, width=lw)
    draw.line([(neck_x, neck_y), l_elbow], fill=draw_col, width=lw)
    draw.line([l_elbow, l_hand], fill=draw_col, width=lw)
    draw.line([(neck_x, neck_y), r_elbow], fill=draw_col, width=lw)
    draw.line([r_elbow, r_hand], fill=draw_col, width=lw)
    draw.line([(hip_x, hip_y), l_knee], fill=draw_col, width=lw)
    draw.line([l_knee, l_foot], fill=draw_col, width=lw)
    draw.line([(hip_x, hip_y), r_knee], fill=draw_col, width=lw)
    draw.line([r_knee, r_foot], fill=draw_col, width=lw)

    # Head
    draw.ellipse([head_cx - r_head_eff, head_cy - r_head_eff, head_cx + r_head_eff, head_cy + r_head_eff], fill=draw_col, outline=draw_col, width=3)

    # Face details
    eye_y = head_cy - int(3 * scale)
    if face == "shock":
        draw.ellipse([head_cx - 16, eye_y - 8, head_cx - 4, eye_y + 8], outline=BG_DARK, fill=WHITE, width=3)
        draw.ellipse([head_cx + 4, eye_y - 8, head_cx + 16, eye_y + 8], outline=BG_DARK, fill=WHITE, width=3)
        draw.text((head_cx + 35, head_cy - 50), "!", fill=CRIMSON, font=font_bang)
    elif face == "strain":
        draw.line([(head_cx - 15, eye_y - 6), (head_cx - 5, eye_y), (head_cx - 15, eye_y + 6)], fill=BG_DARK, width=3)
        draw.line([(head_cx + 15, eye_y - 6), (head_cx + 5, eye_y), (head_cx + 15, eye_y + 6)], fill=BG_DARK, width=3)
        # Big animated sweat drop
        draw.ellipse([head_cx + 28, head_cy - 30, head_cx + 42, head_cy - 12], fill=CYAN)
    elif face == "happy":
        draw.arc([head_cx - 16, eye_y - 8, head_cx - 4, eye_y + 4], start=180, end=360, fill=BG_DARK, width=4)
        draw.arc([head_cx + 4, eye_y - 8, head_cx + 16, eye_y + 4], start=180, end=360, fill=BG_DARK, width=4)
    elif face == "dizzy":
        # Spiral eyes @ @
        draw.ellipse([head_cx - 15, eye_y - 8, head_cx - 3, eye_y + 8], outline=BG_DARK, width=3)
        draw.ellipse([head_cx + 3, eye_y - 8, head_cx + 15, eye_y + 8], outline=BG_DARK, width=3)
        draw.line([(head_cx - 15, eye_y), (head_cx - 3, eye_y)], fill=BG_DARK, width=3)
        draw.line([(head_cx + 3, eye_y), (head_cx + 15, eye_y)], fill=BG_DARK, width=3)
    else:
        draw.ellipse([head_cx - 12, eye_y - 5, head_cx - 6, eye_y + 5], fill=BG_DARK)
        draw.ellipse([head_cx + 6, eye_y - 5, head_cx + 12, eye_y + 5], fill=BG_DARK)

    return (r_hand[0], r_hand[1]), (neck_x, head_cy)

# -------------------------------------------------------------
# GIANT CARTOON HAMMER DRAWING
# -------------------------------------------------------------
def draw_giant_hammer(draw: ImageDraw.ImageDraw, hand_pos: tuple, swing_p: float):
    hx, hy = hand_pos
    if swing_p < 0.5:
        # Windup: angled up and back
        angle = -50 + swing_p * 40
        handle_len = 160
        rad = math.radians(angle)
        h_end_x = hx + math.cos(rad) * handle_len
        h_end_y = hy + math.sin(rad) * handle_len
        draw.line([hand_pos, (h_end_x, h_end_y)], fill=WOOD_BROWN, width=12)
        # Giant Mallet head
        draw.rounded_rectangle([h_end_x - 45, h_end_y - 35, h_end_x + 45, h_end_y + 35], radius=14, fill=METAL_GRAY, outline=WHITE, width=3)
    else:
        # Slam down: pointed downward!
        angle = 45 + (swing_p - 0.5) * 80
        handle_len = 160
        rad = math.radians(angle)
        h_end_x = hx + math.cos(rad) * handle_len
        h_end_y = hy + math.sin(rad) * handle_len
        draw.line([hand_pos, (h_end_x, h_end_y)], fill=WOOD_BROWN, width=12)
        draw.rounded_rectangle([h_end_x - 35, h_end_y - 45, h_end_x + 35, h_end_y + 45], radius=14, fill=METAL_GRAY, outline=WHITE, width=3)

# -------------------------------------------------------------
# 2X BIGGER VARIABLE BOXES & GLOWING ORBS
# -------------------------------------------------------------
def draw_big_box(draw: ImageDraw.ImageDraw, x: int, y: int, name: str, val_text: str = "", active: bool = False):
    w, h = 340, 310
    border_col = EMERALD if active else CYAN

    # Drop shadow
    draw.rounded_rectangle([x + 8, y + 8, x + w + 8, y + h + 8], radius=28, fill=(8, 12, 18))
    # Glass Body
    draw.rounded_rectangle([x, y, x + w, y + h], radius=28, fill=(22, 27, 34), outline=border_col, width=5)
    # Name Plate
    draw.rounded_rectangle([x + 40, y - 24, x + w - 40, y + 30], radius=16, fill=border_col)
    draw.text((x + w // 2, y + 3), f"variable: {name}", fill=BG_DARK, font=font_box, anchor="mm")

    if val_text:
        col = EMERALD if active else GOLD
        cx, cy = x + w // 2, y + h // 2 + 15
        # Radiant glow rings
        draw.ellipse([cx - 75, cy - 75, cx + 75, cy + 75], outline=(col[0], col[1], col[2]), width=3)
        draw.ellipse([cx - 65, cy - 65, cx + 65, cy + 65], fill=col, outline=WHITE, width=4)
        draw.text((cx, cy + 3), val_text, fill=BG_DARK, font=font_orb, anchor="mm")

# -------------------------------------------------------------
# DEDICATED LOWER EXPLANATION HUD (LOCKED BELOW FLOOR)
# -------------------------------------------------------------
def draw_bottom_hud(draw: ImageDraw.ImageDraw, title: str, subtitle: str, color=CYAN):
    hud_y = 1530
    draw.rounded_rectangle([50, hud_y, WIDTH - 50, hud_y + 160], radius=24, fill=(22, 27, 34), outline=color, width=3)
    draw.text((WIDTH // 2, hud_y + 45), title, fill=GOLD, font=font_hud, anchor="mm")
    draw.text((WIDTH // 2, hud_y + 105), subtitle, fill=WHITE, font=font_sub, anchor="mm")

# -------------------------------------------------------------
# CODE TERMINAL (UPPER ZONE)
# -------------------------------------------------------------
def draw_upper_terminal(draw: ImageDraw.ImageDraw, lines: list, active_idx: int = 0, rip_val: bool = False):
    tx, ty, tw, th = 50, 190, WIDTH - 100, 390
    draw.rounded_rectangle([tx + 8, ty + 8, tx + tw + 8, ty + th + 8], radius=24, fill=(5, 8, 15))
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=24, fill=TERMINAL_BG, outline=(48, 54, 61), width=3)

    # Controls
    draw.ellipse([tx + 25, ty + 20, tx + 45, ty + 40], fill=CRIMSON)
    draw.ellipse([tx + 55, ty + 20, tx + 75, ty + 40], fill=GOLD)
    draw.ellipse([tx + 85, ty + 20, tx + 105, ty + 40], fill=EMERALD)
    draw.text((tx + 140, ty + 16), "script.py — Visual Python Memory Engine", fill=MUTED, font=font_sub)

    y_l = ty + 80
    for i, l in enumerate(lines):
        draw.text((tx + 25, y_l), f"{i+1:2d} |", fill=(72, 79, 88), font=font_code)

        if i == active_idx:
            draw.rounded_rectangle([tx + 90, y_l - 4, tx + tw - 20, y_l + 50], radius=10, fill=(30, 58, 138), outline=CYAN, width=2)

        if i == 0 and rip_val:
            draw.text((tx + 115, y_l), "x = [   ]  <-- 5 RIPPED OUT!", fill=GOLD, font=font_code)
        else:
            col = GOLD if "print" in l else CYAN if "=" in l else WHITE
            draw.text((tx + 115, y_l), l, fill=col, font=font_code)
        y_l += 64

# -------------------------------------------------------------
# MAIN ANIMATION GENERATION: 720 FRAMES (24 SECONDS)
# -------------------------------------------------------------
def generate_ultimate_animation():
    print(f"🎬 Generating {TOTAL_FRAMES} Ultimate Frames ({TOTAL_SECONDS}s at {FPS} FPS)...")
    floor_y = 1490

    code_lines = [
        "x = 5",
        "x = x + 3",
        "y = x",
        "print(x, y)"
    ]

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS

        # Screen shake
        sh_x, sh_y = 0, 0
        if 1.0 <= t <= 1.3:
            sh_y = int(math.sin(t * 70) * 14 * (1.0 - (t - 1.0) / 0.3))
        elif 11.5 <= t <= 12.0:  # Giant hammer smash!
            decay = 1.0 - (t - 11.5) / 0.5
            sh_x = int(math.sin(t * 80) * 20 * decay)
            sh_y = int(math.cos(t * 80) * 20 * decay)
        elif 17.0 <= t <= 17.4:  # Electric zap!
            sh_x = int(math.sin(t * 90) * 12)

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Subtle cyber grid
        for gy in range(0, HEIGHT, 80):
            draw.line([(0, gy + sh_y), (WIDTH, gy + sh_y)], fill=(18, 24, 34), width=1)
        for gx in range(0, WIDTH, 80):
            draw.line([(gx + sh_x, 0), (gx + sh_x, HEIGHT)], fill=(18, 24, 34), width=1)

        # Floor Line
        draw.line([(0, floor_y + sh_y), (WIDTH, floor_y + sh_y)], fill=(56, 189, 248), width=5)

        # Top Header
        draw.rounded_rectangle([50 + sh_x, 40 + sh_y, WIDTH - 50 + sh_x, 160 + sh_y], radius=24, fill=(22, 27, 34), outline=CYAN, width=3)
        draw.text((WIDTH // 2 + sh_x, 78 + sh_y), "PYTHON VISUAL SERIES • EP 1", fill=GOLD, font=font_header, anchor="mm")
        draw.text((WIDTH // 2 + sh_x, 126 + sh_y), "Variables & Memory Pointers (No Voiceover Needed)", fill=WHITE, font=font_sub, anchor="mm")

        # -------------------------------------------------------------
        # BEATS BREAKDOWN (24 SECONDS)
        # -------------------------------------------------------------

        # --- BEAT 1: 0.0s - 4.0s (Drop from sky, Squash, Looks up at Code) ---
        if t < 4.0:
            draw_upper_terminal(draw, [code_lines[0]], active_idx=0)
            if t < 1.0:
                p = t / 1.0
                cur_y = int(-150 + (floor_y - 180 + 150) * (p ** 2))
                draw_big_stickman(draw, 540 + sh_x, cur_y + sh_y, action="jump_stretch", param=0.8, face="shock")
            elif t < 1.4:
                p = (t - 1.0) / 0.4
                draw_big_stickman(draw, 540 + sh_x, floor_y - 100 + sh_y, action="land_squash", param=1.0 - p, face="strain")
            elif t < 2.8:
                draw_big_stickman(draw, 540 + sh_x, floor_y - 180 + sh_y, action="pointing", face="shock")
            else:
                # Runs to the left to prepare
                run_p = (t - 2.8) / 1.2
                rx = int(540 - 280 * run_p)
                draw_big_stickman(draw, rx + sh_x, floor_y - 180 + sh_y, action="run", param=run_p, face="normal")

            draw_bottom_hud(draw, "STAGE 1: CREATING A VARIABLE", "Let's see what happens when Python executes 'x = 5'")

        # --- BEAT 2: 4.0s - 9.0s (Box x Drops + Stickman Rips 5 from Code into Box) ---
        elif t < 9.0:
            rel_t = t - 4.0
            box_x = 370 + sh_x
            box_y = floor_y - 360 + sh_y

            if rel_t < 1.2:
                # Box x drops with heavy thud
                p = rel_t / 1.2
                cur_by = int(600 + (box_y - 600) * (p ** 1.8))
                draw_big_box(draw, box_x, cur_by, "x", "")
                draw_upper_terminal(draw, [code_lines[0]], active_idx=0)
                draw_big_stickman(draw, 220 + sh_x, floor_y - 180 + sh_y, action="idle", face="normal")
            elif rel_t < 3.2:
                # Stickman carries golden 5 overhead!
                draw_big_box(draw, box_x, box_y, "x", "")
                draw_upper_terminal(draw, [code_lines[0]], active_idx=0, rip_val=True)
                carry_p = (rel_t - 1.2) / 2.0
                cx = int(220 + 150 * carry_p) + sh_x
                h_pos, head_pt = draw_big_stickman(draw, cx, floor_y - 180 + sh_y, action="carry_heavy", param=carry_p, face="strain")
                # Golden 5 orb carried overhead
                draw.ellipse([cx - 55, head_pt[1] - 110, cx + 55, head_pt[1]], fill=GOLD, outline=WHITE, width=4)
                draw.text((cx, head_pt[1] - 55), "5", fill=BG_DARK, font=font_orb, anchor="mm")
            else:
                # 5 safely inside box x! Stick figure happily taps box!
                draw_upper_terminal(draw, [code_lines[0]], active_idx=0)
                draw_big_box(draw, box_x, box_y, "x", "5", active=True)
                draw_big_stickman(draw, 220 + sh_x, floor_y - 180 + sh_y, action="pointing", face="happy")

            draw_bottom_hud(draw, "MEMORY ALLOCATION", "Variable 'x' is a container storing the integer value 5!")

        # --- BEAT 3: 9.0s - 15.0s (x = x + 3 -> Giant Hammer Mallet Smash into 8!) ---
        elif t < 15.0:
            rel_t = t - 9.0
            box_x = 370 + sh_x
            box_y = floor_y - 360 + sh_y
            draw_upper_terminal(draw, [code_lines[0], code_lines[1]], active_idx=1)

            if rel_t < 1.5:
                # Pulls 5 out onto the floor
                draw_big_box(draw, box_x, box_y, "x", "")
                draw.ellipse([box_x + 110, box_y - 80, box_x + 230, box_y + 40], fill=GOLD, outline=WHITE, width=4)
                draw.text((box_x + 170, box_y - 20), "5", fill=BG_DARK, font=font_orb, anchor="mm")
                draw_big_stickman(draw, 200 + sh_x, floor_y - 180 + sh_y, action="pointing", face="normal")
            elif rel_t < 2.5:
                # +3 drops from above
                p3 = (rel_t - 1.5) / 1.0
                cur_3y = int(500 + (box_y - 80 - 500) * p3)
                draw_big_box(draw, box_x, box_y, "x", "")
                draw.ellipse([box_x + 110, box_y - 80, box_x + 230, box_y + 40], fill=GOLD, outline=WHITE, width=4)
                draw.text((box_x + 170, box_y - 20), "5", fill=BG_DARK, font=font_orb, anchor="mm")
                draw.ellipse([box_x + 250, cur_3y, box_x + 370, cur_3y + 120], fill=PURPLE, outline=WHITE, width=4)
                draw.text((box_x + 310, cur_3y + 60), "+3", fill=WHITE, font=font_orb, anchor="mm")
                draw_big_stickman(draw, 180 + sh_x, floor_y - 180 + sh_y, action="idle", face="shock")
            elif rel_t < 3.8:
                # Stickman winds up GIANT CARTOON HAMMER!
                swing_p = (rel_t - 2.5) / 1.3
                draw_big_box(draw, box_x, box_y, "x", "")
                draw.ellipse([box_x + 110, box_y - 80, box_x + 230, box_y + 40], fill=GOLD, outline=WHITE, width=4)
                draw.text((box_x + 170, box_y - 20), "5", fill=BG_DARK, font=font_orb, anchor="mm")
                draw.ellipse([box_x + 250, box_y - 80, box_x + 370, box_y + 40], fill=PURPLE, outline=WHITE, width=4)
                draw.text((box_x + 310, box_y - 20), "+3", fill=WHITE, font=font_orb, anchor="mm")

                h_hand, _ = draw_big_stickman(draw, 160 + sh_x, floor_y - 180 + sh_y, action="swing_hammer", param=swing_p, face="strain")
                draw_giant_hammer(draw, h_hand, swing_p)
            elif rel_t < 4.8:
                # HAMMER SLAMS DOWN! Explosive shockwave ring + radiating sparks!
                smash_p = (rel_t - 3.8) / 1.0
                draw_big_box(draw, box_x, box_y, "x", "")
                # Shockwave ring
                sw_r = int(280 * smash_p)
                draw.ellipse([box_x + 170 - sw_r, box_y - 20 - sw_r, box_x + 170 + sw_r, box_y - 20 + sw_r], outline=GOLD, width=max(3, int(12 * (1.0 - smash_p))))
                # Radiant sparks
                for deg in range(0, 360, 30):
                    rad = math.radians(deg)
                    sp1 = (box_x + 170 + math.cos(rad) * sw_r * 0.7, box_y - 20 + math.sin(rad) * sw_r * 0.7)
                    sp2 = (box_x + 170 + math.cos(rad) * sw_r, box_y - 20 + math.sin(rad) * sw_r)
                    draw.line([sp1, sp2], fill=EMERALD, width=4)

                # Emerging glowing 8!
                draw.ellipse([box_x + 95, box_y - 95, box_x + 245, box_y + 55], fill=EMERALD, outline=WHITE, width=5)
                draw.text((box_x + 170, box_y - 20), "8", fill=BG_DARK, font=font_orb, anchor="mm")

                h_hand, _ = draw_big_stickman(draw, 160 + sh_x, floor_y - 180 + sh_y, action="swing_hammer", param=0.9, face="happy")
                draw_giant_hammer(draw, h_hand, 0.9)
            else:
                # 8 drops into box x!
                draw_big_box(draw, box_x, box_y, "x", "8", active=True)
                draw_big_stickman(draw, 180 + sh_x, floor_y - 180 + sh_y, action="idle", face="happy")

            draw_bottom_hud(draw, "STAGE 2: REASSIGNMENT (x = x + 3)", "5 and 3 fuse together into a brand new object: 8!")

        # --- BEAT 4: 15.0s - 19.5s (y = x -> Jumper Cable + Funny Skeleton Zap Gag!) ---
        elif t < 19.5:
            rel_t = t - 15.0
            draw_upper_terminal(draw, [code_lines[0], code_lines[1], code_lines[2]], active_idx=2)

            box_x = 160 + sh_x
            box_y = 580 + sh_x
            b_y = floor_y - 360 + sh_y

            draw_big_box(draw, box_x, b_y, "x", "8", active=True)
            draw_big_box(draw, box_y, b_y, "y", "8", active=True)

            # Jumper cable
            start_p = (box_y, b_y + 150)
            end_p = (box_x + 340, b_y + 150)
            wire_p = min(1.0, rel_t / 1.0)
            cur_wx = int(start_p[0] - (start_p[0] - end_p[0]) * wire_p)
            draw.line([start_p, (cur_wx, b_y + 150)], fill=CYAN, width=9)

            # Electric arcs
            if wire_p >= 1.0:
                for arc_x in range(end_p[0] + 20, start_p[0] - 20, 35):
                    arc_h = int(math.sin(arc_x + t * 50) * 18)
                    draw.line([(arc_x, b_y + 150), (arc_x + 15, b_y + 150 + arc_h)], fill=WHITE, width=4)

            # Stickman touches wire and gets zapped gag!
            if 1.8 <= rel_t <= 2.4:
                # Skeleton flash!
                draw_big_stickman(draw, 500 + sh_x, floor_y - 180 + sh_y, action="jump_stretch", param=0.9, face="shock", skeleton_flash=True)
            elif 2.4 < rel_t <= 3.5:
                # Shakes head with dizzy eyes
                draw_big_stickman(draw, 500 + sh_x, floor_y - 180 + sh_y, action="idle", face="dizzy")
            else:
                # Thumbs up!
                draw_big_stickman(draw, 500 + sh_x, floor_y - 180 + sh_y, action="pointing", face="happy")

            draw_bottom_hud(draw, "STAGE 3: THE MEMORY SECRET (y = x)", "y does NOT duplicate 8. Both variables point to the SAME object!")

        # --- BEAT 5: 19.5s - 24.0s (Stomps RUN Button -> Neon Output & Celebration!) ---
        else:
            rel_t = t - 19.5
            draw_upper_terminal(draw, code_lines, active_idx=3)

            box_x = 160 + sh_x
            box_y = 580 + sh_x
            b_y = floor_y - 360 + sh_y

            draw_big_box(draw, box_x, b_y, "x", "8", active=True)
            draw_big_box(draw, box_y, b_y, "y", "8", active=True)

            # Big Arcade RUN Button on Floor
            draw.rounded_rectangle([480, floor_y - 40, 600, floor_y], radius=10, fill=CRIMSON, outline=WHITE, width=3)
            draw.text((540, floor_y - 20), "RUN", fill=WHITE, font=font_sub, anchor="mm")

            # Celebrating stick figure in center
            draw_big_stickman(draw, 540 + sh_x, floor_y - 180 + sh_y, action="celebrate", param=rel_t, face="happy")

            # Terminal Output & CTA Banner locked below floor
            draw.rounded_rectangle([50, 1530, WIDTH - 50, 1680], radius=24, fill=(5, 8, 15), outline=EMERALD, width=4)
            draw.text((WIDTH // 2, 1570), "TERMINAL OUTPUT:", fill=MUTED, font=font_sub, anchor="mm")
            draw.text((WIDTH // 2, 1630), ">>> 8   8", fill=EMERALD, font=font_header, anchor="mm")

            draw.rounded_rectangle([50, 1710, WIDTH - 50, 1850], radius=24, fill=(220, 38, 38), outline=WHITE, width=3)
            draw.text((WIDTH // 2, 1755), "FOLLOW FOR EPISODE 2! 🚀", fill=WHITE, font=font_header, anchor="mm")
            draw.text((WIDTH // 2, 1805), "Next: 'How If-Else Decision Gates Work!'", fill=GOLD, font=font_sub, anchor="mm")

        # Save Frame
        f_path = FRAMES_DIR / f"frame_{frame:04d}.png"
        img.save(f_path)

        if frame % 120 == 0:
            print(f"  Frame {frame}/{TOTAL_FRAMES} rendered ({frame/TOTAL_FRAMES*100:.0f}%)...")

    print("  ✅ All 720 Ultimate frames rendered!")

# -------------------------------------------------------------
# FFMPEG COMPOSITOR: ZERO MUSIC • 100% ASMR SOUND EFFECTS
# -------------------------------------------------------------
def composite_ultimate_video():
    print("\nCompositing 24s video with 100% PURE ASMR SOUND EFFECTS (NO MUSIC)...")
    final_video = RENDERED_DIR / "alan_becker_python_ep1_ultimate.mp4"

    # Synchronized Foley & Sound Effects Timeline:
    # 1.0s: heavy_slam (Stickman lands on floor)
    # 2.8s: footsteps (Stickman runs to left)
    # 4.0s: thud (Box x drops)
    # 5.5s: squeak (Ripping 5 from code)
    # 7.2s: glass_tap (5 drops in box x)
    # 9.2s: keyboard (Typing x = x + 3)
    # 11.2s: hammer_swing (Hammer windup whoosh)
    # 12.8s: shockwave (KABLAM! Hammer smash 5 and 3 into 8)
    # 15.0s: thud (Box y drops)
    # 16.0s: footsteps (Runs with jumper wire)
    # 17.0s: electric_buzz (Zap! Touching live wire)
    # 19.5s: boing (Stomps RUN button)
    # 20.0s: chime (Victory output 8 8)

    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(SFX_DIR / "heavy_slam.wav"),
        "-i", str(SFX_DIR / "footsteps.wav"),
        "-i", str(SFX_DIR / "thud.wav"),
        "-i", str(SFX_DIR / "squeak.wav"),
        "-i", str(SFX_DIR / "glass_tap.wav"),
        "-i", str(SFX_DIR / "keyboard.wav"),
        "-i", str(SFX_DIR / "hammer_swing.wav"),
        "-i", str(SFX_DIR / "shockwave.wav"),
        "-i", str(SFX_DIR / "electric_buzz.wav"),
        "-i", str(SFX_DIR / "boing.wav"),
        "-i", str(SFX_DIR / "chime.wav"),
        "-t", str(TOTAL_SECONDS),
        "-filter_complex",
        (
            "[1:a]adelay=1000|1000,volume=1.0[s1];"
            "[2:a]adelay=2800|2800,volume=0.9[s2];"
            "[3:a]adelay=4000|4000,volume=1.0[s3];"
            "[4:a]adelay=5500|5500,volume=0.8[s4];"
            "[5:a]adelay=7200|7200,volume=1.1[s5];"
            "[6:a]adelay=9200|9200,volume=0.8[s6];"
            "[7:a]adelay=11200|11200,volume=1.0[s7];"
            "[8:a]adelay=12800|12800,volume=1.3[s8];"
            "[3:a]adelay=15000|15000,volume=1.0[s9];"
            "[2:a]adelay=16000|16000,volume=0.9[s10];"
            "[9:a]adelay=17000|17000,volume=1.1[s11];"
            "[10:a]adelay=19500|19500,volume=1.0[s12];"
            "[11:a]adelay=20000|20000,volume=1.2[s13];"
            "[s1][s2][s3][s4][s5][s6][s7][s8][s9][s10][s11][s12][s13]amix=inputs=13:duration=first:dropout_transition=0[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]

    print("Running FFmpeg composite with pure sound design...")
    subprocess.run(cmd, check=True)
    mb = final_video.stat().st_size / (1024 * 1024)
    print(f"\n==================================================================")
    print(f"🎉 ALAN BECKER ULTIMATE EDITION COMPLETE!")
    print(f"Path: {final_video}")
    print(f"Size: {mb:.2f} MB | Duration: {TOTAL_SECONDS}s | FPS: {FPS}")
    print(f"==================================================================")

if __name__ == "__main__":
    generate_ultimate_animation()
    composite_ultimate_video()

