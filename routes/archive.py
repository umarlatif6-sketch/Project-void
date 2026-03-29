from flask import Blueprint, render_template, request, jsonify
import json
import os
import tempfile

archive_bp = Blueprint("archive", __name__)

RESONANCE_FILE = "data/archive_resonance.json"

VALID_SECTIONS = frozenset({"mind", "journey", "faith", "family", "work", "why"})


def _load_resonance():
    if not os.path.exists(RESONANCE_FILE):
        return {}
    try:
        with open(RESONANCE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_resonance(data):
    os.makedirs("data", exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir="data", prefix=".arch_res_", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp_path, RESONANCE_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


@archive_bp.route("/archive")
def archive():
    return render_template("archive.html")


@archive_bp.route("/archive/resonate", methods=["POST"])
def resonate():
    body = request.get_json(silent=True) or {}
    section = body.get("section", "").strip().lower()
    if section not in VALID_SECTIONS:
        return jsonify({"error": "invalid section"}), 400

    data = _load_resonance()
    data[section] = data.get(section, 0) + 1
    _save_resonance(data)

    return jsonify({"section": section, "count": data[section]})


@archive_bp.route("/archive/resonance")
def resonance_counts():
    data = _load_resonance()
    return jsonify({k: v for k, v in data.items() if k in VALID_SECTIONS})
