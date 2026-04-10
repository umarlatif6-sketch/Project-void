"""
Formation Probability Engine — Routes
/formation-probability        (GET  — public)
/formation-probability/run    (POST — admin only, single swarm)
/formation-probability/full-scan  (POST — admin only, all four systems)
"""

import logging
from flask import Blueprint, render_template, request, redirect, jsonify
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


@formation_probability_bp.route("/formation-probability/full-scan", methods=["POST"])
@admin_required
def formation_full_scan():
    """
    Run all four agent systems simultaneously against the Becker formation seed.
    Returns JSON — called via AJAX from the frontend.
    """
    try:
        data = request.get_json(silent=True) or {}
        swarm_agents  = int(data.get("swarm_agents", 10))
        swarm_rounds  = int(data.get("swarm_rounds", 3))
        engine_agents = int(data.get("engine_agents", 15))
        engine_rounds = int(data.get("engine_rounds", 3))
        sandbox_rounds = int(data.get("sandbox_rounds", 3))

        from void_engine.formation_probability import BECKER_SEED, _formation_maths
        from void_engine.formation_orchestrator import run_full_formation

        maths = _formation_maths()

        result = run_full_formation(
            seed_text=BECKER_SEED,
            swarm_agents=swarm_agents,
            swarm_rounds=swarm_rounds,
            engine_agents=engine_agents,
            engine_rounds=engine_rounds,
            sandbox_rounds=sandbox_rounds,
            maths=maths,
        )

        streams = result.get("streams", {})

        village = streams.get("void_village", {})
        engine  = streams.get("mesa_engine", {})
        sandbox = streams.get("mesa_sandbox", {})
        swarm   = streams.get("mesa_swarm", {})

        return jsonify({
            "ok": True,
            "active_streams": result.get("active_streams", 0),
            "elapsed_seconds": result.get("elapsed_seconds", 0),
            "adriana_reading": result.get("adriana_reading", ""),
            "streams": {
                "mesa_swarm": {
                    "ok": swarm.get("ok", False),
                    "agent_count": swarm.get("metadata", {}).get("agent_count", 0),
                    "summary": (swarm.get("summary") or "")[:400],
                    "themes": swarm.get("themes", [])[:5],
                },
                "void_village": {
                    "ok": village.get("ok", False),
                    "zone_id": village.get("zone_id", ""),
                    "resonance_score": village.get("resonance_score", 0),
                    "activity_level": village.get("activity_level", 0),
                },
                "mesa_engine": {
                    "ok": engine.get("ok", False),
                    "dominant_archetype": engine.get("dominant_archetype", ""),
                    "avg_influence": engine.get("avg_influence", 0),
                    "archetype_distribution": engine.get("archetype_distribution", {}),
                },
                "mesa_sandbox": {
                    "ok": sandbox.get("ok", False),
                    "scar_count": sandbox.get("scar_count", 0),
                    "scar_types": sandbox.get("scar_types", {}),
                },
            },
        })

    except Exception as e:
        logger.error("Full formation scan failed: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500
