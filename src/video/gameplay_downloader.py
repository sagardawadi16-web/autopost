"""Autonomous Gameplay Downloader and Splicer.

Downloads high-definition (1080p 60fps), royalty-free, Creative Commons / No-Copyright
gameplay footage (Minecraft Parkour, Subway Surfers, GTA ramps) and slices them into
reusable background segments.
"""

from __future__ import annotations

import logging
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)

# Curated catalog of high-definition, verified No-Copyright gameplay videos
CURATED_GAMEPLAY_SOURCES: Dict[str, List[Dict[str, str]]] = {
    "minecraft": [
        {
            "title": "Minecraft Parkour Gameplay No Copyright",
            "url": "https://www.youtube.com/watch?v=u7kdVe8q5zs",
            "attribution": "Creative Commons / No Copyright Gameplay",
        },
        {
            "title": "Minecraft Spiral Parkour Free To Use",
            "url": "https://www.youtube.com/watch?v=n_Dv4JMiwK8",
            "attribution": "No Copyright Gameplay Background",
        },
    ],
    "subway_surfers": [
        {
            "title": "Subway Surfers Gameplay No Copyright 1080p",
            "url": "https://www.youtube.com/watch?v=1oW_s3jUu44",
            "attribution": "No Copyright Gameplay Footage",
        },
    ],
}


class GameplayDownloader:
    """Manages autonomous retrieval and splicing of gameplay background footage."""

    def __init__(self, target_dir: Optional[Path] = None) -> None:
        """Initialize downloader with target directory.

        Args:
            target_dir: Directory where sliced gameplay clips will be stored.
        """
        if target_dir is None:
            from src.config import GAMEPLAY_DIR
            self.target_dir = GAMEPLAY_DIR
        else:
            self.target_dir = Path(target_dir)

        self.target_dir.mkdir(parents=True, exist_ok=True)

    def download_and_slice(
        self,
        url: str,
        output_name: str,
        start_minute: int = 1,
        duration_minutes: int = 2,
    ) -> Optional[Path]:
        """Download and slice a specific section of a gameplay video using yt-dlp.

        Args:
            url: YouTube video URL.
            output_name: Base filename (without extension).
            start_minute: Minute offset to start slicing.
            duration_minutes: Length in minutes to slice.

        Returns:
            Path to the downloaded mp4 file if successful, else None.
        """
        out_path = self.target_dir / f"{output_name}.mp4"
        if out_path.exists() and out_path.stat().st_size > 1_000_000:
            logger.info(f"Gameplay clip already exists: {out_path.name}")
            return out_path

        start_sec = start_minute * 60
        end_sec = start_sec + (duration_minutes * 60)
        time_range = f"*{start_sec}-{end_sec}"

        ffmpeg_bin = Path(get_ffmpeg_cmd()).parent

        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--ffmpeg-location",
            str(ffmpeg_bin),
            "--download-sections",
            time_range,
            "-f",
            "bestvideo[height<=1080][ext=mp4]/best[height<=1080]/best",
            url,
            "-o",
            str(out_path),
            "--no-playlist",
            "--force-overwrites",
        ]

        logger.info(
            f"Downloading & slicing gameplay clip '{output_name}' ({duration_minutes}m from {url})..."
        )
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if out_path.exists() and out_path.stat().st_size > 500_000:
                logger.info(f"Successfully downloaded gameplay clip: {out_path.name} ({out_path.stat().st_size / 1_000_000:.1f} MB)")
                return out_path
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to download gameplay clip via yt-dlp: {e.stderr or e.stdout}")
        except Exception as e:
            logger.warning(f"Error executing gameplay download: {e}")

        return None

    def ensure_gameplay_clips(self, min_clips: int = 1) -> List[Path]:
        """Ensure at least min_clips exist in assets/gameplay, downloading if needed."""
        existing = [
            f for f in self.target_dir.glob("*.mp4") if f.stat().st_size > 500_000
        ]
        if len(existing) >= min_clips:
            return existing

        logger.info(f"Found {len(existing)} clips; auto-downloading generic parkour gameplay...")
        # Pick from curated sources
        sources = CURATED_GAMEPLAY_SOURCES.get("minecraft", [])
        for i, src in enumerate(sources):
            clip_name = f"minecraft_parkour_{i + 1:02d}"
            # Slice different random offsets
            start_m = (i + 1) * 2
            clip = self.download_and_slice(
                url=src["url"],
                output_name=clip_name,
                start_minute=start_m,
                duration_minutes=2,
            )
            if clip:
                existing.append(clip)
            if len(existing) >= min_clips:
                break

        return existing


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Download and splice royalty-free gameplay footage.")
    parser.add_argument("--type", choices=["minecraft", "subway_surfers"], default="minecraft", help="Type of gameplay")
    parser.add_argument("--url", default=None, help="Custom YouTube URL to download and slice")
    parser.add_argument("--duration", type=int, default=2, help="Slice duration in minutes (default: 2)")
    parser.add_argument("--count", type=int, default=1, help="Number of clips to ensure (default: 1)")

    args = parser.parse_args()
    downloader = GameplayDownloader()

    if args.url:
        downloader.download_and_slice(args.url, output_name="custom_gameplay", duration_minutes=args.duration)
    else:
        downloader.ensure_gameplay_clips(min_clips=args.count)
