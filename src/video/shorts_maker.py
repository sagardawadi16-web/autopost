"""YouTube Shorts Compositor (1080x1920 Vertical Format).

Assembles high-energy vertical videos under 59 seconds with bold centered
karaoke subtitles engineered for maximum retention on the Shorts shelf.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from src.config import VIDEO_OUTPUT_DIR, VIDEO_SETTINGS
from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)


class ShortsMaker:
    """Renders vertical 9:16 Shorts with strict duration compliance."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize Shorts maker.

        Args:
            output_dir: Destination directory for rendered Shorts.
        """
        self.output_dir = output_dir or VIDEO_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assemble_short(
        self,
        background_video: Path,
        soundtrack_audio: Path,
        subtitles_ass: Path,
        output_filename: str,
        duration_seconds: float,
    ) -> Path:
        """Assemble vertical YouTube Short.

        Args:
            background_video: Prepared 1080x1920 vertical background.
            soundtrack_audio: Mixed narration and ambient track.
            subtitles_ass: Styled ASS subtitle file.
            output_filename: Name of the resulting Short MP4.
            duration_seconds: Duration in seconds (capped at 58.0s).

        Returns:
            Path to the completed Short MP4.
        """
        # Hard cap at 58.0 seconds to ensure Shorts algorithm categorizes it properly
        effective_duration = min(duration_seconds, 58.0)
        output_mp4 = self.output_dir / f"{output_filename}_short.mp4"

        clean_sub_path = str(subtitles_ass.resolve()).replace("\\", "/").replace(":", "\\:")

        cmd = [
            get_ffmpeg_cmd(),
            "-y",
            "-i", str(background_video),
            "-i", str(soundtrack_audio),
            "-vf", f"ass='{clean_sub_path}'",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", VIDEO_SETTINGS.video_codec,
            "-preset", "faster",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", VIDEO_SETTINGS.audio_codec,
            "-b:a", VIDEO_SETTINGS.audio_bitrate,
            "-t", str(effective_duration),
            str(output_mp4),
        ]

        logger.info(f"Rendering YouTube Short '{output_mp4.name}' ({effective_duration:.1f}s)...")
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Short rendering complete: '{output_mp4.name}'")
            return output_mp4
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg Short assembly failed: {e.stderr}")
            # Fallback without subtitle filter if libass error occurs
            fallback_cmd = [
                get_ffmpeg_cmd(),
                "-y",
                "-i", str(background_video),
                "-i", str(soundtrack_audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-t", str(effective_duration),
                str(output_mp4),
            ]
            subprocess.run(fallback_cmd, capture_output=True, text=True, check=True)
            return output_mp4
