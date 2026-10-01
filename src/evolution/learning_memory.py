"""Persistent learning and reasoning memory for continuous channel optimization.

Tracks performance metrics, audience retention signals, and strategic reasoning
to autonomously evolve prompts, story selection criteria, thumbnails, and pacing.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


DEFAULT_INITIAL_STRATEGY: Dict[str, Any] = {
    "version": "1.0.0",
    "last_updated": datetime.now(timezone.utc).isoformat(),
    "niche_weights": {
        "nosleep": 1.25,
        "creepy": 1.15,
        "ProRevenge": 1.40,
        "AmItheAsshole": 1.35,
        "entitledparents": 1.20,
        "relationship_advice": 1.10,
        "tifu": 1.05,
    },
    "winning_hook_patterns": [
        "Shock confession opener (e.g. 'I shouldn't be posting this, but...')",
        "Direct stakes confrontation (e.g. 'She thought she could ruin my life. She was wrong.')",
        "Eerie sensory mystery (e.g. 'Every night at 3:17 AM, my basement door clicks unlocked.')",
        "Immediate moral dilemma (e.g. 'My sister demanded I give her my inheritance. Here is what I did instead.')",
    ],
    "failing_patterns": [
        "Long introductory backstory without immediate conflict in first 5 seconds.",
        "Monotone robotic pacing without pitch modulation.",
        "Unclear or cluttered thumbnails with more than 4 words.",
        "Overly complex vocabulary that reduces casual listening accessibility.",
    ],
    "winning_thumbnail_styles": {
        "horror": {
            "dominant_color": "crimson_and_black",
            "contrast_accent": "bright_yellow",
            "max_words": 3,
            "badge_text": "DON'T WATCH ALONE",
        },
        "drama": {
            "dominant_color": "dark_purple_and_black",
            "contrast_accent": "neon_green",
            "max_words": 4,
            "badge_text": "INSTANT REGRET",
        },
        "revenge": {
            "dominant_color": "deep_navy_and_gold",
            "contrast_accent": "blazing_red",
            "max_words": 3,
            "badge_text": "SWEET REVENGE",
        },
    },
    "optimal_pacing": {
        "english_wpm": 155,
        "hindi_wpm": 140,
        "shorts_target_seconds": 54,
        "longform_target_minutes": 9.5,
        "cliffhanger_frequency_seconds": 120,
    },
    "experiment_history": [
        {
            "id": "exp_001_baseline",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hypothesis": "High-conflict ProRevenge and AITA stories generate superior early retention over slow-burn horror on Shorts.",
            "observation": "Audience drops off within 4 seconds if stakes aren't stated in sentence 1.",
            "reasoning": "Mobile viewers need instant context and strong emotional polarity (heroes vs villains) to pause scrolling.",
            "rule_added": "Always rewrite paragraph 1 to plunge straight into climax/conflict before revealing backstory.",
            "confidence_score": 0.88,
        }
    ],
    "channel_stats_summary": {
        "total_analyzed_videos": 0,
        "avg_ctr_percent": 6.8,
        "avg_retention_percent": 62.5,
        "top_performing_category": "revenge",
    },
}


class StrategicLearningMemory:
    """Manages persistent evolution memory, reasoning history, and dynamic directives."""

    def __init__(self, memory_path: Optional[Path] = None) -> None:
        """Initialize learning memory.

        Args:
            memory_path: Path to the JSON persistence file. Defaults to data/learning_memory.json.
        """
        if memory_path is None:
            from src.config import DATA_DIR
            self._path = DATA_DIR / "learning_memory.json"
        else:
            self._path = Path(memory_path)

        self._lock = threading.Lock()
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load memory from file or initialize with defaults."""
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._save(DEFAULT_INITIAL_STRATEGY)
            return dict(DEFAULT_INITIAL_STRATEGY)

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Loaded strategic learning memory successfully")
            return data
        except Exception as e:
            logger.error(f"Error loading learning memory: {e}. Falling back to default.")
            return dict(DEFAULT_INITIAL_STRATEGY)

    def _save(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Persist memory to disk safely."""
        if data is None:
            data = self._data

        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to persist learning memory: {e}")

    def record_reasoning_experiment(
        self,
        hypothesis: str,
        observation: str,
        reasoning: str,
        rule_added: str,
        confidence_score: float = 0.85,
    ) -> str:
        """Record an explicit reasoning step into evolution history.

        Args:
            hypothesis: What we tested or assumed.
            observation: What occurred in analytics or review.
            reasoning: Why it occurred (deduction/induction).
            rule_added: The concrete instruction added to future generation.
            confidence_score: Confidence level between 0.0 and 1.0.

        Returns:
            Experiment ID.
        """
        with self._lock:
            history = self._data.setdefault("experiment_history", [])
            exp_id = f"exp_{len(history) + 1:03d}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
            record = {
                "id": exp_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hypothesis": hypothesis,
                "observation": observation,
                "reasoning": reasoning,
                "rule_added": rule_added,
                "confidence_score": max(0.0, min(1.0, confidence_score)),
            }
            history.append(record)

            # Also maintain active winning patterns or rules
            winning = self._data.setdefault("winning_hook_patterns", [])
            if rule_added not in winning:
                winning.append(rule_added)

            self._save()
            logger.info(f"Recorded new strategic reasoning entry: {exp_id} -> '{rule_added}'")
            return exp_id

    def update_niche_weight(self, subreddit: str, multiplier_delta: float) -> float:
        """Adjust weight of a subreddit/niche based on observed performance.

        Args:
            subreddit: Name of the subreddit.
            multiplier_delta: Positive or negative delta to apply (e.g. +0.05, -0.1).

        Returns:
            The newly updated weight.
        """
        with self._lock:
            weights = self._data.setdefault("niche_weights", {})
            current = weights.get(subreddit, 1.0)
            new_weight = max(0.2, min(3.0, current + multiplier_delta))
            weights[subreddit] = round(new_weight, 3)
            self._save()
            logger.info(f"Updated niche weight for {subreddit}: {current} -> {new_weight}")
            return new_weight

    def get_niche_weight(self, subreddit: str) -> float:
        """Get the current strategic weight for a subreddit."""
        with self._lock:
            return self._data.get("niche_weights", {}).get(subreddit, 1.0)

    def get_all_niche_weights(self) -> Dict[str, float]:
        """Get copy of all current niche weights."""
        with self._lock:
            return dict(self._data.get("niche_weights", {}))

    def get_rewriter_directives(self, category: str, language: str) -> List[str]:
        """Synthesize active, learned directives to inject into the AI scriptwriter prompt.

        Args:
            category: Story category ('horror', 'drama', 'revenge', etc.).
            language: Target language ('english' or 'hindi').

        Returns:
            List of imperative instructions for the LLM rewriter.
        """
        with self._lock:
            rules: List[str] = [
                "CRITICAL HOOK: Drop the audience directly into the heart of the crisis in the first 1-2 sentences. Avoid all slow setups.",
                "EMOTIONAL CONTRAST: Clearly establish relatable motivations and high emotional tension early on.",
                "CLIFFHANGERS: Insert micro-curiosity gaps or question prompts every 90-120 seconds.",
                "NATURAL DIALOGUE: Ensure character dialogue sounds authentic, conversational, and raw rather than staged.",
            ]

            # Append winning patterns
            for hook in self._data.get("winning_hook_patterns", [])[-3:]:
                rules.append(f"INCORPORATE HOOK TECHNIQUE: {hook}")

            # Append language specific instructions
            if language == "hindi":
                rules.append("HINDI ADAPTATION: Use natural, conversational Hinglish/Hindi phrasing that feels modern, dramatic, and captivating to Indian Gen-Z/Millennials.")
            else:
                rules.append("ENGLISH PACING: Maintain punchy, rhythmic sentences with strong verb usage.")

            return rules

    def get_seo_directives(self) -> List[str]:
        """Get learned rules for viral titles and CTR optimization."""
        with self._lock:
            return [
                "TITLE STRATEGY: Limit titles to 45-65 characters so they do not get truncated on mobile.",
                "EMOTIONAL HOOK: Use high-arousal curiosity triggers (e.g. 'The Worst Part Was What She Found', 'They Regretted Everything').",
                "CAPITALIZATION: Capitalize key shock words strategically for contrast.",
                "NO SPAM: Maintain high curiosity without violating YouTube clickbait policy.",
            ]

    def get_thumbnail_directives(self, category: str) -> Dict[str, Any]:
        """Get optimal visual attributes for thumbnail generation."""
        with self._lock:
            styles = self._data.get("winning_thumbnail_styles", {})
            return styles.get(category, styles.get("horror", {}))

    def record_voice_performance(
        self,
        voice_id: str,
        views: int,
        retention_pct: float,
        language: str = "english",
    ) -> None:
        """Update voice performance memory based on post-upload analytics."""
        with self._lock:
            voices = self._data.setdefault("voice_performance", {})
            current = voices.setdefault(voice_id, {
                "total_views": 0,
                "video_count": 0,
                "avg_retention_pct": 60.0,
                "language": language,
                "weight": 1.0,
            })
            current["total_views"] += views
            current["video_count"] += 1
            # Rolling average retention
            old_avg = current["avg_retention_pct"]
            current["avg_retention_pct"] = round((old_avg * (current["video_count"] - 1) + retention_pct) / current["video_count"], 1)

            # Evolve voice weight
            if current["avg_retention_pct"] >= 65.0:
                current["weight"] = round(min(2.5, current["weight"] + 0.1), 2)
            elif current["avg_retention_pct"] < 45.0:
                current["weight"] = round(max(0.3, current["weight"] - 0.15), 2)

            self._save()
            logger.info(f"Updated performance for voice '{voice_id}': {views} views, {current['avg_retention_pct']}% avg retention.")

    def get_top_performing_voice(self, language: str = "english") -> str:
        """Return the best performing voice based on historical retention and views."""
        with self._lock:
            voices = self._data.get("voice_performance", {})
            candidates = {
                vid: data for vid, data in voices.items()
                if data.get("language", "english") == language
            }
            if not candidates:
                return "en-US-ChristopherNeural" if language == "english" else "hi-IN-MadhurNeural"

            best_vid = max(candidates, key=lambda k: candidates[k].get("weight", 1.0) * candidates[k].get("avg_retention_pct", 50.0))
            return best_vid

    def get_full_evolution_summary(self) -> Dict[str, Any]:
        """Retrieve complete evolution stats for auditing."""
        with self._lock:
            return {
                "version": self._data.get("version"),
                "total_experiments": len(self._data.get("experiment_history", [])),
                "latest_experiments": self._data.get("experiment_history", [])[-5:],
                "niche_weights": self._data.get("niche_weights", {}),
                "voice_performance": self._data.get("voice_performance", {}),
                "winning_rules_count": len(self._data.get("winning_hook_patterns", [])),
            }
