from flask import Blueprint, jsonify

from void_engine.codon_heart import delete_character_profile, export_character_profile


character_profile_bp = Blueprint("character_profile", __name__)


@character_profile_bp.route("/api/profile/character", methods=["GET"])
def get_character_profile():
    """Return the current visitor's character profile state."""
    profile = export_character_profile()
    return jsonify({"ok": True, "profile": profile})


@character_profile_bp.route("/api/profile/character", methods=["DELETE"])
def purge_character_profile():
    """Delete the current visitor's character profile state."""
    result = delete_character_profile()
    return jsonify({"ok": True, "result": result})
