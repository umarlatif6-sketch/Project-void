"""
Void Resonance Flower — API Routes
====================================
Endpoints for querying the living flower state, agent positions,
resonance field values, and triggering simulation steps.
"""

import logging
from flask import Blueprint, jsonify, render_template, request, session
from routes.auth import login_required

logger = logging.getLogger(__name__)

void_flower_bp = Blueprint("void_flower", __name__)


@void_flower_bp.route("/void-flower")
def void_flower_page():
    """Visual frontend: the living 12-petal resonance flower with agent swarm."""
    user_id = session.get("user_id")
    username = session.get("username", "")
    display_name = session.get("display_name", "")
    return render_template(
        "void_flower.html",
        user_id=user_id,
        username=username,
        display_name=display_name,
    )


@void_flower_bp.route("/api/void-flower/state")
def api_void_flower_state():
    """
    Return the current void flower state.

    Query params:
        refresh=1  — force a full recalculation (default: use cache)

    Returns:
        {
          petals: [...],
          void_amplitude: float,
          void_clarity: float,
          bloom_intensity: float,
          petal_health: [...],
          ai_anchors: [...],
          agent_placements: [...],
          void_zone_agent_count: int,
          petal_zone_agent_count: int,
          total_agents_placed: int,
          harmonic_ladder: [...],
          sim_step: int,
          computed_at: str,
        }
    """
    try:
        from void_engine.resonance_flower import get_live_flower_state
        force = request.args.get("refresh", "0") == "1"
        state = get_live_flower_state(force_refresh=force)
        return jsonify({"ok": True, "state": state})
    except Exception as e:
        logger.error("void_flower state error: %s", e)
        return jsonify({"error": "Failed to compute flower state"}), 500


@void_flower_bp.route("/api/void-flower/step", methods=["POST"])
@login_required
def api_void_flower_step():
    """
    Advance the flower simulation one step and store a Chronicle snapshot.

    Returns the new state after stepping.
    """
    try:
        from void_engine.resonance_flower import advance_flower_step
        state = advance_flower_step()
        return jsonify({"ok": True, "state": state})
    except Exception as e:
        logger.error("void_flower step error: %s", e)
        return jsonify({"error": "Simulation step failed"}), 500


@void_flower_bp.route("/api/void-flower/field")
def api_void_flower_field():
    """
    Return the resonance field grid.

    Query params:
        size=30    — grid resolution (default 30, max 80)
        petals=1.0,0.9,...  — comma-separated petal health values (12 values)

    Returns:
        {
          field: [[float, ...], ...],
          void_amplitude: float,
          void_zone_points: int,
          grid_size: int,
          grid_step: float,
        }
    """
    try:
        from void_engine.resonance_flower import compute_resonance_field
        grid_size = min(80, max(10, int(request.args.get("size", 30))))

        raw_petals = request.args.get("petals", "")
        petal_health = None
        if raw_petals:
            try:
                petal_health = [
                    float(v) for v in raw_petals.split(",")[:12]
                ]
            except ValueError:
                petal_health = None

        result = compute_resonance_field(grid_size=grid_size, petal_health=petal_health)
        return jsonify({"ok": True, "field_data": result})
    except Exception as e:
        logger.error("void_flower field error: %s", e)
        return jsonify({"error": "Field computation failed"}), 500


@void_flower_bp.route("/api/void-flower/agents")
def api_void_flower_agents():
    """
    Return current agent positions within the flower.

    Query params:
        n=200   — max agents to return (default 200)

    Returns:
        {
          agents: [
            {agent_id, glyph, x, y, r, theta_deg, resonance_amplitude,
             preferred_petal, zone, activity}, ...
          ],
          void_zone_count: int,
          petal_zone_count: int,
          field_zone_count: int,
        }
    """
    try:
        from void_engine.resonance_flower import (
            get_live_flower_state, place_agents_in_flower,
            _derive_petal_health_from_agents
        )
        from void_engine.mesa_engine import _fetch_seed_data
        import random

        n = min(1000, max(10, int(request.args.get("n", 1000))))

        seed_data = _fetch_seed_data(agent_count=n)
        agents = []
        rng = random.Random(42)
        for i, sd in enumerate(seed_data):
            peace = float(sd.get("peace_balance", 0))
            activity = min(1.0, max(0.05, 0.3 + peace / 500.0 * 0.4 + rng.gauss(0, 0.1)))
            agents.append({
                "agent_id": i,
                "glyph": sd.get("glyph", "◆"),
                "activity": activity,
            })

        petal_health = _derive_petal_health_from_agents(agents)
        placements = place_agents_in_flower(agents, n_display=n)

        void_c = sum(1 for p in placements if p["zone"] == "void")
        petal_c = sum(1 for p in placements if p["zone"] == "petal")
        field_c = sum(1 for p in placements if p["zone"] == "field")

        return jsonify({
            "ok": True,
            "agents": placements,
            "void_zone_count": void_c,
            "petal_zone_count": petal_c,
            "field_zone_count": field_c,
            "petal_health": petal_health,
        })
    except Exception as e:
        logger.error("void_flower agents error: %s", e)
        return jsonify({"error": "Agent placement failed"}), 500


@void_flower_bp.route("/api/void-flower/resonance-at")
def api_void_flower_resonance_at():
    """
    Query the resonance amplitude at a specific (x, y) coordinate.

    Query params:
        x=0.0   — x coordinate in [-1, 1]
        y=0.0   — y coordinate in [-1, 1]

    Returns:
        {
          x, y, r, theta_deg, amplitude,
          zone: "void" | "petal" | "field" | "outside",
          dominant_petal: int,
          dominant_frequency_hz: int,
        }
    """
    try:
        import math
        from void_engine.resonance_flower import (
            _petal_signed_wave, _petal_amplitude, VOID_RADIUS, PETAL_FREQUENCIES
        )

        x = float(request.args.get("x", 0.0))
        y = float(request.args.get("y", 0.0))
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))

        r = math.sqrt(x * x + y * y)
        theta = math.atan2(y, x) if r > 1e-9 else 0.0

        petal_signed = [_petal_signed_wave(x, y, i) for i in range(12)]
        petal_amps = [max(0.0, s) for s in petal_signed]
        signed_sum = sum(petal_signed)
        amplitude = round(min(1.0, abs(signed_sum) / 12.0), 4)

        dom_idx = max(range(12), key=lambda i: petal_amps[i])

        if r <= VOID_RADIUS:
            zone = "void"
        elif amplitude > 0.04:
            zone = "petal"
        else:
            zone = "field"

        return jsonify({
            "ok": True,
            "x": round(x, 4),
            "y": round(y, 4),
            "r": round(r, 4),
            "theta_deg": round(math.degrees(theta) % 360, 2),
            "amplitude": amplitude,
            "signed_sum": round(signed_sum, 4),
            "zone": zone,
            "dominant_petal": dom_idx,
            "dominant_frequency_hz": PETAL_FREQUENCIES[dom_idx],
            "petal_amplitudes": [round(a, 4) for a in petal_amps],
        })
    except Exception as e:
        logger.error("void_flower resonance-at error: %s", e)
        return jsonify({"error": "Resonance query failed"}), 500


@void_flower_bp.route("/api/void-flower/history")
def api_void_flower_history():
    """
    Return recent Chronicle snapshots of the void flower evolution.

    Query params:
        limit=20  — max snapshots to return

    Returns:
        { snapshots: [...] }
    """
    try:
        from void_engine.resonance_flower import get_void_snapshot_history
        limit = min(100, max(1, int(request.args.get("limit", 20))))
        history = get_void_snapshot_history(limit=limit)
        return jsonify({"ok": True, "snapshots": history})
    except Exception as e:
        logger.error("void_flower history error: %s", e)
        return jsonify({"error": "History fetch failed"}), 500
