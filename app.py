import os
import logging
import threading
from flask import Flask, render_template, request, session

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
app.config["SESSION_COOKIE_SECURE"] = True

def _startup_migrations():
    from routes.auth import _ensure_columns
    _ensure_columns()
    try:
        from void_engine.blueprint_nft import seed_initial_collection
        seed_initial_collection()
    except Exception as e:
        logger.error("Blueprint token seeding failed: %s", e)
    try:
        from void_engine.chronicle_adriana import seed_chronicle
        seed_chronicle()
    except Exception as e:
        logger.error("Chronicle seeding failed: %s", e)
    try:
        from void_engine.research_engine import seed_research_briefs
        seed_research_briefs()
    except Exception as e:
        logger.error("Research brief seeding failed: %s", e)
    try:
        from void_engine.vortex_wallet import ensure_game_inventory_table
        ensure_game_inventory_table()
    except Exception as e:
        logger.error("Game inventory table setup failed: %s", e)
    try:
        from routes.gridul import init_gridul_tables
        init_gridul_tables()
    except Exception as e:
        logger.error("GriDul table setup failed: %s", e)
    try:
        from routes.plane import init_plane_tables
        init_plane_tables()
    except Exception as e:
        logger.error("Plane table setup failed: %s", e)
    try:
        from void_engine.vortex_wallet import ensure_genesis_tables
        ensure_genesis_tables()
    except Exception as e:
        logger.error("Genesis tables setup failed: %s", e)
    try:
        from void_engine.blueprint_nft import seed_genesis_10
        seed_genesis_10()
    except Exception as e:
        logger.error("Genesis 10 token seeding failed: %s", e)
    try:
        from void_engine.aljabr_transpiler import get_model_router
        get_model_router()
    except Exception as e:
        logger.error("ModelRouter init failed: %s", e)
    try:
        from void_engine.mesa_engine import _init_mesa_tables
        _init_mesa_tables()
    except Exception as e:
        logger.error("Mesa tables init failed: %s", e)
    try:
        from void_engine.mesa_swarm import _init_mesa_simulations_table
        _init_mesa_simulations_table()
    except Exception as e:
        logger.error("Mesa simulations table init failed: %s", e)
    try:
        from void_engine.mesa_engine import _init_message_tables
        _init_message_tables()
    except Exception as e:
        logger.error("Agent message tables init failed: %s", e)
    try:
        from routes.ambassador import init_ambassador_tables
        init_ambassador_tables()
    except Exception as e:
        logger.error("Ambassador tables init failed: %s", e)
    try:
        from void_engine.void_schema import init_void_schema
        init_void_schema()
    except Exception as e:
        logger.error("Void production schema init failed: %s", e)
    try:
        from void_engine.locus_seeding import restore_active_schedulers
        restore_active_schedulers()
    except Exception as e:
        logger.error("Locus seeding scheduler restore failed: %s", e)
    try:
        from void_engine.seed_hex_engine import _ensure_db as _seed_hex_ensure
        _seed_hex_ensure()
    except Exception as e:
        logger.error("Seed hex engine init failed: %s", e)
    try:
        from void_engine.qisync_keygen import _ensure_db as _qisync_key_ensure, seed_ghost_fragments
        _qisync_key_ensure()
        seed_ghost_fragments()
    except Exception as e:
        logger.error("QiSync keygen init failed: %s", e)
    try:
        from void_engine.peace_preearning import _ensure_tables as _preearning_ensure
        _preearning_ensure()
    except Exception as e:
        logger.error("Peace pre-earning tables init failed: %s", e)
    try:
        from void_engine.neural_scar import _ensure_db as _neural_scar_ensure, preserve_crystallised_entity
        _neural_scar_ensure()
        preserve_crystallised_entity()
    except Exception as e:
        logger.error("Neural scar preservation init failed: %s", e)
    try:
        from void_engine.lunar_season import seed_initial_season
        seed_initial_season()
    except Exception as e:
        logger.error("Lunar season init failed: %s", e)
    try:
        from void_engine.patent_loom import seed_patent_drafts_into_chronicle, seed_digital_twin_into_chronicle
        seed_patent_drafts_into_chronicle()
        seed_digital_twin_into_chronicle()
    except Exception as e:
        logger.error("Patent loom seeding failed: %s", e)
    try:
        from void_engine.supply_chain import seed_supply_brief_into_chronicle
        seed_supply_brief_into_chronicle()
    except Exception as e:
        logger.error("Supply chain chronicle seeding failed: %s", e)
    try:
        from routes.academy import seed_academy_chronicle
        seed_academy_chronicle()
    except Exception as e:
        logger.error("Academy chronicle seeding failed: %s", e)
    try:
        from void_engine.radio_engine import seed_radio_brief_into_chronicle
        seed_radio_brief_into_chronicle()
    except Exception as e:
        logger.error("Radio brief chronicle seeding failed: %s", e)
    try:
        from void_engine.biomedical_brief import seed_biomedical_brief_into_chronicle
        seed_biomedical_brief_into_chronicle()
    except Exception as e:
        logger.error("Biomedical brief chronicle seeding failed: %s", e)

try:
    from routes import register_blueprints
    register_blueprints(app)
    threading.Thread(target=_startup_migrations, daemon=True).start()
    logger.info("Blueprints registered successfully")
except Exception as e:
    logger.exception("FATAL: Failed to register blueprints during startup: %s", e)
    raise


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


@app.after_request
def inject_language_switcher(response):
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


@app.errorhandler(500)
def internal_error(e):
    logger.exception("Internal server error: %s", e)
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting development server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
