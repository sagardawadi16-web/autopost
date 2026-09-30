"""Reddit API client wrapper using PRAW.

Provides a clean interface to fetch posts from Reddit subreddits
in read-only mode (no Reddit account required).
"""

import logging
import random
import time
from typing import Optional

import praw
from praw.models import Subreddit, Submission

logger = logging.getLogger(__name__)

# Realistic user agents to rotate through
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/17.1",
]


class RedditClient:
    """Client for fetching Reddit posts via PRAW in read-only mode."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> None:
        """Initialize the Reddit client.

        Args:
            client_id: Reddit app client ID.
            client_secret: Reddit app client secret.
            user_agent: Custom user agent string. If None, a random one is chosen.
            max_retries: Maximum number of retry attempts on failure.
            retry_delay: Base delay in seconds between retries (exponential backoff).
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if user_agent is None:
            user_agent = f"AutoPostBot/1.0 ({random.choice(USER_AGENTS)})"

        self._reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        # Read-only mode — no login needed
        self._reddit.read_only = True
        logger.info("Reddit client initialized in read-only mode")

    def _retry(self, func, *args, **kwargs):
        """Execute a function with retry logic and exponential backoff.

        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the function call.

        Raises:
            Exception: If all retries are exhausted.
        """
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
        raise last_exception

    def get_subreddit(self, name: str) -> Subreddit:
        """Get a subreddit object by name.

        Args:
            name: Subreddit name (without r/ prefix).

        Returns:
            PRAW Subreddit object.
        """
        return self._retry(lambda: self._reddit.subreddit(name))

    def get_top_posts(
        self,
        subreddit_name: str,
        time_filter: str = "week",
        limit: int = 50,
    ) -> list[Submission]:
        """Fetch top posts from a subreddit.

        Args:
            subreddit_name: Name of the subreddit.
            time_filter: Time window — 'hour', 'day', 'week', 'month', 'year', 'all'.
            limit: Maximum number of posts to fetch.

        Returns:
            List of PRAW Submission objects.
        """
        def _fetch():
            subreddit = self._reddit.subreddit(subreddit_name)
            posts = list(subreddit.top(time_filter=time_filter, limit=limit))
            logger.info(
                f"Fetched {len(posts)} top posts from r/{subreddit_name} "
                f"(time_filter={time_filter})"
            )
            return posts

        return self._retry(_fetch)

    def get_hot_posts(
        self,
        subreddit_name: str,
        limit: int = 50,
    ) -> list[Submission]:
        """Fetch hot posts from a subreddit.

        Args:
            subreddit_name: Name of the subreddit.
            limit: Maximum number of posts to fetch.

        Returns:
            List of PRAW Submission objects.
        """
        def _fetch():
            subreddit = self._reddit.subreddit(subreddit_name)
            posts = list(subreddit.hot(limit=limit))
            logger.info(f"Fetched {len(posts)} hot posts from r/{subreddit_name}")
            return posts

        return self._retry(_fetch)

    def get_new_posts(
        self,
        subreddit_name: str,
        limit: int = 50,
    ) -> list[Submission]:
        """Fetch newest posts from a subreddit.

        Args:
            subreddit_name: Name of the subreddit.
            limit: Maximum number of posts to fetch.

        Returns:
            List of PRAW Submission objects.
        """
        def _fetch():
            subreddit = self._reddit.subreddit(subreddit_name)
            posts = list(subreddit.new(limit=limit))
            logger.info(f"Fetched {len(posts)} new posts from r/{subreddit_name}")
            return posts

        return self._retry(_fetch)
