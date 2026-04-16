import os
import logging
from flask import Flask, render_template, request, session

from void_engine.startup_bootstrap import (
    load_local_env,
    run_startup_migrations,
    should_run_startup_migrations,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

load_local_env(logger)

_secret = os.environ.get("SESSION_SECRET")
if not _secret:
    logger.error("FATAL: SESSION_SECRET environment variable is not set")
    raise RuntimeError("SESSION_SECRET environment variable is required")

try:
    from void_engine.packet_security import read_packet_security_config, validate_packet_security_config

    _packet_security_cfg = read_packet_security_config()
    _packet_security_errors = validate_packet_security_config(_packet_security_cfg)
    if _packet_security_errors:
        for _err in _packet_security_errors:
            logger.error("FATAL: %s", _err)
        raise RuntimeError("Packet security configuration invalid in enforced mode")
    if _packet_security_cfg.enforce:
        logger.info(
            "Packet security enforce mode enabled (key_id=%s, require_sector_policy=%s, max_age=%ss)",
            _packet_security_cfg.signing_key_id,
            _packet_security_cfg.require_sector_policy,
            _packet_security_cfg.max_age_seconds,
        )
except Exception as _packet_security_exc:
    logger.error("FATAL: packet security bootstrap failed: %s", _packet_security_exc)
    raise

app.secret_key = _secret
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

from void_engine.stealth_cloak import stealth_gate
stealth_gate(app)

try:
    from routes import register_blueprints
    register_blueprints(app)
    if should_run_startup_migrations():
        run_startup_migrations(logger)
    else:
        logger.info("Startup migrations disabled for this process")
    logger.info("Blueprints registered successfully")
except Exception as e:
    logger.exception("FATAL: Failed to register blueprints during startup: %s", e)
    raise

try:
    from void_engine.resonance_engine import inject_resonance_engine
    inject_resonance_engine(app)
except Exception as e:
    logger.warning("ResonanceEngine injection skipped: %s", e)


_LANG_SWITCHER_HTML = None

def _get_lang_switcher_html():
    global _LANG_SWITCHER_HTML
    if _LANG_SWITCHER_HTML is None:
        switcher_path = os.path.join(os.path.dirname(__file__), "templates", "partials", "language_switcher.html")
        try:
            with open(switcher_path, "r", encoding="utf-8") as f:
                _LANG_SWITCHER_HTML = f.read().strip()
        except Exception:
            _LANG_SWITCHER_HTML = ""
    return _LANG_SWITCHER_HTML


_LANG_SWITCHER_EXCLUDED_PREFIXES = ("/enter",)


@app.after_request
def inject_language_switcher(response):
    from flask import request as _req
    if any(_req.path.startswith(p) for p in _LANG_SWITCHER_EXCLUDED_PREFIXES):
        return response
    if response.content_type and "text/html" in response.content_type:
        content = response.get_data(as_text=True)
        if "<html" not in content or "</body>" not in content:
            return response

        script_tag = '<script src="/static/lang_switcher.js"></script>'
        has_switcher = "lang-switcher" in content
        has_script = "lang_switcher.js" in content

        inject_parts = []
        if not has_switcher:
            switcher = _get_lang_switcher_html()
            if switcher:
                inject_parts.append(
                    '<div style="position:fixed;top:12px;right:16px;z-index:9999">'
                    + switcher
                    + "</div>"
                )
        if not has_script:
            inject_parts.append(script_tag)

        if inject_parts:
            content = content.replace("</body>", "\n".join(inject_parts) + "\n</body>", 1)
            response.set_data(content)
    return response


@app.route("/health")
def health_check():
    return "ok", 200


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)


@app.errorhandler(500)
def internal_error(e):
    logger.exception("Internal server error: %s", e)
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting development server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
