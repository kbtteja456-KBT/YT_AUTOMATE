"""Production Master Animation Studio: Python Ep 2 (Types & The int+str Collision).
Target Channel: Main Channel (Python Master - @bhanuteja-8)

Exact Fixes:
1. Proper Desk, Chair & Laptop facing stickman (screen tilted right toward his eyes, keyboard directly under his tapping hands).
2. Character-by-character progressive typing for EVERY line with moving cursor.
3. STORY FLOW: Types BUGGY CODE FIRST (age + name) -> CRASHES in Terminal -> Confused stickman -> FIXES CODE with str(age) -> SUCCESS & CELEBRATION!
4. Highlight bars drawn UNDERNEATH code text (code is 100% visible and sharp, zero covering blocks!).
5. Rich multi-track SFX: Footsteps entering, chair sit, continuous keyboard typing clacks, enter pops, error buzzer, victory chime, ambient bed.
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
TEMP_DIR = STORAGE / "temp" / "python_ep2_master"
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
TOTAL_SECONDS = 42.0
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Color Palette
BG_COLOR = (11, 14, 20)
STICK_YELLOW = (255, 215, 0)
CYAN_KEYWORD = (56, 189, 248)
GREEN_STRING = (74, 222, 128)
AMBER_NUMBER = (251, 191, 36)
PURPLE_OP = (192, 132, 252)
WHITE_VAR = (255, 255, 255)
MUTED_TEXT = (148, 163, 184)
ERROR_RED = (239, 68, 68)
SUCCESS_GREEN = (34, 197, 94)
CARD_BG = (18, 23, 33)
CARD_BORDER = (35, 45, 65)
TERMINAL_BG = (10, 13, 20)
TERMINAL_BORDER = (30, 38, 55)
LAPTOP_SILVER = (215, 225, 238)
LAPTOP_SCREEN = (25, 45, 75)

# Fonts
try:
    FONT_CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 36)
    FONT_CODE_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 36)
    FONT_HEADER = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 46)
    FONT_SUBTITLE = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 24)
    FONT_TERM = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 28)
    FONT_TERM_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 30)
    FONT_ALERT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
except Exception:
    FONT_CODE = ImageFont.load_default()
    FONT_CODE_BOLD = ImageFont.load_default()
    FONT_HEADER = ImageFont.load_default()
    FONT_SUBTITLE = ImageFont.load_default()
    FONT_TERM = ImageFont.load_default()
    FONT_TERM_BOLD = ImageFont.load_default()
    FONT_ALERT = ImageFont.load_default()


def draw_python_logo(draw, cx, cy, size=40):
    draw.rounded_rectangle([cx - size, cy - size, cx, cy + size // 4], radius=size // 4, fill=(55, 118, 171))
    draw.rounded_rectangle([cx - size, cy - size, cx + size // 2, cy - size // 4], radius=size // 4, fill=(55, 118, 171))
    draw.ellipse([cx - size // 2 - 4, cy - size // 2 - 4, cx - size // 2 + 4, cy - size // 2 + 4], fill=(255, 255, 255))
    draw.rounded_rectangle([cx, cy - size // 4, cx + size, cy + size], radius=size // 4, fill=(255, 212, 59))
    draw.rounded_rectangle([cx - size // 2, cy + size // 4, cx + size, cy + size], radius=size // 4, fill=(255, 212, 59))
    draw.ellipse([cx + size // 2 - 4, cy + size // 2 - 4, cx + size // 2 + 4, cy + size // 2 + 4], fill=(11, 14, 20))


def draw_centered_badge(draw, cx, cy, text, font, fill_color, text_color, outline_color, pad_x=24, pad_y=10):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    rx0 = cx - tw // 2 - pad_x
    ry0 = cy - th // 2 - pad_y
    rx1 = cx + tw // 2 + pad_x
    ry1 = cy + th // 2 + pad_y
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=(ry1 - ry0) // 2, fill=fill_color, outline=outline_color, width=2)
    draw.text((cx - tw // 2, cy - th // 2 - 2), text, fill=text_color, font=font)


def draw_window_frame(draw, x0, y0, x1, y1, title="types_demo.py", is_terminal=False):
    bg = TERMINAL_BG if is_terminal else CARD_BG
    border = TERMINAL_BORDER if is_terminal else CARD_BORDER
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=bg, outline=border, width=2)
    hbar_h = 42
    draw.rounded_rectangle([x0, y0, x1, y0 + hbar_h], radius=16, fill=(24, 30, 44))
    draw.rectangle([x0, y0 + hbar_h - 12, x1, y0 + hbar_h], fill=(24, 30, 44))
    draw.ellipse([x0 + 18, y0 + 15, x0 + 28, y0 + 25], fill=(239, 68, 68))
    draw.ellipse([x0 + 36, y0 + 15, x0 + 46, y0 + 25], fill=(245, 158, 11))
    draw.ellipse([x0 + 54, y0 + 15, x0 + 64, y0 + 25], fill=(16, 185, 129))
    t_color = (125, 211, 252) if is_terminal else (203, 213, 225)
    draw.text((x0 + 80, y0 + 11), title, fill=t_color, font=FONT_SUBTITLE)


def draw_desk_chair_and_laptop(draw, dx=560, dy=1460, stick_pose="sit_typing", t=0.0):
    """Draw accurate desk, chair, and laptop facing the stickman with hands on keyboard."""
    # 1. Desk top & sturdy metal legs
    dw, dh = 300, 14
    dx0 = dx - dw // 2
    dx1 = dx + dw // 2
    draw.rounded_rectangle([dx0, dy, dx1, dy + dh], radius=6, fill=(45, 55, 75), outline=(70, 85, 115), width=2)
    draw.line([(dx0 + 25, dy + dh), (dx0 + 25, 1550)], fill=(70, 85, 115), width=4)
    draw.line([(dx1 - 25, dy + dh), (dx1 - 25, 1550)], fill=(70, 85, 115), width=4)

    # 2. Chair at x=730 (stickman sits facing left)
    cx, cy = 730, dy + 25
    draw.rounded_rectangle([cx - 30, cy, cx + 30, cy + 10], radius=4, fill=(55, 65, 88))
    draw.line([(cx + 25, cy - 85), (cx + 25, cy + 10)], fill=(55, 65, 88), width=5) # backrest
    draw.line([(cx, cy + 10), (cx, 1550)], fill=(40, 50, 70), width=4)               # center leg
    draw.line([(cx - 25, 1550), (cx + 25, 1550)], fill=(40, 50, 70), width=3)       # wheel base

    # 3. Laptop resting on desk at x=550 to 670 (directly in front of stickman!)
    # Keyboard base: flat on desk from x=530 to x=645
    lx_left = 530
    lx_right = 645
    draw.polygon([
        (lx_left, dy),
        (lx_right, dy),
        (lx_right - 8, dy + 8),
        (lx_left + 8, dy + 8)
    ], fill=LAPTOP_SILVER, outline=(160, 175, 195))
    
    # Trackpad
    draw.rectangle([580, dy + 2, 605, dy + 6], fill=(180, 190, 205))
    
    # Screen Hinge at lx_left (530), tilts back to the LEFT (x=495, y=dy-68)
    # The inner face of the screen faces RIGHT toward stickman's eyes!
    sx_hinge = lx_left + 5
    sy_hinge = dy
    sx_top = sx_hinge - 30
    sy_top = dy - 70
    
    # Screen outer lid
    draw.polygon([
        (sx_hinge - 4, sy_hinge),
        (sx_hinge, sy_hinge),
        (sx_top, sy_top),
        (sx_top - 4, sy_top)
    ], fill=(160, 175, 195))
    
    # Glowing screen face facing RIGHT directly at stickman!
    draw.polygon([
        (sx_hinge, sy_hinge),
        (sx_hinge + 45, sy_hinge - 15),
        (sx_top + 45, sy_top),
        (sx_top, sy_top)
    ], fill=(45, 95, 155), outline=(56, 189, 248), width=1)

    # 4. Stickman on Chair
    color = STICK_YELLOW
    head_r = 24
    hx, hy = 720, 1390
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
    neck = (hx - 4, hy + head_r)
    hip = (725, 1485) # sitting on chair
    draw.line([neck, hip], fill=color, width=7)

    # Legs under desk: hip -> knee forward -> foot down
    knee = (660, 1495)
    foot = (650, 1550)
    draw.line([hip, knee], fill=color, width=6)
    draw.line([knee, foot], fill=color, width=6)

    # Arms extending to laptop keyboard!
    shoulder = (neck[0] - 2, neck[1] + 12)
    if stick_pose == "sit_typing":
        # Hands tapping on keyboard at x=610
        t_wave = math.sin(t * 26.0) * 5.0
        elbow = (670, 1445)
        hand = (605, 1460 + t_wave)
        draw.line([shoulder, elbow], fill=color, width=6)
        draw.line([elbow, hand], fill=color, width=6)
    elif stick_pose == "sit_enter":
        # Striking Enter key
        elbow = (660, 1435)
        hand = (600, 1452)
        draw.line([shoulder, elbow], fill=color, width=6)
        draw.line([elbow, hand], fill=color, width=6)
    elif stick_pose == "confused":
        # Left hand scratching head, right hand pulled back
        elbow_scratch = (hx + 24, hy - 10)
        hand_scratch = (hx + 6, hy - 25)
        draw.line([shoulder, elbow_scratch], fill=color, width=6)
        draw.line([elbow_scratch, hand_scratch], fill=color, width=6)
        draw.line([shoulder, (shoulder[0] - 25, shoulder[1] + 20)], fill=color, width=6)
        draw.text((hx - 40, hy - 65), "?", fill=ERROR_RED, font=FONT_HEADER)
        draw.text((hx + 30, hy - 75), "?", fill=AMBER_NUMBER, font=FONT_HEADER)
    elif stick_pose == "celebrate":
        # Victory arms up + stars
        draw.line([shoulder, (shoulder[0] - 35, shoulder[1] - 25)], fill=color, width=6)
        draw.line([(shoulder[0] - 35, shoulder[1] - 25), (shoulder[0] - 55, shoulder[1] - 55)], fill=color, width=6)
        draw.line([shoulder, (shoulder[0] + 35, shoulder[1] - 25)], fill=color, width=6)
        draw.line([(shoulder[0] + 35, shoulder[1] - 25), (shoulder[0] + 55, shoulder[1] - 55)], fill=color, width=6)
        for sx, sy in [(hx - 60, hy - 40), (hx + 65, hy - 45), (hx, hy - 65)]:
            draw.text((sx, sy), "★", fill=(250, 204, 21), font=FONT_HEADER)
    else: # sit_idle
        elbow = (675, 1450)
        hand = (615, 1460)
        draw.line([shoulder, elbow], fill=color, width=6)
        draw.line([elbow, hand], fill=color, width=6)


def draw_stickman_walk(draw, walk_x=100, t=0.0):
    """Draw stickman walking in from left."""
    color = STICK_YELLOW
    head_r = 24
    hx = walk_x
    hy = 1400
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
    neck = (hx, hy + head_r)
    hip = (hx, hy + head_r + 80)
    draw.line([neck, hip], fill=color, width=7)
    
    leg_phase = math.sin(t * 14.0) * 28.0
    draw.line([hip, (hip[0] + leg_phase, 1550)], fill=color, width=6)
    draw.line([hip, (hip[0] - leg_phase, 1550)], fill=color, width=6)
    arm_phase = math.sin(t * 14.0) * 22.0
    draw.line([neck, (neck[0] - arm_phase, neck[1] + 45)], fill=color, width=6)
    draw.line([neck, (neck[0] + arm_phase, neck[1] + 45)], fill=color, width=6)


def render_code_tokens(draw, x_start, y, tokens):
    cx = x_start
    for token, color in tokens:
        draw.text((cx, y), token, fill=color, font=FONT_CODE_BOLD if color in (CYAN_KEYWORD, ERROR_RED) else FONT_CODE)
        bbox = draw.textbbox((cx, y), token, font=FONT_CODE)
        cx = bbox[2]
    return cx


def render_frame(frame_idx: int) -> Image.Image:
    t = frame_idx / FPS
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)
    
    # 1. Floor Horizon
    draw.line([(0, 1550), (WIDTH, 1550)], fill=(22, 28, 42), width=3)
    
    # 2. Header
    draw_python_logo(draw, 440, 115, size=30)
    draw.text((485, 93), "Python", fill=(255, 215, 0), font=FONT_HEADER)
    draw_centered_badge(
        draw, cx=WIDTH // 2, cy=175,
        text="EPISODE 2: DATA TYPES COLLISION",
        font=FONT_SUBTITLE,
        fill_color=(18, 24, 38),
        text_color=CYAN_KEYWORD,
        outline_color=CYAN_KEYWORD,
        pad_x=22, pad_y=8
    )
    
    # 3. Floating Code Editor Window
    ed_x0, ed_y0 = 80, 230
    ed_x1, ed_y1 = 1000, 680
    draw_window_frame(draw, ed_x0, ed_y0, ed_x1, ed_y1, title="types_collision.py", is_terminal=False)
    
    # 4. Floating Terminal Window (ALL outputs & error details appear here!)
    tm_x0, tm_y0 = 80, 720
    tm_x1, tm_y1 = 1000, 1200
    draw_window_frame(draw, tm_x0, tm_y0, tm_x1, tm_y1, title="TERMINAL - python", is_terminal=True)
    
    cursor_char = "_" if int(t * 4.0) % 2 == 0 else " "
    
    # Full Code Snippets
    l1_full = "age = 25          # int"
    l2_full = 'name = "Dev"      # str'
    l3_buggy = "print(age + name)"
    l3_fixed = "print(str(age) + name)"
    
    # =========================================================================
    # TIMELINE PHASES
    # =========================================================================
    if t < 3.0:
        # ---------------------------------------------------------------------
        # ACT 0: Walk In from Left
        # ---------------------------------------------------------------------
        walk_x = int(100 + (t / 3.0) * 620)
        draw_desk_chair_and_laptop(draw, dx=560, dy=1460, stick_pose="none", t=t)
        draw_stickman_walk(draw, walk_x=walk_x, t=t)
        draw.text((tm_x0 + 35, tm_y0 + 65), ">>> booting python interactive shell...", fill=(71, 85, 105), font=FONT_TERM)

    elif t < 14.0:
        # ---------------------------------------------------------------------
        # ACT 1: PROGRESSIVE TYPING OF BUGGY CODE FIRST!
        # ---------------------------------------------------------------------
        t_rel = t - 3.0
        draw_desk_chair_and_laptop(draw, dx=560, dy=1460, stick_pose="sit_typing", t=t)
        
        # Line 1: types age = 25
        p1 = min(1.0, max(0.0, (t_rel - 0.2) / 3.0))
        c1 = l1_full[:int(p1 * len(l1_full))]
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        x1 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)] if p1 >= 1.0 else [(c1, WHITE_VAR)])
        if p1 < 1.0:
            draw.text((x1 + 4, ed_y0 + 75), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            
        # Line 2: types name = "Dev"
        if t_rel >= 3.2:
            p2 = min(1.0, max(0.0, (t_rel - 3.2) / 3.2))
            c2 = l2_full[:int(p2 * len(l2_full))]
            draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
            x2 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)] if p2 >= 1.0 else [(c2, WHITE_VAR)])
            if p2 < 1.0:
                draw.text((x2 + 4, ed_y0 + 135), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
                
        # Line 3: types print(age + name)  (BUGGY CODE TYPED FIRST!)
        if t_rel >= 6.5:
            p3 = min(1.0, max(0.0, (t_rel - 6.5) / 3.8))
            c3 = l3_buggy[:int(p3 * len(l3_buggy))]
            draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
            x3 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("age + name", ERROR_RED), (")", PURPLE_OP)] if p3 >= 1.0 else [(c3, CYAN_KEYWORD)])
            if p3 < 1.0:
                draw.text((x3 + 4, ed_y0 + 195), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
                
        draw.text((tm_x0 + 35, tm_y0 + 65), ">>> typing code...", fill=(71, 85, 105), font=FONT_TERM)

    elif t < 23.0:
        # ---------------------------------------------------------------------
        # ACT 2: EXECUTION -> CRASH! (TypeError In Terminal, Highlight under code!)
        # ---------------------------------------------------------------------
        t_rel = t - 14.0
        pose = "sit_enter" if t_rel < 0.6 else "confused"
        draw_desk_chair_and_laptop(draw, dx=560, dy=1460, stick_pose=pose, t=t)
        
        # Code Editor: Draw highlight bar FIRST so text is drawn ON TOP!
        # Background highlight (red tint under line 3)
        draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(45, 18, 22), outline=ERROR_RED, width=2)
        
        # Render Text on top of highlight (100% visible, sharp and unblocked!)
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("age + name", ERROR_RED), (")", PURPLE_OP)])
        
        # Terminal displays the authentic Python crash
        draw.text((tm_x0 + 35, tm_y0 + 60), 'Traceback (most recent call last):', fill=ERROR_RED, font=FONT_TERM)
        draw.text((tm_x0 + 55, tm_y0 + 105), 'File "types_collision.py", line 3, in <module>', fill=MUTED_TEXT, font=FONT_TERM)
        draw.text((tm_x0 + 75, tm_y0 + 150), 'print(age + name)', fill=WHITE_VAR, font=FONT_TERM)
        draw.text((tm_x0 + 35, tm_y0 + 205), "TypeError: unsupported operand type(s)", fill=ERROR_RED, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 245), "           for +: 'int' and 'str'", fill=ERROR_RED, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 300), ">> Python cannot add integer to string directly!", fill=AMBER_NUMBER, font=FONT_TERM)

    elif t < 34.0:
        # ---------------------------------------------------------------------
        # ACT 3: THE FIX -> Types str(age) -> SUCCESS!
        # ---------------------------------------------------------------------
        t_rel = t - 23.0
        
        # Lightbulb icon appears first
        if t_rel < 2.0:
            draw.text((700, 1310), "💡 IDEA!", fill=(250, 204, 21), font=FONT_HEADER)
            
        pose = "sit_typing" if t_rel < 6.0 else ("sit_enter" if t_rel < 6.6 else "celebrate")
        draw_desk_chair_and_laptop(draw, dx=560, dy=1460, stick_pose=pose, t=t)
        
        # If entered (t_rel >= 6.0), draw GREEN highlight under line 3!
        if t_rel >= 6.0:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(16, 45, 28), outline=SUCCESS_GREEN, width=2)
            
        # Draw code text on top
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        
        # Progressive typing of fix: str(age)
        fix_p = min(1.0, max(0.0, (t_rel - 1.5) / 4.2))
        c_fix = l3_fixed[:int(fix_p * len(l3_fixed))]
        tok_fix = [
            ("print", CYAN_KEYWORD), ("(", PURPLE_OP),
            ("str", CYAN_KEYWORD), ("(", PURPLE_OP), ("age", WHITE_VAR), (") + ", PURPLE_OP),
            ("name", WHITE_VAR), (")", PURPLE_OP)
        ] if fix_p >= 1.0 else [(c_fix, CYAN_KEYWORD)]
        xf = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, tok_fix)
        if fix_p < 1.0:
            draw.text((xf + 4, ed_y0 + 195), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            
        # Terminal Output
        if t_rel >= 6.0:
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> 25Dev", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 115), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 175), ">> Converted integer 25 into string '25'!", fill=GREEN_STRING, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> converting types with str()...", fill=(71, 85, 105), font=FONT_TERM)

    else:
        # ---------------------------------------------------------------------
        # ACT 4: Key Takeaway Banner & Subscribe
        # ---------------------------------------------------------------------
        draw_desk_chair_and_laptop(draw, dx=560, dy=1460, stick_pose="celebrate", t=t)
        
        # Code stays clean
        draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(16, 45, 28), outline=SUCCESS_GREEN, width=2)
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, [
            ("print", CYAN_KEYWORD), ("(", PURPLE_OP),
            ("str", CYAN_KEYWORD), ("(", PURPLE_OP), ("age", WHITE_VAR), (") + ", PURPLE_OP),
            ("name", WHITE_VAR), (")", PURPLE_OP)
        ])
        
        draw.text((tm_x0 + 35, tm_y0 + 65), ">>> 25Dev", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 115), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        
        # Takeaway Box safely in lower zone (zero overlap!)
        box_y0 = 1240
        box_y1 = 1360
        draw.rounded_rectangle([ed_x0, box_y0, ed_x1, box_y1], radius=16, fill=(28, 22, 10), outline=(250, 204, 21), width=3)
        draw.text((ed_x0 + 30, box_y0 + 20), "⭐ KEY TAKEAWAY:", fill=(250, 204, 21), font=FONT_ALERT)
        draw.text((ed_x0 + 30, box_y0 + 65), "int + str = TypeError! Always convert with str(num).", fill=WHITE_VAR, font=FONT_CODE_BOLD)
        
        pulse = 3 * math.sin(t * 6.0)
        draw_centered_badge(
            draw, cx=WIDTH // 2, cy=1630,
            text="🔔 SUBSCRIBE FOR LESSON 3!",
            font=FONT_ALERT,
            fill_color=(220, 38, 38),
            text_color=WHITE_VAR,
            outline_color=WHITE_VAR,
            pad_x=28 + pulse, pad_y=12 + pulse
        )
        
    return im


def main():
    print("==================================================================")
    print("🎬 RENDERING PYTHON EPISODE 2: TYPES COLLISION (int + str)")
    print(f"Total Duration: {TOTAL_SECONDS}s | FPS: {FPS} | Total Frames: {TOTAL_FRAMES}")
    print("Stickman Walk-In -> Proper Laptop -> Progressive Typing -> Rich SFX")
    print("==================================================================")
    
    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        frame.save(FRAMES_DIR / f"frame_{i:04d}.png")
        if i % 150 == 0 or i == TOTAL_FRAMES - 1:
            print(f"  Frame {i}/{TOTAL_FRAMES} rendered ({i/FPS:.1f}s / {TOTAL_SECONDS:.1f}s)")
            
    print(f"✅ All {TOTAL_FRAMES} frames successfully rendered!")
    
    thumb_im = render_frame(int(31.0 * FPS))
    thumb_path = THUMBNAILS_DIR / "educational_ep2.jpg"
    thumb_im.save(thumb_path, quality=95)
    print(f"📸 Thumbnail saved: {thumb_path}")
    
    out_video = RENDERED_DIR / "educational_python_ep2.mp4"
    
    sfx_whoosh = SFX_DIR / "whoosh.wav"
    sfx_pop = SFX_DIR / "pop.wav"
    sfx_buzzer = SFX_DIR / "buzzer.wav"
    sfx_keyboard = SFX_DIR / "keyboard.wav"
    sfx_ding = SFX_DIR / "success_ding.wav"
    sfx_footsteps = SFX_DIR / "footsteps.wav"
    sfx_ambient = SFX_DIR / "ambient_coding_pad.wav"
    
    # Layered typing sound during progressive typing intervals
    filter_complex = (
        "[1:a]volume=0.22[amb];"
        "[2:a]adelay=300|300,volume=0.45[walk1];"
        "[2:a]adelay=1500|1500,volume=0.45[walk2];"
        "[3:a]adelay=3000|3000,volume=0.4[chair_sit];"
        "[4:a]adelay=3300|3300,volume=0.35[k1];"
        "[4:a]adelay=6500|6500,volume=0.35[k2];"
        "[4:a]adelay=9800|9800,volume=0.35[k3];"
        "[4:a]adelay=24500|24500,volume=0.35[k4];"
        "[4:a]adelay=27000|27000,volume=0.35[k5];"
        "[3:a]adelay=14000|14000,volume=0.55[p1];"
        "[3:a]adelay=29000|29000,volume=0.55[p2];"
        "[5:a]adelay=14200|14200,volume=0.65[b_err];"
        "[6:a]adelay=29200|29200,volume=0.65[d_fix];"
        "[amb][walk1][walk2][chair_sit][k1][k2][k3][k4][k5][p1][p2][b_err][d_fix]amix=inputs=13:duration=longest,volume=2.2,alimiter=limit=-1.5dB[aout]"
    )
    
    cmd = [
        FFMPEG, "-y",
        "-r", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(sfx_ambient),
        "-i", str(sfx_footsteps),
        "-i", str(sfx_pop),
        "-i", str(sfx_keyboard),
        "-i", str(sfx_buzzer),
        "-i", str(sfx_ding),
        "-filter_complex", filter_complex,
        "-map", "0:v:0",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_video)
    ]
    
    print("\nEncoding final Python Ep 2 video with FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr[-800:])
        raise RuntimeError("FFmpeg encoding failed.")
        
    print(f"🎉 Final Python Ep 2 saved: {out_video}")


if __name__ == "__main__":
    main()
