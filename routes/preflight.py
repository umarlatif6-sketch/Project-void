"""
Pre-Flight Check — PROJECT VOID
=================================
Public sprint-status dashboard for the April 6th InteRussia Smart Cities deadline.

Routes:
  GET /preflight  — Public pre-flight command-room page (no auth required)
  GET /api/symbiotic/founder-key-status  — JSON status shim (used by Day 2 card)
"""

import logging
import os
from pathlib import Path
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


def _get_lbn_runtime_status() -> dict:
    """Return active SCL-LBN runtime routing status for operator checks."""
    try:
        from void_engine.lbn_runtime import load_active_payload, lbn_validation_enabled

        active = load_active_payload()
        mode = (active.get("mode") or "project").strip().lower()
        route = (active.get("route") or "primary").strip().lower()

        root = Path(__file__).resolve().parents[1]
        project_pack = root / "data" / "lbn_three_hour_pack.project.json"
        project_payload = root / "data" / "lbn_agent_payloads.project.json"
        standalone_pack = root / "data" / "lbn_three_hour_pack.standalone.json"
        standalone_payload = root / "data" / "lbn_agent_payloads.standalone.json"

        return {
            "ok": bool(active.get("ok")),
            "mode": mode,
            "route": route,
            "validate": bool(lbn_validation_enabled()),
            "active_pair": active.get("active_pair"),
            "primary_pair": active.get("primary_pair"),
            "fallback_pair": active.get("fallback_pair"),
            "payload_path": active.get("path"),
            "payload_reason": active.get("reason"),
            "channels": active.get("channels", []),
            "channel_count": len(active.get("channels", [])),
            "codon_count": len(active.get("codon_map", {}) or {}),
            "codon_alias_preview": {
                key: value
                for key, value in list((active.get("codon_map", {}) or {}).items())[:10]
                if isinstance(key, str)
            },
            "switches": {
                "VOID_LBN_MODE": os.getenv("VOID_LBN_MODE") or "project",
                "VOID_LBN_ACTIVE_ROUTE": os.getenv("VOID_LBN_ACTIVE_ROUTE") or "primary",
                "VOID_LBN_VALIDATE": os.getenv("VOID_LBN_VALIDATE") or "false",
                "VOID_LBN_PAYLOAD_PATH": os.getenv("VOID_LBN_PAYLOAD_PATH") or "",
            },
            "artifact_presence": {
                "project_pack": project_pack.exists(),
                "project_payload": project_payload.exists(),
                "standalone_pack": standalone_pack.exists(),
                "standalone_payload": standalone_payload.exists(),
            },
        }
    except Exception as e:
        logger.warning("Could not fetch LBN runtime status: %s", e)
        return {
            "ok": False,
            "mode": "project",
            "route": "primary",
            "validate": False,
            "error": str(e),
        }


def _get_lbn_payload_map() -> dict:
    """Return active payload codon map for audit and resolver telemetry surfaces."""
    try:
        from void_engine.lbn_runtime import load_active_payload

        active = load_active_payload()
        codon_map = active.get("codon_map", {}) or {}

        functions = {
            key: value
            for key, value in codon_map.items()
            if isinstance(key, str) and not key.endswith("_canonical")
        }
        canonical_aliases = {
            key: value
            for key, value in codon_map.items()
            if isinstance(key, str) and key.endswith("_canonical")
        }

        return {
            "ok": bool(active.get("ok")),
            "mode": active.get("mode"),
            "route": active.get("route"),
            "active_pair": active.get("active_pair"),
            "payload_path": active.get("path"),
            "functions": functions,
            "canonical_aliases": canonical_aliases,
            "function_count": len(functions),
            "canonical_alias_count": len(canonical_aliases),
        }
    except Exception as e:
        logger.warning("Could not fetch LBN payload map: %s", e)
        return {
            "ok": False,
            "error": str(e),
            "functions": {},
            "canonical_aliases": {},
            "function_count": 0,
            "canonical_alias_count": 0,
        }


def _get_mycelium_health() -> dict:
    """Return the latest organism health summary for operators."""
    try:
        from scripts.mycelium_health_check import build_report

        report = build_report()
        summary = report.get("summary", {})
        return {
            "ok": True,
            "overall_status": report.get("overall_status", "warn"),
            "summary": summary,
            "report_type": report.get("report_type", "mycelium_health_check"),
            "section_statuses": {
                key: value.get("status")
                for key, value in report.get("sections", {}).items()
            },
        }
    except Exception as e:
        logger.warning("Could not build mycelium health report: %s", e)
        return {
            "ok": False,
            "overall_status": "fail",
            "summary": {"pass": 0, "warn": 0, "fail": 1},
            "error": str(e),
            "section_statuses": {},
        }


@preflight_bp.route("/preflight")
def preflight_page():
    wav = _get_last_wav_export()
    founder_key = _get_founder_key_status()
    patent = _get_patent_status()
    mycelium_health = _get_mycelium_health()

    day1_status = _resolve_day_status(wav["found"])
    day2_status = _resolve_day_status(founder_key.get("key_active", False))
    day3_status = _resolve_day_status(patent["claims_ready"] and patent["whitepaper_ok"])

    return render_template(
        "preflight.html",
        deadline_iso=DEADLINE_ISO,
        wav=wav,
        founder_key=founder_key,
        patent=patent,
        mycelium_health=mycelium_health,
        day1_status=day1_status,
        day2_status=day2_status,
        day3_status=day3_status,
    )


@preflight_bp.route("/api/symbiotic/founder-key-status")
def api_founder_key_status_shim():
    """Public JSON shim for Day 2 card status polling."""
    status = _get_founder_key_status()
    return jsonify({"ok": True, **status})


@preflight_bp.route("/api/lbn/runtime-status")
def api_lbn_runtime_status():
    """Public JSON status endpoint for active LBN route lock and artifact readiness."""
    status = _get_lbn_runtime_status()
    return jsonify(status)


@preflight_bp.route("/api/lbn/payload-map")
def api_lbn_payload_map():
    """Public JSON payload-map endpoint for codon resolver and telemetry overlays."""
    payload_map = _get_lbn_payload_map()
    return jsonify(payload_map)


@preflight_bp.route("/api/mycelium/health")
def api_mycelium_health():
    """Public JSON endpoint for the organism health summary."""
    return jsonify(_get_mycelium_health())
