"""Autonomous Autopilot Scheduler for @GHIBLISTYLESTUDIO.

Runs 100% autonomously in the background:
1. Picks fresh, unrepeated 90s Indian village nostalgia themes.
2. Auto-generates high-aesthetic Ghibli visual frames & Ken Burns animation.
3. Mixes soulful Hindi voice narration with authentic rain/chulha ASMR.
4. Auto-publishes to YouTube with stealth jitter scheduling.
5. Persists publication history to prevent theme duplication.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("ghibli.autopilot")

from src.config import DATA_DIR, ensure_directories
from src.ghibli_pipeline import GhibliPipeline
from src.uploader.scheduler import StealthScheduler

HISTORY_FILE = DATA_DIR / "ghibli_history.json"

# Autonomous topic queue rotating through diverse 90s nostalgic village atmospheres
AUTONOMOUS_THEMES: List[str] = [
    "90s के गांव की वो मूसलाधार बारिश, खपरैल से टपकता पानी और दादी के हाथ के गर्मागर्म पकौड़े",
    "गांव के स्कूल की दोपहर की छुट्टी, भारी बारिश में छाता बंद करके भीगना और कागज़ की नाव तैराना",
    "सर्दियों की सुबह, कच्चे आंगन में अलाव की गर्माहट, और मिट्टी के कुल्हड़ में गुड़ वाली अदरक की चाय",
    "गांव की शाम, पगडंडी पर बजती साइकिल की घंटी, ढलती धूप और मां की प्यार भरी आवाज़",
    "गांव का वो पुराना मेला, लकड़ी का झूला, लालटेन की धीमी रोशनी और जलेबी की सौंधी खुशबू",
    "खेतों में लहलहाती हरी फसलें, चिड़ियों की चहचहाहट, और नीम के पेड़ के नीचे दोपहर का सुकून",
    "गांव के तालाब के किनारे शांत दोपहर, तैरते हुए बत्तख, और दूर बजती बांसुरी की मीठी धुन",
    "दादी के मिट्टी के चूल्हे पर पकती मक्के की रोटी, सरसों का साग और ऊपर से सफेद ताजा मक्खन",
    "बारिश के बाद की शांत गोधूलि बेला, कच्चे घरों से जलती लालटेन और झींगुरों का सुकून भरा संगीत",
    "बचपन की वो बेफिक्र गर्मियां, आम के बगीचे में दोस्तों के साथ दोपहर बिताना और पेड़ की छांव",
]


class GhibliAutoPilot:
    """Fully automated continuous publishing daemon."""

    def __init__(self, interval_hours: float = 24.0, privacy: str = "public") -> None:
        self.interval_hours = interval_hours
        self.privacy = privacy
        ensure_directories()
        self.pipeline = GhibliPipeline(dry_run=False, privacy=privacy)
        self.history = self._load_history()

    def _load_history(self) -> List[str]:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_history(self, theme: str) -> None:
        self.history.append(theme)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history[-100:], f, ensure_ascii=False, indent=2)

    def get_next_theme(self) -> str:
        """Select a fresh theme that hasn't been used recently."""
        candidates = [t for t in AUTONOMOUS_THEMES if t not in self.history[-len(AUTONOMOUS_THEMES) :]]
        if not candidates:
            candidates = AUTONOMOUS_THEMES
        return random.choice(candidates)

    def run_cycle(self, is_shorts: bool = True) -> None:
        """Execute one complete autonomous generation and upload cycle."""
        theme = self.get_next_theme()
        format_type = "Shorts (9:16)" if is_shorts else "Story Video (16:9)"
        logger.info(f"🚀 [Auto-Pilot] Launching autonomous cycle for {format_type}...")
        logger.info(f"🎨 Theme: '{theme}'")

        try:
            result = self.pipeline.run(
                is_shorts=is_shorts,
                theme=theme,
                burn_subtitles=True,
                upload=True,
            )
            self._save_history(theme)
            logger.info(f"✅ [Auto-Pilot] Cycle complete! Video published: {result.get('title')}")
        except Exception as e:
            logger.error(f"❌ [Auto-Pilot] Cycle encountered error: {e}", exc_info=True)

    def start_loop(self) -> None:
        """Run continuous daemon loop, publishing automatically on schedule."""
        logger.info("=========================================================")
        logger.info(f"🤖 @GHIBLISTYLESTUDIO AUTOPILOT DAEMON ACTIVATED")
        logger.info(f"Interval: Every {self.interval_hours:.1f} hours | Privacy: {self.privacy}")
        logger.info("=========================================================")

        while True:
            # Alternate between Shorts and Landscape Story
            self.run_cycle(is_shorts=True)

            sleep_seconds = self.interval_hours * 3600
            # Add random humanized jitter (+/- 15 minutes)
            jitter = random.randint(-900, 900)
            sleep_duration = max(sleep_seconds + jitter, 1800)
            wake_time = datetime.now() + timedelta(seconds=sleep_duration)

            logger.info(f"💤 Sleeping until next cycle at {wake_time.strftime('%Y-%m-%d %H:%M:%S')} (~{sleep_duration/3600:.1f} hours)...")
            time.sleep(sleep_duration)


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomous Autopilot for Ghibli Studio channel.")
    parser.add_argument("--interval", type=float, default=24.0, help="Interval between uploads in hours (default: 24)")
    parser.add_argument("--privacy", default="public", choices=["public", "private", "unlisted"])
    parser.add_argument("--once", action="store_true", help="Run a single cycle right now and exit")
    parser.add_argument("--type", choices=["shorts", "story"], default="shorts")

    args = parser.parse_args()
    autopilot = GhibliAutoPilot(interval_hours=args.interval, privacy=args.privacy)

    if args.once:
        autopilot.run_cycle(is_shorts=(args.type == "shorts"))
    else:
        autopilot.start_loop()


if __name__ == "__main__":
    main()
