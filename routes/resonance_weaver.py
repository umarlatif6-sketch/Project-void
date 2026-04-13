from __future__ import annotations

from flask import Blueprint, jsonify, request

from void_engine.resonance_weaver import read_resonance, weave_entries


resonance_weaver_bp = Blueprint("resonance_weaver", __name__)


@resonance_weaver_bp.route("/api/resonance/weave/read", methods=["POST"])
def api_resonance_weave_read():
    data = request.get_json(silent=True) or {}
    threshold = float(data.get("threshold", 0.30))
    entry = {
        "title": data.get("title", "untitled"),
        "text": data.get("text", ""),
        "source": data.get("source", "api"),
    }
    payload = read_resonance(entry, threshold=threshold)
    return jsonify(payload)


@resonance_weaver_bp.route("/api/resonance/weave/cluster", methods=["POST"])
def api_resonance_weave_cluster():
    data = request.get_json(silent=True) or {}
    threshold = float(data.get("threshold", 0.30))
    entries = data.get("entries") or []
    if not isinstance(entries, list) or not entries:
        return jsonify({"error": "entries must be a non-empty list"}), 400
    payload = weave_entries(entries, threshold=threshold)
    return jsonify(payload)
