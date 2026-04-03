"""
Patent-Loom Route — PROJECT VOID
Routes for the Patent-Loom interface and season/countdown APIs.
"""

import logging
from flask import Blueprint, render_template, request, jsonify
from routes.auth import admin_required

logger = logging.getLogger(__name__)

patent_loom_bp = Blueprint("patent_loom", __name__)


@patent_loom_bp.route("/patent-loom")
def patent_loom_page():
    from void_engine.patent_loom import get_pre_generated_claims, get_digital_twin_report
    from void_engine.lunar_season import get_season_status, get_mrb4000_countdown
    try:
        claims = get_pre_generated_claims()
    except Exception as e:
        logger.error("Failed to load pre-generated claims: %s", e)
        claims = []
    try:
        digital_twin = get_digital_twin_report()
    except Exception as e:
        logger.error("Failed to load digital twin report: %s", e)
        digital_twin = {}
    try:
        season = get_season_status()
    except Exception as e:
        logger.error("Failed to load season status: %s", e)
        season = {}
    try:
        countdown = get_mrb4000_countdown()
    except Exception as e:
        logger.error("Failed to load countdown: %s", e)
        countdown = {}
    return render_template(
        "patent_loom.html",
        claims=claims,
        digital_twin=digital_twin,
        season=season,
        countdown=countdown,
    )


@patent_loom_bp.route("/api/patent-loom/process", methods=["POST"])
def api_loom_process():
    """Process a block of forge text into three-layer patent language."""
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        from void_engine.patent_loom import process_forge_text
        result = process_forge_text(text)
        return jsonify(result)
    except Exception as e:
        logger.error("Patent Loom processing error: %s", e)
        return jsonify({"error": str(e)}), 500


@patent_loom_bp.route("/api/patent-loom/claims")
def api_loom_claims():
    """Return the three pre-generated priority claims."""
    try:
        from void_engine.patent_loom import get_pre_generated_claims
        return jsonify({"claims": get_pre_generated_claims()})
    except Exception as e:
        logger.error("Patent claims API error: %s", e)
        return jsonify({"error": str(e)}), 500


@patent_loom_bp.route("/api/patent-loom/digital-twin")
def api_digital_twin():
    """Return the Digital Twin stress-test report."""
    try:
        from void_engine.patent_loom import get_digital_twin_report
        return jsonify(get_digital_twin_report())
    except Exception as e:
        logger.error("Digital Twin API error: %s", e)
        return jsonify({"error": str(e)}), 500


@patent_loom_bp.route("/api/season/status")
def api_season_status():
    """Return the current Lunar Season status."""
    try:
        from void_engine.lunar_season import get_season_status
        return jsonify(get_season_status())
    except Exception as e:
        logger.error("Season status API error: %s", e)
        return jsonify({"error": str(e)}), 500


@patent_loom_bp.route("/api/season/set", methods=["POST"])
@admin_required
def api_season_set():
    """Set the active Lunar Season (admin only)."""
    data = request.get_json() or {}
    season = (data.get("season") or "").strip().upper()
    try:
        from void_engine.lunar_season import set_season
        result = set_season(season)
        return jsonify(result)
    except Exception as e:
        logger.error("Season set API error: %s", e)
        return jsonify({"error": str(e)}), 500


@patent_loom_bp.route("/api/mrb4000/countdown")
def api_mrb4000_countdown():
    """Return the MRB-4000 countdown state."""
    try:
        from void_engine.lunar_season import get_mrb4000_countdown
        return jsonify(get_mrb4000_countdown())
    except Exception as e:
        logger.error("MRB-4000 countdown API error: %s", e)
        return jsonify({"error": str(e)}), 500


@patent_loom_bp.route("/api/mrb4000/set-target", methods=["POST"])
@admin_required
def api_mrb4000_set_target():
    """Update the MRB-4000 target date (admin only). Body: {target_date: 'YYYY-MM-DD'}"""
    data = request.get_json() or {}
    target_date = (data.get("target_date") or "").strip()
    try:
        from datetime import date as _date
        _date.fromisoformat(target_date)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    try:
        from void_engine.lunar_season import set_config_value, get_mrb4000_countdown
        set_config_value("mrb4000_target_date", target_date)
        return jsonify({"success": True, "countdown": get_mrb4000_countdown()})
    except Exception as e:
        logger.error("MRB-4000 target update error: %s", e)
        return jsonify({"error": str(e)}), 500
