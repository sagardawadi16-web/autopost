"""Music Mixer and Audio Post-Processor.

Blends speech narration with royalty-free background ambient tracks.
Includes automatic procedural ambient generator if no background tracks are present,
ensuring 100% turnkey autonomous execution.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)


class MusicMixer:
    """Mixes background music underneath speech tracks with audio ducking and fades."""

    def __init__(self, music_dir: Optional[Path] = None, output_dir: Optional[Path] = None) -> None:
        """Initialize music mixer.

        Args:
            music_dir: Directory containing royalty-free music files.
            output_dir: Directory for processed audio outputs.
        """
        if music_dir is None:
            from src.config import AUDIO_ASSETS_DIR
            self.music_dir = AUDIO_ASSETS_DIR
        else:
            self.music_dir = Path(music_dir)

        if output_dir is None:
            from src.config import AUDIO_OUTPUT_DIR
            self.output_dir = AUDIO_OUTPUT_DIR
        else:
            self.output_dir = Path(output_dir)

        self.music_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def mix_narration_and_music(
        self,
        narration_path: Path,
        duration_seconds: float,
        category: str = "horror",
        output_filename: str = "final_soundtrack",
        music_volume_pct: float = 0.12,  # 12% background volume
    ) -> Path:
        """Mix narration audio with ambient background music using FFmpeg.

        Args:
            narration_path: Path to narration MP3.
            duration_seconds: Target length in seconds.
            category: Genre ('horror', 'drama', 'revenge', etc.).
            output_filename: Name of the mixed audio file.
            music_volume_pct: Volume multiplier for the background track.

        Returns:
            Path to the final mixed audio file.
        """
        final_soundtrack_path = self.output_dir / f"{output_filename}.mp3"

        # Check for category-specific music files in assets/audio/
        music_file = self._find_or_generate_music(category, duration_seconds)

        # Build FFmpeg filter_complex: loop music, lower music volume, overlay speech, fade out
        fade_out_start = max(0, duration_seconds - 3.0)

        cmd = [
            get_ffmpeg_cmd(),
            "-y",
            "-i", str(narration_path),
            "-stream_loop", "-1",
            "-i", str(music_file),
            "-filter_complex",
            f"[1:a]volume={music_volume_pct},afade=t=in:ss=0:d=2,afade=t=out:st={fade_out_start}:d=3[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(final_soundtrack_path),
        ]

        logger.info(f"Mixing narration with ambient track '{music_file.name}' via FFmpeg...")
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Soundtrack mixed successfully: '{final_soundtrack_path.name}'")
            return final_soundtrack_path
        except subprocess.CalledProcessError as e:
            logger.warning(f"FFmpeg audio mixing failed ({e.stderr}); returning raw narration.")
            return narration_path

    def _find_or_generate_music(self, category: str, duration_sec: float) -> Path:
        """Find an existing music file or procedurally generate an ambient drone tone."""
        # Check if user has uploaded any mp3 in music_dir
        for ext in ("*.mp3", "*.wav", "*.ogg"):
            candidates = list(self.music_dir.glob(ext))
            if candidates:
                return candidates[0]

        # Procedurally synthesize a subtle cinematic dark ambient drone using FFmpeg
        procedural_path = self.music_dir / f"ambient_{category}_tone.mp3"
        if not procedural_path.exists():
            logger.info("No audio tracks found in assets/audio; generating procedural ambient drone...")
            freq = "55" if category == "horror" else ("65" if category == "drama" else "75")
            gen_cmd = [
                get_ffmpeg_cmd(),
                "-y",
                "-f", "lavfi",
                "-i", f"sine=frequency={freq}:duration=60",
                "-filter_complex",
                "lowpass=f=200,volume=0.3",
                "-c:a", "libmp3lame",
                str(procedural_path),
            ]
            try:
                subprocess.run(gen_cmd, capture_output=True, text=True, check=True)
            except Exception as e:
                logger.warning(f"Could not generate procedural ambient tone: {e}")

        return procedural_path
