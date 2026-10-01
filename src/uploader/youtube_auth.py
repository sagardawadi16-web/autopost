"""YouTube OAuth2 Authentication and Credential Manager.

Provides headless OAuth2 authentication using client credentials and refresh tokens,
allowing automated pipeline execution in CI/CD and cloud workers without interactive browser logins.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

logger = logging.getLogger(__name__)

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


class YouTubeAuth:
    """Manages YouTube OAuth2 credentials and service client generation."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        """Initialize YouTube authentication.

        Args:
            client_id: Google OAuth client ID.
            client_secret: Google OAuth client secret.
            refresh_token: Long-lived refresh token for the specific channel.
        """
        self.client_id = client_id or os.environ.get("YOUTUBE_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = refresh_token

    def get_service(self) -> Resource:
        """Construct an authenticated YouTube Resource client.

        Returns:
            Google API client Resource for YouTube Data API v3.

        Raises:
            ValueError: If credentials or refresh token are missing.
        """
        if not self.refresh_token:
            raise ValueError(
                "YouTube refresh token is missing. Please provide a valid refresh token."
            )
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "YouTube client_id or client_secret is missing from environment/config."
            )

        creds = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=None,
        )

        # Refresh access token
        creds.refresh(Request())
        logger.info("Successfully refreshed YouTube OAuth2 access token")

        return build("youtube", "v3", credentials=creds, cache_discovery=False)
