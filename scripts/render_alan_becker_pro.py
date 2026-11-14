"""Alan Becker 'Animation vs. Coding' PRO Edition (60 FPS).

Features:
- Skeletal Stick Figure Rig with 2-segment limbs (knees, elbows, feet, hands)
- Expressive Face (wide eyes, squint, happy eyes, floating cartoon '!' and sweat drop)
- Squash & Stretch physics + dynamic camera screen shake
- Dust puff particles on landing/running
- Impact shockwave rings and spark particle bursts
- Interactive Physical Code (Rips '5' from code line, smashes '5' and '+3' with hammer, connects jumper wire)
- Synchronized Sound Design (Heavy slam, Boing, Skid, Shockwave, Squeak, Keyboard, Chime)
- High-energy arcade gaming soundtrack
- 1080x1920 (9:16 Vertical Short) at 60 FPS
"""

import os
import sys
import math
import random
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary

FFMPEG = get_ffmpeg_binary()
WORKSPACE_DIR = Path(os.getcwd())
STORAGE = WORKSPACE_DIR / "media_storage"
TEMP_DIR = STORAGE / "temp" / "alan_becker_pro"
FRAMES_DIR = TEMP_DIR / "frames"
RENDERED_DIR = STORAGE / "rendered"
SFX_DIR = STORAGE / "assets" / "sfx"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 60
TOTAL_SECONDS = 15.0
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Color Palette (Alan Becker Meets Cyberpunk IDE)
STICK_ORANGE = (255, 128, 0)
STICK_HEAD = (255, 140, 20)
CYAN = (56, 189, 248)
GOLD = (250, 204, 21)
EMERALD = (34, 197, 94)
CRIMSON = (239, 68, 68)
PURPLE = (168, 85, 247)
BG_DARK = (13, 17, 23)           # GitHub Dark Dimmed
TERMINAL_BG = (22, 27, 34)
WHITE = (255, 255, 255)
MUTED = (139, 148, 158)

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

font_header = get_font("bold", 52)
font_sub = get_font("bold", 32)
font_code = get_font("mono", 38)
font_box = get_font("bold", 42)
font_orb = get_font("bold", 50)
font_term = get_font("mono", 36)
font_bang = get_font("bold", 60)

# -------------------------------------------------------------
# ADVANCED ARTICULATED SKELETAL RIG
# -------------------------------------------------------------
def draw_pro_stickman(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    action: str = "idle",
    param: float = 0.0,
    face: str = "normal",
    color = STICK_ORANGE,
    scale: float = 1.0
):
    """Draws an expressive, multi-jointed stick figure with realistic physics & squash/stretch."""
    lw = max(5, int(8 * scale))
    r_head = int(30 * scale)

    # Squash and stretch factor
    sq_x, sq_y = 1.0, 1.0
    if action == "land_squash":
        sq_y = max(0.55, 1.0 - param * 0.45)
        sq_x = min(1.4, 1.0 + param * 0.4)
    elif action == "jump_stretch":
        sq_y = min(1.35, 1.0 + param * 0.35)
        sq_x = max(0.75, 1.0 - param * 0.25)

    torso_h = int(95 * scale * sq_y)
    r_head_eff = int(r_head * ((sq_x + sq_y) / 2))

    hip_x, hip_y = x, y
    neck_x, neck_y = x, y - torso_h
    head_cx, head_cy = x, neck_y - r_head_eff

    # Limbs kinematics
    arm_seg = 40 * scale
    leg_seg = 45 * scale

    # Defaults
    l_elbow = (neck_x - arm_seg * 0.6, neck_y + arm_seg * 0.7)
    l_hand = (l_elbow[0] - arm_seg * 0.4, l_elbow[1] + arm_seg * 0.7)
    r_elbow = (neck_x + arm_seg * 0.6, neck_y + arm_seg * 0.7)
    r_hand = (r_elbow[0] + arm_seg * 0.4, r_elbow[1] + arm_seg * 0.7)

    l_knee = (hip_x - leg_seg * 0.4, hip_y + leg_seg * 0.9 * sq_y)
    l_foot = (l_knee[0] - leg_seg * 0.2, l_knee[1] + leg_seg * 0.9 * sq_y)
    r_knee = (hip_x + leg_seg * 0.4, hip_y + leg_seg * 0.9 * sq_y)
    r_foot = (r_knee[0] + leg_seg * 0.2, r_knee[1] + leg_seg * 0.9 * sq_y)

    # Pose logic
    if action == "run":
        # Cycle 0 to 1
        phase = (param * 4 * math.pi)
        l_knee = (hip_x + math.sin(phase) * leg_seg * 0.8, hip_y + leg_seg * 0.7)
        l_foot = (l_knee[0] + math.sin(phase - 0.5) * leg_seg * 0.8, hip_y + leg_seg * 1.6)
        r_knee = (hip_x - math.sin(phase) * leg_seg * 0.8, hip_y + leg_seg * 0.7)
        r_foot = (r_knee[0] - math.sin(phase - 0.5) * leg_seg * 0.8, hip_y + leg_seg * 1.6)
        # Arms pump opposite
        l_elbow = (neck_x - math.sin(phase) * arm_seg * 0.9, neck_y + arm_seg * 0.5)
        l_hand = (l_elbow[0] - math.sin(phase) * arm_seg * 0.8, l_elbow[1] + arm_seg * 0.6)
        r_elbow = (neck_x + math.sin(phase) * arm_seg * 0.9, neck_y + arm_seg * 0.5)
        r_hand = (r_elbow[0] + math.sin(phase) * arm_seg * 0.8, r_elbow[1] + arm_seg * 0.6)

    elif action == "carry_heavy":
        # Hands straining upward, knees slightly bent
        wobble = math.sin(param * 15) * 4
        l_elbow = (neck_x - arm_seg * 0.8 + wobble, neck_y - arm_seg * 0.8)
        l_hand = (neck_x - 30 + wobble, neck_y - arm_seg * 1.6)
        r_elbow = (neck_x + arm_seg * 0.8 + wobble, neck_y - arm_seg * 0.8)
        r_hand = (neck_x + 30 + wobble, neck_y - arm_seg * 1.6)

    elif action == "smash_hammer":
        # Raising hammer then slamming down
        smash_progress = param  # 0 to 1
        if smash_progress < 0.5:
            # Windup
            w_t = smash_progress / 0.5
            r_elbow = (neck_x + arm_seg * 1.2, neck_y - arm_seg * 1.2)
            r_hand = (neck_x + arm_seg * 1.6, neck_y - arm_seg * 1.8)
            l_elbow = (neck_x - arm_seg * 0.5, neck_y - arm_seg * 0.5)
            l_hand = (r_hand[0] - 15, r_hand[1])
        else:
            # Slam down
            s_t = (smash_progress - 0.5) / 0.5
            r_elbow = (neck_x + arm_seg * 0.8, neck_y + arm_seg * 0.6)
            r_hand = (neck_x + arm_seg * 1.5, hip_y + 10)
            l_elbow = (neck_x + arm_seg * 0.2, neck_y + arm_seg * 0.6)
            l_hand = (r_hand[0] - 15, r_hand[1])

    elif action == "pointing":
        r_elbow = (neck_x + arm_seg * 0.8, neck_y - arm_seg * 0.6)
        r_hand = (neck_x + arm_seg * 1.8, neck_y - arm_seg * 1.5)

    elif action == "celebrate":
        # Jump in mid-air with high V arms
        hop = math.sin(param * 12) * 35
        head_cy -= hop
        neck_y -= hop
        hip_y -= hop
        l_elbow = (neck_x - arm_seg * 1.1, neck_y - arm_seg * 1.2)
        l_hand = (neck_x - arm_seg * 1.6, neck_y - arm_seg * 2.0)
        r_elbow = (neck_x + arm_seg * 1.1, neck_y - arm_seg * 1.2)
        r_hand = (neck_x + arm_seg * 1.6, neck_y - arm_seg * 2.0)
        l_knee = (hip_x - leg_seg * 0.6, hip_y + leg_seg * 0.4)
        l_foot = (l_knee[0] - leg_seg * 0.4, l_knee[1] + leg_seg * 0.4)
        r_knee = (hip_x + leg_seg * 0.6, hip_y + leg_seg * 0.4)
        r_foot = (r_knee[0] + leg_seg * 0.4, r_knee[1] + leg_seg * 0.4)

    # Draw body segments
    # Torso
    draw.line([(neck_x, neck_y), (hip_x, hip_y)], fill=color, width=lw)
    # Left Arm
    draw.line([(neck_x, neck_y), l_elbow], fill=color, width=lw)
    draw.line([l_elbow, l_hand], fill=color, width=lw)
    # Right Arm
    draw.line([(neck_x, neck_y), r_elbow], fill=color, width=lw)
    draw.line([r_elbow, r_hand], fill=color, width=lw)
    # Left Leg
    draw.line([(hip_x, hip_y), l_knee], fill=color, width=lw)
    draw.line([l_knee, l_foot], fill=color, width=lw)
    # Right Leg
    draw.line([(hip_x, hip_y), r_knee], fill=color, width=lw)
    draw.line([r_knee, r_foot], fill=color, width=lw)

    # Head
    draw.ellipse([head_cx - r_head_eff, head_cy - r_head_eff, head_cx + r_head_eff, head_cy + r_head_eff], fill=STICK_HEAD, outline=color, width=3)

    # Face details (Alan Becker style personality)
    eye_r = max(2, int(3.5 * scale))
    eye_y = head_cy - int(3 * scale)
    if face == "normal":
        draw.ellipse([head_cx - 8, eye_y - eye_r, head_cx - 4, eye_y + eye_r], fill=BG_DARK)
        draw.ellipse([head_cx + 4, eye_y - eye_r, head_cx + 8, eye_y + eye_r], fill=BG_DARK)
    elif face == "shock":
        # Wide hollow eyes + '!'
        draw.ellipse([head_cx - 12, eye_y - 6, head_cx - 4, eye_y + 6], outline=BG_DARK, width=2)
        draw.ellipse([head_cx + 4, eye_y - 6, head_cx + 12, eye_y + 6], outline=BG_DARK, width=2)
        draw.text((head_cx + 25, head_cy - 40), "!", fill=CRIMSON, font=font_bang)
    elif face == "strain":
        # Squeezed eyes > < + sweat drop
        draw.line([(head_cx - 11, eye_y - 4), (head_cx - 4, eye_y), (head_cx - 11, eye_y + 4)], fill=BG_DARK, width=2)
        draw.line([(head_cx + 11, eye_y - 4), (head_cx + 4, eye_y), (head_cx + 11, eye_y + 4)], fill=BG_DARK, width=2)
        draw.ellipse([head_cx + 22, head_cy - 20, head_cx + 30, head_cy - 8], fill=CYAN)
    elif face == "happy":
        # Arc eyes ^ ^
        draw.arc([head_cx - 11, eye_y - 5, head_cx - 3, eye_y + 3], start=180, end=360, fill=BG_DARK, width=3)
        draw.arc([head_cx + 3, eye_y - 5, head_cx + 11, eye_y + 3], start=180, end=360, fill=BG_DARK, width=3)

    return (r_hand[0], r_hand[1]), (neck_x, head_cy)

# -------------------------------------------------------------
# VFX HELPERS: DUST, SHOCKWAVE, GLOW ORB, LASER
# -------------------------------------------------------------
def draw_dust_puff(draw: ImageDraw.ImageDraw, x: float, y: float, progress: float):
    if progress <= 0 or progress >= 1.0:
        return
    r = int(25 * progress)
    alpha_decay = int(255 * (1.0 - progress))
    col = (139, 148, 158, alpha_decay)
    draw.ellipse([x - r * 1.5, y - r, x - r * 0.5, y + r * 0.4], outline=col, width=2)
    draw.ellipse([x + r * 0.5, y - r, x + r * 1.5, y + r * 0.4], outline=col, width=2)

def draw_shockwave(draw: ImageDraw.ImageDraw, cx: float, cy: float, progress: float, color=GOLD):
    if progress <= 0 or progress >= 1.0:
        return
    radius = int(220 * progress)
    lw = max(2, int(10 * (1.0 - progress)))
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=color, width=lw)
    # Radiating sparks
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        sp_x1 = cx + math.cos(rad) * (radius * 0.7)
        sp_y1 = cy + math.sin(rad) * (radius * 0.7)
        sp_x2 = cx + math.cos(rad) * radius
        sp_y2 = cy + math.sin(rad) * radius
        draw.line([(sp_x1, sp_y1), (sp_x2, sp_y2)], fill=color, width=3)

def draw_cyber_box(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, val_text: str = "", active: bool = False, scale: float = 1.0):
    w = int(260 * scale)
    h = int(240 * scale)
    border_col = EMERALD if active else CYAN

    # Drop shadow
    draw.rounded_rectangle([x + 6, y + 6, x + w + 6, y + h + 6], radius=24, fill=(8, 12, 18))
    # Glass Body
    draw.rounded_rectangle([x, y, x + w, y + h], radius=24, fill=(22, 27, 34), outline=border_col, width=4)
    # Top Name Tag
    draw.rounded_rectangle([x + 30, y - 20, x + w - 30, y + 24], radius=14, fill=border_col)
    draw.text((x + w // 2, y + 2), f"var: {label}", fill=BG_DARK, font=font_box, anchor="mm")

    if val_text:
        col = EMERALD if active else GOLD
        cx, cy = x + w // 2, y + h // 2 + 10
        # Multi-layer glow
        draw.ellipse([cx - 58, cy - 58, cx + 58, cy + 58], outline=(col[0], col[1], col[2]), width=2)
        draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=col, outline=WHITE, width=3)
        draw.text((cx, cy + 2), val_text, fill=BG_DARK, font=font_orb, anchor="mm")

# -------------------------------------------------------------
# CODE TERMINAL WINDOW
# -------------------------------------------------------------
def draw_terminal(draw: ImageDraw.ImageDraw, lines: list, active_idx: int = 0, rip_line_num: int = -1):
    tx, ty, tw, th = 60, 230, WIDTH - 120, 390
    draw.rounded_rectangle([tx + 8, ty + 8, tx + tw + 8, ty + th + 8], radius=24, fill=(5, 8, 15))
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=24, fill=TERMINAL_BG, outline=(48, 54, 61), width=3)

    # Mac dots
    draw.ellipse([tx + 24, ty + 20, tx + 44, ty + 40], fill=CRIMSON)
    draw.ellipse([tx + 54, ty + 20, tx + 74, ty + 40], fill=GOLD)
    draw.ellipse([tx + 84, ty + 20, tx + 104, ty + 40], fill=EMERALD)
    draw.text((tx + 140, ty + 16), "main.py — Python 3.12 (Interactive Memory)", fill=MUTED, font=font_sub)

    y_l = ty + 80
    for i, l in enumerate(lines):
        num_str = f"{i + 1:2d} |"
        draw.text((tx + 25, y_l), num_str, fill=(72, 79, 88), font=font_code)

        if i == active_idx:
            draw.rounded_rectangle([tx + 90, y_l - 4, tx + tw - 20, y_l + 46], radius=10, fill=(30, 58, 138), outline=CYAN, width=2)

        # Syntax color
        if i == rip_line_num:
            # Code value is missing / ripped out!
            draw.text((tx + 110, y_l), "x = [   ]  <-- VALUE RIPPED OUT!", fill=GOLD, font=font_code)
        else:
            col = GOLD if "print" in l else CYAN if "=" in l else WHITE
            draw.text((tx + 110, y_l), l, fill=col, font=font_code)
        y_l += 58

# -------------------------------------------------------------
# MAIN RENDER LOOP: 900 FRAMES (60 FPS)
# -------------------------------------------------------------
def render_pro_animation():
    print(f"🎬 Rendering {TOTAL_FRAMES} Pro Animation Frames (60 FPS)...")
    floor_y = 1530

    code_lines = [
        "x = 5",
        "x = x + 3",
        "y = x",
        "print(x, y)"
    ]

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS

        # Screen shake offset
        shake_x, shake_y = 0, 0
        if 0.8 <= t <= 1.1:
            decay = 1.0 - (t - 0.8) / 0.3
            shake_y = int(math.sin(t * 70) * 12 * decay)
        elif 7.8 <= t <= 8.2:  # Smash impact shake!
            decay = 1.0 - (t - 7.8) / 0.4
            shake_x = int(math.sin(t * 80) * 16 * decay)
            shake_y = int(math.cos(t * 80) * 16 * decay)
        elif 12.0 <= t <= 12.3:  # Electric zap plug
            decay = 1.0 - (t - 12.0) / 0.3
            shake_x = int(math.sin(t * 90) * 10 * decay)

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Background grid
        for gy in range(0, HEIGHT, 80):
            draw.line([(0, gy + shake_y), (WIDTH, gy + shake_y)], fill=(18, 24, 34), width=1)
        for gx in range(0, WIDTH, 80):
            draw.line([(gx + shake_x, 0), (gx + shake_x, HEIGHT)], fill=(18, 24, 34), width=1)

        # Floor line
        draw.line([(0, floor_y + shake_y), (WIDTH, floor_y + shake_y)], fill=(48, 54, 61), width=4)

        # Header Title
        draw.rounded_rectangle([60 + shake_x, 60 + shake_y, WIDTH - 60 + shake_x, 185 + shake_y], radius=24, fill=(22, 27, 34), outline=CYAN, width=3)
        draw.text((WIDTH // 2 + shake_x, 100 + shake_y), "PYTHON VISUAL SERIES • EP 1", fill=GOLD, font=font_header, anchor="mm")
        draw.text((WIDTH // 2 + shake_x, 150 + shake_y), "How Variables & Memory Pointers Actually Work!", fill=WHITE, font=font_sub, anchor="mm")

        # -------------------------------------------------------------
        # TIMELINE PHASES (60 FPS)
        # -------------------------------------------------------------

        # --- PHASE 1: 0.0s - 2.8s (Stickman Drops, Squashes, Looks at Code) ---
        if t < 2.8:
            draw_terminal(draw, [code_lines[0]], active_idx=0)
            if t < 0.8:
                # Falling from sky
                drop_t = t / 0.8
                cur_y = int(-120 + (floor_y - 140 + 120) * (drop_t ** 2))
                draw_pro_stickman(draw, 540 + shake_x, cur_y + shake_y, action="jump_stretch", param=0.8, face="shock", scale=1.4)
            elif t < 1.1:
                # Squash on impact with dust
                p = (t - 0.8) / 0.3
                draw_pro_stickman(draw, 540 + shake_x, floor_y - 80 + shake_y, action="land_squash", param=1.0 - p, face="strain", scale=1.4)
                draw_dust_puff(draw, 540 + shake_x, floor_y + shake_y, p)
            elif t < 2.0:
                # Points up at code
                draw_pro_stickman(draw, 540 + shake_x, floor_y - 140 + shake_y, action="pointing", face="shock", scale=1.4)
            else:
                draw_pro_stickman(draw, 540 + shake_x, floor_y - 140 + shake_y, action="idle", face="normal", scale=1.4)

        # --- PHASE 2: 2.8s - 6.5s (Box 'x' Drops + Stickman Rips '5' from Code into Box) ---
        elif t < 6.5:
            rel_t = t - 2.8
            box_x = 410 + shake_x
            box_y = floor_y - 280 + shake_y

            if rel_t < 1.0:
                # Box drops from sky with dust
                drop_p = rel_t / 1.0
                b_y = int(600 + (box_y - 600) * (drop_p ** 1.8))
                draw_cyber_box(draw, box_x, b_y, "x", "")
                draw_terminal(draw, [code_lines[0]], active_idx=0)
                draw_pro_stickman(draw, 240 + shake_x, floor_y - 140 + shake_y, action="idle", face="normal", scale=1.4)
                if drop_p > 0.9:
                    draw_dust_puff(draw, box_x + 130, floor_y + shake_y, drop_p - 0.9)
            elif rel_t < 2.5:
                # Stickman jumps up to code line, rips 5 out!
                draw_cyber_box(draw, box_x, box_y, "x", "")
                draw_terminal(draw, [code_lines[0]], active_idx=0, rip_line_num=0)
                # Carrying 5 overhead
                walk_p = (rel_t - 1.0) / 1.5
                cur_x = int(540 - 150 * walk_p) + shake_x
                hand_pt, head_pt = draw_pro_stickman(draw, cur_x, floor_y - 140 + shake_y, action="carry_heavy", param=walk_p, face="strain", scale=1.4)
                # Golden 5 orb carried above head
                draw.ellipse([cur_x - 45, head_pt[1] - 85, cur_x + 45, head_pt[1] + 5], fill=GOLD, outline=WHITE, width=3)
                draw.text((cur_x, head_pt[1] - 40), "5", fill=BG_DARK, font=font_orb, anchor="mm")
            else:
                # 5 inside Box 'x' with pulse!
                draw_terminal(draw, [code_lines[0]], active_idx=0)
                draw_cyber_box(draw, box_x, box_y, "x", "5", active=True)
                draw_pro_stickman(draw, 240 + shake_x, floor_y - 140 + shake_y, action="idle", face="happy", scale=1.4)

                # Explanatory badge
                draw.rounded_rectangle([120, 1100, WIDTH - 120, 1200], radius=24, fill=(22, 27, 34), outline=CYAN, width=3)
                draw.text((WIDTH // 2, 1150), "Variable 'x' created: stores value 5 in memory!", fill=WHITE, font=font_sub, anchor="mm")

        # --- PHASE 3: 6.5s - 10.5s (Slamming 5 and +3 with Giant Hammer -> Fusion into 8) ---
        elif t < 10.5:
            rel_t = t - 6.5
            box_x = 410 + shake_x
            box_y = floor_y - 280 + shake_y
            draw_terminal(draw, [code_lines[0], code_lines[1]], active_idx=1)

            if rel_t < 1.3:
                # Pulling 5 out of box x onto an anvil/ground
                draw_cyber_box(draw, box_x, box_y, "x", "")
                draw.ellipse([box_x + 80, box_y - 60, box_x + 180, box_y + 40], fill=GOLD, outline=WHITE, width=3)
                draw.text((box_x + 130, box_y - 10), "5", fill=BG_DARK, font=font_orb, anchor="mm")
                draw_pro_stickman(draw, 260 + shake_x, floor_y - 140 + shake_y, action="pointing", face="normal", scale=1.4)
            elif rel_t < 2.5:
                # +3 flies in from the right, Stickman winds up hammer!
                fly_p = (rel_t - 1.3) / 1.2
                three_x = int(900 - 350 * fly_p)
                draw_cyber_box(draw, box_x, box_y, "x", "")
                draw.ellipse([box_x + 80, box_y - 60, box_x + 180, box_y + 40], fill=GOLD, outline=WHITE, width=3)
                draw.text((box_x + 130, box_y - 10), "5", fill=BG_DARK, font=font_orb, anchor="mm")
                draw.ellipse([three_x - 50, box_y - 60, three_x + 50, box_y + 40], fill=PURPLE, outline=WHITE, width=3)
                draw.text((three_x, box_y - 10), "+3", fill=WHITE, font=font_orb, anchor="mm")

                draw_pro_stickman(draw, 240 + shake_x, floor_y - 140 + shake_y, action="smash_hammer", param=fly_p * 0.5, face="strain", scale=1.4)
            elif rel_t < 3.2:
                # HAMMER SLAMS DOWN! Explosive shockwave!
                smash_p = (rel_t - 2.5) / 0.7
                draw_cyber_box(draw, box_x, box_y, "x", "")
                draw_shockwave(draw, box_x + 130, box_y - 10, smash_p, color=GOLD)
                # Golden 8 radiating
                draw.ellipse([box_x + 65, box_y - 75, box_x + 195, box_y + 55], fill=EMERALD, outline=WHITE, width=4)
                draw.text((box_x + 130, box_y - 10), "8", fill=BG_DARK, font=font_orb, anchor="mm")
                draw_pro_stickman(draw, 240 + shake_x, floor_y - 140 + shake_y, action="smash_hammer", param=0.9, face="happy", scale=1.4)
            else:
                # 8 drops into box x!
                draw_cyber_box(draw, box_x, box_y, "x", "8", active=True)
                draw_pro_stickman(draw, 240 + shake_x, floor_y - 140 + shake_y, action="idle", face="happy", scale=1.4)

            draw.rounded_rectangle([100, 1100, WIDTH - 100, 1200], radius=24, fill=(22, 27, 34), outline=EMERALD, width=3)
            draw.text((WIDTH // 2, 1150), "Reassignment: 5 + 3 evaluates to NEW object 8!", fill=EMERALD, font=font_sub, anchor="mm")

        # --- PHASE 4: 10.5s - 13.5s (y = x: Jumper Cable Plugged Directly into x's 8) ---
        elif t < 13.5:
            rel_t = t - 10.5
            draw_terminal(draw, [code_lines[0], code_lines[1], code_lines[2]], active_idx=2)

            box_x = 220 + shake_x
            box_y = 650 + shake_x
            b_y = floor_y - 280 + shake_y

            # Box x on left (holds 8), Box y on right
            draw_cyber_box(draw, box_x, b_y, "x", "8", active=True)
            draw_cyber_box(draw, box_y, b_y, "y", "8", active=True)

            # Jumper Cable with pulsating electricity
            cable_p = min(1.0, rel_t / 0.8)
            start_pt = (box_y, b_y + 120)
            end_pt = (box_x + 260, b_y + 120)
            cur_end_x = int(start_pt[0] - (start_pt[0] - end_pt[0]) * cable_p)
            draw.line([start_pt, (cur_end_x, b_y + 120)], fill=CYAN, width=7)

            if cable_p >= 1.0:
                # Electric arcs on cable
                for arc_x in range(end_pt[0] + 30, start_pt[0] - 20, 40):
                    arc_h = int(math.sin(arc_x + t * 40) * 15)
                    draw.line([(arc_x, b_y + 120), (arc_x + 15, b_y + 120 + arc_h)], fill=WHITE, width=3)

            draw_pro_stickman(draw, 540 + shake_x, floor_y - 140 + shake_y, action="pointing", face="shock", scale=1.4)

            # High IQ Insight Drawer
            draw.rounded_rectangle([80, 1100, WIDTH - 80, 1220], radius=24, fill=(22, 27, 34), outline=CYAN, width=3)
            draw.text((WIDTH // 2, 1145), "⚡ MEMORY POINTER TRUTH:", fill=GOLD, font=font_sub, anchor="mm")
            draw.text((WIDTH // 2, 1185), "y does NOT duplicate 8. Both variables point to the SAME 8!", fill=WHITE, font=font_sub, anchor="mm")

        # --- PHASE 5: 13.5s - 15.0s (Stomps RUN Button -> Matrix Printout & Backflip!) ---
        else:
            rel_t = t - 13.5
            draw_terminal(draw, code_lines, active_idx=3)

            box_x = 220 + shake_x
            box_y = 650 + shake_x
            b_y = floor_y - 280 + shake_y
            draw_cyber_box(draw, box_x, b_y, "x", "8", active=True)
            draw_cyber_box(draw, box_y, b_y, "y", "8", active=True)

            # Giant Terminal Console Output
            draw.rounded_rectangle([100, 1060, WIDTH - 100, 1200], radius=24, fill=(5, 8, 15), outline=EMERALD, width=4)
            draw.text((WIDTH // 2, 1105), "TERMINAL STDOUT:", fill=MUTED, font=font_sub, anchor="mm")
            draw.text((WIDTH // 2, 1155), ">>> 8   8", fill=EMERALD, font=font_header, anchor="mm")

            # Stickman backflip / celebration!
            draw_pro_stickman(draw, 540 + shake_x, floor_y - 140 + shake_y, action="celebrate", param=rel_t, face="happy", scale=1.4)

            # Call to Action Banner
            draw.rounded_rectangle([100, 1280, WIDTH - 100, 1410], radius=24, fill=(220, 38, 38), outline=WHITE, width=3)
            draw.text((WIDTH // 2, 1325), "FOLLOW FOR EPISODE 2! 🚀", fill=WHITE, font=font_header, anchor="mm")
            draw.text((WIDTH // 2, 1375), "Next: 'How If-Else Decision Gates Work!'", fill=GOLD, font=font_sub, anchor="mm")

        # Save Frame
        f_path = FRAMES_DIR / f"frame_{frame:04d}.png"
        img.save(f_path)

        if frame % 120 == 0:
            print(f"  Frame {frame}/{TOTAL_FRAMES} rendered ({frame/TOTAL_FRAMES*100:.0f}%)...")

    print("  ✅ All 900 Pro frames rendered at 60 FPS!")

# -------------------------------------------------------------
# FFMPEG COMPOSITOR: 60 FPS + SYNCHRONIZED CARTOON SFX + MUSIC
# -------------------------------------------------------------
def composite_pro_video():
    print("\nCompositing 60 FPS video with synchronized Alan Becker sound effects...")
    final_video = RENDERED_DIR / "alan_becker_python_ep1_pro.mp4"
    bg_music = WORKSPACE_DIR / "media_storage" / "audio" / "bg_music.mp3"

    # Synchronized Sound Triggers:
    # 0.8s: heavy_slam (Stickman lands with squash & screen shake)
    # 2.8s: whoosh (Box x drops)
    # 3.8s: squeak (Stickman strains to rip 5 from code)
    # 5.3s: thud (5 drops into box x)
    # 7.2s: keyboard (typing x = x + 3)
    # 9.0s: shockwave (Hammer smash 5 + 3 into 8!)
    # 10.5s: whoosh (Box y drops)
    # 11.3s: zap (Jumper wire plugs into 8)
    # 13.5s: boing (RUN button stomp)
    # 13.8s: chime (Victory output 8 8)

    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(bg_music),
        "-i", str(SFX_DIR / "heavy_slam.wav"),
        "-i", str(SFX_DIR / "whoosh.wav"),
        "-i", str(SFX_DIR / "squeak.wav"),
        "-i", str(SFX_DIR / "thud.wav"),
        "-i", str(SFX_DIR / "keyboard.wav"),
        "-i", str(SFX_DIR / "shockwave.wav"),
        "-i", str(SFX_DIR / "zap.wav"),
        "-i", str(SFX_DIR / "boing.wav"),
        "-i", str(SFX_DIR / "chime.wav"),
        "-t", str(TOTAL_SECONDS),
        "-filter_complex",
        (
            "[1:a]volume=0.35[bg];"
            "[2:a]adelay=800|800,volume=1.0[s_slam];"
            "[3:a]adelay=2800|2800,volume=0.9[s_whoosh1];"
            "[4:a]adelay=3800|3800,volume=0.8[s_squeak];"
            "[5:a]adelay=5300|5300,volume=0.9[s_thud];"
            "[6:a]adelay=7200|7200,volume=0.8[s_kb];"
            "[7:a]adelay=9000|9000,volume=1.2[s_shock];"
            "[3:a]adelay=10500|10500,volume=0.9[s_whoosh2];"
            "[8:a]adelay=11300|11300,volume=1.0[s_zap];"
            "[9:a]adelay=13500|13500,volume=1.0[s_boing];"
            "[10:a]adelay=13800|13800,volume=1.3[s_chime];"
            "[bg][s_slam][s_whoosh1][s_squeak][s_thud][s_kb][s_shock][s_whoosh2][s_zap][s_boing][s_chime]amix=inputs=11:duration=first:dropout_transition=0[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]

    print("Running final FFmpeg composite...")
    subprocess.run(cmd, check=True)
    size_mb = final_video.stat().st_size / (1024 * 1024)
    print(f"\n==================================================================")
    print(f"🔥 ALAN BECKER PRO EDITION ANIMATION COMPLETE!")
    print(f"Path: {final_video}")
    print(f"Size: {size_mb:.2f} MB | Duration: {TOTAL_SECONDS}s | FPS: {FPS} (60FPS)")
    print(f"==================================================================")

if __name__ == "__main__":
    render_pro_animation()
    composite_pro_video()

