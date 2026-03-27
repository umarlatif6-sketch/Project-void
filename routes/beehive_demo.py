from flask import Blueprint, render_template, jsonify, session, request

from void_engine.beehive import (
    BeehiveProtocol, simulate_two_node_exchange, _sanitize_for_json, SAMPLE_RATE,
    RESONANCE_FREQ, FATIHA_PHASE_ANGLE, SNR_THRESHOLD
)
from void_engine.beehive_audio import AUDIO_BACKEND

import routes.shared as shared

beehive_demo_bp = Blueprint("beehive_demo", __name__)


@beehive_demo_bp.route("/beehive/demo")
def beehive_demo_page():
    status = shared.beehive.get_status()
    return render_template(
        "beehive_demo.html",
        node_id=shared.beehive.node_id,
        mesh_state=shared.beehive.mesh_state,
        status=status,
        audio_backend=AUDIO_BACKEND,
        resonance_freq=RESONANCE_FREQ,
        fatiha_phase_angle=FATIHA_PHASE_ANGLE,
        snr_threshold=SNR_THRESHOLD,
        sample_rate=SAMPLE_RATE,
        username=session.get("username", ""),
        user_tier=session.get("tier", "ghost"),
    )


@beehive_demo_bp.route("/api/beehive/demo/simulate", methods=["POST"])
def demo_simulate():
    data = request.json or {}
    passphrase = data.get("passphrase", "void-432")
    if len(passphrase) > 128:
        return jsonify({"error": "Passphrase too long"}), 400

    try:
        result = simulate_two_node_exchange(passphrase=passphrase)
        return jsonify(_sanitize_for_json({"success": True, "result": result}))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@beehive_demo_bp.route("/api/beehive/demo/status")
def demo_status():
    try:
        status = shared.beehive.get_status()
        return jsonify(_sanitize_for_json({
            "success": True,
            "node_id": shared.beehive.node_id,
            "mesh_state": shared.beehive.mesh_state,
            "audio_backend": AUDIO_BACKEND,
            "audio_available": AUDIO_BACKEND != "simulation",
            "resonance_freq": RESONANCE_FREQ,
            "fatiha_phase_angle": FATIHA_PHASE_ANGLE,
            "snr_threshold": SNR_THRESHOLD,
            "stats": status.get("stats", {}),
            "neighbor_count": status.get("neighbor_count", 0),
            "mode": status.get("mode", "SIMULATION"),
        }))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@beehive_demo_bp.route("/api/beehive/demo/activity")
def demo_activity():
    limit = request.args.get("limit", 20, type=int)
    try:
        log = shared.beehive.get_activity_log(limit)
        return jsonify({"success": True, "activity": log, "count": len(log)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@beehive_demo_bp.route("/api/beehive/demo/handshake", methods=["POST"])
def demo_handshake():
    try:
        pulse = shared.beehive.generate_handshake_pulse(duration=0.5)
        detection = shared.beehive.detect_neighbor(pulse)
        fatiha = shared.beehive.verify_fatiha_signature(pulse)
        auth = shared.beehive.authenticate_phase(pulse)

        return jsonify(_sanitize_for_json({
            "success": True,
            "node_id": shared.beehive.node_id,
            "mesh_state": shared.beehive.mesh_state,
            "pulse_samples": len(pulse),
            "detection": detection,
            "fatiha": fatiha,
            "authentication": auth,
        }))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
