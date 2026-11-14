"""Production Master Animation Studio: C Language Ep 2 (Variables & Core Types).
Target Channel: Second Channel (Bhanu Teja - @bhanuteja-n8x)

Improvements:
- Stickman enters walking from the left with footstep sounds, sits on chair at desk
- Laptop rests naturally on desk
- Zero lag: snappy, fast, fluid typing and execution
- Code editor is NEVER covered by popups or alerts (100% visible red/green line highlights)
- All compiler error details appear in Terminal below
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
TEMP_DIR = STORAGE / "temp" / "c_ep2_master"
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
BLUE_C_LOGO = (0, 89, 156)
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


def draw_c_logo(draw, cx, cy, size=38):
    draw.ellipse([cx - size, cy - size, cx + size, cy + size], fill=(0, 89, 156), outline=(92, 157, 217), width=3)
    draw.text((cx - size // 2 + 3, cy - size + 4), "C", fill=(255, 255, 255), font=FONT_HEADER)


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


def draw_window_frame(draw, x0, y0, x1, y1, title="types.c", is_terminal=False):
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
    dw, dh = 240, 14
    draw.rounded_rectangle([dx - dw // 2, dy, dx + dw // 2, dy + dh], radius=6, fill=(45, 55, 75), outline=(70, 85, 115), width=2)
    draw.line([(dx - dw // 2 + 20, dy + dh), (dx - dw // 2 + 20, 1550)], fill=(70, 85, 115), width=4)
    draw.line([(dx + dw // 2 - 20, dy + dh), (dx + dw // 2 - 20, 1550)], fill=(70, 85, 115), width=4)
    cx, cy = dx + 150, dy + 25
    draw.rounded_rectangle([cx - 30, cy, cx + 30, cy + 10], radius=4, fill=(55, 65, 88))
    draw.line([(cx + 22, cy - 80), (cx + 22, cy + 10)], fill=(55, 65, 88), width=5)
    draw.line([(cx, cy + 10), (cx, 1550)], fill=(40, 50, 70), width=4)
    draw.line([(cx - 25, 1550), (cx + 25, 1550)], fill=(40, 50, 70), width=3)


def draw_laptop_on_desk(draw, lx=600, ly=1460):
    bw, bh = 135, 10
    draw.polygon([
        (lx - bw // 2, ly),
        (lx + bw // 2, ly),
        (lx + bw // 2 - 10, ly + bh),
        (lx - bw // 2 + 10, ly + bh)
    ], fill=LAPTOP_SILVER, outline=(160, 175, 195))
    draw.rectangle([lx - 14, ly + 2, lx + 14, ly + 8], fill=(180, 190, 205))
    sw, sh = 120, 72
    sy_top = ly - sh
    sx_left = lx - sw // 2 + 8
    sx_right = lx + sw // 2 - 8
    draw.polygon([(lx - sw // 2, ly), (lx + sw // 2, ly), (sx_right, sy_top), (sx_left, sy_top)], fill=LAPTOP_SCREEN, outline=LAPTOP_SILVER, width=2)
    draw.polygon([(lx - sw // 2 + 5, ly - 3), (lx + sw // 2 - 5, ly - 3), (sx_right - 5, sy_top + 5), (sx_left + 5, sy_top + 5)], fill=(45, 90, 140))


def draw_stickman_state(draw, state="walk", walk_x=100, t=0.0):
    color = STICK_YELLOW
    head_r = 24
    if state == "walk":
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
    elif state in ("sit_typing", "sit_idle", "sit_enter"):
        hx = 750
        hy = 1395
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx - 4, hy + head_r)
        hip = (750, 1485)
        draw.line([neck, hip], fill=color, width=7)
        draw.line([hip, (680, 1495)], fill=color, width=6)
        draw.line([(680, 1495), (670, 1550)], fill=color, width=6)
        shoulder = (neck[0] - 2, neck[1] + 12)
        if state == "sit_typing":
            t_wave = math.sin(t * 24.0) * 5.0
            draw.line([shoulder, (690, 1445)], fill=color, width=6)
            draw.line([(690, 1445), (610, 1460 + t_wave)], fill=color, width=6)
        elif state == "sit_enter":
            draw.line([shoulder, (680, 1430)], fill=color, width=6)
            draw.line([(680, 1430), (605, 1450)], fill=color, width=6)
        else:
            draw.line([shoulder, (695, 1450)], fill=color, width=6)
            draw.line([(695, 1450), (620, 1462)], fill=color, width=6)
    elif state == "confused":
        hx = 770
        hy = 1380
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx + 2, hy + head_r)
        hip = (755, 1485)
        draw.line([neck, hip], fill=color, width=7)
        draw.line([hip, (690, 1495)], fill=color, width=6)
        draw.line([(690, 1495), (680, 1550)], fill=color, width=6)
        shoulder = (neck[0] - 2, neck[1] + 10)
        draw.line([shoulder, (hx + 24, hy - 10)], fill=color, width=6)
        draw.line([(hx + 24, hy - 10), (hx + 6, hy - 25)], fill=color, width=6)
        draw.line([shoulder, (shoulder[0] - 30, shoulder[1] + 20)], fill=color, width=6)
        draw.text((hx - 40, hy - 65), "?", fill=ERROR_RED, font=FONT_HEADER)
        draw.text((hx + 30, hy - 75), "?", fill=AMBER_NUMBER, font=FONT_HEADER)
    elif state == "celebrate":
        hx = 750
        hy = 1390
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (750, 1485)
        draw.line([neck, hip], fill=color, width=7)
        draw.line([hip, (680, 1495)], fill=color, width=6)
        draw.line([(680, 1495), (670, 1550)], fill=color, width=6)
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
    
    draw.line([(0, 1550), (WIDTH, 1550)], fill=(22, 28, 42), width=3)
    
    draw_c_logo(draw, 410, 115, size=30)
    draw.text((455, 93), "C Language", fill=(92, 157, 217), font=FONT_HEADER)
    draw_centered_badge(
        draw, cx=WIDTH // 2, cy=175,
        text="EPISODE 2: DATA TYPES (%d, %f, %c)",
        font=FONT_SUBTITLE,
        fill_color=(18, 24, 38),
        text_color=CYAN_KEYWORD,
        outline_color=CYAN_KEYWORD,
        pad_x=22, pad_y=8
    )
    
    ed_x0, ed_y0 = 80, 230
    ed_x1, ed_y1 = 1000, 750
    draw_window_frame(draw, ed_x0, ed_y0, ed_x1, ed_y1, title="types.c", is_terminal=False)
    
    tm_x0, tm_y0 = 80, 790
    tm_x1, tm_y1 = 1000, 1220
    draw_window_frame(draw, tm_x0, tm_y0, tm_x1, tm_y1, title="TERMINAL - gcc build", is_terminal=True)
    
    draw_desk_and_chair(draw, dx=600, dy=1460)
    draw_laptop_on_desk(draw, lx=600, ly=1460)
    
    cursor_char = "_" if int(t * 4.0) % 2 == 0 else " "
    
    # C Code Lines
    l1 = [("#include ", PURPLE_OP), ("<stdio.h>", GREEN_STRING)]
    l2 = [("int ", CYAN_KEYWORD), ("main() {", WHITE_VAR)]
    l3 = [("    int ", CYAN_KEYWORD), ("age = ", WHITE_VAR), ("25;", AMBER_NUMBER)]
    l4 = [("    float ", CYAN_KEYWORD), ("score = ", WHITE_VAR), ("9.5;", AMBER_NUMBER)]
    l5_valid = [("    char ", CYAN_KEYWORD), ("grade = ", WHITE_VAR), ("'A';", GREEN_STRING)]
    l5_bug = [("    char ", CYAN_KEYWORD), ("grade = ", WHITE_VAR), ('"A";', ERROR_RED)]
    l6 = [("    printf(\"%d %.1f %c\\n\", age, score, grade);", WHITE_VAR)]
    l7 = [("    return ", CYAN_KEYWORD), ("0;", AMBER_NUMBER)]
    l8 = [("}", WHITE_VAR)]
    
    if t < 3.0:
        walk_x = int(100 + (t / 3.0) * 650)
        draw_stickman_state(draw, state="walk", walk_x=walk_x, t=t)
        draw.text((tm_x0 + 35, tm_y0 + 65), "$ gcc -v (ready for compilation)", fill=(71, 85, 105), font=FONT_TERM)

    elif t < 16.0:
        t_rel = t - 3.0
        draw.text((ed_x0 + 35, ed_y0 + 55), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 55, l1)
        draw.text((ed_x0 + 35, ed_y0 + 95), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 95, l2)
        draw.text((ed_x0 + 35, ed_y0 + 135), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, l3)
        draw.text((ed_x0 + 35, ed_y0 + 175), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 175, l4)
        draw.text((ed_x0 + 35, ed_y0 + 215), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, l5_valid)
        draw.text((ed_x0 + 35, ed_y0 + 255), "6", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 255, l6)
        draw.text((ed_x0 + 35, ed_y0 + 295), "7", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 295, l7)
        draw.text((ed_x0 + 35, ed_y0 + 335), "8", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 335, l8)
        
        # Hit Enter at 10.0s (13.0s overall) -> green highlight on printf line
        if t_rel >= 10.0:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 250, ed_x1 - 20, ed_y0 + 290], radius=6, fill=(16, 185, 129, 30), outline=SUCCESS_GREEN, width=2)
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ gcc types.c -o types && ./types", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 110), "25 9.5 A", fill=WHITE_VAR, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 155), "[Process exited with return code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ waiting for compilation...", fill=(71, 85, 105), font=FONT_TERM)
            
        pose = "sit_typing" if t_rel < 9.8 else ("sit_enter" if t_rel < 10.4 else "sit_idle")
        draw_stickman_state(draw, state=pose, t=t)

    elif t < 26.0:
        # Bug Demo: char grade = "A"; (Double Quotes Error!)
        t_rel = t - 16.0
        draw.text((ed_x0 + 35, ed_y0 + 55), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 55, l1)
        draw.text((ed_x0 + 35, ed_y0 + 95), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 95, l2)
        draw.text((ed_x0 + 35, ed_y0 + 135), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, l3)
        draw.text((ed_x0 + 35, ed_y0 + 175), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 175, l4)
        
        # Buggy Line 5
        draw.text((ed_x0 + 35, ed_y0 + 215), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, l5_bug)
        
        draw.text((ed_x0 + 35, ed_y0 + 255), "6", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 255, l6)
        draw.text((ed_x0 + 35, ed_y0 + 295), "7", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 295, l7)
        draw.text((ed_x0 + 35, ed_y0 + 335), "8", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 335, l8)
        
        # Hit Enter at 3.0s (19.0s overall) -> RED LINE HIGHLIGHT (Zero overlays covering the code!)
        if t_rel >= 3.0:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 210, ed_x1 - 20, ed_y0 + 250], radius=6, fill=(239, 68, 68, 35), outline=ERROR_RED, width=3)
            draw.text((tm_x0 + 35, tm_y0 + 55), "$ gcc types.c -o types", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 95), "types.c: In function 'main':", fill=WHITE_VAR, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 135), "types.c:5:18: error: incompatible types", fill=ERROR_RED, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 175), "char grade = \"A\";", fill=WHITE_VAR, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 215), "             ^~~ In C, 'char' uses single quotes 'A'!", fill=AMBER_NUMBER, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 265), ">> Double quotes \"...\" are for strings (char*)!", fill=MUTED_TEXT, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ compiling...", fill=(71, 85, 105), font=FONT_TERM)
            
        pose = "sit_typing" if t_rel < 2.8 else ("sit_enter" if t_rel < 3.4 else "confused")
        draw_stickman_state(draw, state=pose, t=t)

    elif t < 35.0:
        # Fix: changing to 'A'
        t_rel = t - 26.0
        draw.text((ed_x0 + 35, ed_y0 + 55), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 55, l1)
        draw.text((ed_x0 + 35, ed_y0 + 95), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 95, l2)
        draw.text((ed_x0 + 35, ed_y0 + 135), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, l3)
        draw.text((ed_x0 + 35, ed_y0 + 175), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 175, l4)
        
        # Fixed Line 5
        draw.text((ed_x0 + 35, ed_y0 + 215), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, l5_valid)
        
        draw.text((ed_x0 + 35, ed_y0 + 255), "6", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 255, l6)
        draw.text((ed_x0 + 35, ed_y0 + 295), "7", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 295, l7)
        draw.text((ed_x0 + 35, ed_y0 + 335), "8", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 335, l8)
        
        if t_rel < 2.0:
            draw.text((720, 1310), "💡 IDEA!", fill=(250, 204, 21), font=FONT_HEADER)
            
        # Hit Enter at 2.5s (28.5s overall) -> GREEN HIGHLIGHT
        if t_rel >= 2.5:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 210, ed_x1 - 20, ed_y0 + 250], radius=6, fill=(16, 185, 129, 30), outline=SUCCESS_GREEN, width=2)
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ gcc types.c -o types && ./types", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 110), "25 9.5 A", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 155), "[Process exited with return code 0]", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 205), ">> Single quotes 'A' fixed the char syntax!", fill=GREEN_STRING, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ updating code...", fill=(71, 85, 105), font=FONT_TERM)
            
        pose = "sit_typing" if t_rel < 2.3 else ("sit_enter" if t_rel < 2.9 else "celebrate")
        draw_stickman_state(draw, state=pose, t=t)

    else:
        # Act 4: Takeaway & Subscribe
        draw.text((ed_x0 + 35, ed_y0 + 55), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 55, l1)
        draw.text((ed_x0 + 35, ed_y0 + 95), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 95, l2)
        draw.text((ed_x0 + 35, ed_y0 + 135), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, l3)
        draw.text((ed_x0 + 35, ed_y0 + 175), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 175, l4)
        draw.text((ed_x0 + 35, ed_y0 + 215), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, l5_valid)
        draw.text((ed_x0 + 35, ed_y0 + 255), "6", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 255, l6)
        draw.text((ed_x0 + 35, ed_y0 + 295), "7", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 295, l7)
        draw.text((ed_x0 + 35, ed_y0 + 335), "8", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 335, l8)
        
        draw.text((tm_x0 + 35, tm_y0 + 65), "$ gcc types.c -o types && ./types", fill=MUTED_TEXT, font=FONT_TERM)
        draw.text((tm_x0 + 35, tm_y0 + 110), "25 9.5 A", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 155), "[Process exited with return code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        
        box_y0 = 1260
        box_y1 = 1380
        draw.rounded_rectangle([ed_x0, box_y0, ed_x1, box_y1], radius=16, fill=(28, 22, 10), outline=(250, 204, 21), width=3)
        draw.text((ed_x0 + 30, box_y0 + 20), "⭐ KEY TAKEAWAY:", fill=(250, 204, 21), font=FONT_ALERT)
        draw.text((ed_x0 + 30, box_y0 + 65), "In C, char uses single quotes 'A', strings use \"A\"!", fill=WHITE_VAR, font=FONT_CODE_BOLD)
        
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
    print("🎬 RENDERING C LANGUAGE EPISODE 2: CORE TYPES (%d, %f, %c)")
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
    thumb_path = THUMBNAILS_DIR / "channel2_c_ep2.jpg"
    thumb_im.save(thumb_path, quality=95)
    print(f"📸 Thumbnail saved: {thumb_path}")
    
    out_video = RENDERED_DIR / "channel2_c_ep2.mp4"
    
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
    
    print("\nEncoding final C Ep 2 video with FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr[-800:])
        raise RuntimeError("FFmpeg encoding failed.")
        
    print(f"🎉 Final C Ep 2 saved: {out_video}")


if __name__ == "__main__":
    main()

