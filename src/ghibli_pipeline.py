"""Master Orchestration Pipeline for Ghibli-Style Studio Content.

End-to-End Autonomous Pipeline:
Story Scripting -> Flux Ghibli Painterly Scenes -> 2.5D Ken Burns Animation ->
ASMR Soundscape & Calming Narration -> Warm Subtitle Burn-In -> YouTube Publishing.
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# UTF-8 stdout configuration for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.config import (
    GEMINI_API_KEY,
    OUTPUT_DIR,
    YT_GHIBLI_REFRESH_TOKEN,
    YOUTUBE_SETTINGS,
    ensure_directories,
    get_channel_config,
)
from src.ghibli.cinematic_motion import CinematicMotionEngine
from src.ghibli.flow_director import FlowNarrativeDirector
from src.ghibli.soundscape_engine import SoundscapeEngine
from src.ghibli.story_director import GhibliStory
from src.ghibli.subtitle_styler import GhibliSubtitleStyler
from src.ghibli.visual_engine import VisualEngine
from src.uploader.drive_uploader import GoogleDriveUploader
from src.uploader.youtube_auth import YouTubeAuth
from src.uploader.youtube_upload import YouTubeUploader
from src.utils import get_ffmpeg_cmd


class GhibliPipeline:
    """Master production coordinator for @GHIBLISTYLESTUDIO-like videos."""

    def __init__(self, dry_run: bool = False, privacy: Optional[str] = None) -> None:
        self.dry_run = dry_run
        self.privacy = (privacy or YOUTUBE_SETTINGS.default_privacy_status or "public").lower()
        ensure_directories()

        self.director = FlowNarrativeDirector(api_key=GEMINI_API_KEY)
        self.visual = VisualEngine()
        self.motion = CinematicMotionEngine()
        self.sound = SoundscapeEngine()
        self.subtitles = GhibliSubtitleStyler()
        self.ffmpeg_cmd = get_ffmpeg_cmd()
        self.drive = GoogleDriveUploader()

        # YouTube uploader initialization for Ghibli channel
        self.uploader = None
        if not dry_run and YT_GHIBLI_REFRESH_TOKEN:
            try:
                auth = YouTubeAuth(refresh_token=YT_GHIBLI_REFRESH_TOKEN)
                self.uploader = YouTubeUploader(auth=auth)
                logger.info("YouTube Uploader initialized with secondary Gmail Ghibli channel credentials.")
            except Exception as e:
                logger.warning(f"YouTube Auth warning ({e}). Running in local render mode.")

    def run(
        self,
        is_shorts: bool = True,
        theme: Optional[str] = None,
        scenes: Optional[int] = None,
        burn_subtitles: bool = True,
        upload: bool = False,
        upload_drive: bool = True,
    ) -> Dict[str, Any]:
        """Execute complete automated production lifecycle.

        Args:
            is_shorts: True for 9:16 vertical Shorts (<60s), False for 16:9 landscape.
            theme: Optional custom theme or topic prompt.
            scenes: Optional custom scene count.
            burn_subtitles: Whether to burn warm ASS subtitles into the video.
            upload: Whether to upload to YouTube immediately.
            upload_drive: Whether to upload to Google Drive for phone sharing.

        Returns:
            Dictionary containing paths to output video, thumbnail, and metadata.
        """
        run_id = f"ghibli_{int(time.time())}"
        format_name = "Shorts (9:16)" if is_shorts else "Story Video (16:9)"
        logger.info(f"=== Starting Ghibli Studio Production [{format_name}, ID: {run_id}] ===")

        # -------------------------------------------------------------
        # Step 1: Script & Storyboard Formulation (Google Flow AI)
        # -------------------------------------------------------------
        scene_count = scenes or (4 if is_shorts else 6)
        story: GhibliStory = self.director.generate_flow_story(
            theme=theme,
            is_shorts=is_shorts,
            scene_count=scene_count,
        )
        logger.info(f"Story generated: '{story.title}' ({len(story.scenes)} scenes)")

        # -------------------------------------------------------------
        # Step 2: Multi-Layer Soundscape & Voice Narration
        # -------------------------------------------------------------
        voice_audio = self.sound.synthesize_narration(
            text=story.full_narration,
            output_name=run_id,
            voice="hi-IN-SwaraNeural",
        )
        total_audio_duration = self.sound.get_audio_duration(voice_audio)
        logger.info(f"Total narration audio duration: {total_audio_duration:.2f}s")

        # Distribute scene durations proportionately based on spoken text length
        total_chars = max(sum(len(s.narration_chunk) for s in story.scenes), 1)
        for s in story.scenes:
            char_ratio = len(s.narration_chunk) / total_chars
            s.duration_seconds = max(char_ratio * total_audio_duration, 4.0)

        # Normalize sum of scene durations to match audio length (+ 0.5s padding)
        target_video_duration = total_audio_duration + 0.5
        scale_factor = target_video_duration / sum(s.duration_seconds for s in story.scenes)
        for s in story.scenes:
            s.duration_seconds *= scale_factor

        # Mix soundscape (voice + procedural or file ASMR rain + cozy background)
        mixed_audio = self.sound.mix_soundscape(
            voice_audio=voice_audio,
            output_name=run_id,
        )

        # -------------------------------------------------------------
        # Step 3: Visual Generation & Ken Burns Animation
        # -------------------------------------------------------------
        scene_clips = []
        for idx, scene in enumerate(story.scenes, start=1):
            logger.info(f"Producing Scene {idx}/{len(story.scenes)}: {scene.duration_seconds:.1f}s")
            # Generate Ghibli frame
            frame_path = self.visual.generate_scene_image(
                prompt=scene.visual_prompt,
                scene_index=idx,
                is_shorts=is_shorts,
            )
            # Animate with Ken Burns 2.5D camera motion
            clip_path = self.motion.animate_scene(
                image_path=frame_path,
                scene_index=idx,
                duration=scene.duration_seconds,
                motion_type=scene.motion_type,
                is_shorts=is_shorts,
            )
            scene_clips.append(clip_path)

        # Concatenate animated scene clips
        raw_video = OUTPUT_DIR / "ghibli" / f"{run_id}_raw_video.mp4"
        self.motion.concatenate_scenes(scene_clips, raw_video)

        # -------------------------------------------------------------
        # Step 4: Subtitles & Final Video Compositing
        # -------------------------------------------------------------
        ass_path = self.subtitles.generate_subtitles(
            scenes=story.scenes,
            output_name=run_id,
            is_shorts=is_shorts,
        )

        final_video = OUTPUT_DIR / "ghibli" / f"{run_id}_final.mp4"
        clean_sub_path = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")

        logger.info(f"Compositing final video with audio and subtitles into {final_video.name}...")
        if burn_subtitles:
            cmd = [
                self.ffmpeg_cmd, "-y",
                "-i", str(raw_video),
                "-i", str(mixed_audio),
                "-vf", f"subtitles='{clean_sub_path}'",
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(final_video),
            ]
        else:
            cmd = [
                self.ffmpeg_cmd, "-y",
                "-i", str(raw_video),
                "-i", str(mixed_audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(final_video),
            ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error(f"Final compositing error: {res.stderr}")
            raise RuntimeError(f"FFmpeg compositing failed: {res.stderr[:200]}")

        # -------------------------------------------------------------
        # Step 5: Thumbnail & Social Media Caption Export
        # -------------------------------------------------------------
        thumbnail_path = OUTPUT_DIR / "ghibli" / f"{run_id}_thumbnail.jpg"
        # Generate 16:9 thumbnail frame for YouTube
        self.visual.generate_scene_image(
            prompt=f"{story.scenes[0].visual_prompt}, stunning cinematic YouTube thumbnail masterpiece, emotional lighting",
            scene_index=999,
            is_shorts=False,
        ).rename(thumbnail_path)

        # Generate copy-paste captions for Instagram Reels & TikTok
        social_pack_path = OUTPUT_DIR / "ghibli" / f"{run_id}_social_pack.txt"
        with open(social_pack_path, "w", encoding="utf-8") as f:
            f.write("==================================================\n")
            f.write("📸 INSTAGRAM REELS CAPTION (COPY & PASTE)\n")
            f.write("==================================================\n\n")
            f.write(f"✨ {story.title}\n\n")
            f.write(f"{story.description}\n\n")
            f.write("#ghibli #ghiblistyle #90skids #indianvillage #monsoon #rainasmr #cozyvibes #nostalgia #reelsindia #reels\n\n")
            f.write("==================================================\n")
            f.write("🎵 TIKTOK CAPTION (COPY & PASTE)\n")
            f.write("==================================================\n\n")
            f.write(f"{story.thumbnail_hook} 🌧️ 90s village nostalgia\n\n")
            f.write("#fyp #ghibli #nostalgia #90s #indianvillage #asmr #rain #cozy #viral\n\n")
            f.write("==================================================\n")
            f.write("💡 Pro-Tip: In Instagram/TikTok, you can keep original voice audio or search & pair with 'Studio Ghibli Lofi' sound for 3x algorithmic reach.\n")

        logger.info(f"🎉 Production Complete! Final Video: {final_video.name} ({final_video.stat().st_size / (1024*1024):.2f} MB)")
        logger.info(f"📋 Social copy-paste pack saved: {social_pack_path.name}")

        # -------------------------------------------------------------
        # Step 6: YouTube Upload (if enabled and authenticated)
        # -------------------------------------------------------------
        video_id = None
        if upload and not self.dry_run and self.uploader:
            logger.info("Uploading finalized Ghibli video to YouTube...")
            try:
                from src.scriptwriter.seo import VideoMetadata
                video_metadata = VideoMetadata(
                    title=story.title,
                    description=story.description,
                    tags=story.tags,
                    hashtags=["#ghibli", "#nostalgia", "#90skids", "#rainasmr", "#shorts"],
                    thumbnail_text=story.thumbnail_hook or "वो बारिश का दिन...",
                    category_id=24,
                )
                upload_res = self.uploader.upload_video(
                    video_path=final_video,
                    metadata=video_metadata,
                    thumbnail_path=thumbnail_path,
                    privacy_status=self.privacy,
                    channel_name="ghibli",
                    dry_run=self.dry_run,
                )
                video_id = upload_res.get("video_id")
                logger.info(f"✅ Video published to YouTube! ID: {video_id}")
            except Exception as e:
                logger.error(f"YouTube upload error: {e}")

        # -------------------------------------------------------------
        # Step 7: Google Drive Auto-Upload (Ready for Instagram & TikTok on phone)
        # -------------------------------------------------------------
        drive_link = None
        if (upload_drive or upload) and not self.dry_run:
            try:
                drive_package = self.drive.upload_package(
                    video_path=final_video,
                    thumbnail_path=thumbnail_path,
                    social_pack_path=social_pack_path,
                    folder_name="Ghibli Studio Posts",
                )
                drive_link = drive_package.get("folder_link")
                logger.info(f"📱 Ready on your phone in Google Drive! Folder: {drive_link}")
            except Exception as e:
                logger.info(f"Google Drive auto-upload note (will upload when Google token is active): {e}")

        return {
            "run_id": run_id,
            "title": story.title,
            "description": story.description,
            "tags": story.tags,
            "video_path": str(final_video.resolve()),
            "thumbnail_path": str(thumbnail_path.resolve()),
            "video_id": video_id,
            "drive_link": drive_link,
            "duration": target_video_duration,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate @GHIBLISTYLESTUDIO animated YouTube videos.")
    parser.add_argument(
        "--type",
        choices=["shorts", "story"],
        default="shorts",
        help="Video format: shorts (9:16 vertical) or story (16:9 landscape)",
    )
    parser.add_argument("--scenes", type=int, default=None, help="Number of animated scenes to produce")
    parser.add_argument("--theme", default=None, help="Custom story theme / memory description")
    parser.add_argument("--no-subs", action="store_true", help="Disable burned-in subtitles")
    parser.add_argument("--upload", action="store_true", help="Upload to secondary Gmail YouTube channel")
    parser.add_argument(
        "--privacy",
        choices=["public", "unlisted", "private"],
        default=YOUTUBE_SETTINGS.default_privacy_status,
        help="YouTube video visibility (default: public)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Operate in dry-run mode")

    args = parser.parse_args()
    pipeline = GhibliPipeline(dry_run=args.dry_run, privacy=args.privacy)
    pipeline.run(
        is_shorts=(args.type == "shorts"),
        theme=args.theme,
        scenes=args.scenes,
        burn_subtitles=not args.no_subs,
        upload=args.upload,
    )


if __name__ == "__main__":
    main()
