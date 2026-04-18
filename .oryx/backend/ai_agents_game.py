"""Compatibility layer exposing a simple ORYX agent world."""

from pathlib import Path

from flask import Flask, jsonify, request

from oryx_engine import OryxEngine

app = Flask(__name__)
engine = OryxEngine(Path(__file__).resolve().parent / "data")
DEFAULT_WORLD_ID = ""


def ensure_default_world() -> str:
    global DEFAULT_WORLD_ID
    if DEFAULT_WORLD_ID:
        return DEFAULT_WORLD_ID

    world = engine.create_world(
        name="ORYX Agent Arena",
        template_key="sunsteel_frontier",
        company_name="ORYX Studios",
        integration_mode="optional",
    )
    DEFAULT_WORLD_ID = world["world"]["id"]
    return DEFAULT_WORLD_ID


@app.route("/ai-game/state")
def game_state():
    return jsonify(engine.load_world(ensure_default_world()))


@app.route("/ai-game/step", methods=["POST"])
def game_step():
    payload = request.get_json(silent=True) or {}
    return jsonify(engine.step_world(ensure_default_world(), steps=int(payload.get("steps", 1))))


@app.route("/ai-game/reset", methods=["POST"])
def game_reset():
    global DEFAULT_WORLD_ID
    DEFAULT_WORLD_ID = ""
    return jsonify(engine.load_world(ensure_default_world()))


if __name__ == "__main__":
    app.run(debug=True)
