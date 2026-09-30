"""Interactive YouTube Channel OAuth2 Authorizer.

Generates persistent refresh tokens for English and Hindi channels using Google OAuth 2.0 flow.
Automatically saves tokens to .env and syncs them to GitHub Secrets for autonomous CI/CD publishing.
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import src.config  # Automatically loads .env file

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def update_env_file(key: str, value: str, env_path: Optional[Path] = None) -> None:
    """Safely append or update a key in the local .env file."""
    if env_path is None:
        from src.config import BASE_DIR
        env_path = BASE_DIR / ".env"

    lines = []
    found = False
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}=") or line.startswith(f"#{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)

    if not found:
        lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info(f"Updated {key} in {env_path.name}")


def sync_github_secret(repo: str, secret_name: str, secret_value: str) -> bool:
    """Sync secret to GitHub Actions repository secrets using gh CLI."""
    try:
        cmd = ["gh", "secret", "set", secret_name, "--repo", repo, "--body", secret_value]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Synchronized secret '{secret_name}' to GitHub repository '{repo}'")
        return True
    except Exception as e:
        logger.warning(f"Could not auto-sync secret to GitHub ({e}). You can set it manually in GitHub Settings.")
        return False


def authorize_channel(channel: str, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> str:
    """Run interactive local server OAuth flow to obtain channel refresh token."""
    cid = client_id or os.environ.get("YOUTUBE_CLIENT_ID")
    csecret = client_secret or os.environ.get("YOUTUBE_CLIENT_SECRET")

    print("\n" + "=" * 60)
    print(f"  YOUTUBE OAUTH2 SETUP FOR CHANNEL: {channel.upper()}")
    print("=" * 60)

    if not cid:
        cid = input("Enter your Google Cloud OAuth Client ID: ").strip()
    if not csecret:
        csecret = input("Enter your Google Cloud OAuth Client Secret: ").strip()

    if not cid or not csecret:
        print("❌ Error: Both Client ID and Client Secret are required.")
        sys.exit(1)

    # Save client credentials to .env
    update_env_file("YOUTUBE_CLIENT_ID", cid)
    update_env_file("YOUTUBE_CLIENT_SECRET", csecret)

    client_config = {
        "installed": {
            "client_id": cid,
            "client_secret": csecret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"],
        }
    }

    flow = InstalledAppFlow.from_client_config(
        client_config=client_config,
        scopes=YOUTUBE_SCOPES,
    )

    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    print("\n" + "=" * 60)
    print("🌐 GOOGLE YOUTUBE AUTHORIZATION LINK:")
    print(auth_url)
    print("=" * 60)
    print("👉 If your browser did not automatically open, click or paste the URL above.")
    print("👉 Sign in with your YouTube channel account.")
    print("👉 If you see 'Google hasn't verified this app', click 'Advanced' -> 'Go to AutoPost (unsafe)' -> 'Allow'.\n")

    creds = None
    for test_port in (8080, 8090, 8888, 0):
        try:
            logger.info(f"Starting local OAuth listener on port {test_port}...")
            creds = flow.run_local_server(
                port=test_port,
                prompt="consent",
                access_type="offline",
                open_browser=True,
            )
            if creds:
                break
        except OSError as e:
            logger.warning(f"Port {test_port} unavailable ({e}), trying next port...")

    if not creds:
        raise RuntimeError("Failed to bind OAuth listener to any local port.")

    refresh_token = creds.refresh_token
    if not refresh_token:
        print("⚠️ Warning: No refresh token returned. Did you grant offline access?")
        sys.exit(1)

    # Test the connection by retrieving the channel title
    try:
        yt_service = build("youtube", "v3", credentials=creds)
        channels_resp = yt_service.channels().list(mine=True, part="snippet").execute()
        items = channels_resp.get("items", [])
        channel_title = items[0]["snippet"]["title"] if items else "Unknown"
        print(f"\n🎉 Connected successfully to YouTube Channel: '{channel_title}'!")
    except Exception as e:
        print(f"Note: Token generated, but channel metadata fetch had note: {e}")

    # Determine token variable names (both short and descriptive forms)
    short_var = "YT_EN_REFRESH_TOKEN" if channel == "english" else "YT_HI_REFRESH_TOKEN"
    long_var = f"YT_{channel.upper()}_REFRESH_TOKEN"
    update_env_file(short_var, refresh_token)
    update_env_file(long_var, refresh_token)

    # Sync to GitHub Actions Secrets
    repo_name = "sagardawadi16-web/autopost"
    sync_github_secret(repo_name, "YT_CLIENT_ID", cid)
    sync_github_secret(repo_name, "YT_CLIENT_SECRET", csecret)
    sync_github_secret(repo_name, short_var, refresh_token)
    sync_github_secret(repo_name, long_var, refresh_token)

    print(f"\n✅ All set! Token saved to .env as '{short_var}' and '{long_var}' and synchronized to GitHub Actions!")
    return refresh_token


def main() -> None:
    parser = argparse.ArgumentParser(description="Authorize YouTube Channel OAuth access.")
    parser.add_argument(
        "--channel",
        choices=["english", "hindi"],
        default="english",
        help="Target channel profile (english or hindi)",
    )
    parser.add_argument("--client-id", default=None, help="Google OAuth Client ID")
    parser.add_argument("--client-secret", default=None, help="Google OAuth Client Secret")

    args = parser.parse_args()
    authorize_channel(args.channel, args.client_id, args.client_secret)


if __name__ == "__main__":
    main()
