"""Ghibli Visual Engine.

Generates breathtaking Studio Ghibli watercolor anime frames using AI image synthesis
optimized for 16:9 landscape (story videos) and 9:16 vertical (YouTube Shorts).
"""

from __future__ import annotations

import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

from src.config import OUTPUT_DIR

logger = logging.getLogger(__name__)

GHIBLI_OUTPUT_DIR = OUTPUT_DIR / "ghibli"
SCENES_OUTPUT_DIR = GHIBLI_OUTPUT_DIR / "scenes"


class VisualEngine:
    """Generates painterly Studio Ghibli-inspired scene imagery."""

    def __init__(self, scenes_dir: Optional[Path] = None) -> None:
        self.scenes_dir = scenes_dir or SCENES_OUTPUT_DIR
        self.scenes_dir.mkdir(parents=True, exist_ok=True)

    def generate_scene_image(
        self,
        prompt: str,
        scene_index: int,
        is_shorts: bool = True,
        seed: Optional[int] = None,
    ) -> Path:
        """Generate high-resolution Ghibli visual frame for a scene.

        Args:
            prompt: Text prompt describing the scene.
            scene_index: Index number of the scene.
            is_shorts: If True, renders 9:16 vertical (720x1280). If False, 16:9 landscape (1280x720).
            seed: Optional integer seed for visual consistency.

        Returns:
            Path to the downloaded image file.
        """
        width, height = (720, 1280) if is_shorts else (1280, 720)
        output_file = self.scenes_dir / f"scene_{scene_index:03d}_{width}x{height}.jpg"

        # Enhance prompt with Ghibli signature tags if not already present
        enhanced_prompt = prompt
        if "studio ghibli" not in enhanced_prompt.lower():
            enhanced_prompt = f"Studio Ghibli style, Hayao Miyazaki anime aesthetic, {enhanced_prompt}"
        if "watercolor" not in enhanced_prompt.lower():
            enhanced_prompt = f"{enhanced_prompt}, soft watercolor gouache textures, cinematic lighting, cozy peaceful 90s village"

        logger.info(f"Generating Ghibli frame for Scene {scene_index} ({width}x{height})...")

        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        seed_param = f"&seed={seed}" if seed is not None else ""

        # Multi-model fallback across attempts (Flux -> Turbo)
        models = ["flux", "turbo", "flux"]
        for attempt, model_name in enumerate(models, start=1):
            try:
                t0 = time.time()
                image_url = (
                    f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                    f"?width={width}&height={height}&model={model_name}&nologo=true{seed_param}"
                )
                req = urllib.request.Request(
                    image_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                    with open(output_file, "wb") as f:
                        f.write(data)

                # Verify valid image using Pillow
                with Image.open(output_file) as img:
                    img.verify()

                logger.info(f"Scene {scene_index} image successfully rendered in {time.time() - t0:.2f}s [{model_name}] ({output_file.name})")
                return output_file

            except Exception as e:
                logger.warning(f"Image generation attempt {attempt} ({model_name}) note: {e}. Trying next...")
                time.sleep(1.5)

        # Fallback procedural painterly placeholder if network fails
        logger.warning(f"Network generation failed. Generating emergency Ghibli placeholder for Scene {scene_index}")
        self._generate_fallback_image(output_file, width, height, scene_index)
        return output_file

    def _generate_fallback_image(self, target_path: Path, width: int, height: int, scene_idx: int) -> None:
        """Create a soft watercolor gradient image as offline fallback."""
        from PIL import ImageDraw

        img = Image.new("RGB", (width, height), color=(45, 90, 65))
        draw = ImageDraw.Draw(img)
        # Draw soft atmospheric color bands
        for y in range(height):
            r = int(35 + (y / height) * 50)
            g = int(70 + (y / height) * 70)
            b = int(55 + (y / height) * 45)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        img.save(target_path, "JPEG", quality=90)
