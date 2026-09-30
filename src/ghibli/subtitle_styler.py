"""Subtitle Styler for Ghibli Nostalgic Videos.

Generates elegant Advanced SubStation Alpha (.ass) subtitles featuring soft warm pastel
typography, subtle dark borders, and clean word pacing suited for Ghibli aesthetic.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from src.config import OUTPUT_DIR
from src.ghibli.story_director import GhibliScene

logger = logging.getLogger(__name__)

GHIBLI_SUBS_DIR = OUTPUT_DIR / "ghibli" / "subtitles"


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp format: H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


class GhibliSubtitleStyler:
    """Creates warm, artistic ASS subtitles matching Studio Ghibli tone."""

    def __init__(self, subs_dir: Optional[Path] = None) -> None:
        self.subs_dir = subs_dir or GHIBLI_SUBS_DIR
        self.subs_dir.mkdir(parents=True, exist_ok=True)

    def generate_subtitles(
        self,
        scenes: List[GhibliScene],
        output_name: str,
        is_shorts: bool = True,
    ) -> Path:
        """Generate ASS subtitle file for the story scenes.

        Args:
            scenes: List of GhibliScene objects with timing and text.
            output_name: Base name for output file.
            is_shorts: Whether the format is vertical 9:16 or horizontal 16:9.

        Returns:
            Path to the saved .ass file.
        """
        output_file = self.subs_dir / f"{output_name}.ass"
        res_x, res_y = (720, 1280) if is_shorts else (1280, 720)
        font_size = 28 if is_shorts else 24
        margin_v = 140 if is_shorts else 60

        # Soft warm cream text color (&H00E8F8FF in BGR format: White-Cream), soft dark outline (&H00101825)
        ass_header = f"""[Script Info]
Title: Ghibli Nostalgic Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: GhibliWarm,Arial,{font_size},&H00D0FFFF,&H000000FF,&H00181515,&H80000000,-1,0,0,0,100,100,1,0,1,2.5,1.5,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        current_time = 0.5  # slight delay before first subtitle

        for scene in scenes:
            start_str = format_ass_time(current_time)
            end_time = current_time + max(scene.duration_seconds - 0.4, 2.0)
            end_str = format_ass_time(end_time)

            clean_text = scene.narration_chunk.replace("\n", " ").strip()
            # If text is too long, break into 2 lines for readability
            if len(clean_text) > 45 and " " in clean_text:
                mid = len(clean_text) // 2
                split_idx = clean_text.find(" ", mid)
                if split_idx != -1:
                    clean_text = clean_text[:split_idx] + "\\N" + clean_text[split_idx + 1 :]

            events.append(f"Dialogue: 0,{start_str},{end_str},GhibliWarm,,0,0,0,,{clean_text}")
            current_time += scene.duration_seconds

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(ass_header)
            f.write("\n".join(events))
            f.write("\n")

        logger.info(f"Generated Ghibli styled subtitles: {output_file.name}")
        return output_file
