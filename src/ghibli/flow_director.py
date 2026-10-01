"""Google Flow AI Inspired Cinematic Narrative Director.

Generates Ghibli-style videos with profound emotional resonance, sensory depth,
and Kishōtenketsu 4-act narrative flow. Built-in Multi-Model Quota Manager
automatically bypasses 429 rate limits across Gemini models with intelligent fallback.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import DATA_DIR, GEMINI_API_KEY
from src.ghibli.story_director import GhibliScene, GhibliStory
from src.llm.multi_provider_gateway import MultiProviderGateway, gateway

logger = logging.getLogger(__name__)

# Preferred models in priority order for quota management
FLOW_GEMINI_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.8-flash",
]

FLOW_CACHE_FILE = DATA_DIR / "flow_story_cache.json"


class FlowNarrativeDirector:
    """Orchestrates cinematic Flow AI stories with emotional resonance and quota resilience."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or GEMINI_API_KEY
        self.gateway = MultiProviderGateway()
        self.cache_file = FLOW_CACHE_FILE
        self._init_cache()

    def _init_cache(self) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.cache_file.exists():
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def generate_flow_story(
        self,
        theme: Optional[str] = None,
        is_shorts: bool = True,
        scene_count: int = 4,
    ) -> GhibliStory:
        """Craft a deeply moving Flow AI story with automatic quota management.

        Uses 4-Act Flow Structure:
        - Act 1: Atmospheric Prelude (Sensory grounding, quiet village horizon)
        - Act 2: Sensory Immersion (Tactile details: rain on tin, clay chulha warmth)
        - Act 3: Emotional Climax (Childhood innocence, family bond, lost simplicity)
        - Act 4: Soulful Afterglow (Dusk settling, golden lantern glow, peaceful lingering)
        """
        logger.info(f"🌿 [Flow AI Director] Crafting emotionally resonant narrative (Scenes: {scene_count})...")

        # Attempt multi-provider generation (Tier 1 Keyless -> Tier 2 Free -> Tier 3 Gemini Backup -> Tier 4 Gemini User Key Last)
        try:
            story = self._generate_with_gateway(theme=theme, is_shorts=is_shorts, scene_count=scene_count)
            if story:
                return story
        except Exception as e:
            logger.warning(f"⚠️ Gateway attempt notice: {e}")

        # Resilient fallback if all API quotas are saturated
        logger.info("🌿 [Flow AI Director] Utilizing high-resonance curated Flow blueprint.")
        return self._generate_master_flow_story(is_shorts=is_shorts, scene_count=scene_count)

    def _generate_with_gateway(
        self,
        theme: Optional[str],
        is_shorts: bool,
        scene_count: int,
    ) -> Optional[GhibliStory]:
        """Generate structured story via MultiProviderGateway across provider tiers."""
        format_str = "YouTube Short (35-45s, high emotional hook)" if is_shorts else f"Landscape Story ({scene_count} scenes, 3-5 min)"
        prompt = f"""You are the Lead Narrative Director for Studio Ghibli and Google Flow AI.
Craft a soulful, deeply nostalgic 90s Indian/South Asian village memory in Hindi.
Focus on emotional resonance, sensory depth (petrichor, crackling chulha, sound of rain on tin sheets), and poetic tranquility.

Format: {format_str}
Theme: {theme or '90s village monsoon rain, grandmother cooking warm rotis on clay chulha, innocent childhood simplicity'}

Structure the narrative into {scene_count} chronological cinematic scenes following Kishōtenketsu emotional flow:
1. Atmospheric Prelude: Wide shot, morning rain or golden dawn, smell of wet earth.
2. Sensory Immersion: Close tactile actions, steaming tea, clay hearth embers, childhood wonder.
3. Emotional Climax: The warmth of togetherness, unhurried 90s innocence, freedom from modern rush.
4. Soulful Afterglow: Twilight lanterns, quiet rain drizzle, heartwarming peace.

Output ONLY a JSON object with:
- "title": Heartwarming title in Hindi with English subtitle.
- "description": 2-3 poetic sentences with #ghibli #nostalgia #indianvillage #rainasmr hashtags.
- "tags": 8-10 viral tags.
- "thumbnail_hook": 3-4 word emotional Hindi phrase.
- "full_narration": Complete continuous soulful Hindi voiceover.
- "scenes": Array of {scene_count} scene objects:
  - "scene_index": 1, 2, ...
  - "narration_chunk": The calm Hindi spoken line for this scene (2 sentences).
  - "visual_prompt": Strict Flow AI prompt: 'Studio Ghibli aesthetic, Hayao Miyazaki anime style, watercolor gouache cel, soft diffused lighting, 90s Indian village, [scene details], cinematic composition'.
  - "motion_type": 'zoom_in', 'zoom_out', 'pan_left', or 'pan_right'.
  - "asmr_cue": 'rain_heavy', 'rain_light', 'chulha_fire', or 'crickets_night'.
  - "duration_seconds": 6.5 to 8.5.
"""
        data, provider_name = self.gateway.generate_json(
            prompt=prompt,
            system_prompt="You are an expert anime director and Ghibli narrative designer. Respond strictly in valid JSON.",
            temperature=0.72,
        )

        raw_scenes = data.get("scenes") or data.get("Scenes") or data.get("scene_list") or data.get("shots")
        if not raw_scenes:
            for val in data.values():
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    raw_scenes = val
                    break
        if not raw_scenes:
            raise ValueError(f"JSON response from {provider_name} missing scenes list.")

        scenes = [
            GhibliScene(
                scene_index=s.get("scene_index", idx),
                narration_chunk=s.get("narration_chunk") or s.get("narration") or s.get("voiceover") or s.get("text", ""),
                visual_prompt=s.get("visual_prompt") or s.get("prompt") or s.get("image_prompt", "Studio Ghibli style cozy village"),
                motion_type=s.get("motion_type", "zoom_in"),
                asmr_cue=s.get("asmr_cue", "rain_light"),
                duration_seconds=float(s.get("duration_seconds", 7.0)),
            )
            for idx, s in enumerate(raw_scenes, start=1)
        ]

        story = GhibliStory(
            title=data.get("title", "90s के गांव का सुकून"),
            description=data.get("description", "A nostalgic journey to 90s village memories."),
            tags=data.get("tags", ["ghibli", "nostalgia", "village"]),
            thumbnail_hook=data.get("thumbnail_hook", "वो सादा बचपन..."),
            full_narration=data.get("full_narration", " ".join(s.narration_chunk for s in scenes)),
            scenes=scenes,
        )

        logger.info(f"✅ [Flow AI Director] Synthesized story successfully using '{provider_name}'!")
        return story

    def _generate_with_quota_manager(
        self,
        theme: Optional[str],
        is_shorts: bool,
        scene_count: int,
    ) -> Optional[GhibliStory]:
        """Try models in sequence to prevent 429 quota exhaustion."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)

        format_str = "YouTube Short (35-45s, high emotional hook)" if is_shorts else f"Landscape Story ({scene_count} scenes, 3-5 min)"
        prompt = f"""
You are the Lead Narrative Director for Studio Ghibli and Google Flow AI.
Craft a soulful, deeply nostalgic 90s Indian/South Asian village memory in Hindi.
Focus on emotional resonance, sensory depth (petrichor, crackling chulha, sound of rain on tin sheets), and poetic tranquility.

Format: {format_str}
Theme: {theme or '90s village monsoon rain, grandmother cooking warm rotis on clay chulha, innocent childhood simplicity'}

Structure the narrative into {scene_count} chronological cinematic scenes following Kishōtenketsu emotional flow:
1. Atmospheric Prelude: Wide shot, morning rain or golden dawn, smell of wet earth.
2. Sensory Immersion: Close tactile actions, steaming tea, clay hearth embers, childhood wonder.
3. Emotional Climax: The warmth of togetherness, unhurried 90s innocence, freedom from modern rush.
4. Soulful Afterglow: Twilight lanterns, quiet rain drizzle, heartwarming peace.

Output ONLY a JSON object with:
- "title": Heartwarming title in Hindi with English subtitle.
- "description": 2-3 poetic sentences with #ghibli #nostalgia #indianvillage #rainasmr hashtags.
- "tags": 8-10 viral tags.
- "thumbnail_hook": 3-4 word emotional Hindi phrase.
- "full_narration": Complete continuous soulful Hindi voiceover.
- "scenes": Array of {scene_count} scene objects:
  - "scene_index": 1, 2, ...
  - "narration_chunk": The calm Hindi spoken line for this scene (2 sentences).
  - "visual_prompt": Strict Flow AI prompt: 'Studio Ghibli aesthetic, Hayao Miyazaki anime style, watercolor gouache cel, soft diffused lighting, 90s Indian village, [scene details], cinematic composition'.
  - "motion_type": 'zoom_in', 'zoom_out', 'pan_left', or 'pan_right'.
  - "asmr_cue": 'rain_heavy', 'rain_light', 'chulha_fire', or 'crickets_night'.
  - "duration_seconds": 6.5 to 8.5.
"""

        generation_config = {
            "max_output_tokens": 2048,
            "temperature": 0.72,
            "response_mime_type": "application/json",
        }

        for model_name in FLOW_GEMINI_MODELS:
            try:
                logger.info(f"Trying Flow AI generation with model: '{model_name}'...")
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt, generation_config=generation_config)
                raw_text = resp.text.strip()

                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                data = json.loads(raw_text)
                scenes = [
                    GhibliScene(
                        scene_index=s["scene_index"],
                        narration_chunk=s["narration_chunk"],
                        visual_prompt=s["visual_prompt"],
                        motion_type=s.get("motion_type", "zoom_in"),
                        asmr_cue=s.get("asmr_cue", "rain_light"),
                        duration_seconds=float(s.get("duration_seconds", 7.0)),
                    )
                    for s in data["scenes"]
                ]

                story = GhibliStory(
                    title=data["title"],
                    description=data["description"],
                    tags=data.get("tags", []),
                    thumbnail_hook=data.get("thumbnail_hook", "वो सादा बचपन..."),
                    full_narration=data.get("full_narration", " ".join(s.narration_chunk for s in scenes)),
                    scenes=scenes,
                )

                logger.info(f"✅ [Flow AI Director] Successfully synthesized original story via '{model_name}'!")
                return story

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower():
                    logger.warning(f"⚠️ Model '{model_name}' quota limit reached (429). Automatically cascading to next model...")
                else:
                    logger.warning(f"Model '{model_name}' note ({err_str[:90]}). Trying next...")
                time.sleep(1.0)

        logger.warning("All Gemini models encountered quota limits. Falling back gracefully to curated Flow memory.")
        return None

    def _generate_master_flow_story(self, is_shorts: bool, scene_count: int) -> GhibliStory:
        """Deeply resonant Flow AI master story curated for maximum emotional nostalgia."""
        master_story = {
            "title": "90s के गांव की वो बारिश और दादी का चूल्हा | Soul-Healing Village Memories",
            "description": "खपरैल की छतों से टपकती वो बारिश की बूंदें, मिट्टी की सोंधी महक और दादी के चूल्हे की गर्माहट। 90s के उस सादगी भरे बचपन की यादें, जहाँ सुकून ही सबसे बड़ा धन था। #ghibli #nostalgia #indianvillage #rainasmr #cozyvibes",
            "tags": [
                "ghibli style",
                "indian village nostalgia",
                "90s memories",
                "rain asmr",
                "dadi ka chulha",
                "cozy anime hindi",
                "relaxing village life",
            ],
            "thumbnail_hook": "वो सुकून भरे दिन...",
            "full_narration": (
                "याद है 90s के वो बारिश वाले दिन? "
                "जब पहली फुहार पड़ते ही मिट्टी की वो भीनी खुशबू पूरे आंगन में तैर जाती थी। "
                "खपरैल से टपकता वो साफ पानी, और कागज़ की कश्ती को पानी के बहाव में तैराते हुए घंटो खुश होना। "
                "दादी के मिट्टी के चूल्हे से उठता हल्का सा धुआं, अदरक वाली चाय की महक, और कढ़ाही में छनछनाते गर्म पकौड़े। "
                "न कोई मोबाइल की जल्दबाजी, न कल की फिक्र... बस बारिश की मीठी खनक और अपनों का वो अनमोल साथ। "
                "काश... हम उस सादे बचपन को एक बार फिर जी पाते।"
            ),
            "scenes": [
                {
                    "scene_index": 1,
                    "narration_chunk": "याद है 90s के वो बारिश वाले दिन? जब पहली फुहार पड़ते ही मिट्टी की वो भीनी खुशबू पूरे आंगन में तैर जाती थी।",
                    "visual_prompt": "Studio Ghibli aesthetic, Hayao Miyazaki anime style, cinematic wide shot of a peaceful 1990s Indian village at dawn during gentle monsoon rain, lush emerald paddy fields, wet clay paths, dark rainclouds with soft golden rim light, watercolor gouache cel texture, poetic nostalgic tranquility",
                    "motion_type": "zoom_in",
                    "asmr_cue": "rain_light",
                    "duration_seconds": 8.0,
                },
                {
                    "scene_index": 2,
                    "narration_chunk": "खपरैल से टपकता वो साफ पानी, और कागज़ की कश्ती को पानी के बहाव में तैराते हुए घंटो खुश होना।",
                    "visual_prompt": "Studio Ghibli style, close up of terracotta tile roof eave dripping crystal raindrops into a clear village puddle, a delicate folded paper boat floating peacefully, wet vibrant banana leaves in the backdrop, warm soft diffused lighting, Hayao Miyazaki atmospheric detail",
                    "motion_type": "pan_left",
                    "asmr_cue": "rain_heavy",
                    "duration_seconds": 7.5,
                },
                {
                    "scene_index": 3,
                    "narration_chunk": "दादी के मिट्टी के चूल्हे से उठता हल्का सा धुआं, अदरक वाली चाय की महक, और कढ़ाही में छनछनाते गर्म पकौड़े।",
                    "visual_prompt": "Studio Ghibli aesthetic, cozy indoor verandah of an earthen village home, elderly grandmother in soft cotton saree gently cooking on a traditional clay chulha, glowing orange firewood embers, hot iron pan with golden fritters sizzling, fragrant steam rising, warm intimate lighting",
                    "motion_type": "zoom_out",
                    "asmr_cue": "chulha_fire",
                    "duration_seconds": 8.5,
                },
                {
                    "scene_index": 4,
                    "narration_chunk": "न कोई मोबाइल की जल्दबाजी, न कल की फिक्र... बस बारिश की मीठी खनक और अपनों का वो अनमोल साथ। काश... वो दिन लौट आते।",
                    "visual_prompt": "Studio Ghibli style, cinematic twilight shot of the tranquil village, glowing kerosene lamps shining warmly through rustic windows, reflection of twilight sky in puddles, soft misty horizon, deeply moving soulful anime masterpiece",
                    "motion_type": "pan_right",
                    "asmr_cue": "rain_light",
                    "duration_seconds": 8.0,
                },
            ],
        }

        scenes = [
            GhibliScene(
                scene_index=s["scene_index"],
                narration_chunk=s["narration_chunk"],
                visual_prompt=s["visual_prompt"],
                motion_type=s["motion_type"],
                asmr_cue=s["asmr_cue"],
                duration_seconds=s["duration_seconds"],
            )
            for s in master_story["scenes"][:scene_count]
        ]

        return GhibliStory(
            title=master_story["title"],
            description=master_story["description"],
            tags=master_story["tags"],
            thumbnail_hook=master_story["thumbnail_hook"],
            full_narration=master_story["full_narration"],
            scenes=scenes,
        )
