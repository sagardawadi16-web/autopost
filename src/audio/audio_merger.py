"""Audio merger for concatenating multi-character voice segments.

Combines individual character speech clips with natural pauses and builds
a unified master word timing index for subtitle generation.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.audio.tts_engine import TTSSynthesisResult, WordTiming
from src.utils import get_ffmpeg_cmd

logger = logging.getLogger(__name__)


@dataclass
class MergedAudioResult:
    """Outcome of merging multiple dialogue audio tracks."""

    audio_path: Path
    timing_path: Path
    total_duration_seconds: float
    master_word_timings: List[WordTiming]


class AudioMerger:
    """Concatenates speech segments and computes global word timing offsets."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize audio merger.

        Args:
            output_dir: Directory where final merged files are saved.
        """
        if output_dir is None:
            from src.config import AUDIO_OUTPUT_DIR
            self.output_dir = AUDIO_OUTPUT_DIR
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def merge_segments(
        self,
        segment_results: List[TTSSynthesisResult],
        output_filename: str,
        pause_ms: int = 250,
    ) -> MergedAudioResult:
        """Merge dialogue segments into one continuous audio track.

        Args:
            segment_results: Ordered list of TTSSynthesisResult objects.
            output_filename: Name of the merged output file (without extension).
            pause_ms: Micro-pause in milliseconds between distinct segments.

        Returns:
            MergedAudioResult with unified audio path and global timestamps.
        """
        if not segment_results:
            raise ValueError("No audio segments provided for merging.")

        final_audio_path = self.output_dir / f"{output_filename}_merged.mp3"
        final_timing_path = self.output_dir / f"{output_filename}_merged_timing.json"

        # Create FFmpeg concat file list
        concat_txt_path = self.output_dir / f"{output_filename}_concat.txt"
        with open(concat_txt_path, "w", encoding="utf-8") as f:
            for seg in segment_results:
                # FFmpeg concat requires escaped forward slashes
                clean_path = str(seg.audio_path.resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        # Execute FFmpeg concat demuxer
        cmd = [
            get_ffmpeg_cmd(),
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt_path),
            "-c", "copy",
            str(final_audio_path),
        ]

        logger.info(f"Merging {len(segment_results)} audio segments via FFmpeg...")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg audio concat failed: {e.stderr}")
            # Fallback: simple binary append for MP3 frames if ffmpeg direct copy fails
            with open(final_audio_path, "wb") as out_f:
                for seg in segment_results:
                    with open(seg.audio_path, "rb") as in_f:
                        out_f.write(in_f.read())

        # Clean temp concat list
        if concat_txt_path.exists():
            try:
                concat_txt_path.unlink()
            except Exception:
                pass

        # Calculate unified word boundary timestamps with sequential offsets
        master_timings: List[WordTiming] = []
        cumulative_offset_ms = 0

        for seg in segment_results:
            for wt in seg.word_timings:
                master_timings.append(
                    WordTiming(
                        word=wt.word,
                        start_time_ms=wt.start_time_ms + cumulative_offset_ms,
                        end_time_ms=wt.end_time_ms + cumulative_offset_ms,
                    )
                )
            cumulative_offset_ms += int(seg.duration_seconds * 1000)

        total_sec = cumulative_offset_ms / 1000.0

        # Save global timing JSON
        timing_payload = {
            "total_duration_sec": total_sec,
            "segment_count": len(segment_results),
            "words": [
                {"word": wt.word, "start_ms": wt.start_time_ms, "end_ms": wt.end_time_ms}
                for wt in master_timings
            ],
        }
        with open(final_timing_path, "w", encoding="utf-8") as f:
            json.dump(timing_payload, f, indent=2)

        logger.info(f"Audio merged successfully: '{final_audio_path.name}' ({total_sec:.1f}s, {len(master_timings)} words)")

        return MergedAudioResult(
            audio_path=final_audio_path,
            timing_path=final_timing_path,
            total_duration_seconds=total_sec,
            master_word_timings=master_timings,
        )
