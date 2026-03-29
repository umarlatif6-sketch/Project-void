"""
Mesa Village routes — /mesa-village and /admin/mesa
"""

import logging
from flask import Blueprint, render_template, request, redirect, jsonify, session
from routes.auth import login_required, admin_required

logger = logging.getLogger(__name__)

mesa_bp = Blueprint("mesa", __name__)


@mesa_bp.route("/mesa-village")
@login_required
def mesa_village():
    from void_engine.mesa_engine import get_latest_run, get_run_history
    latest = get_latest_run()
    history = get_run_history(10)
    return render_template(
        "mesa_village.html",
        latest=latest,
        history=history,
    )


@mesa_bp.route("/admin/mesa", methods=["GET"])
@admin_required
def admin_mesa_get():
    from void_engine.mesa_engine import get_latest_run, get_run_history
    latest = get_latest_run()
    history = get_run_history(20)
    triggered = request.args.get("triggered")
    error = request.args.get("error")
    return render_template(
        "admin_mesa.html",
        latest=latest,
        history=history,
        triggered=triggered,
        error=error,
    )


@mesa_bp.route("/admin/mesa/run", methods=["POST"])
@admin_required
def admin_mesa_run():
    try:
        agent_count = int(request.form.get("agent_count", 100))
        agent_count = max(10, min(1000, agent_count))
        rounds = int(request.form.get("rounds", 5))
        rounds = max(1, min(20, rounds))
        seed_event = (request.form.get("seed_event") or "").strip() or None
    except (ValueError, TypeError):
        return redirect("/admin/mesa?error=invalid_input")

    try:
        import threading
        from void_engine.mesa_engine import run_simulation

        def _run():
            try:
                run_simulation(agent_count=agent_count, rounds=rounds, seed_event=seed_event)
            except Exception as exc:
                logger.error("Background mesa simulation failed: %s", exc)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        return redirect(f"/admin/mesa?triggered={agent_count}")
    except Exception as e:
        logger.error("Admin mesa run failed: %s", e)
        return redirect(f"/admin/mesa?error=run_failed")


@mesa_bp.route("/api/mesa/latest")
@login_required
def api_mesa_latest():
    from void_engine.mesa_engine import get_latest_run
    latest = get_latest_run()
    if not latest:
        return jsonify({"status": "no_run", "run": None}), 200
    return jsonify({"status": "ok", "run": latest}), 200


@mesa_bp.route("/api/mesa/history")
@login_required
def api_mesa_history():
    from void_engine.mesa_engine import get_run_history
    history = get_run_history(10)
    return jsonify({"status": "ok", "history": history}), 200
