"""
Grok X routes — PROJECT VOID
/grok-x          : Grok X terminal (public)
/grok-x/audit    : Platform audit (POST)
/grok-x/predict  : Seed prediction (POST)
/api/grok/status : JSON status check
"""

import logging
from flask import Blueprint, render_template, request, jsonify, session

logger = logging.getLogger(__name__)

grok_bp = Blueprint("grok_ai", __name__)


@grok_bp.route("/grok-x")
def grok_terminal():
    from void_engine.grok_integration import grok_available, get_grok_sessions, init_grok_tables, GROK_USER_ID
    init_grok_tables()
    sessions = get_grok_sessions(limit=10)
    return render_template(
        "grok_terminal.html",
        grok_active=grok_available(),
        sessions=sessions,
        grok_user_id=GROK_USER_ID,
    )


@grok_bp.route("/grok-x/audit", methods=["POST"])
def grok_audit():
    from void_engine.grok_integration import grok_test_platform, store_grok_session
    result = grok_test_platform()
    store_grok_session("platform_audit", "Full platform test", result)
    return jsonify(result)


@grok_bp.route("/grok-x/predict", methods=["POST"])
def grok_predict():
    data = request.get_json(silent=True) or {}
    seed = (data.get("seed") or "").strip()
    if not seed:
        return jsonify({"ok": False, "error": "Seed text required"}), 400
    n_agents = max(5, min(50, int(data.get("n_agents", 20))))
    rounds = max(1, min(10, int(data.get("rounds", 5))))
    from void_engine.grok_integration import grok_run_prediction, store_grok_session
    result = grok_run_prediction(seed, n_agents=n_agents, rounds=rounds)
    store_grok_session("void_prediction", seed, result)
    return jsonify(result)


@grok_bp.route("/grok-x/speak", methods=["POST"])
def grok_speak_endpoint():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "Prompt required"}), 400
    from void_engine.grok_integration import grok_speak, store_grok_session
    result = grok_speak(prompt)
    store_grok_session("direct_speak", prompt, result)
    return jsonify(result)


@grok_bp.route("/api/grok/status")
def grok_status():
    from void_engine.grok_integration import grok_available, GROK_USER_ID, GROK_MODEL
    return jsonify({
        "ok": True,
        "active": grok_available(),
        "user_id": GROK_USER_ID,
        "username": "grok_x",
        "display_name": "Grok X — xAI",
        "model": GROK_MODEL,
        "tier": "sovereign",
        "message": "XAI_API_KEY required to activate" if not grok_available() else "Grok X is live",
    })
