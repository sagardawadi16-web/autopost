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
        part_number: Optional[int] = None,
        total_parts: Optional[int] = None,
    ) -> VideoMetadata:
        """Generate high-performing title, description, tags, and thumbnail text.

        Args:
            story: Reddit story dict.
            category: Genre/mood ('horror', 'drama', 'revenge', etc.).
            language: Target language ('english' or 'hindi').
            is_shorts: True if targeting Shorts format.
            part_number: Optional 1 or 2 for multi-part series.
            total_parts: Total parts in series.

        Returns:
            VideoMetadata object ready for YouTube Data API.
        """
        raw_title = story.get("title", "")
        subreddit = story.get("subreddit", "")

        if self.api_key:
            try:
                return self._generate_with_gemini(
                    raw_title, subreddit, category, language, is_shorts, part_number, total_parts
                )
            except Exception as e:
                logger.warning(f"Gemini SEO generation error ({e}); using heuristic optimizer.")

        return self._generate_heuristic(
            raw_title, subreddit, category, language, is_shorts, part_number, total_parts
        )

    def _generate_with_gemini(
        self,
        raw_title: str,
        subreddit: str,
        category: str,
        language: str,
        is_shorts: bool,
        part_number: Optional[int] = None,
        total_parts: Optional[int] = None,
    ) -> VideoMetadata:
        """Generate metadata using Gemini LLM."""
        from src.utils import call_gemini_with_fallback

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
        text = call_gemini_with_fallback(prompt=prompt, api_key=self.api_key)
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text).strip()
        import json
        title = data.get("title", raw_title)[:SEO_SETTINGS.max_title_length]

        if part_number is not None:
            part_tag = f"[Part {part_number}]" if not total_parts else f"[Part {part_number}/{total_parts}]"
            if "part" not in title.lower():
                title = f"{title} {part_tag}"

        if is_shorts and "#Shorts" not in title:
            title = f"{title[:85]} #Shorts"

        thumb_text = data.get("thumbnail_text", "UNBELIEVABLE")[:30]
        if part_number is not None:
            thumb_text = f"PART {part_number}"

        followup_note = ""
        if part_number == 1:
            followup_note = "👉 Part 1 of 2. Subscribe and check the pinned comment for Part 2!\n\n"
        elif part_number == 2:
            followup_note = "⚡ Part 2 (Conclusion)! Watch Part 1 on our channel if you missed the setup.\n\n"

        description = f"{followup_note}{data.get('description', '')}"[:SEO_SETTINGS.max_description_length]

        tags = data.get("tags", list(SEO_SETTINGS.default_tags))[:SEO_SETTINGS.max_tags]
        if part_number:
            tags.extend([f"part {part_number}", "part 1", "part 2", "series"])

        return VideoMetadata(
            title=title,
            description=description,
            tags=tags[:SEO_SETTINGS.max_tags],
            hashtags=data.get("hashtags", ["#redditstories", "#storytime", "#viral"])[:SEO_SETTINGS.hashtag_count],
            thumbnail_text=thumb_text,
        )

    def _generate_heuristic(
        self,
        raw_title: str,
        subreddit: str,
        category: str,
        language: str,
        is_shorts: bool,
        part_number: Optional[int] = None,
        total_parts: Optional[int] = None,
    ) -> VideoMetadata:
        """Deterministic heuristic metadata generator."""
        # Clean title of Reddit specific jargon (e.g. [UPDATE], AITA, etc.)
        clean_title = re.sub(r"\[.*?\]|\(.*?\)", "", raw_title).strip()
        clean_title = re.sub(r"\s+", " ", clean_title)

        if len(clean_title) > 60:
            clean_title = clean_title[:57] + "..."

        if category == "horror":
            base = f"The Scariest Thing Happened: {clean_title}"
            thumb_text = "DON'T LOOK"
        elif category == "revenge":
            base = f"Entitled Person Demanded Everything: {clean_title}"
            thumb_text = "INSTANT REGRET"
        elif category == "drama":
            base = f"I Couldn't Believe What They Did: {clean_title}"
            thumb_text = "THEY CONFESSED"
        else:
            base = f"Unbelievable Reddit Story: {clean_title}"
            thumb_text = "WHAT HAPPENED"

        part_tag = f"[Part {part_number}]" if part_number else ""
        shorts_tag = "#Shorts" if is_shorts else ""

        # Reserve space for part_tag and shorts_tag so they are never truncated
        tags_overhead = len(f" {part_tag} {shorts_tag}".strip())
        max_base_len = max(30, 85 - tags_overhead)
        if len(base) > max_base_len:
            base = base[:max_base_len - 3].rstrip() + "..."

        title_parts = [base]
        if part_tag:
            title_parts.append(part_tag)
            thumb_text = f"PART {part_number}"
        if shorts_tag:
            title_parts.append(shorts_tag)

        title = " ".join(title_parts)

        hashtags = ["#redditstories", f"#{category}", "#viral", "#shorts"] if is_shorts else ["#redditstories", f"#{category}", "#storytime"]

        followup_note = ""
        if part_number == 1:
            followup_note = "👉 Part 1 of 2. Subscribe and check the pinned comment for Part 2!\n\n"
        elif part_number == 2:
            followup_note = "⚡ Part 2 (Conclusion)! Watch Part 1 on our channel if you missed the setup.\n\n"

        description = (
            f"{title}\n\n"
            f"{followup_note}"
            f"An incredible story from r/{subreddit}. What would you have done in this situation? "
            f"Share your thoughts in the comments below!\n\n"
            f"🔔 Subscribe for daily stories and updates.\n\n"
            f"{' '.join(hashtags)}"
        )

        tags = list(SEO_SETTINGS.default_tags) + [category, subreddit.lower(), "reddit confessions", "scary stories"]
        if part_number:
            tags.extend([f"part {part_number}", "part 1", "part 2", "series"])

        return VideoMetadata(
            title=title,
            description=description,
            tags=tags[:SEO_SETTINGS.max_tags],
            hashtags=hashtags[:SEO_SETTINGS.hashtag_count],
            thumbnail_text=thumb_text,
        )
