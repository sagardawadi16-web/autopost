"""Comparison Story Director.

Formulates contrasting two-part emotional heroism story concepts for viral
comparison Shorts ("Normal Save VS Genuine Love" theme) using Gemini with
automatic offline fallback templates.
"""

from __future__ import annotations

import copy
import json
import logging
import random
import re
from typing import Any, Dict, List, Optional

from src.comparison.schemas import (
    CaptionBeat,
    ComparisonStory,
    PivotMoment,
    StorySegment,
)
from src.utils import call_gemini_with_fallback

logger = logging.getLogger(__name__)

# Master offline fallback templates representing rich emotional heroism comparisons
FALLBACK_COMPARISON_STORIES: List[Dict[str, Any]] = [
    {
        "story_id": "comparison_dog_flood_001",
        "title": "Normal Save 🥶 VS Genuine Love ❤️ #shorts",
        "theme": "Loyal Dog Dives Into Raging Rapids",
        "part1": {
            "header_text": "NORMAL SAVE 🥶",
            "duration": 12.0,
            "tone": "cool_suspense",
            "search_queries": [
                "firefighter calm canal dog rescue",
                "standard animal rescue safe harness",
            ],
            "caption_beats": [
                {"text": "Standard routine rescue.", "time_offset": 0.5, "duration": 3.5},
                {"text": "Full gear. Protocol followed.", "time_offset": 4.5, "duration": 3.5},
                {"text": "Safe and sound.", "time_offset": 8.5, "duration": 3.0},
            ],
        },
        "pivot": {
            "timestamp": 12.0,
            "transition_effect": "fadeblack",
            "sfx": "impact_whoosh",
        },
        "part2": {
            "header_text": "GENUINE LOVE ❤️",
            "duration": 18.0,
            "tone": "emotional_epic",
            "search_queries": [
                "dog dives into torrential flood river save puppy",
                "heroic dog rescues drowning puppy rapids",
            ],
            "caption_beats": [
                {"text": "No harness. No hesitation.", "time_offset": 12.5, "duration": 3.5},
                {"text": "He leaped straight into the raging flood.", "time_offset": 16.5, "duration": 4.0},
                {"text": "Because genuine love never lets go. ❤️", "time_offset": 21.0, "duration": 4.5},
            ],
        },
        "total_duration": 30.0,
        "description": "The difference between doing a job and genuine devotion... ❤️ #heroism #shorts #rescue #faithinhumanity #animals",
        "tags": ["shorts", "heroism", "emotional", "rescue", "loyalty", "viral", "genuine love", "normal save"],
    },
    {
        "story_id": "comparison_ice_sinkhole_002",
        "title": "Normal Save 🥶 VS Genuine Love ❤️ (Freezing Ice) #shorts",
        "theme": "Freezing Ice Sinkhole Rescue",
        "part1": {
            "header_text": "NORMAL SAVE 🥶",
            "duration": 11.0,
            "tone": "cool_suspense",
            "search_queries": [
                "fire rescue pole ice pond dog",
                "professional winter pet retrieval",
            ],
            "caption_beats": [
                {"text": "Calculated distance.", "time_offset": 0.5, "duration": 3.0},
                {"text": "Standard safety protocol.", "time_offset": 4.0, "duration": 3.5},
                {"text": "Job done.", "time_offset": 8.0, "duration": 2.5},
            ],
        },
        "pivot": {
            "timestamp": 11.0,
            "transition_effect": "fadeblack",
            "sfx": "impact_whoosh",
        },
        "part2": {
            "header_text": "GENUINE LOVE ❤️",
            "duration": 17.0,
            "tone": "emotional_epic",
            "search_queries": [
                "man strips coat crawls thin ice bare hands save dog",
                "owner breaks freezing ice with bare hands rescues dog",
            ],
            "caption_beats": [
                {"text": "Zero protective gear.", "time_offset": 11.5, "duration": 3.0},
                {"text": "Breaking freezing ice with bare hands.", "time_offset": 15.0, "duration": 4.0},
                {"text": "He risked hypothermia to save his best friend. ❤️", "time_offset": 19.5, "duration": 4.5},
            ],
        },
        "total_duration": 28.0,
        "description": "Would you jump into freezing ice with bare hands? 🥶 True love knows no cold. ❤️ #shorts #hero #ice #rescue #emotional",
        "tags": ["shorts", "ice rescue", "hero", "emotional", "loyalty", "dog", "love"],
    },
    {
        "story_id": "comparison_highrise_ledge_003",
        "title": "Normal Save 🥶 VS Genuine Love ❤️ (5th Floor Ledge) #shorts",
        "theme": "Apartment Window Ledge Rescue",
        "part1": {
            "header_text": "NORMAL SAVE 🥶",
            "duration": 12.0,
            "tone": "cool_suspense",
            "search_queries": [
                "fire truck cherry picker crane cat balcony",
                "professional animal ladder rescue",
            ],
            "caption_beats": [
                {"text": "Hydraulic lift engaged.", "time_offset": 0.5, "duration": 3.5},
                {"text": "Routine municipal callout.", "time_offset": 4.5, "duration": 3.5},
                {"text": "Secure and contained.", "time_offset": 8.5, "duration": 3.0},
            ],
        },
        "pivot": {
            "timestamp": 12.0,
            "transition_effect": "fadeblack",
            "sfx": "impact_whoosh",
        },
        "part2": {
            "header_text": "GENUINE LOVE ❤️",
            "duration": 18.0,
            "tone": "emotional_epic",
            "search_queries": [
                "man climbs out 5th floor window ledge rain save cat",
                "fearless owner crawls exterior ledge high rise save pet",
            ],
            "caption_beats": [
                {"text": "50 feet above the pavement.", "time_offset": 12.5, "duration": 3.5},
                {"text": "No ropes. No safety net.", "time_offset": 16.5, "duration": 3.5},
                {"text": "Fingertips slipping in the pouring rain.", "time_offset": 20.5, "duration": 3.5},
                {"text": "He chose love over his own life. ❤️", "time_offset": 24.5, "duration": 4.0},
            ],
        },
        "total_duration": 30.0,
        "description": "No ropes, no net, 50 feet up in the rain... would you do this? ❤️ #shorts #highrise #courage #love #heroism",
        "tags": ["shorts", "courage", "heroism", "highrise rescue", "cat lover", "genuine love"],
    },
    {
        "story_id": "comparison_rubble_vigil_004",
        "title": "Normal Save 🥶 VS Genuine Love ❤️ (Rubble Vigil) #shorts",
        "theme": "Earthquake Rubble Vigil & Rescue",
        "part1": {
            "header_text": "NORMAL SAVE 🥶",
            "duration": 10.0,
            "tone": "cool_suspense",
            "search_queries": [
                "urban search rescue acoustic sensor rubble",
                "disaster team marking collapsed building",
            ],
            "caption_beats": [
                {"text": "Shift concluded.", "time_offset": 0.5, "duration": 3.0},
                {"text": "Protocol marked on the wall.", "time_offset": 4.0, "duration": 3.0},
                {"text": "Awaiting secondary team.", "time_offset": 7.5, "duration": 2.2},
            ],
        },
        "pivot": {
            "timestamp": 10.0,
            "transition_effect": "fadeblack",
            "sfx": "impact_whoosh",
        },
        "part2": {
            "header_text": "GENUINE LOVE ❤️",
            "duration": 16.0,
            "tone": "emotional_epic",
            "search_queries": [
                "dog digs bloody paws rubble saves trapped owner",
                "loyal shepherd refuses to leave collapsed ruins owner alive",
            ],
            "caption_beats": [
                {"text": "18 straight hours of digging.", "time_offset": 10.5, "duration": 3.0},
                {"text": "Paws bleeding through jagged concrete.", "time_offset": 14.0, "duration": 3.5},
                {"text": "He refused to stop until he heard his voice.", "time_offset": 18.0, "duration": 3.5},
                {"text": "Loyalty that defies death itself. ❤️", "time_offset": 22.0, "duration": 3.5},
            ],
        },
        "total_duration": 26.0,
        "description": "18 hours of digging with bleeding paws... an unbreakable bond. ❤️ #shorts #loyalty #dog #rescue #faithinhumanity",
        "tags": ["shorts", "dog loyalty", "rubble rescue", "heroic dog", "genuine love"],
    },
    {
        "story_id": "comparison_wildfire_shield_005",
        "title": "Normal Save 🥶 VS Genuine Love ❤️ (Wildfire Shield) #shorts",
        "theme": "Wildfire Inferno Mother Animal Sacrifice",
        "part1": {
            "header_text": "NORMAL SAVE 🥶",
            "duration": 11.0,
            "tone": "cool_suspense",
            "search_queries": [
                "aerial water bomber wildfire smoke drop",
                "fire helicopter water drop trees",
            ],
            "caption_beats": [
                {"text": "Aerial containment drop.", "time_offset": 0.5, "duration": 3.0},
                {"text": "Perimeter control active.", "time_offset": 4.0, "duration": 3.5},
                {"text": "Monitoring burn line.", "time_offset": 8.0, "duration": 2.5},
            ],
        },
        "pivot": {
            "timestamp": 11.0,
            "transition_effect": "fadeblack",
            "sfx": "impact_whoosh",
        },
        "part2": {
            "header_text": "GENUINE LOVE ❤️",
            "duration": 19.0,
            "tone": "emotional_epic",
            "search_queries": [
                "mother dog shields puppies wildfire ashes unburned",
                "heroic mother animal protects babies fire rescue",
            ],
            "caption_beats": [
                {"text": "The flames surrounded them.", "time_offset": 11.5, "duration": 3.0},
                {"text": "She used her own body as a living shield.", "time_offset": 15.0, "duration": 4.0},
                {"text": "Her fur was scorched, but every puppy survived.", "time_offset": 19.5, "duration": 4.0},
                {"text": "A mother's love is unbreakable. ❤️", "time_offset": 24.0, "duration": 4.5},
            ],
        },
        "total_duration": 30.0,
        "description": "She shielded her puppies with her own body through the fire... ❤️ #shorts #motherlove #heroism #sacrifice #animals",
        "tags": ["shorts", "mother love", "wildfire", "animal hero", "genuine love", "sacrifice"],
    },
]


class ComparisonStoryDirector:
    """Directs and formulates contrasting comparison video scenarios."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    def generate_story(self, topic_or_theme: Optional[str] = None) -> ComparisonStory:
        """Formulate a contrasting two-part comparison story.

        Attempts AI generation using Gemini with automatic failover, falling back
        to rich curated offline templates if AI generation is unavailable.

        Args:
            topic_or_theme: Optional narrative theme or prompt guidance.

        Returns:
            Validated ComparisonStory instance.
        """
        logger.info(f"Directing comparison story (Theme: {topic_or_theme or 'dynamic'})...")

        try:
            story = self._generate_with_gemini(topic_or_theme)
            if story:
                logger.info(f"Successfully generated comparison story via Gemini: {story.title}")
                return story
        except Exception as e:
            logger.warning(
                f"Gemini comparison story generation notice ({e}); seamlessly falling back to curated master template."
            )

        return self.get_fallback_story()

    def get_fallback_story(self, index: Optional[int] = None) -> ComparisonStory:
        """Retrieve a validated offline fallback story template.

        Args:
            index: Optional template index (0 to 4). If None, selects randomly.

        Returns:
            Validated ComparisonStory instance.
        """
        if index is not None:
            safe_index = index % len(FALLBACK_COMPARISON_STORIES)
            template_data = copy.deepcopy(FALLBACK_COMPARISON_STORIES[safe_index])
        else:
            template_data = copy.deepcopy(random.choice(FALLBACK_COMPARISON_STORIES))

        return ComparisonStory.model_validate(template_data)

    def _generate_with_gemini(self, topic_or_theme: Optional[str]) -> Optional[ComparisonStory]:
        """Generate dynamic story using Gemini via call_gemini_with_fallback."""
        prompt = self._build_prompt(topic_or_theme)
        system_instruction = (
            "You are the master creative scenario director for viral @AuralyEditsYT comparison Shorts. "
            "Your signature style is contrasting 'Normal Save 🥶' (everyday routine rescue) with "
            "'Genuine Love ❤️' (extraordinary devotion, extreme sacrifice, deep emotional impact). "
            "You MUST respond ONLY with valid JSON conforming to the requested schema."
        )

        response_text = call_gemini_with_fallback(
            prompt=prompt,
            system_instruction=system_instruction,
            api_key=self.api_key,
        )

        if not response_text:
            return None

        parsed_json = self._parse_json_response(response_text)
        return ComparisonStory.model_validate(parsed_json)

    def _build_prompt(self, topic_or_theme: Optional[str]) -> str:
        """Build structured prompt for LLM scenario generation."""
        theme_directive = (
            f"Theme: {topic_or_theme}"
            if topic_or_theme
            else "Theme: Everyday routine animal rescue vs extraordinary selfless animal/human heroism"
        )

        return f"""
{theme_directive}

Format: YouTube Shorts 9:16 (Total Duration: 26 to 36 seconds).

Construct a viral comparison scenario divided into two contrasting parts:
1. Part 1: "NORMAL SAVE 🥶" (Duration: 10.0 to 14.0 seconds)
   - Baseline, routine, professional, or detached rescue.
   - Top Header MUST be: "NORMAL SAVE 🥶"
   - Tone: "cool_suspense"
   - Search queries: 2-3 search queries to find real video clips.
   - Caption beats: 2-3 short, understated on-screen caption beats with time_offset and duration.

2. Pivot: Transition moment at the exact end of Part 1.
   - Timestamp: equal to Part 1 duration.
   - transition_effect: "fadeblack"
   - sfx: "impact_whoosh"

3. Part 2: "GENUINE LOVE ❤️" (Duration: 16.0 to 22.0 seconds)
   - Extreme devotion, risking life, unconditional loyalty or maternal sacrifice.
   - Top Header MUST be: "GENUINE LOVE ❤️"
   - Tone: "emotional_epic"
   - Search queries: 2-3 search queries to find real video clips.
   - Caption beats: 2-4 emotional, high-retention on-screen caption beats.

4. Total Duration: 26.0 to 36.0 seconds (sum of Part 1 + Part 2).

Output strictly in JSON format with this exact structure:
{{
  "title": "Normal Save 🥶 VS Genuine Love ❤️ #shorts",
  "theme": "Brief 1-line narrative description",
  "part1": {{
    "header_text": "NORMAL SAVE 🥶",
    "duration": 12.0,
    "tone": "cool_suspense",
    "search_queries": ["query 1", "query 2"],
    "caption_beats": [
      {{"text": "A standard rescue.", "time_offset": 0.5, "duration": 3.5}},
      {{"text": "Safe and professional.", "time_offset": 4.5, "duration": 3.5}}
    ]
  }},
  "pivot": {{
    "timestamp": 12.0,
    "transition_effect": "fadeblack",
    "sfx": "impact_whoosh"
  }},
  "part2": {{
    "header_text": "GENUINE LOVE ❤️",
    "duration": 18.0,
    "tone": "emotional_epic",
    "search_queries": ["query 1", "query 2"],
    "caption_beats": [
      {{"text": "No gear. No hesitation.", "time_offset": 12.5, "duration": 3.5}},
      {{"text": "He risked everything.", "time_offset": 16.5, "duration": 4.0}},
      {{"text": "That is genuine love. ❤️", "time_offset": 21.0, "duration": 4.5}}
    ]
  }},
  "total_duration": 30.0,
  "description": "Video description with hashtags #heroism #shorts #rescue",
  "tags": ["shorts", "heroism", "emotional", "rescue"]
}}

Respond ONLY with valid JSON. Do not include markdown code fences or conversational text.
"""

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Clean and parse JSON from LLM output."""
        cleaned = text.strip()

        # Remove markdown code fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Extract content between outer braces if text contains extra noise
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()

        return json.loads(cleaned)
