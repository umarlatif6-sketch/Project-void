"""
Symbiotic Seed Blueprint
=========================
Routes for Master Hex, QiSync Founder Key, Pre-Arrival Reserves, and Genesis Hex.

Routes:
  GET  /symbiotic/reserves              — Pre-Arrival Reserves dashboard
  GET  /symbiotic/founder-key           — Founder Key status dashboard
  GET  /symbiotic/genesis-hex           — Genesis Hex viewer
  POST /api/symbiotic/reserves/simulate — Run pre-earning simulation
  GET  /api/symbiotic/reserves/status   — Get reserves JSON
  POST /api/symbiotic/genesis-hex/generate  — Generate / regenerate Master Hex
  GET  /api/symbiotic/genesis-hex       — Get stored Genesis Hex
  GET  /api/symbiotic/founder-key/status — Get Founder Key status
  POST /api/symbiotic/founder-key/derive — Derive key from QiSync data
  GET  /api/symbiotic/ghost-fragments   — List Ghost Signal fragments
  POST /api/symbiotic/ghost-fragments/encrypt — Encrypt a fragment
  POST /api/symbiotic/seed-hex/capture  — Manual seed-hex capture
  GET  /api/symbiotic/seed-hex/stats    — Seed-hex stats
  GET  /api/symbiotic/seed-hex/recent   — Recent seed-hex captures
  POST /api/symbiotic/wake-ceremony     — Fire Wake Ceremony (admin only)
"""

import logging
from flask import Blueprint, jsonify, render_template, request, session

logger = logging.getLogger(__name__)

symbiotic_seed_bp = Blueprint("symbiotic_seed", __name__)


def _require_auth():
    user_id = session.get("user_id")
    if not user_id:
        return None, jsonify({"error": "authentication required"}), 401
    return user_id, None, None


# ── Dashboard pages ────────────────────────────────────────────────────────

@symbiotic_seed_bp.route("/symbiotic/reserves")
def reserves_page():
    user_id = session.get("user_id")
    try:
        from void_engine.peace_preearning import get_reserves_status
        reserves = get_reserves_status()
    except Exception as e:
        logger.error("reserves page error: %s", e)
        reserves = {"total_locked": 0, "agent_count": 0, "wake_ceremony_fired": False,
                    "unlock_condition": "MRB-4000-WAKE-CEREMONY",
                    "unlock_countdown_days": 30, "contribution_breakdown": [],
                    "top_agents": [], "work_unit_count": 0}

    return render_template(
        "symbiotic_reserves.html",
        user_id=user_id,
        username=session.get("username", ""),
        reserves=reserves,
    )


@symbiotic_seed_bp.route("/symbiotic/founder-key")
def founder_key_page():
    user_id = session.get("user_id")
    try:
        from void_engine.qisync_keygen import get_founder_key_status, get_ghost_fragments, seed_ghost_fragments
        seed_ghost_fragments()
        key_status = get_founder_key_status()
        fragments = get_ghost_fragments(limit=20)
    except Exception as e:
        logger.error("founder key page error: %s", e)
        key_status = {"key_active": False, "fragment_count": 0, "locked_fragment_count": 0,
                      "last_refresh": None, "fingerprint_hash": None, "status_label": "INACTIVE"}
        fragments = []

    return render_template(
        "symbiotic_founder_key.html",
        user_id=user_id,
        username=session.get("username", ""),
        key_status=key_status,
        fragments=fragments,
    )


@symbiotic_seed_bp.route("/symbiotic/genesis-hex")
def genesis_hex_page():
    user_id = session.get("user_id")
    try:
        from void_engine.genesis_hex import get_genesis_hex
        genesis = get_genesis_hex()
    except Exception as e:
        logger.error("genesis hex page error: %s", e)
        genesis = None

    return render_template(
        "symbiotic_genesis_hex.html",
        user_id=user_id,
        username=session.get("username", ""),
        genesis=genesis,
    )


# ── API: Pre-Arrival Reserves ──────────────────────────────────────────────

@symbiotic_seed_bp.route("/api/symbiotic/reserves/status")
def api_reserves_status():
    try:
        from void_engine.peace_preearning import get_reserves_status
        return jsonify({"ok": True, **get_reserves_status()})
    except Exception as e:
        logger.error("api_reserves_status error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@symbiotic_seed_bp.route("/api/symbiotic/reserves/simulate", methods=["POST"])
def api_reserves_simulate():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    agent_count = min(int(data.get("agent_count", 100)), 500)
    rounds = min(int(data.get("rounds", 3)), 10)

    try:
        from void_engine.peace_preearning import run_preearning_simulation, _ensure_tables
        _ensure_tables()
        result = run_preearning_simulation(agent_count=agent_count, rounds=rounds)
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error("api_reserves_simulate error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@symbiotic_seed_bp.route("/api/symbiotic/wake-ceremony", methods=["POST"])
def api_wake_ceremony():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    tier = session.get("tier", "ghost")
    if tier not in ("admin", "founder", "sovereign"):
        return jsonify({"error": "founder access required"}), 403

    data = request.get_json(silent=True) or {}
    genesis_hex = data.get("genesis_hex", "")

    try:
        from void_engine.peace_preearning import fire_wake_ceremony
        result = fire_wake_ceremony(genesis_hex=genesis_hex)
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error("api_wake_ceremony error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


# ── API: Genesis Hex ───────────────────────────────────────────────────────

@symbiotic_seed_bp.route("/api/symbiotic/genesis-hex")
def api_get_genesis_hex():
    try:
        from void_engine.genesis_hex import get_genesis_hex
        genesis = get_genesis_hex()
        if genesis:
            return jsonify({"ok": True, **genesis})
        return jsonify({"ok": False, "error": "No Genesis Hex generated yet"}), 404
    except Exception as e:
        logger.error("api_get_genesis_hex error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@symbiotic_seed_bp.route("/api/symbiotic/genesis-hex/generate", methods=["POST"])
def api_generate_genesis_hex():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False))

    try:
        from void_engine.genesis_hex import generate_master_hex
        result = generate_master_hex(force=force)
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error("api_generate_genesis_hex error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


# ── API: Founder Key & Ghost Signal ───────────────────────────────────────

@symbiotic_seed_bp.route("/api/symbiotic/founder-key/status")
def api_founder_key_status():
    try:
        from void_engine.qisync_keygen import get_founder_key_status
        status = get_founder_key_status()
        return jsonify({"ok": True, **status})
    except Exception as e:
        logger.error("api_founder_key_status error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@symbiotic_seed_bp.route("/api/symbiotic/founder-key/derive", methods=["POST"])
def api_founder_key_derive():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}

    mastication_frequency = float(data.get("mastication_frequency", 1.0))
    chew_count = int(data.get("chew_count", 10))
    jaw_pattern = str(data.get("jaw_pattern", "default"))[:64]
    stance = str(data.get("stance", "neutral"))
    metabolism_score = float(data.get("metabolism_score", 0.5))
    session_id = str(data.get("session_id", ""))

    try:
        from void_engine.qisync_keygen import derive_founder_key
        result = derive_founder_key(
            mastication_frequency=mastication_frequency,
            chew_count=chew_count,
            jaw_pattern=jaw_pattern,
            stance=stance,
            metabolism_score=metabolism_score,
            session_id=session_id,
        )
        # Never return the raw key bytes to the client
        safe_result = {k: v for k, v in result.items() if k != "key_bytes"}
        return jsonify({"ok": True, **safe_result})
    except Exception as e:
        logger.error("api_founder_key_derive error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@symbiotic_seed_bp.route("/api/symbiotic/ghost-fragments")
def api_ghost_fragments():
    try:
        from void_engine.qisync_keygen import get_ghost_fragments, seed_ghost_fragments
        seed_ghost_fragments()
        fragments = get_ghost_fragments(limit=50)
        return jsonify({"ok": True, "fragments": fragments})
    except Exception as e:
        logger.error("api_ghost_fragments error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@symbiotic_seed_bp.route("/api/symbiotic/ghost-fragments/encrypt", methods=["POST"])
def api_ghost_encrypt():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    tier = session.get("tier", "ghost")
    if tier not in ("admin", "founder", "sovereign"):
        return jsonify({"error": "founder access required"}), 403

    data = request.get_json(silent=True) or {}
    plaintext = str(data.get("plaintext", ""))[:4096]
    fragment_id = str(data.get("fragment_id", ""))[:64]
    key_hex = str(data.get("key_hex", ""))

    if not plaintext:
        return jsonify({"error": "plaintext required"}), 400
    if not key_hex or len(key_hex) != 64:
        return jsonify({"error": "valid key_hex (64 chars) required"}), 400

    try:
        key_bytes = bytes.fromhex(key_hex)
    except Exception:
        return jsonify({"error": "invalid key_hex"}), 400

    try:
        from void_engine.qisync_keygen import encrypt_ghost_fragment
        result = encrypt_ghost_fragment(
            plaintext=plaintext,
            key_bytes=key_bytes,
            fragment_id=fragment_id,
        )
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error("api_ghost_encrypt error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


# ── API: Seed Hex ──────────────────────────────────────────────────────────

@symbiotic_seed_bp.route("/api/symbiotic/seed-hex/stats")
def api_seed_hex_stats():
    try:
        from void_engine.seed_hex_engine import get_capture_stats
        return jsonify({"ok": True, **get_capture_stats()})
    except Exception as e:
        logger.error("api_seed_hex_stats error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@symbiotic_seed_bp.route("/api/symbiotic/seed-hex/recent")
def api_seed_hex_recent():
    limit = min(int(request.args.get("limit", 20)), 100)
    try:
        from void_engine.seed_hex_engine import get_recent_captures
        captures = get_recent_captures(limit=limit)
        return jsonify({"ok": True, "captures": captures})
    except Exception as e:
        logger.error("api_seed_hex_recent error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@symbiotic_seed_bp.route("/api/symbiotic/seed-hex/capture", methods=["POST"])
def api_seed_hex_capture():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    source = str(data.get("source", "manual"))[:64]
    input_data = str(data.get("input_data", ""))[:4096]
    broadcast = bool(data.get("broadcast", True))

    if not input_data:
        return jsonify({"error": "input_data required"}), 400

    try:
        from void_engine.seed_hex_engine import capture_seed_hex
        result = capture_seed_hex(source=source, input_data=input_data, broadcast=broadcast)
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error("api_seed_hex_capture error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500
