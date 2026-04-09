"""
What Is Pushing The Sand — A Frequency Manual
================================================
Route: GET /frequency-manual  — The 12-step demonstration document
"""

from flask import Blueprint, render_template

frequency_manual_bp = Blueprint("frequency_manual", __name__)


@frequency_manual_bp.route("/frequency-manual")
def frequency_manual():
    return render_template("frequency_manual.html")
