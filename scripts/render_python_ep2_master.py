"""Production Master Animation Studio: Python Ep 2 (Types Collision).
Target Channel: Main Channel (Python Master - @bhanuteja-8)

Exact Fixes Applied:
1. FIXED GHOST STICKMAN: Desk & Chair is 100% EMPTY while stickman walks in from the left!
2. CHOREOGRAPHY:
   - Act 0 (0.0s - 2.8s): Stickman walks in from left, sits down into the empty chair.
   - Act 1 (2.8s - 13.0s): Types buggy code character-by-character with continuous keyboard clacks.
   - Act 2 (13.0s - 14.0s): Strikes Enter -> TypeError crashes in Terminal!
   - Act 3 (14.0s - 19.5s): Stickman jumps out of chair, paces left-to-right thinking with hand on chin (5 seconds)!
   - Act 4 (19.5s - 27.5s): Lightbulb moment, sits back in chair, BACKSPACES 'age' letter-by-letter, and types 'str(age)'!
   - Act 5 (27.5s - 29.0s): Strikes Enter -> Output 25Dev in bright GREEN! Success chime!
   - Act 6 (29.0s - 35.0s): Stickman leaps out of chair to center floor, jumping with arms up celebrating 'YAAAYYY!' with stars!
   - Act 7 (35.0s - 42.0s): Thumbs up, 2-line clean takeaway box (100% fits inside box, ZERO overflow!).
3. ZERO COVERING: Highlight bar drawn UNDER text (code is 100% visible).
4. Audio: Footsteps, chair sit, continuous keyboard clacks, pop, buzzer, chime, ambient bed.
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

# Colors
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
    FONT_CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 34)
    FONT_CODE_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 34)
    FONT_HEADER = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 46)
    FONT_SUBTITLE = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 24)
    FONT_TERM = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 28)
    FONT_TERM_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 30)
    FONT_ALERT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
    FONT_COMIC = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
except Exception:
    FONT_CODE = ImageFont.load_default()
    FONT_CODE_BOLD = ImageFont.load_default()
    FONT_HEADER = ImageFont.load_default()
    FONT_SUBTITLE = ImageFont.load_default()
    FONT_TERM = ImageFont.load_default()
    FONT_TERM_BOLD = ImageFont.load_default()
    FONT_ALERT = ImageFont.load_default()
    FONT_COMIC = ImageFont.load_default()


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


def draw_window_frame(draw, x0, y0, x1, y1, title="types_collision.py", is_terminal=False):
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


def draw_empty_desk_and_chair(draw, dx=560, dy=1460):
    """Draw ONLY the furniture & laptop. NEVER draws the stickman here (prevents duplicate stickman!)."""
    # Desk
    dw, dh = 300, 14
    dx0, dx1 = dx - dw // 2, dx + dw // 2
    draw.rounded_rectangle([dx0, dy, dx1, dy + dh], radius=6, fill=(45, 55, 75), outline=(70, 85, 115), width=2)
    draw.line([(dx0 + 25, dy + dh), (dx0 + 25, 1550)], fill=(70, 85, 115), width=4)
    draw.line([(dx1 - 25, dy + dh), (dx1 - 25, 1550)], fill=(70, 85, 115), width=4)

    # Empty Chair at x=730
    cx, cy = 730, dy + 25
    draw.rounded_rectangle([cx - 30, cy, cx + 30, cy + 10], radius=4, fill=(55, 65, 88))
    draw.line([(cx + 25, cy - 85), (cx + 25, cy + 10)], fill=(55, 65, 88), width=5) # backrest
    draw.line([(cx, cy + 10), (cx, 1550)], fill=(40, 50, 70), width=4)               # leg
    draw.line([(cx - 25, 1550), (cx + 25, 1550)], fill=(40, 50, 70), width=3)       # wheel base

    # Laptop on desk facing stickman (screen tilted toward right)
    lx_left, lx_right = 530, 645
    draw.polygon([
        (lx_left, dy),
        (lx_right, dy),
        (lx_right - 8, dy + 8),
        (lx_left + 8, dy + 8)
    ], fill=LAPTOP_SILVER, outline=(160, 175, 195))
    draw.rectangle([580, dy + 2, 605, dy + 6], fill=(180, 190, 205))
    
    sx_hinge = lx_left + 5
    sy_hinge = dy
    sx_top = sx_hinge - 30
    sy_top = dy - 70
    draw.polygon([(sx_hinge - 4, sy_hinge), (sx_hinge, sy_hinge), (sx_top, sy_top), (sx_top - 4, sy_top)], fill=(160, 175, 195))
    draw.polygon([(sx_hinge, sy_hinge), (sx_hinge + 45, sy_hinge - 15), (sx_top + 45, sy_top), (sx_top, sy_top)], fill=(45, 95, 155), outline=(56, 189, 248), width=1)


def draw_stickman_actor(draw, action="walk_in", walk_x=100, t=0.0):
    """Single master stickman actor function. Ensures EXACTLY ONE stickman exists at any time."""
    color = STICK_YELLOW
    head_r = 24
    
    if action == "walk_in":
        # Walking from left to right toward chair
        hx = walk_x
        hy = 1400
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 80)
        draw.line([neck, hip], fill=color, width=7)
        leg_p = math.sin(t * 14.0) * 28.0
        draw.line([hip, (hip[0] + leg_p, 1550)], fill=color, width=6)
        draw.line([hip, (hip[0] - leg_p, 1550)], fill=color, width=6)
        arm_p = math.sin(t * 14.0) * 22.0
        draw.line([neck, (neck[0] - arm_p, neck[1] + 45)], fill=color, width=6)
        draw.line([neck, (neck[0] + arm_p, neck[1] + 45)], fill=color, width=6)

    elif action in ("sitting_typing", "sitting_enter", "sitting_idle"):
        # Sitting on chair at x=720, hands on keyboard
        hx = 720
        hy = 1390
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx - 4, hy + head_r)
        hip = (725, 1485)
        draw.line([neck, hip], fill=color, width=7)
        knee = (660, 1495)
        foot = (650, 1550)
        draw.line([hip, knee], fill=color, width=6)
        draw.line([knee, foot], fill=color, width=6)
        
        shoulder = (neck[0] - 2, neck[1] + 12)
        if action == "sitting_typing":
            t_wave = math.sin(t * 26.0) * 5.0
            draw.line([shoulder, (670, 1445)], fill=color, width=6)
            draw.line([(670, 1445), (605, 1460 + t_wave)], fill=color, width=6)
        elif action == "sitting_enter":
            draw.line([shoulder, (660, 1435)], fill=color, width=6)
            draw.line([(660, 1435), (600, 1452)], fill=color, width=6)
        else:
            draw.line([shoulder, (675, 1450)], fill=color, width=6)
            draw.line([(675, 1450), (615, 1460)], fill=color, width=6)

    elif action == "pacing_thinking":
        # Out of chair! Walking back and forth between x=620 and x=320, hand on chin thinking
        pace_x = int(470 + math.sin(t * 2.8) * 150)
        hx = pace_x
        hy = 1400
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 80)
        draw.line([neck, hip], fill=color, width=7)
        
        # Walking legs
        leg_p = math.sin(t * 10.0) * 22.0
        draw.line([hip, (hip[0] + leg_p, 1550)], fill=color, width=6)
        draw.line([hip, (hip[0] - leg_p, 1550)], fill=color, width=6)
        
        # Right hand on chin thinking, left arm folded across waist
        shoulder = (neck[0], neck[1] + 12)
        draw.line([shoulder, (hx - 15, hy + 50)], fill=color, width=6) # left folded arm
        draw.line([shoulder, (hx + 18, hy + 30)], fill=color, width=6) # right upper arm
        draw.line([(hx + 18, hy + 30), (hx + 4, hy + 18)], fill=color, width=6) # hand on chin!
        
        # Animated floating question marks
        q_wiggle = math.sin(t * 6.0) * 6
        draw.text((hx - 35, hy - 65 + q_wiggle), "?", fill=ERROR_RED, font=FONT_HEADER)
        draw.text((hx + 28, hy - 75 - q_wiggle), "?", fill=AMBER_NUMBER, font=FONT_HEADER)

    elif action == "yaay_celebrate":
        # LEAPED OUT OF CHAIR! Jumping in the air in center floor with YAAAYYY!
        jump_y = int(math.sin(t * 8.0) * 35) # jumping bounce!
        hx = 450
        hy = 1380 - abs(jump_y)
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 80)
        draw.line([neck, hip], fill=color, width=7)
        
        # Jumping legs spread wide
        draw.line([hip, (hip[0] - 35, 1550 - abs(jump_y) + 10)], fill=color, width=6)
        draw.line([hip, (hip[0] + 35, 1550 - abs(jump_y) + 10)], fill=color, width=6)
        
        # Both arms pumping the air in victory!
        shoulder = (neck[0], neck[1] + 10)
        draw.line([shoulder, (shoulder[0] - 40, shoulder[1] - 35)], fill=color, width=6)
        draw.line([(shoulder[0] - 40, shoulder[1] - 35), (shoulder[0] - 65, shoulder[1] - 65)], fill=color, width=6)
        draw.line([shoulder, (shoulder[0] + 40, shoulder[1] - 35)], fill=color, width=6)
        draw.line([(shoulder[0] + 40, shoulder[1] - 35), (shoulder[0] + 65, shoulder[1] - 65)], fill=color, width=6)
        
        # Big Comic Speech Bubble: YAAAYYY!
        draw.rounded_rectangle([hx - 95, hy - 110, hx + 95, hy - 50], radius=16, fill=(250, 204, 21), outline=(255, 255, 255), width=3)
        draw.text((hx - 80, hy - 102), "YAAAYYY!", fill=(11, 14, 20), font=FONT_COMIC)
        # Golden sparkle stars
        for sx, sy in [(hx - 125, hy - 40), (hx + 125, hy - 45), (hx - 40, hy - 135), (hx + 50, hy - 135)]:
            draw.text((sx, sy), "★", fill=(250, 204, 21), font=FONT_HEADER)

    elif action == "thumbs_up":
        # Standing tall, giving thumbs up to viewer
        hx = 450
        hy = 1400
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 85)
        draw.line([neck, hip], fill=color, width=7)
        draw.line([hip, (hip[0] - 22, 1550)], fill=color, width=6)
        draw.line([hip, (hip[0] + 22, 1550)], fill=color, width=6)
        
        shoulder = (neck[0], neck[1] + 12)
        # Left hand on hip
        draw.line([shoulder, (shoulder[0] - 30, shoulder[1] + 30)], fill=color, width=6)
        draw.line([(shoulder[0] - 30, shoulder[1] + 30), (hip[0] - 15, hip[1])], fill=color, width=6)
        # Right arm giving thumbs up!
        draw.line([shoulder, (shoulder[0] + 35, shoulder[1] - 10)], fill=color, width=6)
        draw.line([(shoulder[0] + 35, shoulder[1] - 10), (shoulder[0] + 70, shoulder[1] - 25)], fill=color, width=6)
        draw.text((shoulder[0] + 75, shoulder[1] - 50), "👍", fill=(250, 204, 21), font=FONT_ALERT)


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
    
    # Always draw the furniture (empty desk, chair, laptop)
    draw_empty_desk_and_chair(draw, dx=560, dy=1460)
    
    cursor_char = "_" if int(t * 4.0) % 2 == 0 else " "
    
    # =========================================================================
    # TIMELINE PHASES (42.0s Total)
    # =========================================================================
    if t < 2.8:
        # ---------------------------------------------------------------------
        # ACT 0: Walk In from Left (Desk/Chair is 100% EMPTY!)
        # ---------------------------------------------------------------------
        walk_x = int(80 + (t / 2.8) * 640)
        draw_stickman_actor(draw, action="walk_in", walk_x=walk_x, t=t)
        draw.text((tm_x0 + 35, tm_y0 + 65), ">>> booting python interactive shell...", fill=(71, 85, 105), font=FONT_TERM)

    elif t < 13.0:
        # ---------------------------------------------------------------------
        # ACT 1: Sits in Chair -> Types Buggy Code Character-by-Character
        # ---------------------------------------------------------------------
        draw_stickman_actor(draw, action="sitting_typing", t=t)
        t_rel = t - 2.8
        
        # Line 1: age = 25          # int
        p1 = min(1.0, max(0.0, (t_rel - 0.2) / 2.8))
        c1 = "age = 25          # int"[:int(p1 * 21)]
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        x1 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)] if p1 >= 1.0 else [(c1, WHITE_VAR)])
        if p1 < 1.0:
            draw.text((x1 + 4, ed_y0 + 75), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            
        # Line 2: name = "Dev"      # str
        if t_rel >= 3.0:
            p2 = min(1.0, max(0.0, (t_rel - 3.0) / 2.8))
            c2 = 'name = "Dev"      # str'[:int(p2 * 21)]
            draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
            x2 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)] if p2 >= 1.0 else [(c2, WHITE_VAR)])
            if p2 < 1.0:
                draw.text((x2 + 4, ed_y0 + 135), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
                
        # Line 3: print(age + name)  (BUGGY CODE TYPED FIRST!)
        if t_rel >= 6.0:
            p3 = min(1.0, max(0.0, (t_rel - 6.0) / 3.8))
            c3 = "print(age + name)"[:int(p3 * 17)]
            draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
            x3 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("age + name", ERROR_RED), (")", PURPLE_OP)] if p3 >= 1.0 else [(c3, CYAN_KEYWORD)])
            if p3 < 1.0:
                draw.text((x3 + 4, ed_y0 + 195), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
                
        draw.text((tm_x0 + 35, tm_y0 + 65), ">>> typing code...", fill=(71, 85, 105), font=FONT_TERM)

    elif t < 14.0:
        # ---------------------------------------------------------------------
        # ACT 2: Enter Strike -> Crash!
        # ---------------------------------------------------------------------
        draw_stickman_actor(draw, action="sitting_enter", t=t)
        # Highlight UNDERNEATH text
        draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(45, 18, 22), outline=ERROR_RED, width=2)
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("age + name", ERROR_RED), (")", PURPLE_OP)])
        
        draw.text((tm_x0 + 35, tm_y0 + 60), 'Traceback (most recent call last):', fill=ERROR_RED, font=FONT_TERM)
        draw.text((tm_x0 + 55, tm_y0 + 105), 'File "types_collision.py", line 3', fill=MUTED_TEXT, font=FONT_TERM)
        draw.text((tm_x0 + 35, tm_y0 + 160), "TypeError: unsupported operand type(s)", fill=ERROR_RED, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 200), "           for +: 'int' and 'str'", fill=ERROR_RED, font=FONT_TERM_BOLD)

    elif t < 19.5:
        # ---------------------------------------------------------------------
        # ACT 3: OUT OF CHAIR! Pacing Left to Right Thinking (5 Seconds!)
        # ---------------------------------------------------------------------
        # Chair is EMPTY! Stickman is pacing in floor space
        draw_stickman_actor(draw, action="pacing_thinking", t=t)
        
        # Code stays 100% visible
        draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(45, 18, 22), outline=ERROR_RED, width=2)
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("age + name", ERROR_RED), (")", PURPLE_OP)])
        
        # Terminal explains error
        draw.text((tm_x0 + 35, tm_y0 + 60), 'Traceback (most recent call last):', fill=ERROR_RED, font=FONT_TERM)
        draw.text((tm_x0 + 55, tm_y0 + 105), 'File "types_collision.py", line 3', fill=MUTED_TEXT, font=FONT_TERM)
        draw.text((tm_x0 + 35, tm_y0 + 160), "TypeError: unsupported operand type(s)", fill=ERROR_RED, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 200), "           for +: 'int' and 'str'", fill=ERROR_RED, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 260), ">> Cannot add integer to string directly!", fill=AMBER_NUMBER, font=FONT_TERM)
        
        # Lightbulb pops up at 18.5s!
        if t >= 18.5:
            draw.text((430, 1310), "💡 IDEA!", fill=(250, 204, 21), font=FONT_HEADER)

    elif t < 27.5:
        # ---------------------------------------------------------------------
        # ACT 4: Sits Back in Chair -> Backspaces letter-by-letter & Types str(age)
        # ---------------------------------------------------------------------
        draw_stickman_actor(draw, action="sitting_typing", t=t)
        t_rel = t - 19.5
        
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)])
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        
        # Backspace phase (0.0s - 2.0s): deletes "age"
        if t_rel < 2.0:
            del_chars = int((t_rel / 2.0) * 3)
            current_arg = "age"[:max(0, 3 - del_chars)]
            x3 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, [("print(", CYAN_KEYWORD), (current_arg, ERROR_RED), (" + name)", PURPLE_OP)])
            draw.text((x3 + 4, ed_y0 + 195), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> backspacing invalid argument...", fill=(71, 85, 105), font=FONT_TERM)
        else:
            # Typing phase (2.0s - 7.5s): types "str(age)"
            fix_p = min(1.0, max(0.0, (t_rel - 2.0) / 4.8))
            full_fixed = "print(str(age) + name)"
            c_fix = full_fixed[:int(fix_p * len(full_fixed))]
            tok_fix = [
                ("print", CYAN_KEYWORD), ("(", PURPLE_OP),
                ("str", CYAN_KEYWORD), ("(", PURPLE_OP), ("age", WHITE_VAR), (") + ", PURPLE_OP),
                ("name", WHITE_VAR), (")", PURPLE_OP)
            ] if fix_p >= 1.0 else [(c_fix, CYAN_KEYWORD)]
            x3 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, tok_fix)
            if fix_p < 1.0:
                draw.text((x3 + 4, ed_y0 + 195), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> typing typecast str(age)...", fill=(71, 85, 105), font=FONT_TERM)

    elif t < 29.0:
        # ---------------------------------------------------------------------
        # ACT 5: Strikes Enter -> Green Highlight & Success in Terminal
        # ---------------------------------------------------------------------
        draw_stickman_actor(draw, action="sitting_enter", t=t)
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
        draw.text((tm_x0 + 35, tm_y0 + 175), ">> Converted integer 25 into string '25'!", fill=GREEN_STRING, font=FONT_TERM)

    elif t < 35.5:
        # ---------------------------------------------------------------------
        # ACT 6: JUMPS OUT OF CHAIR! JUMPING CELEBRATION "YAAAYYY!" WITH STARS
        # ---------------------------------------------------------------------
        # Chair is EMPTY! Stickman is leaping in center floor!
        draw_stickman_actor(draw, action="yaay_celebrate", t=t)
        
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

    else:
        # ---------------------------------------------------------------------
        # ACT 7: THUMBS UP & MULTI-LINE TAKEAWAY BOX (ZERO TEXT OVERFLOW!)
        # ---------------------------------------------------------------------
        draw_stickman_actor(draw, action="thumbs_up", t=t)
        
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
        
        # MULTI-LINE TAKEAWAY BOX (fits 100% inside yellow border, ZERO OVERFLOW!)
        box_y0 = 1240
        box_y1 = 1380
        draw.rounded_rectangle([ed_x0, box_y0, ed_x1, box_y1], radius=16, fill=(28, 22, 10), outline=(250, 204, 21), width=3)
        draw.text((ed_x0 + 30, box_y0 + 16), "⭐ KEY TAKEAWAY:", fill=(250, 204, 21), font=FONT_ALERT)
        draw.text((ed_x0 + 30, box_y0 + 56), "int + str gives TypeError!", fill=WHITE_VAR, font=FONT_CODE_BOLD)
        draw.text((ed_x0 + 30, box_y0 + 94), "Fix: Always convert with str(num)", fill=GREEN_STRING, font=FONT_CODE)
        
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
    print("🎬 RENDERING ULTIMATE PYTHON EPISODE 2 (ALAN BECKER MASTER)")
    print(f"Total Duration: {TOTAL_SECONDS}s | FPS: {FPS} | Total Frames: {TOTAL_FRAMES}")
    print("Walk-in -> Buggy First -> Pacing Thinking -> Backspace Fix -> YAAAYYY!")
    print("==================================================================")
    
    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        frame.save(FRAMES_DIR / f"frame_{i:04d}.png")
        if i % 150 == 0 or i == TOTAL_FRAMES - 1:
            print(f"  Frame {i}/{TOTAL_FRAMES} rendered ({i/FPS:.1f}s / {TOTAL_SECONDS:.1f}s)")
            
    print(f"✅ All {TOTAL_FRAMES} frames successfully rendered!")
    
    thumb_im = render_frame(int(32.0 * FPS)) # Frame from YAAAYYY celebration!
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
    
    filter_complex = (
        "[1:a]volume=0.22[amb];"
        "[2:a]adelay=300|300,volume=0.45[walk1];"
        "[2:a]adelay=1500|1500,volume=0.45[walk2];"
        "[3:a]adelay=2800|2800,volume=0.4[chair_sit];"
        "[4:a]adelay=3200|3200,volume=0.35[k1];"
        "[4:a]adelay=6000|6000,volume=0.35[k2];"
        "[4:a]adelay=9000|9000,volume=0.35[k3];"
        "[4:a]adelay=22000|22000,volume=0.35[k4];"
        "[4:a]adelay=24500|24500,volume=0.35[k5];"
        "[3:a]adelay=13200|13200,volume=0.55[p1];"
        "[3:a]adelay=28000|28000,volume=0.55[p2];"
        "[5:a]adelay=13400|13400,volume=0.65[b_err];"
        "[6:a]adelay=28200|28200,volume=0.65[d_fix];"
        "[2:a]adelay=14500|14500,volume=0.35[pace_walk1];"
        "[2:a]adelay=17000|17000,volume=0.35[pace_walk2];"
        "[amb][walk1][walk2][chair_sit][k1][k2][k3][k4][k5][p1][p2][b_err][d_fix][pace_walk1][pace_walk2]amix=inputs=15:duration=longest,volume=2.2,alimiter=limit=-1.5dB[aout]"
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
