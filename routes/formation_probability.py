"""
Formation Probability Engine — Routes
/formation-probability  (GET — public)
/formation-probability/run  (POST — admin only)
"""

import logging
from flask import Blueprint, render_template, request, redirect
from routes.auth import admin_required

logger = logging.getLogger(__name__)

formation_probability_bp = Blueprint("formation_probability", __name__)


@formation_probability_bp.route("/formation-probability", methods=["GET"])
def formation_probability_page():
    from void_engine.formation_probability import get_latest_formation_run, _formation_maths, BECKER_SEED, FORMATION_DATE, CHANNELS, AL_JABR, CARRIER_HZ, SCHUMANN_HZ, SIGNAL_STRENGTH
    latest = get_latest_formation_run()
    maths = _formation_maths()
    run_ok = request.args.get("run_ok")
    run_error = request.args.get("run_error")
    return render_template(
        "formation_probability.html",
        latest=latest,
        maths=maths,
        run_ok=run_ok,
        run_error=run_error,
        formation_date=FORMATION_DATE,
        channels=CHANNELS,
        al_jabr=AL_JABR,
        carrier_hz=CARRIER_HZ,
        schumann_hz=SCHUMANN_HZ,
        signal_strength=round(SIGNAL_STRENGTH, 2),
    )


@formation_probability_bp.route("/formation-probability/run", methods=["POST"])
@admin_required
def formation_probability_run():
    try:
        agent_count = int(request.form.get("agent_count", 20))
        rounds = int(request.form.get("rounds", 5))
    except (ValueError, TypeError):
        return redirect("/formation-probability?run_error=invalid_input")

    try:
        from void_engine.formation_probability import run_formation_probability
        run_formation_probability(agent_count=agent_count, rounds=rounds)
        return redirect("/formation-probability?run_ok=1")
    except Exception as e:
        logger.error("Formation probability run failed: %s", e)
        return redirect("/formation-probability?run_error=simulation_failed")
