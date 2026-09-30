"""Story Director for Ghibli-Style Nostalgic Village Content.

Generates emotionally resonant 90s rural Indian/South Asian village stories and
deconstructs them into timed, scene-by-scene prompts with visual directions and ASMR sound cues.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GhibliScene:
    """Represents a single timed shot in the Ghibli video."""

    scene_index: int
    narration_chunk: str
    visual_prompt: str
    motion_type: str = "zoom_in"  # zoom_in, zoom_out, pan_left, pan_right
    asmr_cue: str = "rain_light"  # rain_light, rain_heavy, chulha_fire, chai_boil, village_morning
    duration_seconds: float = 6.0


@dataclass
class GhibliStory:
    """Complete story container with metadata and scene breakdown."""

    title: str
    description: str
    tags: List[str]
    thumbnail_hook: str
    full_narration: str
    scenes: List[GhibliScene] = field(default_factory=list)


# Hand-crafted high-fidelity curated nostalgic village stories as rock-solid templates/fallbacks
FALLBACK_STORIES: List[Dict[str, Any]] = [
    {
        "title": "90s के गांव की वो बारिश और दादी का चूल्हा | Cozy Village Memories",
        "description": "याद है वो 90s के गांव की बारिश? जब खपरैल की छत पर बूंदें गिरती थीं, मिट्टी की सौंधी खुशबू फैलती थी, और दादी चूल्हे पर गरमा-गरम चाय और पकौड़े बनाती थीं। एक सुकून भरा सफर। #ghibli #nostalgia #indianvillage #rainasmr #cozystory",
        "tags": [
            "ghibli style",
            "indian village nostalgia",
            "90s memories",
            "rain asmr",
            "dadi ka chulha",
            "monsoon village",
            "relaxing story",
            "cozy anime hindi",
        ],
        "thumbnail_hook": "वो बारिश का दिन...",
        "full_narration": (
            "याद है आपको 90s के वो बारिश वाले दिन? "
            "जब आसमान से पहली बूंद गिरती थी और मिट्टी की वो भीनी खुशबू पूरे गांव में महक उठती थी। "
            "खपरैल की छतों से टपकता वो पानी, और आंगन में कागज़ की छोटी-छोटी नावें तैराना। "
            "दादी के मिट्टी के चूल्हे से उठता वो हल्का सा धुआं, अदरक वाली गरमा-गरम चाय, और कढ़ाही में छनछनाते पकौड़े। "
            "न कोई मोबाइल की जल्दबाजी, न कोई फिक्र... बस बारिश की वो सुकून भरी खनक और अपनों का साथ। "
            "काश... वो दिन एक बार फिर लौट आते।"
        ),
        "scenes": [
            {
                "scene_index": 1,
                "narration_chunk": "याद है आपको 90s के वो बारिश वाले दिन? जब आसमान से पहली बूंद गिरती थी और मिट्टी की वो भीनी खुशबू पूरे गांव में महक उठती थी।",
                "visual_prompt": "Studio Ghibli style, peaceful 1990s Indian village during monsoon rain, lush emerald green rice fields, traditional mud and brick cottage with terracotta tiled roof, dark rain clouds, soft golden diffused ambient light, hyper-detailed watercolor texture, Hayao Miyazaki aesthetic, nostalgic peaceful atmosphere",
                "motion_type": "zoom_in",
                "asmr_cue": "rain_heavy",
                "duration_seconds": 7.0,
            },
            {
                "scene_index": 2,
                "narration_chunk": "खपरैल की छतों से टपकता वो पानी, और आंगन में कागज़ की छोटी-छोटी नावें तैराना।",
                "visual_prompt": "Studio Ghibli anime aesthetic, close up of terracotta tile roof eave dripping clear rain droplets into a muddy puddle, small folded paper boat floating in the clear rainwater puddle, lush wet banana tree leaves in background, anime watercolor gouache, cozy nostalgic mood",
                "motion_type": "pan_left",
                "asmr_cue": "rain_light",
                "duration_seconds": 6.5,
            },
            {
                "scene_index": 3,
                "narration_chunk": "दादी के मिट्टी के चूल्हे से उठता वो हल्का सा धुआं, अदरक वाली गरमा-गरम चाय, और कढ़ाही में छनछनाते पकौड़े।",
                "visual_prompt": "Studio Ghibli aesthetic, cozy indoor verandah of an Indian village cottage, kind elderly grandmother in traditional cotton saree sitting near a warm clay chulha stove, glowing orange firewood embers, hot iron pan with golden fritters pakoras sizzling, gentle fragrant steam rising, warm cozy glow, Hayao Miyazaki food animation detail",
                "motion_type": "zoom_out",
                "asmr_cue": "chulha_fire",
                "duration_seconds": 7.5,
            },
            {
                "scene_index": 4,
                "narration_chunk": "न कोई मोबाइल की जल्दबाजी, न कोई फिक्र... बस बारिश की वो सुकून भरी खनक और अपनों का साथ।",
                "visual_prompt": "Studio Ghibli style, a young child sitting on a wooden window sill wrapped in a light shawl, resting chin on hands, peacefully looking out at heavy monsoon rain washing over lush village gardens, warm indoor lantern light, peaceful serene reflection",
                "motion_type": "pan_right",
                "asmr_cue": "rain_heavy",
                "duration_seconds": 7.0,
            },
            {
                "scene_index": 5,
                "narration_chunk": "काश... वो दिन एक बार फिर लौट आते। वो सादगी और वो बेपरवाह बचपन।",
                "visual_prompt": "Studio Ghibli aesthetic, wide cinematic shot of the peaceful village at twilight after the rain, glowing yellow kerosene lanterns in cozy cottage windows, puddles reflecting evening twilight sky, soft mist over lush fields, calming cinematic masterpiece, emotional nostalgic warmth",
                "motion_type": "zoom_in",
                "asmr_cue": "rain_light",
                "duration_seconds": 6.5,
            },
        ],
    },
    {
        "title": "गांव के स्कूल की वो शाम | Nostalgic Village Childhood In 90s",
        "description": "साइकिल की घंटी, कच्चे रास्तों पर उड़ती धूल और शाम होते ही मां की वो आवाज़। 90s के बचपन का वो खोया हुआ सुकून। #ghibli #nostalgia #village #childhood #peace",
        "tags": [
            "ghibli style",
            "90s childhood nostalgia",
            "village school memories",
            "indian village anime",
            "relaxing hindi story",
            "vintage village",
        ],
        "thumbnail_hook": "स्कूल की वो शाम...",
        "full_narration": (
            "दोपहर ढलते ही स्कूल की वो पीतल वाली घंटी बजना। "
            "बस्तों को कंधे पर लटकाए दोस्तों के साथ कच्ची पगडंडियों पर दौड़ लगाना। "
            "रास्ते में बेर और इमली तोड़ना, और तालाब के किनारे थोड़ी देर बैठकर लहरों को गिनना। "
            "शाम की लालटेन जलते ही मां की वो प्यार भरी पुकार... हाथ-मुंह धोकर खाने बैठ जाओ। "
            "सचमुच, कितना अमीर था हमारा वो सादा बचपन।"
        ),
        "scenes": [
            {
                "scene_index": 1,
                "narration_chunk": "दोपहर ढलते ही स्कूल की वो पीतल वाली घंटी बजना। बस्तों को कंधे पर लटकाए दोस्तों के साथ कच्ची पगडंडियों पर दौड़ लगाना।",
                "visual_prompt": "Studio Ghibli style, rustic rural village school building with a large brass bell hanging under a banyan tree, children in simple school uniforms running happily down a sunny dirt trail, golden afternoon sunlight filtering through tree leaves, Hayao Miyazaki painterly aesthetic",
                "motion_type": "pan_right",
                "asmr_cue": "village_morning",
                "duration_seconds": 7.0,
            },
            {
                "scene_index": 2,
                "narration_chunk": "रास्ते में बेर और इमली तोड़ना, और तालाब के किनारे थोड़ी देर बैठकर लहरों को गिनना।",
                "visual_prompt": "Studio Ghibli anime art, clear serene village lotus pond, calm water ripples reflecting blue sky and fluffy white cumulus clouds, a child sitting on a wooden bench near giant green water lilies, tranquil and innocent, vibrant watercolor colors",
                "motion_type": "zoom_in",
                "asmr_cue": "rain_light",
                "duration_seconds": 6.5,
            },
            {
                "scene_index": 3,
                "narration_chunk": "शाम की लालटेन जलते ही मां की वो प्यार भरी पुकार... हाथ-मुंह धोकर खाने बैठ जाओ।",
                "visual_prompt": "Studio Ghibli aesthetic, cozy village kitchen courtyard at dusk, glowing warm lantern, mother serving steaming hot fresh rotis and vegetables in brass plates, smiling warmly, heartwarming family atmosphere, detailed warm lighting",
                "motion_type": "zoom_out",
                "asmr_cue": "chulha_fire",
                "duration_seconds": 6.5,
            },
            {
                "scene_index": 4,
                "narration_chunk": "सचमुच, कितना अमीर था हमारा वो सादा बचपन। वो बेफिक्री और वो मीठी यादें।",
                "visual_prompt": "Studio Ghibli style, rooftop view of rural village under a starlit night sky, moonlit palm trees, warm lights from village homes, peaceful tranquil night, breathtaking anime painting, nostalgic emotional beauty",
                "motion_type": "pan_left",
                "asmr_cue": "crickets_night",
                "duration_seconds": 6.0,
            },
        ],
    },
]


class StoryDirector:
    """Directs and orchestrates nostalgic Ghibli-style story scripts."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    def generate_story(
        self,
        topic: Optional[str] = None,
        is_shorts: bool = True,
        scene_count: int = 5,
    ) -> GhibliStory:
        """Generate a complete Ghibli village story with timed scenes."""
        logger.info(f"Generating Ghibli story (Format: {'Shorts' if is_shorts else 'Long-Form'}, Scenes: {scene_count})...")

        # Try Gemini LLM generation if API key is present
        if self.api_key:
            try:
                story = self._generate_with_gemini(topic=topic, is_shorts=is_shorts, scene_count=scene_count)
                if story:
                    return story
            except Exception as e:
                logger.warning(f"Gemini story generation note ({e}), utilizing curated master template.")

        # Fallback to rich curated master stories
        chosen = random.choice(FALLBACK_STORIES)
        scenes = [
            GhibliScene(
                scene_index=s["scene_index"],
                narration_chunk=s["narration_chunk"],
                visual_prompt=s["visual_prompt"],
                motion_type=s.get("motion_type", "zoom_in"),
                asmr_cue=s.get("asmr_cue", "rain_light"),
                duration_seconds=s.get("duration_seconds", 6.5),
            )
            for s in chosen["scenes"]
        ]

        if scene_count and len(scenes) > scene_count:
            scenes = scenes[:scene_count]

        return GhibliStory(
            title=chosen["title"],
            description=chosen["description"],
            tags=chosen["tags"],
            thumbnail_hook=chosen["thumbnail_hook"],
            full_narration=chosen["full_narration"],
            scenes=scenes,
        )

    def _generate_with_gemini(
        self,
        topic: Optional[str],
        is_shorts: bool,
        scene_count: int,
    ) -> Optional[GhibliStory]:
        """Use Gemini to craft an original 90s village nostalgia Ghibli script."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)

        format_desc = "YouTube Short (35-50 seconds total, 4-5 scenes)" if is_shorts else f"Long-form Story ({scene_count} scenes, 3-5 minutes)"
        prompt = f"""
You are the creative director for a viral YouTube channel inspired by @GHIBLISTYLESTUDIO.
The channel creates soul-healing, deeply nostalgic 90s Indian/South Asian village life stories with Studio Ghibli watercolor anime aesthetics and ASMR soundscapes.

Format: {format_desc}
Theme: {topic or 'Monsoon rain in 90s village, grandmother cooking on clay chulha, innocent childhood memories'}

Generate a structured JSON output with:
1. "title": Catchy, emotional Hindi/English title with emojis and #shorts if applicable.
2. "description": Heartwarming video description with hashtags.
3. "tags": 8-12 relevant tags.
4. "thumbnail_hook": 3-4 word emotional Hindi hook for thumbnail.
5. "full_narration": Complete soulful Hindi narration script.
6. "scenes": Array of {scene_count} scene objects:
   - "scene_index": 1, 2, ...
   - "narration_chunk": The Hindi spoken line for this scene (2-3 calm sentences).
   - "visual_prompt": A highly detailed prompt for image generation. MUST include: 'Studio Ghibli style, Hayao Miyazaki anime aesthetic, watercolor gouache textures, soft warm lighting, lush village scenery, 90s nostalgia'.
   - "motion_type": 'zoom_in', 'zoom_out', 'pan_left', or 'pan_right'.
   - "asmr_cue": 'rain_heavy', 'rain_light', 'chulha_fire', 'chai_boil', or 'crickets_night'.
   - "duration_seconds": 6.0 to 8.0.

Respond ONLY with valid JSON.
"""
        model = genai.GenerativeModel("gemini-3.8-flash")
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)
        scenes = [
            GhibliScene(
                scene_index=s["scene_index"],
                narration_chunk=s["narration_chunk"],
                visual_prompt=s["visual_prompt"],
                motion_type=s.get("motion_type", "zoom_in"),
                asmr_cue=s.get("asmr_cue", "rain_light"),
                duration_seconds=float(s.get("duration_seconds", 6.5)),
            )
            for s in data["scenes"]
        ]

        return GhibliStory(
            title=data["title"],
            description=data["description"],
            tags=data.get("tags", []),
            thumbnail_hook=data.get("thumbnail_hook", "वो पुराने दिन..."),
            full_narration=data.get("full_narration", " ".join(s.narration_chunk for s in scenes)),
            scenes=scenes,
        )
