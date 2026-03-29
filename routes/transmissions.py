from flask import Blueprint, render_template, request, jsonify
import json
import os
import tempfile

transmissions_bp = Blueprint("transmissions", __name__)

RESONANCE_FILE = "data/transmissions_resonance.json"

VALID_TRANSMISSIONS = frozenset({
    "t01", "t02", "t03", "t04", "t05", "t06",
    "t07", "t08", "t09", "t10", "t11", "t12",
})


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
    tmp_fd, tmp_path = tempfile.mkstemp(dir="data", prefix=".trans_res_", suffix=".json")
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


@transmissions_bp.route("/transmissions")
def transmissions():
    return render_template("transmissions.html")


@transmissions_bp.route("/transmissions/resonate", methods=["POST"])
def resonate():
    body = request.get_json(silent=True) or {}
    transmission = body.get("transmission", "").strip().lower()
    if transmission not in VALID_TRANSMISSIONS:
        return jsonify({"error": "invalid transmission"}), 400

    data = _load_resonance()
    data[transmission] = data.get(transmission, 0) + 1
    _save_resonance(data)

    return jsonify({"transmission": transmission, "count": data[transmission]})


@transmissions_bp.route("/transmissions/resonance")
def resonance_counts():
    data = _load_resonance()
    return jsonify({k: v for k, v in data.items() if k in VALID_TRANSMISSIONS})
