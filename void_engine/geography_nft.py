import json
import logging
from decimal import Decimal
from datetime import datetime, timezone
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str, fatiha_286_truncated
from void_engine.vortex_wallet import _create_block
from void_engine.blueprint_nft import mint_token_with_cursor

logger = logging.getLogger(__name__)

GEOGRAPHY_MINT_COST = Decimal("5")

TX_TYPE_LABELS = {
    "mint_resonance":  "VoidEcho Encode",
    "mint_relay":      "Mesh Relay",
    "mint_vigilance":  "Vigilance Reward",
    "mint_purchase":   "VTX Purchase",
    "mint_qisync":     "QiSync Session",
    "mint_gridul_move": "GriDul Move",
    "nft_purchase":    "NFT Acquisition",
    "nft_purchase_fiat": "NFT Acquisition",
    "burn":            "VTX Burn",
    "spend":           "VTX Spend",
    "transfer":        "VTX Transfer",
    "gift":            "VTX Gift",
    "ambassador_activation": "Ambassador Activation",
}


def _get_db():
    from void_engine.db_pool import get_db
    return get_db()


def _ensure_geography_tables():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS geography_claims (
                id SERIAL PRIMARY KEY,
                ledger_hash VARCHAR(72) NOT NULL UNIQUE,
                phase VARCHAR(60),
                owner_id INTEGER NOT NULL REFERENCES users(id),
                token_id INTEGER REFERENCES blueprint_tokens(id),
                claimed_at TIMESTAMP DEFAULT NOW(),
                source_tx_type VARCHAR(30),
                ledger_block_index INTEGER
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_geo_owner ON geography_claims(owner_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_geo_ledger ON geography_claims(ledger_hash)")
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to ensure geography tables")
    finally:
        conn.close()


def get_unclaimed_geographies(user_id, limit=50, offset=0):
    _ensure_geography_tables()
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT vl.block_hash, vl.phase_key_signature, vl.tx_type,
                      vl.timestamp, vl.block_index
               FROM vortex_ledger vl
               WHERE vl.to_user_id = %s
                 AND vl.block_hash NOT IN (
                     SELECT ledger_hash FROM geography_claims
                 )
                 AND vl.tx_type != 'geography_mint'
                 AND vl.block_hash IS NOT NULL
                 AND length(vl.block_hash) >= 8
               ORDER BY vl.block_index DESC
               LIMIT %s OFFSET %s""",
            (user_id, limit, offset),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            block_hash = r[0]
            phase = r[1] or "resonance"
            tx_type = r[2]
            timestamp = r[3]
            block_index = r[4]
            result.append({
                "ledger_hash": block_hash,
                "phase": phase,
                "tx_type": tx_type,
                "source_label": TX_TYPE_LABELS.get(tx_type, tx_type),
                "timestamp": timestamp.isoformat() if timestamp else None,
                "block_index": block_index,
            })
        return result
    finally:
        conn.close()


def get_claimed_geographies(user_id, limit=50, offset=0):
    _ensure_geography_tables()
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT gc.ledger_hash, gc.phase, gc.source_tx_type,
                      gc.claimed_at, gc.ledger_block_index, bt.id as token_id
               FROM geography_claims gc
               LEFT JOIN blueprint_tokens bt ON bt.id = gc.token_id
               WHERE gc.owner_id = %s
               ORDER BY gc.claimed_at DESC
               LIMIT %s OFFSET %s""",
            (user_id, limit, offset),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "ledger_hash": r[0],
                "phase": r[1] or "resonance",
                "tx_type": r[2],
                "source_label": TX_TYPE_LABELS.get(r[2] or "", r[2] or "Unknown"),
                "claimed_at": r[3].isoformat() if r[3] else None,
                "block_index": r[4],
                "token_id": r[5],
                "claimed": True,
            })
        return result
    finally:
        conn.close()


def mint_geography(user_id, ledger_hash, phase):
    _ensure_geography_tables()

    if not ledger_hash or len(ledger_hash) < 8:
        return {"error": "Invalid ledger hash"}

    conn = _get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            """SELECT block_hash, tx_type, to_user_id, from_user_id, phase_key_signature, block_index, timestamp
               FROM vortex_ledger
               WHERE block_hash = %s
               LIMIT 1""",
            (ledger_hash,),
        )
        ledger_row = cur.fetchone()
        if not ledger_row:
            return {"error": "Hash not found in ledger"}

        tx_to = ledger_row[2]
        tx_from = ledger_row[3]
        tx_type = ledger_row[1]
        ledger_phase = ledger_row[4]
        block_index = ledger_row[5]
        block_timestamp = ledger_row[6]

        if tx_to != user_id:
            return {"error": "This ledger entry does not belong to you"}

        cur.execute(
            "SELECT id FROM geography_claims WHERE ledger_hash = %s",
            (ledger_hash,),
        )
        if cur.fetchone():
            return {"error": "This geography has already been claimed"}

        cur.execute(
            "SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "User not found"}
        balance = row[0]
        if balance < GEOGRAPHY_MINT_COST:
            return {"error": f"Insufficient VTX. Need {float(GEOGRAPHY_MINT_COST)}, have {float(balance)}"}

        cur.execute(
            "UPDATE users SET vortex_balance = vortex_balance - %s WHERE id = %s",
            (GEOGRAPHY_MINT_COST, user_id),
        )

        resolved_phase = phase or ledger_phase or "resonance"
        source_label = TX_TYPE_LABELS.get(tx_type, tx_type)
        title = f"VOID Geography \u25c8 {ledger_hash[:8]}"
        description = (
            f"A unique glyph geography sealed from {source_label}. "
            f"Hash: {ledger_hash}. Phase: {resolved_phase}."
        )

        geo_payload_hash = fatiha_286_hexdigest_from_str(
            f"geography|{user_id}|{ledger_hash}|{resolved_phase}"
        )
        block = _create_block(
            cur, "geography_mint", user_id, None, GEOGRAPHY_MINT_COST, geo_payload_hash
        )

        token_id, _ = mint_token_with_cursor(
            cur,
            tier='common',
            title=title,
            description=description,
            edition=1,
            total_editions=1,
            price_gbp=0,
            price_vtx=float(GEOGRAPHY_MINT_COST),
            minted_by=user_id,
            extra_token_hash=geo_payload_hash,
            collection='geography',
            status='sold',
            metadata_override={
                "hash": ledger_hash,
                "phase": resolved_phase,
                "source": tx_type,
            },
        )

        cur.execute(
            """INSERT INTO token_ownership
               (token_id, owner_id, purchase_type, vtx_ledger_block_id)
               VALUES (%s, %s, 'vtx', %s)""",
            (token_id, user_id, block["block_index"]),
        )

        cur.execute(
            """INSERT INTO geography_claims
               (ledger_hash, phase, owner_id, token_id, source_tx_type, ledger_block_index)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (ledger_hash, resolved_phase, user_id, token_id, tx_type, block_index),
        )

        conn.commit()
        return {
            "success": True,
            "token_id": token_id,
            "title": title,
            "ledger_hash": ledger_hash,
            "phase": resolved_phase,
            "source": tx_type,
            "source_label": source_label,
            "spent_vtx": float(GEOGRAPHY_MINT_COST),
            "block": block,
        }
    except Exception as e:
        conn.rollback()
        logger.error("Geography mint failed: %s", e, exc_info=True)
        return {"error": "Geography mint failed. Please try again."}
    finally:
        conn.close()
