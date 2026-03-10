import os
from flask import Flask, render_template

app = Flask(__name__)
_secret = os.environ.get("SESSION_SECRET")
if not _secret:
    raise RuntimeError("SESSION_SECRET environment variable is required")
app.secret_key = _secret
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

from routes.auth import _ensure_columns

_ensure_columns()
from routes import register_blueprints

register_blueprints(app)


@app.route("/health")
def health_check():
    return "ok", 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
