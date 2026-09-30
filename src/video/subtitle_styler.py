"""Karaoke Subtitle Generator in Advanced SubStation Alpha (.ass) format.

Transforms word boundary timing metadata into modern, high-engagement
word-by-word highlighted subtitles with customizable fonts, outlines, and positions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.audio.tts_engine import WordTiming

logger = logging.getLogger(__name__)


def ms_to_ass_time(ms: int) -> str:
    """Convert millisecond timestamp to ASS timecode format (H:MM:SS.cc)."""
    total_sec = ms / 1000.0
    hours = int(total_sec // 3600)
    minutes = int((total_sec % 3600) // 60)
    seconds = int(total_sec % 60)
    centiseconds = int((total_sec - int(total_sec)) * 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


class SubtitleStyler:
    """Generates styled ASS subtitle files with word-by-word karaoke highlighting."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize subtitle styler.

        Args:
            output_dir: Directory where .ass files will be stored.
        """
        if output_dir is None:
            from src.config import TEMP_OUTPUT_DIR
            self.output_dir = TEMP_OUTPUT_DIR
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_ass_subtitles(
        self,
        word_timings: List[WordTiming],
        output_filename: str,
        is_shorts: bool = False,
        words_per_card: int = 4,
    ) -> Path:
        """Create an ASS subtitle file from word timestamps.

        Args:
            word_timings: Ordered list of WordTiming objects.
            output_filename: Name of the generated file (without extension).
            is_shorts: If True, formats for 1080x1920 portrait Shorts.
            words_per_card: Number of words displayed simultaneously on screen.

        Returns:
            Path to the saved .ass subtitle file.
        """
        output_path = self.output_dir / f"{output_filename}.ass"

        # Dimensions & Styling
        res_x = 1080 if is_shorts else 1920
        res_y = 1920 if is_shorts else 1080
        font_size = 72 if is_shorts else 52
        vertical_margin = 850 if is_shorts else 110  # Centered for Shorts, bottom for landscape

        header = f"""[Script Info]
Title: AutoPost Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5,3,2,40,40,{vertical_margin},1
Style: Highlight,Impact,{font_size},&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,105,105,2,0,1,6,4,2,40,40,{vertical_margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events: List[str] = []

        # Group words into small visual cards (chunks of 3-5 words)
        chunks: List[List[WordTiming]] = []
        for i in range(0, len(word_timings), words_per_card):
            chunks.append(word_timings[i : i + words_per_card])

        for chunk in chunks:
            if not chunk:
                continue

            card_start_ms = chunk[0].start_time_ms
            card_end_ms = chunk[-1].end_time_ms

            # For each word in the chunk, generate a micro-event highlighting that active word
            for active_idx, active_word in enumerate(chunk):
                word_start_ms = active_word.start_time_ms
                # Highlight lasts until next word starts or card ends
                word_end_ms = (
                    chunk[active_idx + 1].start_time_ms
                    if active_idx + 1 < len(chunk)
                    else card_end_ms
                )

                if word_end_ms <= word_start_ms:
                    word_end_ms = word_start_ms + 150

                start_str = ms_to_ass_time(word_start_ms)
                end_str = ms_to_ass_time(word_end_ms)

                # Build line where active word has yellow color tag
                formatted_words = []
                for idx, w in enumerate(chunk):
                    clean_w = w.word.upper()
                    if idx == active_idx:
                        # Highlighted word: Yellow + slight zoom
                        formatted_words.append(f"{{\\c&H00FFFF&\\t(0,100,\\fscx108\\fscy108)}}{clean_w}{{\\r}}")
                    else:
                        # Regular white word
                        formatted_words.append(f"{{\\c&HFFFFFF&}}{clean_w}")

                card_text = " ".join(formatted_words)
                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{card_text}")

        full_ass_content = header + "\n".join(events) + "\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_ass_content)

        logger.info(f"Generated ASS subtitle file: '{output_path.name}' ({len(events)} events)")
        return output_path
