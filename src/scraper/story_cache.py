"""Cache for tracking used Reddit stories to prevent duplicates.

Stores used story IDs in a JSON file with metadata for auditing.
Supports cleanup of old entries to keep the cache manageable.
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import threading

logger = logging.getLogger(__name__)


class StoryCache:
    """Persistent cache for tracking which Reddit stories have been used."""

    def __init__(self, cache_file: Optional[str] = None) -> None:
        """Initialize the story cache.

        Args:
            cache_file: Path to the JSON cache file.
                        Defaults to data/used_stories.json.
        """
        if cache_file is None:
            from src.config import DATA_DIR
            self._cache_path = DATA_DIR / "used_stories.json"
        else:
            self._cache_path = Path(cache_file)

        self._lock = threading.Lock()
        self._cache: dict = self._load()

    def _load(self) -> dict:
        """Load the cache from disk.

        Returns:
            Dictionary of used stories {story_id: metadata}.
        """
        if not self._cache_path.exists():
            # Create parent directories and empty cache
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._save({})
            return {}

        try:
            with open(self._cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded story cache with {len(data)} entries")
            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load cache, starting fresh: {e}")
            return {}

    def _save(self, data: Optional[dict] = None) -> None:
        """Save the cache to disk.

        Args:
            data: Data to save. If None, saves self._cache.
        """
        if data is None:
            data = self._cache

        self._cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to save cache: {e}")

    def is_used(self, story_id: str) -> bool:
        """Check if a story has already been used.

        Args:
            story_id: Reddit post ID.

        Returns:
            True if the story has been used before.
        """
        with self._lock:
            return story_id in self._cache

    def is_title_used(self, title: str) -> bool:
        """Check if a story title or similar title has already been used.

        Args:
            title: Story title to check.

        Returns:
            True if a matching or near-matching title was used.
        """
        clean_target = " ".join(title.lower().split())
        with self._lock:
            for meta in self._cache.values():
                used_title = " ".join(meta.get("title", "").lower().split())
                if used_title and (clean_target in used_title or used_title in clean_target):
                    return True
        return False

    def get_recent_titles(self, limit: int = 25) -> list[str]:
        """Retrieve recent used story titles to pass to LLM generators for anti-duplication."""
        with self._lock:
            titles = [meta.get("title", "") for meta in self._cache.values() if meta.get("title")]
            return titles[-limit:]


    def mark_used(
        self,
        story_id: str,
        title: str,
        subreddit: str,
        channel: str = "unknown",
    ) -> None:
        """Mark a story as used.

        Args:
            story_id: Reddit post ID.
            title: Story title for reference.
            subreddit: Source subreddit name.
            channel: Which channel used this story (english/hindi).
        """
        with self._lock:
            self._cache[story_id] = {
                "title": title,
                "subreddit": subreddit,
                "channel": channel,
                "used_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save()
            logger.info(f"Marked story as used: [{subreddit}] {title[:50]}...")

    def get_used_ids(self) -> set[str]:
        """Get all used story IDs.

        Returns:
            Set of story ID strings.
        """
        with self._lock:
            return set(self._cache.keys())

    def cleanup_old(self, days: int = 90) -> int:
        """Remove cache entries older than the specified number of days.

        This allows stories to be reused after enough time has passed.

        Args:
            days: Age threshold in days.

        Returns:
            Number of entries removed.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        removed = 0

        with self._lock:
            to_remove = []
            for story_id, meta in self._cache.items():
                used_at_str = meta.get("used_at", "")
                try:
                    used_at = datetime.fromisoformat(used_at_str)
                    if used_at < cutoff:
                        to_remove.append(story_id)
                except (ValueError, TypeError):
                    # If date is unparseable, keep it
                    continue

            for story_id in to_remove:
                del self._cache[story_id]
                removed += 1

            if removed > 0:
                self._save()
                logger.info(f"Cleaned up {removed} old cache entries (>{days} days)")

        return removed

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats.
        """
        with self._lock:
            by_subreddit: dict[str, int] = {}
            by_channel: dict[str, int] = {}

            for meta in self._cache.values():
                sub = meta.get("subreddit", "unknown")
                chan = meta.get("channel", "unknown")
                by_subreddit[sub] = by_subreddit.get(sub, 0) + 1
                by_channel[chan] = by_channel.get(chan, 0) + 1

            return {
                "total_used": len(self._cache),
                "by_subreddit": by_subreddit,
                "by_channel": by_channel,
            }
