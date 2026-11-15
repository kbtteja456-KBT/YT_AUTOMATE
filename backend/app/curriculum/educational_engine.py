"""Production Master Animation Studio: Educational Engine (Alan Becker Style).
Generates high-retention live-coding 2D stickman programming Shorts (Ep 1 to 10,000+).

Core Design Rules:
1. ZERO VOICE NARRATION: Pure international visual storytelling + punchy SFX.
2. NO GHOST STICKMAN: Desk & Chair is 100% EMPTY when stickman walks in from left!
3. LAPTOP OPPOSITE STICKMAN: Laptop screen tilted toward stickman's eyes and hands.
4. PROGRESSIVE TYPING: Characters type with continuous keyboard clacks.
5. BUGGY CODE FIRST: Runs buggy code -> Terminal error -> Red highlight underneath code.
6. 5-SECOND PACING & THINKING: Stickman leaves chair, walks back and forth with hand on chin (? ?).
7. BACKSPACE LETTER-BY-LETTER: Sits back down, deletes mistake with backspace audio, types fix.
8. YAAAYYY CELEBRATION: Terminal succeeds (Green) -> leaps out of chair into center floor shouting YAAAYYY! with golden stars!
9. MULTI-LINE TAKEAWAY: Structured 2-to-3 line key takeaway box that fits 100% inside borders (zero overflow!).
"""

import os
import sys
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary
from backend.app.core.logging import logger

FFMPEG = get_ffmpeg_binary()
WORKSPACE_DIR = Path(os.getcwd())
STORAGE = WORKSPACE_DIR / "media_storage"
TEMP_DIR = STORAGE / "temp" / "educational_studio"
RENDERED_DIR = STORAGE / "rendered"
THUMBNAILS_DIR = STORAGE / "thumbnails"
SFX_DIR = STORAGE / "assets" / "sfx"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
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
AMBER_NUMBER = (251, 146, 60)
PURPLE_OP = (192, 132, 252)
GREEN_STRING = (52, 211, 153)
WHITE_VAR = (241, 245, 249)
MUTED_TEXT = (100, 116, 139)
CARD_BG = (17, 24, 39)
CARD_BORDER = (31, 41, 55)
TERMINAL_BG = (10, 15, 26)
TERMINAL_BORDER = (30, 41, 59)
ERROR_RED = (239, 68, 68)
SUCCESS_GREEN = (34, 197, 94)
LAPTOP_SILVER = (190, 200, 215)

def load_cross_platform_font(font_names: List[str], size: int) -> ImageFont.ImageFont:
    """Search Windows, Linux/Ubuntu, and macOS font directories for matching fonts."""
    search_dirs = [
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts/truetype"),
        Path("/usr/share/fonts/truetype/liberation"),
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts"),
        Path.home() / ".fonts",
    ]
    for name in font_names:
        p = Path(name)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
        for d in search_dirs:
            if not d.exists():
                continue
            candidate = d / name
            if candidate.exists():
                try:
                    return ImageFont.truetype(str(candidate), size)
                except Exception:
                    pass
            matches = list(d.rglob(name))
            if matches:
                try:
                    return ImageFont.truetype(str(matches[0]), size)
                except Exception:
                    pass
    return ImageFont.load_default()

FONT_CODE = load_cross_platform_font(["consola.ttf", "LiberationMono-Regular.ttf", "DejaVuSansMono.ttf"], 34)
FONT_CODE_BOLD = load_cross_platform_font(["consolab.ttf", "LiberationMono-Bold.ttf", "DejaVuSansMono-Bold.ttf"], 34)
FONT_HEADER = load_cross_platform_font(["arialbd.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"], 46)
FONT_SUBTITLE = load_cross_platform_font(["arialbd.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"], 24)
FONT_TERM = load_cross_platform_font(["consola.ttf", "LiberationMono-Regular.ttf", "DejaVuSansMono.ttf"], 28)
FONT_TERM_BOLD = load_cross_platform_font(["consolab.ttf", "LiberationMono-Bold.ttf", "DejaVuSansMono-Bold.ttf"], 30)
FONT_ALERT = load_cross_platform_font(["arialbd.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"], 28)
FONT_COMIC = load_cross_platform_font(["arialbd.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"], 36)


def tokenize_code(line: str, is_c: bool = False) -> List[Tuple[str, Tuple[int, int, int]]]:
    """Tokenize source line into colored syntax tokens."""
    keywords_py = {'def', 'return', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'in', 'class', 'print', 'str', 'int', 'float', 'bool', 'True', 'False', 'None'}
    keywords_c = {'int', 'float', 'char', 'double', 'void', 'return', 'if', 'else', 'for', 'while', 'printf', 'include', 'define', 'struct', 'typedef', 'NULL'}
    keywords = keywords_c if is_c else keywords_py

    pattern = re.compile(r'(\".*?\"|\'.*?\'|//.*|\#.*|\b\d+\b|\b[a-zA-Z_]\w*\b|[^\s\w]|\s+)')
    tokens = []
    for match in pattern.finditer(line):
        token = match.group()
        if token.startswith('#') or token.startswith('//'):
            tokens.append((token, MUTED_TEXT))
        elif (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            tokens.append((token, GREEN_STRING))
        elif token.isdigit():
            tokens.append((token, AMBER_NUMBER))
        elif token in keywords:
            tokens.append((token, CYAN_KEYWORD))
        elif token in '+-*/=<>!&|^%':
            tokens.append((token, PURPLE_OP))
        else:
            tokens.append((token, WHITE_VAR))
    return tokens


def draw_branding_logo(draw, cx, cy, is_c: bool = False, size: int = 40):
    if is_c:
        # C Logo
        draw.ellipse([cx - size, cy - size, cx + size, cy + size], fill=(0, 89, 156), outline=(92, 157, 219), width=3)
        draw.text((cx - size // 2 + 5, cy - size // 2 - 4), "C", fill=(255, 255, 255), font=FONT_HEADER)
    else:
        # Python Logo
        draw.rounded_rectangle([cx - size, cy - size, cx, cy], radius=size // 4, fill=(56, 114, 164))
        draw.ellipse([cx - size * 0.7, cy - size * 0.7, cx - size * 0.4, cy - size * 0.4], fill=(255, 255, 255))
        draw.rounded_rectangle([cx, cy, cx + size, cy + size], radius=size // 4, fill=(255, 212, 59))
        draw.ellipse([cx + size * 0.4, cy + size * 0.4, cx + size * 0.7, cy + size * 0.7], fill=(11, 14, 20))


def draw_window_frame(draw, x0, y0, x1, y1, title="code.py", is_terminal=False):
    bg = TERMINAL_BG if is_terminal else CARD_BG
    border = TERMINAL_BORDER if is_terminal else CARD_BORDER
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=bg, outline=border, width=2)
    draw.rounded_rectangle([x0, y0, x1, y0 + 44], radius=16, fill=(22, 30, 46) if is_terminal else (26, 36, 54))
    draw.rectangle([x0, y0 + 30, x1, y0 + 44], fill=(22, 30, 46) if is_terminal else (26, 36, 54))
    draw.ellipse([x0 + 16, y0 + 15, x0 + 28, y0 + 27], fill=(239, 68, 68))
    draw.ellipse([x0 + 36, y0 + 15, x0 + 48, y0 + 27], fill=(245, 158, 11))
    draw.ellipse([x0 + 56, y0 + 15, x0 + 68, y0 + 27], fill=(34, 197, 94))
    t_color = (148, 163, 184) if is_terminal else (203, 213, 225)
    draw.text((x0 + 80, y0 + 11), title, fill=t_color, font=FONT_SUBTITLE)


def draw_empty_desk_and_chair(draw, dx=560, dy=1460):
    """Draw ONLY the furniture & laptop. Chair is empty (no ghost stickman!)."""
    # Desk
    dw, dh = 300, 14
    dx0, dx1 = dx - dw // 2, dx + dw // 2
    draw.rounded_rectangle([dx0, dy, dx1, dy + dh], radius=6, fill=(45, 55, 75), outline=(70, 85, 115), width=2)
    draw.line([(dx0 + 25, dy + dh), (dx0 + 25, 1550)], fill=(70, 85, 115), width=4)
    draw.line([(dx1 - 25, dy + dh), (dx1 - 25, 1550)], fill=(70, 85, 115), width=4)

    # Empty Chair at x=730
    cx, cy = 730, dy + 25
    draw.rounded_rectangle([cx - 30, cy, cx + 30, cy + 10], radius=4, fill=(55, 65, 88))
    draw.line([(cx + 25, cy - 85), (cx + 25, cy + 10)], fill=(55, 65, 88), width=5)
    draw.line([(cx, cy + 10), (cx, 1550)], fill=(40, 50, 70), width=4)
    draw.line([(cx - 25, 1550), (cx + 25, 1550)], fill=(40, 50, 70), width=3)

    # Laptop on desk facing stickman (screen tilted right toward his eyes)
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
        draw.line([shoulder, (hx - 15, hy + 50)], fill=color, width=6)
        draw.line([shoulder, (hx + 18, hy + 30)], fill=color, width=6)
        draw.line([(hx + 18, hy + 30), (hx + 4, hy + 18)], fill=color, width=6)
        
        # Animated floating question marks
        q_wiggle = math.sin(t * 6.0) * 6
        draw.text((hx - 35, hy - 65 + q_wiggle), "?", fill=ERROR_RED, font=FONT_HEADER)
        draw.text((hx + 28, hy - 75 - q_wiggle), "?", fill=AMBER_NUMBER, font=FONT_HEADER)

    elif action == "yaay_celebrate":
        # LEAPED OUT OF CHAIR! Jumping in the air in center floor with YAAAYYY!
        jump_y = int(math.sin(t * 8.0) * 35)
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
        
        # Sparkle celebration stars
        for sx, sy in [(hx - 140, hy - 40), (hx + 130, hy - 30), (hx - 90, hy + 50), (hx + 100, hy + 60)]:
            s_wiggle = 5 + int(3 * math.sin(t * 12.0))
            draw.line([(sx - s_wiggle, sy), (sx + s_wiggle, sy)], fill=(255, 215, 0), width=3)
            draw.line([(sx, sy - s_wiggle), (sx, sy + s_wiggle)], fill=(255, 215, 0), width=3)

    elif action == "thumbs_up":
        # Standing proudly next to desk, giving big thumbs up!
        hx = 480
        hy = 1400
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        neck = (hx, hy + head_r)
        hip = (hx, hy + head_r + 80)
        draw.line([neck, hip], fill=color, width=7)
        draw.line([hip, (hip[0] - 18, 1550)], fill=color, width=6)
        draw.line([hip, (hip[0] + 18, 1550)], fill=color, width=6)
        shoulder = (neck[0], neck[1] + 12)
        draw.line([shoulder, (shoulder[0] - 25, shoulder[1] + 45)], fill=color, width=6)
        draw.line([shoulder, (shoulder[0] + 35, shoulder[1] - 10)], fill=color, width=6)
        draw.line([(shoulder[0] + 35, shoulder[1] - 10), (shoulder[0] + 55, shoulder[1] - 25)], fill=color, width=6)
        draw.line([(shoulder[0] + 55, shoulder[1] - 25), (shoulder[0] + 55, shoulder[1] - 40)], fill=color, width=7)


def render_code_tokens(draw, x_start, y, tokens):
    cur_x = x_start
    for text, col in tokens:
        draw.text((cur_x, y), text, fill=col, font=FONT_CODE)
        bbox = FONT_CODE.getbbox(text)
        cur_x += (bbox[2] - bbox[0])
    return cur_x


def render_educational_episode(ep_data: Dict[str, Any], is_c: bool = False) -> str:
    """Master production generator for any Python or C programming episode (Ep 1 to 10,000)."""
    ep_num = ep_data.get("actual_episode_number") or ep_data.get("episode", 1)
    title = ep_data.get("title", f"Concept Lesson {ep_num}")
    if "is_c" in ep_data:
        is_c = ep_data["is_c"]
    elif "c programming" in title.lower() or "c " in title.lower() or ep_data.get("niche") == "C Programming":
        is_c = True

    channel_name = "C Programming Mastery" if is_c else "Python Mastery Series"
    file_prefix = f"channel2_c_ep{ep_num}" if is_c else f"educational_python_ep{ep_num}"
    final_video = RENDERED_DIR / f"{file_prefix}.mp4"
    final_thumb = THUMBNAILS_DIR / f"{file_prefix}.jpg"

    code_lines_raw = ep_data.get("code_lines", [])
    output_str = ep_data.get("output_str", "Success")
    error_demo = ep_data.get("error_demo") or {}

    if is_c:
        filename = f"lesson_{ep_num}.c"
        buggy_token = '"A"'
        fixed_token = "'A'"
        takeaway_l1 = f"In C, single char uses single quotes '{fixed_token[1]}'!"
        takeaway_l2 = "Double quotes are strictly reserved for strings (char*)"
        err_cmd = f"$ gcc {filename} -o out"
        err_msg = error_demo.get("error_msg", f"error: invalid conversion in assignment")
        ok_cmd = f"$ gcc {filename} -o out && ./out"
        ok_msg = output_str
    else:
        filename = f"lesson_{ep_num}.py"
        buggy_token = "age + name"
        fixed_token = "str(age) + name"
        takeaway_l1 = f"int + str gives TypeError in Python!"
        takeaway_l2 = "Fix: Always convert with str(num) before combining"
        err_cmd = f">>> python3 {filename}"
        err_msg = error_demo.get("error_msg", "TypeError: unsupported operand type(s) for +: 'int' and 'str'")
        ok_cmd = f">>> python3 {filename}"
        ok_msg = f">>> {output_str}"

    print(f"\n==================================================================")
    print(f"🎬 RENDERING MASTER EDUCATIONAL EPISODE {ep_num}: {title.upper()}")
    print(f"Target: {'C Programming' if is_c else 'Python'} | Duration: {TOTAL_SECONDS}s")
    print(f"==================================================================")

    ep_frames_dir = TEMP_DIR / f"frames_ep{ep_num}_{'c' if is_c else 'py'}"
    if ep_frames_dir.exists():
        shutil.rmtree(ep_frames_dir)
    ep_frames_dir.mkdir(parents=True, exist_ok=True)

    ed_x0, ed_y0, ed_x1, ed_y1 = 80, 240, 1000, 720
    tm_x0, tm_y0, tm_x1, tm_y1 = 80, 760, 1000, 1040

    # 1. Render all frames
    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS
        im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(im)

        # Subtle dark grid
        for gy in range(0, HEIGHT, 100):
            draw.line([(0, gy), (WIDTH, gy)], fill=(16, 20, 28), width=1)
        for gx in range(0, WIDTH, 100):
            draw.line([(gx, 0), (gx, HEIGHT)], fill=(16, 20, 28), width=1)

        # Header
        draw_branding_logo(draw, 140, 120, is_c=is_c, size=38)
        draw.text((200, 85), channel_name, fill=CYAN_KEYWORD, font=FONT_SUBTITLE)
        draw.text((200, 115), f"EPISODE {ep_num}: {title[:32]}", fill=WHITE_VAR, font=FONT_HEADER)

        # Base Windows
        draw_window_frame(draw, ed_x0, ed_y0, ed_x1, ed_y1, title=filename, is_terminal=False)
        draw_window_frame(draw, tm_x0, tm_y0, tm_x1, tm_y1, title="TERMINAL - output", is_terminal=True)

        # Always draw empty furniture
        draw_empty_desk_and_chair(draw, dx=560, dy=1460)

        # Choreography State Machine
        if t < 2.8:
            # Act 0: Walking in
            walk_prog = t / 2.8
            walk_x = int(80 + walk_prog * (720 - 80))
            draw_stickman_actor(draw, action="walk_in", walk_x=walk_x, t=t)
            draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
            draw.rectangle([ed_x0 + 90, ed_y0 + 75, ed_x0 + 92, ed_y0 + 115], fill=WHITE_VAR)

        elif t < 13.0:
            # Act 1: Seated typing buggy code
            draw_stickman_actor(draw, action="sitting_typing", t=t)
            draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
            tokens_l1 = tokenize_code(code_lines_raw[0] if code_lines_raw else "a = 25", is_c=is_c)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokens_l1)

            if len(code_lines_raw) > 1:
                draw.text((ed_x0 + 35, ed_y0 + 130), "2", fill=MUTED_TEXT, font=FONT_CODE)
                render_code_tokens(draw, ed_x0 + 90, ed_y0 + 130, tokenize_code(code_lines_raw[1], is_c=is_c))

            draw.text((ed_x0 + 35, ed_y0 + 185), "3", fill=MUTED_TEXT, font=FONT_CODE)
            target_line = code_lines_raw[2] if len(code_lines_raw) > 2 else f"print({buggy_token})"
            sub_len = max(1, min(len(target_line), int((t - 6.5) * 12))) if t >= 6.5 else 1
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 185, tokenize_code(target_line[:sub_len], is_c=is_c))

        elif t < 14.0:
            # Act 2: Hits Enter -> Error crashes!
            draw_stickman_actor(draw, action="sitting_enter", t=t)
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(45, 16, 16), outline=ERROR_RED, width=2)
            draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokenize_code(code_lines_raw[0], is_c=is_c))
            if len(code_lines_raw) > 1:
                draw.text((ed_x0 + 35, ed_y0 + 130), "2", fill=MUTED_TEXT, font=FONT_CODE)
                render_code_tokens(draw, ed_x0 + 90, ed_y0 + 130, tokenize_code(code_lines_raw[1], is_c=is_c))
            draw.text((ed_x0 + 35, ed_y0 + 185), "3", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 185, tokenize_code(code_lines_raw[2] if len(code_lines_raw) > 2 else f"print({buggy_token})", is_c=is_c))

            draw.text((tm_x0 + 35, tm_y0 + 65), err_cmd, fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 115), err_msg[:50], fill=ERROR_RED, font=FONT_TERM_BOLD)

        elif t < 19.5:
            # Act 3: Jumps out of chair! Pacing thinking for 5 seconds (? ?)
            draw_stickman_actor(draw, action="pacing_thinking", t=t)
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(45, 16, 16), outline=ERROR_RED, width=2)
            draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokenize_code(code_lines_raw[0], is_c=is_c))
            if len(code_lines_raw) > 1:
                draw.text((ed_x0 + 35, ed_y0 + 130), "2", fill=MUTED_TEXT, font=FONT_CODE)
                render_code_tokens(draw, ed_x0 + 90, ed_y0 + 130, tokenize_code(code_lines_raw[1], is_c=is_c))
            draw.text((ed_x0 + 35, ed_y0 + 185), "3", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 185, tokenize_code(code_lines_raw[2] if len(code_lines_raw) > 2 else f"print({buggy_token})", is_c=is_c))

            draw.text((tm_x0 + 35, tm_y0 + 65), err_cmd, fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 115), err_msg[:50], fill=ERROR_RED, font=FONT_TERM_BOLD)

        elif t < 27.5:
            # Act 4: Backspaces mistake & types fix!
            draw_stickman_actor(draw, action="sitting_typing", t=t)
            draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokenize_code(code_lines_raw[0], is_c=is_c))
            if len(code_lines_raw) > 1:
                draw.text((ed_x0 + 35, ed_y0 + 130), "2", fill=MUTED_TEXT, font=FONT_CODE)
                render_code_tokens(draw, ed_x0 + 90, ed_y0 + 130, tokenize_code(code_lines_raw[1], is_c=is_c))
            draw.text((ed_x0 + 35, ed_y0 + 185), "3", fill=MUTED_TEXT, font=FONT_CODE)
            fixed_line = f"print({fixed_token})" if not is_c else f"char grade = {fixed_token};"
            sub_fix = max(1, min(len(fixed_line), int((t - 21.0) * 14))) if t >= 21.0 else 1
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 185, tokenize_code(fixed_line[:sub_fix], is_c=is_c))

        elif t < 29.0:
            # Act 5: Strikes Enter -> Success in Green!
            draw_stickman_actor(draw, action="sitting_enter", t=t)
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(16, 45, 28), outline=SUCCESS_GREEN, width=2)
            draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokenize_code(code_lines_raw[0], is_c=is_c))
            if len(code_lines_raw) > 1:
                draw.text((ed_x0 + 35, ed_y0 + 130), "2", fill=MUTED_TEXT, font=FONT_CODE)
                render_code_tokens(draw, ed_x0 + 90, ed_y0 + 130, tokenize_code(code_lines_raw[1], is_c=is_c))
            draw.text((ed_x0 + 35, ed_y0 + 185), "3", fill=MUTED_TEXT, font=FONT_CODE)
            fixed_line = f"print({fixed_token})" if not is_c else f"char grade = {fixed_token};"
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 185, tokenize_code(fixed_line, is_c=is_c))

            draw.text((tm_x0 + 35, tm_y0 + 65), ok_cmd, fill=MUTED_TEXT, font=FONT_TERM)
            draw.text((tm_x0 + 35, tm_y0 + 115), ok_msg, fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 165), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)

        elif t < 35.0:
            # Act 6: LEAPED OUT OF CHAIR! Jumping with YAAAYYY!
            draw_stickman_actor(draw, action="yaay_celebrate", t=t)
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(16, 45, 28), outline=SUCCESS_GREEN, width=2)
            draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokenize_code(code_lines_raw[0], is_c=is_c))
            if len(code_lines_raw) > 1:
                draw.text((ed_x0 + 35, ed_y0 + 130), "2", fill=MUTED_TEXT, font=FONT_CODE)
                render_code_tokens(draw, ed_x0 + 90, ed_y0 + 130, tokenize_code(code_lines_raw[1], is_c=is_c))
            draw.text((ed_x0 + 35, ed_y0 + 185), "3", fill=MUTED_TEXT, font=FONT_CODE)
            fixed_line = f"print({fixed_token})" if not is_c else f"char grade = {fixed_token};"
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 185, tokenize_code(fixed_line, is_c=is_c))

            draw.text((tm_x0 + 35, tm_y0 + 65), ok_msg, fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 115), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)

        else:
            # Act 7: Thumbs Up & Clean Multi-Line Takeaway Box (ZERO OVERFLOW!)
            draw_stickman_actor(draw, action="thumbs_up", t=t)
            draw.rounded_rectangle([ed_x0 + 20, ed_y0 + 185, ed_x1 - 20, ed_y0 + 245], radius=8, fill=(16, 45, 28), outline=SUCCESS_GREEN, width=2)
            draw.text((ed_x0 + 35, ed_y0 + 75), "1", fill=MUTED_TEXT, font=FONT_CODE)
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 75, tokenize_code(code_lines_raw[0], is_c=is_c))
            if len(code_lines_raw) > 1:
                draw.text((ed_x0 + 35, ed_y0 + 130), "2", fill=MUTED_TEXT, font=FONT_CODE)
                render_code_tokens(draw, ed_x0 + 90, ed_y0 + 130, tokenize_code(code_lines_raw[1], is_c=is_c))
            draw.text((ed_x0 + 35, ed_y0 + 185), "3", fill=MUTED_TEXT, font=FONT_CODE)
            fixed_line = f"print({fixed_token})" if not is_c else f"char grade = {fixed_token};"
            render_code_tokens(draw, ed_x0 + 90, ed_y0 + 185, tokenize_code(fixed_line, is_c=is_c))

            draw.text((tm_x0 + 35, tm_y0 + 65), ok_msg, fill=SUCCESS_GREEN, font=FONT_TERM_BOLD)
            draw.text((tm_x0 + 35, tm_y0 + 115), "[Program finished with exit code 0]", fill=MUTED_TEXT, font=FONT_TERM)

            # Takeaway Box safely inside bounds
            box_y0, box_y1 = 1240, 1380
            draw.rounded_rectangle([ed_x0, box_y0, ed_x1, box_y1], radius=16, fill=(28, 22, 10), outline=(250, 204, 21), width=3)
            draw.text((ed_x0 + 30, box_y0 + 16), "⭐ KEY TAKEAWAY:", fill=(250, 204, 21), font=FONT_ALERT)
            draw.text((ed_x0 + 30, box_y0 + 56), takeaway_l1, fill=WHITE_VAR, font=FONT_CODE_BOLD)
            draw.text((ed_x0 + 30, box_y0 + 94), takeaway_l2, fill=GREEN_STRING, font=FONT_CODE)

        # Bottom Subscribe Badge
        draw.rounded_rectangle([320, 1780, 760, 1850], radius=35, fill=(220, 38, 38))
        draw.text((375, 1798), "▶ SUBSCRIBE FOR MORE!", fill=(255, 255, 255), font=FONT_ALERT)

        im.save(ep_frames_dir / f"f_{frame_idx:05d}.png")
        if frame_idx % 200 == 0:
            print(f"  Frame {frame_idx}/{TOTAL_FRAMES} rendered ({t:.1f}s / {TOTAL_SECONDS}s)")

    # 2. Save high-impact thumbnail
    thumb_frame = Image.open(ep_frames_dir / f"f_{int(32.0 * FPS):05d}.png")
    thumb_frame.save(final_thumb, quality=95)
    print(f"📸 Thumbnail saved: {final_thumb}")

    # 3. Audio Mix with SFX
    sfx_pop = SFX_DIR / "pop.wav"
    sfx_keyboard = SFX_DIR / "keyboard.wav"
    sfx_buzzer = SFX_DIR / "buzzer.wav"
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
        "-i", str(ep_frames_dir / "f_%05d.png"),
        "-i", str(sfx_ambient),
        "-i", str(sfx_footsteps),
        "-i", str(sfx_pop),
        "-i", str(sfx_keyboard),
        "-i", str(sfx_buzzer),
        "-i", str(sfx_ding),
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(TOTAL_SECONDS),
        str(final_video)
    ]

    subprocess.run(cmd, check=True)
    shutil.rmtree(ep_frames_dir, ignore_errors=True)
    print(f"🎉 Final Master Educational Video saved: {final_video}")
    return str(final_video)
