"""Shorts Extractor and Script Condenser.

Extracts the most dramatic, high-tension 50-58 second narrative excerpts from stories
specifically engineered for vertical YouTube Shorts.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Optional, Tuple

from src.scriptwriter.evaluator import ContentEvaluator, EvaluationReport

logger = logging.getLogger(__name__)


class ShortsExtractor:
    """Condenses long stories into high-impact 60-second YouTube Shorts scripts."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        evaluator: Optional[ContentEvaluator] = None,
    ) -> None:
        """Initialize Shorts extractor.

        Args:
            api_key: Gemini API key.
            evaluator: Quality evaluator instance.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.evaluator = evaluator or ContentEvaluator(api_key=self.api_key)

    def extract_shorts_script(
        self,
        story: Dict[str, Any],
        category: str = "general",
        language: str = "english",
    ) -> Tuple[str, EvaluationReport]:
        """Generate a punchy 50-58 second Shorts script with speaker tags.

        Target word count: 125-165 words (~48-55 seconds spoken duration).

        Args:
            story: Reddit story dict.
            category: Genre/mood.
            language: Language ('english' or 'hindi').

        Returns:
            Tuple of (shorts_script, evaluation_report).
        """
        title = story.get("title", "")
        body = story.get("body", "")

        if self.api_key:
            try:
                shorts_text = self._extract_with_gemini(title, body, category, language)
            except Exception as e:
                logger.warning(f"Shorts generation error ({e}); using heuristic condenser.")
                shorts_text = self._extract_heuristic(title, body, category)
        else:
            shorts_text = self._extract_heuristic(title, body, category)

        report = self.evaluator.evaluate_script(
            title=title,
            script_text=shorts_text,
            category=category,
            is_shorts=True,
        )

        return shorts_text, report

    def _extract_with_gemini(
        self,
        title: str,
        body: str,
        category: str,
        language: str,
    ) -> str:
        """Call Gemini to condense the narrative into a viral vertical Short."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
You are an expert viral YouTube Shorts producer. Condense the following story into an intense 50-second Short.

TITLE: {title}
CATEGORY: {category}
LANGUAGE: {language}

CRITICAL CONSTRAINTS:
1. WORD COUNT: Exactly 130 to 160 words. No more, no less. (Must fit in under 58 seconds).
2. FIRST 3 SECONDS: Start with a devastating or shocking hook sentence.
3. STRUCTURE: Hook -> Rapid Escalation -> Shocking Climax -> Cliffhanger Question.
4. TAGS: Use [NARRATOR] and [CHARACTER: Name] tags for spoken lines.

STORY TEXT:
{body[:3500]}

Generate the Shorts script now:
"""
        response = model.generate_content(prompt)
        return response.text.strip()

    def _extract_heuristic(self, title: str, body: str, category: str) -> str:
        """Deterministic heuristic condenser targeting ~140 words."""
        # Grab first 2 sentences and last 2 sentences
        sentences = re.split(r'(?<=[.!?])\s+', body.replace("\n", " "))
        selected = []

        # Hook
        if category == "horror":
            selected.append("[NARRATOR] You will never look at your closet the same way after hearing this.")
        elif category == "revenge":
            selected.append("[NARRATOR] This entitled bully thought they got away with ruining my life.")
        else:
            selected.append("[NARRATOR] I still cannot believe this actually happened.")

        # Story body
        for s in sentences:
            if len(" ".join(selected).split()) >= 110:
                break
            s_clean = s.strip()
            if s_clean and len(s_clean) > 15:
                selected.append(f"[NARRATOR] {s_clean}")

        # Climax / Call to action
        selected.append("[NARRATOR] Would you have forgiven them? Subscribe for part two.")

        return "\n\n".join(selected)
