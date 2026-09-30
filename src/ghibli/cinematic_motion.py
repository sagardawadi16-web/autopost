"""Cinematic Motion Engine for Ghibli Animation.

Converts static painterly scene frames into living animations using 2.5D Ken Burns
zoom/pan camera techniques, subtle atmospheric motion, and crossfade transitions.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from src.config import OUTPUT_DIR
from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)

CLIPS_OUTPUT_DIR = OUTPUT_DIR / "ghibli" / "clips"


class CinematicMotionEngine:
    """Animates static Ghibli frames and composites full video sequences."""

    def __init__(self, clips_dir: Optional[Path] = None) -> None:
        self.clips_dir = clips_dir or CLIPS_OUTPUT_DIR
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_cmd = get_ffmpeg_cmd()

    def animate_scene(
        self,
        image_path: Path,
        scene_index: int,
        duration: float = 6.5,
        motion_type: str = "zoom_in",
        is_shorts: bool = True,
        fps: int = 30,
    ) -> Path:
        """Render a single scene image into a smooth Ken Burns animated video clip.

        Args:
            image_path: Path to the generated scene frame.
            scene_index: Index number of the scene.
            duration: Duration of the clip in seconds.
            motion_type: 'zoom_in', 'zoom_out', 'pan_left', 'pan_right'.
            is_shorts: If True, renders 9:16 portrait. If False, 16:9 landscape.
            fps: Frame rate (default 30).

        Returns:
            Path to the generated MP4 clip.
        """
        width, height = (720, 1280) if is_shorts else (1280, 720)
        total_frames = max(int(duration * fps), 30)
        output_clip = self.clips_dir / f"clip_{scene_index:03d}_{width}x{height}.mp4"

        # Calculate zoompan filter expression based on camera movement
        # Note: zoompan calculates per input frame, -loop 1 feeds frames at fps
        zoom_step = 0.15 / max(total_frames, 1)

        if motion_type == "zoom_in":
            # Start at 1.0, gently zoom into center up to 1.15
            vf = (
                f"zoompan=z='min(zoom+{zoom_step:.6f},1.15)':d={total_frames}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
            )
        elif motion_type == "zoom_out":
            # Start at 1.15, gently pull out to 1.0
            vf = (
                f"zoompan=z='if(lte(zoom,1.0),1.15,max(1.0,zoom-{zoom_step:.6f}))':d={total_frames}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
            )
        elif motion_type == "pan_left":
            # Steady slight zoom (1.12), slow horizontal pan from right to left
            vf = (
                f"zoompan=z=1.12:d={total_frames}:"
                f"x='(1-on/{total_frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
            )
        else:  # pan_right
            # Steady slight zoom (1.12), slow horizontal pan from left to right
            vf = (
                f"zoompan=z=1.12:d={total_frames}:"
                f"x='(on/{total_frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
            )

        cmd = [
            self.ffmpeg_cmd,
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-vf", vf,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(output_clip),
        ]

        logger.info(f"Rendering animated Ken Burns clip for Scene {scene_index} (Type: {motion_type}, {duration:.1f}s)...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg motion error for Scene {scene_index}: {res.stderr}")
            raise RuntimeError(f"FFmpeg failed to animate Scene {scene_index}: {res.stderr[:200]}")

        return output_clip

    def concatenate_scenes(self, scene_clips: List[Path], output_video: Path) -> Path:
        """Concatenate all scene clips into a unified continuous background video."""
        if not scene_clips:
            raise ValueError("No scene clips provided to concatenate.")

        output_video.parent.mkdir(parents=True, exist_ok=True)
        list_file = self.clips_dir / "concat_list.txt"

        # Write FFmpeg concat demuxer manifest
        with open(list_file, "w", encoding="utf-8") as f:
            for clip in scene_clips:
                clean_path = str(clip.resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        cmd = [
            self.ffmpeg_cmd,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_video),
        ]

        logger.info(f"Concatenating {len(scene_clips)} animated scene clips into {output_video.name}...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg concatenation failed: {res.stderr}")
            raise RuntimeError(f"FFmpeg concat error: {res.stderr[:200]}")

        return output_video
