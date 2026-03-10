import os
import sys
import logging
import threading
from flask import Flask, render_template, jsonify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_secret = os.environ.get("SESSION_SECRET")
if not _secret:
    logger.critical(
        "SESSION_SECRET environment variable is not set. "
        "The application cannot start without it. "
        "Set this secret in the Deployments secrets panel."
    )
    sys.exit(1)

app.secret_key = _secret
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

logger.info("Registering application blueprints...")

try:
    from routes.auth import _ensure_columns
    from routes import register_blueprints
    register_blueprints(app)
    logger.info("Blueprints registered successfully.")
except Exception as exc:
    logger.critical("Failed to register blueprints: %s", exc, exc_info=True)
    sys.exit(1)

threading.Thread(target=_ensure_columns, daemon=True).start()


@app.route("/health")
def health_check():
    return jsonify({"status": "ok"}), 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error("Internal server error: %s", e, exc_info=True)
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting development server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
