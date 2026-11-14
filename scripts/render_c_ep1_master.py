"""Production Master Animation Studio: C Language Ep 1 (First Program & printf()).
Target Channel: Second Channel (Bhanu Teja - @bhanuteja-n8x)

Key Features:
- 100% Fixed Stickman sitting posture: knees fold forward naturally toward laptop!
- Mathematically centered badges & text (zero clipping, zero overflow)
- Pure high-energy Sound Effects (Keyboard typing, enter pops, error buzz, success chime, whooshes)
- NO VOICE / Pure visual Alan Becker storytelling
- 1 concept per video: First C program & printf() + missing semicolon error demo!
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
TEMP_DIR = STORAGE / "temp" / "c_ep1_master"
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
TOTAL_SECONDS = 42.0  # 42s short
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Color Palette
BG_COLOR = (11, 14, 20)
STICK_YELLOW = (255, 215, 0)
CYAN_KEYWORD = (56, 189, 248)
BLUE_C_LOGO = (0, 89, 156)
GREEN_STRING = (74, 222, 128)
AMBER_ACCENT = (251, 191, 36)
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
    """Draw clean official vector C programming badge."""
    draw.ellipse([cx - size, cy - size, cx + size, cy + size], fill=(0, 89, 156), outline=(92, 157, 217), width=3)
    draw.text((cx - size // 2 + 3, cy - size + 4), "C", fill=(255, 255, 255), font=FONT_HEADER)


def draw_centered_badge(draw, cx, cy, text, font, fill_color, text_color, outline_color, pad_x=24, pad_y=10):
    """Draw mathematically centered pill badge with zero text overflow."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    rx0 = cx - tw // 2 - pad_x
    ry0 = cy - th // 2 - pad_y
    rx1 = cx + tw // 2 + pad_x
    ry1 = cy + th // 2 + pad_y
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=(ry1 - ry0) // 2, fill=fill_color, outline=outline_color, width=2)
    draw.text((cx - tw // 2, cy - th // 2 - 2), text, fill=text_color, font=font)


def draw_window_frame(draw, x0, y0, x1, y1, title="main.c", is_terminal=False):
    """Draw sleek modern floating window with window control dots."""
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


def draw_natural_stickman(draw, x, y, pose="sit_typing", typing_t=0.0):
    """Render anatomically correct stickman with forward-folding knees facing laptop."""
    head_r = 25
    color = STICK_YELLOW
    
    if pose in ("sit_typing", "sit_idle", "sit_enter"):
        hx = x
        hy = y - 110
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        
        neck = (hx - 4, hy + head_r)
        hip = (hx + 20, hy + head_r + 95)
        draw.line([neck, hip], fill=color, width=8)
        
        # Thigh moves FORWARD, shin folds BACK under hips
        knee = (hip[0] - 42, hip[1] + 32)
        foot = (hip[0] + 18, hip[1] + 45)
        draw.line([hip, knee], fill=color, width=7)
        draw.line([knee, foot], fill=color, width=7)
        
        shoulder = (neck[0] - 4, neck[1] + 15)
        if pose == "sit_typing":
            t_wave = math.sin(typing_t * 22.0) * 6.0
            elbow = (shoulder[0] - 38, shoulder[1] + 28)
            hand = (shoulder[0] - 82, shoulder[1] + 36 + t_wave)
            draw.line([shoulder, elbow], fill=color, width=7)
            draw.line([elbow, hand], fill=color, width=7)
        elif pose == "sit_enter":
            elbow = (shoulder[0] - 32, shoulder[1] + 12)
            hand = (shoulder[0] - 78, shoulder[1] + 28)
            draw.line([shoulder, elbow], fill=color, width=7)
            draw.line([elbow, hand], fill=color, width=7)
        else:
            elbow = (shoulder[0] - 25, shoulder[1] + 28)
            hand = (shoulder[0] - 65, shoulder[1] + 40)
            draw.line([shoulder, elbow], fill=color, width=7)
            draw.line([elbow, hand], fill=color, width=7)
            
    elif pose == "confused":
        hx = x + 30
        hy = y - 120
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx - 4, hy + head_r)
        hip = (hx + 25, hy + head_r + 95)
        draw.line([neck, hip], fill=color, width=8)
        
        knee = (hip[0] - 30, hip[1] + 32)
        foot = (hip[0] + 25, hip[1] + 45)
        draw.line([hip, knee], fill=color, width=7)
        draw.line([knee, foot], fill=color, width=7)
        
        shoulder = (neck[0], neck[1] + 15)
        elbow_scratch = (hx + 28, hy - 12)
        hand_scratch = (hx + 8, hy - 26)
        draw.line([shoulder, elbow_scratch], fill=color, width=7)
        draw.line([elbow_scratch, hand_scratch], fill=color, width=7)
        
        elbow_flail = (shoulder[0] - 35, shoulder[1] + 25)
        hand_flail = (elbow_flail[0] - 25, elbow_flail[1] - 15)
        draw.line([shoulder, elbow_flail], fill=color, width=7)
        draw.line([elbow_flail, hand_flail], fill=color, width=7)
        
        draw.text((hx - 40, hy - 65), "?", fill=ERROR_RED, font=FONT_HEADER)
        draw.text((hx + 30, hy - 75), "?", fill=AMBER_ACCENT, font=FONT_HEADER)

    elif pose == "celebrate":
        hx = x - 20
        hy = y - 145
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 95)
        draw.line([neck, hip], fill=color, width=8)
        
        draw.line([hip, (hip[0] - 25, hip[1] + 75)], fill=color, width=7)
        draw.line([hip, (hip[0] + 25, hip[1] + 75)], fill=color, width=7)
        
        shoulder = (neck[0], neck[1] + 15)
        draw.line([shoulder, (shoulder[0] - 40, shoulder[1] - 25)], fill=color, width=7)
        draw.line([(shoulder[0] - 40, shoulder[1] - 25), (shoulder[0] - 65, shoulder[1] - 55)], fill=color, width=7)
        draw.line([shoulder, (shoulder[0] + 40, shoulder[1] - 25)], fill=color, width=7)
        draw.line([(shoulder[0] + 40, shoulder[1] - 25), (shoulder[0] + 65, shoulder[1] - 55)], fill=color, width=7)
        
        for sx, sy in [(hx - 60, hy - 40), (hx + 65, hy - 45), (hx, hy - 65)]:
            draw.text((sx, sy), "★", fill=(250, 204, 21), font=FONT_HEADER)

    elif pose == "stand_pointing":
        hx = x - 20
        hy = y - 140
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 95)
        draw.line([neck, hip], fill=color, width=8)
        
        draw.line([hip, (hip[0] - 20, hip[1] + 75)], fill=color, width=7)
        draw.line([hip, (hip[0] + 20, hip[1] + 75)], fill=color, width=7)
        
        shoulder = (neck[0], neck[1] + 15)
        draw.line([shoulder, (shoulder[0] - 25, shoulder[1] + 30)], fill=color, width=7)
        draw.line([(shoulder[0] - 25, shoulder[1] + 30), (shoulder[0] - 10, shoulder[1] + 35)], fill=color, width=7)
        draw.line([shoulder, (shoulder[0] - 35, shoulder[1] - 20)], fill=color, width=7)
        draw.line([(shoulder[0] - 35, shoulder[1] - 20), (shoulder[0] - 85, shoulder[1] - 55)], fill=color, width=7)


def draw_sleek_laptop(draw, lx, ly):
    bw, bh = 145, 14
    draw.polygon([
        (lx - bw // 2, ly),
        (lx + bw // 2, ly),
        (lx + bw // 2 - 12, ly + bh),
        (lx - bw // 2 + 12, ly + bh)
    ], fill=LAPTOP_SILVER, outline=(160, 175, 195))
    
    draw.rectangle([lx - 16, ly + 3, lx + 16, ly + 10], fill=(180, 190, 205))
    
    sw, sh = 130, 80
    sy_top = ly - sh
    sx_left = lx - sw // 2 + 10
    sx_right = lx + sw // 2 - 10
    
    draw.polygon([
        (lx - sw // 2, ly),
        (lx + sw // 2, ly),
        (sx_right, sy_top),
        (sx_left, sy_top)
    ], fill=LAPTOP_SCREEN, outline=LAPTOP_SILVER, width=2)
    
    draw.polygon([
        (lx - sw // 2 + 6, ly - 4),
        (lx + sw // 2 - 6, ly - 4),
        (sx_right - 6, sy_top + 6),
        (sx_left + 6, sy_top + 6)
    ], fill=(45, 90, 140))


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
    
    # 1. Background Floor Horizon
    draw.line([(0, 1540), (WIDTH, 1540)], fill=(22, 28, 42), width=3)
    
    # 2. Header: Centered C Logo + Title
    draw_c_logo(draw, 410, 120, size=30)
    draw.text((455, 98), "C Language", fill=(92, 157, 217), font=FONT_HEADER)
    # Centered Badge
    draw_centered_badge(
        draw, cx=WIDTH // 2, cy=180,
        text="EPISODE 1: printf() & SEMICOLONS",
        font=FONT_SUBTITLE,
        fill_color=(18, 24, 38),
        text_color=CYAN_KEYWORD,
        outline_color=CYAN_KEYWORD,
        pad_x=22, pad_y=8
    )
    
    # 3. Floating Code Editor Window
    ed_x0, ed_y0 = 80, 240
    ed_x1, ed_y1 = 1000, 750
    draw_window_frame(draw, ed_x0, ed_y0, ed_x1, ed_y1, title="main.c", is_terminal=False)
    
    # 4. Floating Terminal Window
    tm_x0, tm_y0 = 80, 790
    tm_x1, tm_y1 = 1000, 1220
    draw_window_frame(draw, tm_x0, tm_y0, tm_x1, tm_y1, title="TERMINAL - gcc build", is_terminal=True)
    
    # Stickman & Laptop Coordinates
    sm_x, sm_y = 760, 1500
    lp_x, lp_y = 620, 1485
    
    cursor_char = "_" if int(t * 3.5) % 2 == 0 else " "
    
    # =========================================================================
    # TIMELINE PHASES (Total 42.0s)
    # =========================================================================
    if t < 12.0:
        # ---------------------------------------------------------------------
        # PHASE 1: Typing & Running C Program (0s - 12s)
        # ---------------------------------------------------------------------
        draw.text((ed_x0 + 35, ed_y0 + 65), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 65, [("#include ", PURPLE_OP), ("<stdio.h>", GREEN_STRING)])
        
        draw.text((ed_x0 + 35, ed_y0 + 115), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 115, [("int ", CYAN_KEYWORD), ("main() {", WHITE_VAR)])
        
        draw.text((ed_x0 + 35, ed_y0 + 165), "3", fill=MUTED_TEXT, font=FONT_CODE)
        full_line3 = '    printf("Hello, C!\\n");'
        type_p = min(1.0, max(0.0, (t - 1.2) / 4.5))
        chars = int(type_p * len(full_line3))
        c3 = full_line3[:chars]
        tokens3 = [("    printf", CYAN_KEYWORD), ("(", PURPLE_OP), ('"Hello, C!\\n"', GREEN_STRING), (");", PURPLE_OP)] if type_p >= 1.0 else [(c3, CYAN_KEYWORD)]
        x3 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 165, tokens3)
        if type_p < 1.0:
            draw.text((x3 + 4, ed_y0 + 165), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            
        draw.text((ed_x0 + 35, ed_y0 + 215), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, [("    return ", CYAN_KEYWORD), ("0;", AMBER_ACCENT)])
        draw.text((ed_x0 + 35, ed_y0 + 265), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 265, [("}", WHITE_VAR)])
        
        # Enter hit at 7.5s -> line execution highlight
        if t >= 7.5:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 160, ed_x1 - 20, ed_y0 + 210], radius=8, fill=(16, 185, 129, 30), outline=SUCCESS_GREEN, width=2)
            
        # Terminal Output appears at 7.8s
        if t >= 7.8:
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ gcc main.c -o main && ./main", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 115), "Hello, C!", fill=WHITE_VAR, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 165), "[Process exited with return code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ waiting for gcc build...", fill=(71, 85, 105), font=FONT_TERM)
            
        # Stickman
        if t < 7.2:
            pose = "sit_typing"
        elif 7.2 <= t < 7.8:
            pose = "sit_enter"
        else:
            pose = "sit_idle"
            
        draw_natural_stickman(draw, sm_x, sm_y, pose=pose, typing_t=t)
        draw_sleek_laptop(draw, lp_x, lp_y)

    elif t < 24.0:
        # ---------------------------------------------------------------------
        # PHASE 2: The Missing Semicolon Error Trap! (12s - 24s)
        # ---------------------------------------------------------------------
        t_rel = t - 12.0
        draw.text((ed_x0 + 35, ed_y0 + 65), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 65, [("#include ", PURPLE_OP), ("<stdio.h>", GREEN_STRING)])
        
        draw.text((ed_x0 + 35, ed_y0 + 115), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 115, [("int ", CYAN_KEYWORD), ("main() {", WHITE_VAR)])
        
        # Line 3: MISSING SEMICOLON
        draw.text((ed_x0 + 35, ed_y0 + 165), "3", fill=MUTED_TEXT, font=FONT_CODE)
        tokens3 = [("    printf", CYAN_KEYWORD), ("(", PURPLE_OP), ('"Hello, C!\\n"', GREEN_STRING), (")", PURPLE_OP)]  # No semicolon!
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 165, tokens3)
        
        draw.text((ed_x0 + 35, ed_y0 + 215), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, [("    return ", CYAN_KEYWORD), ("0;", AMBER_ACCENT)])
        draw.text((ed_x0 + 35, ed_y0 + 265), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 265, [("}", WHITE_VAR)])
        
        # Hit Enter at 5.0s (17.0s overall) -> C COMPILER CRASH!
        if t_rel >= 5.0:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 160, ed_x1 - 20, ed_y0 + 210], radius=8, fill=(239, 68, 68, 35), outline=ERROR_RED, width=3)
            # Terminal Error Message
            draw.text((tm_x0 + 35, tm_y0 + 60), "$ gcc main.c -o main", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 105), "main.c: In function 'main':", fill=WHITE_VAR, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 150), "main.c:4:5: error: expected ';' before 'return'", fill=ERROR_RED, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 55, tm_y0 + 195), "return 0;", fill=WHITE_VAR, font=FONT_TERM)
            draw.text((tm_x0 + 55, tm_y0 + 235), "^~~~~~ (Missing Semicolon on line 3!)", fill=AMBER_ACCENT, font=FONT_TERM)
            
            # Centered Warning Badge
            draw_centered_badge(
                draw, cx=WIDTH // 2, cy=ed_y0 + 320,
                text="⚠️ C SYNTAX ERROR: MISSING ';' SEMICOLON",
                font=FONT_ALERT,
                fill_color=(45, 15, 20),
                text_color=ERROR_RED,
                outline_color=ERROR_RED,
                pad_x=25, pad_y=10
            )
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ compiling with gcc...", fill=(71, 85, 105), font=FONT_TERM)
            
        if t_rel < 4.8:
            pose = "sit_typing"
        elif 4.8 <= t_rel < 5.4:
            pose = "sit_enter"
        else:
            pose = "confused"
            
        draw_natural_stickman(draw, sm_x, sm_y, pose=pose, typing_t=t)
        draw_sleek_laptop(draw, lp_x, lp_y)

    elif t < 34.0:
        # ---------------------------------------------------------------------
        # PHASE 3: Adding the Semicolon & Victory Celebration (24s - 34s)
        # ---------------------------------------------------------------------
        t_rel = t - 24.0
        draw.text((ed_x0 + 35, ed_y0 + 65), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 65, [("#include ", PURPLE_OP), ("<stdio.h>", GREEN_STRING)])
        
        draw.text((ed_x0 + 35, ed_y0 + 115), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 115, [("int ", CYAN_KEYWORD), ("main() {", WHITE_VAR)])
        
        # Line 3: Fixed with semicolon
        draw.text((ed_x0 + 35, ed_y0 + 165), "3", fill=MUTED_TEXT, font=FONT_CODE)
        tokens3 = [("    printf", CYAN_KEYWORD), ("(", PURPLE_OP), ('"Hello, C!\\n"', GREEN_STRING), (");", SUCCESS_GREEN)]
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 165, tokens3)
        
        draw.text((ed_x0 + 35, ed_y0 + 215), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, [("    return ", CYAN_KEYWORD), ("0;", AMBER_ACCENT)])
        draw.text((ed_x0 + 35, ed_y0 + 265), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 265, [("}", WHITE_VAR)])
        
        if t_rel < 2.5:
            draw.text((sm_x - 30, sm_y - 200), "💡 IDEA!", fill=(250, 204, 21), font=FONT_HEADER)
            
        # Hit Enter at 3.0s (27.0s overall) -> SUCCESS
        if t_rel >= 3.0:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 160, ed_x1 - 20, ed_y0 + 210], radius=8, fill=(16, 185, 129, 30), outline=SUCCESS_GREEN, width=2)
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ gcc main.c -o main && ./main", fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 115), "Hello, C!", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 165), "[Process exited with return code 0]", fill=MUTED_TEXT, font=FONT_TERM)
            
            # Centered Success Badge
            draw_centered_badge(
                draw, cx=WIDTH // 2, cy=ed_y0 + 320,
                text="✅ FIXED: ADDED ';' SEMICOLON!",
                font=FONT_ALERT,
                fill_color=(15, 45, 25),
                text_color=SUCCESS_GREEN,
                outline_color=SUCCESS_GREEN,
                pad_x=25, pad_y=10
            )
        else:
            draw.text((tm_x0 + 35, tm_y0 + 65), "$ fixing code...", fill=(71, 85, 105), font=FONT_TERM)
            
        if t_rel < 2.8:
            pose = "sit_typing"
        elif 2.8 <= t_rel < 3.4:
            pose = "sit_enter"
        else:
            pose = "celebrate"
            
        draw_natural_stickman(draw, sm_x, sm_y, pose=pose, typing_t=t)
        draw_sleek_laptop(draw, lp_x, lp_y)

    else:
        # ---------------------------------------------------------------------
        # PHASE 4: Golden Takeaway & Subscribe (34s - 42.0s)
        # ---------------------------------------------------------------------
        draw.text((ed_x0 + 35, ed_y0 + 65), "1", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 65, [("#include ", PURPLE_OP), ("<stdio.h>", GREEN_STRING)])
        draw.text((ed_x0 + 35, ed_y0 + 115), "2", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 115, [("int ", CYAN_KEYWORD), ("main() {", WHITE_VAR)])
        draw.text((ed_x0 + 35, ed_y0 + 165), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 165, [("    printf", CYAN_KEYWORD), ("(", PURPLE_OP), ('"Hello, C!\\n"', GREEN_STRING), (");", SUCCESS_GREEN)])
        draw.text((ed_x0 + 35, ed_y0 + 215), "4", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 215, [("    return ", CYAN_KEYWORD), ("0;", AMBER_ACCENT)])
        draw.text((ed_x0 + 35, ed_y0 + 265), "5", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 265, [("}", WHITE_VAR)])
        
        draw.text((tm_x0 + 35, tm_y0 + 65), "$ gcc main.c -o main && ./main", fill=MUTED_TEXT, font=FONT_TERM)
        draw.text((tm_x0 + 35, tm_y0 + 115), "Hello, C!", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 165), "[Process exited with return code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        
        # KEY TAKEAWAY BOX (zero overflow!)
        box_y0 = ed_y0 + 310
        box_y1 = ed_y0 + 440
        draw.rounded_rectangle([ed_x0 + 30, box_y0, ed_x1 - 30, box_y1], radius=16, fill=(28, 22, 10), outline=(250, 204, 21), width=3)
        draw.text((ed_x0 + 60, box_y0 + 22), "⭐ KEY TAKEAWAY:", fill=(250, 204, 21), font=FONT_ALERT)
        draw.text((ed_x0 + 60, box_y0 + 68), "Every statement in C must end with ';'!", fill=WHITE_VAR, font=FONT_CODE_BOLD)
        
        draw_natural_stickman(draw, sm_x, sm_y, pose="stand_pointing", typing_t=t)
        draw_sleek_laptop(draw, lp_x, lp_y)
        
        pulse = 3 * math.sin(t * 6.0)
        draw_centered_badge(
            draw, cx=WIDTH // 2, cy=1630,
            text="🔔 SUBSCRIBE FOR LESSON 2!",
            font=FONT_ALERT,
            fill_color=(220, 38, 38),
            text_color=WHITE_VAR,
            outline_color=WHITE_VAR,
            pad_x=28 + pulse, pad_y=12 + pulse
        )
        
    return im


def main():
    print("==================================================================")
    print("🎬 RENDERING C LANGUAGE EPISODE 1: FIRST PROGRAM & printf()")
    print(f"Total Duration: {TOTAL_SECONDS}s | FPS: {FPS} | Total Frames: {TOTAL_FRAMES}")
    print("Zero Voice | Pure Visual Alan Becker Storytelling | Rich SFX")
    print("==================================================================")
    
    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        frame.save(FRAMES_DIR / f"frame_{i:04d}.png")
        if i % 150 == 0 or i == TOTAL_FRAMES - 1:
            print(f"  Frame {i}/{TOTAL_FRAMES} rendered ({i/FPS:.1f}s / {TOTAL_SECONDS:.1f}s)")
            
    print(f"✅ All {TOTAL_FRAMES} frames successfully rendered!")
    
    thumb_im = render_frame(int(31.0 * FPS))
    thumb_path = THUMBNAILS_DIR / "channel2_c_ep1.jpg"
    thumb_im.save(thumb_path, quality=95)
    print(f"📸 Thumbnail saved: {thumb_path}")
    
    out_video = RENDERED_DIR / "channel2_c_ep1.mp4"
    
    sfx_whoosh = SFX_DIR / "whoosh.wav"
    sfx_pop = SFX_DIR / "pop.wav"
    sfx_buzzer = SFX_DIR / "buzzer.wav"
    sfx_keyboard = SFX_DIR / "keyboard.wav"
    sfx_ding = SFX_DIR / "success_ding.wav"
    sfx_ambient = SFX_DIR / "ambient_coding_pad.wav"
    
    filter_complex = (
        "[1:a]volume=0.22[amb];"
        "[2:a]adelay=0|0,volume=0.35[w0];"
        "[2:a]adelay=12000|12000,volume=0.35[w1];"
        "[2:a]adelay=24000|24000,volume=0.35[w2];"
        "[2:a]adelay=34000|34000,volume=0.35[w3];"
        "[3:a]adelay=1500|1500,volume=0.35[k1];"
        "[3:a]adelay=13000|13000,volume=0.35[k2];"
        "[3:a]adelay=25000|25000,volume=0.35[k3];"
        "[4:a]adelay=7500|7500,volume=0.55[p1];"
        "[4:a]adelay=17000|17000,volume=0.55[p2];"
        "[4:a]adelay=27000|27000,volume=0.55[p3];"
        "[5:a]adelay=17200|17200,volume=0.65[b_err];"
        "[6:a]adelay=7800|7800,volume=0.55[d1];"
        "[6:a]adelay=27200|27200,volume=0.65[d2];"
        "[amb][w0][w1][w2][w3][k1][k2][k3][p1][p2][p3][b_err][d1][d2]amix=inputs=14:duration=longest[aout]"
    )
    
    cmd = [
        FFMPEG, "-y",
        "-r", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(sfx_ambient),
        "-i", str(sfx_whoosh),
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
    
    print("\nEncoding final C Ep 1 video with FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr[-800:])
        raise RuntimeError("FFmpeg encoding failed.")
        
    print(f"🎉 Final C Ep 1 saved: {out_video}")


if __name__ == "__main__":
    main()

