import os
import logging
import threading
from flask import Flask, render_template

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_secret = os.environ.get("SESSION_SECRET")
if not _secret:
    logger.error("FATAL: SESSION_SECRET environment variable is not set")
    raise RuntimeError("SESSION_SECRET environment variable is required")

app.secret_key = _secret
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

try:
    from routes.auth import _ensure_columns
    from routes import register_blueprints
    register_blueprints(app)
    threading.Thread(target=_ensure_columns, daemon=True).start()
    logger.info("Blueprints registered successfully")
except Exception as e:
    logger.exception("FATAL: Failed to register blueprints during startup: %s", e)
    raise


@app.route("/health")
def health_check():
    return "ok", 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    logger.exception("Internal server error: %s", e)
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting development server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
