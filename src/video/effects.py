"""Video Effects, Stealth Processing, and Post-Processing.

Applies subtle visual color grading, contrast enhancement, and slight speed jitter
to prevent digital content-ID fingerprinting and maximize humanized presentation.
"""

from __future__ import annotations

import logging
import random
import subprocess
from pathlib import Path

from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)


class VideoEffects:
    """Applies stealth anti-detection and aesthetic grading filters to rendered video."""

    @staticmethod
    def apply_stealth_jitter(
        input_video: Path,
        output_video: Path,
        jitter_range: tuple[float, float] = (0.985, 1.015),
    ) -> Path:
        """Apply imperceptible speed jitter (±1.5%) to randomize video duration and signatures.

        Args:
            input_video: Source video path.
            output_video: Destination video path.
            jitter_range: Speed multiplier interval.

        Returns:
            Path to jittered video.
        """
        speed_factor = round(random.uniform(*jitter_range), 4)
        video_pts = round(1.0 / speed_factor, 4)
        audio_tempo = speed_factor

        cmd = [
            get_ffmpeg_cmd(),
            "-y",
            "-i", str(input_video),
            "-filter_complex",
            f"[0:v]setpts={video_pts}*PTS,eq=saturation=1.08:contrast=1.05[v];"
            f"[0:a]atempo={audio_tempo}[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "22",
            "-c:a", "aac",
            str(output_video),
        ]

        logger.info(f"Applying stealth jitter (speed={speed_factor}x) to '{input_video.name}'...")
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_video
        except subprocess.CalledProcessError as e:
            logger.warning(f"Stealth jitter failed ({e.stderr}); returning original video.")
            return input_video
