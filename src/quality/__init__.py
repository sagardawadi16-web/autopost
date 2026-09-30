"""Quality & Verification Package.

Contains guardrails, checkpoint validators, and grasping inspectors to ensure
the autonomous pipelines never miss the mark.
"""

from src.quality.checkpoint_guard import CheckpointGuard, CheckpointResult

__all__ = ["CheckpointGuard", "CheckpointResult"]
