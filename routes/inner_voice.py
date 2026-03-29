"""
Inner Voice — Silent Speech Module
=====================================
Defensive prior-art publication documenting the VOID approach to silent
speech detection using surface EMG (sEMG) neuromuscular signals processed
entirely on the MRB-4000, with no cloud dependency.

Route: GET /inner-voice
"""

import logging
from flask import Blueprint, render_template, session

logger = logging.getLogger(__name__)
inner_voice_bp = Blueprint("inner_voice", __name__)

PUBLICATION_DATE = "29 March 2026"
PUBLICATION_DATE_ISO = "2026-03-29"
INVENTOR = "Umar"


@inner_voice_bp.route("/inner-voice")
def inner_voice_page():
    return render_template(
        "inner_voice.html",
        publication_date=PUBLICATION_DATE,
        publication_date_iso=PUBLICATION_DATE_ISO,
        inventor=INVENTOR,
        username=session.get("username", ""),
    )
