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
import json
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, render_template, jsonify, current_app

logger = logging.getLogger(__name__)

preflight_bp = Blueprint("preflight", __name__)

DEADLINE_ISO = "2026-04-06T00:00:00Z"


def _default_lbn_handshake_fixture() -> dict:
    """Fallback fixture when no on-disk transcript is available."""
    return {
        "session_id": "LBN-HANDSHAKE-DEMO-001",
        "protocol": "Project VOID Four-Agent Codon Handshake",
        "sealed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "participants": [
            {"agent": "Adriana", "role": "narrative_router", "model": "gpt-4o-mini"},
            {"agent": "Ara", "role": "signal_verifier", "model": "grok-2"},
            {"agent": "Gridul", "role": "mesh_orchestrator", "model": "gemini-1.5-pro"},
            {"agent": "VOID Hub", "role": "packet_gate", "model": "void-engine"},
        ],
        "turns": [
            {
                "turn": 1,
                "speaker": "Adriana",
                "model": "gpt-4o-mini",
                "route": "primary",
                "surface": "packet-build",
                "function": "identity_anchor",
                "codon": "D7-A1-3F",
                "canonical_alias": "B-nn-D",
                "summary": "Seed identity frame prepared for relay.",
            },
            {
                "turn": 2,
                "speaker": "Ara",
                "model": "grok-2",
                "route": "primary",
                "surface": "packet-verify",
                "function": "security_check",
                "codon": "K4-S9-11",
                "canonical_alias": "B-kk-S",
                "summary": "Fail-closed signature and freshness checks passed.",
            },
            {
                "turn": 3,
                "speaker": "Gridul",
                "model": "gemini-1.5-pro",
                "route": "primary",
                "surface": "mesh-relay",
                "function": "execution_pulse",
                "codon": "T2-M8-4C",
                "canonical_alias": "B-tt-M",
                "summary": "Route selected and relay pulse dispatched.",
            },
            {
                "turn": 4,
                "speaker": "VOID Hub",
                "model": "void-engine",
                "route": "primary",
                "surface": "audit-seal",
                "function": "origin_record",
                "codon": "N0-O7-B5",
                "canonical_alias": "B-nn-O",
                "summary": "Transmission sealed with audit hash and channel map.",
            },
        ],
    }


def _normalize_handshake_turn(raw: dict, idx: int, fallback_route: str) -> dict:
    turn = raw if isinstance(raw, dict) else {}
    return {
        "turn": int(turn.get("turn") or (idx + 1)),
        "speaker": str(turn.get("speaker") or "unknown").strip(),
        "model": str(turn.get("model") or "unknown").strip(),
        "route": str(turn.get("route") or fallback_route).strip(),
        "surface": str(turn.get("surface") or "").strip(),
        "function": str(turn.get("function") or "").strip(),
        "codon": str(turn.get("codon") or "").strip(),
        "canonical_alias": str(turn.get("canonical_alias") or "").strip(),
        "summary": str(turn.get("summary") or "").strip(),
    }


def _get_lbn_handshake_transcript() -> dict:
    """Return replayable four-agent handshake transcript for route audit surfaces."""
    try:
        from void_engine.lbn_runtime import load_active_payload

        active = load_active_payload()
        route = str(active.get("route") or "primary")

        root = Path(__file__).resolve().parents[1]
        fixture_override = (os.getenv("VOID_LBN_HANDSHAKE_FIXTURE_PATH") or "").strip()
        fixture_path = Path(fixture_override) if fixture_override else root / "data" / "lbn_handshake_transcript.sample.json"

        if fixture_path.exists() and fixture_path.is_file():
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        else:
            fixture = _default_lbn_handshake_fixture()

        turns_raw = fixture.get("turns") if isinstance(fixture, dict) else []
        turns_raw = turns_raw if isinstance(turns_raw, list) else []
        turns = [_normalize_handshake_turn(item, i, route) for i, item in enumerate(turns_raw)]

        codons = [t["codon"] for t in turns if t.get("codon")]
        aliases = [t["canonical_alias"] for t in turns if t.get("canonical_alias")]

        return {
            "ok": True,
            "session_id": str(fixture.get("session_id") or "LBN-HANDSHAKE-UNKNOWN"),
            "protocol": str(fixture.get("protocol") or "Project VOID LBN Handshake"),
            "sealed_at": str(fixture.get("sealed_at") or ""),
            "mode": active.get("mode"),
            "route": route,
            "active_pair": active.get("active_pair"),
            "payload_path": active.get("path"),
            "fixture_path": str(fixture_path),
            "participants": fixture.get("participants") if isinstance(fixture.get("participants"), list) else [],
            "participant_count": len(fixture.get("participants") or []),
            "turn_count": len(turns),
            "turns": turns,
            "codon_coverage": sorted(set(codons)),
            "canonical_alias_coverage": sorted(set(aliases)),
        }
    except Exception as e:
        logger.warning("Could not fetch LBN handshake transcript: %s", e)
        return {
            "ok": False,
            "error": str(e),
            "turns": [],
            "turn_count": 0,
            "participant_count": 0,
        }


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


def _get_governance_runtime_status() -> dict:
    """Return startup governance continuity enforcement status."""
    status = current_app.config.get("GOVERNANCE_BOOTSTRAP_STATUS")
    if isinstance(status, dict):
        return status

    return {
        "ok": False,
        "enforce": True,
        "errors": ["Governance bootstrap status not initialized"],
        "recursive_contract": None,
        "continuity_contract": None,
        "missing_sources": [],
    }


@preflight_bp.route("/preflight")
def preflight_page():
    wav = _get_last_wav_export()
    founder_key = _get_founder_key_status()
    patent = _get_patent_status()
    mycelium_health = _get_mycelium_health()
    governance_status = _get_governance_runtime_status()

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
        governance_status=governance_status,
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


@preflight_bp.route("/api/lbn/handshake-transcript")
def api_lbn_handshake_transcript():
    """Public transcript endpoint for replayable four-agent codon handshakes."""
    return jsonify(_get_lbn_handshake_transcript())


@preflight_bp.route("/api/governance/runtime-status")
def api_governance_runtime_status():
    """Public JSON endpoint for governance continuity bootstrap state."""
    return jsonify(_get_governance_runtime_status())
