"""QuizCardRenderer generating hand-drawn 1080x1920 quiz and reveal cards using Pillow."""

import re
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from backend.app.core.logging import logger


class QuizCardRenderer:
    """Renders high-resolution (1080x1920) sketchy / hand-drawn aesthetic Python quiz cards."""

    WIDTH = 1080
    HEIGHT = 1920

    # Color Palette (Warm hand-drawn / pastel paper notebook theme)
    BG_COLOR = (248, 245, 237)          # Warm cream paper
    BG_INNER = (255, 253, 249)          # Slightly lighter inner card
    BORDER_COLOR = (45, 52, 54)         # Hand-drawn ink dark charcoal
    CODE_BG = (33, 37, 43)              # Dark slate code container
    CODE_BORDER = (75, 82, 99)          # Subtle code box outline
    TEXT_MAIN = (30, 30, 36)            # Dark ink text
    TEXT_MUTED = (108, 117, 125)        # Muted annotation text

    # Syntax Highlighting Colors
    SYN_KEYWORD = (255, 121, 198)       # Bright pink/orange
    SYN_BUILTIN = (189, 147, 249)       # Purple
    SYN_STRING = (80, 250, 123)         # Mint green
    SYN_NUMBER = (139, 233, 253)        # Cyan
    SYN_COMMENT = (98, 114, 164)        # Muted slate
    SYN_DEFAULT = (248, 248, 242)       # Light cream

    # Option Badges (Pastel Palette)
    OPTION_COLORS = [
        {"bg": (255, 235, 238), "badge": (239, 83, 80), "border": (229, 115, 115)},   # A: Coral
        {"bg": (227, 242, 253), "badge": (33, 150, 243), "border": (100, 181, 246)},   # B: Sky Blue
        {"bg": (254, 249, 231), "badge": (245, 158, 11), "border": (251, 191, 36)},   # C: Amber
        {"bg": (243, 232, 255), "badge": (147, 51, 234), "border": (192, 132, 252)},   # D: Purple
    ]

    # Reveal Highlight
    REVEAL_BG = (230, 249, 237)         # Emerald pastel
    REVEAL_BORDER = (46, 204, 113)      # Bold green
    REVEAL_BADGE = (39, 174, 96)

    @classmethod
    def _get_font(cls, family: str, size: int) -> ImageFont.ImageFont:
        """Load requested TrueType font from system with reliable fallbacks."""
        candidates = []
        if family == "mono":
            candidates = [
                "consola.ttf", "consolab.ttf", "cour.ttf", "courbd.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
            ]
        elif family == "bold":
            candidates = [
                "arialbd.ttf", "segoepb.ttf", "calibrib.ttf", "tahomabd.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ]
        else:
            candidates = [
                "arial.ttf", "segoeui.ttf", "calibri.ttf", "tahoma.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ]

        for cand in candidates:
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                continue

        return ImageFont.load_default()

    @classmethod
    def _draw_doodle_rect(
        cls,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        fill: Optional[tuple[int, int, int]] = None,
        outline: Optional[tuple[int, int, int]] = None,
        radius: int = 16,
        width: int = 3
    ) -> None:
        """Draw rounded rectangle with subtle hand-drawn character."""
        x1, y1, x2, y2 = box
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)
        # Subtle imperfect double outline on top/left for sketchy look
        if outline and width > 1:
            draw.rounded_rectangle([x1 - 1, y1 - 1, x2 + 1, y2 + 1], radius=radius, outline=outline, width=1)

    @classmethod
    def _draw_python_badge(cls, draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """Draw a stylized Python emblem."""
        # Blue top hook
        draw.rounded_rectangle([x, y, x + 36, y + 20], radius=8, fill=(55, 118, 171))
        draw.rectangle([x + 18, y + 10, x + 36, y + 36], fill=(55, 118, 171))
        draw.ellipse([x + 8, y + 6, x + 14, y + 12], fill=(255, 255, 255))

        # Yellow bottom hook
        draw.rounded_rectangle([x + 18, y + 24, x + 54, y + 44], radius=8, fill=(255, 212, 56))
        draw.rectangle([x + 18, y + 8, x + 36, y + 34], fill=(255, 212, 56))
        draw.ellipse([x + 40, y + 32, x + 46, y + 38], fill=(30, 30, 30))

    @classmethod
    def _tokenize_python_line(cls, line: str) -> list[tuple[str, tuple[int, int, int]]]:
        """Simple regex-based syntax tokenization for clean code display."""
        keywords = {
            "def", "class", "for", "in", "while", "if", "elif", "else", "return",
            "yield", "import", "from", "as", "try", "except", "finally", "with",
            "lambda", "pass", "break", "continue", "and", "or", "not", "is"
        }
        builtins = {"print", "len", "range", "list", "dict", "set", "str", "int", "bool", "True", "False", "None"}

        tokens = []
        pattern = re.compile(r'(\#[^\n]*|\"[^\"]*\"|\'[^\']*\'|\b\d+\b|\b\w+\b|[^\w\s]|\s+)')
        for part in pattern.findall(line):
            if part.startswith("#"):
                tokens.append((part, cls.SYN_COMMENT))
            elif (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
                tokens.append((part, cls.SYN_STRING))
            elif part.isdigit():
                tokens.append((part, cls.SYN_NUMBER))
            elif part in keywords:
                tokens.append((part, cls.SYN_KEYWORD))
            elif part in builtins:
                tokens.append((part, cls.SYN_BUILTIN))
            else:
                tokens.append((part, cls.SYN_DEFAULT))
        return tokens

    @classmethod
    def render_quiz_cards(
        cls,
        question_code: str,
        options: list[str],
        correct_option: str,
        explanation: str,
        output_dir: str,
        job_id: str
    ) -> tuple[str, str]:
        """Render both question card PNG and reveal card PNG at 1080x1920 resolution.

        Returns (question_card_path, reveal_card_path).
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        q_path = str(Path(output_dir) / f"quiz_question_{job_id}.png")
        r_path = str(Path(output_dir) / f"quiz_reveal_{job_id}.png")

        # Fonts
        font_headline = cls._get_font("bold", 54)
        font_sub = cls._get_font("regular", 36)
        font_code = cls._get_font("mono", 38)
        font_line_num = cls._get_font("mono", 34)
        font_option = cls._get_font("bold", 40)
        font_badge = cls._get_font("bold", 38)
        font_sticker = cls._get_font("bold", 32)
        font_expl = cls._get_font("bold", 34)

        # Normalize options to 4 items
        clean_opts = options[:4] if len(options) >= 4 else (options + ["N/A"] * 4)[:4]
        # Clean correct_option identifier (e.g. "B" or "B)" or full option text)
        corr_letter = correct_option.strip().upper()
        if len(corr_letter) > 1 and corr_letter[0] in "ABCD":
            corr_letter = corr_letter[0]

        # -------------------------------------------------------------
        # 1. RENDER QUESTION CARD
        # -------------------------------------------------------------
        img_q = Image.new("RGB", (cls.WIDTH, cls.HEIGHT), cls.BG_COLOR)
        draw_q = ImageDraw.Draw(img_q)

        # Draw outer decorative paper border
        cls._draw_doodle_rect(draw_q, (40, 60, cls.WIDTH - 40, cls.HEIGHT - 60), fill=cls.BG_INNER, outline=cls.BORDER_COLOR, radius=28, width=4)

        # Top Header: Python Badge + Headline
        cls._draw_python_badge(draw_q, 80, 115)
        draw_q.text((150, 110), "PYTHON QUIZ", fill=(55, 118, 171), font=font_sub)
        draw_q.text((80, 175), "What is the output of this code?", fill=cls.TEXT_MAIN, font=font_headline)

        # Hand-drawn scribble underline under headline
        draw_q.line([(80, 245), (750, 245)], fill=(245, 158, 11), width=5)
        draw_q.line([(90, 252), (680, 252)], fill=(251, 191, 36), width=3)

        # Center: Code Box
        code_top = 285
        code_height = 560
        cls._draw_doodle_rect(
            draw_q,
            (70, code_top, cls.WIDTH - 70, code_top + code_height),
            fill=cls.CODE_BG,
            outline=cls.CODE_BORDER,
            radius=24,
            width=3
        )

        # Code header bar (mini terminal dots)
        draw_q.ellipse([95, code_top + 20, 111, code_top + 36], fill=(255, 95, 86))
        draw_q.ellipse([120, code_top + 20, 136, code_top + 36], fill=(255, 189, 46))
        draw_q.ellipse([145, code_top + 20, 161, code_top + 36], fill=(39, 201, 63))
        draw_q.text((200, code_top + 16), "main.py", fill=(140, 145, 160), font=font_sub)

        # Code lines with line numbers & syntax highlights
        code_lines = [line.rstrip() for line in question_code.strip().splitlines()][:10]
        y_cursor = code_top + 80
        line_height = 46

        for i, line in enumerate(code_lines, start=1):
            # Line number
            draw_q.text((95, y_cursor), f"{i:2d} |", fill=cls.SYN_COMMENT, font=font_line_num)
            # Syntax token rendering
            x_cursor = 175
            tokens = cls._tokenize_python_line(line)
            for tok_text, tok_color in tokens:
                draw_q.text((x_cursor, y_cursor), tok_text, fill=tok_color, font=font_code)
                bbox = font_code.getbbox(tok_text)
                tok_w = bbox[2] - bbox[0] if bbox else len(tok_text) * 22
                x_cursor += tok_w
            y_cursor += line_height

        # "Think carefully!" doodle sticker banner
        sticker_box = (cls.WIDTH - 420, code_top + code_height + 25, cls.WIDTH - 70, code_top + code_height + 85)
        cls._draw_doodle_rect(draw_q, sticker_box, fill=(254, 240, 138), outline=cls.BORDER_COLOR, radius=18, width=3)
        draw_q.text((cls.WIDTH - 390, code_top + code_height + 37), "🤔 Think carefully!", fill=cls.TEXT_MAIN, font=font_sticker)

        # 4 Stacked Option Pill Rows
        options_start_y = code_top + code_height + 115
        opt_box_h = 135
        letters = ["A", "B", "C", "D"]

        for idx, opt_raw in enumerate(clean_opts):
            y_opt = options_start_y + idx * (opt_box_h + 24)
            pal = cls.OPTION_COLORS[idx % 4]

            # Pill Box
            cls._draw_doodle_rect(
                draw_q,
                (70, y_opt, cls.WIDTH - 70, y_opt + opt_box_h),
                fill=pal["bg"],
                outline=pal["border"],
                radius=32,
                width=3
            )

            # Circular Badge with Letter
            badge_cx = 140
            badge_cy = y_opt + opt_box_h // 2
            draw_q.ellipse([badge_cx - 36, badge_cy - 36, badge_cx + 36, badge_cy + 36], fill=pal["badge"])
            draw_q.text((badge_cx - 14, badge_cy - 24), letters[idx], fill=(255, 255, 255), font=font_badge)

            # Strip leading "A)" or "A:" if already embedded in option string
            opt_display = re.sub(r'^[A-Da-d][\)\:\.\s\-]+', '', opt_raw).strip()
            draw_q.text((210, y_opt + 42), opt_display, fill=cls.TEXT_MAIN, font=font_option)

        # Save question card
        img_q.save(q_path, "PNG")

        # -------------------------------------------------------------
        # 2. RENDER REVEAL CARD (Visually Distinct)
        # -------------------------------------------------------------
        img_r = Image.new("RGB", (cls.WIDTH, cls.HEIGHT), cls.BG_COLOR)
        draw_r = ImageDraw.Draw(img_r)

        # Outer border
        cls._draw_doodle_rect(draw_r, (40, 60, cls.WIDTH - 40, cls.HEIGHT - 60), fill=cls.BG_INNER, outline=cls.BORDER_COLOR, radius=28, width=4)

        # Top Header
        cls._draw_python_badge(draw_r, 80, 115)
        draw_r.text((150, 110), "PYTHON QUIZ — ANSWER", fill=(46, 204, 113), font=font_sub)
        draw_r.text((80, 175), f"Correct Answer: Option {corr_letter}!", fill=cls.TEXT_MAIN, font=font_headline)

        # Underline
        draw_r.line([(80, 245), (750, 245)], fill=(46, 204, 113), width=5)

        # Code Box (Identical for continuity)
        cls._draw_doodle_rect(
            draw_r,
            (70, code_top, cls.WIDTH - 70, code_top + code_height),
            fill=cls.CODE_BG,
            outline=cls.CODE_BORDER,
            radius=24,
            width=3
        )
        draw_r.ellipse([95, code_top + 20, 111, code_top + 36], fill=(255, 95, 86))
        draw_r.ellipse([120, code_top + 20, 136, code_top + 36], fill=(255, 189, 46))
        draw_r.ellipse([145, code_top + 20, 161, code_top + 36], fill=(39, 201, 63))
        draw_r.text((200, code_top + 16), "main.py", fill=(140, 145, 160), font=font_sub)

        y_cursor = code_top + 80
        for i, line in enumerate(code_lines, start=1):
            draw_r.text((95, y_cursor), f"{i:2d} |", fill=cls.SYN_COMMENT, font=font_line_num)
            x_cursor = 175
            tokens = cls._tokenize_python_line(line)
            for tok_text, tok_color in tokens:
                draw_r.text((x_cursor, y_cursor), tok_text, fill=tok_color, font=font_code)
                bbox = font_code.getbbox(tok_text)
                tok_w = bbox[2] - bbox[0] if bbox else len(tok_text) * 22
                x_cursor += tok_w
            y_cursor += line_height

        # Reveal banner sticker
        sticker_box_r = (cls.WIDTH - 440, code_top + code_height + 25, cls.WIDTH - 70, code_top + code_height + 85)
        cls._draw_doodle_rect(draw_r, sticker_box_r, fill=(220, 252, 231), outline=cls.REVEAL_BORDER, radius=18, width=3)
        draw_r.text((cls.WIDTH - 410, code_top + code_height + 37), f"✅ Verified: '{corr_letter}'", fill=(22, 101, 52), font=font_sticker)

        # 4 Options with Correct Option Prominently Highlighted
        for idx, opt_raw in enumerate(clean_opts):
            y_opt = options_start_y + idx * (opt_box_h + 24)
            is_correct = (letters[idx] == corr_letter)

            if is_correct:
                # Vibrant green highlight for winner
                fill_color = cls.REVEAL_BG
                border_color = cls.REVEAL_BORDER
                border_width = 5
                badge_fill = cls.REVEAL_BADGE
            else:
                # Slightly muted
                fill_color = (245, 245, 247)
                border_color = (209, 213, 219)
                border_width = 2
                badge_fill = (156, 163, 175)

            cls._draw_doodle_rect(
                draw_r,
                (70, y_opt, cls.WIDTH - 70, y_opt + opt_box_h),
                fill=fill_color,
                outline=border_color,
                radius=32,
                width=border_width
            )

            # Circular Badge
            badge_cx = 140
            badge_cy = y_opt + opt_box_h // 2
            draw_r.ellipse([badge_cx - 36, badge_cy - 36, badge_cx + 36, badge_cy + 36], fill=badge_fill)
            label = f"{letters[idx]} ✓" if is_correct else letters[idx]
            draw_r.text((badge_cx - 18, badge_cy - 24), label, fill=(255, 255, 255), font=font_badge)

            opt_display = re.sub(r'^[A-Da-d][\)\:\.\s\-]+', '', opt_raw).strip()
            draw_r.text((210, y_opt + 42), opt_display, fill=cls.TEXT_MAIN, font=font_option)

        # Bottom Explanation Strip (Reveal Card Only)
        expl_top = options_start_y + 4 * (opt_box_h + 24) + 10
        expl_h = cls.HEIGHT - 80 - expl_top
        if expl_h > 80:
            cls._draw_doodle_rect(
                draw_r,
                (70, expl_top, cls.WIDTH - 70, expl_top + expl_h),
                fill=(254, 249, 195),
                outline=(234, 179, 8),
                radius=20,
                width=3
            )
            draw_r.text((100, expl_top + 20), "💡 WHY THIS HAPPENS:", fill=(133, 77, 14), font=font_expl)
            # Wrap explanation text
            expl_line = explanation.strip()
            if len(expl_line) > 110:
                expl_line = expl_line[:107] + "..."
            draw_r.text((100, expl_top + 68), expl_line, fill=cls.TEXT_MAIN, font=font_sub)

        # Save reveal card
        img_r.save(r_path, "PNG")

        logger.info(f"[QuizCardRenderer] Successfully generated {q_path} and {r_path}")
        return q_path, r_path
