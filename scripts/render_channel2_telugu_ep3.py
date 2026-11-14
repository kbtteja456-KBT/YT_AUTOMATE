"""High-Quality Educational Animation Studio (Channel 2 Telugu Edition - Episode 3).
Concept: Lesson 3 - Taking User Input & Type Casting (input(), int(), str())
Language: Conversational Telugu / Tenglish (Articulate teacher / sir delivery)
Voice Provider: Kenpath Labs Svara TTS (Vamsi: sv_2fqanvcj)
Channel: @bhanuteja-n8x
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
TEMP_DIR = STORAGE / "temp" / "ch2_telugu_ep3"
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
TOTAL_SECONDS = 39.34
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Color Palette
BG_DARK = (10, 12, 16)
STICK_YELLOW = (255, 215, 0)
STICK_OUTLINE = (235, 195, 0)
CYAN_ACCENT = (56, 189, 248)
EMERALD_GREEN = (34, 197, 94)
GOLD_VAL = (250, 204, 21)
PURPLE_STR = (192, 132, 252)
RED_CRASH = (239, 68, 68)
WHITE = (255, 255, 255)
MUTED_GRAY = (148, 163, 184)
PANEL_BG = (18, 22, 30)
PANEL_BORDER = (40, 48, 65)
LAPTOP_SILVER = (190, 200, 215)
DESK_COLOR = (28, 34, 46)


def get_font(family: str, size: int):
    candidates = []
    if family == "mono":
        candidates = ["consola.ttf", "consolab.ttf", "cour.ttf", "courbd.ttf", "LiberationMono-Bold.ttf"]
    elif family == "bold":
        candidates = ["segoepb.ttf", "arialbd.ttf", "calibrib.ttf", "tahomabd.ttf", "LiberationSans-Bold.ttf"]
    else:
        candidates = ["segoeui.ttf", "arial.ttf", "calibri.ttf", "tahoma.ttf", "LiberationSans-Regular.ttf"]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


font_header = get_font("bold", 44)
font_sub = get_font("bold", 28)
font_code = get_font("mono", 40)
font_term = get_font("mono", 40)
font_box_label = get_font("bold", 36)
font_box_val = get_font("mono", 44)
font_callout = get_font("bold", 34)


def draw_stickman(draw: ImageDraw.ImageDraw, x: float, y: float, action: str = "idle", param: float = 0.0, face: str = "smile", scale: float = 1.75):
    lw = max(6, int(8 * scale))
    r_head = int(28 * scale)
    h_torso = int(68 * scale)
    l_arm = int(52 * scale)
    l_thigh = int(55 * scale)
    l_calf = int(52 * scale)

    head_x = x
    head_y = y - h_torso - r_head
    torso_top = (x, y - h_torso)
    torso_bot = (x, y)

    draw.ellipse([head_x - r_head, head_y - r_head, head_x + r_head, head_y + r_head], fill=STICK_YELLOW, outline=STICK_OUTLINE, width=3)

    ew, eh = 4, 6
    if face == "blink":
        draw.line([(head_x - 14, head_y), (head_x - 4, head_y)], fill=(20, 20, 20), width=3)
        draw.line([(head_x + 4, head_y), (head_x + 14, head_y)], fill=(20, 20, 20), width=3)
    elif face == "happy":
        draw.arc([head_x - 16, head_y - 6, head_x - 2, head_y + 8], 180, 360, fill=(20, 20, 20), width=3)
        draw.arc([head_x + 2, head_y - 6, head_x + 16, head_y + 8], 180, 360, fill=(20, 20, 20), width=3)
        draw.arc([head_x - 10, head_y + 6, head_x + 10, head_y + 20], 0, 180, fill=(20, 20, 20), width=3)
    elif face == "curious":
        draw.ellipse([head_x - 14, head_y - 6, head_x - 4, head_y + 6], fill=(20, 20, 20))
        draw.ellipse([head_x + 4, head_y - 10, head_x + 16, head_y + 6], fill=(20, 20, 20))
        draw.arc([head_x - 6, head_y + 8, head_x + 8, head_y + 18], 0, 180, fill=(20, 20, 20), width=2)
    else:  # smile
        draw.ellipse([head_x - 12 - ew, head_y - eh, head_x - 12 + ew, head_y + eh], fill=(20, 20, 20))
        draw.ellipse([head_x + 12 - ew, head_y - eh, head_x + 12 + ew, head_y + eh], fill=(20, 20, 20))
        draw.arc([head_x - 8, head_y + 6, head_x + 8, head_y + 18], 0, 180, fill=(20, 20, 20), width=3)

    draw.line([torso_top, torso_bot], fill=STICK_YELLOW, width=lw)

    if action == "walk":
        cycle = param * math.pi * 4
        a1, a2 = math.sin(cycle) * 35, -math.sin(cycle) * 35
        draw.line([torso_top, (x + a1, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + a1, y - h_torso * 0.4), (x + a1 * 1.3, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + a2, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + a2, y - h_torso * 0.4), (x + a2 * 1.3, y - 5)], fill=STICK_YELLOW, width=lw)
        l1, l2 = math.sin(cycle) * 45, -math.sin(cycle) * 45
        draw.line([torso_bot, (x + l1, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + l1, y + l_thigh), (x + l1 * 1.2, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + l2, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + l2, y + l_thigh), (x + l2 * 1.2, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    elif action == "typing_at_laptop":
        t_off = math.sin(param * 18) * 4
        draw.line([torso_top, (x - 35, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 35, y - h_torso * 0.5), (x - 70, y - h_torso * 0.3 + t_off)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x - 20, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 20, y - h_torso * 0.4), (x - 55, y - h_torso * 0.2 - t_off)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 45, y + 25)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 45, y + 25), (x - 50, y + 105)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 25, y + 35)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y + 35), (x - 30, y + 115)], fill=STICK_YELLOW, width=lw)

    elif action == "point_right":
        draw.line([torso_top, (x - 25, y - h_torso * 0.5)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y - h_torso * 0.5), (x - 25, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + 50, y - h_torso * 0.8)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 50, y - h_torso * 0.8), (x + 110, y - h_torso * 0.9)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 15, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 15, y + l_thigh), (x - 15, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + 20, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 20, y + l_thigh), (x + 20, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    elif action == "thumbs_up":
        draw.line([torso_top, (x - 35, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 35, y - h_torso * 0.4), (x - 45, y - h_torso * 0.9)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 45, y - h_torso * 0.9), (x - 45, y - h_torso * 1.1)], fill=STICK_YELLOW, width=lw + 2)
        draw.line([torso_top, (x + 35, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 35, y - h_torso * 0.4), (x + 45, y - h_torso * 0.9)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 45, y - h_torso * 0.9), (x + 45, y - h_torso * 1.1)], fill=STICK_YELLOW, width=lw + 2)
        draw.line([torso_bot, (x - 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 25, y + l_thigh), (x - 30, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + 25, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 25, y + l_thigh), (x + 30, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)

    else:
        sway = math.sin(param * 3) * 6
        draw.line([torso_top, (x - 28 + sway * 0.5, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 28 + sway * 0.5, y - h_torso * 0.4), (x - 28, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_top, (x + 28 - sway * 0.5, y - h_torso * 0.4)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 28 - sway * 0.5, y - h_torso * 0.4), (x + 28, y - 5)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x - 18, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x - 18, y + l_thigh), (x - 18, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)
        draw.line([torso_bot, (x + 18, y + l_thigh)], fill=STICK_YELLOW, width=lw)
        draw.line([(x + 18, y + l_thigh), (x + 18, y + l_thigh + l_calf)], fill=STICK_YELLOW, width=lw)


def draw_desk_and_laptop(draw: ImageDraw.ImageDraw, x: float, y: float, laptop_open: float = 1.0):
    draw.rounded_rectangle([x - 20, y, x + 240, y + 22], radius=6, fill=DESK_COLOR, outline=(45, 55, 75), width=2)
    draw.rectangle([x + 10, y + 22, x + 26, y + 195], fill=(20, 25, 35))
    draw.rectangle([x + 194, y + 22, x + 210, y + 195], fill=(20, 25, 35))

    lb_x0, lb_y0 = x + 35, y - 10
    lb_x1, lb_y1 = x + 185, y
    draw.rounded_rectangle([lb_x0, lb_y0, lb_x1, lb_y1], radius=3, fill=LAPTOP_SILVER)

    if laptop_open > 0.15:
        ls_h = int(95 * laptop_open)
        ls_y = lb_y0 - ls_h
        if ls_y < lb_y0 - 10:
            draw.rounded_rectangle([lb_x0 + 4, ls_y, lb_x1 - 4, lb_y0], radius=4, fill=(35, 42, 54), outline=LAPTOP_SILVER, width=2)
            draw.rectangle([lb_x0 + 10, ls_y + 6, lb_x1 - 10, lb_y0 - 4], fill=BG_DARK)
            draw.rectangle([lb_x0 + 16, ls_y + 14, lb_x0 + 55, ls_y + 18], fill=CYAN_ACCENT)
            draw.rectangle([lb_x0 + 16, ls_y + 24, lb_x0 + 75, ls_y + 28], fill=STICK_YELLOW)


def draw_floating_code_editor(draw: ImageDraw.ImageDraw, code_lines: list, highlight_mask: list):
    x0, y0 = 60, 205
    x1, y1 = WIDTH - 60, 580
    draw.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=PANEL_BG, outline=PANEL_BORDER, width=2)

    draw.ellipse([x0 + 25, y0 + 20, x0 + 41, y0 + 36], fill=(239, 68, 68))
    draw.ellipse([x0 + 50, y0 + 20, x0 + 66, y0 + 36], fill=(245, 158, 11))
    draw.ellipse([x0 + 75, y0 + 20, x0 + 91, y0 + 36], fill=(34, 197, 94))
    draw.text((x0 + 120, y0 + 18), "lesson3_input.py — Python 3.12", fill=MUTED_GRAY, font=font_sub)
    draw.line([(x0, y0 + 54), (x1, y0 + 54)], fill=PANEL_BORDER, width=1)

    cy = y0 + 76
    for idx, (code_text, is_hl) in enumerate(zip(code_lines, highlight_mask)):
        draw.text((x0 + 25, cy), f"{idx + 1:2d}", fill=(75, 90, 115), font=font_code)
        if is_hl:
            draw.rounded_rectangle([x0 + 95, cy - 6, x1 - 30, cy + 48], radius=8, fill=(38, 52, 75))
        if "#" in code_text:
            parts = code_text.split("#")
            draw.text((x0 + 110, cy), parts[0], fill=WHITE, font=font_code)
            w_code = draw.textlength(parts[0], font=font_code)
            draw.text((x0 + 110 + w_code, cy), "#" + parts[1], fill=(110, 130, 160), font=font_code)
        elif "input" in code_text:
            draw.text((x0 + 110, cy), code_text, fill=CYAN_ACCENT, font=font_code)
        elif "int(" in code_text:
            draw.text((x0 + 110, cy), code_text, fill=EMERALD_GREEN, font=font_code)
        else:
            draw.text((x0 + 110, cy), code_text, fill=WHITE, font=font_code)
        cy += 58


def draw_terminal_output(draw: ImageDraw.ImageDraw, output_lines: list):
    x0, y0 = 60, 610
    x1, y1 = WIDTH - 60, 770
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(14, 18, 24), outline=PANEL_BORDER, width=2)
    draw.text((x0 + 30, y0 + 28), "Terminal Output", fill=MUTED_GRAY, font=get_font("bold", 24), anchor="lm")
    draw.line([(x0, y0 + 46), (x1, y0 + 46)], fill=(30, 38, 50), width=1)
    cy = y0 + 72
    for l in output_lines:
        draw.text((x0 + 30, cy), ">>> ", fill=(100, 115, 140), font=font_term)
        col = RED_CRASH if "TypeError" in l else EMERALD_GREEN
        draw.text((x0 + 130, cy), l, fill=col, font=font_term)
        cy += 48


def draw_callout_banner(draw: ImageDraw.ImageDraw, step_text: str, explanation: str):
    by = 1620
    draw.rounded_rectangle([50, by, WIDTH - 50, by + 230], radius=22, fill=PANEL_BG, outline=CYAN_ACCENT, width=3)
    draw.rounded_rectangle([80, by + 20, 520, by + 75], radius=12, fill=(30, 48, 75))
    draw.text((95, by + 47), step_text, fill=GOLD_VAL, font=font_sub, anchor="lm")
    draw.text((80, by + 115), explanation[:46], fill=WHITE, font=font_callout)
    if len(explanation) > 46:
        draw.text((80, by + 165), explanation[46:95], fill=MUTED_GRAY, font=font_sub)


# -------------------------------------------------------------
# MAIN RENDER FUNCTION
# -------------------------------------------------------------
def render_channel2_telugu_ep3():
    print(f"\n==================================================================")
    print(f"🎬 RENDERING CHANNEL 2 TELUGU EPISODE 3: USER INPUT & TYPE CASTING")
    print(f"Total Duration: {TOTAL_SECONDS:.2f}s | FPS: {FPS} | Total Frames: {TOTAL_FRAMES}")
    print(f"Voice: Kenpath Labs Svara (Vamsi - Pace 0.88)")
    print(f"==================================================================")

    desk_x, desk_y = 100, 1380
    narration_audio = STORAGE / "temp" / "telugu_ep3_narration.mp3"

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Blueprint grid
        for gy in range(0, HEIGHT, 100):
            draw.line([(0, gy), (WIDTH, gy)], fill=(16, 20, 28), width=1)
        for gx in range(0, WIDTH, 100):
            draw.line([(gx, 0), (gx, HEIGHT)], fill=(16, 20, 28), width=1)

        draw.line([(0, 1580), (WIDTH, 1580)], fill=(35, 45, 60), width=4)

        # Header Pill
        draw.rounded_rectangle([60, 45, WIDTH - 60, 175], radius=20, fill=PANEL_BG, outline=PANEL_BORDER, width=2)
        draw.text((WIDTH // 2, 85), "PYTHON IN TELUGU • LESSON 3", fill=STICK_YELLOW, font=font_header, anchor="mm")
        draw.text((WIDTH // 2, 135), "Taking User Input with input() & int() Type Casting", fill=WHITE, font=font_sub, anchor="mm")

        # --- BEAT 1: 0.0s - 6.5s (Intro to input()) ---
        if t < 6.5:
            lines = ["# Taking User Input", "age_str = input('Enter age: ')", "# Always returns string!", "age = int(age_str)", "print(age + 1)"]
            draw_floating_code_editor(draw, lines, [False, False, False, False, False])
            draw_terminal_output(draw, ["Python 3.12 Input Engine Loaded"])
            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=min(1.0, t / 4.0))

            walk_p = min(1.0, t / 4.0)
            sx = 250 + walk_p * 180
            draw_stickman(draw, sx, 1540, action="walk", param=t, face="smile")
            draw_callout_banner(draw, "STAGE 1: input() FUNCTION", "యూజర్ నుండి ఇన్ పుట్ ఎలా తీసుకోవాలో నేర్చుకుందాం!")

        # --- BEAT 2: 6.5s - 14.0s (The String Trap) ---
        elif t < 14.0:
            lines = ["age_str = input('Enter age: ') # User types: 20", "# Memory: age_str = '20' (TEXT!)", "next_year = age_str + 1", "print(next_year)"]
            draw_floating_code_editor(draw, lines, [True, True, False, False])
            draw_terminal_output(draw, ["Enter age: 20", "Stored as STRING: '20'"])

            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_stickman(draw, 450, 1540, action="point_right", param=t, face="curious")
            draw_callout_banner(draw, "CAUTION: STRING TRAP", "input() ఎల్లప్పుడూ టెక్స్ట్ ని STRING గా మాత్రమే ఇస్తుంది!")

        # --- BEAT 3: 14.0s - 22.0s (The TypeError Crash) ---
        elif t < 22.0:
            lines = ["age_str = '20'", "# CRASH: '20' + 1 ❌", "TypeError: can only concatenate", "str (not int) to str"]
            draw_floating_code_editor(draw, lines, [False, True, True, True])
            draw_terminal_output(draw, ["TypeError: can't add int to str! ❌"])

            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_stickman(draw, 450, 1540, action="point_right", param=t, face="blink")
            draw_callout_banner(draw, "THE ERROR", "టెక్స్ట్ '20' కి + 1 కలిపితే పైథాన్ ఎర్రర్ ఇస్తుంది!")

        # --- BEAT 4: 22.0s - 30.0s (int() Type Casting) ---
        elif t < 30.0:
            lines = ["age_str = input('Age: ')  # '20'", "age_num = int(age_str)   # 20 (NUMBER!)", "print(age_num + 1)      # 21 ✅"]
            draw_floating_code_editor(draw, lines, [False, True, True])
            draw_terminal_output(draw, ["Converting '20' -> 20", "Calculation Result: 21 ✅"])

            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_stickman(draw, 450, 1540, action="typing_at_laptop", param=t, face="happy")
            draw_callout_banner(draw, "SOLUTION: int() TYPE CASTING", "int() వాడి టెక్స్ట్ ని అసలైన సంఖ్య గా మార్చాలి!")

        # --- BEAT 5: 30.0s - 34.5s (Key Takeaway) ---
        elif t < 34.5:
            lines = ["# Rule for Math with Input:", "num = int(input('Enter: '))", "print('Result:', num * 2)"]
            draw_floating_code_editor(draw, lines, [True, True, True])
            draw_terminal_output(draw, ["Math with input works perfectly!"])

            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_stickman(draw, 450, 1540, action="thumbs_up", face="smile")
            draw_callout_banner(draw, "GOLDEN RULE", "గణితం చేయాలంటే input() చుట్టూ int() వాడాలి!")

        # --- BEAT 6: 34.5s - 39.34s (Outro Teaser) ---
        else:
            lines = ["# Rule for Math with Input:", "num = int(input('Enter: '))", "print('Result:', num * 2)"]
            draw_floating_code_editor(draw, lines, [False, False, False])
            draw_terminal_output(draw, ["Lesson 3 Complete!"])

            draw_desk_and_laptop(draw, desk_x, desk_y, laptop_open=1.0)
            draw_stickman(draw, 520, 1540, action="thumbs_up", face="happy")

            # Teaser Banner
            draw.rounded_rectangle([60, 1450, WIDTH - 60, 1565], radius=18, fill=STICK_YELLOW)
            draw.text((WIDTH // 2, 1507), "FOLLOW FOR LESSON 4: PYTHON OPERATORS! 🚀", fill=(20, 20, 20), font=get_font("bold", 34), anchor="mm")
            draw_callout_banner(draw, "LESSON 3 COMPLETE!", "రేపటి లెసన్ 4 లో Python Operators నేర్చుకుందాం, సబ్స్క్రైబ్ చేయండి!")

        frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
        img.save(frame_path, format="PNG")

        if frame % 150 == 0:
            print(f"  Frame {frame}/{TOTAL_FRAMES} rendered ({t:.1f}s / {TOTAL_SECONDS:.1f}s)")

    print(f"✅ All {TOTAL_FRAMES} frames successfully rendered for Episode 3!")

    final_video = RENDERED_DIR / "channel2_telugu_ep3.mp4"

    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-i", str(narration_audio),
        "-i", str(SFX_DIR / "whoosh.wav"),
        "-i", str(SFX_DIR / "pop.wav"),
        "-i", str(SFX_DIR / "zap.wav"),
        "-i", str(SFX_DIR / "keyboard.wav"),
        "-i", str(SFX_DIR / "success_ding.wav"),
        "-i", str(SFX_DIR / "chime.wav"),
        "-t", str(TOTAL_SECONDS),
        "-filter_complex",
        (
            "[0:v]fps=30,format=yuv420p[v];"
            "[1:a]volume=1.0[narr];"
            "[2:a]adelay=1500|1500,volume=0.35[s_open];"
            "[3:a]adelay=6500|6500,volume=0.4[s_pop];"
            "[4:a]adelay=14000|14000,volume=0.35[s_zap];"
            "[5:a]adelay=22000|22000,volume=0.3[s_key];"
            "[6:a]adelay=30000|30000,volume=0.5[s_ding];"
            "[7:a]adelay=34500|34500,volume=0.4[s_chime];"
            "[narr][s_open][s_pop][s_zap][s_key][s_ding][s_chime]amix=inputs=7:duration=first:dropout_transition=0[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]

    print(f"\nEncoding final Channel 2 Telugu Ep 3 video with FFmpeg...")
    subprocess.run(cmd, check=True)
    print(f"🎉 Final Channel 2 Telugu Ep 3 saved to: {final_video}")

    # Generate Thumbnail
    thumb_path = THUMBNAILS_DIR / "channel2_telugu_ep3.jpg"
    thumb_frame_path = FRAMES_DIR / f"frame_{int(28.0 * FPS):04d}.png"
    if thumb_frame_path.exists():
        thumb_img = Image.open(thumb_frame_path).convert("RGB")
        thumb_img.save(thumb_path, "JPEG", quality=95)
        print(f"📸 Thumbnail saved to: {thumb_path}")


if __name__ == "__main__":
    render_channel2_telugu_ep3()

