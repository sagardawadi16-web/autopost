"""AI Script Rewriter with Autonomous Reasoning and Revision Loop.

Transforms raw Reddit stories into high-retention video narration scripts.
Injects learned strategic directives and iteratively refines scripts
through the ContentEvaluator gatekeeper until quality standards are met.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from src.evolution.learning_memory import StrategicLearningMemory
from src.scriptwriter.evaluator import ContentEvaluator, EvaluationReport

logger = logging.getLogger(__name__)


class ScriptRewriter:
    """Transforms raw stories into scripted dialogues and enforces quality evaluation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        memory: Optional[StrategicLearningMemory] = None,
        evaluator: Optional[ContentEvaluator] = None,
    ) -> None:
        """Initialize script rewriter.

        Args:
            api_key: Gemini API key. Defaults to GEMINI_API_KEY environment variable.
            memory: Instance of StrategicLearningMemory for dynamic prompt injection.
            evaluator: Quality gatekeeper for auditing drafts.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.memory = memory or StrategicLearningMemory()
        self.evaluator = evaluator or ContentEvaluator(api_key=self.api_key)

    def rewrite_story(
        self,
        story: Dict[str, Any],
        language: str = "english",
        category: str = "general",
        max_revision_attempts: int = 3,
    ) -> Tuple[str, EvaluationReport]:
        """Rewrite a Reddit story into a production-ready script with an iterative critique loop.

        Args:
            story: Raw Reddit story dict containing 'title', 'body', 'subreddit', etc.
            language: Target language ('english' or 'hindi').
            category: Story genre/mood ('horror', 'drama', 'revenge', etc.).
            max_revision_attempts: Maximum self-correction iterations.

        Returns:
            Tuple of (final_script_text, evaluation_report).
        """
        directives = self.memory.get_rewriter_directives(category, language)
        title = story.get("title", "")
        raw_body = story.get("body", "")

        last_report: Optional[EvaluationReport] = None
        current_script = ""
        revisions_context: List[str] = []

        for attempt in range(1, max_revision_attempts + 1):
            logger.info(f"Generating script draft (attempt {attempt}/{max_revision_attempts})...")

            if self.api_key:
                try:
                    current_script = self._generate_with_gemini(
                        title=title,
                        body=raw_body,
                        category=category,
                        language=language,
                        directives=directives,
                        revisions_context=revisions_context,
                    )
                except Exception as e:
                    logger.warning(f"Gemini generation error: {e}. Falling back to structured heuristic formatter.")
                    current_script = self._generate_heuristic(title, raw_body, category, language)
            else:
                current_script = self._generate_heuristic(title, raw_body, category, language)

            # Audit draft with the Reasoning Content Gatekeeper
            last_report = self.evaluator.evaluate_script(
                title=title,
                script_text=current_script,
                category=category,
                is_shorts=False,
            )

            if last_report.is_approved:
                logger.info(f"Script approved on attempt {attempt}! Score: {last_report.overall_score}/10")
                break
            else:
                logger.warning(
                    f"Draft rejected on attempt {attempt}. Score: {last_report.overall_score}/10. "
                    f"Causes: {last_report.rejection_causes}. Revisions requested: {last_report.actionable_revisions}"
                )
                revisions_context = last_report.actionable_revisions

        return current_script, last_report

    def _generate_with_gemini(
        self,
        title: str,
        body: str,
        category: str,
        language: str,
        directives: List[str],
        revisions_context: List[str],
    ) -> str:
        """Call Gemini API to transform narrative with specific structural tags."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        directives_str = "\n".join(f"- {d}" for d in directives)
        revisions_str = ""
        if revisions_context:
            revisions_str = "\nCRITICAL FIXES FROM PREVIOUS REJECTION:\n" + "\n".join(f"- {r}" for r in revisions_context)

        system_instructions = f"""
You are an award-winning YouTube storyteller who adapts Reddit stories into viral narration videos.
Rewrite the story below into an immersive script.

GENRE: {category.upper()}
LANGUAGE: {language.upper()}
TITLE: {title}

ACTIVE STRATEGIC DIRECTIVES:
{directives_str}
{revisions_str}

FORMATTING REQUIREMENTS:
1. Every spoken paragraph MUST be tagged with the speaker identity:
   [NARRATOR] for main narrator
   [CHARACTER: Name/Role] for spoken dialogue
2. Write with intense suspense, vivid sensory details, and immediate tension.
3. Keep sentence structure accessible for Text-to-Speech narration.
4. Hook the audience in the opening two sentences.
"""

        prompt = f"""
ORIGINAL REDDIT STORY:
Title: {title}
Body:
{body[:5000]}

Generate the formatted script now:
"""

        response = model.generate_content([system_instructions, prompt])
        return response.text.strip()

    def _generate_heuristic(
        self,
        title: str,
        body: str,
        category: str,
        language: str,
    ) -> str:
        """Deterministic heuristic script formatter when operating offline or in dry-run mode."""
        lines = [f"[NARRATOR] {title}.\n"]

        # Insert a high-converting opening hook
        if category == "horror":
            lines.append("[NARRATOR] I never believed in the paranormal until what happened to me last month. If you are listening to this alone in the dark, turn on your lights right now.\n")
        elif category == "revenge":
            lines.append("[NARRATOR] She looked me dead in the eye and told me I was completely powerless. Little did she know, her arrogance was about to cost her everything.\n")
        elif category == "drama":
            lines.append("[NARRATOR] I never thought my own family would stab me in the back for money. But when the truth finally surfaced, nobody could defend what they did.\n")
        else:
            lines.append("[NARRATOR] You are not going to believe how this situation spiraled completely out of control.\n")

        # Format paragraphs and detect dialogue quotes
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        for para in paragraphs[:15]:
            # Simple heuristic detection of dialogue
            if '"' in para or '“' in para:
                parts = re.split(r'["“](.*?)["”]', para)
                for i, part in enumerate(parts):
                    part_clean = part.strip()
                    if not part_clean:
                        continue
                    if i % 2 == 1:
                        lines.append(f"[CHARACTER: Speaker] \"{part_clean}\"")
                    else:
                        lines.append(f"[NARRATOR] {part_clean}")
            else:
                lines.append(f"[NARRATOR] {para}")

        # Climax / conclusion
        lines.append("\n[NARRATOR] What would you have done in my situation? Leave your thoughts in the comments below, and don't forget to like and subscribe for more stories every single day.")

        return "\n\n".join(lines)
