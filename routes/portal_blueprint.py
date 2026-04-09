"""
Resonance Node Portal — Blueprint
===================================
Route: GET /portal-blueprint  — Technical blueprint document
"""

from flask import Blueprint, render_template

portal_blueprint_bp = Blueprint("portal_blueprint", __name__)


@portal_blueprint_bp.route("/portal-blueprint")
def portal_blueprint():
    return render_template("portal_blueprint.html")
