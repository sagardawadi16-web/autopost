"""YouTube Live Analytics & Strategic Evolution Engine.

Queries the YouTube Data API v3 for live audience engagement metrics
(viewCount, likeCount, commentCount) on published videos.
Feeds telemetry into StrategicLearningMemory to autonomously adapt
narrative hooks, subreddit niche weights, audio parameters, and pacing.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Standalone CLI path resilience
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.config import DATA_DIR, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YT_GHIBLI_REFRESH_TOKEN, YT_EN_REFRESH_TOKEN
from src.evolution.learning_memory import StrategicLearningMemory
from src.evolution.optimizer import ChannelOptimizer
from src.uploader.youtube_auth import YouTubeAuth

logger = logging.getLogger(__name__)

UPLOAD_LOG_PATH = DATA_DIR / "upload_log.json"


class AnalyticsCollector:
    """Collects YouTube metrics and drives autonomous evolutionary adjustments."""

    def __init__(
        self,
        memory: Optional[StrategicLearningMemory] = None,
        log_path: Optional[Path] = None,
    ) -> None:
        self.memory = memory or StrategicLearningMemory()
        self.optimizer = ChannelOptimizer(memory=self.memory)
        self.log_path = log_path or UPLOAD_LOG_PATH

    def _get_youtube_service(self, channel_name: str = "ghibli") -> Any:
        """Construct authenticated YouTube client."""
        token = YT_GHIBLI_REFRESH_TOKEN if channel_name == "ghibli" else (YT_EN_REFRESH_TOKEN or YT_GHIBLI_REFRESH_TOKEN)
        if not token:
            raise ValueError(f"No refresh token available for channel '{channel_name}'.")

        auth = YouTubeAuth(
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            refresh_token=token,
        )
        return auth.get_service()

    def fetch_video_stats(self, video_ids: List[str], channel_name: str = "ghibli") -> Dict[str, Dict[str, Any]]:
        """Fetch live statistics for a batch of YouTube video IDs."""
        if not video_ids:
            return {}

        stats_map: Dict[str, Dict[str, Any]] = {}
        try:
            yt = self._get_youtube_service(channel_name=channel_name)
            # YouTube API accepts up to 50 comma-separated IDs
            id_chunk = ",".join(video_ids[:50])
            resp = yt.videos().list(part="statistics,snippet", id=id_chunk).execute()

            for item in resp.get("items", []):
                v_id = item["id"]
                s = item.get("statistics", {})
                snippet = item.get("snippet", {})
                views = int(s.get("viewCount", 0))
                likes = int(s.get("likeCount", 0))
                comments = int(s.get("commentCount", 0))

                stats_map[v_id] = {
                    "video_id": v_id,
                    "title": snippet.get("title", ""),
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagement_rate": round(((likes + comments) / max(1, views)) * 100, 2),
                    "published_at": snippet.get("publishedAt", ""),
                }
        except Exception as e:
            logger.warning(f"Failed to fetch live YouTube analytics for {video_ids}: {e}")

        return stats_map

    def sync_and_evolve(self) -> Dict[str, Any]:
        """Audit all published videos, extract telemetry, and dynamically evolve strategy."""
        logger.info("🔍 [Analytics Collector] Auditing published video performance...")

        if not self.log_path.exists():
            logger.info("No upload log found. Initializing baseline strategy.")
            return {"status": "no_upload_log"}

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read upload log: {e}")
            return {"status": "error", "error": str(e)}

        # Filter valid uploaded video IDs
        real_uploads = [item for item in logs if not item.get("dry_run") and not item.get("video_id", "").startswith("sim_")]
        if not real_uploads:
            logger.info("No live uploaded videos yet to audit. Baseline directives preserved.")
            return {"status": "no_live_videos"}

        video_ids = [item["video_id"] for item in real_uploads]
        stats = self.fetch_video_stats(video_ids, channel_name="ghibli")

        total_views = 0
        total_likes = 0
        evolution_actions: List[str] = []

        for item in real_uploads:
            v_id = item["video_id"]
            stat = stats.get(v_id)
            if not stat:
                continue

            views = stat["views"]
            likes = stat["likes"]
            total_views += views
            total_likes += likes

            channel = item.get("channel", "ghibli")
            title = stat["title"].lower()

            # Dynamic Subreddit / Niche Weighting based on traction
            if "horror" in title or "scariest" in title or "creepy" in title:
                niche = "nosleep"
                if views > 100 or likes > 5:
                    new_w = self.memory.update_niche_weight(niche, 0.15)
                    evolution_actions.append(f"Boosted '{niche}' weight to {new_w} (High Horror Traction)")
            elif "aita" in title or "revenge" in title:
                niche = "ProRevenge"
                if views > 100 or likes > 5:
                    new_w = self.memory.update_niche_weight(niche, 0.15)
                    evolution_actions.append(f"Boosted '{niche}' weight to {new_w} (High Drama Traction)")

            # Record voice feedback into learning memory
            if channel == "ghibli":
                self.memory.record_voice_performance(
                    voice_id="hi-IN-SwaraNeural",
                    views=views,
                    retention_pct=65.0 if views > 10 else 55.0,
                    language="hindi",
                )
            else:
                self.memory.record_voice_performance(
                    voice_id="en-US-ChristopherNeural",
                    views=views,
                    retention_pct=62.0 if views > 10 else 50.0,
                    language="english",
                )

        summary = {
            "audited_count": len(stats),
            "total_views": total_views,
            "total_likes": total_likes,
            "evolution_actions": evolution_actions,
            "active_directives": self.memory.get_rewriter_directives("horror", "english"),
            "current_niche_weights": self.memory.get_all_niche_weights(),
        }

        logger.info(f"✅ [Analytics Collector] Evolution complete! Audited {len(stats)} videos, Total Views: {total_views}")
        return summary


# Global singleton
analytics_collector = AnalyticsCollector()
