"""Multi-Part Story Director & Sequencer.

Splits long narratives or creates sequel/follow-up scripts (Part 1 and Part 2)
specifically engineered for viral YouTube Shorts retention loops.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from src.scriptwriter.evaluator import ContentEvaluator, EvaluationReport
from src.scriptwriter.seo import SEOGenerator, VideoMetadata

logger = logging.getLogger(__name__)


@dataclass
class MultiPartStory:
    """Container for paired Part 1 and Part 2 YouTube Shorts content."""

    story_id: str
    part_1_script: str
    part_2_script: str
    part_1_title: str
    part_2_title: str
    part_1_metadata: VideoMetadata
    part_2_metadata: VideoMetadata
    part_1_eval: Optional[EvaluationReport] = None
    part_2_eval: Optional[EvaluationReport] = None


class MultiPartDirector:
    """Director that produces linked Part 1 and Part 2 Shorts with cliffhangers and payoffs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        evaluator: Optional[ContentEvaluator] = None,
        seo_generator: Optional[SEOGenerator] = None,
    ) -> None:
        """Initialize MultiPartDirector.

        Args:
            api_key: Gemini API key.
            evaluator: Quality evaluator instance.
            seo_generator: SEO metadata generator.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.evaluator = evaluator or ContentEvaluator(api_key=self.api_key)
        self.seo = seo_generator or SEOGenerator(api_key=self.api_key)

    def split_story_into_parts(
        self,
        story: Dict[str, Any],
        category: str = "general",
        language: str = "english",
    ) -> MultiPartStory:
        """Create a synchronized 2-Part story series from a single narrative.

        Args:
            story: Reddit/AI story dictionary.
            category: Story genre/mood ('drama', 'revenge', 'horror', etc.).
            language: Target language ('english' or 'hindi').

        Returns:
            MultiPartStory containing scripts, titles, and SEO for both parts.
        """
        raw_title = story.get("title", "Story")
        body = story.get("body", "")
        story_id = story.get("id", "multipart_story")

        if self.api_key:
            try:
                p1_script, p2_script = self._generate_two_parts_gemini(
                    raw_title, body, category, language
                )
            except Exception as e:
                logger.warning(f"Gemini multi-part generation failed ({e}); falling back to heuristic split.")
                p1_script, p2_script = self._generate_two_parts_heuristic(raw_title, body, category)
        else:
            p1_script, p2_script = self._generate_two_parts_heuristic(raw_title, body, category)

        # Generate metadata with Part 1 and Part 2 branding
        p1_meta = self.seo.generate_metadata(
            story=story,
            category=category,
            language=language,
            is_shorts=True,
            part_number=1,
            total_parts=2,
        )
        p2_meta = self.seo.generate_metadata(
            story=story,
            category=category,
            language=language,
            is_shorts=True,
            part_number=2,
            total_parts=2,
        )

        p1_eval = self.evaluator.evaluate_script(raw_title, p1_script, category, is_shorts=True)
        p2_eval = self.evaluator.evaluate_script(raw_title, p2_script, category, is_shorts=True)

        return MultiPartStory(
            story_id=story_id,
            part_1_script=p1_script,
            part_2_script=p2_script,
            part_1_title=p1_meta.title,
            part_2_title=p2_meta.title,
            part_1_metadata=p1_meta,
            part_2_metadata=p2_meta,
            part_1_eval=p1_eval,
            part_2_eval=p2_eval,
        )

    def generate_followup_for_existing_part1(
        self,
        part_1_text: str,
        title: str,
        category: str = "general",
        language: str = "english",
        story_id: str = "followup",
        full_context: Optional[str] = None,
    ) -> Tuple[str, VideoMetadata]:
        """Generate the Part 2 resolution script when Part 1 already exists.

        Args:
            part_1_text: The spoken narration or script of Part 1.
            title: Original story title.
            category: Story genre/category.
            language: Target language.
            story_id: Unique story ID.
            full_context: Optional background story context.

        Returns:
            Tuple of (part_2_script, part_2_metadata).
        """
        if self.api_key:
            try:
                p2_script = self._generate_followup_gemini(
                    title=title,
                    part_1_text=part_1_text,
                    category=category,
                    language=language,
                    context=full_context or "",
                )
            except Exception as e:
                logger.warning(f"Gemini followup generation failed ({e}); using heuristic resolution.")
                p2_script = self._generate_followup_heuristic(part_1_text, category)
        else:
            p2_script = self._generate_followup_heuristic(part_1_text, category)

        dummy_story = {"title": title, "body": full_context or part_1_text, "id": story_id}
        p2_meta = self.seo.generate_metadata(
            story=dummy_story,
            category=category,
            language=language,
            is_shorts=True,
            part_number=2,
            total_parts=2,
        )

        return p2_script, p2_meta

    def _generate_two_parts_gemini(
        self,
        title: str,
        body: str,
        category: str,
        language: str,
    ) -> Tuple[str, str]:
        """Generate Part 1 and Part 2 via Gemini."""
        from src.utils import call_gemini_with_fallback
        import json

        prompt = f"""
You are a viral YouTube Shorts script director. Split this story into an irresistible 2-Part Shorts series.

TITLE: {title}
CATEGORY: {category}
LANGUAGE: {language}

PART 1 REQUIREMENTS:
- 130 to 155 words (fits strictly under 55 seconds).
- Hook in first 3 seconds (instant conflict/stakes).
- Rising tension, ending on a cliffhanger so intense that viewers MUST watch Part 2.
- End with: "[NARRATOR] Follow and check the pinned comment for Part 2 right now!"
- Use speaker tags [NARRATOR] and [CHARACTER: Name].

PART 2 REQUIREMENTS:
- 130 to 155 words (fits strictly under 55 seconds).
- Starts with: "[NARRATOR] This is Part 2." then immediately resolves the climax.
- Massive emotional satisfaction, revenge karma, or shocking twist.
- Ends with: "[NARRATOR] Did I do the right thing? Let me know in the comments."
- Use speaker tags [NARRATOR] and [CHARACTER: Name].

ORIGINAL STORY:
{body[:3500]}

Respond ONLY with valid JSON:
{{
  "part_1": "...",
  "part_2": "..."
}}
"""
        response_text = call_gemini_with_fallback(prompt)
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text.strip(), flags=re.MULTILINE)
        data = json.loads(cleaned)
        return data["part_1"], data["part_2"]

    def _generate_followup_gemini(
        self,
        title: str,
        part_1_text: str,
        category: str,
        language: str,
        context: str,
    ) -> str:
        """Synthesize Part 2 to follow an existing Part 1 using Gemini."""
        from src.utils import call_gemini_with_fallback

        prompt = f"""
You are a viral YouTube Shorts script director. Write the official PART 2 (FINALE) for this viral Short.

ORIGINAL TITLE: {title}
CATEGORY: {category}
PART 1 TEXT:
{part_1_text}

ADDITIONAL CONTEXT (if any):
{context[:1500]}

PART 2 REQUIREMENTS:
1. WORD COUNT: Exactly 130 to 155 words (fits in under 55 seconds).
2. OPENING: Start with "[NARRATOR] Welcome back to Part 2." and immediately dive into the explosive aftermath.
3. STORY ARC: Complete resolution of the conflict from Part 1. Deliver devastating karma, legal consequences, or satisfying family fallout.
4. CLOSING: End with a thought-provoking moral question: "[NARRATOR] Was I wrong to do this? Tell me in the comments below."
5. FORMAT: Use [NARRATOR] and [CHARACTER: Name] tags for spoken lines.

Output ONLY the final Part 2 script text with speaker tags.
"""
        return call_gemini_with_fallback(prompt).strip()

    def _generate_two_parts_heuristic(
        self,
        title: str,
        body: str,
        category: str,
    ) -> Tuple[str, str]:
        """Heuristic splitting when Gemini is offline."""
        sentences = re.split(r"(?<=[.!?])\s+", body.strip())
        mid = max(3, len(sentences) // 2)

        part_1_sentences = sentences[:mid]
        part_2_sentences = sentences[mid:]

        p1_text = " ".join(part_1_sentences[:8])
        if len(p1_text.split()) > 140:
            p1_text = " ".join(p1_text.split()[:135])
        p1_text = f"[NARRATOR] {p1_text} What happened next changed everything. Follow for Part 2 right now!"

        p2_text = " ".join(part_2_sentences[:8])
        if len(p2_text.split()) > 140:
            p2_text = " ".join(p2_text.split()[:135])
        p2_text = f"[NARRATOR] This is Part 2. {p2_text} Did justice get served? Let me know in the comments."

        return p1_text, p2_text

    def _generate_followup_heuristic(
        self,
        part_1_text: str,
        category: str,
    ) -> str:
        """Deterministic fallback Part 2 script."""
        if category == "revenge":
            return (
                "[NARRATOR] Welcome back to Part 2. The fallout was swift and total. "
                "The next morning, I contacted our venue coordinator and locked down every single vendor with a password. "
                "When my sister tried to call them pretending to be me, they flagged the account and threatened legal action for fraud. "
                "At Sunday brunch, my parents sat in dead silence after listening to the full voicemails. "
                "My dad looked at Claire and said, 'You are paying for your own wedding, or you are not having one.' "
                "Claire was forced to book a local community hall, while our original dream wedding went ahead without a single hitch. "
                "Was I wrong for not giving in to her demands? Let me know in the comments below."
            )
        elif category == "horror":
            return (
                "[NARRATOR] Welcome back to Part 2. As the shadow stepped closer, I held my breath. "
                "The cold air smelled like damp earth. Suddenly, the flashlight beam flickered back to life, hitting the mirror directly. "
                "There was no intruder behind me. The reflection was smiling, but my real mouth was frozen in terror. "
                "I sprinted out the front door into the pouring rain and never went back inside that house again. "
                "The police investigated the next day and found the floorboards torn open from underneath. "
                "Would you have stayed to find out what it was? Tell me in the comments below."
            )
        else:
            return (
                "[NARRATOR] Welcome back to Part 2. After the confrontation, the truth finally came out. "
                "The family tried to pressure me into backing down, but I showed everyone the evidence. "
                "Within forty-eight hours, the entire family realized who was really in the wrong. "
                "Claire was left with no choice but to apologize publicly, and my parents finally admitted they had enabled her for too long. "
                "Now, boundaries are firmly set, and I haven't heard a single complaint since. "
                "Did I handle this the right way? Tell me what you think in the comments below."
            )
