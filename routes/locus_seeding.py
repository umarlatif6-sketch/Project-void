"""
Locus Seeding — Digital Haunting Routes

Routes:
  GET  /locus-seeding                 — Ghost Signal status page
  POST /locus-seeding/create          — Create a new locus session
  POST /locus-seeding/broadcast       — Manually trigger a broadcast
  POST /locus-seeding/pause           — Pause broadcasting
  POST /locus-seeding/resume          — Resume broadcasting
  POST /locus-seeding/wake-ceremony   — Trigger MRB-4000 arrival Wake Ceremony
  GET  /api/locus-seeding/status      — JSON status for active session
  GET  /api/locus-seeding/log         — JSON broadcast log
"""

import logging
from flask import Blueprint, render_template, request, jsonify, session, redirect

from routes.auth import login_required, admin_required

logger = logging.getLogger(__name__)

locus_seeding_bp = Blueprint("locus_seeding", __name__)


def _require_founder(f):
    import functools
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect("/login")
        role = session.get("role", "user")
        if role != "founder":
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Founder access required"}), 403
            return redirect("/")
        return f(*args, **kwargs)
    return decorated


@locus_seeding_bp.route("/locus-seeding")
@admin_required
def locus_seeding_page():
    from void_engine.locus_seeding import get_all_locus_sessions, get_broadcast_log

    sessions_list = get_all_locus_sessions()
    active_session = None
    broadcasts = []

    for s in sessions_list:
        if s.get("is_active") and not s.get("mrb_arrived"):
            active_session = s
            break

    if not active_session and sessions_list:
        active_session = sessions_list[0]

    if active_session:
        broadcasts = get_broadcast_log(active_session["id"], limit=50)

    return render_template(
        "locus_seeding.html",
        sessions=sessions_list,
        active_session=active_session,
        broadcasts=broadcasts,
    )


@locus_seeding_bp.route("/locus-seeding/create", methods=["POST"])
@admin_required
def create_locus():
    label = (request.form.get("label") or "").strip()
    latitude = request.form.get("latitude", "").strip()
    longitude = request.form.get("longitude", "").strip()
    interval_seconds = request.form.get("interval_seconds", "300").strip()

    if not label or not latitude or not longitude:
        return redirect("/locus-seeding?error=missing_fields")

    try:
        lat = float(latitude)
        lon = float(longitude)
        interval = max(60, min(3600, int(interval_seconds)))
    except (ValueError, TypeError):
        return redirect("/locus-seeding?error=invalid_coords")

    try:
        from void_engine.locus_seeding import create_locus_session, _start_broadcast_scheduler
        new_session = create_locus_session(label, lat, lon, interval)
        _start_broadcast_scheduler(new_session["id"])

        from void_engine.locus_seeding import broadcast_fragment
        broadcast_fragment(new_session["id"])

        return redirect(f"/locus-seeding?created={new_session['id']}")
    except Exception as e:
        logger.error("[LocusSeeding] Create error: %s", e)
        return redirect("/locus-seeding?error=create_failed")


@locus_seeding_bp.route("/locus-seeding/broadcast", methods=["POST"])
@admin_required
def manual_broadcast():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id") or request.form.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    try:
        session_id = int(session_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid session_id"}), 400

    try:
        from void_engine.locus_seeding import broadcast_fragment, get_locus_session
        locus = get_locus_session(session_id)
        if not locus:
            return jsonify({"error": "Session not found"}), 404
        if locus.get("mrb_arrived"):
            return jsonify({"error": "MRB-4000 has arrived — session complete"}), 400

        result = broadcast_fragment(session_id)
        return jsonify(result)
    except Exception as e:
        logger.error("[LocusSeeding] Manual broadcast error: %s", e)
        return jsonify({"error": str(e)}), 500


@locus_seeding_bp.route("/locus-seeding/pause", methods=["POST"])
@admin_required
def pause_locus():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id") or request.form.get("session_id")

    try:
        session_id = int(session_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid session_id"}), 400

    from void_engine.locus_seeding import pause_locus_session
    result = pause_locus_session(session_id)
    return jsonify(result)


@locus_seeding_bp.route("/locus-seeding/resume", methods=["POST"])
@admin_required
def resume_locus():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id") or request.form.get("session_id")

    try:
        session_id = int(session_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid session_id"}), 400

    from void_engine.locus_seeding import resume_locus_session
    result = resume_locus_session(session_id)
    return jsonify(result)


@locus_seeding_bp.route("/locus-seeding/wake-ceremony", methods=["POST"])
@_require_founder
def wake_ceremony():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id") or request.form.get("session_id")

    try:
        session_id = int(session_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid session_id"}), 400

    try:
        from void_engine.locus_seeding import trigger_wake_ceremony
        result = trigger_wake_ceremony(session_id)
        return jsonify(result)
    except Exception as e:
        logger.error("[LocusSeeding] Wake ceremony error: %s", e)
        return jsonify({"error": str(e)}), 500


@locus_seeding_bp.route("/api/locus-seeding/status")
@admin_required
def api_locus_status():
    try:
        from void_engine.locus_seeding import get_all_locus_sessions, get_broadcast_log
        sessions_list = get_all_locus_sessions()
        active = None
        for s in sessions_list:
            if s.get("is_active") and not s.get("mrb_arrived"):
                active = s
                break

        broadcasts = []
        if active:
            broadcasts = get_broadcast_log(active["id"], limit=20)

        return jsonify({
            "active_session": active,
            "all_sessions": sessions_list,
            "recent_broadcasts": broadcasts,
        })
    except Exception as e:
        logger.error("[LocusSeeding] Status API error: %s", e)
        return jsonify({"error": str(e)}), 500


@locus_seeding_bp.route("/api/locus-seeding/log")
@admin_required
def api_locus_log():
    session_id = request.args.get("session_id")
    try:
        limit = max(1, min(200, int(request.args.get("limit", 50))))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid limit"}), 400

    try:
        session_id = int(session_id) if session_id else None
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid session_id"}), 400

    try:
        from void_engine.locus_seeding import get_broadcast_log, get_active_locus_session, get_locus_session
        if session_id:
            locus = get_locus_session(session_id)
        else:
            locus = get_active_locus_session()

        if not locus:
            return jsonify({"broadcasts": [], "session": None})

        broadcasts = get_broadcast_log(locus["id"], limit=limit)
        return jsonify({
            "session": locus,
            "broadcasts": broadcasts,
            "count": len(broadcasts),
        })
    except Exception as e:
        logger.error("[LocusSeeding] Log API error: %s", e)
        return jsonify({"error": str(e)}), 500
