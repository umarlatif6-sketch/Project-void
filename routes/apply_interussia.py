from flask import Blueprint, render_template
from void_engine.apply_interussia import get_application_data

apply_interussia_bp = Blueprint("apply_interussia", __name__)


@apply_interussia_bp.route("/apply/interussia")
def apply_interussia():
    data = get_application_data()
    return render_template("apply_interussia.html", data=data)


@apply_interussia_bp.route("/apply/interussia/cover")
def apply_interussia_cover():
    data = get_application_data()
    return render_template("apply_interussia_cover.html", data=data)


@apply_interussia_bp.route("/apply/interussia/checklist")
def apply_interussia_checklist():
    data = get_application_data()
    return render_template("apply_interussia_checklist.html", data=data)
