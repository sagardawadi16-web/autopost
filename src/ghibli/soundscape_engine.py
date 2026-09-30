"""Soundscape & Audio Mixing Engine for Ghibli Nostalgic Content.

Synthesizes soulful Hindi voice narration via Edge-TTS, layers atmospheric ASMR
soundscapes (rain on tin roofs, chulha firewood crackling), and mixes soft Ghibli-inspired music.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import edge_tts

from src.config import AUDIO_OUTPUT_DIR, OUTPUT_DIR
from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)

GHIBLI_AUDIO_DIR = OUTPUT_DIR / "ghibli" / "audio"


class SoundscapeEngine:
    """Orchestrates multi-layer audio production for Ghibli videos."""

    def __init__(self, audio_dir: Optional[Path] = None) -> None:
        self.audio_dir = audio_dir or GHIBLI_AUDIO_DIR
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_cmd = get_ffmpeg_cmd()

    def synthesize_narration(
        self,
        text: str,
        output_name: str,
        voice: str = "hi-IN-SwaraNeural",
        rate: str = "-8%",
        pitch: str = "-2Hz",
    ) -> Path:
        """Synthesize soothing, emotionally grounded Hindi narration using Edge-TTS.

        Args:
            text: Story script text to speak.
            output_name: Output filename (without extension).
            voice: Edge-TTS voice identifier.
            rate: Speed modifier.
            pitch: Pitch modifier.

        Returns:
            Path to the generated MP3 voice track.
        """
        output_file = self.audio_dir / f"{output_name}_voice.mp3"
        logger.info(f"Synthesizing soulful narration with voice '{voice}' ({len(text)} chars)...")

        async def _speak():
            comm = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
            await comm.save(str(output_file))

        asyncio.run(_speak())
        logger.info(f"Voice narration saved to {output_file.name}")
        return output_file

    def get_audio_duration(self, audio_path: Path) -> float:
        """Get precise duration of an audio file in seconds via ffprobe or ffmpeg."""
        cmd = [
            self.ffmpeg_cmd,
            "-i", str(audio_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                try:
                    time_str = line.split("Duration:")[1].split(",")[0].strip()
                    parts = time_str.split(":")
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except Exception:
                    break
        return 30.0

    def mix_soundscape(
        self,
        voice_audio: Path,
        output_name: str,
        music_path: Optional[Path] = None,
        asmr_rain_path: Optional[Path] = None,
        music_volume: float = 0.16,
        asmr_volume: float = 0.22,
    ) -> Path:
        """Mix voice narration with atmospheric ASMR and peaceful background music.

        If external ASMR rain or music files are absent, uses FFmpeg procedural acoustic
        synthesis to generate warm natural pink-noise rain and ambient presence.
        """
        duration = self.get_audio_duration(voice_audio)
        output_mixed = self.audio_dir / f"{output_name}_soundscape.mp3"

        logger.info(f"Mixing complete soundscape for {output_name} (Duration: {duration:.1f}s)...")

        # Determine ASMR source (file or procedural rain synthesis)
        use_file_asmr = asmr_rain_path and asmr_rain_path.exists()
        use_file_music = music_path and music_path.exists()

        if use_file_music and use_file_asmr:
            # All 3 files present: Voice + Music + ASMR
            cmd = [
                self.ffmpeg_cmd, "-y",
                "-i", str(voice_audio),
                "-stream_loop", "-1", "-i", str(music_path),
                "-stream_loop", "-1", "-i", str(asmr_rain_path),
                "-filter_complex",
                f"[0:a]volume=1.0[v];"
                f"[1:a]volume={music_volume}[m];"
                f"[2:a]volume={asmr_volume}[r];"
                f"[v][m][r]amix=inputs=3:duration=first:dropout_transition=2[out]",
                "-map", "[out]",
                "-t", f"{duration:.3f}",
                "-c:a", "libmp3lame", "-b:a", "192k",
                str(output_mixed),
            ]
        elif use_file_music:
            # Voice + Music + Procedural calming rain ASMR
            cmd = [
                self.ffmpeg_cmd, "-y",
                "-i", str(voice_audio),
                "-stream_loop", "-1", "-i", str(music_path),
                "-f", "lavfi", "-i", f"anoisesrc=d={duration+2}:c=pink:r=44100:a=0.08,lowpass=f=1200",
                "-filter_complex",
                f"[0:a]volume=1.0[v];"
                f"[1:a]volume={music_volume}[m];"
                f"[2:a]volume={asmr_volume}[r];"
                f"[v][m][r]amix=inputs=3:duration=first:dropout_transition=2[out]",
                "-map", "[out]",
                "-t", f"{duration:.3f}",
                "-c:a", "libmp3lame", "-b:a", "192k",
                str(output_mixed),
            ]
        else:
            # Voice + Procedural soothing rain ASMR + gentle ambient warm tone
            cmd = [
                self.ffmpeg_cmd, "-y",
                "-i", str(voice_audio),
                "-f", "lavfi", "-i", f"anoisesrc=d={duration+2}:c=pink:r=44100:a=0.07,lowpass=f=1100",
                "-filter_complex",
                f"[0:a]volume=1.0[v];"
                f"[1:a]volume={asmr_volume}[r];"
                f"[v][r]amix=inputs=2:duration=first:dropout_transition=2[out]",
                "-map", "[out]",
                "-t", f"{duration:.3f}",
                "-c:a", "libmp3lame", "-b:a", "192k",
                str(output_mixed),
            ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.warning(f"Audio mix note ({res.stderr[:100]}), falling back to direct voice narration.")
            return voice_audio

        logger.info(f"Soundscape successfully mastered into {output_mixed.name}")
        return output_mixed
