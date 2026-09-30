"""Master Video Assembler for Landscape Long-Form Videos (1920x1080).

Combines sliced gameplay video, multi-character narration, ambient background soundtrack,
and burned-in karaoke subtitles into a broadcast-ready MP4.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from src.config import VIDEO_OUTPUT_DIR, VIDEO_SETTINGS
from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)


class VideoAssembler:
    """Renders finalized landscape YouTube videos using FFmpeg."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize video assembler.

        Args:
            output_dir: Destination directory for rendered videos.
        """
        self.output_dir = output_dir or VIDEO_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assemble_longform(
        self,
        background_video: Path,
        soundtrack_audio: Path,
        subtitles_ass: Path,
        output_filename: str,
        duration_seconds: float,
    ) -> Path:
        """Assemble full long-form video with burned-in subtitles.

        Args:
            background_video: Prepared background gameplay video.
            soundtrack_audio: Mixed audio track (speech + background music).
            subtitles_ass: Styled ASS subtitle file.
            output_filename: Name of the resulting MP4 (without extension).
            duration_seconds: Total duration of narration audio.

        Returns:
            Path to the completed MP4 video.
        """
        output_mp4 = self.output_dir / f"{output_filename}.mp4"

        # Escape subtitle path for FFmpeg filter syntax
        clean_sub_path = str(subtitles_ass.resolve()).replace("\\", "/").replace(":", "\\:")

        # Build FFmpeg command
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
            "-t", str(duration_seconds),
            str(output_mp4),
        ]

        logger.info(f"Rendering long-form video '{output_mp4.name}' ({duration_seconds:.1f}s)...")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Video assembly complete: '{output_mp4.name}'")
            return output_mp4
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg video assembly failed: {e.stderr}")
            # If ASS filter fails (e.g. libass missing in some builds), render without subtitle burn-in
            fallback_cmd = [
                get_ffmpeg_cmd(),
                "-y",
                "-i", str(background_video),
                "-i", str(soundtrack_audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-t", str(duration_seconds),
                str(output_mp4),
            ]
            subprocess.run(fallback_cmd, capture_output=True, text=True, check=True)
            return output_mp4
