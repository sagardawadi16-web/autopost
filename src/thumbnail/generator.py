"""Automated High-CTR YouTube Thumbnail Generator using Pillow.

Creates cinematic, viral 1280x720 thumbnails with dynamic high-contrast typography,
atmospheric color gradients, category warning badges, and drop shadows.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from src.config import FONTS_DIR, THUMBNAILS_OUTPUT_DIR
from src.evolution.learning_memory import StrategicLearningMemory

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """Generates viral, click-optimized 1280x720 YouTube thumbnails."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        fonts_dir: Optional[Path] = None,
        memory: Optional[StrategicLearningMemory] = None,
    ) -> None:
        """Initialize thumbnail generator.

        Args:
            output_dir: Directory where generated thumbnails will be saved.
            fonts_dir: Directory containing TrueType fonts.
            memory: Instance of StrategicLearningMemory for thumbnail styling directives.
        """
        self.output_dir = output_dir or THUMBNAILS_OUTPUT_DIR
        self.fonts_dir = fonts_dir or FONTS_DIR
        self.memory = memory or StrategicLearningMemory()

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fonts_dir.mkdir(parents=True, exist_ok=True)

    def generate_thumbnail(
        self,
        headline_text: str,
        category: str = "horror",
        output_filename: str = "thumbnail",
        badge_text: Optional[str] = None,
    ) -> Path:
        """Create a complete 1280x720 thumbnail with typography and badge overlays.

        Args:
            headline_text: Shock headline (2-4 punchy words, e.g. 'DON'T LOOK OUTSIDE').
            category: Story category ('horror', 'drama', 'revenge', etc.).
            output_filename: Base name of the output image file.
            badge_text: Optional callout badge text (e.g. 'DON'T WATCH ALONE').

        Returns:
            Path to the generated JPEG thumbnail.
        """
        width, height = 1280, 720
        directives = self.memory.get_thumbnail_directives(category)
        if badge_text is None:
            badge_text = directives.get("badge_text", "TRUE STORY")

        # 1. Create base background canvas with atmospheric gradient
        canvas = self._create_gradient_background(width, height, category)

        draw = ImageDraw.Draw(canvas)
        font = self._load_font(size=96)
        badge_font = self._load_font(size=36)

        # 2. Draw Top Category Warning Badge
        self._draw_warning_badge(draw, badge_text, badge_font, width)

        # 3. Format and draw bold headline text with thick outline and drop shadow
        clean_headline = headline_text.strip().upper()
        words = clean_headline.split()
        if len(words) > 4:
            clean_headline = " ".join(words[:4])

        # Break into 1 or 2 lines
        lines = self._wrap_text_to_lines(clean_headline, max_chars_per_line=16)

        text_y_start = height // 2 - (len(lines) * 55)
        for i, line in enumerate(lines):
            line_y = text_y_start + (i * 115)
            # Alternate colors: Top line bright yellow, second line pure white
            text_color = (255, 220, 0) if i == 0 else (255, 255, 255)
            self._draw_text_with_outline(
                draw=draw,
                text=line,
                position=(width // 2, line_y),
                font=font,
                text_color=text_color,
                outline_color=(0, 0, 0),
                outline_width=8,
                shadow_offset=(6, 6),
            )

        # 4. Save optimized JPEG (under 2MB per YouTube requirements)
        out_path = self.output_dir / f"{output_filename}.jpg"
        canvas.save(out_path, format="JPEG", quality=92, optimize=True)
        logger.info(f"Generated thumbnail: '{out_path.name}' ({width}x{height})")
        return out_path

    def _create_gradient_background(self, width: int, height: int, category: str) -> Image.Image:
        """Create a procedural atmospheric gradient canvas."""
        base = Image.new("RGB", (width, height), (0, 0, 0))

        if category == "horror":
            c1 = (45, 5, 5)     # Deep dark crimson
            c2 = (10, 0, 15)    # Midnight void
        elif category == "revenge":
            c1 = (10, 20, 45)   # Navy blue
            c2 = (40, 10, 0)    # Ember copper
        elif category == "drama":
            c1 = (30, 5, 45)    # Dark royal purple
            c2 = (5, 5, 20)     # Void blue
        else:
            c1 = (20, 20, 25)
            c2 = (5, 5, 8)

        draw = ImageDraw.Draw(base)
        for y in range(height):
            ratio = y / height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Add vignette
        vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        v_draw = ImageDraw.Draw(vignette)
        v_draw.ellipse(
            [(-width * 0.2, -height * 0.2), (width * 1.2, height * 1.2)],
            fill=(0, 0, 0, 0),
            outline=(0, 0, 0, 180),
            width=int(height * 0.35),
        )
        vignette = vignette.filter(ImageFilter.GaussianBlur(30))
        base.paste(vignette, (0, 0), vignette)

        return base

    def _draw_warning_badge(
        self,
        draw: ImageDraw.ImageDraw,
        badge_text: str,
        font: ImageFont.ImageFont,
        canvas_width: int,
    ) -> None:
        """Draw an attention-grabbing warning badge at the top of the thumbnail."""
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        pad_x, pad_y = 28, 12
        badge_w = text_w + (pad_x * 2)
        badge_h = text_h + (pad_y * 2)

        badge_x = (canvas_width - badge_w) // 2
        badge_y = 45

        # Draw red pill badge
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=10,
            fill=(220, 20, 20),
            outline=(255, 255, 255),
            width=3,
        )

        draw.text(
            (badge_x + pad_x, badge_y + pad_y - 2),
            badge_text,
            fill=(255, 255, 255),
            font=font,
        )

    def _draw_text_with_outline(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.ImageFont,
        text_color: Tuple[int, int, int],
        outline_color: Tuple[int, int, int],
        outline_width: int = 6,
        shadow_offset: Tuple[int, int] = (6, 6),
    ) -> None:
        """Draw bold text with drop shadow and multi-directional stroke outline."""
        x, y = position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        centered_x = x - (text_w // 2)
        centered_y = y - (text_h // 2)

        # Drop shadow
        sx, sy = shadow_offset
        draw.text((centered_x + sx, centered_y + sy), text, fill=(0, 0, 0), font=font)

        # Thick outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx * dx + dy * dy <= outline_width * outline_width:
                    draw.text((centered_x + dx, centered_y + dy), text, fill=outline_color, font=font)

        # Main text fill
        draw.text((centered_x, centered_y), text, fill=text_color, font=font)

    def _wrap_text_to_lines(self, text: str, max_chars_per_line: int = 16) -> List[str]:
        """Wrap short headline into 1 or 2 visual lines."""
        words = text.split()
        if len(words) <= 2:
            return [text]

        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        return [line1, line2]

    def _load_font(self, size: int) -> ImageFont.ImageFont:
        """Load a bold TrueType font or fallback to system default."""
        # Try custom font in assets/fonts/
        for font_file in self.fonts_dir.glob("*.ttf"):
            try:
                return ImageFont.truetype(str(font_file), size)
            except Exception:
                pass

        # Try common Windows fonts
        for win_font in ["impact.ttf", "arialbd.ttf", "segoeprb.ttf"]:
            try:
                return ImageFont.truetype(win_font, size)
            except Exception:
                pass

        return ImageFont.load_default()
