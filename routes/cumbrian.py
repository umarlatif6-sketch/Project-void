from flask import Blueprint, render_template, session

cumbrian_bp = Blueprint("cumbrian", __name__)


@cumbrian_bp.route("/cumbrian")
def cumbrian_page():
    return render_template(
        "cumbrian.html",
        username=session.get("username", ""),
        user_tier=session.get("tier", "ghost"),
    )
