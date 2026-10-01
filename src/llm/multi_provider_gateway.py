"""Resilient Multi-Provider LLM Gateway with Token Quota Bypass.

Architecture & Invariants:
1. Tier 1: Zero-Touch Keyless Provider (Pollinations.ai Text API - 100% free, 0 key, 0 rate limit).
2. Tier 2: Free 3rd-Party Providers (Groq Cloud, OpenRouter, Cloudflare Workers AI - if keys set).
3. Tier 3: Auxiliary Gemini Keys (Round-robin rotation over GEMINI_BACKUP_KEYS).
4. Tier 4: Primary User Gemini API Key (GEMINI_API_KEY) - STRICT USER INVARIANT: Touched LAST among live LLMs!
5. Robust JSON Parser with markdown cleaning and schema extraction.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Standalone CLI path resilience
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.config import (
    GEMINI_API_KEY,
    GEMINI_BACKUP_KEYS,
    GROQ_API_KEY,
    OPENROUTER_API_KEY,
    CF_API_TOKEN,
    CF_ACCOUNT_ID,
)

logger = logging.getLogger(__name__)


def extract_clean_json(text: str) -> Dict[str, Any]:
    """Extract and parse a JSON object from raw LLM output."""
    cleaned = text.strip()

    # Strip markdown code blocks
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    # Direct JSON parse attempt
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Regex extraction of outermost { ... }
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # Trailing comma cleanup
        fixed = re.sub(r",\s*([\]}])", r"\1", candidate)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        # Try repairing cut-off JSON by closing unclosed brackets/braces
        for repair in [fixed + '"]}', fixed + '"}', fixed + ']}', fixed + '}']:
            try:
                return json.loads(repair)
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not extract valid JSON from response: {cleaned[:200]}...")


# ==============================================================================
# Abstract Provider Interface
# ==============================================================================

class BaseLLMProvider(ABC):
    """Base class for all LLM providers in the gateway."""

    name: str = "BaseProvider"
    tier: int = 1

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider has necessary credentials/network availability."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_json: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate raw text response from provider."""
        pass


# ==============================================================================
# Tier 1: Keyless Zero-Hassle Provider (Pollinations.ai)
# ==============================================================================

class PollinationsProvider(BaseLLMProvider):
    """100% Keyless, zero-touch text API from Pollinations.ai.
    
    Zero configuration required. Operates with high availability.
    """

    name = "Pollinations (Keyless)"
    tier = 1

    def __init__(self, models: Optional[List[str]] = None) -> None:
        self.models = models or ["openai-fast"]

    def is_available(self) -> bool:
        return True

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_json: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for model in self.models:
            try:
                payload = {
                    "messages": messages,
                    "model": model,
                    "jsonMode": response_json,
                    "temperature": temperature,
                }
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    "https://text.pollinations.ai/",
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "autopost/2.0 (Studio-Ghibli-Engine)",
                    },
                )
                with urllib.request.urlopen(req, timeout=45) as resp:
                    text = resp.read().decode("utf-8").strip()
                    if text:
                        return text
            except Exception as e:
                logger.warning(f"Pollinations model '{model}' warning: {e}. Trying next...")
                last_error = e

        raise RuntimeError(f"Pollinations API failed across models: {last_error}")


# ==============================================================================
# Tier 2: Free 3rd-Party Providers (Groq & OpenRouter & CF)
# ==============================================================================

class GroqProvider(BaseLLMProvider):
    """Groq Cloud API provider (Ultra-fast, generous free tier)."""

    name = "Groq Cloud"
    tier = 2

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or GROQ_API_KEY
        self.models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_json: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self.is_available():
            raise ValueError("Groq API key not configured.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for model in self.models:
            try:
                body: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_json:
                    body["response_format"] = {"type": "json_object"}

                data = json.dumps(body).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                        "User-Agent": "autopost/2.0",
                    },
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    return res_json["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"Groq model '{model}' error: {e}. Cascading...")
                last_error = e

        raise RuntimeError(f"Groq API failed: {last_error}")


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Free Tier Provider (Direct access to :free models)."""

    name = "OpenRouter (Free)"
    tier = 2

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or OPENROUTER_API_KEY
        self.models = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
        ]

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_json: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self.is_available():
            raise ValueError("OpenRouter API key not configured.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for model in self.models:
            try:
                body: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_json:
                    body["response_format"] = {"type": "json_object"}

                data = json.dumps(body).encode("utf-8")
                req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://github.com/sagardawadi16-web/autopost",
                        "X-Title": "Autopost Multi-Provider Gateway",
                    },
                )
                with urllib.request.urlopen(req, timeout=25) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    return res_json["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"OpenRouter model '{model}' error: {e}. Cascading...")
                last_error = e

        raise RuntimeError(f"OpenRouter API failed: {last_error}")


# ==============================================================================
# Tier 3 & Tier 4: Gemini Multi-Key & Primary Key Provider
# ==============================================================================

class GeminiRotatorProvider(BaseLLMProvider):
    """Gemini API Provider with multi-model cascade and multi-key rotation.
    
    Can operate in:
    - Auxiliary Mode (Tier 3): Iterates through backup keys only.
    - Primary User Mode (Tier 4): Strict invariant - executed LAST among live LLMs.
    """

    models = [
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest",
        "gemini-3.8-flash",
    ]

    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        is_primary_user_key: bool = False,
    ) -> None:
        self.is_primary = is_primary_user_key
        self.name = "Gemini Primary Key (User)" if is_primary_user_key else "Gemini Auxiliary Pool"
        self.tier = 4 if is_primary_user_key else 3

        if is_primary_user_key:
            self.keys = [GEMINI_API_KEY] if GEMINI_API_KEY else []
        else:
            self.keys = api_keys or GEMINI_BACKUP_KEYS

        self._key_index = 0

    def is_available(self) -> bool:
        return any(k and k.strip() for k in self.keys)

    def _get_current_key(self) -> str:
        valid_keys = [k for k in self.keys if k and k.strip()]
        if not valid_keys:
            raise ValueError(f"No valid Gemini keys available for {self.name}.")
        return valid_keys[self._key_index % len(valid_keys)]

    def _advance_key(self) -> None:
        self._key_index = (self._key_index + 1) % max(1, len(self.keys))

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_json: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self.is_available():
            raise ValueError(f"Provider '{self.name}' has no available API keys.")

        import google.generativeai as genai

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System Instructions:\n{system_prompt}\n\nTask:\n{prompt}"

        gen_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_json:
            gen_config["response_mime_type"] = "application/json"

        # Try across keys and models
        initial_key_idx = self._key_index
        keys_to_try = len([k for k in self.keys if k and k.strip()])

        for _ in range(keys_to_try):
            current_key = self._get_current_key()
            genai.configure(api_key=current_key)

            for model_name in self.models:
                try:
                    logger.info(f"[{self.name}] Calling model '{model_name}'...")
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content(full_prompt, generation_config=gen_config)
                    text = resp.text.strip()
                    if text:
                        return text
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "quota" in err_str.lower():
                        logger.warning(
                            f"[{self.name}] Model '{model_name}' quota exhausted (429). Cascading..."
                        )
                    else:
                        logger.warning(f"[{self.name}] Model '{model_name}' error: {e}")
                    continue

            # If all models failed for this key, rotate to next backup key
            logger.warning(f"[{self.name}] All models exhausted for current key. Rotating key...")
            self._advance_key()

        raise RuntimeError(f"All models and keys exhausted on {self.name}.")


# ==============================================================================
# Master Gateway
# ==============================================================================

class MultiProviderGateway:
    """Master Multi-Provider LLM Gateway.
    
    Orchestrates tier-based failover with zero-downtime and preserves the user's
    primary API key as the absolute last resort.
    """

    def __init__(
        self,
        enable_keyless: bool = True,
        enable_third_party: bool = True,
        enable_auxiliary_gemini: bool = True,
        enable_primary_gemini: bool = True,
    ) -> None:
        self.providers: List[BaseLLMProvider] = []

        # Tier 1: Zero-touch keyless (Pollinations)
        if enable_keyless:
            self.providers.append(PollinationsProvider())

        # Tier 2: Free 3rd-party providers (Groq & OpenRouter)
        if enable_third_party:
            self.providers.append(GroqProvider())
            self.providers.append(OpenRouterProvider())

        # Tier 3: Auxiliary Gemini backup pool
        if enable_auxiliary_gemini:
            self.providers.append(GeminiRotatorProvider(is_primary_user_key=False))

        # Tier 4: Primary User Gemini Key (CRITICAL: Placed strictly LAST)
        if enable_primary_gemini:
            self.providers.append(GeminiRotatorProvider(is_primary_user_key=True))

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.72,
        max_tokens: int = 2048,
    ) -> Tuple[Dict[str, Any], str]:
        """Generate structured JSON, automatically trying providers in strict priority order.
        
        Returns:
            Tuple of (parsed_json_dict, provider_name_that_succeeded)
        """
        last_error = None

        for provider in self.providers:
            if not provider.is_available():
                continue

            try:
                logger.info(
                    f"🚀 [Gateway] Routing request to Tier {provider.tier}: '{provider.name}'..."
                )
                raw_text = provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    response_json=True,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                parsed = extract_clean_json(raw_text)
                logger.info(
                    f"✅ [Gateway] Successfully generated structured output via '{provider.name}'!"
                )
                return parsed, provider.name

            except Exception as e:
                logger.warning(
                    f"⚠️ [Gateway] Provider '{provider.name}' failed ({e}). Auto-failing over to next provider..."
                )
                last_error = e

        raise RuntimeError(
            f"All gateway providers exhausted. Last error: {last_error}"
        )

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Tuple[str, str]:
        """Generate plain text output across available providers."""
        last_error = None

        for provider in self.providers:
            if not provider.is_available():
                continue

            try:
                logger.info(
                    f"🚀 [Gateway] Routing request to Tier {provider.tier}: '{provider.name}'..."
                )
                text = provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    response_json=False,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                logger.info(f"✅ [Gateway] Output generated via '{provider.name}'!")
                return text, provider.name

            except Exception as e:
                logger.warning(f"⚠️ [Gateway] Provider '{provider.name}' failed: {e}. Cascading...")
                last_error = e

        raise RuntimeError(f"All gateway providers exhausted. Last error: {last_error}")


# Global shared gateway singleton
gateway = MultiProviderGateway()
