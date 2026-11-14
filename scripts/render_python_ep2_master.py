"""Production Master Animation Studio: Python Ep 2 (Variables & Core Data Types).
Target Channel: Main Channel (Python Master - @bhanuteja-8)

Improvements:
- Stickman enters walking from the left with footstep sounds, sits on chair at desk
- Laptop rests naturally on desk
- Zero lag: snappy, fast, fluid typing and execution
- Code editor is NEVER covered by popups or alerts (100% visible red/green line highlights)
- All error details appear in Terminal below
- Pure Alan Becker sound effects (footsteps, chair sit, keyboard, pop, buzzer, chime)
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
    FONT_CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 34)
    FONT_CODE_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 34)
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


def draw_window_frame(draw, x0, y0, x1, y1, title="main.py", is_terminal=False):
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


def draw_desk_and_chair(draw, dx=600, dy=1460):
    """Draw clean minimalist programmer desk and chair."""
    # Desk Top
    dw, dh = 240, 14
    draw.rounded_rectangle([dx - dw // 2, dy, dx + dw // 2, dy + dh], radius=6, fill=(45, 55, 75), outline=(70, 85, 115), width=2)
    # Desk Legs down to floor (floor at 1550)
    draw.line([(dx - dw // 2 + 20, dy + dh), (dx - dw // 2 + 20, 1550)], fill=(70, 85, 115), width=4)
    draw.line([(dx + dw // 2 - 20, dy + dh), (dx + dw // 2 - 20, 1550)], fill=(70, 85, 115), width=4)

    # Chair
    cx, cy = dx + 150, dy + 25
    draw.rounded_rectangle([cx - 30, cy, cx + 30, cy + 10], radius=4, fill=(55, 65, 88))  # seat
    draw.line([(cx + 22, cy - 80), (cx + 22, cy + 10)], fill=(55, 65, 88), width=5)      # backrest
    draw.line([(cx, cy + 10), (cx, 1550)], fill=(40, 50, 70), width=4)                    # chair center leg
    draw.line([(cx - 25, 1550), (cx + 25, 1550)], fill=(40, 50, 70), width=3)            # base


def draw_laptop_on_desk(draw, lx=600, ly=1460):
    """Draw sleek laptop resting on the desk surface."""
    bw, bh = 135, 10
    draw.polygon([
        (lx - bw // 2, ly),
        (lx + bw // 2, ly),
        (lx + bw // 2 - 10, ly + bh),
        (lx - bw // 2 + 10, ly + bh)
    ], fill=LAPTOP_SILVER, outline=(160, 175, 195))
    
    # Trackpad
    draw.rectangle([lx - 14, ly + 2, lx + 14, ly + 8], fill=(180, 190, 205))
    
    # Screen
    sw, sh = 120, 72
    sy_top = ly - sh
    sx_left = lx - sw // 2 + 8
    sx_right = lx + sw // 2 - 8
    draw.polygon([
        (lx - sw // 2, ly),
        (lx + sw // 2, ly),
        (sx_right, sy_top),
        (sx_left, sy_top)
    ], fill=LAPTOP_SCREEN, outline=LAPTOP_SILVER, width=2)
    draw.polygon([
        (lx - sw // 2 + 5, ly - 3),
        (lx + sw // 2 - 5, ly - 3),
        (sx_right - 5, sy_top + 5),
        (sx_left + 5, sy_top + 5)
    ], fill=(45, 90, 140))


def draw_stickman_state(draw, state="walk", walk_x=100, t=0.0):
    """Draw stickman in walking, sitting, typing, shocked, or celebrating states."""
    color = STICK_YELLOW
    head_r = 24
    
    if state == "walk":
        # Stickman walking from left to right toward chair at x=750
        hx = walk_x
        hy = 1400
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 80)
        draw.line([neck, hip], fill=color, width=7)
        
        # Scissor walking legs
        leg_phase = math.sin(t * 14.0) * 28.0
        foot1 = (hip[0] + leg_phase, 1550)
        foot2 = (hip[0] - leg_phase, 1550)
        draw.line([hip, foot1], fill=color, width=6)
        draw.line([hip, foot2], fill=color, width=6)
        
        # Swinging arms
        arm_phase = math.sin(t * 14.0) * 22.0
        draw.line([neck, (neck[0] - arm_phase, neck[1] + 45)], fill=color, width=6)
        draw.line([neck, (neck[0] + arm_phase, neck[1] + 45)], fill=color, width=6)

    elif state in ("sit_typing", "sit_idle", "sit_enter"):
        # Sitting on chair at x=750
        hx = 750
        hy = 1395
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx - 4, hy + head_r)
        hip = (750, 1485) # on chair seat
        draw.line([neck, hip], fill=color, width=7)
        
        # Legs under desk: hip -> knee forward -> foot down
        knee = (680, 1495)
        foot = (670, 1550)
        draw.line([hip, knee], fill=color, width=6)
        draw.line([knee, foot], fill=color, width=6)
        
        # Arms reaching to laptop on desk
        shoulder = (neck[0] - 2, neck[1] + 12)
        if state == "sit_typing":
            t_wave = math.sin(t * 24.0) * 5.0
            elbow = (690, 1445)
            hand = (610, 1460 + t_wave)
            draw.line([shoulder, elbow], fill=color, width=6)
            draw.line([elbow, hand], fill=color, width=6)
        elif state == "sit_enter":
            elbow = (680, 1430)
            hand = (605, 1450)
            draw.line([shoulder, elbow], fill=color, width=6)
            draw.line([elbow, hand], fill=color, width=6)
        else: # sit_idle
            elbow = (695, 1450)
            hand = (620, 1462)
            draw.line([shoulder, elbow], fill=color, width=6)
            draw.line([elbow, hand], fill=color, width=6)

    elif state == "confused":
        # Recoiling back in chair
        hx = 770
        hy = 1380
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx + 2, hy + head_r)
        hip = (755, 1485)
        draw.line([neck, hip], fill=color, width=7)
        
        knee = (690, 1495)
        foot = (680, 1550)
        draw.line([hip, knee], fill=color, width=6)
        draw.line([knee, foot], fill=color, width=6)
        
        # Left hand scratching head
        shoulder = (neck[0] - 2, neck[1] + 10)
        draw.line([shoulder, (hx + 24, hy - 10)], fill=color, width=6)
        draw.line([(hx + 24, hy - 10), (hx + 6, hy - 25)], fill=color, width=6)
        # Right hand flailing back
        draw.line([shoulder, (shoulder[0] - 30, shoulder[1] + 20)], fill=color, width=6)
        
        draw.text((hx - 40, hy - 65), "?", fill=ERROR_RED, font=FONT_HEADER)
        draw.text((hx + 30, hy - 75), "?", fill=AMBER_NUMBER, font=FONT_HEADER)

    elif state == "celebrate":
        # Sitting with victory arms up + sparkle stars
        hx = 750
        hy = 1390
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (750, 1485)
        draw.line([neck, hip], fill=color, width=7)
        
        knee = (680, 1495)
        foot = (670, 1550)
        draw.line([hip, knee], fill=color, width=6)
        draw.line([knee, foot], fill=color, width=6)
        
        # Both arms raised in triumph
        shoulder = (neck[0], neck[1] + 10)
        draw.line([shoulder, (shoulder[0] - 35, shoulder[1] - 25)], fill=color, width=6)
        draw.line([(shoulder[0] - 35, shoulder[1] - 25), (shoulder[0] - 55, shoulder[1] - 55)], fill=color, width=6)
        draw.line([shoulder, (shoulder[0] + 35, shoulder[1] - 25)], fill=color, width=6)
        draw.line([(shoulder[0] + 35, shoulder[1] - 25), (shoulder[0] + 55, shoulder[1] - 55)], fill=color, width=6)
        
        for sx, sy in [(hx - 60, hy - 40), (hx + 65, hy - 45), (hx, hy - 65)]:
            draw.text((sx, sy), "★", fill=(250, 204, 21), font=FONT_HEADER)


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
        text="EPISODE 2: 4 CORE DATA TYPES",
        font=FONT_SUBTITLE,
        fill_color=(18, 24, 38),
        text_color=CYAN_KEYWORD,
        outline_color=CYAN_KEYWORD,
        pad_x=22, pad_y=8
    )
    
    # 3. Floating Code Editor Window (100% visible lines, zero covering popups!)
    ed_x0, ed_y0 = 80, 230
    ed_x1, ed_y1 = 1000, 750
    draw_window_frame(draw, ed_x0, ed_y0, ed_x1, ed_y1, title="types_demo.py", is_terminal=False)
    
    # 4. Floating Terminal Window (All error & output details live here!)
    tm_x0, tm_y0 = 80, 790
    tm_x1, tm_y1 = 1000, 1220
    draw_window_frame(draw, tm_x0, tm_y0, tm_x1, tm_y1, title="TERMINAL - output", is_terminal=True)
    
    # Desk, Laptop & Chair (Fixed in bottom right)
    draw_desk_and_chair(draw, dx=600, dy=1460)
    draw_laptop_on_desk(draw, lx=600, ly=1460)
    
    cursor_char = "_" if int(t * 4.0) % 2 == 0 else " "
    
    # =========================================================================
    # TIMELINE & ACTS
    # =========================================================================
    # Code Lines
    line1 = [("age = ", WHITE_VAR), ("25", AMBER_NUMBER), ("          # int", MUTED_TEXT)]
    line2 = [("price = ", WHITE_VAR), ("19.99", AMBER_NUMBER), ("     # float", MUTED_TEXT)]
    line3 = [("name = ", WHITE_VAR), ('"Dev"', GREEN_STRING), ("      # str", MUTED_TEXT)]
    line4 = [("is_coder = ", WHITE_VAR), ("True", CYAN_KEYWORD), ("   # bool", MUTED_TEXT)]
    
    if t < 3.0:
        # Act 0: Stickman walks in from left to right toward chair
        walk_x = int(100 + (t / 3.0) * 650)
        draw_stickman_state(draw, state="walk", walk_x=walk_x, t=t)
        draw.text((tm_x0 + 35, tm_y0 + 65), ">>> booting environment...", fill=(71, 85, 105), font=FONT_TERM)

    elif t < 16.0:
        # Act 1: Typing Data Types & Running type() check
        t_rel = t - 3.0
        draw.text((ed_x0 + 35, ed_y0 + 65), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 65, line1)
        
        if t_rel >= 1.5:
            draw.text((ed_x0 + 35, ed_y0 + 115), "2", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 115, line2)
        if t_rel >= 3.0:
            draw.text((ed_x0 + 35, ed_y0 + 165), "3", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 165, line3)
        if t_rel >= 4.5:
            draw.text((ed_x0 + 35, ed_y0 + 215), "4", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, line4)
            
        # Line 5: print(type(age), type(name))
        if t_rel >= 6.0:
            draw.text((ed_x0 + 35, ed_y0 + 265), "5", fill=MUTED_TEXT, font=FONT_CODE)
            p5 = min(1.0, (t_rel - 6.0) / 3.5)
            f5 = "print(type(age), type(name))"
            c5 = f5[:int(p5 * len(f5))]
            tok5 = [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("type(age), type(name)", WHITE_VAR), (")", PURPLE_OP)] if p5 >= 1.0 else [(c5, CYAN_KEYWORD)]
            x5 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 265, tok5)
            if p5 < 1.0:
                draw.text((x5 + 4, ed_y0 + 265), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
                
        # Hit Enter at 10.0s (13.0s overall) -> green line execution highlight
        if t_rel >= 10.0:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 260, ed_x1 - 20, ed_y0 + 310], radius=8, fill=(16, 185, 129, 30), outline=SUCCESS_GREEN, width=2)
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> <class 'int'> <class 'str'>", fill=WHITE_VAR, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 115), "[Program exited with code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> waiting for execution...", fill=(71, 85, 105), font=FONT_TERM)
            
        pose = "sit_typing" if t_rel < 9.8 else ("sit_enter" if t_rel < 10.4 else "sit_idle")
        draw_stickman_state(draw, state=pose, t=t)

    elif t < 26.0:
        # Act 2: Bug Demonstration (age + name) -> TypeError!
        t_rel = t - 16.0
        draw.text((ed_x0 + 35, ed_y0 + 65), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 65, line1)
        draw.text((ed_x0 + 35, ed_y0 + 115), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 115, line2)
        draw.text((ed_x0 + 35, ed_y0 + 165), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 165, line3)
        draw.text((ed_x0 + 35, ed_y0 + 215), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, line4)
        
        # Buggy Line 5: print(age + name)
        draw.text((ed_x0 + 35, ed_y0 + 265), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 265, [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("age + name", ERROR_RED), (")", PURPLE_OP)])
        
        # Hit Enter at 3.0s (19.0s overall) -> RED LINE HIGHLIGHT (Zero overlays covering the code!)
        if t_rel >= 3.0:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 260, ed_x1 - 20, ed_y0 + 310], radius=8, fill=(239, 68, 68, 35), outline=ERROR_RED, width=3)
            # Terminal shows full error clearly
            draw.text((tm_x0 + 35, tm_y0 + 60), 'Traceback (most recent call last):', fill=ERROR_RED, font=FONT_TERM)
            draw.text((tm_x0 + 55, tm_y0 + 105), 'File "types_demo.py", line 5, in <module>', fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 75, tm_y0 + 150), 'print(age + name)', fill=WHITE_VAR, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 200), "TypeError: unsupported operand type(s)", fill=ERROR_RED, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 240), "           for +: 'int' and 'str'", fill=ERROR_RED, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 290), ">> Cannot add integer to string directly!", fill=AMBER_NUMBER, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> running operation...", fill=(71, 85, 105), font=FONT_TERM)
            
        pose = "sit_typing" if t_rel < 2.8 else ("sit_enter" if t_rel < 3.4 else "confused")
        draw_stickman_state(draw, state=pose, t=t)

    elif t < 35.0:
        # Act 3: The Fix: print(str(age) + name) -> Success!
        t_rel = t - 26.0
        draw.text((ed_x0 + 35, ed_y0 + 65), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 65, line1)
        draw.text((ed_x0 + 35, ed_y0 + 115), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 115, line2)
        draw.text((ed_x0 + 35, ed_y0 + 165), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 165, line3)
        draw.text((ed_x0 + 35, ed_y0 + 215), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, line4)
        
        # Fixed Line 5: print(str(age) + name)
        draw.text((ed_x0 + 35, ed_y0 + 265), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 265, [
            ("print", CYAN_KEYWORD), ("(", PURPLE_OP),
            ("str", CYAN_KEYWORD), ("(", PURPLE_OP), ("age", WHITE_VAR), (") + ", PURPLE_OP),
            ("name", WHITE_VAR), (")", PURPLE_OP)
        ])
        
        if t_rel < 2.0:
            draw.text((720, 1310), "💡 IDEA!", fill=(250, 204, 21), font=FONT_HEADER)
            
        # Hit Enter at 2.5s (28.5s overall) -> GREEN EXECUTION HIGHLIGHT
        if t_rel >= 2.5:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 260, ed_x1 - 20, ed_y0 + 310], radius=8, fill=(16, 185, 129, 30), outline=SUCCESS_GREEN, width=2)
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> 25Dev", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 115), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 175), ">> Converted int to str before concatenating!", fill=GREEN_STRING, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), ">>> converting types...", fill=(71, 85, 105), font=FONT_TERM)
            
        pose = "sit_typing" if t_rel < 2.3 else ("sit_enter" if t_rel < 2.9 else "celebrate")
        draw_stickman_state(draw, state=pose, t=t)

    else:
        # Act 4: Key Takeaway & Subscribe CTA (35s - 42.0s)
        draw.text((ed_x0 + 35, ed_y0 + 65), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 65, line1)
        draw.text((ed_x0 + 35, ed_y0 + 115), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 115, line2)
        draw.text((ed_x0 + 35, ed_y0 + 165), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 165, line3)
        draw.text((ed_x0 + 35, ed_y0 + 215), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, line4)
        draw.text((ed_x0 + 35, ed_y0 + 265), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 265, [
            ("print", CYAN_KEYWORD), ("(", PURPLE_OP),
            ("str", CYAN_KEYWORD), ("(", PURPLE_OP), ("age", WHITE_VAR), (") + ", PURPLE_OP),
            ("name", WHITE_VAR), (")", PURPLE_OP)
        ])
        
        draw.text((tm_x0 + 35, tm_y0 + 65), ">>> 25Dev", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 115), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        
        # Takeaway Box (Safely placed in lower-middle, zero overlapping)
        box_y0 = 1260
        box_y1 = 1380
        draw.rounded_rectangle([ed_x0, box_y0, ed_x1, box_y1], radius=16, fill=(28, 22, 10), outline=(250, 204, 21), width=3)
        draw.text((ed_x0 + 30, box_y0 + 20), "⭐ KEY TAKEAWAY:", fill=(250, 204, 21), font=FONT_ALERT)
        draw.text((ed_x0 + 30, box_y0 + 65), "Data types matter! Cast int to str(n) to concatenate.", fill=WHITE_VAR, font=FONT_CODE_BOLD)
        
        draw_stickman_state(draw, state="celebrate", t=t)
        
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
    print("🎬 RENDERING PYTHON EPISODE 2: 4 CORE DATA TYPES")
    print(f"Total Duration: {TOTAL_SECONDS}s | FPS: {FPS} | Total Frames: {TOTAL_FRAMES}")
    print("Stickman Walk-In -> Desk/Chair Sitting -> Pure SFX")
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
    
    filter_complex = (
        "[1:a]volume=0.22[amb];"
        "[2:a]adelay=300|300,volume=0.45[walk1];"
        "[2:a]adelay=1500|1500,volume=0.45[walk2];"
        "[3:a]adelay=3000|3000,volume=0.4[chair_sit];"
        "[4:a]adelay=4500|4500,volume=0.35[k1];"
        "[4:a]adelay=9000|9000,volume=0.35[k2];"
        "[4:a]adelay=26500|26500,volume=0.35[k3];"
        "[5:a]adelay=13000|13000,volume=0.55[p1];"
        "[5:a]adelay=19000|19000,volume=0.55[p2];"
        "[5:a]adelay=28500|28500,volume=0.55[p3];"
        "[6:a]adelay=19200|19200,volume=0.65[b_err];"
        "[7:a]adelay=13200|13200,volume=0.55[d1];"
        "[7:a]adelay=28700|28700,volume=0.65[d2];"
        "[amb][walk1][walk2][chair_sit][k1][k2][k3][p1][p2][p3][b_err][d1][d2]amix=inputs=13:duration=longest,volume=2.2,alimiter=limit=-1.5dB[aout]"
    )
    
    cmd = [
        FFMPEG, "-y",
        "-r", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(sfx_ambient),
        "-i", str(sfx_footsteps),
        "-i", str(sfx_pop),
        "-i", str(sfx_keyboard),
        "-i", str(sfx_pop),
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

