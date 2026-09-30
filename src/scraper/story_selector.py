"""Score and select the best Reddit stories for video content.

Ranks stories by engagement metrics and keyword relevance,
then selects the top candidates for long-form videos and Shorts.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Keywords that boost a story's score (proven viral topics)
BOOST_KEYWORDS = {
    # Horror/scary
    "scary": 1.3,
    "terrifying": 1.3,
    "creepy": 1.3,
    "horror": 1.3,
    "nightmare": 1.2,
    "haunted": 1.2,
    "paranormal": 1.2,
    "demon": 1.2,
    "ghost": 1.2,
    # Drama
    "aita": 1.4,
    "revenge": 1.3,
    "entitled": 1.3,
    "cheating": 1.3,
    "divorce": 1.2,
    "betrayal": 1.3,
    "caught": 1.2,
    "exposed": 1.2,
    # Engagement hooks
    "update": 1.5,  # Updates to previous stories perform very well
    "final update": 1.6,
    "part 2": 1.3,
    "plot twist": 1.3,
}


class StorySelector:
    """Scores and selects the best stories for video production."""

    def __init__(self) -> None:
        """Initialize the story selector."""
        pass

    @staticmethod
    def score_story(story: dict) -> float:
        """Calculate a composite score for a Reddit story.

        Formula:
            base = (upvotes * 0.4) + (comments * 0.3) + (word_count * 0.001 * 0.3)
            final = base * keyword_multiplier * upvote_ratio_bonus

        Args:
            story: Story dictionary with score, num_comments, word_count, title.

        Returns:
            Composite score as a float.
        """
        # Base score from engagement metrics
        base_score = (
            story.get("score", 0) * 0.4
            + story.get("num_comments", 0) * 0.3
            + story.get("word_count", 0) * 0.001 * 0.3
        )

        # Keyword boost — check title for viral keywords
        title_lower = story.get("title", "").lower()
        keyword_multiplier = 1.0
        for keyword, boost in BOOST_KEYWORDS.items():
            if keyword in title_lower:
                keyword_multiplier = max(keyword_multiplier, boost)

        # Upvote ratio bonus — controversial posts (high comments, lower ratio)
        # can be good for engagement
        upvote_ratio = story.get("upvote_ratio", 0.5)
        ratio_bonus = 1.0
        if upvote_ratio >= 0.95:
            ratio_bonus = 1.1  # Universally loved = bonus
        elif upvote_ratio <= 0.7:
            ratio_bonus = 1.15  # Controversial = even better for engagement

        final_score = base_score * keyword_multiplier * ratio_bonus

        return round(final_score, 2)

    def select_best(
        self,
        stories: list[dict],
        count: int = 3,
        exclude_ids: Optional[set] = None,
    ) -> list[dict]:
        """Select the top N stories by composite score.

        Args:
            stories: List of story dictionaries.
            count: Number of stories to select.
            exclude_ids: Set of story IDs to skip (already used).

        Returns:
            List of top-scored stories.
        """
        if exclude_ids is None:
            exclude_ids = set()

        # Filter out already-used stories
        available = [s for s in stories if s["id"] not in exclude_ids]

        if not available:
            logger.warning("No stories available after filtering exclusions")
            return []

        # Score and sort
        for story in available:
            story["_composite_score"] = self.score_story(story)

        available.sort(key=lambda s: s["_composite_score"], reverse=True)

        selected = available[:count]

        logger.info(
            f"Selected {len(selected)} stories from {len(available)} available. "
            f"Top score: {selected[0]['_composite_score'] if selected else 'N/A'}"
        )

        for i, story in enumerate(selected):
            logger.info(
                f"  #{i+1}: [{story['subreddit']}] \"{story['title'][:60]}...\" "
                f"(score={story['score']}, composite={story['_composite_score']})"
            )

        return selected

    def select_for_shorts(
        self,
        stories: list[dict],
        count: int = 2,
        exclude_ids: Optional[set] = None,
    ) -> list[dict]:
        """Select stories best suited for YouTube Shorts (< 60 seconds).

        Prefers shorter, more dramatic stories (1000-2000 words)
        that can be condensed into a punchy 60-second clip.

        Args:
            stories: List of story dictionaries.
            count: Number of Shorts candidates to select.
            exclude_ids: Set of story IDs to exclude.

        Returns:
            List of stories suited for Shorts format.
        """
        if exclude_ids is None:
            exclude_ids = set()

        available = [s for s in stories if s["id"] not in exclude_ids]

        # For Shorts, prefer stories in the 500-2000 word range
        shorts_candidates = [
            s for s in available
            if 500 <= s.get("word_count", 0) <= 2000
        ]

        # If not enough short stories, fall back to all available
        if len(shorts_candidates) < count:
            shorts_candidates = available

        # Score with a preference for shorter stories
        for story in shorts_candidates:
            base = self.score_story(story)
            # Bonus for shorter stories (easier to condense to 60s)
            word_count = story.get("word_count", 1000)
            if word_count <= 1000:
                length_bonus = 1.3
            elif word_count <= 1500:
                length_bonus = 1.2
            elif word_count <= 2000:
                length_bonus = 1.1
            else:
                length_bonus = 0.9
            story["_shorts_score"] = round(base * length_bonus, 2)

        shorts_candidates.sort(key=lambda s: s["_shorts_score"], reverse=True)

        selected = shorts_candidates[:count]

        logger.info(f"Selected {len(selected)} stories for Shorts")
        return selected

    def categorize_story(self, story: dict) -> str:
        """Determine the category/mood of a story for voice and music selection.

        Args:
            story: Story dictionary.

        Returns:
            Category string: 'horror', 'drama', 'revenge', 'wholesome', or 'general'.
        """
        title_lower = story.get("title", "").lower()
        subreddit = story.get("subreddit", "").lower()

        # Horror/scary
        if subreddit in ("nosleep", "creepy", "letsnotmeet"):
            return "horror"
        if any(w in title_lower for w in ("scary", "terrifying", "creepy", "horror", "demon", "ghost")):
            return "horror"

        # Revenge
        if subreddit in ("prorevenge", "pettyrevenge", "maliciouscompliance"):
            return "revenge"
        if "revenge" in title_lower:
            return "revenge"

        # Drama / AITA
        if subreddit in ("amitheasshole", "relationship_advice", "entitledparents"):
            return "drama"
        if any(w in title_lower for w in ("aita", "entitled", "cheating", "divorce")):
            return "drama"

        # TIFU — can be wholesome or dramatic
        if subreddit == "tifu":
            return "drama"

        return "general"
