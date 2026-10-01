"""Hindi Visual Storyteller Engine.

Generates thematic, high-contrast visual backdrops with Ken Burns pan/zoom motion
for Hindi Shorts without burning in text subtitles.
Zero API cost, zero external quota limits, 100% turnkey offline execution.
"""

from __future__ import annotations

import logging
import math
import random
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFilter

from src.config import OUTPUT_DIR
from src.ghibli.cinematic_motion import CinematicMotionEngine
from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)

HINDI_VISUAL_DIR = OUTPUT_DIR / "hindi_visuals"


class HindiVisualEngine:
    """Generates visual storytelling slideshows with Ken Burns camera motion."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize Hindi visual engine."""
        self.output_dir = output_dir or HINDI_VISUAL_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.motion_engine = CinematicMotionEngine(clips_dir=self.output_dir / "clips")

    def generate_visual_background(
        self,
        duration_seconds: float,
        category: str = "drama",
        output_filename: str = "hindi_visual_bg",
        is_shorts: bool = True,
    ) -> Path:
        """Create a continuous Ken Burns animated visual sequence for narration.

        Args:
            duration_seconds: Total duration needed.
            category: Story genre/mood ('horror', 'revenge', 'drama', etc.).
            output_filename: Name of the output video.
            is_shorts: If True, renders 9:16 portrait.

        Returns:
            Path to the completed background MP4.
        """
        width, height = (720, 1280) if is_shorts else (1280, 720)
        output_video = self.output_dir / f"{output_filename}.mp4"

        # Determine number of scenes (each 5 to 7 seconds)
        scene_duration = 5.5
        num_scenes = max(3, math.ceil(duration_seconds / scene_duration))
        actual_scene_duration = duration_seconds / num_scenes

        logger.info(f"Generating {num_scenes} atmospheric frames for Hindi video ({category})...")
        scene_clips: List[Path] = []
        motions = ["zoom_in", "pan_left", "zoom_out", "pan_right"]

        for i in range(num_scenes):
            frame_path = self._generate_atmospheric_frame(
                scene_idx=i,
                width=width,
                height=height,
                category=category,
            )
            motion = motions[i % len(motions)]
            clip = self.motion_engine.animate_scene(
                image_path=frame_path,
                scene_index=i,
                duration=actual_scene_duration,
                motion_type=motion,
                is_shorts=is_shorts,
            )
            scene_clips.append(clip)

        concatenated = self.motion_engine.concatenate_scenes(
            scene_clips=scene_clips,
            output_video=output_video,
        )
        logger.info(f"Hindi visual background ready: {concatenated.name}")
        return concatenated

    def _generate_atmospheric_frame(
        self,
        scene_idx: int,
        width: int,
        height: int,
        category: str,
    ) -> Path:
        """Synthesize rich mood-setting visual frames using Pillow."""
        frame_file = self.output_dir / f"frame_{category}_{scene_idx:02d}.jpg"
        if frame_file.exists():
            return frame_file

        img = Image.new("RGB", (width, height), color=(15, 15, 20))
        draw = ImageDraw.Draw(img)

        # Palette selection based on genre
        if category in ("horror", "creepy", "nosleep"):
            color_top = (10, 5, 15)
            color_bottom = (35, 10, 20)
            accent = (180, 40, 40, 30)
        elif category == "revenge":
            color_top = (15, 20, 35)
            color_bottom = (40, 25, 15)
            accent = (220, 140, 30, 30)
        else:  # drama / general
            color_top = (20, 25, 40)
            color_bottom = (45, 30, 50)
            accent = (100, 120, 200, 30)

        # Draw smooth vertical atmospheric gradient
        for y in range(height):
            ratio = y / height
            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Add cinematic vignette and layered ambient lighting circles
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        center_x = width // 2 + random.randint(-80, 80)
        center_y = height // 2 + random.randint(-120, 120)
        radius = width // 2 + (scene_idx * 25) % 150

        overlay_draw.ellipse(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            fill=accent,
        )

        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=60))
        img.paste(overlay, (0, 0), overlay)

        # Edge vignette
        vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        v_draw = ImageDraw.Draw(vignette)
        v_draw.rectangle([0, 0, width, height], outline=(0, 0, 0, 180), width=60)
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=40))
        img.paste(vignette, (0, 0), vignette)

        img.save(frame_file, "JPEG", quality=92)
        return frame_file
