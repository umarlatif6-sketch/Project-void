from __future__ import annotations

from flask import Blueprint, jsonify, request

from routes.auth import admin_required, tier_required
from void_engine.fork_integration import (
    DEFAULT_FORK_REPO_URL,
    load_delta_pack,
    load_fork_index,
    sync_index_and_build_delta,
)

fork_integration_bp = Blueprint("fork_integration", __name__)


@fork_integration_bp.route("/api/integrations/ai-agents/index", methods=["GET"])
@tier_required("journalist")
def ai_agents_index():
    refresh = str(request.args.get("refresh", "false")).strip().lower() in {"1", "true", "yes", "on"}
    if refresh:
        return jsonify({"ok": False, "error": "refresh_requires_admin_sync"}), 403

    data = load_fork_index()
    if not data.get("ok"):
        return jsonify(data), 404
    return jsonify({"ok": True, **data})


@fork_integration_bp.route("/api/integrations/ai-agents/delta-pack", methods=["GET"])
@tier_required("journalist")
def ai_agents_delta_pack():
    refresh = str(request.args.get("refresh", "false")).strip().lower() in {"1", "true", "yes", "on"}
    if refresh:
        return jsonify({"ok": False, "error": "refresh_requires_admin_sync"}), 403

    data = load_delta_pack()
    if not data.get("ok"):
        return jsonify(data), 404
    return jsonify({"ok": True, **data})


@fork_integration_bp.route("/api/integrations/ai-agents/sync", methods=["POST"])
@admin_required
def ai_agents_sync():
    data = request.get_json(silent=True) or {}
    repo_url = str(data.get("repo_url") or DEFAULT_FORK_REPO_URL).strip() or DEFAULT_FORK_REPO_URL

    try:
        max_files = int(data.get("max_files", 8000) or 8000)
    except Exception:  # noqa: BLE001
        return jsonify({"ok": False, "error": "invalid_max_files"}), 400

    try:
        max_delta_entries = int(data.get("max_delta_entries", 96) or 96)
    except Exception:  # noqa: BLE001
        return jsonify({"ok": False, "error": "invalid_max_delta_entries"}), 400

    if max_files < 100 or max_files > 50000:
        return jsonify({"ok": False, "error": "max_files_out_of_bounds"}), 400
    if max_delta_entries < 10 or max_delta_entries > 2000:
        return jsonify({"ok": False, "error": "max_delta_entries_out_of_bounds"}), 400

    result = sync_index_and_build_delta(
        repo_url=repo_url,
        max_files=max_files,
        max_delta_entries=max_delta_entries,
    )
    status = 200 if result.get("ok") else 500
    return jsonify(result), status
