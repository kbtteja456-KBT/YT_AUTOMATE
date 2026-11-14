"""Production Master Animation Studio: Yellow Stickman Python Education Video.
Created in strict adherence to the Master Reference Prompt & Reference Video.

Key Features:
- Pure/Near-Black Minimalism (#0B0E14)
- Centered Python Header with Official Serpents Icon
- Floating Clean Monospace Code Editor (Microsoft Consolas)
- Progressive character-by-character typing with blinking cursor
- Genuine real-time code execution with line highlight glow
- Floating Terminal below code with authentic outputs & real TypeError
- Dynamic Minimalist Yellow Stickman:
  * Kneeling / typing on sleek silver laptop
  * Pressing Enter/Run
  * Observing outputs
  * Confused reaction to TypeError (scratching head with '?')
  * Lightbulb fix moment
  * Celebrating success with thumbs up & golden sparkle particles
- Synchronized with Kenpath Labs Svara TTS (Vamsi, tuned pace 0.88)
- Zero slides, zero RAM memory boxes, 100% live coding demonstration
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
TEMP_DIR = STORAGE / "temp" / "master_stickman_demo"
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
TOTAL_SECONDS = 57.10
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Color Palette
BG_COLOR = (11, 14, 20)
STICK_YELLOW = (255, 215, 0)
STICK_OUTLINE = (235, 195, 0)
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
    FONT_CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 38)
    FONT_CODE_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 38)
    FONT_HEADER = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 44)
    FONT_SUBTITLE = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
    FONT_TERM = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 32)
    FONT_TERM_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 34)
    FONT_TELUGU = ImageFont.truetype("C:/Windows/Fonts/Nirmala.ttc", 36)
    FONT_ALERT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
except Exception:
    FONT_CODE = ImageFont.load_default()
    FONT_CODE_BOLD = ImageFont.load_default()
    FONT_HEADER = ImageFont.load_default()
    FONT_SUBTITLE = ImageFont.load_default()
    FONT_TERM = ImageFont.load_default()
    FONT_TERM_BOLD = ImageFont.load_default()
    FONT_TELUGU = ImageFont.load_default()
    FONT_ALERT = ImageFont.load_default()


def draw_python_logo(draw, cx, cy, size=40):
    """Draw crisp official vector Python serpents logo."""
    # Blue serpent (top-left)
    draw.rounded_rectangle([cx - size, cy - size, cx, cy + size // 4], radius=size // 4, fill=(55, 118, 171))
    draw.rounded_rectangle([cx - size, cy - size, cx + size // 2, cy - size // 4], radius=size // 4, fill=(55, 118, 171))
    draw.ellipse([cx - size // 2 - 4, cy - size // 2 - 4, cx - size // 2 + 4, cy - size // 2 + 4], fill=(255, 255, 255))
    
    # Yellow serpent (bottom-right)
    draw.rounded_rectangle([cx, cy - size // 4, cx + size, cy + size], radius=size // 4, fill=(255, 212, 59))
    draw.rounded_rectangle([cx - size // 2, cy + size // 4, cx + size, cy + size], radius=size // 4, fill=(255, 212, 59))
    draw.ellipse([cx + size // 2 - 4, cy + size // 2 - 4, cx + size // 2 + 4, cy + size // 2 + 4], fill=(11, 14, 20))


def draw_window_frame(draw, x0, y0, x1, y1, title="main.py", is_terminal=False):
    """Draw sleek modern floating window with window control dots."""
    bg = TERMINAL_BG if is_terminal else CARD_BG
    border = TERMINAL_BORDER if is_terminal else CARD_BORDER
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=bg, outline=border, width=2)
    
    # Header bar
    hbar_h = 44
    draw.rounded_rectangle([x0, y0, x1, y0 + hbar_h], radius=16, fill=(24, 30, 44))
    draw.rectangle([x0, y0 + hbar_h - 12, x1, y0 + hbar_h], fill=(24, 30, 44))
    
    # Window control dots
    draw.ellipse([x0 + 18, y0 + 16, x0 + 30, y0 + 28], fill=(239, 68, 68))
    draw.ellipse([x0 + 38, y0 + 16, x0 + 50, y0 + 28], fill=(245, 158, 11))
    draw.ellipse([x0 + 58, y0 + 16, x0 + 70, y0 + 28], fill=(16, 185, 129))
    
    # Title
    t_color = (125, 211, 252) if is_terminal else (203, 213, 225)
    draw.text((x0 + 85, y0 + 12), title, fill=t_color, font=FONT_SUBTITLE)


def draw_stickman(draw, x, y, pose="sit_typing", typing_t=0.0, is_confused=False, is_celebrating=False):
    """Render dynamic minimalist yellow stickman with purpose-driven animation."""
    head_r = 26
    color = STICK_YELLOW
    
    if pose in ("sit_typing", "sit_idle", "sit_enter"):
        # Sitting / kneeling pose on floor
        hx = x
        hy = y - 110
        # Head
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        
        # Torso (slight lean toward laptop on left)
        lean = 15 if pose == "sit_typing" else 5
        neck = (hx, hy + head_r)
        hip = (hx + lean, hy + head_r + 95)
        draw.line([neck, hip], fill=color, width=8)
        
        # Legs (folded sitting posture)
        knee = (hip[0] + 45, hip[1] + 35)
        foot = (knee[0] - 50, knee[1] + 25)
        draw.line([hip, knee], fill=color, width=7)
        draw.line([knee, foot], fill=color, width=7)
        
        # Arms
        shoulder = (neck[0] + 4, neck[1] + 15)
        if pose == "sit_typing":
            # Animated fingers tapping keyboard
            t_wave = math.sin(typing_t * 18.0) * 8.0
            elbow = (shoulder[0] - 40, shoulder[1] + 35)
            hand = (shoulder[0] - 85, shoulder[1] + 55 + t_wave)
            draw.line([shoulder, elbow], fill=color, width=7)
            draw.line([elbow, hand], fill=color, width=7)
        elif pose == "sit_enter":
            # Right arm raised striking enter key
            elbow = (shoulder[0] - 30, shoulder[1] + 15)
            hand = (shoulder[0] - 80, shoulder[1] + 45)
            draw.line([shoulder, elbow], fill=color, width=7)
            draw.line([elbow, hand], fill=color, width=7)
        else: # sit_idle
            elbow = (shoulder[0] - 25, shoulder[1] + 30)
            hand = (shoulder[0] - 65, shoulder[1] + 55)
            draw.line([shoulder, elbow], fill=color, width=7)
            draw.line([elbow, hand], fill=color, width=7)
            
    elif pose == "confused":
        # Recoiling back, scratching head in shock
        hx = x + 35
        hy = y - 120
        # Head tilted
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx - 5, hy + head_r)
        hip = (hx + 40, hy + head_r + 95)
        draw.line([neck, hip], fill=color, width=8)
        
        # Legs
        knee1 = (hip[0] + 30, hip[1] + 35)
        foot1 = (knee1[0] - 40, knee1[1] + 25)
        draw.line([hip, knee1], fill=color, width=7)
        draw.line([knee1, foot1], fill=color, width=7)
        
        # Left arm scratching head
        shoulder = (neck[0] + 5, neck[1] + 15)
        elbow_scratch = (hx + 30, hy - 10)
        hand_scratch = (hx + 10, hy - 25)
        draw.line([shoulder, elbow_scratch], fill=color, width=7)
        draw.line([elbow_scratch, hand_scratch], fill=color, width=7)
        
        # Right arm flailing back
        elbow_flail = (shoulder[0] + 40, shoulder[1] + 30)
        hand_flail = (elbow_flail[0] + 30, elbow_flail[1] - 10)
        draw.line([shoulder, elbow_flail], fill=color, width=7)
        draw.line([elbow_flail, hand_flail], fill=color, width=7)
        
        # Floating '?' confusion marks
        draw.text((hx - 45, hy - 65), "?", fill=(239, 68, 68), font=FONT_HEADER)
        draw.text((hx + 35, hy - 75), "?", fill=(245, 158, 11), font=FONT_HEADER)

    elif pose == "celebrate":
        # Victorious thumbs up / arms up
        hx = x
        hy = y - 150
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 100)
        draw.line([neck, hip], fill=color, width=8)
        
        # Legs standing slightly spread
        foot_l = (hip[0] - 35, hip[1] + 85)
        foot_r = (hip[0] + 35, hip[1] + 85)
        draw.line([hip, foot_l], fill=color, width=7)
        draw.line([hip, foot_r], fill=color, width=7)
        
        # Both arms raised in triumph
        shoulder = (neck[0], neck[1] + 15)
        hand_l = (shoulder[0] - 55, shoulder[1] - 50)
        hand_r = (shoulder[0] + 55, shoulder[1] - 50)
        draw.line([shoulder, (shoulder[0] - 35, shoulder[1] - 20)], fill=color, width=7)
        draw.line([(shoulder[0] - 35, shoulder[1] - 20), hand_l], fill=color, width=7)
        draw.line([shoulder, (shoulder[0] + 35, shoulder[1] - 20)], fill=color, width=7)
        draw.line([(shoulder[0] + 35, shoulder[1] - 20), hand_r], fill=color, width=7)
        
        # Golden sparkle stars
        for sx, sy in [(hx - 70, hy - 40), (hx + 75, hy - 45), (hx, hy - 65)]:
            draw.text((sx, sy), "★", fill=(250, 204, 21), font=FONT_ALERT)

    elif pose == "stand_pointing":
        # Standing holding laptop, pointing at code
        hx = x
        hy = y - 145
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 100)
        draw.line([neck, hip], fill=color, width=8)
        
        # Legs
        draw.line([hip, (hip[0] - 20, hip[1] + 85)], fill=color, width=7)
        draw.line([hip, (hip[0] + 20, hip[1] + 85)], fill=color, width=7)
        
        # Left arm holding laptop at chest
        shoulder = (neck[0], neck[1] + 15)
        draw.line([shoulder, (shoulder[0] - 30, shoulder[1] + 35)], fill=color, width=7)
        draw.line([(shoulder[0] - 30, shoulder[1] + 35), (shoulder[0] - 15, shoulder[1] + 40)], fill=color, width=7)
        
        # Right arm pointing up-left toward code
        draw.line([shoulder, (shoulder[0] - 40, shoulder[1] - 20)], fill=color, width=7)
        draw.line([(shoulder[0] - 40, shoulder[1] - 20), (shoulder[0] - 90, shoulder[1] - 50)], fill=color, width=7)


def draw_sleek_laptop(draw, lx, ly, screen_tilt=0.75):
    """Render sleek modern aluminum MacBook style laptop with glowing screen."""
    # Base / keyboard body
    bw, bh = 150, 16
    draw.polygon([
        (lx - bw // 2, ly),
        (lx + bw // 2, ly),
        (lx + bw // 2 - 15, ly + bh),
        (lx - bw // 2 + 15, ly + bh)
    ], fill=LAPTOP_SILVER, outline=(160, 175, 195))
    
    # Trackpad
    draw.rectangle([lx - 18, ly + 4, lx + 18, ly + 12], fill=(180, 190, 205))
    
    # Screen display tilted open
    sw, sh = 135, 85
    sy_top = ly - sh
    sx_left = lx - sw // 2 + 10
    sx_right = lx + sw // 2 - 10
    
    # Screen backing
    draw.polygon([
        (lx - sw // 2, ly),
        (lx + sw // 2, ly),
        (sx_right, sy_top),
        (sx_left, sy_top)
    ], fill=LAPTOP_SCREEN, outline=LAPTOP_SILVER, width=2)
    
    # Screen ambient glow (simulating active code window)
    draw.polygon([
        (lx - sw // 2 + 6, ly - 4),
        (lx + sw // 2 - 6, ly - 4),
        (sx_right - 6, sy_top + 6),
        (sx_left + 6, sy_top + 6)
    ], fill=(45, 90, 140))


def render_code_tokens(draw, x_start, y, tokens):
    """Render syntax highlighted tokens sequentially along a line."""
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
    
    # 1. Subtle Background Floor / Grid
    draw.line([(0, 1620), (WIDTH, 1620)], fill=(22, 28, 42), width=3)
    
    # 2. Centered Top Header: Python Logo + Title
    draw_python_logo(draw, 440, 130, size=32)
    draw.text((490, 105), "Python", fill=(255, 215, 0), font=FONT_HEADER)
    draw.rounded_rectangle([390, 175, 690, 215], radius=20, fill=(18, 24, 38), outline=(56, 189, 248), width=1)
    draw.text((425, 182), "LIVE CODE EXECUTION", fill=(56, 189, 248), font=FONT_SUBTITLE)
    
    # 3. Floating Code Editor Window (Upper-Middle)
    ed_x0, ed_y0 = 80, 250
    ed_x1, ed_y1 = 1000, 780
    draw_window_frame(draw, ed_x0, ed_y0, ed_x1, ed_y1, title="main.py", is_terminal=False)
    
    # 4. Floating Terminal Window (Lower-Middle)
    tm_x0, tm_y0 = 80, 820
    tm_x1, tm_y1 = 1000, 1260
    draw_window_frame(draw, tm_x0, tm_y0, tm_x1, tm_y1, title="TERMINAL - output", is_terminal=True)
    
    # Stickman & Laptop Default Coordinates (Lower-Right)
    sm_x, sm_y = 780, 1580
    lp_x, lp_y = 660, 1560
    
    # Cursor blink
    cursor_char = "_" if int(t * 3.5) % 2 == 0 else " "
    
    # =========================================================================
    # SCENE TIMELINE LOGIC
    # =========================================================================
    if t < 7.5:
        # ---------------------------------------------------------------------
        # SCENE 1: Basic Print (0.0s - 7.5s)
        # ---------------------------------------------------------------------
        full_code = 'print("Hello Python")'
        type_progress = min(1.0, max(0.0, (t - 1.2) / 3.8))
        chars_typed = int(type_progress * len(full_code))
        displayed_code = full_code[:chars_typed]
        
        # Render line 1
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        
        # Tokenize displayed portion
        tokens = []
        if chars_typed <= 5: # 'print'
            tokens.append((displayed_code, CYAN_KEYWORD))
        elif chars_typed <= 6: # 'print('
            tokens.append(("print", CYAN_KEYWORD))
            tokens.append(("(", PURPLE_OP))
        else: # 'print("...'
            tokens.append(("print", CYAN_KEYWORD))
            tokens.append(("(", PURPLE_OP))
            str_part = displayed_code[6:]
            if str_part.endswith(")"):
                tokens.append((str_part[:-1], GREEN_STRING))
                tokens.append((")", PURPLE_OP))
            else:
                tokens.append((str_part, GREEN_STRING))
                
        last_x = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokens)
        if type_progress < 1.0:
            draw.text((last_x + 4, ed_y0 + 75), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            
        # Execution highlight at 5.8s+
        if t >= 5.8:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 70, ed_x1 - 20, ed_y0 + 125], radius=8, fill=(16, 185, 129, 30), outline=(16, 185, 129), width=2)
            
        # Terminal Output appears at 6.0s
        if t >= 6.0:
            draw.text((tm_x0 + 35, tm_y0 + 75), ">>> Hello Python", fill=WHITE_VAR, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 130), "[Program exited with code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 75), ">>> waiting for execution...", fill=(71, 85, 105), font=FONT_TERM)
            
        # Stickman Animation
        if t < 5.6:
            pose = "sit_typing"
        elif 5.6 <= t < 6.2:
            pose = "sit_enter" # Hit enter
        else:
            pose = "sit_idle"
        draw_stickman(draw, sm_x, sm_y, pose=pose, typing_t=t)
        draw_sleek_laptop(draw, lp_x, lp_y)

    elif t < 17.0:
        # ---------------------------------------------------------------------
        # SCENE 2: Variables & Calculations (7.5s - 17.0s)
        # ---------------------------------------------------------------------
        t_rel = t - 7.5
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        
        # Line 1: a = 10
        p1 = min(1.0, max(0.0, (t_rel - 0.5) / 1.8))
        code1 = "a = 10"[:int(p1 * 6)]
        tokens1 = [("a", WHITE_VAR), (" = ", PURPLE_OP), (code1[4:], AMBER_NUMBER)] if len(code1) >= 4 else [(code1, WHITE_VAR)]
        x1 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokens1)
        if p1 < 1.0 and t_rel >= 0.5:
            draw.text((x1 + 4, ed_y0 + 75), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            
        # Line 2: b = 20
        if t_rel >= 2.5:
            p2 = min(1.0, max(0.0, (t_rel - 2.5) / 1.8))
            code2 = "b = 20"[:int(p2 * 6)]
            tokens2 = [("b", WHITE_VAR), (" = ", PURPLE_OP), (code2[4:], AMBER_NUMBER)] if len(code2) >= 4 else [(code2, WHITE_VAR)]
            x2 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, tokens2)
            if p2 < 1.0:
                draw.text((x2 + 4, ed_y0 + 135), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
                
        # Line 3: print(a + b)
        if t_rel >= 4.5:
            p3 = min(1.0, max(0.0, (t_rel - 4.5) / 2.0))
            code3 = "print(a + b)"[:int(p3 * 12)]
            tokens3 = [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("a + b", WHITE_VAR), (")", PURPLE_OP)] if p3 >= 1.0 else [(code3, CYAN_KEYWORD)]
            x3 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, tokens3)
            if p3 < 1.0:
                draw.text((x3 + 4, ed_y0 + 195), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
                
        # Execution highlight on line 3 at t_rel >= 6.8
        if t_rel >= 6.8:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 190, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(16, 185, 129, 30), outline=(16, 185, 129), width=2)
            
        # Terminal Output at 7.0s (14.5s overall)
        if t_rel >= 7.0:
            draw.text((tm_x0 + 35, tm_y0 + 75), ">>> 30", fill=WHITE_VAR, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 130), "[Program exited with code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 75), ">>> waiting for execution...", fill=(71, 85, 105), font=FONT_TERM)
            
        # Stickman
        if t_rel < 6.6:
            pose = "sit_typing"
        elif 6.6 <= t_rel < 7.2:
            pose = "sit_enter"
        else:
            pose = "stand_pointing" # Points at output 30
        draw_stickman(draw, sm_x, sm_y, pose=pose, typing_t=t)
        draw_sleek_laptop(draw, lp_x, lp_y)

    elif t < 32.0:
        # ---------------------------------------------------------------------
        # SCENE 3: String + Int TypeError Trap (17.0s - 32.0s)
        # ---------------------------------------------------------------------
        t_rel = t - 17.0
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        
        # Line 1: name = "Python"
        tokens1 = [("name", WHITE_VAR), (" = ", PURPLE_OP), ('"Python"', GREEN_STRING)]
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokens1)
        
        # Line 2: version = 3
        tokens2 = [("version", WHITE_VAR), (" = ", PURPLE_OP), ("3", AMBER_NUMBER)]
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, tokens2)
        
        # Line 3: print(name + version) (progressive typing)
        p3 = min(1.0, max(0.0, (t_rel - 1.0) / 4.0))
        full_line3 = "print(name + version)"
        c3 = full_line3[:int(p3 * len(full_line3))]
        tokens3 = [("print", CYAN_KEYWORD), ("(", PURPLE_OP), ("name", WHITE_VAR), (" + ", PURPLE_OP), ("version", WHITE_VAR), (")", PURPLE_OP)] if p3 >= 1.0 else [(c3, CYAN_KEYWORD)]
        x3 = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, tokens3)
        if p3 < 1.0:
            draw.text((x3 + 4, ed_y0 + 195), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            
        # Error Trigger at 7.5s (24.5s overall)
        if t_rel >= 7.5:
            # Highlight error line in RED
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 190, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(239, 68, 68, 40), outline=ERROR_RED, width=3)
            # Terminal Error Message
            draw.text((tm_x0 + 35, tm_y0 + 65), 'Traceback (most recent call last):', fill=ERROR_RED, font=FONT_TERM)
            draw.text((tm_x0 + 55, tm_y0 + 115), 'File "main.py", line 3, in <module>', fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 75, tm_y0 + 165), 'print(name + version)', fill=WHITE_VAR, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 225), 'TypeError: can only concatenate str', fill=ERROR_RED, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 270), '           (not "int") to str', fill=ERROR_RED, font=FONT_TERM_BOLD)
            
            # Confusion alert pill
            draw.rounded_rectangle([ed_x0 + 250, ed_y0 + 280, ed_x1 - 250, ed_y0 + 340], radius=15, fill=(45, 15, 20), outline=ERROR_RED, width=2)
            draw.text((ed_x0 + 285, ed_y0 + 292), "⚠️ TYPE ERROR: str + int", fill=ERROR_RED, font=FONT_ALERT)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 75), ">>> running program...", fill=(71, 85, 105), font=FONT_TERM)
            
        # Stickman pose
        if t_rel < 7.0:
            pose = "sit_typing"
        elif 7.0 <= t_rel < 7.6:
            pose = "sit_enter"
        else:
            pose = "confused" # Head scratch, shocked by error!
        draw_stickman(draw, sm_x, sm_y, pose=pose, typing_t=t, is_confused=(t_rel >= 7.6))
        draw_sleek_laptop(draw, lp_x, lp_y)

    elif t < 45.0:
        # ---------------------------------------------------------------------
        # SCENE 4: The Fix with str() & Celebration (32.0s - 45.0s)
        # ---------------------------------------------------------------------
        t_rel = t - 32.0
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        
        # Line 1: name = "Python"
        tokens1 = [("name", WHITE_VAR), (" = ", PURPLE_OP), ('"Python"', GREEN_STRING)]
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokens1)
        
        # Line 2: version = 3
        tokens2 = [("version", WHITE_VAR), (" = ", PURPLE_OP), ("3", AMBER_NUMBER)]
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, tokens2)
        
        # Line 3: print(name + str(version))
        fix_p = min(1.0, max(0.0, (t_rel - 1.5) / 4.5))
        full_fix = "print(name + str(version))"
        cf = full_fix[:int(fix_p * len(full_fix))]
        tokens3 = [
            ("print", CYAN_KEYWORD), ("(", PURPLE_OP),
            ("name", WHITE_VAR), (" + ", PURPLE_OP),
            ("str", CYAN_KEYWORD), ("(", PURPLE_OP),
            ("version", WHITE_VAR), (")", PURPLE_OP), (")", PURPLE_OP)
        ] if fix_p >= 1.0 else [(cf, CYAN_KEYWORD)]
        xf = render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, tokens3)
        if fix_p < 1.0:
            draw.text((xf + 4, ed_y0 + 195), cursor_char, fill=CYAN_KEYWORD, font=FONT_CODE)
            
        # Lightbulb icon during fix phase (0.0s - 3.5s)
        if t_rel < 3.5:
            draw.text((sm_x - 30, sm_y - 210), "💡 IDEA!", fill=(250, 204, 21), font=FONT_HEADER)
            
        # Execution highlight at 8.0s (40.0s overall)
        if t_rel >= 8.0:
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 190, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(16, 185, 129, 30), outline=(16, 185, 129), width=2)
            # Terminal Output: Python3 SUCCESS
            draw.text((tm_x0 + 35, tm_y0 + 75), ">>> Python3", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 130), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)
            # Success Pill
            draw.rounded_rectangle([ed_x0 + 250, ed_y0 + 280, ed_x1 - 250, ed_y0 + 340], radius=15, fill=(15, 45, 25), outline=SUCCESS_GREEN, width=2)
            draw.text((ed_x0 + 285, ed_y0 + 292), "✅ TYPECASTING FIXED!", fill=SUCCESS_GREEN, font=FONT_ALERT)
        else:
            draw.text((tm_x0 + 35, tm_y0 + 75), ">>> editing code...", fill=(71, 85, 105), font=FONT_TERM)
            
        # Stickman pose
        if t_rel < 7.5:
            pose = "sit_typing"
        elif 7.5 <= t_rel < 8.2:
            pose = "sit_enter"
        else:
            pose = "celebrate" # Arms up, victory sparkle stars!
        draw_stickman(draw, sm_x, sm_y, pose=pose, typing_t=t, is_celebrating=(t_rel >= 8.2))
        draw_sleek_laptop(draw, lp_x, lp_y)

    else:
        # ---------------------------------------------------------------------
        # SCENE 5: Golden Rule Takeaway & Subscribe (45.0s - 57.10s)
        # ---------------------------------------------------------------------
        # Show complete working code
        draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
        draw.text((ed_x0 + 35, ed_y0 + 135), "2", fill=MUTED_TEXT, font=FONT_CODE)
        draw.text((ed_x0 + 35, ed_y0 + 195), "3", fill=MUTED_TEXT, font=FONT_CODE)
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, [("name", WHITE_VAR), (" = ", PURPLE_OP), ('"Python"', GREEN_STRING)])
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 135, [("version", WHITE_VAR), (" = ", PURPLE_OP), ("3", AMBER_NUMBER)])
        render_code_tokens(draw, ed_x0 + 90, ed_y0 + 195, [
            ("print", CYAN_KEYWORD), ("(", PURPLE_OP),
            ("name", WHITE_VAR), (" + ", PURPLE_OP),
            ("str", CYAN_KEYWORD), ("(", PURPLE_OP),
            ("version", WHITE_VAR), (")", PURPLE_OP), (")", PURPLE_OP)
        ])
        
        # Terminal Final Result
        draw.text((tm_x0 + 35, tm_y0 + 75), ">>> Python3", fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
        draw.text((tm_x0 + 35, tm_y0 + 130), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)
        
        # Big Golden Rule Banner in Center
        draw.rounded_rectangle([ed_x0 + 30, ed_y0 + 270, ed_x1 - 30, ed_y0 + 390], radius=16, fill=(28, 22, 10), outline=(250, 204, 21), width=3)
        draw.text((ed_x0 + 60, ed_y0 + 295), "⭐ KEY TAKEAWAY:", fill=(250, 204, 21), font=FONT_ALERT)
        draw.text((ed_x0 + 60, ed_y0 + 340), "str + int gives TypeError → Use str(num)!", fill=WHITE_VAR, font=FONT_CODE_BOLD)
        
        # Stickman standing holding laptop, pointing at camera
        draw_stickman(draw, sm_x, sm_y, pose="stand_pointing", typing_t=t)
        draw_sleek_laptop(draw, lp_x, lp_y)
        
        # Subscribe Pill (Lower Center)
        pulse = 4 * math.sin(t * 6.0)
        draw.rounded_rectangle([320 - pulse, 1720 - pulse, 760 + pulse, 1800 + pulse], radius=40, fill=(220, 38, 38), outline=(255, 255, 255), width=2)
        draw.text((375, 1740), "🔔 SUBSCRIBE FOR MORE!", fill=WHITE_VAR, font=FONT_ALERT)
        
    return im


def main():
    print("==================================================================")
    print("🎬 RENDERING PRODUCTION MASTER STICKMAN PYTHON VIDEO")
    print(f"Total Duration: {TOTAL_SECONDS}s | FPS: {FPS} | Total Frames: {TOTAL_FRAMES}")
    print("Zero Slides | Zero Memory Boxes | Pure Code Typing & Execution")
    print("==================================================================")
    
    # 1. Render all frames
    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        frame.save(FRAMES_DIR / f"frame_{i:04d}.png")
        if i % 150 == 0 or i == TOTAL_FRAMES - 1:
            print(f"  Frame {i}/{TOTAL_FRAMES} rendered ({i/FPS:.1f}s / {TOTAL_SECONDS:.1f}s)")
            
    print(f"✅ All {TOTAL_FRAMES} frames successfully rendered!")
    
    # 2. Render high-contrast thumbnail
    thumb_im = render_frame(int(36.0 * FPS)) # Frame from lightbulb / fix moment
    thumb_path = THUMBNAILS_DIR / "master_stickman_coding_demo.jpg"
    thumb_im.save(thumb_path, quality=95)
    print(f"📸 High-Contrast Thumbnail saved: {thumb_path}")
    
    # 3. Audio & SFX Mixing via FFmpeg
    narration_path = STORAGE / "temp" / "master_telugu_narration.mp3"
    out_video = RENDERED_DIR / "master_stickman_coding_demo.mp4"
    
    sfx_whoosh = SFX_DIR / "whoosh.wav"
    sfx_pop = SFX_DIR / "pop.wav"
    sfx_zap = SFX_DIR / "zap.wav"
    sfx_keyboard = SFX_DIR / "keyboard.wav"
    sfx_ding = SFX_DIR / "success_ding.wav"
    
    filter_complex = (
        "[1:a]volume=1.0[narration];"
        "[2:a]adelay=0|0,volume=0.3[w0];"
        "[2:a]adelay=7500|7500,volume=0.3[w1];"
        "[2:a]adelay=17000|17000,volume=0.3[w2];"
        "[2:a]adelay=32000|32000,volume=0.3[w3];"
        "[3:a]adelay=1500|1500,volume=0.25[k1];"
        "[3:a]adelay=9000|9000,volume=0.25[k2];"
        "[3:a]adelay=18500|18500,volume=0.25[k3];"
        "[3:a]adelay=33500|33500,volume=0.25[k4];"
        "[4:a]adelay=5800|5800,volume=0.45[p1];"
        "[4:a]adelay=14300|14300,volume=0.45[p2];"
        "[4:a]adelay=24300|24300,volume=0.45[p3];"
        "[4:a]adelay=39800|39800,volume=0.45[p4];"
        "[5:a]adelay=24800|24800,volume=0.6[z_err];"
        "[6:a]adelay=40200|40200,volume=0.55[d_fix];"
        "[narration][w0][w1][w2][w3][k1][k2][k3][k4][p1][p2][p3][p4][z_err][d_fix]amix=inputs=15:duration=longest[aout]"
    )
    
    cmd = [
        FFMPEG, "-y",
        "-r", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(narration_path),
        "-i", str(sfx_whoosh),
        "-i", str(sfx_keyboard),
        "-i", str(sfx_pop),
        "-i", str(sfx_zap),
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
    
    print("\nEncoding final master video with FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr[-800:])
        raise RuntimeError("FFmpeg encoding failed.")
        
    print(f"🎉 Final Master Stickman Video saved: {out_video}")


if __name__ == "__main__":
    main()

