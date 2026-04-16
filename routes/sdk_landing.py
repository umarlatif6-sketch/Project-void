"""SDK landing pages — short homepage and enterprise sales page."""

from flask import Blueprint, render_template

sdk_landing_bp = Blueprint("sdk_landing", __name__)


@sdk_landing_bp.route("/sdk")
def sdk_home():
    """Short homepage — high-conversion, single scroll."""
    return render_template("sdk_home.html")


@sdk_landing_bp.route("/sdk/enterprise")
def sdk_enterprise():
    """Enterprise sales page — CTO/CFO review, full detail."""
    return render_template("sdk_enterprise.html")
