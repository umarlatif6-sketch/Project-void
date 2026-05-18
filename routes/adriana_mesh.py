"""Routes for Adriana local mesh runtime and evaluation."""

from __future__ import annotations

from pathlib import Path
from flask import Blueprint, jsonify, request

from scripts.adriana_local_mesh import run_mesh, load_profile_bundle
from scripts.adriana_mesh_eval import run_eval

adriana_mesh_bp = Blueprint("adriana_mesh", __name__)

ROOT = Path(__file__).resolve().parents[1]
PROFILES_PATH = ROOT / "data" / "adriana_mesh_profiles.json"
PROMPTS_PATH = ROOT / "data" / "adriana_eval_prompts.json"
OUT_DIR = ROOT / "data" / "adriana_mesh_runs"


@adriana_mesh_bp.route("/api/adriana/mesh/profiles", methods=["GET"])
def list_profiles():
    bundle = load_profile_bundle(PROFILES_PATH, "cpu_light")
    profiles = bundle["profiles"]
    return jsonify(
        {
            "ok": True,
            "profiles": list(profiles.keys()),
            "default": "cpu_light",
        }
    )


@adriana_mesh_bp.route("/api/adriana/mesh/run", methods=["POST"])
def run_mesh_api():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "missing_prompt"}), 400

    profile = str(data.get("profile") or "cpu_light")
    sandbox = str(data.get("sandbox") or "api")[:64]
    mock = bool(data.get("mock", False))
    timeout = int(data.get("timeout", 60) or 60)
    ollama_url = str(data.get("ollama_url") or "http://127.0.0.1:11434")

    peer_inputs = []
    raw_peers = data.get("peer_inputs")
    if isinstance(raw_peers, list):
        for item in raw_peers:
            p = str(item or "").strip()
            if p:
                peer_inputs.append(Path(p))

    try:
        artifact = run_mesh(
            prompt=prompt,
            profile_name=profile,
            profiles_path=PROFILES_PATH,
            out_dir=OUT_DIR,
            ollama_url=ollama_url,
            timeout_s=timeout,
            sandbox=sandbox,
            peer_inputs=peer_inputs,
            force_mock=mock,
            write_artifact=True,
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify({"ok": True, "artifact": artifact})


@adriana_mesh_bp.route("/api/adriana/mesh/eval", methods=["POST"])
def run_mesh_eval_api():
    data = request.get_json(silent=True) or {}
    profile = str(data.get("profile") or "cpu_light")
    mock = bool(data.get("mock", False))
    timeout = int(data.get("timeout", 60) or 60)
    ollama_url = str(data.get("ollama_url") or "http://127.0.0.1:11434")

    try:
        report = run_eval(
            prompts_path=PROMPTS_PATH,
            profile_name=profile,
            profiles_path=PROFILES_PATH,
            out_dir=OUT_DIR,
            ollama_url=ollama_url,
            timeout_s=timeout,
            force_mock=mock,
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify({"ok": True, "report": report})
