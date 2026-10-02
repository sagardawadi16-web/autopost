"""Master Daily Powerhouse Multi-Format Production & Upload Engine.

Orchestrates 3 distinct video streams every single day forever:
1. Ghibli Calm Story (Hayao Miyazaki painterly watercolor, 90s village nostalgia, ASMR, Flow AI).
2. Hindi Reddit Story (Ken Burns visual storytelling in Hindi, high-retention narration).
3. English Viral Reddit Story (Christopher voice, horror/drama SFX, dynamic colored ASS subtitles).

Features:
- Live YouTube Analytics Audit & Strategic Evolution Loop (adapting subreddit weights & hooks).
- Multi-Provider LLM Tier Invariant (Tier 1 Pollinations keyless first, primary key strictly last).
- Perpetual 24/7 daemon mode and one-shot CI/CD execution.
- Uploads directly to the powerhouse YouTube channel ("Ghibi") with Drive archival backup.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# UTF-8 stdout configuration for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Standalone CLI path resilience
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("autopost.powerhouse")

from src.config import DATA_DIR, YOUTUBE_SETTINGS, ensure_directories
from src.evolution.analytics_collector import AnalyticsCollector, analytics_collector
from src.evolution.learning_memory import StrategicLearningMemory
from src.ghibli_pipeline import GhibliPipeline
from src.pipeline import AutomationPipeline


class DailyPowerhouseRunner:
    """Master orchestrator generating and uploading all 3 content streams daily."""

    def __init__(
        self,
        dry_run: bool = False,
        upload: bool = True,
        privacy: Optional[str] = None,
        target_channel: str = "ghibli",
    ) -> None:
        self.dry_run = dry_run
        self.upload = upload and not dry_run
        self.privacy = (privacy or YOUTUBE_SETTINGS.default_privacy_status or "public").lower()
        self.target_channel = target_channel
        ensure_directories()

        self.reports_dir = DATA_DIR / "daily_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.analytics = analytics_collector
        self.memory = StrategicLearningMemory()

    def sync_analytics_and_evolve(self) -> Dict[str, Any]:
        """Step 1: Audit published videos and evolve content weights based on performance."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 STEP 1: AUDITING YOUTUBE ENGAGEMENT & EVOLVING STRATEGY")
        logger.info("=" * 60)

        try:
            audit = self.analytics.sync_and_evolve()
            logger.info(f"Audited Videos Count: {audit.get('audited_count', 0)}")
            logger.info(f"Total Views Monitored: {audit.get('total_views', 0)}")
            logger.info(f"Active Directives: {audit.get('active_directives', [])}")
            logger.info(f"Current Niche Weights: {audit.get('current_niche_weights', {})}")
            return audit
        except Exception as e:
            logger.warning(f"Analytics synchronization warning: {e}. Proceeding with existing learned weights.")
            return {"status": "warning", "error": str(e)}

    def run_ghibli_stream(self) -> Dict[str, Any]:
        """Step 2: Generate and publish Ghibli Calm Story."""
        logger.info("\n" + "=" * 60)
        logger.info("🎨 STEP 2: PRODUCING GHIBLI CALM STORY (90s Village Nostalgia)")
        logger.info("=" * 60)

        start_time = time.time()
        try:
            pipeline = GhibliPipeline(dry_run=self.dry_run, privacy=self.privacy)
            result = pipeline.run(
                is_shorts=True,
                burn_subtitles=False,
                upload=self.upload,
                upload_drive=True,
            )
            elapsed = round(time.time() - start_time, 2)
            logger.info(f"✅ Ghibli Stream Completed in {elapsed}s! Video URL: https://youtu.be/{result.get('video_id')}")
            return {
                "status": "SUCCESS",
                "stream": "ghibli_calm",
                "title": result.get("title"),
                "video_id": result.get("video_id"),
                "url": f"https://youtu.be/{result.get('video_id')}" if result.get("video_id") else None,
                "video_path": result.get("video_path"),
                "drive_link": result.get("drive_link"),
                "duration_seconds": result.get("duration"),
                "elapsed_seconds": elapsed,
            }
        except Exception as e:
            logger.error(f"❌ Ghibli Stream Error: {e}", exc_info=True)
            return {"status": "ERROR", "stream": "ghibli_calm", "error": str(e)}

    def run_hindi_reddit_stream(self) -> Dict[str, Any]:
        """Step 3: Generate and publish Hindi Reddit Story with visual slideshow."""
        logger.info("\n" + "=" * 60)
        logger.info("🇮🇳 STEP 3: PRODUCING HINDI REDDIT STORY (Ken Burns Slideshow)")
        logger.info("=" * 60)

        start_time = time.time()
        try:
            pipeline = AutomationPipeline(
                channel="hindi",
                dry_run=self.dry_run,
                privacy=self.privacy,
                target_upload_channel="hindi",
            )
            result = pipeline.run(is_shorts=True, multipart=False, burn_subtitles=False)
            elapsed = round(time.time() - start_time, 2)
            upload_info = result.get("upload_info", {})
            v_id = upload_info.get("video_id")
            v_url = upload_info.get("url")
            logger.info(f"✅ Hindi Reddit Stream Completed in {elapsed}s! Video URL: {v_url}")
            return {
                "status": "SUCCESS",
                "stream": "hindi_reddit",
                "title": upload_info.get("title"),
                "video_id": v_id,
                "url": v_url,
                "video_path": result.get("video_path"),
                "thumbnail_path": result.get("thumbnail_path"),
                "duration_seconds": result.get("duration_seconds"),
                "elapsed_seconds": elapsed,
            }
        except Exception as e:
            logger.error(f"❌ Hindi Reddit Stream Error: {e}", exc_info=True)
            return {"status": "ERROR", "stream": "hindi_reddit", "error": str(e)}

    def run_english_reddit_stream(self) -> Dict[str, Any]:
        """Step 4: Generate and publish English Viral Reddit Story."""
        logger.info("\n" + "=" * 60)
        logger.info("🇺🇸 STEP 4: PRODUCING ENGLISH VIRAL REDDIT STORY (Christopher Voice + SFX)")
        logger.info("=" * 60)

        start_time = time.time()
        try:
            pipeline = AutomationPipeline(
                channel="english",
                dry_run=self.dry_run,
                privacy=self.privacy,
                target_upload_channel="english",
            )
            result = pipeline.run(is_shorts=True, multipart=True, burn_subtitles=False)
            elapsed = round(time.time() - start_time, 2)
            upload_info = result.get("upload_info", {})
            v_id = upload_info.get("video_id")
            v_url = upload_info.get("url")
            logger.info(f"✅ English Reddit Stream Completed in {elapsed}s! Video URL: {v_url}")
            return {
                "status": "SUCCESS",
                "stream": "english_reddit",
                "title": upload_info.get("title"),
                "video_id": v_id,
                "url": v_url,
                "video_path": result.get("video_path"),
                "thumbnail_path": result.get("thumbnail_path"),
                "duration_seconds": result.get("duration_seconds"),
                "elapsed_seconds": elapsed,
            }
        except Exception as e:
            logger.error(f"❌ English Reddit Stream Error: {e}", exc_info=True)
            return {"status": "ERROR", "stream": "english_reddit", "error": str(e)}

    def execute_daily_batch(self, stream_filter: str = "all") -> Dict[str, Any]:
        """Execute complete daily batch cycle across selected streams."""
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        logger.info("\n" + "🌟" * 30)
        logger.info(f"🚀 INITIATING DAILY POWERHOUSE PRODUCTION BATCH: {batch_id}")
        logger.info(f"🎯 Target Channel: {self.target_channel.upper()} | Upload: {self.upload} | Dry-Run: {self.dry_run}")
        logger.info("🌟" * 30 + "\n")

        # 1. Analytics & Strategy Evolution
        analytics_summary = self.sync_analytics_and_evolve()

        # 2. Execute selected video streams
        stream_results: Dict[str, Any] = {}

        if stream_filter in ["all", "ghibli"]:
            stream_results["ghibli"] = self.run_ghibli_stream()

        if stream_filter in ["all", "hindi"]:
            stream_results["hindi"] = self.run_hindi_reddit_stream()

        if stream_filter in ["all", "english"]:
            stream_results["english"] = self.run_english_reddit_stream()

        # 3. Compile Master Report
        successful_streams = sum(1 for r in stream_results.values() if r.get("status") == "SUCCESS")
        report = {
            "batch_id": batch_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_channel": self.target_channel,
            "dry_run": self.dry_run,
            "upload_enabled": self.upload,
            "analytics_summary": analytics_summary,
            "streams_executed": len(stream_results),
            "successful_streams": successful_streams,
            "stream_results": stream_results,
        }

        # Save to disk
        report_file = self.reports_dir / f"daily_batch_{batch_id}.json"
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📁 Daily production report saved to: {report_file}")
        except Exception as e:
            logger.warning(f"Could not persist batch report: {e}")

        # Summary Log
        logger.info("\n" + "🏁" * 30)
        logger.info(f"🏆 DAILY BATCH COMPLETED: {successful_streams}/{len(stream_results)} STREAMS SUCCESSFUL")
        for stream_name, res in stream_results.items():
            st = res.get("status")
            url = res.get("url") or "Local Render"
            logger.info(f"  • {stream_name.upper()}: [{st}] {res.get('title', 'N/A')} -> {url}")
        logger.info("🏁" * 30 + "\n")

        return report

    def run_forever(self, interval_hours: float = 24.0, stream_filter: str = "all") -> None:
        """Run perpetual daily generation and publishing loop forever."""
        logger.info(f"♾️ Starting Perpetual Autonomous Daemon (Interval: {interval_hours} hours)...")
        iteration = 1
        while True:
            logger.info(f"\n⏰ === Perpetual Cycle #{iteration} Starting at {datetime.now(timezone.utc).isoformat()} ===")
            try:
                self.execute_daily_batch(stream_filter=stream_filter)
            except Exception as e:
                logger.error(f"Unexpected error during batch cycle #{iteration}: {e}", exc_info=True)

            sleep_seconds = int(interval_hours * 3600)
            logger.info(f"💤 Sleeping for {interval_hours} hours ({sleep_seconds} seconds) until next daily release...")
            time.sleep(sleep_seconds)
            iteration += 1


def main() -> None:
    """CLI Entrypoint for Daily Powerhouse Runner."""
    parser = argparse.ArgumentParser(description="Autonomous Triple-Format Daily Powerhouse & Analytics Engine")
    parser.add_argument(
        "--stream",
        choices=["all", "ghibli", "hindi", "english"],
        default="all",
        help="Specific stream to produce (default: all)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously forever in background loop",
    )
    parser.add_argument(
        "--interval-hours",
        type=float,
        default=24.0,
        help="Interval between runs when operating in daemon mode (default: 24.0)",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Disable uploading to YouTube and Drive (local render only)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Operate in simulation mode without real uploads or video renders",
    )
    parser.add_argument(
        "--privacy",
        choices=["public", "unlisted", "private"],
        default=YOUTUBE_SETTINGS.default_privacy_status,
        help="YouTube video visibility (default: public)",
    )
    parser.add_argument(
        "--target-channel",
        default="ghibli",
        help="Powerhouse YouTube channel target (default: ghibli)",
    )

    args = parser.parse_args()

    runner = DailyPowerhouseRunner(
        dry_run=args.dry_run,
        upload=not args.no_upload,
        privacy=args.privacy,
        target_channel=args.target_channel,
    )

    if args.daemon:
        runner.run_forever(interval_hours=args.interval_hours, stream_filter=args.stream)
    else:
        runner.execute_daily_batch(stream_filter=args.stream)


if __name__ == "__main__":
    main()
