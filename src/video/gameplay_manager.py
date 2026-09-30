"""Gameplay Footage Manager and Procedural Video Generator.

Manages background gameplay clips (Minecraft parkour, Subway Surfers, etc.)
with random offset slicing to ensure visual diversity across uploads.
Includes a procedural visual fallback generator for headless/dry-run environments.
"""

from __future__ import annotations

import logging
import random
import subprocess
from pathlib import Path
from typing import List, Optional

from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)


class GameplayManager:
    """Selects, slices, and prepares background footage for video composition."""

    def __init__(self, gameplay_dir: Optional[Path] = None, output_dir: Optional[Path] = None) -> None:
        """Initialize gameplay manager.

        Args:
            gameplay_dir: Path to directory holding raw gameplay footage (.mp4, .mkv).
            output_dir: Path where sliced segments will be cached.
        """
        if gameplay_dir is None:
            from src.config import GAMEPLAY_DIR
            self.gameplay_dir = GAMEPLAY_DIR
        else:
            self.gameplay_dir = Path(gameplay_dir)

        if output_dir is None:
            from src.config import TEMP_OUTPUT_DIR
            self.output_dir = TEMP_OUTPUT_DIR
        else:
            self.output_dir = Path(output_dir)

        self.gameplay_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_background(
        self,
        duration_seconds: float,
        is_shorts: bool = False,
        output_filename: str = "bg_prepared",
    ) -> Path:
        """Prepare a background video of the exact required duration.

        Args:
            duration_seconds: Target length of narration audio.
            is_shorts: If True, crops/formats for 1080x1920 (9:16) portrait.
            output_filename: Name of the rendered background file.

        Returns:
            Path to the prepared background video.
        """
        out_path = self.output_dir / f"{output_filename}.mp4"

        # Check for gameplay clips in assets/gameplay
        available_clips: List[Path] = [
            f for f in self.gameplay_dir.glob("*.mp4") if f.stat().st_size > 500_000
        ]
        for ext in ("*.mkv", "*.mov", "*.webm"):
            available_clips.extend(self.gameplay_dir.glob(ext))

        if not available_clips:
            try:
                from src.video.gameplay_downloader import GameplayDownloader
                downloader = GameplayDownloader(target_dir=self.gameplay_dir)
                available_clips = downloader.ensure_gameplay_clips(min_clips=1)
            except Exception as e:
                logger.warning(f"Could not auto-download gameplay ({e}); proceeding to procedural visualizer.")

        if available_clips:
            source_clip = random.choice(available_clips)
            logger.info(f"Selected gameplay background clip: '{source_clip.name}'")
            return self._slice_and_scale_clip(source_clip, duration_seconds, is_shorts, out_path)

        # Procedural fallback video generator if offline and no clips exist
        logger.info("No gameplay footage found; generating procedural visual background...")
        return self._generate_procedural_background(duration_seconds, is_shorts, out_path)

    def _slice_and_scale_clip(
        self,
        clip_path: Path,
        duration_sec: float,
        is_shorts: bool,
        out_path: Path,
    ) -> Path:
        """Slice a random offset from a video and scale/crop to target resolution."""
        # Random start offset between 0 and 20 seconds
        start_offset = random.randint(0, 20)

        if is_shorts:
            # Crop 16:9 to 9:16 portrait and scale to exactly 1080x1920
            filter_chain = "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920,setsar=1"
        else:
            # 16:9 1080p landscape
            filter_chain = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1"

        cmd = [
            get_ffmpeg_cmd(),
            "-y",
            "-ss", str(start_offset),
            "-stream_loop", "2",
            "-i", str(clip_path),
            "-t", str(duration_sec + 1.0),
            "-vf", filter_chain,
            "-an",  # strip original audio
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(out_path),
        ]

        logger.info(f"Rendering sliced background via FFmpeg...")
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return out_path
        except Exception as e:
            logger.warning(f"Gameplay clip slice failed ({e}); falling back to procedural background.")
            return self._generate_procedural_background(duration_sec, is_shorts, out_path)

    def _generate_procedural_background(
        self,
        duration_sec: float,
        is_shorts: bool,
        out_path: Path,
    ) -> Path:
        """Synthesize an animated gradient background using FFmpeg filters."""
        res_x = 1080 if is_shorts else 1920
        res_y = 1920 if is_shorts else 1080

        # Create a dynamic moving geometric plasma / gradient effect
        filter_expr = (
            f"testsrc2=size={res_x}x{res_y}:rate=30,"
            f"boxblur=20:5,"
            f"hue=H='2*PI*t/15':s=1.2,"
            f"eq=contrast=1.3:brightness=-0.15"
        )

        cmd = [
            get_ffmpeg_cmd(),
            "-y",
            "-f", "lavfi",
            "-i", filter_expr,
            "-t", str(duration_sec + 1.0),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "26",
            "-pix_fmt", "yuv420p",
            str(out_path),
        ]

        logger.info(f"Generating procedural background ({res_x}x{res_y}, {duration_sec:.1f}s)...")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return out_path
