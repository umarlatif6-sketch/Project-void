"""
Pre-Flight Check — PROJECT VOID
=================================
Public sprint-status dashboard for the April 6th InteRussia Smart Cities deadline.

Routes:
  GET /preflight  — Public pre-flight command-room page (no auth required)
  GET /api/symbiotic/founder-key-status  — JSON status shim (used by Day 2 card)
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, jsonify

logger = logging.getLogger(__name__)

preflight_bp = Blueprint("preflight", __name__)

DEADLINE_ISO = "2026-04-06T00:00:00Z"


def _get_last_wav_export() -> dict:
    """Return the most recent Sovereign Manifesto WAV export from SEED_CAPTURE records."""
    try:
        from void_engine.chronicle_adriana import get_seed_captures
        captures = get_seed_captures(limit=50)
        for cap in captures:
            label = cap.get("label", "")
            if "Manifesto" in label or "manifesto" in label or "VoidEcho" in label:
                return {
                    "found": True,
                    "timestamp": cap.get("posted_at", ""),
                    "label": label,
                    "hex_digest": cap.get("hex_digest", ""),
                }
    except Exception as e:
        logger.warning("Could not fetch WAV export timestamp: %s", e)
    return {"found": False, "timestamp": None, "label": None, "hex_digest": None}


def _get_founder_key_status() -> dict:
    """Return founder key status from qisync_keygen module."""
    try:
        from void_engine.qisync_keygen import get_founder_key_status
        return get_founder_key_status()
    except Exception as e:
        logger.warning("Could not fetch founder key status: %s", e)
        return {
            "key_active": False,
            "fragment_count": 0,
            "locked_fragment_count": 0,
            "last_refresh": None,
            "fingerprint_hash": None,
            "status_label": "INACTIVE",
        }


def _get_patent_status() -> dict:
    """Return patent claim count and whitepaper route availability."""
    try:
        from void_engine.patent_loom import get_pre_generated_claims
        claims = get_pre_generated_claims()
        claim_count = len(claims)
    except Exception as e:
        logger.warning("Could not fetch patent claims: %s", e)
        claim_count = 0

    whitepaper_ok = False
    try:
        from flask import current_app
        with current_app.test_client() as tc:
            resp = tc.get("/al-jabr-286")
            whitepaper_ok = resp.status_code == 200
    except Exception as e:
        logger.warning("Could not probe /al-jabr-286: %s", e)
        whitepaper_ok = False

    return {
        "claim_count": claim_count,
        "claims_ready": claim_count >= 3,
        "whitepaper_ok": whitepaper_ok,
    }


def _resolve_day_status(condition: bool) -> str:
    return "READY" if condition else "PENDING"


@preflight_bp.route("/preflight")
def preflight_page():
    wav = _get_last_wav_export()
    founder_key = _get_founder_key_status()
    patent = _get_patent_status()

    day1_status = _resolve_day_status(wav["found"])
    day2_status = _resolve_day_status(founder_key.get("key_active", False))
    day3_status = _resolve_day_status(patent["claims_ready"] and patent["whitepaper_ok"])

    return render_template(
        "preflight.html",
        deadline_iso=DEADLINE_ISO,
        wav=wav,
        founder_key=founder_key,
        patent=patent,
        day1_status=day1_status,
        day2_status=day2_status,
        day3_status=day3_status,
    )


@preflight_bp.route("/api/symbiotic/founder-key-status")
def api_founder_key_status_shim():
    """Public JSON shim for Day 2 card status polling."""
    status = _get_founder_key_status()
    return jsonify({"ok": True, **status})
