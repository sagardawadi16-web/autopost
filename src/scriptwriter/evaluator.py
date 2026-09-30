"""Content Evaluator and Quality Gatekeeper.

Performs reasoning-driven evaluation of video scripts, titles, and hooks before
allowing them into audio/video rendering and upload pipelines.
Filters out low-retention, boring, or unsafe content.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvaluationReport:
    """Detailed audit report produced by the reasoning evaluator."""

    is_approved: bool
    overall_score: float  # Scale 0 to 10
    hook_score: float     # Scale 0 to 10
    pacing_score: float   # Scale 0 to 10
    payoff_score: float   # Scale 0 to 10
    safety_passed: bool
    reasoning: List[str] = field(default_factory=list)
    rejection_causes: List[str] = field(default_factory=list)
    actionable_revisions: List[str] = field(default_factory=list)


class ContentEvaluator:
    """Reasoning critic that audits scripts and decides what goes on the channel."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        min_passing_score: float = 7.2,
    ) -> None:
        """Initialize content evaluator.

        Args:
            api_key: Gemini API key (optional). If omitted, uses heuristic reasoning engine.
            min_passing_score: Minimum composite score (0-10) required to approve a script.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.min_passing_score = min_passing_score

    def evaluate_script(
        self,
        title: str,
        script_text: str,
        category: str,
        is_shorts: bool = False,
    ) -> EvaluationReport:
        """Evaluate a candidate script and determine whether it goes on the channel.

        Args:
            title: Candidate YouTube title.
            script_text: Full formatted script (including dialogue/narrator segments).
            category: Story genre/mood.
            is_shorts: Whether this is destined for YouTube Shorts (< 60s).

        Returns:
            EvaluationReport with approval status and reasoning.
        """
        # If Gemini API key is available, use LLM reasoning critic
        if self.api_key:
            try:
                return self._evaluate_with_llm(title, script_text, category, is_shorts)
            except Exception as e:
                logger.warning(f"LLM evaluation encountered an error ({e}); using heuristic reasoner.")

        # Fallback to robust deterministic heuristic reasoning
        return self._evaluate_with_heuristics(title, script_text, category, is_shorts)

    def _evaluate_with_heuristics(
        self,
        title: str,
        script_text: str,
        category: str,
        is_shorts: bool,
    ) -> EvaluationReport:
        """Deterministic heuristic analysis when external LLM is offline or in dry-run mode."""
        reasoning: List[str] = []
        rejections: List[str] = []
        revisions: List[str] = []

        words = script_text.split()
        word_count = len(words)
        paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
        opening_50_words = " ".join(words[:50]).lower()

        # 1. Safety check
        banned_terms = ["kill myself", "suicide", "child abuse", "doxxed", "bomb threat"]
        safety_passed = True
        for term in banned_terms:
            if term in script_text.lower():
                safety_passed = False
                rejections.append(f"Safety violation: Contains dangerous keyword '{term}'.")
                break

        # 2. Hook Analysis
        hook_score = 7.0
        strong_hook_words = [
            "never", "mistake", "regret", "warning", "secret", "horror",
            "screaming", "caught", "trapped", "ruined", "threatened", "confession",
            "worst", "shocked", "discovered"
        ]
        hook_matches = sum(1 for w in strong_hook_words if w in opening_50_words)

        if hook_matches >= 3:
            hook_score = 9.0
            reasoning.append("Hook contains high-urgency curiosity triggers in the first 50 words.")
        elif hook_matches >= 1:
            hook_score = 7.8
            reasoning.append("Hook has acceptable curiosity elements but could be sharper.")
        else:
            hook_score = 5.0
            reasoning.append("Opening lacks immediate drama; risks viewer bounce in first 5 seconds.")
            revisions.append("Rewrite the first sentence to present the core shock or dilemma immediately.")

        # 3. Pacing & Length Check
        pacing_score = 8.0
        if is_shorts:
            # Optimal Shorts length: 130 - 170 words (~45 - 56 seconds at 155 WPM)
            if word_count < 90:
                pacing_score -= 3.0
                rejections.append("Shorts script too brief (< 90 words); underutilizes runtime.")
            elif word_count > 185:
                pacing_score -= 3.5
                rejections.append(f"Shorts script too long ({word_count} words); will exceed 59-second cutoff.")
                revisions.append("Condense script by eliminating transitional fluff and non-essential dialogue.")
            else:
                reasoning.append(f"Word count ({word_count} words) is optimal for Shorts pacing.")
        else:
            # Long-form: 1000 - 2500 words (~7 - 16 minutes)
            if word_count < 600:
                pacing_score -= 2.0
                reasoning.append("Script is somewhat short for long-form mid-roll monetization.")
            elif word_count > 3500:
                pacing_score -= 2.0
                revisions.append("Pacing is overly expansive; trim secondary subplots to sustain tension.")
            else:
                reasoning.append(f"Word count ({word_count} words) provides healthy retention potential.")

        # 4. Payoff / Climax Check
        payoff_score = 7.5
        climax_indicators = ["finally", "turns out", "revealed", "aftermath", "lesson", "police", "justice", "truth"]
        last_100_words = " ".join(words[-100:]).lower() if len(words) >= 100 else opening_50_words
        if any(c in last_100_words for c in climax_indicators):
            payoff_score = 8.8
            reasoning.append("Ending delivers a conclusive emotional resolution or lingering shock.")
        else:
            payoff_score = 6.2
            revisions.append("Strengthen conclusion to deliver a stronger emotional punch or twist.")

        # Title CTR Analysis
        title_length = len(title)
        if 35 <= title_length <= 75:
            reasoning.append(f"Title length ({title_length} chars) is well-optimized for mobile feeds.")
        else:
            reasoning.append(f"Title length ({title_length} chars) may suffer truncation or lack detail.")
            revisions.append("Adjust title length between 40 and 70 characters.")

        # Compute overall score
        overall_score = round((hook_score * 0.40) + (pacing_score * 0.35) + (payoff_score * 0.25), 2)
        is_approved = safety_passed and (overall_score >= self.min_passing_score) and (len(rejections) == 0)

        if not is_approved:
            reasoning.append(f"GATEKEEPER VERDICT: REJECTED (Score: {overall_score}/{self.min_passing_score}). Script does not meet channel quality thresholds.")
        else:
            reasoning.append(f"GATEKEEPER VERDICT: APPROVED (Score: {overall_score}/10). High-conviction piece approved for production.")

        return EvaluationReport(
            is_approved=is_approved,
            overall_score=overall_score,
            hook_score=hook_score,
            pacing_score=pacing_score,
            payoff_score=payoff_score,
            safety_passed=safety_passed,
            reasoning=reasoning,
            rejection_causes=rejections,
            actionable_revisions=revisions,
        )

    def _evaluate_with_llm(
        self,
        title: str,
        script_text: str,
        category: str,
        is_shorts: bool,
    ) -> EvaluationReport:
        """Utilize Gemini LLM to execute structured editorial reasoning."""
        from src.utils import call_gemini_with_fallback

        prompt = f"""
You are the Executive Editorial Director and Chief Algorithm Strategist of a viral YouTube network.
Audit the following candidate video script with ruthless precision.

CATEGORY: {category}
TARGET FORMAT: {"YouTube Shorts (< 60s)" if is_shorts else "Long-Form Video (8-15 min)"}
TITLE: {title}

SCRIPT CONTENT:
\"\"\"
{script_text[:4000]}
\"\"\"

Critique this submission on:
1. First 5-second Hook Retention (Is it irresistible or does it drag?)
2. Narrative Pacing & Tension Maintenance
3. Emotional Payoff/Climax
4. YouTube Policy & Advertiser-Friendliness

Return ONLY valid JSON matching this schema:
{{
  "is_approved": boolean,
  "overall_score": float (0.0 to 10.0),
  "hook_score": float (0.0 to 10.0),
  "pacing_score": float (0.0 to 10.0),
  "payoff_score": float (0.0 to 10.0),
  "safety_passed": boolean,
  "reasoning": [string],
  "rejection_causes": [string],
  "actionable_revisions": [string]
}}
"""
        text = call_gemini_with_fallback(prompt=prompt, api_key=self.api_key)
        # Clean markdown codeblocks
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text).strip()
        data = json.loads(text)

        return EvaluationReport(
            is_approved=data.get("is_approved", False) and data.get("overall_score", 0) >= self.min_passing_score,
            overall_score=float(data.get("overall_score", 5.0)),
            hook_score=float(data.get("hook_score", 5.0)),
            pacing_score=float(data.get("pacing_score", 5.0)),
            payoff_score=float(data.get("payoff_score", 5.0)),
            safety_passed=bool(data.get("safety_passed", True)),
            reasoning=data.get("reasoning", []),
            rejection_causes=data.get("rejection_causes", []),
            actionable_revisions=data.get("actionable_revisions", []),
        )
