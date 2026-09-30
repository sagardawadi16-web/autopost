"""Cross-platform utility functions and binary locators for FFmpeg and FFprobe."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Known standard installation paths on Windows for FFmpeg
KNOWN_FFMPEG_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.2-full_build" / "bin" / "ffmpeg.exe",
    Path("C:/ffmpeg/bin/ffmpeg.exe"),
    Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
    Path("C:/ProgramData/chocolatey/bin/ffmpeg.exe"),
]


def get_ffmpeg_cmd() -> str:
    """Resolve the working command/path to the FFmpeg executable."""
    # 1. Check if 'ffmpeg' is already in system PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    # 2. Check known Windows locations
    for p in KNOWN_FFMPEG_PATHS:
        if p.exists():
            return str(p.resolve())

    # 3. Search under WinGet packages directory dynamically
    winget_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_dir.exists():
        candidates = list(winget_dir.glob("**/ffmpeg.exe"))
        if candidates:
            return str(candidates[0].resolve())

    return "ffmpeg"


def get_ffprobe_cmd() -> str:
    """Resolve the working command/path to the FFprobe executable."""
    found = shutil.which("ffprobe")
    if found:
        return found

    ffmpeg_path = Path(get_ffmpeg_cmd())
    if ffmpeg_path.is_file():
        probe_sibling = ffmpeg_path.parent / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if probe_sibling.exists():
            return str(probe_sibling.resolve())

    return "ffprobe"
