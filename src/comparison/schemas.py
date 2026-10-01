"""Comparison Video Schemas and Data Models.

Defines validated data structures for contrasting comparison Shorts
following the "Normal Save VS Genuine Love" emotional heroism theme.
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CaptionBeat(BaseModel):
    """Represents a synchronized on-screen caption beat."""

    text: str = Field(..., description="On-screen subtitle text")
    time_offset: float = Field(..., description="Timeline start offset in seconds")
    duration: float = Field(default=3.0, description="Display duration in seconds")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Caption text cannot be empty.")
        return s

    @field_validator("time_offset")
    @classmethod
    def validate_time_offset(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"time_offset must be non-negative, got {v}")
        return round(float(v), 2)

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"duration must be positive, got {v}")
        return round(float(v), 2)

    @property
    def timestamp(self) -> float:
        """Alias for time_offset for backwards/cross-module compatibility."""
        return self.time_offset

    @property
    def end_time(self) -> float:
        """End timestamp on video timeline."""
        return round(self.time_offset + self.duration, 2)


class StorySegment(BaseModel):
    """Represents one of the two contrasting story segments."""

    header_text: str = Field(..., description="Top comparison badge header text")
    duration: float = Field(..., description="Segment duration in seconds")
    tone: str = Field(..., description="Emotional audio-visual tone")
    search_queries: List[str] = Field(..., description="Search queries for footage sourcing")
    caption_beats: List[CaptionBeat] = Field(default_factory=list, description="Timed on-screen captions")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Support 'duration_seconds' alias
            if "duration_seconds" in data and "duration" not in data:
                data["duration"] = data["duration_seconds"]
            # Ensure search_queries is a list
            if "search_queries" in data and isinstance(data["search_queries"], str):
                data["search_queries"] = [data["search_queries"]]
        return data

    @field_validator("header_text")
    @classmethod
    def validate_header_text(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Header text cannot be empty.")
        return s

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"Segment duration must be positive, got {v}")
        return round(float(v), 2)

    @field_validator("search_queries")
    @classmethod
    def validate_search_queries(cls, v: List[str]) -> List[str]:
        cleaned = [q.strip() for q in v if isinstance(q, str) and q.strip()]
        if not cleaned:
            raise ValueError("search_queries must contain at least one valid query string.")
        return cleaned


class PivotMoment(BaseModel):
    """Represents the dramatic pivot / drop transition between Part 1 and Part 2."""

    timestamp: float = Field(..., description="Exact transition moment in seconds")
    transition_effect: str = Field(default="fadeblack", description="FFmpeg transition style")
    sfx: str = Field(default="impact_whoosh", description="Sound effect cue at the pivot")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "transition_timestamp" in data and "timestamp" not in data:
                data["timestamp"] = data["transition_timestamp"]
        return data

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Pivot timestamp must be non-negative, got {v}")
        return round(float(v), 2)

    @field_validator("transition_effect")
    @classmethod
    def validate_transition_effect(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("transition_effect cannot be empty.")
        return s

    @field_validator("sfx")
    @classmethod
    def validate_sfx(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("sfx cue cannot be empty.")
        return s


class ComparisonStory(BaseModel):
    """Container for a complete two-part comparison Short narrative."""

    story_id: str = Field(default="", description="Unique identifier for the story run")
    title: str = Field(..., description="Video title with emojis and tags")
    theme: str = Field(..., description="Core narrative premise/theme")
    part1: StorySegment = Field(..., description="Part 1: Baseline/Normal save")
    pivot: PivotMoment = Field(..., description="Transition pivot point")
    part2: StorySegment = Field(..., description="Part 2: Genuine love/devotion")
    total_duration: float = Field(..., description="Total Short duration (20s - 50s)")
    description: str = Field(default="", description="Optimized YouTube video description")
    tags: List[str] = Field(default_factory=list, description="YouTube tags")

    @model_validator(mode="before")
    @classmethod
    def pre_validate_and_normalize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Auto-generate story_id if missing or empty
        if not data.get("story_id"):
            theme_slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(data.get("theme", "story"))).strip("_").lower()
            theme_slug = theme_slug[:30] if theme_slug else "comparison"
            data["story_id"] = f"{theme_slug}_{uuid.uuid4().hex[:8]}"

        # Auto-compute total_duration if missing or zero
        part1 = data.get("part1", {})
        part2 = data.get("part2", {})
        p1_dur = float(part1.get("duration", part1.get("duration_seconds", 0.0))) if isinstance(part1, dict) else (part1.duration if hasattr(part1, "duration") else 0.0)
        p2_dur = float(part2.get("duration", part2.get("duration_seconds", 0.0))) if isinstance(part2, dict) else (part2.duration if hasattr(part2, "duration") else 0.0)

        if ("total_duration" not in data or data["total_duration"] is None or data["total_duration"] <= 0) and (p1_dur > 0 and p2_dur > 0):
            data["total_duration"] = round(p1_dur + p2_dur, 2)

        # Auto-create pivot if missing
        if "pivot" not in data or not data["pivot"]:
            data["pivot"] = {
                "timestamp": p1_dur if p1_dur > 0 else 12.0,
                "transition_effect": "fadeblack",
                "sfx": "impact_whoosh",
            }

        # Normalize caption beat offsets in Part 2 if they are segment-relative (< part1.duration)
        if isinstance(part2, dict) and "caption_beats" in part2 and isinstance(part2["caption_beats"], list):
            new_beats = []
            for b in part2["caption_beats"]:
                if isinstance(b, dict):
                    offset = float(b.get("time_offset", b.get("timestamp", 0.0)))
                    # If offset is relative to part2 start (less than part1 duration), adjust to absolute timeline
                    if offset < p1_dur and p1_dur > 0:
                        b_copy = dict(b)
                        b_copy["time_offset"] = round(p1_dur + offset, 2)
                        new_beats.append(b_copy)
                    else:
                        new_beats.append(b)
                else:
                    new_beats.append(b)
            part2["caption_beats"] = new_beats

        return data

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Story title cannot be empty.")
        return s

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Story theme cannot be empty.")
        return s

    @field_validator("total_duration")
    @classmethod
    def validate_total_duration(cls, v: float) -> float:
        duration = round(float(v), 2)
        if duration < 20.0:
            raise ValueError(f"Total duration ({duration}s) is below minimum of 20.0 seconds.")
        if duration > 50.0:
            raise ValueError(f"Total duration ({duration}s) exceeds maximum of 50.0 seconds.")
        return duration

    @model_validator(mode="after")
    def validate_story_integrity(self) -> ComparisonStory:
        # 1. Validate Part 1 header
        p1_header = self.part1.header_text.upper()
        if not any(token in p1_header for token in ["NORMAL", "SAVE", "STANDARD", "ROUTINE", "CASUAL"]):
            raise ValueError(
                f"Part 1 header ('{self.part1.header_text}') must reflect the baseline/normal rescue theme."
            )

        # 2. Validate Part 2 header
        p2_header = self.part2.header_text.upper()
        if not any(token in p2_header for token in ["LOVE", "GENUINE", "HEROIC", "DEVOTION", "SACRIFICE", "HEART"]):
            raise ValueError(
                f"Part 2 header ('{self.part2.header_text}') must reflect the genuine love / emotional devotion theme."
            )

        # 3. Validate duration consistency
        calculated_total = round(self.part1.duration + self.part2.duration, 2)
        if abs(self.total_duration - calculated_total) > 1.5:
            raise ValueError(
                f"total_duration ({self.total_duration}s) does not match sum of part1 ({self.part1.duration}s) "
                f"and part2 ({self.part2.duration}s) = {calculated_total}s."
            )

        # 4. Validate pivot timestamp matches part1 duration within tolerance
        if abs(self.pivot.timestamp - self.part1.duration) > 1.0:
            raise ValueError(
                f"Pivot timestamp ({self.pivot.timestamp}s) must align with Part 1 duration ({self.part1.duration}s)."
            )

        # 5. Validate caption beats stay within their respective segments
        for beat in self.part1.caption_beats:
            if beat.time_offset >= self.part1.duration:
                raise ValueError(
                    f"Part 1 caption beat at {beat.time_offset}s exceeds Part 1 duration ({self.part1.duration}s)."
                )

        for beat in self.part2.caption_beats:
            if beat.time_offset < self.part1.duration:
                raise ValueError(
                    f"Part 2 caption beat at {beat.time_offset}s occurs before Part 2 start ({self.part1.duration}s)."
                )
            if beat.time_offset >= self.total_duration:
                raise ValueError(
                    f"Part 2 caption beat at {beat.time_offset}s exceeds total video duration ({self.total_duration}s)."
                )

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert story to dictionary representation."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Convert story to formatted JSON string."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ComparisonStory:
        """Instantiate ComparisonStory from dictionary."""
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, json_str: str) -> ComparisonStory:
        """Instantiate ComparisonStory from JSON string."""
        return cls.model_validate_json(json_str)
