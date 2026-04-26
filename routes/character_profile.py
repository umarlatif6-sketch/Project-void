from flask import Blueprint, jsonify

from void_engine.codon_heart import delete_character_profile, export_character_profile


character_profile_bp = Blueprint("character_profile", __name__)


@character_profile_bp.route("/api/profile/character", methods=["GET"])
def get_character_profile():
    """Return the current visitor's character profile state."""
    profile = export_character_profile()
    return jsonify({"ok": True, "profile": profile})


@character_profile_bp.route("/api/profile/character/transparency", methods=["GET"])
def get_character_profile_transparency():
    """
    Return a transparency summary explaining what data is held in the character
    profile, where it came from, and how it is used.  No raw personal data is
    returned here — this endpoint is safe for unauthenticated read.
    """
    profile = export_character_profile()
    codon_count = profile.get("codon_count", 0) if isinstance(profile, dict) else 0
    buffer_count = profile.get("buffer_message_count", 0) if isinstance(profile, dict) else 0
    return jsonify({
        "ok": True,
        "transparency": {
            "data_held": {
                "codons": {
                    "count": codon_count,
                    "description": "LBN seed codons generated from visitor interactions",
                    "source": "server-side codon heart (void_engine.codon_heart)",
                    "retention": "retained until visitor requests deletion via DELETE /api/profile/character",
                },
                "buffer_messages": {
                    "count": buffer_count,
                    "description": "recent conversation context window for AI continuity",
                    "source": "visitor session messages",
                    "retention": "retained per session; cleared on profile deletion",
                },
            },
            "used_for": [
                "personalised LBN codon routing",
                "AI session continuity across page loads",
                "ORYX governance audit trail (aggregated, no PII)",
            ],
            "not_used_for": [
                "advertising",
                "third-party data sharing",
                "persistent tracking across devices",
            ],
            "deletion": "Send DELETE /api/profile/character to remove all held data immediately",
        },
    })


@character_profile_bp.route("/api/profile/character", methods=["DELETE"])
def purge_character_profile():
    """Delete the current visitor's character profile state."""
    result = delete_character_profile()
    return jsonify({"ok": True, "result": result})
