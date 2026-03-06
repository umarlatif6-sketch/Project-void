import os
import psycopg2
from decimal import Decimal
from datetime import datetime, timezone
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str, fatiha_286_truncated


def _get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])


VTX_PER_MB = Decimal("1.0")
VTX_MIN_MINT = Decimal("0.001")
VTX_PER_RELAY = Decimal("0.1")

VIGILANCE_BOUNTY = {
    "critical": Decimal("50"),
    "high": Decimal("25"),
    "medium": Decimal("10"),
    "low": Decimal("5"),
    "cosmetic": Decimal("1"),
}


def _get_last_block(cur):
    cur.execute("SELECT block_index, block_hash FROM vortex_ledger ORDER BY block_index DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        return row[0], row[1]
    return 0, "0" * 72


def _create_block(cur, tx_type, from_user_id, to_user_id, amount, payload_hash=None, payload_size_bytes=None):
    last_index, prev_hash = _get_last_block(cur)
    new_index = last_index + 1
    ts = datetime.now(timezone.utc).isoformat()
    block_data = f"{new_index}|{prev_hash}|{ts}|{tx_type}|{from_user_id or 'MINT'}|{to_user_id}|{amount}"
    if payload_hash:
        block_data += f"|{payload_hash}"
    block_hash = fatiha_286_hexdigest_from_str(block_data)
    phase_sig = fatiha_286_truncated(block_data.encode("utf-8"), 16)

    machine_id = os.environ.get("REPL_ID", "local")
    node_id = fatiha_286_truncated(machine_id.encode("utf-8"), 16)

    cur.execute(
        """INSERT INTO vortex_ledger (block_index, previous_hash, tx_type, from_user_id, to_user_id,
                                       amount, payload_hash, payload_size_bytes, block_hash, phase_key_signature, node_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (new_index, prev_hash, tx_type, from_user_id, to_user_id,
         amount, payload_hash, payload_size_bytes, block_hash, phase_sig, node_id),
    )
    return {
        "block_index": new_index,
        "block_hash": block_hash,
        "phase_key_signature": phase_sig,
        "amount": float(amount),
        "tx_type": tx_type,
    }


def mint_resonance(user_id, payload_size_bytes, payload_hash):
    size_mb = Decimal(payload_size_bytes) / Decimal(1024 * 1024)
    amount = max(size_mb * VTX_PER_MB, VTX_MIN_MINT)
    amount = amount.quantize(Decimal("0.0001"))

    conn = _get_db()
    try:
        cur = conn.cursor()
        block = _create_block(cur, "mint_resonance", None, user_id, amount, payload_hash, payload_size_bytes)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (amount, user_id),
        )
        conn.commit()
        block["vtx_earned"] = float(amount)
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mint_relay(user_id, packets_relayed=1):
    amount = (VTX_PER_RELAY * Decimal(packets_relayed)).quantize(Decimal("0.0001"))
    if amount <= 0:
        return None

    conn = _get_db()
    try:
        cur = conn.cursor()
        block = _create_block(cur, "mint_relay", None, user_id, amount)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (amount, user_id),
        )
        conn.commit()
        block["vtx_earned"] = float(amount)
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def transfer(from_user_id, to_user_id, amount_float):
    amount = Decimal(str(amount_float)).quantize(Decimal("0.0001"))
    if amount <= 0:
        return {"error": "Amount must be positive"}

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s", (from_user_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Sender not found"}
        balance = row[0]
        if balance < amount:
            return {"error": f"Insufficient balance. You have {float(balance)} VTX"}

        cur.execute("SELECT 1 FROM users WHERE id = %s", (to_user_id,))
        if not cur.fetchone():
            return {"error": "Recipient not found"}

        block = _create_block(cur, "transfer", from_user_id, to_user_id, amount)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) - %s WHERE id = %s",
            (amount, from_user_id),
        )
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (amount, to_user_id),
        )
        conn.commit()
        block["transferred"] = float(amount)
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_balance(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()


def get_ledger(user_id, limit=50):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT vl.block_index, vl.timestamp, vl.tx_type, vl.from_user_id, vl.to_user_id,
                      vl.amount, vl.payload_hash, vl.payload_size_bytes, vl.block_hash, vl.phase_key_signature,
                      fu.username as from_username, tu.username as to_username
               FROM vortex_ledger vl
               LEFT JOIN users fu ON fu.id = vl.from_user_id
               JOIN users tu ON tu.id = vl.to_user_id
               WHERE vl.from_user_id = %s OR vl.to_user_id = %s
               ORDER BY vl.block_index DESC LIMIT %s""",
            (user_id, user_id, limit),
        )
        entries = []
        for row in cur.fetchall():
            entries.append({
                "block_index": row[0],
                "timestamp": row[1].isoformat() if row[1] else None,
                "tx_type": row[2],
                "from_user_id": row[3],
                "to_user_id": row[4],
                "amount": float(row[5]),
                "payload_hash": row[6],
                "payload_size_bytes": row[7],
                "block_hash": row[8],
                "phase_key_signature": row[9],
                "from_username": row[10],
                "to_username": row[11],
            })
        return entries
    finally:
        conn.close()


def get_chain_stats():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vortex_ledger")
        total_blocks = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM vortex_ledger WHERE tx_type LIKE 'mint_%'")
        total_minted = float(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM users WHERE COALESCE(vortex_balance, 0) > 0")
        active_holders = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(vortex_balance), 0) FROM users")
        circulating = float(cur.fetchone()[0])
        return {
            "total_blocks": total_blocks,
            "total_minted": total_minted,
            "active_holders": active_holders,
            "circulating_supply": circulating,
            "symbol": "VTX",
            "chain_type": "Al-Jabr 286-bit Sovereign Hash",
            "consensus": "Proof of Resonance",
        }
    finally:
        conn.close()


def mint_vigilance(user_id, amount_decimal, report_id):
    amount = amount_decimal.quantize(Decimal("0.0001"))
    if amount <= 0:
        return None
    payload_hash = fatiha_286_hexdigest_from_str(f"vigilance_report_{report_id}")

    conn = _get_db()
    try:
        cur = conn.cursor()
        block = _create_block(cur, "mint_vigilance", None, user_id, amount, payload_hash)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (amount, user_id),
        )
        conn.commit()
        block["vtx_earned"] = float(amount)
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def validate_chain(limit=100):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT block_index, previous_hash, block_hash FROM vortex_ledger ORDER BY block_index ASC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        if not rows:
            return {"valid": True, "blocks_checked": 0, "message": "Empty chain"}

        valid = True
        errors = []
        for i in range(1, len(rows)):
            expected_prev = rows[i - 1][2]
            actual_prev = rows[i][1]
            if expected_prev != actual_prev:
                valid = False
                errors.append(f"Block {rows[i][0]}: previous_hash mismatch (expected {expected_prev[:16]}..., got {actual_prev[:16]}...)")

        return {
            "valid": valid,
            "blocks_checked": len(rows),
            "errors": errors,
            "message": "Chain integrity verified" if valid else f"{len(errors)} chain break(s) detected",
        }
    finally:
        conn.close()
