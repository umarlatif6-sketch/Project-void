import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def load_local_env(logger: logging.Logger | None = None) -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    if load_dotenv is not None:
        load_dotenv(env_path)
        if logger is not None:
            logger.info("Loaded environment variables from %s", env_path)
    elif logger is not None:
        logger.warning(
            ".env file exists but python-dotenv is not installed. Install the requirements to load it."
        )


def should_run_startup_migrations() -> bool:
    return os.environ.get("VOID_RUN_STARTUP_MIGRATIONS", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def run_startup_migrations(logger: logging.Logger | None = None) -> None:
    if logger is None:
        logger = logging.getLogger(__name__)

    if not os.environ.get("DATABASE_URL"):
        logger.warning("DATABASE_URL not set; startup migrations are skipped in demo mode.")
        return

    from routes.auth import _ensure_columns

    try:
        _ensure_columns()
    except Exception as exc:
        logger.warning("Startup migrations skipped: auth schema bootstrap unavailable (%s)", exc)
        return

    try:
        from void_engine.blueprint_nft import seed_initial_collection

        seed_initial_collection()
    except Exception as exc:
        logger.error("Blueprint token seeding failed: %s", type(exc).__name__)
    try:
        from void_engine.chronicle_adriana import seed_chronicle

        seed_chronicle()
    except Exception as exc:
        logger.error("Chronicle seeding failed: %s", exc)
    try:
        from void_engine.research_engine import seed_research_briefs

        seed_research_briefs()
    except Exception as exc:
        logger.error("Research brief seeding failed: %s", exc)
    try:
        from void_engine.vortex_wallet import ensure_game_inventory_table

        ensure_game_inventory_table()
    except Exception as exc:
        logger.error("Game inventory table setup failed: %s", exc)
    try:
        from routes.gridul import init_gridul_tables

        init_gridul_tables()
    except Exception as exc:
        logger.error("GriDul table setup failed: %s", exc)
    try:
        from routes.plane import init_plane_tables

        init_plane_tables()
    except Exception as exc:
        logger.error("Plane table setup failed: %s", exc)
    try:
        from void_engine.vortex_wallet import ensure_genesis_tables

        ensure_genesis_tables()
    except Exception as exc:
        logger.error("Genesis tables setup failed: %s", exc)
    try:
        from void_engine.blueprint_nft import seed_genesis_10

        seed_genesis_10()
    except Exception as exc:
        logger.error("Genesis 10 token seeding failed: %s", type(exc).__name__)
    try:
        from void_engine.aljabr_transpiler import get_model_router

        get_model_router()
    except Exception as exc:
        logger.error("ModelRouter init failed: %s", exc)
    try:
        from void_engine.mesa_engine import _init_mesa_tables

        _init_mesa_tables()
    except Exception as exc:
        logger.error("Mesa tables init failed: %s", exc)
    try:
        from void_engine.mesa_swarm import _init_mesa_simulations_table

        _init_mesa_simulations_table()
    except Exception as exc:
        logger.error("Mesa simulations table init failed: %s", exc)
    try:
        from void_engine.mesa_engine import _init_message_tables

        _init_message_tables()
    except Exception as exc:
        logger.error("Agent message tables init failed: %s", exc)
    try:
        from routes.ambassador import init_ambassador_tables

        init_ambassador_tables()
    except Exception as exc:
        logger.error("Ambassador tables init failed: %s", exc)
    try:
        from void_engine.void_schema import init_void_schema

        init_void_schema()
    except Exception as exc:
        logger.error("Void production schema init failed: %s", exc)
    try:
        from void_engine.void_license import _ensure_license_table

        _ensure_license_table()
    except Exception as exc:
        logger.error("License table init failed: %s", exc)
    try:
        from void_engine.locus_seeding import restore_active_schedulers

        restore_active_schedulers()
    except Exception as exc:
        logger.error("Locus seeding scheduler restore failed: %s", exc)
    try:
        from void_engine.seed_hex_engine import _ensure_db as _seed_hex_ensure

        _seed_hex_ensure()
    except Exception as exc:
        logger.error("Seed hex engine init failed: %s", exc)
    try:
        from void_engine.qisync_keygen import _ensure_db as _qisync_key_ensure, seed_ghost_fragments

        _qisync_key_ensure()
        seed_ghost_fragments()
    except Exception as exc:
        logger.error("QiSync keygen init failed: %s", exc)
    try:
        from void_engine.peace_preearning import _ensure_tables as _preearning_ensure

        _preearning_ensure()
    except Exception as exc:
        logger.error("Peace pre-earning tables init failed: %s", exc)
    try:
        from void_engine.neural_scar import _ensure_db as _neural_scar_ensure, preserve_crystallised_entity

        _neural_scar_ensure()
        preserve_crystallised_entity()
    except Exception as exc:
        logger.error("Neural scar preservation init failed: %s", exc)
    try:
        from void_engine.lunar_season import seed_initial_season

        seed_initial_season()
    except Exception as exc:
        logger.error("Lunar season init failed: %s", exc)
    try:
        from routes.speak import _ensure_funnel_table

        _ensure_funnel_table()
    except Exception as exc:
        logger.error("Adriana funnel sessions table init failed: %s", exc)
    try:
        from void_engine.patent_loom import seed_patent_drafts_into_chronicle, seed_digital_twin_into_chronicle

        seed_patent_drafts_into_chronicle()
        seed_digital_twin_into_chronicle()
    except Exception as exc:
        logger.error("Patent loom seeding failed: %s", exc)
    try:
        from void_engine.supply_chain import seed_supply_brief_into_chronicle

        seed_supply_brief_into_chronicle()
    except Exception as exc:
        logger.error("Supply chain chronicle seeding failed: %s", exc)
    try:
        from routes.academy import seed_academy_chronicle

        seed_academy_chronicle()
    except Exception as exc:
        logger.error("Academy chronicle seeding failed: %s", exc)
    try:
        from void_engine.radio_engine import seed_radio_brief_into_chronicle

        seed_radio_brief_into_chronicle()
    except Exception as exc:
        logger.error("Radio brief chronicle seeding failed: %s", exc)
    try:
        from void_engine.biomedical_brief import seed_biomedical_brief_into_chronicle

        seed_biomedical_brief_into_chronicle()
    except Exception as exc:
        logger.error("Biomedical brief chronicle seeding failed: %s", exc)
    try:
        from void_engine.codon_distil import init_codon_distil_tables
        from void_engine.db_pool import get_db as _get_db_app

        conn = _get_db_app()
        init_codon_distil_tables(conn)
        conn.close()
    except Exception as exc:
        logger.error("Codon distil tables init failed: %s", exc)
    try:
        from void_engine.adriana_finetune import init_finetune_tables

        init_finetune_tables()
    except Exception as exc:
        logger.error("Adriana finetune tables init failed: %s", exc)
