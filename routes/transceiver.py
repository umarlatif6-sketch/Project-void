from flask import Blueprint, request, jsonify

from void_engine.kinetic import EXERCISE_WEIGHTS

import routes.shared as shared

transceiver_bp = Blueprint("transceiver", __name__)


@transceiver_bp.route("/api/kinetic/log-set", methods=["POST"])
def kinetic_log_set():
    try:
        data = request.get_json(force=True)
        exercise = data.get("exercise", "push_up")
        reps = int(data.get("reps", 0))
        duration_sec = float(data.get("duration_sec", 30.0))
        heart_rate = int(data.get("heart_rate", 0))
        result = shared.kinetic.log_set(exercise, reps, duration_sec, heart_rate)
        if "error" in result:
            return jsonify(result), 400
        shared.silt_ledger.add_block(
            {"type": "kinetic_set", "exercise": exercise, "reps": reps, "cc_earned": result.get("cc_earned", 0)},
            shared.beehive.node_id,
            shared.kinetic.get_status().get("stability_score", 0),
            shared.biological.get_health_score().get("composite_score", 0)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@transceiver_bp.route("/api/kinetic/status")
def kinetic_status():
    status = shared.kinetic.get_status()
    status["exercises"] = list(EXERCISE_WEIGHTS.keys())
    return jsonify(status)


@transceiver_bp.route("/api/kinetic/history")
def kinetic_history():
    return jsonify(shared.kinetic.get_history())


@transceiver_bp.route("/api/biological/update-sensors", methods=["POST"])
def biological_update_sensors():
    try:
        data = request.get_json(force=True)
        result = shared.biological.update_sensors(
            water_level=data.get("water_level"),
            temperature=data.get("temperature"),
            ph=data.get("ph"),
            dissolved_oxygen=data.get("dissolved_oxygen")
        )
        if result.get("governance_triggered"):
            for p in result.get("governance_proposals", []):
                desc = p.get("intervention", p.get("proposal", "biological intervention"))
                shared.silt_ledger.propose_vote(str(desc), shared.beehive.node_id)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@transceiver_bp.route("/api/biological/impedance")
def biological_impedance():
    impedance = shared.biological.calculate_impedance()
    return jsonify({
        "whale_shelf": impedance.whale_multiplier,
        "bird_shelf": impedance.bird_multiplier,
        "insect_shelf": impedance.insect_multiplier,
        "overall_attenuation": impedance.overall_attenuation,
        "alerts": impedance.alerts,
    })


@transceiver_bp.route("/api/biological/health")
def biological_health():
    return jsonify(shared.biological.get_health_score())


@transceiver_bp.route("/api/biological/govern", methods=["POST"])
def biological_govern():
    try:
        data = request.get_json(force=True) if request.data else {}
        intervention = data.get("intervention", "water_refill")
        reason = data.get("reason", "Manual governance trigger")
        result = shared.biological.trigger_governance_vote(intervention, reason)
        if result.get("proposal"):
            desc = result["proposal"].get("intervention", intervention)
            prop_result = shared.silt_ledger.propose_vote(str(desc), shared.beehive.node_id)
            result["ledger_proposal"] = prop_result
        shared.silt_ledger.add_block(
            {"type": "governance_trigger", "intervention": intervention},
            shared.beehive.node_id,
            shared.kinetic.get_status().get("stability_score", 0),
            shared.biological.get_health_score().get("composite_score", 0)
        )
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@transceiver_bp.route("/api/ledger/chain")
def ledger_chain():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"blocks": shared.silt_ledger.get_chain(limit)})


@transceiver_bp.route("/api/ledger/status")
def ledger_status():
    status = shared.silt_ledger.get_status()
    integrity = status.get("integrity", {})
    kinetic_w = shared.kinetic.get_status().get("stability_score", 0)
    biological_w = shared.biological.get_health_score().get("composite_score", 0)
    honor = 1.0
    if status.get("relay_honor_scores"):
        node_honor = status["relay_honor_scores"].get(shared.beehive.node_id[:8], None)
        if node_honor is not None:
            honor = node_honor
    status["integrity_valid"] = integrity.get("valid", False)
    status["relay_honor"] = status.get("relay_honor_scores", {})
    status["voting_weight"] = {
        "kinetic": kinetic_w,
        "biological": biological_w,
        "relay": honor,
        "total": kinetic_w * 0.4 + biological_w * 0.4 + honor * 0.2,
    }
    return jsonify(status)


@transceiver_bp.route("/api/ledger/vote", methods=["POST"])
def ledger_vote():
    try:
        data = request.get_json(force=True)
        proposal_id = data.get("proposal_id", "")
        vote = data.get("vote", "yes")
        if isinstance(vote, bool):
            vote = "yes" if vote else "no"
        kinetic_w = shared.kinetic.get_status().get("stability_score", 0)
        biological_w = shared.biological.get_health_score().get("composite_score", 0)
        result = shared.silt_ledger.cast_vote(
            proposal_id, shared.beehive.node_id, vote,
            kinetic_weight=kinetic_w,
            biological_weight=biological_w
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@transceiver_bp.route("/api/ledger/votes")
def ledger_votes():
    return jsonify({"proposals": shared.silt_ledger.get_proposals()})


@transceiver_bp.route("/api/resonance/evaluate")
def resonance_evaluate():
    try:
        state = shared.resonance_contract.evaluate()
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transceiver_bp.route("/api/resonance/axioms")
def resonance_axioms():
    return jsonify(shared.resonance_contract.get_axioms())


@transceiver_bp.route("/api/resonance/status")
def resonance_status():
    try:
        return jsonify(shared.resonance_contract.get_status())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transceiver_bp.route("/api/resonance/harvest-bloom", methods=["POST"])
def resonance_harvest_bloom():
    try:
        result = shared.resonance_contract.harvest_bloom()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@transceiver_bp.route("/api/resonance/history")
def resonance_history():
    limit = request.args.get("limit", 20, type=int)
    return jsonify(shared.resonance_contract.get_history(limit))
