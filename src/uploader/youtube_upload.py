"""YouTube Video Uploader and Metadata Publisher.

Uploads rendered MP4 videos, attaches custom thumbnails, sets visibility status,
and logs publication history to data/upload_log.json.
Includes full dry-run simulation mode for testing.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from googleapiclient.http import MediaFileUpload

from src.config import DATA_DIR, YOUTUBE_SETTINGS
from src.scriptwriter.seo import VideoMetadata
from src.uploader.youtube_auth import YouTubeAuth

logger = logging.getLogger(__name__)


class YouTubeUploader:
    """Publishes videos and thumbnails to YouTube via YouTube Data API v3."""

    def __init__(
        self,
        auth: Optional[YouTubeAuth] = None,
        log_file: Optional[Path] = None,
    ) -> None:
        """Initialize YouTube uploader.

        Args:
            auth: YouTubeAuth instance for the target channel.
            log_file: Path to upload log file.
        """
        self.auth = auth
        self.log_file = log_file or (DATA_DIR / "upload_log.json")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def upload_video(
        self,
        video_path: Path,
        metadata: VideoMetadata,
        thumbnail_path: Optional[Path] = None,
        privacy_status: str = "unlisted",
        channel_name: str = "english",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Upload video file and attach thumbnail.

        Args:
            video_path: Path to MP4 file.
            metadata: VideoMetadata containing title, description, tags.
            thumbnail_path: Optional path to custom thumbnail JPEG.
            privacy_status: 'private', 'unlisted', or 'public'.
            channel_name: Identifier of the channel ('english' or 'hindi').
            dry_run: If True, simulates upload without contacting YouTube.

        Returns:
            Dictionary with upload result (video_id, url, status).
        """
        if dry_run:
            logger.info(f"[DRY-RUN] Simulating YouTube upload for '{video_path.name}'...")
            fake_id = f"sim_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            res = {
                "video_id": fake_id,
                "url": f"https://youtu.be/{fake_id}",
                "title": metadata.title,
                "privacy_status": privacy_status,
                "channel": channel_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dry_run": True,
            }
            self._log_upload(res)
            return res

        if not self.auth:
            raise ValueError("YouTubeAuth instance must be provided for live uploads.")

        youtube = self.auth.get_service()

        body = {
            "snippet": {
                "title": metadata.title,
                "description": metadata.description,
                "tags": metadata.tags,
                "categoryId": str(metadata.category_id or YOUTUBE_SETTINGS.category_id),
                "defaultLanguage": "en" if channel_name == "english" else "hi",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": YOUTUBE_SETTINGS.self_declared_made_for_kids,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            chunksize=1024 * 1024 * 4,
            resumable=True,
        )

        logger.info(f"Uploading '{video_path.name}' to YouTube ({channel_name} channel)...")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = request.execute()
        video_id = response.get("id")
        video_url = f"https://youtu.be/{video_id}"
        logger.info(f"Video uploaded successfully! ID: {video_id} -> {video_url}")

        # Upload custom thumbnail if present
        if thumbnail_path and thumbnail_path.exists() and video_id:
            try:
                logger.info(f"Uploading custom thumbnail '{thumbnail_path.name}' for video {video_id}...")
                thumb_media = MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
                youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
                logger.info("Custom thumbnail attached successfully")
            except Exception as e:
                logger.warning(f"Failed to set custom thumbnail: {e}")

        result_payload = {
            "video_id": video_id,
            "url": video_url,
            "title": metadata.title,
            "privacy_status": privacy_status,
            "channel": channel_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": False,
        }
        self._log_upload(result_payload)
        return result_payload

    def _log_upload(self, entry: Dict[str, Any]) -> None:
        """Append upload record to upload_log.json."""
        records = []
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                records = []

        records.append(entry)

        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write upload log: {e}")
