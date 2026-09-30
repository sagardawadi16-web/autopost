"""Configuration module for the automated YouTube channel pipeline.

This module centralizes all application settings, directory paths, API credentials,
scraping parameters, voice configurations, video rendering settings, and YouTube
channel metadata.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Load local .env file if present
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    try:
        with open(_env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass


# ==============================================================================
# Base Directory & Paths
# ==============================================================================

BASE_DIR: Path = Path(__file__).parent.parent.resolve()
SRC_DIR: Path = BASE_DIR / "src"

# Data Directories
DATA_DIR: Path = BASE_DIR / "data"
STORIES_DIR: Path = DATA_DIR / "stories"
METADATA_DIR: Path = DATA_DIR / "metadata"
DATABASE_DIR: Path = DATA_DIR / "db"

# Asset Directories
ASSETS_DIR: Path = BASE_DIR / "assets"
GAMEPLAY_DIR: Path = ASSETS_DIR / "gameplay"
FONTS_DIR: Path = ASSETS_DIR / "fonts"
AUDIO_ASSETS_DIR: Path = ASSETS_DIR / "audio"
IMAGES_ASSETS_DIR: Path = ASSETS_DIR / "images"

# Output Directories
OUTPUT_DIR: Path = BASE_DIR / "output"
AUDIO_OUTPUT_DIR: Path = OUTPUT_DIR / "audio"
VIDEO_OUTPUT_DIR: Path = OUTPUT_DIR / "video"
THUMBNAILS_OUTPUT_DIR: Path = OUTPUT_DIR / "thumbnails"
TEMP_OUTPUT_DIR: Path = OUTPUT_DIR / "temp"

ALL_DIRECTORIES: List[Path] = [
    DATA_DIR,
    STORIES_DIR,
    METADATA_DIR,
    DATABASE_DIR,
    ASSETS_DIR,
    GAMEPLAY_DIR,
    FONTS_DIR,
    AUDIO_ASSETS_DIR,
    IMAGES_ASSETS_DIR,
    OUTPUT_DIR,
    AUDIO_OUTPUT_DIR,
    VIDEO_OUTPUT_DIR,
    THUMBNAILS_OUTPUT_DIR,
    TEMP_OUTPUT_DIR,
]


def ensure_directories() -> None:
    """Ensure that all necessary project directories exist on the filesystem."""
    for directory in ALL_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# Secrets & Environment Variables
# ==============================================================================

REDDIT_CLIENT_ID: Optional[str] = os.environ.get("REDDIT_CLIENT_ID", None)
REDDIT_CLIENT_SECRET: Optional[str] = os.environ.get("REDDIT_CLIENT_SECRET", None)
REDDIT_USER_AGENT: str = os.environ.get("REDDIT_USER_AGENT", "autopost:v1.0.0 (by /u/autopost)")

GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY", None)

YOUTUBE_CLIENT_ID: Optional[str] = os.environ.get("YOUTUBE_CLIENT_ID", None)
YOUTUBE_CLIENT_SECRET: Optional[str] = os.environ.get("YOUTUBE_CLIENT_SECRET", None)
YT_EN_REFRESH_TOKEN: Optional[str] = os.environ.get("YT_EN_REFRESH_TOKEN", None)
YT_HI_REFRESH_TOKEN: Optional[str] = os.environ.get("YT_HI_REFRESH_TOKEN", None)

R2_ACCESS_KEY: Optional[str] = os.environ.get("R2_ACCESS_KEY", None)
R2_SECRET_KEY: Optional[str] = os.environ.get("R2_SECRET_KEY", None)
R2_ENDPOINT_URL: Optional[str] = os.environ.get("R2_ENDPOINT_URL", None)
R2_BUCKET_NAME: Optional[str] = os.environ.get("R2_BUCKET_NAME", None)


# ==============================================================================
# Data Classes for Structured Configuration
# ==============================================================================

@dataclass(frozen=True)
class StorySelectionCriteria:
    """Criteria used to filter and select stories from Reddit.

    Attributes:
        min_upvotes: Minimum upvote threshold for a story to be considered.
        min_words: Minimum word count required for story content.
        max_words: Maximum word count permitted for story content.
    """

    min_upvotes: int = 1000
    min_words: int = 500
    max_words: int = 5000


@dataclass(frozen=True)
class RedditConfig:
    """Reddit scraping and API client configuration.

    Attributes:
        client_id: Reddit OAuth client ID.
        client_secret: Reddit OAuth client secret.
        user_agent: User agent string passed in Reddit API requests.
        subreddits: Target subreddits to monitor for high-quality stories.
        story_criteria: Selection parameters to qualify eligible posts.
    """

    client_id: Optional[str] = REDDIT_CLIENT_ID
    client_secret: Optional[str] = REDDIT_CLIENT_SECRET
    user_agent: str = REDDIT_USER_AGENT
    subreddits: List[str] = field(
        default_factory=lambda: [
            "nosleep",
            "creepy",
            "AmItheAsshole",
            "ProRevenge",
            "entitledparents",
            "relationship_advice",
            "tifu",
        ]
    )
    story_criteria: StorySelectionCriteria = field(default_factory=StorySelectionCriteria)


@dataclass(frozen=True)
class EnglishVoiceConfig:
    """Edge-TTS voice profiles for English audio narration.

    Attributes:
        narrator: Primary neutral male narrator voice.
        narrator_female: Primary female narrator voice.
        young_male: Voice profile for young male character dialogues.
        young_female: Voice profile for young female character dialogues.
        villain: Voice profile for ominous/antagonist characters.
        child: Voice profile for child characters.
    """

    narrator: str = "en-US-GuyNeural"
    narrator_female: str = "en-US-JennyNeural"
    young_male: str = "en-US-ChristopherNeural"
    young_female: str = "en-US-AriaNeural"
    villain: str = "en-US-DavisNeural"
    child: str = "en-US-AnaNeural"


@dataclass(frozen=True)
class HindiVoiceConfig:
    """Edge-TTS voice profiles for Hindi audio narration.

    Attributes:
        narrator: Primary Hindi male narrator voice.
        narrator_female: Primary Hindi female narrator voice.
    """

    narrator: str = "hi-IN-MadhurNeural"
    narrator_female: str = "hi-IN-SwaraNeural"


@dataclass(frozen=True)
class VoiceConfig:
    """Combined voice configuration container for all supported languages.

    Attributes:
        english: English voice profile mappings.
        hindi: Hindi voice profile mappings.
    """

    english: EnglishVoiceConfig = field(default_factory=EnglishVoiceConfig)
    hindi: HindiVoiceConfig = field(default_factory=HindiVoiceConfig)


@dataclass(frozen=True)
class VideoSettings:
    """Video rendering and encoding parameters.

    Attributes:
        long_form_duration_range: Minimum and maximum duration in seconds for long-form videos.
        shorts_max_duration: Maximum duration in seconds for YouTube Shorts.
        resolution_landscape: Default resolution string for landscape videos (16:9).
        resolution_portrait: Default resolution string for portrait Shorts (9:16).
        fps: Target frame rate for rendered videos.
        video_codec: FFmpeg video codec for output encoding.
        audio_codec: FFmpeg audio codec for output encoding.
        audio_bitrate: Audio bitrate for encoding.
    """

    long_form_duration_range: Tuple[int, int] = (480, 900)
    shorts_max_duration: int = 59
    resolution_landscape: str = "1920x1080"
    resolution_portrait: str = "1080x1920"
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"


@dataclass(frozen=True)
class YouTubeUploadSettings:
    """YouTube API upload and categorization settings.

    Attributes:
        category_id: YouTube video category identifier (24 = Entertainment).
        default_privacy_status: Initial visibility status on YouTube (private, unlisted, public).
        default_language: Default language tag for metadata.
        notify_subscribers: Whether subscribers receive notifications upon publishing.
        self_declared_made_for_kids: Compliance flag for COPPA.
    """

    category_id: int = 24  # Entertainment
    default_privacy_status: str = "private"
    default_language: str = "en"
    notify_subscribers: bool = True
    self_declared_made_for_kids: bool = False


@dataclass(frozen=True)
class SEOSettings:
    """Metadata and search engine optimization settings for generated content.

    Attributes:
        max_title_length: Maximum allowed characters in a YouTube video title.
        max_description_length: Maximum allowed characters in video descriptions.
        max_tags: Maximum number of tags allowed per upload.
        max_tags_length: Maximum total character count for all tags combined.
        default_tags: Baseline list of tags included across channel uploads.
        hashtag_count: Target number of hashtags to append to descriptions.
    """

    max_title_length: int = 100
    max_description_length: int = 5000
    max_tags: int = 20
    max_tags_length: int = 500
    default_tags: List[str] = field(
        default_factory=lambda: [
            "reddit",
            "reddit stories",
            "storytime",
            "askreddit",
            "reddit readings",
            "viral",
        ]
    )
    hashtag_count: int = 3


@dataclass(frozen=True)
class ChannelConfig:
    """Target YouTube channel configuration for a specific language.

    Attributes:
        channel_id_key: Identifier key for the channel.
        language: Language name ('english' or 'hindi').
        language_code: ISO 639-1 language code ('en' or 'hi').
        default_voice: Default voice identifier used for narration.
        refresh_token: YouTube OAuth refresh token for authentication.
        seo_tags: Language-specific SEO tags.
        title_prefix: Optional prefix for generated video titles.
    """

    channel_id_key: str
    language: str
    language_code: str
    default_voice: str
    refresh_token: Optional[str]
    seo_tags: List[str] = field(default_factory=list)
    title_prefix: str = ""


# ==============================================================================
# Instantiated Global Configurations
# ==============================================================================

STORY_CRITERIA = StorySelectionCriteria(
    min_upvotes=1000,
    min_words=500,
    max_words=5000,
)

REDDIT_CONFIG = RedditConfig(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    subreddits=[
        "nosleep",
        "creepy",
        "AmItheAsshole",
        "ProRevenge",
        "entitledparents",
        "relationship_advice",
        "tifu",
    ],
    story_criteria=STORY_CRITERIA,
)

VOICE_CONFIG = VoiceConfig(
    english=EnglishVoiceConfig(
        narrator="en-US-GuyNeural",
        narrator_female="en-US-JennyNeural",
        young_male="en-US-ChristopherNeural",
        young_female="en-US-AriaNeural",
        villain="en-US-DavisNeural",
        child="en-US-AnaNeural",
    ),
    hindi=HindiVoiceConfig(
        narrator="hi-IN-MadhurNeural",
        narrator_female="hi-IN-SwaraNeural",
    ),
)

VIDEO_SETTINGS = VideoSettings(
    long_form_duration_range=(480, 900),
    shorts_max_duration=59,
    resolution_landscape="1920x1080",
    resolution_portrait="1080x1920",
    fps=30,
    video_codec="libx264",
    audio_codec="aac",
    audio_bitrate="192k",
)

YOUTUBE_SETTINGS = YouTubeUploadSettings(
    category_id=24,
    default_privacy_status="private",
    default_language="en",
    notify_subscribers=True,
    self_declared_made_for_kids=False,
)

SEO_SETTINGS = SEOSettings(
    max_title_length=100,
    max_description_length=5000,
    max_tags=20,
    max_tags_length=500,
    default_tags=[
        "reddit",
        "reddit stories",
        "storytime",
        "askreddit",
        "reddit readings",
        "viral",
    ],
    hashtag_count=3,
)

CHANNEL_CONFIGS: Dict[str, ChannelConfig] = {
    "english": ChannelConfig(
        channel_id_key="english",
        language="english",
        language_code="en",
        default_voice=VOICE_CONFIG.english.narrator,
        refresh_token=YT_EN_REFRESH_TOKEN,
        seo_tags=["reddit tales", "reddit confessions", "scary reddit stories"],
        title_prefix="",
    ),
    "hindi": ChannelConfig(
        channel_id_key="hindi",
        language="hindi",
        language_code="hi",
        default_voice=VOICE_CONFIG.hindi.narrator,
        refresh_token=YT_HI_REFRESH_TOKEN,
        seo_tags=["reddit kahaniya", "hindi stories", "hindi horror stories"],
        title_prefix="",
    ),
}


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_channel_config(language: str) -> ChannelConfig:
    """Retrieve channel configuration by language key.

    Args:
        language: Language key ('english' or 'hindi').

    Returns:
        ChannelConfig for the specified language.

    Raises:
        KeyError: If language is not configured in CHANNEL_CONFIGS.
    """
    key = language.strip().lower()
    if key not in CHANNEL_CONFIGS:
        raise KeyError(
            f"Unsupported channel language: {language}. Available options: {list(CHANNEL_CONFIGS.keys())}"
        )
    return CHANNEL_CONFIGS[key]


def validate_environment() -> Dict[str, bool]:
    """Check availability of required third-party API credentials in the environment.

    Returns:
        A dictionary mapping credential names to a boolean indicating if they are set.
    """
    status: Dict[str, bool] = {
        "REDDIT_CLIENT_ID": REDDIT_CLIENT_ID is not None,
        "REDDIT_CLIENT_SECRET": REDDIT_CLIENT_SECRET is not None,
        "GEMINI_API_KEY": GEMINI_API_KEY is not None,
        "YOUTUBE_CLIENT_ID": YOUTUBE_CLIENT_ID is not None,
        "YOUTUBE_CLIENT_SECRET": YOUTUBE_CLIENT_SECRET is not None,
        "YT_EN_REFRESH_TOKEN": YT_EN_REFRESH_TOKEN is not None,
        "YT_HI_REFRESH_TOKEN": YT_HI_REFRESH_TOKEN is not None,
        "R2_ACCESS_KEY": R2_ACCESS_KEY is not None,
        "R2_SECRET_KEY": R2_SECRET_KEY is not None,
    }
    return status
