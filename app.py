import os
from flask import Flask

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "void-engine-dev-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

from routes.auth import _ensure_columns

_ensure_columns()
from routes import register_blueprints

register_blueprints(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
