"""
Mesa Village routes — /mesa-village, /admin/mesa, /mesa/simulate
"""

import logging
from flask import Blueprint, render_template, request, redirect, jsonify, session
from routes.auth import login_required, admin_required

logger = logging.getLogger(__name__)

mesa_bp = Blueprint("mesa", __name__)


@mesa_bp.route("/mesa-village")
@login_required
def mesa_village():
    from void_engine.mesa_engine import get_latest_run, get_run_history, get_user_owned_agent
    latest = get_latest_run()
    history = get_run_history(10)
    user_id = session.get("user_id")
    my_agent = get_user_owned_agent(user_id) if user_id else None
    return render_template(
        "mesa_village.html",
        latest=latest,
        history=history,
        my_agent=my_agent,
    )


@mesa_bp.route("/admin/mesa", methods=["GET"])
@admin_required
def admin_mesa_get():
    from void_engine.mesa_engine import get_latest_run, get_run_history, get_translation_fee
    latest = get_latest_run()
    history = get_run_history(20)
    triggered = request.args.get("triggered")
    error = request.args.get("error")
    mint_ok = request.args.get("mint_ok")
    revoke_ok = request.args.get("revoke_ok")
    mint_error = request.args.get("mint_error")
    fee_ok = request.args.get("fee_ok")
    fee_error = request.args.get("fee_error")
    current_fee = float(get_translation_fee())
    return render_template(
        "admin_mesa.html",
        latest=latest,
        history=history,
        triggered=triggered,
        error=error,
        mint_ok=mint_ok,
        revoke_ok=revoke_ok,
        mint_error=mint_error,
        fee_ok=fee_ok,
        fee_error=fee_error,
        current_fee=current_fee,
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


@mesa_bp.route("/mesa-village/agents")
@login_required
def mesa_agents_registry():
    from void_engine.mesa_engine import get_all_agent_slots, get_user_owned_agent
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    data = get_all_agent_slots(page=page, per_page=100)
    user_id = session.get("user_id")
    my_agent = get_user_owned_agent(user_id) if user_id else None
    return render_template(
        "mesa_agents.html",
        data=data,
        my_agent=my_agent,
        page=page,
    )


@mesa_bp.route("/admin/mesa/mint", methods=["POST"])
@admin_required
def admin_mesa_mint():
    try:
        agent_id = int(request.form.get("agent_id", ""))
    except (ValueError, TypeError):
        return redirect("/admin/mesa?mint_error=invalid_agent_id")

    identifier = (request.form.get("identifier") or "").strip()
    if not identifier:
        return redirect("/admin/mesa?mint_error=user_identifier_required")

    from void_engine.mesa_engine import resolve_user_for_mint, mint_agent_nft
    user_info = resolve_user_for_mint(identifier)
    if not user_info:
        return redirect(f"/admin/mesa?mint_error=user_not_found")

    result = mint_agent_nft(agent_id, user_info["user_id"], user_info["username"])
    if result["ok"]:
        return redirect(f"/admin/mesa?mint_ok={agent_id}")
    else:
        raw_err = result.get("error", "unknown")
        if "already owned" in raw_err and "Agent" in raw_err:
            err = "agent_already_owned"
        elif "already owns" in raw_err:
            err = "user_already_owns_agent"
        else:
            err = "mint_failed"
        return redirect(f"/admin/mesa?mint_error={err}")


@mesa_bp.route("/admin/mesa/revoke", methods=["POST"])
@admin_required
def admin_mesa_revoke():
    try:
        agent_id = int(request.form.get("agent_id", ""))
    except (ValueError, TypeError):
        return redirect("/admin/mesa?mint_error=invalid_input")

    from void_engine.mesa_engine import revoke_agent_nft
    result = revoke_agent_nft(agent_id)
    if result["ok"]:
        return redirect(f"/admin/mesa?revoke_ok={agent_id}")
    else:
        return redirect(f"/admin/mesa?mint_error=revoke_failed")


@mesa_bp.route("/mesa-village/agents/<int:agent_id>")
@login_required
def agent_report(agent_id: int):
    from void_engine.mesa_engine import (
        get_agent_slot, get_or_generate_agent_report,
        get_user_translation, get_translation_fee,
    )
    slot = get_agent_slot(agent_id)
    if slot is None:
        return redirect("/mesa-village/agents")

    report = get_or_generate_agent_report(agent_id)
    user_id = session.get("user_id")
    translation = None
    already_translated = False
    is_owner = bool(slot.get("owner") and slot["owner"]["user_id"] == user_id)

    if report and user_id and is_owner:
        cached = get_user_translation(agent_id, user_id, report["report_id"])
        if cached:
            translation = cached
            already_translated = True

    translate_error = request.args.get("translate_error")
    translate_ok = request.args.get("translate_ok")

    fee = get_translation_fee()

    return render_template(
        "agent_report.html",
        slot=slot,
        report=report,
        translation=translation,
        already_translated=already_translated,
        is_owner=is_owner,
        fee=float(fee),
        translate_error=translate_error,
        translate_ok=translate_ok,
    )


@mesa_bp.route("/mesa-village/agents/<int:agent_id>/translate", methods=["POST"])
@login_required
def agent_translate(agent_id: int):
    from void_engine.mesa_engine import (
        get_agent_slot, get_or_generate_agent_report, purchase_translation,
    )
    user_id = session.get("user_id")
    if not user_id:
        return redirect(f"/mesa-village/agents/{agent_id}?translate_error=not_logged_in")

    slot = get_agent_slot(agent_id)
    if slot is None:
        return redirect("/mesa-village/agents")

    if not (slot.get("owner") and slot["owner"]["user_id"] == user_id):
        return redirect(f"/mesa-village/agents/{agent_id}?translate_error=not_owner")

    report = get_or_generate_agent_report(agent_id)
    if not report:
        return redirect(f"/mesa-village/agents/{agent_id}?translate_error=no_report")

    result = purchase_translation(agent_id, user_id, report["report_id"], report["role"])
    if result["ok"]:
        return redirect(f"/mesa-village/agents/{agent_id}?translate_ok=1")
    else:
        error = result.get("error", "failed")
        if "Insufficient" in error or "insufficient" in error:
            return redirect(f"/mesa-village/agents/{agent_id}?translate_error=insufficient_peace")
        return redirect(f"/mesa-village/agents/{agent_id}?translate_error=failed")


@mesa_bp.route("/admin/mesa/fee", methods=["POST"])
@admin_required
def admin_mesa_set_fee():
    from void_engine.mesa_engine import set_translation_fee
    from decimal import Decimal, InvalidOperation
    try:
        raw = (request.form.get("translation_fee") or "").strip()
        new_fee = Decimal(raw).quantize(Decimal("0.01"))
        if new_fee <= 0:
            raise ValueError("Fee must be positive")
    except (InvalidOperation, ValueError):
        return redirect("/admin/mesa?fee_error=invalid_fee")
    ok = set_translation_fee(new_fee)
    if ok:
        return redirect(f"/admin/mesa?fee_ok={float(new_fee):.2f}")
    return redirect("/admin/mesa?fee_error=save_failed")


@mesa_bp.route("/mesa/simulate", methods=["POST"])
@login_required
def mesa_simulate():
    """
    Seed-to-agent simulation endpoint.
    Accepts: { "seed": <text>, "rounds": <int>, "agent_count": <int> }
    Returns: plain-English prediction summary + simulation metadata.
    Stores result in mesa_simulations table.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        seed_text = (data.get("seed") or "").strip()
        if not seed_text:
            return jsonify({"status": "error", "message": "seed text is required"}), 400

        agent_count = int(data.get("agent_count", 10))
        agent_count = max(2, min(30, agent_count))

        rounds = int(data.get("rounds", 3))
        rounds = max(1, min(10, rounds))
    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": f"invalid parameters: {e}"}), 400

    try:
        from void_engine.mesa_swarm import simulate_from_seed, store_simulation_result
        result = simulate_from_seed(seed_text, n_agents=agent_count, rounds=rounds)
    except Exception as e:
        logger.error("Mesa simulate failed: %s", e)
        return jsonify({"status": "error", "message": "simulation failed"}), 500

    try:
        sim_id = store_simulation_result(seed_text, agent_count, rounds, result)
    except Exception as e:
        logger.error("Mesa simulate DB store failed: %s", e)
        sim_id = None

    result["simulation_id"] = sim_id
    stored = sim_id is not None
    return jsonify({
        "status": "ok",
        "result": result,
        "stored": stored,
        **({"warning": "simulation result could not be persisted to the database"} if not stored else {}),
    }), 200
