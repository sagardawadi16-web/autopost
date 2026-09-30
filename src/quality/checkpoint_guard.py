"""Checkpoint Guard and Grasping Validator.

Ensures that the autonomous generation pipelines adhere strictly to user
intent, specifications, and quality thresholds without missing the mark.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CheckpointResult:
    """Result of a checkpoint verification gate."""

    passed: bool
    stage: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """Return formatted summary of verification result."""
        status = "[PASS]" if self.passed else "[FAIL]"
        lines = [f"{status} Checkpoint Gate: {self.stage}"]
        if self.errors:
            lines.append("  Errors:")
            for err in self.errors:
                lines.append(f"    - {err}")
        if self.warnings:
            lines.append("  Warnings:")
            for w in self.warnings:
                lines.append(f"    - {w}")
        if self.metrics:
            lines.append(f"  Metrics: {self.metrics}")
        return "\n".join(lines)


class GraspingValidator:
    """Validates that user requirements and creative intent are fully grasped."""

    MANDATORY_GHIBLI_KEYS = ["style_keywords", "aspect_ratio", "target_format", "channel"]
    REQUIRED_ASPECT_RATIOS = ["9:16", "16:9"]

    @classmethod
    def validate_spec(cls, spec: Dict[str, Any]) -> CheckpointResult:
        """Validate pipeline specification before any execution starts."""
        errors: List[str] = []
        warnings: List[str] = []
        metrics: Dict[str, Any] = {}

        # 1. Check mandatory keys
        for key in cls.MANDATORY_GHIBLI_KEYS:
            if key not in spec or not spec[key]:
                errors.append(f"Missing mandatory specification parameter: '{key}'")

        # 2. Check aspect ratio
        ratio = spec.get("aspect_ratio")
        if ratio and ratio not in cls.REQUIRED_ASPECT_RATIOS:
            errors.append(f"Invalid aspect ratio '{ratio}'. Must be '9:16' or '16:9'")

        # 3. Check duration constraint
        target_format = spec.get("target_format", "")
        max_duration = spec.get("max_duration_sec", 60)
        if target_format == "shorts" and max_duration > 59:
            errors.append(f"YouTube Shorts ceiling exceeded: {max_duration}s > 59s limit")

        # 4. Check style grasping
        style = spec.get("style_keywords", "")
        if isinstance(style, str) and len(style.strip()) < 10:
            warnings.append("Style description is very short; might lead to generic visuals")

        metrics["spec_keys_count"] = len(spec)
        metrics["format"] = target_format
        metrics["aspect_ratio"] = ratio

        return CheckpointResult(
            passed=len(errors) == 0,
            stage="Phase 0: Intent & Requirement Grasping",
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )


class CheckpointGuard:
    """Verification gatekeeper that stops execution if quality thresholds are missed."""

    @staticmethod
    def verify_story_checkpoint(
        scenes: List[Dict[str, Any]],
        is_shorts: bool = False,
    ) -> CheckpointResult:
        """Audit story scenes deconstruction."""
        errors: List[str] = []
        warnings: List[str] = []
        metrics: Dict[str, Any] = {}

        if not scenes:
            return CheckpointResult(
                passed=False,
                stage="Checkpoint 1: Story & Scene Deconstruction",
                errors=["No scenes generated"],
            )

        min_scenes = 3 if is_shorts else 6
        max_scenes = 8 if is_shorts else 50

        if len(scenes) < min_scenes:
            errors.append(f"Insufficient scene count: {len(scenes)} (minimum required: {min_scenes})")
        elif len(scenes) > max_scenes:
            warnings.append(f"High scene count: {len(scenes)} (max recommended: {max_scenes})")

        total_est_duration = sum(s.get("duration", 5.0) for s in scenes)
        if is_shorts and total_est_duration > 59.0:
            errors.append(f"Estimated story duration {total_est_duration:.1f}s exceeds Shorts limit (59s)")

        # Verify each scene has prompt and direction
        for idx, scene in enumerate(scenes, 1):
            if not scene.get("prompt"):
                errors.append(f"Scene {idx} missing visual prompt")
            if not scene.get("narration") and not scene.get("asmr_cue"):
                warnings.append(f"Scene {idx} has neither narration nor ASMR cue")

        metrics["scene_count"] = len(scenes)
        metrics["total_est_duration_sec"] = total_est_duration

        return CheckpointResult(
            passed=len(errors) == 0,
            stage="Checkpoint 1: Story & Scene Deconstruction",
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )

    @staticmethod
    def verify_visual_checkpoint(image_paths: List[Path | str]) -> CheckpointResult:
        """Audit visual outputs before video assembly."""
        errors: List[str] = []
        warnings: List[str] = []
        valid_count = 0

        for p in image_paths:
            path = Path(p)
            if not path.exists():
                errors.append(f"Visual asset not found on disk: {path}")
            elif path.stat().st_size < 10_000:  # < 10KB usually corrupted/empty
                errors.append(f"Visual asset file size suspiciously small ({path.stat().st_size} bytes): {path}")
            else:
                valid_count += 1

        metrics = {"total_requested": len(image_paths), "valid_images": valid_count}

        return CheckpointResult(
            passed=len(errors) == 0 and valid_count > 0,
            stage="Checkpoint 2: Visual Generation & Upscaling",
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )

    @staticmethod
    def verify_audio_checkpoint(
        audio_path: Path | str,
        max_duration_sec: float = 59.0,
        is_shorts: bool = False,
    ) -> CheckpointResult:
        """Audit synthesized voiceover and ASMR audio track."""
        errors: List[str] = []
        warnings: List[str] = []
        path = Path(audio_path)

        if not path.exists():
            return CheckpointResult(
                passed=False,
                stage="Checkpoint 3: Audio & Soundscape Synthesis",
                errors=[f"Audio master file not found: {path}"],
            )

        file_size = path.stat().st_size
        if file_size < 5_000:
            errors.append(f"Audio file size too small ({file_size} bytes); likely silent or truncated")

        # In production, probe audio duration with ffprobe if available
        metrics = {"file_size_bytes": file_size, "path": str(path)}

        return CheckpointResult(
            passed=len(errors) == 0,
            stage="Checkpoint 3: Audio & Soundscape Synthesis",
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )

    @staticmethod
    def verify_video_checkpoint(
        video_path: Path | str,
        expected_ratio: str = "9:16",
        is_shorts: bool = False,
    ) -> CheckpointResult:
        """Audit assembled video MP4 before upload."""
        errors: List[str] = []
        warnings: List[str] = []
        path = Path(video_path)

        if not path.exists():
            return CheckpointResult(
                passed=False,
                stage="Checkpoint 4: Video Compositing & Subtitles",
                errors=[f"Rendered video not found on disk: {path}"],
            )

        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb < 0.5:
            errors.append(f"Rendered video size is under 500KB ({file_size_mb:.2f}MB); render likely failed")

        metrics = {
            "file_size_mb": round(file_size_mb, 2),
            "expected_aspect_ratio": expected_ratio,
            "path": str(path),
        }

        return CheckpointResult(
            passed=len(errors) == 0,
            stage="Checkpoint 4: Video Compositing & Subtitles",
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )
