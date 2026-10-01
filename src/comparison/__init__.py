"""Comparison Shorts Generation Package (@AuralyEditsYT Style).

Exposes story schemas, director, and upcoming media/compositor modules.
"""

from src.comparison.schemas import (
    CaptionBeat,
    ComparisonStory,
    PivotMoment,
    StorySegment,
)
from src.comparison.story_director import (
    FALLBACK_COMPARISON_STORIES,
    ComparisonStoryDirector,
)

__all__ = [
    "CaptionBeat",
    "StorySegment",
    "PivotMoment",
    "ComparisonStory",
    "ComparisonStoryDirector",
    "FALLBACK_COMPARISON_STORIES",
]
