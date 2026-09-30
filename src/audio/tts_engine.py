"""Edge-TTS Text-to-Speech Engine with Word-Level Timestamp Extraction.

Wraps Microsoft Edge-TTS async API to generate natural neural voices
while capturing cue and word boundary timing metadata for karaoke-style subtitles.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WordTiming:
    """Represents precise timing offset for a spoken word."""

    word: str
    start_time_ms: int
    end_time_ms: int


@dataclass
class TTSSynthesisResult:
    """Outcome of an Edge-TTS synthesis run."""

    audio_path: Path
    timing_path: Path
    duration_seconds: float
    word_timings: List[WordTiming]


class TTSEngine:
    """Generates audio files with word boundary metadata via Edge-TTS."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize TTS engine.

        Args:
            output_dir: Directory where generated audio files are stored.
        """
        if output_dir is None:
            from src.config import AUDIO_OUTPUT_DIR
            self.output_dir = AUDIO_OUTPUT_DIR
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize_async(
        self,
        text: str,
        voice: str,
        output_filename: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
    ) -> TTSSynthesisResult:
        """Synthesize text to MP3 and extract word timestamps asynchronously.

        Args:
            text: Text passage to speak.
            voice: Edge-TTS neural voice identifier (e.g. 'en-US-GuyNeural').
            output_filename: Base name for output audio and timing files (without extension).
            rate: Speech rate modifier (e.g. '+5%', '-10%').
            pitch: Speech pitch modifier (e.g. '+0Hz', '-5Hz').
            volume: Speech volume modifier.

        Returns:
            TTSSynthesisResult containing paths and timing metadata.
        """
        import edge_tts

        audio_path = self.output_dir / f"{output_filename}.mp3"
        timing_path = self.output_dir / f"{output_filename}_timing.json"

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )

        submaker = edge_tts.SubMaker()
        audio_chunks: List[bytes] = []

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)

        # Write audio data to file
        with open(audio_path, "wb") as f:
            for chunk_data in audio_chunks:
                f.write(chunk_data)

        # Extract word timings from submaker cues
        word_timings: List[WordTiming] = []
        for cue in submaker.cues:
            # cue.start and cue.end are timedelta objects
            start_ms = int(cue.start.total_seconds() * 1000)
            end_ms = int(cue.end.total_seconds() * 1000)
            cue_text = cue.content.strip()
            words_in_cue = cue_text.split()

            if not words_in_cue:
                continue

            cue_duration = max(end_ms - start_ms, 100)
            ms_per_word = cue_duration // len(words_in_cue)

            for w_idx, w in enumerate(words_in_cue):
                w_start = start_ms + (w_idx * ms_per_word)
                w_end = w_start + ms_per_word
                word_timings.append(
                    WordTiming(
                        word=w,
                        start_time_ms=w_start,
                        end_time_ms=w_end,
                    )
                )

        # If no cues were returned (rare edge case), interpolate based on total word count and ~150 WPM
        if not word_timings and text.strip():
            words_in_text = text.strip().split()
            estimated_duration_ms = int((len(words_in_text) / 2.5) * 1000)
            ms_per_word = max(150, estimated_duration_ms // max(1, len(words_in_text)))
            for w_idx, w in enumerate(words_in_text):
                word_timings.append(
                    WordTiming(
                        word=w,
                        start_time_ms=w_idx * ms_per_word,
                        end_time_ms=(w_idx + 1) * ms_per_word,
                    )
                )

        total_duration_sec = (word_timings[-1].end_time_ms / 1000.0) if word_timings else 1.0

        # Save timing metadata
        timings_data = [
            {"word": wt.word, "start_ms": wt.start_time_ms, "end_ms": wt.end_time_ms}
            for wt in word_timings
        ]
        with open(timing_path, "w", encoding="utf-8") as f:
            json.dump({"duration_sec": total_duration_sec, "words": timings_data}, f, indent=2)

        logger.info(f"Synthesized '{output_filename}.mp3' ({total_duration_sec:.1f}s, {len(word_timings)} words)")
        return TTSSynthesisResult(
            audio_path=audio_path,
            timing_path=timing_path,
            duration_seconds=total_duration_sec,
            word_timings=word_timings,
        )

    def synthesize(
        self,
        text: str,
        voice: str,
        output_filename: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
    ) -> TTSSynthesisResult:
        """Synchronous wrapper for synthesize_async."""
        return asyncio.run(
            self.synthesize_async(
                text=text,
                voice=voice,
                output_filename=output_filename,
                rate=rate,
                pitch=pitch,
                volume=volume,
            )
        )
