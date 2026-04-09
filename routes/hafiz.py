from flask import Blueprint, render_template

hafiz_bp = Blueprint('hafiz', __name__)

@hafiz_bp.route('/to-the-hafiz')
def hafiz():
    return render_template('hafiz.html')
