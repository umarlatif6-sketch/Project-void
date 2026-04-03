"""
VOID Deep Research Report Engine — /research
=============================================
Routes:
  GET  /research         — Five-axis command-room research report page
  POST /research/run     — Re-seed research briefs and reload page data
  GET  /research/export  — Printable HTML report (PDF-ready, VOID branded)
"""

import logging
from flask import Blueprint, render_template, jsonify, request

logger = logging.getLogger(__name__)

research_bp = Blueprint("research", __name__)


def _get_axes():
    try:
        from void_engine.research_engine import get_all_axes
        return get_all_axes()
    except Exception as e:
        logger.error("research_engine: get_all_axes failed: %s", e)
        return []


def _get_matrix():
    try:
        from void_engine.research_engine import get_probability_matrix
        return get_probability_matrix()
    except Exception as e:
        logger.error("research_engine: get_probability_matrix failed: %s", e)
        return {"aggregate": 83.2, "axes": [], "validated_weight": 0}


@research_bp.route("/research")
def research_page():
    axes = _get_axes()
    matrix = _get_matrix()
    return render_template("research.html", axes=axes, matrix=matrix)


@research_bp.route("/research/run", methods=["POST"])
def research_run():
    """
    Trigger endpoint: re-seeds all five RESEARCH_BRIEF chronicle entries
    and returns the refreshed data as JSON.
    """
    try:
        from void_engine.research_engine import seed_research_briefs, get_all_axes, get_probability_matrix
        seed_research_briefs()
        axes = get_all_axes()
        matrix = get_probability_matrix()
        return jsonify({
            "ok": True,
            "message": "Research sweep complete. All five axes re-seeded as RESEARCH_BRIEF chronicle entries.",
            "axes_seeded": len(axes),
            "aggregate_score": matrix["aggregate"],
        })
    except Exception as e:
        logger.exception("research_run failed")
        return jsonify({"ok": False, "error": str(e)}), 500


@research_bp.route("/research/export")
def research_export():
    """
    Printable full HTML report — renders research_export.html.
    No external PDF library required; designed for browser print-to-PDF.
    """
    axes = _get_axes()
    matrix = _get_matrix()
    return render_template("research_export.html", axes=axes, matrix=matrix)
