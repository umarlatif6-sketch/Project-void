import logging
from flask import Blueprint, render_template, request, jsonify, session, redirect
from routes.auth import admin_required
from void_engine.agent_vision import search, api_status, MODES

logger = logging.getLogger(__name__)

agent_vision_bp = Blueprint("agent_vision", __name__)


@agent_vision_bp.route("/admin/agent-vision", methods=["GET"])
@admin_required
def agent_vision_dashboard():
    statuses = api_status()
    return render_template("admin_agent_vision.html", statuses=statuses, modes=MODES)


@agent_vision_bp.route("/api/agent-vision/search", methods=["POST"])
@admin_required
def agent_vision_search():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    mode = (data.get("mode") or "").strip()

    if not query:
        return jsonify({"error": "query is required"}), 400
    if mode not in MODES:
        return jsonify({"error": f"Invalid mode. Must be one of: {MODES}"}), 400

    try:
        result = search(query, mode)
        result.pop("raw", None)
        return jsonify({"success": True, "result": result})
    except EnvironmentError as e:
        return jsonify({"error": str(e), "type": "config"}), 503
    except RuntimeError as e:
        return jsonify({"error": str(e), "type": "api"}), 502
    except Exception as e:
        logger.exception("Agent Vision search error: %s", e)
        return jsonify({"error": "Internal error", "type": "unknown"}), 500


@agent_vision_bp.route("/api/agent-vision/status", methods=["GET"])
@admin_required
def agent_vision_status():
    return jsonify(api_status())
