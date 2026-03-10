import os
import time
import logging
import threading
from flask import Blueprint, request, jsonify

from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

import routes.shared as shared

logger = logging.getLogger(__name__)

node_bp = Blueprint("node", __name__)

_node_registry = {}
_registry_lock = threading.Lock()
_NODE_TIMEOUT_SEC = 300


def _generate_node_token(node_id, hardware_hash):
    raw = f"VOID-NODE-{node_id}-{hardware_hash}-{os.environ.get('SESSION_SECRET', 'void')}"
    return fatiha_286_hexdigest_from_str(raw)


def _cleanup_stale_nodes():
    now = time.time()
    with _registry_lock:
        stale = [nid for nid, info in _node_registry.items()
                 if now - info.get("last_seen", 0) > _NODE_TIMEOUT_SEC]
        for nid in stale:
            del _node_registry[nid]


def _validate_node_token(req):
    token = req.headers.get("X-Void-Node-Token", "")
    node_id = req.headers.get("X-Void-Node-Id", "")
    if not token or not node_id:
        return None, None
    with _registry_lock:
        entry = _node_registry.get(node_id)
    if entry and entry.get("token") == token:
        return node_id, entry
    return None, None


@node_bp.route("/api/node/register", methods=["POST"])
def node_register():
    _cleanup_stale_nodes()
    data = request.get_json(silent=True) or {}
    hardware_type = data.get("hardware_type", "unknown")
    gpu_name = data.get("gpu_name", "")
    mode = data.get("mode", "light")
    platform = data.get("platform", "unknown")
    python_version = data.get("python_version", "")

    if mode not in ("light", "heavy"):
        return jsonify({"error": "Mode must be 'light' or 'heavy'"}), 400

    hardware_hash = fatiha_286_hexdigest_from_str(
        f"{hardware_type}-{gpu_name}-{platform}-{time.time()}"
    )
    node_id = f"VN-{hardware_hash[:16]}"
    token = _generate_node_token(node_id, hardware_hash)

    entry = {
        "node_id": node_id,
        "token": token,
        "hardware_type": hardware_type,
        "gpu_name": gpu_name,
        "mode": mode,
        "platform": platform,
        "python_version": python_version,
        "registered_at": time.time(),
        "last_seen": time.time(),
        "status": "connected",
    }

    with _registry_lock:
        _node_registry[node_id] = entry

    try:
        shared.beehive._log_event(
            "NODE_REGISTERED",
            f"External node {node_id} registered | mode={mode} | hw={hardware_type} | gpu={gpu_name}"
        )
    except Exception:
        pass

    logger.info("Node registered: %s (mode=%s, hw=%s)", node_id, mode, hardware_type)

    return jsonify({
        "success": True,
        "node_id": node_id,
        "token": token,
        "mode": mode,
        "message": f"Welcome to the mesh, Node {node_id}. Mode: {mode.upper()}.",
    })


@node_bp.route("/api/node/heartbeat", methods=["POST"])
def node_heartbeat():
    node_id, entry = _validate_node_token(request)
    if not entry:
        return jsonify({"error": "Invalid or expired node token"}), 401

    with _registry_lock:
        _node_registry[node_id]["last_seen"] = time.time()

    return jsonify({
        "success": True,
        "node_id": node_id,
        "status": "alive",
        "mesh_state": shared.beehive.mesh_state,
    })


@node_bp.route("/api/node/status/<node_id>")
def node_status(node_id):
    _cleanup_stale_nodes()
    with _registry_lock:
        entry = _node_registry.get(node_id)

    if not entry:
        return jsonify({"error": "Node not found or expired"}), 404

    req_token = request.headers.get("X-Void-Node-Token", "")
    is_owner = req_token and entry.get("token") == req_token

    if is_owner:
        return jsonify({
            "success": True,
            "node_id": entry["node_id"],
            "mode": entry["mode"],
            "hardware_type": entry["hardware_type"],
            "gpu_name": entry["gpu_name"],
            "platform": entry["platform"],
            "status": entry["status"],
            "registered_at": entry["registered_at"],
            "last_seen": entry["last_seen"],
            "uptime_sec": round(time.time() - entry["registered_at"], 1),
        })

    return jsonify({
        "success": True,
        "node_id": entry["node_id"][:8] + "...",
        "mode": entry["mode"],
        "status": entry["status"],
    })


@node_bp.route("/api/node/count")
def node_count():
    _cleanup_stale_nodes()
    with _registry_lock:
        total = len(_node_registry)
        heavy = sum(1 for e in _node_registry.values() if e["mode"] == "heavy")
        light = total - heavy

    return jsonify({
        "success": True,
        "total_nodes": total,
        "heavy_nodes": heavy,
        "light_nodes": light,
    })


@node_bp.route("/api/node/list")
def node_list():
    _cleanup_stale_nodes()
    with _registry_lock:
        nodes = []
        for entry in _node_registry.values():
            nodes.append({
                "node_id": entry["node_id"][:8] + "...",
                "mode": entry["mode"],
                "status": entry["status"],
            })

    return jsonify({
        "success": True,
        "nodes": nodes,
        "count": len(nodes),
    })
