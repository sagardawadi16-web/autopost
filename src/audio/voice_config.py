"""Voice Configuration and Character Audio Profiles.

Maps character personas to Microsoft Edge-TTS voices with pitch and rate adjustments.
Supports both English and Hindi neural voices.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from src.config import VOICE_CONFIG


@dataclass
class VoiceProfile:
    """Settings for an Edge-TTS speaker."""

    voice_id: str
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"


# Default voice profile registry
VOICE_PROFILES: Dict[str, Dict[str, VoiceProfile]] = {
    "english": {
        "narrator": VoiceProfile(voice_id=VOICE_CONFIG.english.narrator, rate="+0%", pitch="+0Hz"),
        "narrator_female": VoiceProfile(voice_id=VOICE_CONFIG.english.narrator_female, rate="+0%", pitch="+0Hz"),
        "young_male": VoiceProfile(voice_id=VOICE_CONFIG.english.young_male, rate="+3%", pitch="+5Hz"),
        "young_female": VoiceProfile(voice_id=VOICE_CONFIG.english.young_female, rate="+3%", pitch="+5Hz"),
        "villain": VoiceProfile(voice_id=VOICE_CONFIG.english.villain, rate="-6%", pitch="-8Hz"),
        "child": VoiceProfile(voice_id=VOICE_CONFIG.english.child, rate="+5%", pitch="+25Hz"),
    },
    "hindi": {
        "narrator": VoiceProfile(voice_id=VOICE_CONFIG.hindi.narrator, rate="+0%", pitch="+0Hz"),
        "narrator_female": VoiceProfile(voice_id=VOICE_CONFIG.hindi.narrator_female, rate="+0%", pitch="+0Hz"),
        "young_male": VoiceProfile(voice_id=VOICE_CONFIG.hindi.narrator, rate="+5%", pitch="+10Hz"),
        "young_female": VoiceProfile(voice_id=VOICE_CONFIG.hindi.narrator_female, rate="+4%", pitch="+15Hz"),
        "villain": VoiceProfile(voice_id=VOICE_CONFIG.hindi.narrator, rate="-8%", pitch="-12Hz"),
        "child": VoiceProfile(voice_id=VOICE_CONFIG.hindi.narrator_female, rate="+8%", pitch="+30Hz"),
    },
}


def get_voice_profile(language: str, character_type: str) -> VoiceProfile:
    """Retrieve voice profile for a language and character type.

    Args:
        language: 'english' or 'hindi'.
        character_type: Character role ('narrator', 'young_male', etc.).

    Returns:
        VoiceProfile object.
    """
    lang_key = language.lower()
    profiles = VOICE_PROFILES.get(lang_key, VOICE_PROFILES["english"])
    return profiles.get(character_type, profiles.get("narrator", VoiceProfile(voice_id="en-US-GuyNeural")))
