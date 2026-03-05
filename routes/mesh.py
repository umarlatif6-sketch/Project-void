from flask import Blueprint, request, jsonify

from void_engine.beehive import MeshPacket, simulate_two_node_exchange, _sanitize_for_json

import routes.shared as shared

mesh_bp = Blueprint("mesh", __name__)


@mesh_bp.route("/api/mesh/connect", methods=["POST"])
def mesh_connect():
    try:
        shared.wallet.debit({"type": "mesh_connect"})
        result = shared.beehive.connect()
        shared.chronicle.record_consensus(
            {
                "consensus_command": "WSL.A",
                "consensus_intent": "Mesh connect — entering Sovereign Mesh Mode",
                "outcome": f"Node {shared.beehive.node_id[:8]} connected, state={shared.beehive.mesh_state}",
                "success": True,
                "timestamp": __import__("time").time(),
                "energy_pct": 0.0,
                "wallet": {"balance": shared.wallet.balance},
            },
            {},
        )
        return jsonify({"success": True, "node_id": result["node_id"], "state": result["state"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mesh_bp.route("/api/mesh/disconnect", methods=["POST"])
def mesh_disconnect():
    try:
        shared.wallet.debit({"type": "mesh_disconnect"})
        result = shared.beehive.disconnect()
        shared.chronicle.record_consensus(
            {
                "consensus_command": "WSL.D",
                "consensus_intent": "Mesh disconnect — leaving Sovereign Mesh",
                "outcome": f"Left mesh from {result['previous_state']} state",
                "success": True,
                "timestamp": __import__("time").time(),
                "energy_pct": 0.0,
                "wallet": {"balance": shared.wallet.balance},
            },
            {},
        )
        return jsonify({"success": True, "previous_state": result["previous_state"], "neighbors_released": result["neighbors_released"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mesh_bp.route("/api/mesh/status")
def mesh_status():
    try:
        status = shared.beehive.get_status()
        return jsonify({"success": True, **status})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mesh_bp.route("/api/mesh/send", methods=["POST"])
def mesh_send():
    data = request.json or {}
    message = data.get("message", "")
    dest_id = data.get("dest_id", "")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        debit_result = shared.wallet.debit({"type": "mesh_send"})
        payload = message.encode("utf-8")

        if dest_id:
            packet = shared.mesh_router.create_packet(dest_id, payload)
        else:
            packet = MeshPacket.create_broadcast(shared.beehive.node_id, payload)
            shared.beehive.stats["packets_sent"] += 1
            shared.beehive._log_event("BROADCAST_SENT", f"Broadcast {len(payload)} bytes")

        return jsonify({
            "success": True,
            "packet": packet.to_dict(),
            "wallet": debit_result,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mesh_bp.route("/api/mesh/neighbors")
def mesh_neighbors():
    try:
        status = shared.beehive.get_status()
        return jsonify({"success": True, "neighbors": status["neighbors"], "count": status["neighbor_count"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mesh_bp.route("/api/mesh/handshake", methods=["POST"])
def mesh_handshake():
    try:
        debit_result = shared.wallet.debit({"type": "mesh_handshake"})
        pulse = shared.beehive.generate_handshake_pulse(duration=0.5)
        detection = shared.beehive.detect_neighbor(pulse)
        auth = shared.beehive.authenticate_phase(pulse)

        return jsonify(_sanitize_for_json({
            "success": True,
            "detection": detection,
            "authentication": auth,
            "pulse_samples": len(pulse),
            "wallet": debit_result,
        }))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mesh_bp.route("/api/mesh/activity")
def mesh_activity():
    limit = request.args.get("limit", 50, type=int)
    try:
        log = shared.beehive.get_activity_log(limit)
        return jsonify({"success": True, "activity": log, "count": len(log)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@mesh_bp.route("/api/mesh/simulate", methods=["POST"])
def mesh_simulate():
    try:
        result = simulate_two_node_exchange()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
