"""
PROJECT VOID — Production DB Schema Init
Version 2.0 | April 2026

Creates all sequences and tables that are not managed by the main ORM.
Safe to call on every startup — all statements use IF NOT EXISTS.
"""

import logging
from void_engine.db_pool import get_db

logger = logging.getLogger(__name__)

_SEQUENCES = """
CREATE SEQUENCE IF NOT EXISTS seq_vtx_transaction_id
    AS bigint INCREMENT BY 1 MINVALUE 1000000000 START WITH 1000000000 CACHE 100 NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_node_id
    AS bigint INCREMENT BY 1 MINVALUE 100000 START WITH 100000 CACHE 50 NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_glyph_event_id
    AS bigint INCREMENT BY 1 MINVALUE 1 START WITH 1 CACHE 200 NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_chronicle_event_id
    AS bigint INCREMENT BY 1 MINVALUE 1 START WITH 1 CACHE 100 NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_adriana_interaction_id
    AS bigint INCREMENT BY 1 MINVALUE 1 START WITH 1 CACHE 100 NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_hardware_rmw_id
    AS bigint INCREMENT BY 1 MINVALUE 1000 START WITH 1000 CACHE 20 NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_mrb4000_unit_id
    AS bigint INCREMENT BY 1 MINVALUE 400000 START WITH 400000 CACHE 10 NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_silt_drop_id
    AS bigint INCREMENT BY 1 MINVALUE 1 START WITH 1 CACHE 100 NO CYCLE;

CREATE SEQUENCE IF NOT EXISTS seq_blueprint_token_id
    AS bigint INCREMENT BY 1 MINVALUE 1 START WITH 1 CACHE 50 NO CYCLE;
"""

_TABLES = """
CREATE TABLE IF NOT EXISTS glyph_events (
    event_id        bigint PRIMARY KEY DEFAULT nextval('seq_glyph_event_id'),
    user_id         integer REFERENCES users(id),
    glyph           text NOT NULL,
    frequency       numeric(6,1),
    domain          text,
    harmonic_state  text,
    created_at      timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS adriana_interactions (
    interaction_id  bigint PRIMARY KEY DEFAULT nextval('seq_adriana_interaction_id'),
    user_id         integer REFERENCES users(id),
    input           text,
    response        text,
    glyph           text,
    created_at      timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sovereign_nodes (
    node_id         bigint PRIMARY KEY DEFAULT nextval('seq_node_id'),
    owner_id        integer REFERENCES users(id),
    status          text DEFAULT 'pirate_build',
    serial          text UNIQUE,
    created_at      timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hardware_rmw01 (
    rmw_id          bigint PRIMARY KEY DEFAULT nextval('seq_hardware_rmw_id'),
    node_id         bigint REFERENCES sovereign_nodes(node_id),
    status          text DEFAULT 'preparation',
    hardness        numeric(5,2),
    resistivity     numeric(8,2),
    created_at      timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mrb4000_units (
    unit_id         bigint PRIMARY KEY DEFAULT nextval('seq_mrb4000_unit_id'),
    node_id         bigint REFERENCES sovereign_nodes(node_id),
    status          text DEFAULT 'assembly',
    created_at      timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS silt_drops (
    drop_id         bigint PRIMARY KEY DEFAULT nextval('seq_silt_drop_id'),
    sender_id       integer REFERENCES users(id),
    receiver_id     integer REFERENCES users(id),
    carrier_hash    text,
    created_at      timestamptz DEFAULT now()
);
"""

_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_glyph_events_user      ON glyph_events(user_id);
CREATE INDEX IF NOT EXISTS idx_adriana_interactions_user ON adriana_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_silt_drops_sender      ON silt_drops(sender_id);
CREATE INDEX IF NOT EXISTS idx_silt_drops_receiver    ON silt_drops(receiver_id);
"""

_COMMENTS = """
COMMENT ON TABLE glyph_events         IS 'Every meaningful action becomes a glyph poem';
COMMENT ON TABLE adriana_interactions  IS 'Persistent record of every /speak exchange with Adriana';
COMMENT ON TABLE sovereign_nodes       IS 'Physical 4000-Series hardware units';
COMMENT ON TABLE hardware_rmw01        IS 'Bio-Steel composite manufacturing records';
COMMENT ON TABLE mrb4000_units         IS 'MRB-4000 unit assembly records';
COMMENT ON TABLE silt_drops            IS 'Steganographic hidden message transmissions';
"""


def init_void_schema():
    """
    Idempotent schema initialisation. Creates sequences, tables, indexes,
    and comments for the six tables that are not managed elsewhere.

    Called from _startup_migrations() in app.py. Safe to call on every boot.
    """
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(_SEQUENCES)
        conn.commit()

        cur.execute(_TABLES)
        conn.commit()

        cur.execute(_INDEXES)
        conn.commit()

        try:
            cur.execute(_COMMENTS)
            conn.commit()
        except Exception:
            conn.rollback()

        cur.close()
        conn.close()
        logger.info("[VoidSchema] Production schema initialised successfully.")
    except Exception as e:
        logger.error("[VoidSchema] Schema init failed: %s", e)
