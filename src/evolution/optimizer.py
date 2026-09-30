"""Channel evolution optimizer that evaluates analytics and reasons about performance.

Analyzes audience metrics (CTR, retention, engagement) across different niches,
video lengths, and hook formulas to continuously refine channel strategy.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from src.evolution.learning_memory import StrategicLearningMemory

logger = logging.getLogger(__name__)


class ChannelOptimizer:
    """Analyzes content performance, formulates reasoning hypotheses, and tunes generation parameters."""

    def __init__(self, memory: Optional[StrategicLearningMemory] = None) -> None:
        """Initialize optimizer with learning memory.

        Args:
            memory: Instance of StrategicLearningMemory. If None, instantiates default.
        """
        self.memory = memory or StrategicLearningMemory()

    def evaluate_video_performance(
        self,
        video_id: str,
        category: str,
        subreddit: str,
        views: int,
        ctr: float,
        avg_retention_pct: float,
        duration_seconds: float,
        hook_type: str,
    ) -> Dict[str, Any]:
        """Evaluate a published video's metrics and deduce reasoning for future optimization.

        Args:
            video_id: YouTube video identifier or internal reference.
            category: Story genre/mood.
            subreddit: Source subreddit.
            views: Total views accumulated.
            ctr: Click-through rate percentage (e.g. 7.2).
            avg_retention_pct: Average percentage of video watched (e.g. 58.4).
            duration_seconds: Total length in seconds.
            hook_type: Type of hook used in opening 10 seconds.

        Returns:
            Dictionary containing audit outcome, reasoning verdict, and strategy adjustments.
        """
        reasoning_notes = []
        rule_added = ""
        niche_delta = 0.0

        # CTR Evaluation (Thumbnail & Title Effectiveness)
        if ctr >= 8.0:
            reasoning_notes.append(f"Outstanding CTR ({ctr:.1f}%). High emotional resonance in title and high-contrast thumbnail.")
            niche_delta += 0.05
        elif ctr < 4.5:
            reasoning_notes.append(f"Underperforming CTR ({ctr:.1f}%). Title was likely too verbose or thumbnail lacked a clear focal point.")
            niche_delta -= 0.05

        # Retention Evaluation (Script Hook & Pacing)
        if avg_retention_pct >= 65.0:
            reasoning_notes.append(f"Superior audience retention ({avg_retention_pct:.1f}%). Hook '{hook_type}' captivated audience effectively.")
            rule_added = f"Prioritize '{hook_type}' hook style for {category} content."
            niche_delta += 0.05
        elif avg_retention_pct < 45.0:
            reasoning_notes.append(f"Low retention ({avg_retention_pct:.1f}%). Drop-off indicates intro was too slow or middle lacked cliffhangers.")
            rule_added = f"Avoid slow buildup in {category}; enforce micro-hooks every 60 seconds."
            niche_delta -= 0.08

        # Niche weight adaptation
        new_weight = self.memory.update_niche_weight(subreddit, niche_delta)

        # Record formal experiment/learning
        exp_id = self.memory.record_reasoning_experiment(
            hypothesis=f"Testing {category} story from r/{subreddit} with {hook_type} hook.",
            observation=f"Achieved {views} views, {ctr:.1f}% CTR, and {avg_retention_pct:.1f}% retention.",
            reasoning="; ".join(reasoning_notes),
            rule_added=rule_added or f"Maintain baseline pacing for {category}.",
            confidence_score=0.85 if views > 500 else 0.65,
        )

        audit_report = {
            "experiment_id": exp_id,
            "video_id": video_id,
            "category": category,
            "subreddit": subreddit,
            "niche_new_weight": new_weight,
            "reasoning": reasoning_notes,
            "rule_enforced": rule_added,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Evolution audit complete for video {video_id}: {audit_report}")
        return audit_report

    def generate_strategy_evolution_report(self) -> str:
        """Produce a formatted markdown report of the channel's strategic evolution."""
        summary = self.memory.get_full_evolution_summary()
        weights = summary.get("niche_weights", {})
        experiments = summary.get("latest_experiments", [])

        lines = [
            "# 📈 Channel Strategic Evolution Report",
            f"**Last Updated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Total Learning Cycles**: {summary.get('total_experiments', 0)}",
            "",
            "## 🎯 Current Niche Weightings (Autonomous Adaptation)",
            "| Subreddit | Current Weight | Strategic Stance |",
            "|---|---|---|",
        ]

        for sub, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            stance = "🚀 Prioritized (Viral High Performer)" if weight >= 1.25 else ("⚖️ Neutral" if weight >= 0.95 else "🔻 Deprioritized")
            lines.append(f"| r/{sub} | {weight:.2f} | {stance} |")

        lines.extend([
            "",
            "## 🧠 Recent Strategic Reasonings & Rules Added",
        ])

        if not experiments:
            lines.append("_No experiments logged yet. Baseline strategy active._")
        else:
            for exp in experiments:
                lines.append(f"### 🧪 `{exp.get('id')}` — Confidence {exp.get('confidence_score', 0)*100:.0f}%")
                lines.append(f"- **Hypothesis**: {exp.get('hypothesis')}")
                lines.append(f"- **Observation**: {exp.get('observation')}")
                lines.append(f"- **Reasoning**: {exp.get('reasoning')}")
                lines.append(f"- **Rule Added**: `{exp.get('rule_added')}`")
                lines.append("")

        return "\n".join(lines)
