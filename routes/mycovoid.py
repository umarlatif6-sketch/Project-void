from flask import Blueprint, render_template, session

mycovoid_bp = Blueprint("mycovoid", __name__)


@mycovoid_bp.route("/mycovoid")
def mycovoid_page():
    return render_template(
        "mycovoid.html",
        username=session.get("username", ""),
        user_tier=session.get("tier", "ghost"),
    )
