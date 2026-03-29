from flask import Blueprint, render_template

peace_bp = Blueprint("peace", __name__)


@peace_bp.route("/peace/flywheel")
def flywheel():
    return render_template("peace_flywheel.html")
