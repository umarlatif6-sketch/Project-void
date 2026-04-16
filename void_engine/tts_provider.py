"""
Unified TTS provider for PROJECT VOID.

Supports:
- OpenAI-compatible speech API
- ElevenLabs-compatible text-to-speech API (including self-hosted variants)
- VoxCPM (OpenBMB) speech synthesis with per-user voice sovereignty

Selection is controlled by environment variables:
- TTS_PROVIDER=auto|openai|elevenlabs|elevenlabs_oss|voxcpm
- AI_INTEGRATIONS_OPENAI_API_KEY / OPENAI_API_KEY
- AI_INTEGRATIONS_OPENAI_BASE_URL
- TTS_OPENAI_MODEL (default: tts-1)
- TTS_OPENAI_VOICE (default: alloy)
- ELEVENLABS_API_KEY
- ELEVENLABS_BASE_URL (default: https://api.elevenlabs.io/v1)
- ELEVENLABS_MODEL_ID (default: eleven_multilingual_v2)
- VOXCPM_BASE_URL (default: http://localhost:8000)
- VOXCPM_MODEL_PATH (default: checkpoints/checkpoint_step_1000.pth)
- VOXCPM_SPEAKER_EMBEDDING_DB (path to speaker embedding database)
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)


def _normalise_provider(provider: Optional[str]) -> str:
    p = (provider or os.environ.get("TTS_PROVIDER", "auto")).strip().lower()
    aliases = {
        "elevenlabs_oss": "elevenlabs",
        "elevenlabs-compatible": "elevenlabs",
        "openai_compatible": "openai",
    }
    return aliases.get(p, p)


def _pick_auto_provider() -> str:
    eleven_base = os.environ.get("ELEVENLABS_BASE_URL", "").strip()
    eleven_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    openai_key = (
        os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )

    # Prefer ElevenLabs-compatible when explicitly configured or keyed.
    if eleven_key or eleven_base:
        return "elevenlabs"
    if openai_key:
        return "openai"
    # Default fallback so caller gets a direct configuration error message.
    return "openai"


def _synth_openai(text: str, voice: str) -> bytes:
    from openai import OpenAI

    api_key = (
        os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or ""
    ).strip()
    if not api_key:
        raise RuntimeError("OpenAI TTS selected but no API key is configured")

    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "").strip() or None
    model = os.environ.get("TTS_OPENAI_MODEL", "tts-1").strip() or "tts-1"

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="mp3",
    )
    return response.content


def _synth_elevenlabs(text: str, voice: str) -> bytes:
    base_url = os.environ.get("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1").rstrip("/")
    model_id = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip()
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()

    if not voice:
        raise RuntimeError("ElevenLabs-compatible TTS requires a voice id")

    url = f"{base_url}/text-to-speech/{voice}"
    payload = json.dumps(
        {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }
    ).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    if api_key:
        headers["xi-api-key"] = api_key

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read()


def _synth_voxcpm(text: str, voice: str, user_id: Optional[str] = None) -> bytes:
    """
    Synthesize audio using OpenBMB/VoxCPM model.
    
    Args:
        text: Text to synthesize
        voice: Speaker embedding ID or user-specific voice profile ID
        user_id: Optional user ID for voice profile lookup from database
    
    Returns:
        MP3 audio bytes
    """
    base_url = os.environ.get("VOXCPM_BASE_URL", "http://localhost:8000").rstrip("/")
    model_path = os.environ.get("VOXCPM_MODEL_PATH", "checkpoints/checkpoint_step_1000.pth").strip()
    speaker_db = os.environ.get("VOXCPM_SPEAKER_EMBEDDING_DB", "").strip()
    
    # If user_id provided, look up voice profile from database
    speaker_embedding = voice  # default to provided voice
    if user_id and speaker_db:
        try:
            speaker_embedding = _lookup_user_voice_profile(user_id, speaker_db)
        except Exception as e:
            logger.warning(f"Failed to lookup user voice profile for {user_id}, using default: {e}")
            # Fall back to provided voice parameter or Adriana sovereign voice
            speaker_embedding = voice or os.environ.get("VOXCPM_ADRIANA_VOICE", "adriana_sovereign")
    
    url = f"{base_url}/synthesize"
    payload = json.dumps({
        "text": text,
        "speaker_embedding": speaker_embedding,
        "model_path": model_path,
        "language": "en",
        "prosody_speed": 1.0,
    }).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        raise RuntimeError(f"VoxCPM synthesis failed: {e}")


def _lookup_user_voice_profile(user_id: str, speaker_db_path: str) -> str:
    """
    Lookup user's unique voice profile from database.
    
    This enables voice sovereignty: each user agent has persistent voice identity.
    
    Args:
        user_id: User identifier
        speaker_db_path: Path to speaker embedding database (JSON or database)
    
    Returns:
        Speaker embedding ID for user
    """
    try:
        if speaker_db_path.endswith(".json"):
            with open(speaker_db_path, "r") as f:
                profiles = json.load(f)
                return profiles.get(user_id, os.environ.get("VOXCPM_DEFAULT_VOICE", "default_speaker"))
        else:
            # Could be extended to support database lookups
            logger.warning(f"Speaker DB format not recognized: {speaker_db_path}")
            return os.environ.get("VOXCPM_DEFAULT_VOICE", "default_speaker")
    except FileNotFoundError:
        logger.warning(f"Speaker database not found: {speaker_db_path}")
        return os.environ.get("VOXCPM_DEFAULT_VOICE", "default_speaker")


def synthesize_mp3(text: str, voice: Optional[str] = None, provider: Optional[str] = None, user_id: Optional[str] = None) -> bytes:
    provider_norm = _normalise_provider(provider)
    if provider_norm == "auto":
        provider_norm = _pick_auto_provider()

    if provider_norm == "openai":
        chosen_voice = voice or os.environ.get("TTS_OPENAI_VOICE", "alloy")
        return _synth_openai(text, chosen_voice)

    if provider_norm == "elevenlabs":
        # OpenAI-style voice names are common in existing routes; ignore those
        # for ElevenLabs-compatible providers and use explicit voice id config.
        openai_voice_names = {"alloy", "nova", "shimmer", "onyx", "fable"}
        if (voice or "").strip().lower() in openai_voice_names:
            chosen_voice = os.environ.get("TTS_ELEVENLABS_VOICE", "")
        else:
            chosen_voice = voice or os.environ.get("TTS_ELEVENLABS_VOICE", "")
        return _synth_elevenlabs(text, chosen_voice)

    if provider_norm == "voxcpm":
        chosen_voice = voice or os.environ.get("VOXCPM_DEFAULT_VOICE", "default_speaker")
        return _synth_voxcpm(text, chosen_voice, user_id=user_id)

    raise RuntimeError(f"Unsupported TTS_PROVIDER: {provider_norm}")


def synthesize_long_text_mp3(
    text: str,
    voice: Optional[str] = None,
    provider: Optional[str] = None,
    user_id: Optional[str] = None,
    max_chars: int = 3800,
) -> bytes:
    words = text.split()
    if not words:
        return b""

    chunks = []
    current = []
    current_len = 0
    for word in words:
        word_len = len(word) + 1
        if current_len + word_len > max_chars:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += word_len
    if current:
        chunks.append(" ".join(current))

    audio_bytes = b""
    for chunk in chunks:
        audio_bytes += synthesize_mp3(chunk, voice=voice, provider=provider, user_id=user_id)
    return audio_bytes


def get_tts_runtime_info(provider: Optional[str] = None) -> dict:
    """Return non-secret runtime info for diagnostics and health endpoints."""
    provider_norm = _normalise_provider(provider)
    resolved = _pick_auto_provider() if provider_norm == "auto" else provider_norm

    return {
        "requested_provider": provider_norm,
        "resolved_provider": resolved,
        "openai_base_url": os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1",
        "openai_model": os.environ.get("TTS_OPENAI_MODEL", "tts-1").strip() or "tts-1",
        "openai_voice": os.environ.get("TTS_OPENAI_VOICE", "alloy").strip() or "alloy",
        "elevenlabs_base_url": os.environ.get("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1").strip() or "https://api.elevenlabs.io/v1",
        "elevenlabs_model_id": os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip() or "eleven_multilingual_v2",
        "elevenlabs_default_voice": os.environ.get("TTS_ELEVENLABS_VOICE", "").strip(),
        "voxcpm_base_url": os.environ.get("VOXCPM_BASE_URL", "http://localhost:8000").strip() or "http://localhost:8000",
        "voxcpm_model_path": os.environ.get("VOXCPM_MODEL_PATH", "checkpoints/checkpoint_step_1000.pth").strip(),
        "voxcpm_speaker_db": bool(os.environ.get("VOXCPM_SPEAKER_EMBEDDING_DB", "").strip()),
        "has_openai_key": bool(
            (os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "").strip())
            or (os.environ.get("OPENAI_API_KEY", "").strip())
        ),
        "has_elevenlabs_key": bool(os.environ.get("ELEVENLABS_API_KEY", "").strip()),
        "voxcpm_available": bool(os.environ.get("VOXCPM_BASE_URL", "").strip()),
    }


def run_tts_probe(text: str = "health check", voice: Optional[str] = None, provider: Optional[str] = None) -> dict:
    """
    Execute a tiny synthesis probe to validate connectivity and credentials.
    Returns a dict with ok/error and output length metadata.
    """
    info = get_tts_runtime_info(provider=provider)
    try:
        audio = synthesize_mp3(text=text, voice=voice, provider=provider)
        return {
            "ok": True,
            "bytes": len(audio),
            "provider": info["resolved_provider"],
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": info["resolved_provider"],
            "error": str(exc),
        }