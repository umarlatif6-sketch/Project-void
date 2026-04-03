import os
import sys
import logging

import psycopg2
from psycopg2 import sql as pgsql

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        logger.warning("DATABASE_URL is not set — skipping migrations (no database available at build time)")
        return

    conn = psycopg2.connect(dsn)
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                password_hash VARCHAR(200) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversation_members (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) NOT NULL,
                user_id INTEGER REFERENCES users(id) NOT NULL,
                UNIQUE(conversation_id, user_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) NOT NULL,
                sender_id INTEGER REFERENCES users(id) NOT NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS fairy_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) NOT NULL UNIQUE,
                display_name VARCHAR(100),
                bio TEXT,
                avatar_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vortex_ledger (
                id SERIAL PRIMARY KEY,
                block_index INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT NOW(),
                previous_hash VARCHAR(72) NOT NULL,
                tx_type VARCHAR(30) NOT NULL,
                from_user_id INTEGER REFERENCES users(id),
                to_user_id INTEGER REFERENCES users(id),
                amount DECIMAL(18,4) NOT NULL,
                payload_hash VARCHAR(72),
                payload_size_bytes BIGINT,
                block_hash VARCHAR(72) NOT NULL,
                phase_key_signature VARCHAR(16),
                node_id VARCHAR(72)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vtx_unlocks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) NOT NULL,
                feature VARCHAR(40) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, feature)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vigilance_reports (
                id SERIAL PRIMARY KEY,
                reporter_id INTEGER REFERENCES users(id) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                severity VARCHAR(20) NOT NULL,
                category VARCHAR(40),
                steps_to_reproduce TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                admin_notes TEXT,
                vtx_reward DECIMAL(18,4) DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                reviewed_at TIMESTAMP,
                reviewed_by INTEGER REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vortex_gifts (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER REFERENCES users(id),
                recipient_id INTEGER REFERENCES users(id),
                amount DECIMAL(18,4),
                message_id INTEGER,
                conversation_id INTEGER,
                al_jabr_286_hash VARCHAR(72),
                chime_path VARCHAR(255),
                status VARCHAR(20) DEFAULT 'settled',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS blueprint_tokens (
                id SERIAL PRIMARY KEY,
                token_hash VARCHAR(72) NOT NULL UNIQUE,
                tier VARCHAR(20) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                edition_number INTEGER NOT NULL,
                total_editions INTEGER NOT NULL,
                price_gbp INTEGER NOT NULL,
                price_vtx DECIMAL(18,4) NOT NULL,
                image_path VARCHAR(500),
                metadata_json TEXT,
                minted_at TIMESTAMP DEFAULT NOW(),
                minted_by INTEGER REFERENCES users(id),
                status VARCHAR(20) DEFAULT 'available'
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS token_ownership (
                id SERIAL PRIMARY KEY,
                token_id INTEGER REFERENCES blueprint_tokens(id) NOT NULL,
                owner_id INTEGER REFERENCES users(id) NOT NULL,
                purchased_at TIMESTAMP DEFAULT NOW(),
                purchase_type VARCHAR(20) NOT NULL,
                stripe_session_id VARCHAR(200),
                vtx_ledger_block_id INTEGER,
                transfer_from_id INTEGER REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS manufacturing_fund (
                id SERIAL PRIMARY KEY,
                token_id INTEGER REFERENCES blueprint_tokens(id) NOT NULL,
                amount_gbp INTEGER NOT NULL,
                purpose VARCHAR(40) NOT NULL,
                allocated_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(20) DEFAULT 'pledged'
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS mystery_collection (
                id SERIAL PRIMARY KEY,
                total_supply INTEGER NOT NULL DEFAULT 1000,
                minted_count INTEGER NOT NULL DEFAULT 0,
                base_price_vtx DECIMAL(18,4) NOT NULL DEFAULT 50,
                price_step_threshold INTEGER NOT NULL DEFAULT 250,
                step_multiplier DECIMAL(5,2) NOT NULL DEFAULT 2.0,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("SELECT COUNT(*) FROM mystery_collection")
        if cur.fetchone()[0] == 0:
            cur.execute(
                """INSERT INTO mystery_collection
                       (total_supply, minted_count, base_price_vtx, price_step_threshold, step_multiplier)
                   VALUES (1000, 0, 50, 250, 2.0)"""
            )

        cur.execute("""
            CREATE TABLE IF NOT EXISTS token_listings (
                id SERIAL PRIMARY KEY,
                token_id INTEGER REFERENCES blueprint_tokens(id) NOT NULL UNIQUE,
                seller_id INTEGER REFERENCES users(id) NOT NULL,
                price_vtx DECIMAL(18,4) NOT NULL,
                price_gbp_pence INTEGER,
                listed_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(20) DEFAULT 'active'
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS token_rentals (
                id SERIAL PRIMARY KEY,
                token_id INTEGER REFERENCES blueprint_tokens(id) NOT NULL,
                owner_id INTEGER REFERENCES users(id) NOT NULL,
                renter_id INTEGER REFERENCES users(id),
                vtx_per_day DECIMAL(18,4) NOT NULL,
                max_days INTEGER NOT NULL DEFAULT 30,
                starts_at TIMESTAMP,
                ends_at TIMESTAMP,
                status VARCHAR(20) DEFAULT 'offered',
                total_vtx_paid DECIMAL(18,4) DEFAULT 0,
                access_tier VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS market_configs (
                id SERIAL PRIMARY KEY,
                item_key VARCHAR(50) NOT NULL UNIQUE,
                display_name VARCHAR(200) NOT NULL,
                gbp_pence INTEGER NOT NULL,
                vtx_cost DECIMAL(18,4) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS yield_events (
                id SERIAL PRIMARY KEY,
                amount_gbp INTEGER NOT NULL,
                amount_vtx DECIMAL(18,4) NOT NULL,
                notes TEXT,
                posted_at TIMESTAMP DEFAULT NOW(),
                posted_by INTEGER REFERENCES users(id),
                idempotency_key VARCHAR(72) UNIQUE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS yield_claims (
                id SERIAL PRIMARY KEY,
                owner_id INTEGER REFERENCES users(id) NOT NULL,
                token_id INTEGER REFERENCES blueprint_tokens(id) NOT NULL,
                event_id INTEGER REFERENCES yield_events(id) NOT NULL,
                amount_vtx DECIMAL(18,4) NOT NULL,
                claimed_at TIMESTAMP,
                UNIQUE(owner_id, token_id, event_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS chronicle_entries (
                id SERIAL PRIMARY KEY,
                chapter_number INTEGER NOT NULL DEFAULT 0,
                title VARCHAR(200) NOT NULL,
                subtitle VARCHAR(300),
                glyph_sequence VARCHAR(200) NOT NULL DEFAULT '',
                body_text TEXT NOT NULL DEFAULT '',
                posted_at TIMESTAMP DEFAULT NOW(),
                posted_by INTEGER REFERENCES users(id),
                al_jabr_hash VARCHAR(72)
            )
        """)

        _optional_columns = [
            ("users",    "role",                   "VARCHAR(20) DEFAULT 'user'"),
            ("users",    "tier",                   "VARCHAR(20) DEFAULT 'ghost'"),
            ("users",    "tier_expires_at",        "TIMESTAMP"),
            ("users",    "stripe_customer_id",     "VARCHAR(100)"),
            ("users",    "stripe_subscription_id", "VARCHAR(100)"),
            ("users",    "vortex_balance",         "DECIMAL(18,4) DEFAULT 0"),
            ("users",    "last_free_mint_at",      "TIMESTAMP"),
            ("users",    "game_level",             "INTEGER DEFAULT 1"),
            ("users",    "nodes_built",            "INTEGER DEFAULT 0"),
            ("users",    "vaults_opened",          "INTEGER DEFAULT 0"),
            ("users",    "glyphs_solved",          "INTEGER DEFAULT 0"),
            ("users",    "total_game_vtx",         "DECIMAL(18,4) DEFAULT 0"),
            ("messages", "attachment_filename",    "VARCHAR(255)"),
            ("messages", "attachment_path",        "VARCHAR(500)"),
            ("messages", "attachment_size",        "BIGINT"),
            ("messages", "attachment_type",        "VARCHAR(50)"),
            ("messages", "silt_hash_key",          "TEXT"),
            ("messages", "silt_carrier_style",     "VARCHAR(50)"),
            ("messages", "vtx_earned",             "DECIMAL(18,4) DEFAULT 0"),
            ("blueprint_tokens",  "collection",   "VARCHAR(20) DEFAULT 'genesis'"),
            ("blueprint_tokens",  "revealed_at",  "TIMESTAMP"),
            ("token_rentals",     "access_tier",  "VARCHAR(20)"),
            ("chronicle_entries", "entry_type",   "VARCHAR(50) DEFAULT 'chronicle'"),
            ("chronicle_entries", "full_text",    "TEXT"),
            ("chronicle_entries", "season",       "VARCHAR(20) DEFAULT 'INCUBATION'"),
        ]
        for (table, column, definition) in _optional_columns:
            cur.execute(
                "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
                (table, column),
            )
            if not cur.fetchone():
                cur.execute(
                    pgsql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                        pgsql.Identifier(table),
                        pgsql.Identifier(column),
                        pgsql.SQL(definition),
                    )
                )

        indexes = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_ledger_block_index ON vortex_ledger(block_index)",
            "CREATE INDEX IF NOT EXISTS idx_ledger_from ON vortex_ledger(from_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_ledger_to ON vortex_ledger(to_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_ledger_payload_hash ON vortex_ledger(payload_hash)",
            "CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_stripe_cust ON users(stripe_customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_stripe_sub ON users(stripe_subscription_id)",
            "CREATE INDEX IF NOT EXISTS idx_unlocks_user ON vtx_unlocks(user_id, expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_vigilance_reporter ON vigilance_reports(reporter_id)",
            "CREATE INDEX IF NOT EXISTS idx_gifts_sender ON vortex_gifts(sender_id)",
            "CREATE INDEX IF NOT EXISTS idx_gifts_recipient ON vortex_gifts(recipient_id)",
            "CREATE INDEX IF NOT EXISTS idx_blueprint_tokens_tier ON blueprint_tokens(tier)",
            "CREATE INDEX IF NOT EXISTS idx_blueprint_tokens_status ON blueprint_tokens(status)",
            "CREATE INDEX IF NOT EXISTS idx_token_ownership_owner ON token_ownership(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_token_ownership_token ON token_ownership(token_id)",
            "CREATE INDEX IF NOT EXISTS idx_mfg_fund_token ON manufacturing_fund(token_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_ownership_stripe_session ON token_ownership(stripe_session_id) WHERE stripe_session_id IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS idx_token_listings_seller ON token_listings(seller_id)",
            "CREATE INDEX IF NOT EXISTS idx_token_listings_status ON token_listings(status)",
            "CREATE INDEX IF NOT EXISTS idx_token_rentals_token ON token_rentals(token_id)",
            "CREATE INDEX IF NOT EXISTS idx_token_rentals_renter ON token_rentals(renter_id)",
            "CREATE INDEX IF NOT EXISTS idx_token_rentals_owner ON token_rentals(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_chronicle_chapter ON chronicle_entries(chapter_number)",
        ]
        for idx_sql in indexes:
            cur.execute(idx_sql)

        market_rows = [
            ("nft_common",          "Blueprint Token — Common (Vibe-Coder Access)",   2800,    50,    True),
            ("nft_rare",            "Blueprint Token — Rare (Fractional Node)",        66000,   1000,  True),
            ("nft_legendary",       "Blueprint Token — Legendary (Sovereign Machine)", 2500000, 40000, True),
            ("vtx_starter",         "VTX Pack — Starter (50 VTX)",                    500,     0,     True),
            ("vtx_builder",         "VTX Pack — Builder (250 VTX)",                   2000,    0,     True),
            ("vtx_sovereign_stack", "VTX Pack — Sovereign Stack (1000 VTX)",          6500,    0,     True),
        ]
        for (item_key, display_name, gbp_pence, vtx_cost, is_active) in market_rows:
            cur.execute(
                """INSERT INTO market_configs (item_key, display_name, gbp_pence, vtx_cost, is_active)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (item_key) DO NOTHING""",
                (item_key, display_name, gbp_pence, vtx_cost, is_active),
            )

        constraints = [
            ("blueprint_tokens", "chk_bt_tier",
             "ALTER TABLE blueprint_tokens ADD CONSTRAINT chk_bt_tier CHECK (tier IN ('common','rare','legendary','mystery'))"),
            ("blueprint_tokens", "chk_bt_status",
             "ALTER TABLE blueprint_tokens ADD CONSTRAINT chk_bt_status CHECK (status IN ('available','reserved','sold','sealed','revealed','merged'))"),
            ("token_ownership", "chk_to_type",
             "ALTER TABLE token_ownership ADD CONSTRAINT chk_to_type CHECK (purchase_type IN ('vtx','stripe','free','merge'))"),
            ("manufacturing_fund", "chk_mf_purpose",
             "ALTER TABLE manufacturing_fund ADD CONSTRAINT chk_mf_purpose CHECK (purpose IN ('capex','materials','assembly'))"),
            ("manufacturing_fund", "chk_mf_status",
             "ALTER TABLE manufacturing_fund ADD CONSTRAINT chk_mf_status CHECK (status IN ('pledged','spent'))"),
        ]
        for (tbl, chk_name, chk_sql) in constraints:
            cur.execute("SAVEPOINT chk_sp")
            try:
                cur.execute(chk_sql)
                cur.execute("RELEASE SAVEPOINT chk_sp")
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT chk_sp")
                cur.execute("RELEASE SAVEPOINT chk_sp")
                cur.execute("SAVEPOINT chk_drop_sp")
                try:
                    cur.execute(
                        pgsql.SQL("ALTER TABLE {} DROP CONSTRAINT IF EXISTS {}").format(
                            pgsql.Identifier(tbl),
                            pgsql.Identifier(chk_name),
                        )
                    )
                    cur.execute(chk_sql)
                    cur.execute("RELEASE SAVEPOINT chk_drop_sp")
                except Exception:
                    cur.execute("ROLLBACK TO SAVEPOINT chk_drop_sp")
                    cur.execute("RELEASE SAVEPOINT chk_drop_sp")

        conn.commit()
        logger.info("Migration complete — all tables and indexes are up to date")

    except Exception:
        logger.exception("Migration failed — rolling back")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    run()
