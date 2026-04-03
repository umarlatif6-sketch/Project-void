"""
Biomedical Brief Route — PROJECT VOID
Renders the /biomedical-brief presentation page.
No authentication required — designed for offline meeting use.
"""

import logging
from flask import Blueprint, render_template

logger = logging.getLogger(__name__)

biomedical_brief_bp = Blueprint("biomedical_brief", __name__)


@biomedical_brief_bp.route("/biomedical-brief")
def biomedical_brief_page():
    from void_engine.biomedical_brief import get_brief_data
    data = get_brief_data()
    return render_template("biomedical_brief.html", **data)
