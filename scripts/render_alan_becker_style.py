"""Alan Becker 'Animation vs. Coding' Style Python Visual Series Renderer.

Episode 1: How Variables & Memory Work in Python
- 100% Pure Visual Animation (No voiceover needed, universal appeal)
- Orange Stick Figure Mascot interacting with code and physical memory boxes
- Animated variable containers, glowing data orbs, fusion effects, pointer wires
- Synchronized Sound Effects (Thud, Whoosh, Pop, Keyboard, Zap, Laser, Chime)
- Bouncy retro background music
- 1080x1920 (9:16 Shorts standard) at 30 FPS
"""

import os
import sys
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

sys.path.insert(0, os.getcwd())
from backend.app.core.ffmpeg_utils import get_ffmpeg_binary

FFMPEG = get_ffmpeg_binary()
WORKSPACE_DIR = Path(os.getcwd())
STORAGE = WORKSPACE_DIR / "media_storage"
TEMP_DIR = STORAGE / "temp" / "alan_becker_ep1"
FRAMES_DIR = TEMP_DIR / "frames"
RENDERED_DIR = STORAGE / "rendered"
SFX_DIR = STORAGE / "assets" / "sfx"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
RENDERED_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_SECONDS = 18.0
TOTAL_FRAMES = int(FPS * TOTAL_SECONDS)

# Colors
ORANGE = (255, 130, 0)         # Alan Becker style stickman
CYAN = (56, 189, 248)          # Memory box border / glow
GOLD = (250, 204, 21)          # Number orbs
EMERALD = (34, 197, 94)        # Success green
PURPLE = (168, 85, 247)        # Accent
BG_SLATE = (15, 23, 42)        # Modern dark IDE background
PANEL_BG = (30, 41, 59)
TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)

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

font_title = get_font("bold", 54)
font_sub = get_font("bold", 34)
font_code = get_font("mono", 40)
font_box_label = get_font("bold", 44)
font_orb_val = get_font("bold", 48)
font_console = get_font("mono", 36)
font_badge = get_font("bold", 30)

# -------------------------------------------------------------
# CHARACTER DRAWING FUNCTION (STICK FIGURE)
# -------------------------------------------------------------
def draw_stick_figure(draw: ImageDraw.ImageDraw, x: float, y: float, pose: str = "idle", scale: float = 1.0, color = ORANGE):
    """Draws an expressive stick figure with limbs, head, and active pose."""
    head_r = int(26 * scale)
    torso_len = int(80 * scale)
    arm_len = int(55 * scale)
    leg_len = int(70 * scale)
    lw = max(4, int(7 * scale))

    # Base coordinates
    head_cx = int(x)
    head_cy = int(y - torso_len - head_r)
    neck = (int(x), int(y - torso_len))
    hips = (int(x), int(y))

    # 1. Poses
    if pose == "idle":
        l_arm = (int(x - arm_len * 0.7), int(y - torso_len * 0.6))
        r_arm = (int(x + arm_len * 0.7), int(y - torso_len * 0.6))
        l_foot = (int(x - leg_len * 0.4), int(y + leg_len))
        r_foot = (int(x + leg_len * 0.4), int(y + leg_len))

    elif pose == "pointing_up":
        l_arm = (int(x - arm_len * 0.4), int(y - torso_len * 0.4))
        r_arm = (int(x + arm_len * 0.6), int(y - torso_len - head_r * 2))  # Pointing straight up!
        l_foot = (int(x - leg_len * 0.3), int(y + leg_len))
        r_foot = (int(x + leg_len * 0.5), int(y + leg_len))

    elif pose == "carry_up":
        # Holding orb with both hands raised
        l_arm = (int(x - arm_len * 0.7), int(y - torso_len - head_r * 1.5))
        r_arm = (int(x + arm_len * 0.7), int(y - torso_len - head_r * 1.5))
        l_foot = (int(x - leg_len * 0.5), int(y + leg_len))
        r_foot = (int(x + leg_len * 0.5), int(y + leg_len))

    elif pose == "jumping":
        # Mid-air tuck
        hips = (int(x), int(y - 25))
        l_arm = (int(x - arm_len * 0.9), int(y - torso_len * 1.1))
        r_arm = (int(x + arm_len * 0.9), int(y - torso_len * 1.1))
        l_foot = (int(x - leg_len * 0.6), int(y + leg_len * 0.4))
        r_foot = (int(x + leg_len * 0.6), int(y + leg_len * 0.4))

    elif pose == "crouch":
        torso_len = int(torso_len * 0.7)
        neck = (int(x), int(y - torso_len))
        head_cy = int(y - torso_len - head_r)
        l_arm = (int(x - arm_len * 0.8), int(y - torso_len * 0.3))
        r_arm = (int(x + arm_len * 0.8), int(y - torso_len * 0.3))
        l_foot = (int(x - leg_len * 0.7), int(y + leg_len * 0.7))
        r_foot = (int(x + leg_len * 0.7), int(y + leg_len * 0.7))

    elif pose == "tada":
        # Arms in high V victory!
        l_arm = (int(x - arm_len * 1.1), int(y - torso_len - head_r * 1.6))
        r_arm = (int(x + arm_len * 1.1), int(y - torso_len - head_r * 1.6))
        l_foot = (int(x - leg_len * 0.6), int(y + leg_len))
        r_foot = (int(x + leg_len * 0.6), int(y + leg_len))
    else:
        l_arm = (int(x - arm_len * 0.7), int(y - torso_len * 0.5))
        r_arm = (int(x + arm_len * 0.7), int(y - torso_len * 0.5))
        l_foot = (int(x - leg_len * 0.4), int(y + leg_len))
        r_foot = (int(x + leg_len * 0.4), int(y + leg_len))

    # Draw body parts
    # Head
    draw.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r], outline=color, fill=color, width=lw)
    # Torso
    draw.line([neck, hips], fill=color, width=lw)
    # Arms
    draw.line([neck, l_arm], fill=color, width=lw)
    draw.line([neck, r_arm], fill=color, width=lw)
    # Legs
    draw.line([hips, l_foot], fill=color, width=lw)
    draw.line([hips, r_foot], fill=color, width=lw)

# -------------------------------------------------------------
# DRAW MEMORY BOX & VALUE ORB
# -------------------------------------------------------------
def draw_memory_box(draw: ImageDraw.ImageDraw, x: int, y: int, name: str, orb_val: str = "", active: bool = False):
    w, h = 260, 240
    border_col = EMERALD if active else CYAN
    bg_col = (20, 30, 48)

    # Box outline
    draw.rounded_rectangle([x, y, x + w, y + h], radius=24, fill=bg_col, outline=border_col, width=4)
    # Name plate at top
    draw.rounded_rectangle([x + 30, y - 22, x + w - 30, y + 26], radius=14, fill=border_col)
    draw.text((x + w // 2, y + 2), f"var: {name}", fill=BG_SLATE, font=font_box_label, anchor="mm")

    # Inside orb
    if orb_val:
        draw_glowing_orb(draw, x + w // 2, y + h // 2 + 10, orb_val, radius=55, color=GOLD if not active else EMERALD)

def draw_glowing_orb(draw: ImageDraw.ImageDraw, cx: int, cy: int, text: str, radius: int = 55, color = GOLD):
    # Outer glow
    draw.ellipse([cx - radius - 10, cy - radius - 10, cx + radius + 10, cy + radius + 10], outline=(color[0], color[1], color[2], 80), width=4)
    # Solid body
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color, outline=TEXT_WHITE, width=3)
    # Number text
    draw.text((cx, cy + 2), str(text), fill=BG_SLATE, font=font_orb_val, anchor="mm")

# -------------------------------------------------------------
# DRAW TERMINAL & CODE
# -------------------------------------------------------------
def draw_code_terminal(draw: ImageDraw.ImageDraw, code_lines: list, active_idx: int = -1, typing_progress: float = 1.0):
    tx, ty, tw, th = 70, 220, WIDTH - 140, 420
    draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=24, fill=(10, 15, 26), outline=(71, 85, 105), width=3)

    # Window bar
    draw.ellipse([tx + 25, ty + 20, tx + 45, ty + 40], fill=(239, 68, 68))
    draw.ellipse([tx + 55, ty + 20, tx + 75, ty + 40], fill=(234, 179, 8))
    draw.ellipse([tx + 85, ty + 20, tx + 105, ty + 40], fill=(34, 197, 94))
    draw.text((tx + 140, ty + 16), "script.py — Visual Python", fill=TEXT_MUTED, font=font_sub)

    # Lines
    y_line = ty + 85
    for i, line in enumerate(code_lines):
        line_num = f"{i + 1:2d} |"
        draw.text((tx + 30, y_line), line_num, fill=(100, 116, 139), font=font_code)

        # Highlight background if active
        if i == active_idx:
            draw.rounded_rectangle([tx + 95, y_line - 4, tx + tw - 25, y_line + 46], radius=10, fill=(30, 58, 138, 180), outline=CYAN, width=2)

        # Draw code
        col = GOLD if "def" in line or "print" in line else CYAN if "=" in line else TEXT_WHITE
        # Typing effect on active line
        display_line = line
        if i == active_idx and typing_progress < 1.0:
            chars_to_show = int(len(line) * typing_progress)
            display_line = line[:chars_to_show] + "█"

        draw.text((tx + 115, y_line), display_line, fill=col, font=font_code)
        y_line += 58

# -------------------------------------------------------------
# MAIN FRAME GENERATION LOOP
# -------------------------------------------------------------
def generate_all_frames():
    print(f"Generating {TOTAL_FRAMES} frames ({TOTAL_SECONDS}s at {FPS} FPS)...")
    
    # Ground floor level
    floor_y = 1550

    code_history = [
        "x = 5",
        "x = x + 3",
        "y = x",
        "print(x, y)"
    ]

    for frame in range(TOTAL_FRAMES):
        t = frame / FPS
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_SLATE)
        draw = ImageDraw.Draw(img)

        # Subtle cyber grid on background
        for gy in range(0, HEIGHT, 80):
            draw.line([(0, gy), (WIDTH, gy)], fill=(20, 30, 48), width=1)
        for gx in range(0, WIDTH, 80):
            draw.line([(gx, 0), (gx, HEIGHT)], fill=(20, 30, 48), width=1)

        # Ground line
        draw.line([(0, floor_y), (WIDTH, floor_y)], fill=(71, 85, 105), width=4)

        # Top Header Banner
        draw.rounded_rectangle([70, 70, WIDTH - 70, 180], radius=24, fill=(30, 41, 59), outline=CYAN, width=3)
        draw.text((WIDTH // 2, 105), "PYTHON VISUAL SERIES • EP 1", fill=GOLD, font=font_title, anchor="mm")
        draw.text((WIDTH // 2, 150), "How Variables & Memory Actually Work!", fill=TEXT_WHITE, font=font_sub, anchor="mm")

        # -------------------------------------------------------------
        # TIMELINE STAGES (18 SECONDS)
        # -------------------------------------------------------------
        
        # --- PHASE 1: 0.0s - 2.5s (Stickman Drops from Sky & Discovers Code) ---
        if t < 2.5:
            # Code box shows line 1
            draw_code_terminal(draw, [code_history[0]], active_idx=0, typing_progress=min(1.0, t / 1.0))
            
            # Stickman drops down
            if t < 1.0:
                drop_t = t / 1.0
                stick_y = int(-100 + (floor_y - 120 + 100) * (drop_t ** 2))
                pose = "falling"
            elif t < 1.3:
                stick_y = floor_y - 120
                pose = "crouch"  # Squash on landing!
            elif t < 2.0:
                stick_y = floor_y - 120
                pose = "pointing_up"  # Looks up at x = 5
            else:
                stick_y = floor_y - 120
                pose = "idle"

            draw_stick_figure(draw, 540, stick_y, pose=pose, scale=1.4)

        # --- PHASE 2: 2.5s - 6.5s (Variable Box Drops + Value 5 Pops in) ---
        elif t < 6.5:
            rel_t = t - 2.5
            draw_code_terminal(draw, [code_history[0]], active_idx=0)

            # Box X drops from terminal down to floor
            if rel_t < 1.0:
                box_y = int(600 + (floor_y - 250 - 600) * (rel_t / 1.0))
                box_val = ""
                stick_pose = "pointing_up"
            elif rel_t < 2.2:
                # 5 Orb flies out of code into box
                box_y = floor_y - 250
                orb_t = (rel_t - 1.0) / 1.2
                orb_x = int(500)
                orb_y = int(350 + (box_y + 120 - 350) * orb_t)
                draw_glowing_orb(draw, orb_x, orb_y, "5", radius=50)
                box_val = ""
                stick_pose = "carry_up" if rel_t < 1.6 else "idle"
            else:
                # 5 inside Box X
                box_y = floor_y - 250
                box_val = "5"
                stick_pose = "idle"

            draw_memory_box(draw, 380, box_y, "x", orb_val=box_val, active=(rel_t >= 2.2))
            draw_stick_figure(draw, 220, floor_y - 120, pose=stick_pose, scale=1.4)

            # Explanatory badge
            if rel_t >= 2.0:
                draw.rounded_rectangle([150, 1100, WIDTH - 150, 1200], radius=24, fill=(30, 41, 59), outline=CYAN, width=3)
                draw.text((WIDTH // 2, 1150), "x stores a reference to value 5 in memory!", fill=TEXT_WHITE, font=font_sub, anchor="mm")

        # --- PHASE 3: 6.5s - 11.5s (Updating: x = x + 3 -> 5 + 3 fuse into 8) ---
        elif t < 11.5:
            rel_t = t - 6.5
            draw_code_terminal(draw, [code_history[0], code_history[1]], active_idx=1, typing_progress=min(1.0, rel_t / 0.8))

            box_y = floor_y - 250
            if rel_t < 1.5:
                # Stickman jumps up and pulls 5 out of box
                draw_memory_box(draw, 380, box_y, "x", orb_val="")
                draw_glowing_orb(draw, 450, int(box_y - 80), "5", radius=50)
                draw_stick_figure(draw, 350, floor_y - 120, pose="carry_up", scale=1.4)
            elif rel_t < 3.2:
                # + 3 orb flies in from the right and fuses with 5!
                fuse_t = (rel_t - 1.5) / 1.7
                orb5_x = 420
                orb3_x = int(850 - 380 * fuse_t)
                orb_y = box_y - 120
                draw_memory_box(draw, 380, box_y, "x", orb_val="")

                if fuse_t < 0.85:
                    draw_glowing_orb(draw, orb5_x, orb_y, "5", radius=50, color=GOLD)
                    draw_glowing_orb(draw, orb3_x, orb_y, "+3", radius=50, color=PURPLE)
                else:
                    # Fusion sparkle explosion!
                    draw_glowing_orb(draw, 460, orb_y, "8", radius=65, color=EMERALD)

                draw_stick_figure(draw, 250, floor_y - 120, pose="pointing_up", scale=1.4)
            else:
                # 8 drops back into box x!
                draw_memory_box(draw, 380, box_y, "x", orb_val="8", active=True)
                draw_stick_figure(draw, 250, floor_y - 120, pose="tada", scale=1.4)

            # Explanatory badge
            draw.rounded_rectangle([120, 1100, WIDTH - 120, 1200], radius=24, fill=(30, 41, 59), outline=EMERALD, width=3)
            draw.text((WIDTH // 2, 1150), "Old value replaced: x now holds 8!", fill=EMERALD, font=font_sub, anchor="mm")

        # --- PHASE 4: 11.5s - 15.0s (Two Variables: y = x, Pointer Wire Connects) ---
        elif t < 15.0:
            rel_t = t - 11.5
            draw_code_terminal(draw, [code_history[0], code_history[1], code_history[2]], active_idx=2)

            box_y = floor_y - 250
            # Draw Box x on left (380) and Box y on right (680)
            draw_memory_box(draw, 200, box_y, "x", orb_val="8", active=True)
            draw_memory_box(draw, 620, box_y, "y", orb_val="8", active=True)

            # Glowing Pointer Laser between y and the value 8
            wire_start = (620, box_y + 120)
            wire_end = (460, box_y + 120)
            draw.line([wire_start, wire_end], fill=CYAN, width=6)
            # Energy pulse on wire
            pulse_x = int(wire_start[0] - (wire_start[0] - wire_end[0]) * ((rel_t * 2) % 1.0))
            draw.ellipse([pulse_x - 12, wire_start[1] - 12, pulse_x + 12, wire_start[1] + 12], fill=TEXT_WHITE)

            draw_stick_figure(draw, 540, floor_y - 120, pose="pointing_up", scale=1.4)

            # Explanatory badge
            draw.rounded_rectangle([100, 1100, WIDTH - 100, 1220], radius=24, fill=(30, 41, 59), outline=CYAN, width=3)
            draw.text((WIDTH // 2, 1145), "⚡ Memory Secret: y does NOT copy 8!", fill=GOLD, font=font_sub, anchor="mm")
            draw.text((WIDTH // 2, 1185), "Both x and y point to the SAME object!", fill=TEXT_WHITE, font=font_sub, anchor="mm")

        # --- PHASE 5: 15.0s - 18.0s (Print & Celebration Outro) ---
        else:
            rel_t = t - 15.0
            draw_code_terminal(draw, code_history, active_idx=3)

            box_y = floor_y - 250
            draw_memory_box(draw, 200, box_y, "x", orb_val="8", active=True)
            draw_memory_box(draw, 620, box_y, "y", orb_val="8", active=True)

            # Console Output Box at bottom
            draw.rounded_rectangle([120, 1080, WIDTH - 120, 1220], radius=24, fill=(0, 0, 0), outline=EMERALD, width=4)
            draw.text((WIDTH // 2, 1130), "TERMINAL OUTPUT:", fill=TEXT_MUTED, font=font_badge, anchor="mm")
            draw.text((WIDTH // 2, 1175), ">>> 8   8", fill=EMERALD, font=font_title, anchor="mm")

            # Celebrating Jump!
            jump_h = int(abs(math.sin(rel_t * 6)) * 60)
            draw_stick_figure(draw, 540, floor_y - 120 - jump_h, pose="jumping" if jump_h > 15 else "tada", scale=1.4)

            # End Card call to action
            draw.rounded_rectangle([100, 1300, WIDTH - 100, 1420], radius=24, fill=(220, 38, 38), outline=TEXT_WHITE, width=3)
            draw.text((WIDTH // 2, 1345), "FOLLOW FOR EPISODE 2 🚀", fill=TEXT_WHITE, font=font_title, anchor="mm")
            draw.text((WIDTH // 2, 1390), "Next: 'How If-Else Gates Work in Memory!'", fill=GOLD, font=font_sub, anchor="mm")

        # Save frame
        frame_path = FRAMES_DIR / f"frame_{frame:04d}.png"
        img.save(frame_path)

        if frame % 60 == 0:
            print(f"  Rendered {frame}/{TOTAL_FRAMES} frames ({frame/TOTAL_FRAMES*100:.0f}%)...")

    print("  ✅ All frames generated successfully!")

# -------------------------------------------------------------
# STEP 4: ASSEMBLE WITH FFMPEG (With Synchronized Alan Becker SFX + Music)
# -------------------------------------------------------------
def assemble_video():
    print("\nCompositing 18s 60FPS video with synchronized sound design...")
    final_video = RENDERED_DIR / "trial_alan_becker_python_ep1.mp4"
    bg_music = WORKSPACE_DIR / "media_storage" / "audio" / "bg_music.mp3"

    # Synchronized sound triggers:
    # 0.8s: thud (stickman landing)
    # 2.5s: whoosh (box dropping)
    # 3.5s: pop (5 entering box)
    # 6.5s: keyboard (typing x = x + 3)
    # 8.0s: zap (5 and 3 fusion)
    # 9.8s: pop (8 entering box)
    # 11.5s: laser (pointer wire connecting)
    # 15.0s: chime (celebration output)

    cmd = [
        FFMPEG, "-y",
        # Frame input
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        # Audio inputs
        "-i", str(bg_music),
        "-i", str(SFX_DIR / "thud.wav"),
        "-i", str(SFX_DIR / "whoosh.wav"),
        "-i", str(SFX_DIR / "pop.wav"),
        "-i", str(SFX_DIR / "keyboard.wav"),
        "-i", str(SFX_DIR / "zap.wav"),
        "-i", str(SFX_DIR / "laser.wav"),
        "-i", str(SFX_DIR / "chime.wav"),
        "-t", str(TOTAL_SECONDS),
        "-filter_complex",
        (
            # Music at moderate volume
            "[1:a]volume=0.35[bg];"
            # SFX triggers with adelay
            "[2:a]adelay=800|800,volume=1.0[s_thud];"
            "[3:a]adelay=2500|2500,volume=0.9[s_whoosh];"
            "[4:a]adelay=3500|3500,volume=1.0[s_pop1];"
            "[5:a]adelay=6500|6500,volume=0.8[s_kb];"
            "[6:a]adelay=8000|8000,volume=1.0[s_zap];"
            "[4:a]adelay=9800|9800,volume=1.0[s_pop2];"
            "[7:a]adelay=11500|11500,volume=0.9[s_laser];"
            "[8:a]adelay=15000|15000,volume=1.2[s_chime];"
            # Mix all 9 sound tracks
            "[bg][s_thud][s_whoosh][s_pop1][s_kb][s_zap][s_pop2][s_laser][s_chime]amix=inputs=9:duration=first:dropout_transition=0[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(final_video)
    ]

    print("Rendering final MP4...")
    subprocess.run(cmd, check=True)
    mb = final_video.stat().st_size / (1024 * 1024)
    print(f"\n🎉 ALAN BECKER STYLE PYTHON ANIMATION RENDER COMPLETE!")
    print(f"Path: {final_video}")
    print(f"Size: {mb:.2f} MB | Duration: {TOTAL_SECONDS}s | FPS: {FPS}")

if __name__ == "__main__":
    generate_all_frames()
    assemble_video()

