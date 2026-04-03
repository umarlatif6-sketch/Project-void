"""
The Four Quls — Protection Set
Route: GET /quls

Renders the canonical SCL poems for the four protective Surahs (109, 112, 113, 114).
Data is sourced from CANONICAL_SURAH_POEMS in adriana_scl — pre-ordained, not hash-derived.
"""

from flask import Blueprint, render_template
from void_engine.adriana_scl import get_four_quls

quls_bp = Blueprint("quls", __name__)


@quls_bp.route("/quls")
def quls():
    four_quls = get_four_quls()
    return render_template("quls.html", quls=four_quls)
