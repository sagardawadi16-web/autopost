"""Google Drive Automated Uploader.

Uploads finalized videos, thumbnails, and copy-paste social captions directly
to a dedicated Google Drive folder ('Ghibli Studio Posts') so creators can easily
open Google Drive on their phone and share to Instagram Reels and TikTok in seconds.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


class GoogleDriveUploader:
    """Manages autonomous uploads to Google Drive."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("YOUTUBE_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.environ.get("YT_GHIBLI_REFRESH_TOKEN") or os.environ.get("YT_EN_REFRESH_TOKEN")
        self._service: Optional[Resource] = None

    def get_service(self) -> Resource:
        """Construct an authenticated Google Drive v3 client."""
        if self._service:
            return self._service

        if not self.refresh_token or not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials missing for Google Drive upload.")

        creds = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=None,
        )
        creds.refresh(Request())
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def get_or_create_folder(self, folder_name: str = "Ghibli Studio Posts") -> str:
        """Find or create target folder in Google Drive and return folder ID."""
        service = self.get_service()
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        files = res.get("files", [])

        if files:
            folder_id = files[0]["id"]
            logger.info(f"Using existing Google Drive folder: '{folder_name}' (ID: {folder_id})")
            return folder_id

        # Create folder
        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=metadata, fields="id").execute()
        folder_id = folder.get("id")
        logger.info(f"Created new Google Drive folder: '{folder_name}' (ID: {folder_id})")
        return folder_id

    def upload_file(
        self,
        file_path: Path,
        mime_type: str,
        folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a local file to Google Drive.

        Returns:
            Dictionary with file ID, name, and webViewLink.
        """
        service = self.get_service()
        file_metadata: Dict[str, Any] = {"name": file_path.name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
        uploaded = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
            .execute()
        )
        logger.info(f"Uploaded {file_path.name} to Google Drive (ID: {uploaded.get('id')})")
        return uploaded

    def upload_package(
        self,
        video_path: Path,
        thumbnail_path: Optional[Path] = None,
        social_pack_path: Optional[Path] = None,
        folder_name: str = "Ghibli Studio Posts",
    ) -> Dict[str, Any]:
        """Upload complete video package (MP4 + thumbnail + social captions) to Google Drive."""
        results = {}
        try:
            folder_id = self.get_or_create_folder(folder_name)

            # 1. Upload Video
            if video_path.exists():
                v_res = self.upload_file(video_path, "video/mp4", folder_id)
                results["video_id"] = v_res.get("id")
                results["video_link"] = v_res.get("webViewLink")

            # 2. Upload Thumbnail
            if thumbnail_path and thumbnail_path.exists():
                t_res = self.upload_file(thumbnail_path, "image/jpeg", folder_id)
                results["thumbnail_id"] = t_res.get("id")

            # 3. Upload Social Copy-Paste Pack
            if social_pack_path and social_pack_path.exists():
                s_res = self.upload_file(social_pack_path, "text/plain", folder_id)
                results["caption_link"] = s_res.get("webViewLink")

            results["folder_id"] = folder_id
            results["folder_link"] = f"https://drive.google.com/drive/folders/{folder_id}"
            logger.info(f"🎉 Complete package uploaded to Google Drive! View at: {results['folder_link']}")
        except Exception as e:
            logger.warning(
                f"⚠️ Google Drive upload notice: {e}. (Video is safely stored locally at {video_path})."
            )
            results["error"] = str(e)
            results["folder_link"] = None
        return results
