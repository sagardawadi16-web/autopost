"""Cross-platform utility functions, binary locators, and Gemini API fallback helper."""

from __future__ import annotations

import logging
import os
import shutil
import time
from pathlib import Path
from typing import List, Optional

# Automatically load .env if present
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    try:
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass

logger = logging.getLogger(__name__)

# Known standard installation paths on Windows for FFmpeg
KNOWN_FFMPEG_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.2-full_build" / "bin" / "ffmpeg.exe",
    Path("C:/ffmpeg/bin/ffmpeg.exe"),
    Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
    Path("C:/ProgramData/chocolatey/bin/ffmpeg.exe"),
]

# Preferred models in priority order
PREFERRED_GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]


def get_ffmpeg_cmd() -> str:
    """Resolve the working command/path to the FFmpeg executable."""
    found = shutil.which("ffmpeg")
    if found:
        return found

    for p in KNOWN_FFMPEG_PATHS:
        if p.exists():
            return str(p.resolve())

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


def call_gemini_with_fallback(
    prompt: str,
    system_instruction: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Invoke LLM with resilient multi-provider fallback.

    Tier 1 keyless (Pollinations) is tried first to preserve user quota.
    Primary user GEMINI_API_KEY is touched strictly as the last live resort.

    Args:
        prompt: User prompt content.
        system_instruction: Optional system instruction.
        api_key: Gemini API key.

    Returns:
        Generated text response.
    """
    # 1. First attempt resilient MultiProviderGateway (Tier 1 Keyless -> Tier 2 Free -> Tier 3 Backup Keys)
    try:
        from src.llm.multi_provider_gateway import gateway
        text, provider_name = gateway.generate_text(
            prompt=prompt,
            system_prompt=system_instruction,
        )
        if text and text.strip():
            logger.info(f"Generated text response via '{provider_name}'.")
            return text.strip()
    except Exception as gw_err:
        logger.warning(f"Gateway generation note: {gw_err}. Cascading to direct Gemini loop...")

    # 2. Direct Gemini model loop if gateway was bypassed or explicitly requested
    import google.generativeai as genai

    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured and gateway exhausted.")

    genai.configure(api_key=key)

    last_error: Optional[Exception] = None
    for model_name in PREFERRED_GEMINI_MODELS:
        try:
            logger.info(f"Invoking Gemini model: {model_name}...")
            kwargs = {}
            if system_instruction:
                kwargs["system_instruction"] = system_instruction
            model = genai.GenerativeModel(model_name, **kwargs)
            res = model.generate_content(prompt)
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Model {model_name} encountered error: {err_str[:120]}... Trying next model.")
            last_error = e
            if "429" in err_str or "quota" in err_str.lower():
                logger.warning("Gemini API quota exhausted (429). Fast-failing to offline fallback engine.")
                raise e
            time.sleep(0.5)

    if last_error:
        raise last_error
    raise RuntimeError("All Gemini models failed.")
