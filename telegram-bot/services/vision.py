"""
Project Void — Vision Service
==============================
Sends user photos to OpenAI's vision-capable model for space analysis.
Falls back to a heuristic analysis if the API is unavailable.
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, PHOTO_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def analyze_photo(image_path: str | Path) -> dict:
    """
    Analyze a photo of a physical space and return structured JSON
    describing usable training surfaces and exercises.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Encode image to base64
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    # Determine MIME type
    suffix = image_path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = mime_map.get(suffix, "image/jpeg")

    client = _get_client()

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PHOTO_ANALYSIS_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1500,
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()

        # Extract JSON from potential markdown code fences
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        analysis = json.loads(raw)
        return analysis

    except json.JSONDecodeError:
        logger.warning("Vision API returned non-JSON; wrapping raw text.")
        return {
            "space_type": "unknown",
            "features": [
                {
                    "name": "general space",
                    "exercises": ["push-ups", "squats", "shadow boxing", "burpees"],
                    "safety_notes": "Could not parse detailed features — using universal exercises.",
                }
            ],
            "overall_assessment": raw if 'raw' in dir() else "Space analysis unavailable.",
            "vibe": "The void adapts.",
        }
    except Exception as e:
        logger.error(f"Vision API error: {e}")
        return _fallback_analysis()


def _fallback_analysis() -> dict:
    """Return a generic analysis when the API is unavailable."""
    return {
        "space_type": "unknown",
        "features": [
            {
                "name": "open floor space",
                "exercises": [
                    "push-ups", "squats", "lunges", "burpees",
                    "shadow boxing", "roundhouse kick drills",
                    "plank holds", "mountain climbers",
                ],
                "safety_notes": "Ensure clear area with no obstacles.",
            }
        ],
        "overall_assessment": (
            "I couldn't analyze the photo in detail, but every space has potential. "
            "Here's a universal routine that works anywhere."
        ),
        "vibe": "Even the void trains.",
    }
