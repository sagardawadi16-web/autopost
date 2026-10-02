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

FILLER = {"basically", "actually", "literally", "just", "really", "very", "so", "kind", "sort", "like", "guys", "hey", "welcome", "today", "video", "subscribe", "channel"}
VAGUE = {"amazing", "incredible", "insane", "crazy", "huge", "massive", "game", "changer", "secret", "powerful", "ultimate", "best", "revolutionary", "mind", "blowing", "unbelievable"}
CONCRETE = re.compile(r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b", re.I)
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I)
STAKE = re.compile(r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b", re.I)
CURIOSITY = re.compile(r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b", re.I)

FIX_SUGGESTIONS = {
    "SPECIFICITY": "swap vague adjectives for concrete figures, names, or dates",
    "ADDRESS": "say 'you' or 'your' in the first 6 words",
    "STAKES": "name what it costs to ignore or misjudge this situation",
    "CURIOSITY": "cut the portion of the sentence that answers itself",
    "BREVITY": "keep hook length strictly between 9 and 24 words",
}


def score_hook(text: str) -> tuple[dict, int, str]:
    """Score a hook on 5 properties (0-100 each) and compute a weighted verdict."""
    w = re.findall(r"[a-z0-9'%$.]+", text.lower())
    if not w:
        return {"SPECIFICITY": 0, "ADDRESS": 0, "STAKES": 0, "CURIOSITY": 0, "BREVITY": 0}, 0, "BREVITY"

    # Specificity
    nums = len(CONCRETE.findall(text))
    vague_cnt = sum(1 for x in w if x in VAGUE)
    filler_cnt = sum(1 for x in w if x in FILLER)
    spec = max(0, min(100, 34 + nums * 22 - vague_cnt * 16 - filler_cnt * 5))

    # Address
    you_cnt = len(YOU.findall(text))
    first_you = 30 if YOU.search(" ".join(text.split()[:6])) else 0
    addr = max(0, min(100, 26 + you_cnt * 20 + first_you))

    # Stakes
    stake_cnt = len(STAKE.findall(text))
    stk = max(0, min(100, 22 + stake_cnt * 26 + (14 if CONCRETE.search(text) else 0)))

    # Curiosity
    cur_cnt = len(CURIOSITY.findall(text))
    q = 18 if text.strip().endswith("?") else 0
    closed = -18 if re.search(r"\b(because|so that|which means)\b", text, re.I) else 0
    cur = max(0, min(100, 24 + cur_cnt * 17 + q + closed))

    # Brevity
    n_words = len(w)
    if 9 <= n_words <= 24:
        brev = 100
    elif n_words < 9:
        brev = max(30, 100 - (9 - n_words) * 11)
    else:
        brev = max(10, 100 - (n_words - 24) * 7)

    parts = {"SPECIFICITY": spec, "ADDRESS": addr, "STAKES": stk, "CURIOSITY": cur, "BREVITY": brev}
    vals = list(parts.values())
    verdict = round(0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals))
    weakest = min(parts, key=parts.get)
    return parts, verdict, weakest


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

        # 2. Hook Analysis via yt-script hookscore algorithm
        first_sentence = paragraphs[0] if paragraphs else script_text[:150]
        # Remove speaker tags for hook evaluation
        clean_first_sentence = re.sub(r"\[.*?\]", "", first_sentence).strip()
        hook_parts, hook_verdict_100, weakest_prop = score_hook(clean_first_sentence)
        hook_score = round(hook_verdict_100 / 10.0, 1)

        reasoning.append(f"HookScore: {hook_verdict_100}/100 ({hook_parts}). Weakest property: {weakest_prop}.")
        if hook_verdict_100 < 60:
            fix_tip = FIX_SUGGESTIONS.get(weakest_prop, "strengthen opening tension")
            revisions.append(f"Hook score is weak ({hook_verdict_100}/100). Fix {weakest_prop}: {fix_tip}.")
        else:
            reasoning.append(f"Hook is strong ({hook_verdict_100}/100) with clear retention pull.")

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
