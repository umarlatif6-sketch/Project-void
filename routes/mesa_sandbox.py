"""
Mesa Sandbox Scar System — Routes
Endpoints for the sandbox control panel.
"""

import logging
import threading

from flask import Blueprint, render_template, request, jsonify, session as flask_session

from routes.auth import login_required, admin_required

logger = logging.getLogger(__name__)

mesa_sandbox_bp = Blueprint("mesa_sandbox", __name__)


def _is_admin() -> bool:
    return flask_session.get("role") in ("admin", "founder")


@mesa_sandbox_bp.route("/mesa/sandbox")
@login_required
def sandbox_panel():
    from void_engine.mesa_sandbox import list_sandbox_sessions, get_live_scar_entries
    sessions = list_sandbox_sessions()
    live_scars = get_live_scar_entries(20)
    return render_template(
        "mesa_sandbox.html",
        sessions=sessions,
        live_scars=live_scars,
        is_admin=_is_admin(),
    )


@mesa_sandbox_bp.route("/api/mesa/sandbox/run", methods=["POST"])
@login_required
def api_sandbox_run():
    try:
        data = request.get_json(silent=True) or {}
        rounds = int(data.get("rounds", 5))
        seed_event = (data.get("seed_event") or "").strip() or None
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid parameters"}), 400

    try:
        from void_engine.mesa_sandbox import start_sandbox_session

        result_holder: dict = {}
        event = threading.Event()

        def _run():
            try:
                result_holder["result"] = start_sandbox_session(rounds=rounds, seed_event=seed_event)
            except Exception as exc:
                logger.error("Sandbox session failed: %s", exc)
                result_holder["error"] = str(exc)
            finally:
                event.set()

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        finished = event.wait(timeout=60)

        if not finished:
            return jsonify({
                "error": "Session is still computing — poll /api/mesa/sandbox/sessions for updates"
            }), 202

        if "error" in result_holder:
            return jsonify({"error": result_holder["error"]}), 500

        return jsonify({"success": True, "session": result_holder["result"]})
    except Exception as e:
        logger.error("Sandbox run endpoint error: %s", e)
        return jsonify({"error": str(e)}), 500


@mesa_sandbox_bp.route("/api/mesa/sandbox/merge", methods=["POST"])
@admin_required
def api_sandbox_merge():
    data = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    from void_engine.mesa_sandbox import get_sandbox_session
    sb = get_sandbox_session(session_id)
    if not sb:
        return jsonify({"error": "Session not found"}), 404

    result = sb.merge_scars()
    return jsonify(result)


@mesa_sandbox_bp.route("/api/mesa/sandbox/discard", methods=["POST"])
@admin_required
def api_sandbox_discard():
    data = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    from void_engine.mesa_sandbox import get_sandbox_session
    sb = get_sandbox_session(session_id)
    if not sb:
        return jsonify({"error": "Session not found"}), 404

    result = sb.discard()
    return jsonify(result)


@mesa_sandbox_bp.route("/api/mesa/sandbox/sessions")
@login_required
def api_sandbox_sessions():
    from void_engine.mesa_sandbox import list_sandbox_sessions
    return jsonify({"sessions": list_sandbox_sessions()})


@mesa_sandbox_bp.route("/api/mesa/sandbox/session/<session_id>")
@login_required
def api_sandbox_session_detail(session_id: str):
    from void_engine.mesa_sandbox import get_sandbox_session
    sb = get_sandbox_session(session_id)
    if not sb:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(sb.to_dict())


@mesa_sandbox_bp.route("/api/mesa/sandbox/live_scars")
@login_required
def api_sandbox_live_scars():
    from void_engine.mesa_sandbox import get_live_scar_entries
    scars = get_live_scar_entries(50)
    return jsonify({"scars": scars, "count": len(scars)})
