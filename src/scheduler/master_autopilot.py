"""Master Autopilot Daemon for Hands-Free 24/7 Channel Growth.

Continuously and autonomously:
1. Detects pending sequels/follow-ups (e.g. Part 1 without Part 2) and publishes Part 2.
2. Selects high-resonance story themes (AmItheAsshole, ProRevenge, nosleep).
3. Produces vertical Shorts with Christopher voice, scary SFX, and thumbnail hooks.
4. Produces Hindi visual slideshows (zero subtitles).
5. Publishes to YouTube with humanized stealth jitter.
6. Audits view telemetry, evaluates retention, and evolves strategic learning memory.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.config import ensure_directories, YOUTUBE_SETTINGS
from src.evolution.optimizer import ChannelOptimizer
from src.pipeline import AutomationPipeline
from src.uploader.scheduler import StealthScheduler

logger = logging.getLogger("autopost.master_autopilot")


class MasterAutoPilot:
    """Master controller orchestrating autonomous multi-part storytelling publication."""

    def __init__(
        self,
        interval_hours: float = 12.0,
        channel: str = "english",
        privacy: str = "public",
        dry_run: bool = False,
    ) -> None:
        """Initialize Master Autopilot.

        Args:
            interval_hours: Hours to wait between automated production cycles.
            channel: Target channel language ('english', 'hindi', or 'both').
            privacy: YouTube privacy status ('public', 'unlisted', 'private').
            dry_run: Whether to simulate YouTube upload.
        """
        self.interval_hours = interval_hours
        self.channel = channel
        self.privacy = privacy
        self.dry_run = dry_run
        ensure_directories()
        self.optimizer = ChannelOptimizer()

    def run_cycle(self) -> None:
        """Execute one complete autonomous publishing cycle."""
        logger.info("=========================================================")
        logger.info(f"🤖 [AUTOPILOT CYCLE START] {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"Target Channel: {self.channel.upper()} | Privacy: {self.privacy}")
        logger.info("=========================================================")

        # 1. Post pending Part 2 follow-up if applicable
        followup_id = "ai_20260930145547_449"
        part2_video = _repo_root / "output" / "video" / f"final_{followup_id}_part2_english_short.mp4"

        channels_to_run = ["english", "hindi"] if self.channel == "both" else [self.channel]

        for ch in channels_to_run:
            pipeline = AutomationPipeline(channel=ch, dry_run=self.dry_run, privacy=self.privacy)

            # If English and Part 2 is pending, publish follow-up first
            if ch == "english" and part2_video.exists():
                logger.info(f"Publishing pending Part 2 follow-up for '{followup_id}'...")
                try:
                    pipeline.run(is_shorts=True, followup_id=followup_id)
                    logger.info("✅ Part 2 follow-up published successfully!")
                except Exception as e:
                    logger.error(f"Error publishing Part 2 follow-up: {e}")

            # Produce fresh multi-part storytelling Short
            logger.info(f"Generating fresh automated Short for channel '{ch}'...")
            try:
                result = pipeline.run(is_shorts=True, multipart=True)
                logger.info(f"✅ Video published successfully: {result.get('upload_info', {}).get('url')}")
            except Exception as e:
                logger.error(f"Error during video production: {e}")

        # 2. Run post-cycle evolution audit
        logger.info("Auditing published videos and updating voice/niche learning memory...")
        try:
            reports = self.optimizer.audit_uploaded_videos()
            logger.info(f"Audited {len(reports)} video entries. Channel strategy evolved.")
        except Exception as e:
            logger.warning(f"Audit warning: {e}")

    def start_loop(self) -> None:
        """Run 24/7 continuous autonomous daemon."""
        logger.info("=========================================================")
        logger.info("🚀 24/7 MASTER AUTOPILOT DAEMON ACTIVATED")
        logger.info(f"Interval: Every {self.interval_hours:.1f} hours | Privacy: {self.privacy}")
        logger.info("Hands-free operation: Generating Part 1 + Part 2 arcs & evolving strategy.")
        logger.info("=========================================================")

        cycle_count = 0
        while True:
            cycle_count += 1
            logger.info(f"\n--- Starting Autopilot Cycle #{cycle_count} ---")
            try:
                self.run_cycle()
            except Exception as e:
                logger.error(f"Cycle #{cycle_count} halted with exception: {e}", exc_info=True)

            sleep_seconds = int(self.interval_hours * 3600)
            next_run = datetime.now(timezone.utc).timestamp() + sleep_seconds
            logger.info(f"Cycle #{cycle_count} complete. Next cycle scheduled in {self.interval_hours:.1f} hours.")
            time.sleep(sleep_seconds)


def main() -> None:
    """CLI entrypoint for master autopilot daemon."""
    parser = argparse.ArgumentParser(description="Master Autopilot 24/7 Production Daemon")
    parser.add_argument("--interval", type=float, default=12.0, help="Interval in hours (default: 12.0)")
    parser.add_argument("--channel", choices=["english", "hindi", "both"], default="english", help="Target channel")
    parser.add_argument("--privacy", choices=["public", "unlisted", "private"], default="public", help="Visibility")
    parser.add_argument("--dry-run", action="store_true", help="Simulate upload without live publish")

    args = parser.parse_args()
    autopilot = MasterAutoPilot(
        interval_hours=args.interval,
        channel=args.channel,
        privacy=args.privacy,
        dry_run=args.dry_run,
    )
    autopilot.start_loop()


if __name__ == "__main__":
    main()
