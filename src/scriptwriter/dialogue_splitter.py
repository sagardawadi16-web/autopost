"""Dialogue splitter and character voice assignment engine.

Parses formatted scripts into distinct speaker segments and assigns appropriate
Edge-TTS voice profiles based on character archetypes, gender, and emotional tone.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.config import VOICE_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class DialogueSegment:
    """Represents an atomic spoken passage assigned to a specific voice profile."""

    speaker_tag: str
    character_name: str
    character_type: str  # 'narrator', 'young_male', 'young_female', 'villain', 'child', etc.
    voice: str
    text: str
    language: str


class DialogueSplitter:
    """Splits structured scripts into segmented lines with assigned voice models."""

    def __init__(self, language: str = "english") -> None:
        """Initialize dialogue splitter.

        Args:
            language: Target language ('english' or 'hindi').
        """
        self.language = language.lower()

    def parse_script(self, script_text: str) -> List[DialogueSegment]:
        """Parse raw tagged script text into dialogue segments.

        Args:
            script_text: Full script containing tags like [NARRATOR] and [CHARACTER: Name].

        Returns:
            List of DialogueSegment objects with voice assignments.
        """
        segments: List[DialogueSegment] = []
        raw_blocks = script_text.split("\n\n")

        current_speaker = "NARRATOR"
        current_name = "Narrator"

        for block in raw_blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            for line in lines:
                # Match tags like [NARRATOR] or [CHARACTER: Sarah]
                tag_match = re.match(r"^\[([A-Z0-9_\-]+)(?::\s*([^\]]+))?\]\s*(.*)$", line, re.IGNORECASE)
                if tag_match:
                    raw_tag = tag_match.group(1).upper()
                    raw_name = tag_match.group(2) or ("Narrator" if "NARRATOR" in raw_tag else "Character")
                    content = tag_match.group(3).strip()

                    current_speaker = raw_tag
                    current_name = raw_name.strip()
                    text_to_speak = content
                else:
                    text_to_speak = line

                # Clean quotation marks and markdown artifacts
                clean_text = text_to_speak.strip('"\u201c\u201d*')
                if not clean_text:
                    continue

                # Prompt leak filter - ignore system instructions / prompt echo lines
                prompt_leak_keywords = [
                    "you are an award-winning",
                    "you are an expert viral",
                    "original reddit story:",
                    "active strategic directives:",
                    "formatting requirements:",
                    "critical requirements:",
                    "critical constraints:",
                    "word count:",
                    "first 3 seconds:",
                    "structure:",
                    "tags: use",
                    "story text:",
                    "generate the formatted script",
                    "generate the shorts script",
                    "genre: ",
                    "language: ",
                    "critical fixes from previous rejection:",
                ]
                if any(kw in clean_text.lower() for kw in prompt_leak_keywords):
                    logger.warning(f"Filtered out leaked prompt text: '{clean_text[:60]}...'")
                    continue

                char_type = self._classify_character(current_name, clean_text)
                voice = self._assign_voice(char_type)

                segments.append(
                    DialogueSegment(
                        speaker_tag=current_speaker,
                        character_name=current_name,
                        character_type=char_type,
                        voice=voice,
                        text=clean_text,
                        language=self.language,
                    )
                )

        logger.info(f"Parsed {len(segments)} dialogue segments for language '{self.language}'")
        return segments

    def _classify_character(self, name: str, sample_text: str) -> str:
        """Deduce character archetype from name and dialogue content."""
        name_lower = name.lower()
        text_lower = sample_text.lower()

        if "narrator" in name_lower:
            return "narrator"

        # Female identifiers
        female_names = ["mom", "mother", "sister", "wife", "girlfriend", "karen", "susan", "lisa", "emma", "woman", "girl", "aunt"]
        if any(f in name_lower for f in female_names):
            return "young_female"

        # Child identifiers
        child_names = ["child", "kid", "son", "daughter", "toddler", "boy", "little", "baby"]
        if any(c in name_lower for c in child_names):
            return "child"

        # Villain / Antagonist identifiers
        villain_names = ["boss", "landlord", "officer", "demon", "stalker", "stranger", "intruder", "creature"]
        if any(v in name_lower for v in villain_names):
            return "villain"

        # Male identifiers or default
        male_names = ["dad", "father", "brother", "husband", "boyfriend", "man", "guy", "uncle", "cop"]
        if any(m in name_lower for m in male_names):
            return "young_male"

        return "young_male"

    def _assign_voice(self, char_type: str) -> str:
        """Map character archetype to configured Edge-TTS voice identifier."""
        if self.language == "hindi":
            # Hindi channel voice profiles
            if char_type in ("narrator_female", "young_female"):
                return VOICE_CONFIG.hindi.narrator_female
            return VOICE_CONFIG.hindi.narrator

        # English channel voice profiles
        cfg = VOICE_CONFIG.english
        mapping = {
            "narrator": cfg.narrator,
            "narrator_female": cfg.narrator_female,
            "young_male": cfg.young_male,
            "young_female": cfg.young_female,
            "villain": cfg.villain,
            "child": cfg.child,
        }
        return mapping.get(char_type, cfg.narrator)
