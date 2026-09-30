"""Stealth Scheduler and Jitter Optimizer.

Introduces randomized timing offsets to video publication schedules to emulate
human behavior and avoid rigid cron patterns detected by platform algorithms.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class StealthScheduler:
    """Calculates humanized upload and publishing schedules with randomized jitter."""

    @staticmethod
    def calculate_jittered_publish_time(
        target_hour_utc: int,
        target_minute_utc: int = 0,
        jitter_minutes: int = 25,
    ) -> str:
        """Calculate scheduled ISO 8601 publish time with randomized jitter.

        Args:
            target_hour_utc: Base target hour (0-23 UTC).
            target_minute_utc: Base target minute (0-59 UTC).
            jitter_minutes: Range of random minutes to add or subtract.

        Returns:
            ISO 8601 formatted datetime string.
        """
        now = datetime.now(timezone.utc)
        target = now.replace(hour=target_hour_utc, minute=target_minute_utc, second=0, microsecond=0)

        # If target has already passed today, schedule for tomorrow
        if target <= now:
            target += timedelta(days=1)

        # Apply random jitter offset (e.g. -25 to +25 minutes)
        jitter = random.randint(-jitter_minutes, jitter_minutes)
        scheduled_time = target + timedelta(minutes=jitter)

        iso_str = scheduled_time.isoformat()
        logger.info(f"Calculated jittered publish time: {iso_str} (jitter offset: {jitter:+d}m)")
        return iso_str
