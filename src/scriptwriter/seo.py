"""SEO & Metadata Generation Engine.

Generates high-CTR titles, mobile-optimized descriptions, tags, hashtags,
and short punchy thumbnail overlay text using strategic learning directives.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.config import SEO_SETTINGS
from src.evolution.learning_memory import StrategicLearningMemory

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Container for complete YouTube video metadata."""

    title: str
    description: str
    tags: List[str]
    hashtags: List[str]
    thumbnail_text: str  # 2-4 punchy words for thumbnail overlay
    category_id: int = 24  # Entertainment


class SEOGenerator:
    """Generates optimized metadata for YouTube long-form and Shorts uploads."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        memory: Optional[StrategicLearningMemory] = None,
    ) -> None:
        """Initialize SEO generator.

        Args:
            api_key: Gemini API key.
            memory: Learning memory instance for active SEO directives.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.memory = memory or StrategicLearningMemory()

    def generate_metadata(
        self,
        story: Dict[str, Any],
        category: str = "general",
        language: str = "english",
        is_shorts: bool = False,
    ) -> VideoMetadata:
        """Generate high-performing title, description, tags, and thumbnail text.

        Args:
            story: Reddit story dict.
            category: Genre/mood ('horror', 'drama', 'revenge', etc.).
            language: Target language ('english' or 'hindi').
            is_shorts: True if targeting Shorts format.

        Returns:
            VideoMetadata object ready for YouTube Data API.
        """
        raw_title = story.get("title", "")
        subreddit = story.get("subreddit", "")

        if self.api_key:
            try:
                return self._generate_with_gemini(raw_title, subreddit, category, language, is_shorts)
            except Exception as e:
                logger.warning(f"Gemini SEO generation error ({e}); using heuristic optimizer.")

        return self._generate_heuristic(raw_title, subreddit, category, language, is_shorts)

    def _generate_with_gemini(
        self,
        raw_title: str,
        subreddit: str,
        category: str,
        language: str,
        is_shorts: bool,
    ) -> VideoMetadata:
        """Generate metadata using Gemini LLM."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        directives = self.memory.get_seo_directives()
        directives_str = "\n".join(f"- {d}" for d in directives)

        prompt = f"""
You are a viral YouTube SEO specialist with deep expertise in Reddit story channels.
Create optimized metadata for this video:

ORIGINAL REDDIT TITLE: {raw_title}
SUBREDDIT: r/{subreddit}
CATEGORY: {category}
LANGUAGE: {language}
FORMAT: {"YouTube Shorts" if is_shorts else "Long-Form Video"}

STRATEGIC DIRECTIVES:
{directives_str}

REQUIREMENTS:
1. TITLE: 45 to 65 characters, intense curiosity gap, clean mobile formatting.
2. THUMBNAIL_TEXT: Exactly 2 to 4 bold, shocking words (e.g. "SHE REGRETTED THIS", "DON'T LOOK OUTSIDE", "CAUGHT RED HANDED").
3. DESCRIPTION: Engaging summary, call to action, and 3 hashtags.
4. TAGS: 12-15 relevant high-search keywords.

Return ONLY valid JSON:
{{
  "title": "string",
  "thumbnail_text": "string",
  "description": "string",
  "tags": ["string"],
  "hashtags": ["#string"]
}}
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text).strip()
        import json
        data = json.loads(text)

        title = data.get("title", raw_title)[:SEO_SETTINGS.max_title_length]
        if is_shorts and "#Shorts" not in title:
            title = f"{title} #Shorts"

        return VideoMetadata(
            title=title,
            description=data.get("description", "")[:SEO_SETTINGS.max_description_length],
            tags=data.get("tags", SEO_SETTINGS.default_tags)[:SEO_SETTINGS.max_tags],
            hashtags=data.get("hashtags", ["#redditstories", "#storytime", "#viral"])[:SEO_SETTINGS.hashtag_count],
            thumbnail_text=data.get("thumbnail_text", "UNBELIEVABLE")[:30],
        )

    def _generate_heuristic(
        self,
        raw_title: str,
        subreddit: str,
        category: str,
        language: str,
        is_shorts: bool,
    ) -> VideoMetadata:
        """Deterministic heuristic metadata generator."""
        # Clean title of Reddit specific jargon (e.g. [UPDATE], AITA, etc.)
        clean_title = re.sub(r"\[.*?\]|\(.*?\)", "", raw_title).strip()
        clean_title = re.sub(r"\s+", " ", clean_title)

        if len(clean_title) > 65:
            clean_title = clean_title[:62] + "..."

        if category == "horror":
            title = f"The Scariest Thing Happened: {clean_title}"
            thumb_text = "DON'T LOOK"
        elif category == "revenge":
            title = f"Entitled Person Demanded Everything: {clean_title}"
            thumb_text = "INSTANT REGRET"
        elif category == "drama":
            title = f"I Couldn't Believe What They Did: {clean_title}"
            thumb_text = "THEY CONFESSED"
        else:
            title = f"Unbelievable Reddit Story: {clean_title}"
            thumb_text = "WHAT HAPPENED"

        if len(title) > SEO_SETTINGS.max_title_length:
            title = title[:SEO_SETTINGS.max_title_length - 3] + "..."

        if is_shorts:
            title = f"{title[:85]} #Shorts"

        hashtags = ["#redditstories", f"#{category}", "#viral", "#shorts"] if is_shorts else ["#redditstories", f"#{category}", "#storytime"]

        description = (
            f"{title}\n\n"
            f"An incredible story from r/{subreddit}. What would you have done in this situation? "
            f"Share your thoughts in the comments below!\n\n"
            f"🔔 Subscribe for daily stories and updates.\n\n"
            f"{' '.join(hashtags)}"
        )

        tags = list(SEO_SETTINGS.default_tags) + [category, subreddit.lower(), "reddit confessions", "scary stories"]

        return VideoMetadata(
            title=title,
            description=description,
            tags=tags[:SEO_SETTINGS.max_tags],
            hashtags=hashtags[:SEO_SETTINGS.hashtag_count],
            thumbnail_text=thumb_text,
        )
