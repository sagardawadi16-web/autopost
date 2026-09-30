"""Fetch and filter Reddit stories from configured subreddits.

Pulls top posts, extracts story data, and filters by quality criteria.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from src.scraper.reddit_client import RedditClient

logger = logging.getLogger(__name__)


class StoryFetcher:
    """Fetches and filters Reddit stories for video content."""

    def __init__(self, client: RedditClient) -> None:
        """Initialize with a RedditClient instance.

        Args:
            client: Configured RedditClient for API access.
        """
        self.client = client

    @staticmethod
    def _extract_story(submission) -> Optional[dict]:
        """Extract relevant data from a Reddit submission.

        Args:
            submission: PRAW Submission object.

        Returns:
            Dictionary with story data, or None if the post is not suitable.
        """
        # Skip posts without text content (link posts, images, etc.)
        selftext = getattr(submission, "selftext", "")
        if not selftext or selftext in ("[removed]", "[deleted]"):
            return None

        # Skip NSFW content
        if getattr(submission, "over_18", False):
            return None

        word_count = len(selftext.split())

        return {
            "id": submission.id,
            "title": submission.title,
            "body": selftext,
            "score": submission.score,
            "num_comments": submission.num_comments,
            "url": f"https://reddit.com{submission.permalink}",
            "permalink": submission.permalink,
            "subreddit": str(submission.subreddit),
            "created_utc": submission.created_utc,
            "created_date": datetime.fromtimestamp(
                submission.created_utc, tz=timezone.utc
            ).isoformat(),
            "word_count": word_count,
            "author": str(getattr(submission, "author", "[deleted]")),
            "upvote_ratio": getattr(submission, "upvote_ratio", 0),
        }

    def fetch_stories(
        self,
        subreddits: list[str],
        time_filter: str = "week",
        limit: int = 50,
        min_upvotes: int = 1000,
        min_words: int = 500,
        max_words: int = 5000,
    ) -> list[dict]:
        """Fetch and filter stories from multiple subreddits.

        Args:
            subreddits: List of subreddit names to scrape.
            time_filter: Time window for top posts.
            limit: Max posts to fetch per subreddit.
            min_upvotes: Minimum score/upvotes required.
            min_words: Minimum story word count.
            max_words: Maximum story word count.

        Returns:
            List of story dicts, sorted by score descending.
        """
        all_stories = []

        for sub_name in subreddits:
            try:
                posts = self.client.get_top_posts(
                    subreddit_name=sub_name,
                    time_filter=time_filter,
                    limit=limit,
                )

                for post in posts:
                    story = self._extract_story(post)
                    if story is None:
                        continue

                    # Apply quality filters
                    if story["score"] < min_upvotes:
                        continue
                    if story["word_count"] < min_words:
                        continue
                    if story["word_count"] > max_words:
                        continue

                    all_stories.append(story)

                logger.info(
                    f"r/{sub_name}: {len(posts)} posts fetched, "
                    f"{sum(1 for s in all_stories if s['subreddit'] == sub_name)} passed filters"
                )

            except Exception as e:
                logger.error(f"Failed to fetch from r/{sub_name}: {e}")
                continue

        # Sort by score (highest first)
        all_stories.sort(key=lambda s: s["score"], reverse=True)

        logger.info(f"Total stories after filtering: {len(all_stories)}")
        return all_stories

    def fetch_from_all_configured(
        self,
        time_filter: str = "week",
        limit: int = 50,
    ) -> list[dict]:
        """Fetch stories from all subreddits defined in config.

        Args:
            time_filter: Time window for top posts.
            limit: Max posts per subreddit.

        Returns:
            List of filtered story dicts.
        """
        from src.config import REDDIT_CONFIG

        return self.fetch_stories(
            subreddits=REDDIT_CONFIG["subreddits"],
            time_filter=time_filter,
            limit=limit,
            min_upvotes=REDDIT_CONFIG["story_selection"]["min_upvotes"],
            min_words=REDDIT_CONFIG["story_selection"]["min_words"],
            max_words=REDDIT_CONFIG["story_selection"]["max_words"],
        )

    def fetch_multi_timeframe(self, subreddits: list[str]) -> list[dict]:
        """Fetch stories from both 'day' and 'week' timeframes for more variety.

        Args:
            subreddits: List of subreddit names.

        Returns:
            Deduplicated list of stories from both timeframes.
        """
        day_stories = self.fetch_stories(subreddits, time_filter="day", limit=25)
        week_stories = self.fetch_stories(subreddits, time_filter="week", limit=50)

        # Deduplicate by story ID
        seen_ids = set()
        combined = []
        for story in day_stories + week_stories:
            if story["id"] not in seen_ids:
                seen_ids.add(story["id"])
                combined.append(story)

        combined.sort(key=lambda s: s["score"], reverse=True)
        logger.info(f"Multi-timeframe fetch: {len(combined)} unique stories")
        return combined
