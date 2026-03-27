import os
from decimal import Decimal
from datetime import datetime, timezone
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str, fatiha_286_truncated
from void_engine.db_pool import get_db


def _get_db():
    return get_db()


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

VTX_PACKS = {
    "starter": {"vtx": Decimal("50"), "price_pence": 500, "label": "Starter", "bonus": ""},
    "builder": {"vtx": Decimal("250"), "price_pence": 2000, "label": "Builder", "bonus": "20% bonus"},
    "sovereign_stack": {"vtx": Decimal("1000"), "price_pence": 6500, "label": "Sovereign Stack", "bonus": "35% bonus"},
}

VTX_UNLOCK_FEATURES = {
    "extended_capacity": {"cost": Decimal("10"), "hours": 24, "label": "Extended Capacity (+10 MB)", "description": "Unlock 10 MB upload bonus for 24 hours"},
    "mesh_day_pass": {"cost": Decimal("25"), "hours": 24, "label": "Mesh Day Pass", "description": "Temporary mesh network access for 24 hours"},
    "journalism_day_pass": {"cost": Decimal("15"), "hours": 24, "label": "Journalism Day Pass", "description": "Temporary Silt Journalism access for 24 hours"},
}


def _get_last_block(cur):
    cur.execute("SELECT block_index, block_hash FROM vortex_ledger ORDER BY block_index DESC LIMIT 1 FOR UPDATE")
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
        cur.execute(
            "SELECT id FROM vortex_ledger WHERE payload_hash = %s AND tx_type = 'mint_resonance'",
            (payload_hash,),
        )
        if cur.fetchone():
            conn.close()
            return {"already_minted": True, "payload_hash": payload_hash}
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


def mint_relay(user_id, packets_relayed=1, relay_id=None):
    amount = (VTX_PER_RELAY * Decimal(packets_relayed)).quantize(Decimal("0.0001"))
    if amount <= 0:
        return None

    if not relay_id:
        relay_id = f"auto_{user_id}_{packets_relayed}_{int(datetime.now(timezone.utc).timestamp())}"

    payload_hash = fatiha_286_hexdigest_from_str(f"relay_{user_id}_{relay_id}")

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM vortex_ledger WHERE payload_hash = %s AND tx_type = 'mint_relay'",
            (payload_hash,),
        )
        if cur.fetchone():
            conn.close()
            return {"already_minted": True, "relay_id": relay_id}
        block = _create_block(cur, "mint_relay", None, user_id, amount, payload_hash)
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
        cur.execute("SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE", (from_user_id,))
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


def gift_transfer(from_user_id, to_user_id, amount_float, message_id=None):
    amount = Decimal(str(amount_float)).quantize(Decimal("0.0001"))
    if amount <= 0:
        return {"error": "Amount must be positive"}

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE", (from_user_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Sender not found"}
        balance = row[0]
        if balance < amount:
            return {"error": f"Insufficient balance. You have {float(balance)} VTX"}

        cur.execute("SELECT 1 FROM users WHERE id = %s", (to_user_id,))
        if not cur.fetchone():
            return {"error": "Recipient not found"}

        payload_hash = fatiha_286_hexdigest_from_str(
            f"gift_{from_user_id}_{to_user_id}_{amount}_{message_id}_{datetime.now(timezone.utc).isoformat()}"
        )
        block = _create_block(cur, "gift", from_user_id, to_user_id, amount, payload_hash)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) - %s WHERE id = %s",
            (amount, from_user_id),
        )
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (amount, to_user_id),
        )
        conn.commit()
        block["gifted"] = float(amount)
        block["gift_hash"] = payload_hash
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_burn_stats():
    """Returns a breakdown of all VTX burned across the platform."""
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM vortex_ledger WHERE tx_type IN ('burn', 'spend', 'spend_equipment')"
        )
        total_burned = float(cur.fetchone()[0])
        cur.execute(
            "SELECT COUNT(*) FROM vortex_ledger WHERE tx_type IN ('burn', 'spend', 'spend_equipment')"
        )
        burn_events = int(cur.fetchone()[0])
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM vortex_ledger WHERE tx_type LIKE 'mint_%'")
        total_minted = float(cur.fetchone()[0])
        cur.execute(
            """SELECT
                 COALESCE(SUM(CASE WHEN tx_type = 'burn' AND payload_hash LIKE 'equip_%' THEN amount ELSE 0 END), 0),
                 COALESCE(SUM(CASE WHEN tx_type IN ('burn', 'spend') THEN amount ELSE 0 END), 0)
               FROM vortex_ledger
               WHERE tx_type IN ('burn', 'spend', 'spend_equipment')"""
        )
        row = cur.fetchone()
        return {
            "total_burned": round(total_burned, 4),
            "burn_events": burn_events,
            "total_minted": round(total_minted, 4),
            "net_supply": round(total_minted - total_burned, 4),
            "burn_rate": round((total_burned / total_minted * 100) if total_minted > 0 else 0, 2),
        }
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
               LEFT JOIN users tu ON tu.id = vl.to_user_id
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
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM vortex_ledger WHERE tx_type IN ('burn', 'spend', 'spend_equipment')"
        )
        total_burned = float(cur.fetchone()[0])
        cur.execute(
            "SELECT COUNT(*) FROM vortex_ledger WHERE tx_type IN ('burn', 'spend', 'spend_equipment')"
        )
        burn_events = cur.fetchone()[0]
        return {
            "total_blocks": total_blocks,
            "total_minted": total_minted,
            "total_burned": total_burned,
            "burn_events": burn_events,
            "net_supply": round(total_minted - total_burned, 4),
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
        cur.execute(
            "SELECT id FROM vortex_ledger WHERE payload_hash = %s AND tx_type = 'mint_vigilance'",
            (payload_hash,),
        )
        if cur.fetchone():
            conn.close()
            return {"already_minted": True, "report_id": report_id}
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


def mint_purchase(user_id, amount_decimal, session_id):
    amount = amount_decimal.quantize(Decimal("0.0001"))
    if amount <= 0:
        return None
    payload_hash = fatiha_286_hexdigest_from_str(f"vtx_purchase_{session_id}")

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM vortex_ledger WHERE payload_hash = %s AND tx_type = 'mint_purchase'",
            (payload_hash,),
        )
        if cur.fetchone():
            conn.close()
            return {"already_minted": True, "session_id": session_id}
        block = _create_block(cur, "mint_purchase", None, user_id, amount, payload_hash)
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


def mint_qisync(user_id, session_id, metabolism_score, stance, duration_sec):
    """
    Grant VOID credits at the end of a QiSync BioStance / Mastication session.

    Thresholds:
      score >= 0.8  → 5.0 VTX  (excellent)
      score >= 0.6  → 3.0 VTX  (good)
      score >= 0.4  → 1.5 VTX  (developing)
      score >= 0.2  → 0.5 VTX  (beginner)
      score <  0.2  → 0.1 VTX  (participation)
    """
    if metabolism_score >= 0.8:
        base = Decimal("5.0")
    elif metabolism_score >= 0.6:
        base = Decimal("3.0")
    elif metabolism_score >= 0.4:
        base = Decimal("1.5")
    elif metabolism_score >= 0.2:
        base = Decimal("0.5")
    else:
        base = Decimal("0.1")

    duration_bonus = Decimal(str(min(duration_sec, 600))) / Decimal("600") * Decimal("0.5")
    amount = (base + duration_bonus).quantize(Decimal("0.0001"))

    payload_hash = fatiha_286_hexdigest_from_str(f"qisync_{user_id}_{session_id}")

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM vortex_ledger WHERE payload_hash = %s AND tx_type = 'mint_qisync'",
            (payload_hash,),
        )
        if cur.fetchone():
            conn.close()
            return {"already_minted": True, "session_id": session_id}
        block = _create_block(cur, "mint_qisync", None, user_id, amount, payload_hash)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (amount, user_id),
        )
        conn.commit()
        block["vtx_earned"] = float(amount)
        block["metabolism_score"] = metabolism_score
        block["stance"] = stance
        block["duration_sec"] = duration_sec
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def spend_vtx(user_id, amount_decimal, purpose):
    amount = amount_decimal.quantize(Decimal("0.0001"))
    if amount <= 0:
        return {"error": "Amount must be positive"}

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE", (user_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "User not found"}
        balance = row[0]
        if balance < amount:
            return {"error": f"Insufficient VTX balance. You have {float(balance)} VTX, need {float(amount)}"}

        payload_hash = fatiha_286_hexdigest_from_str(f"spend_{purpose}_{user_id}")
        block = _create_block(cur, "burn", user_id, None, amount, payload_hash)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) - %s WHERE id = %s",
            (amount, user_id),
        )
        conn.commit()
        block["spent"] = float(amount)
        block["purpose"] = purpose
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def spend_vtx_with_unlock(user_id, amount_decimal, feature, duration):
    from datetime import datetime, timezone
    amount = amount_decimal.quantize(Decimal("0.0001"))
    if amount <= 0:
        return {"error": "Amount must be positive"}

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE", (user_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "User not found"}
        balance = row[0]
        if balance < amount:
            return {"error": f"Insufficient VTX balance. You have {float(balance)} VTX, need {float(amount)}"}

        payload_hash = fatiha_286_hexdigest_from_str(f"spend_{feature}_{user_id}")
        block = _create_block(cur, "burn", user_id, None, amount, payload_hash)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) - %s WHERE id = %s",
            (amount, user_id),
        )

        expires = datetime.now(timezone.utc) + duration
        cur.execute(
            """INSERT INTO vtx_unlocks (user_id, feature, expires_at)
               VALUES (%s, %s, %s)
               ON CONFLICT (user_id, feature) DO UPDATE SET expires_at = EXCLUDED.expires_at""",
            (user_id, feature, expires),
        )

        conn.commit()
        block["spent"] = float(amount)
        block["purpose"] = feature
        block["expires_at"] = expires.isoformat()
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


GAME_REWARD_TIERS = {
    "vault_discovered": Decimal("0.5"),
    "glyph_solved": Decimal("1.0"),
    "node_built": Decimal("2.0"),
    "level_up": Decimal("5.0"),
}

GAME_DAILY_CAP = Decimal("50.0")

EQUIPMENT_CATALOG = {
    "signal_array": {
        "name": "Signal Array",
        "vtx_price": Decimal("15"),
        "multiplier": Decimal("1.25"),
        "description": "Enhanced resonance scanner. Boosts vault discovery rewards by 25%.",
        "icon": "📡",
        "tier": 1,
        "unlocks": "Deeper signal vaults with 25% higher VTX yield",
    },
    "resonance_coil": {
        "name": "Resonance Coil",
        "vtx_price": Decimal("35"),
        "multiplier": Decimal("1.25"),
        "description": "Amplifies node construction efficiency. +25% node building rewards.",
        "icon": "🔁",
        "tier": 2,
        "unlocks": "Bonus sovereign node slots, 25% node reward boost",
    },
    "adriana_decoder": {
        "name": "Adriana Decoder",
        "vtx_price": Decimal("50"),
        "multiplier": Decimal("1.5"),
        "description": "Unlocks advanced Adriana glyph chambers. +50% cipher rewards.",
        "icon": "Ψ",
        "tier": 3,
        "unlocks": "Hard-tier Adriana puzzles with 50% higher VTX yield",
    },
    "sovereign_rig": {
        "name": "Sovereign Rig",
        "vtx_price": Decimal("150"),
        "multiplier": Decimal("1.75"),
        "description": "Full sovereign loadout. All-mode +75% earn boost. Exclusive sovereign vaults.",
        "icon": "◆",
        "tier": 4,
        "unlocks": "All-mode 75% reward boost + exclusive Sovereign Vault zones",
    },
    "void_core": {
        "name": "Void Core",
        "vtx_price": Decimal("500"),
        "multiplier": Decimal("2.0"),
        "description": "Elite Al-Jabr 286 core. Doubles all in-game VTX earnings permanently.",
        "icon": "⬡",
        "tier": 5,
        "unlocks": "2x all rewards + Al-Jabr 286 exclusive cipher challenges",
    },
}


def ensure_game_inventory_table():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_inventory (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                equipment_slug VARCHAR(50) NOT NULL,
                purchased_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, equipment_slug)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_inventory(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT equipment_slug, purchased_at FROM game_inventory WHERE user_id = %s ORDER BY purchased_at ASC",
            (user_id,),
        )
        rows = cur.fetchall()
        owned = {}
        for slug, purchased_at in rows:
            item = EQUIPMENT_CATALOG.get(slug, {})
            owned[slug] = {
                "slug": slug,
                "name": item.get("name", slug),
                "icon": item.get("icon", "?"),
                "tier": item.get("tier", 0),
                "purchased_at": purchased_at.isoformat() if purchased_at else None,
            }
        return owned
    finally:
        conn.close()


def get_earning_multiplier(user_id):
    owned = get_inventory(user_id)
    best = Decimal("1.0")
    for slug in owned:
        m = EQUIPMENT_CATALOG.get(slug, {}).get("multiplier", Decimal("1.0"))
        if m > best:
            best = m
    return best


def spend_on_equipment(user_id, equipment_slug):
    item = EQUIPMENT_CATALOG.get(equipment_slug)
    if not item:
        return {"error": f"Unknown equipment: {equipment_slug}"}

    price = item["vtx_price"]
    conn = _get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT 1 FROM game_inventory WHERE user_id = %s AND equipment_slug = %s",
            (user_id, equipment_slug),
        )
        if cur.fetchone():
            return {"error": "already_owned", "message": "You already own this equipment."}

        cur.execute(
            "SELECT vortex_balance FROM users WHERE id = %s FOR UPDATE",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "User not found"}
        balance = Decimal(str(row[0] or 0))

        if balance < price:
            return {
                "error": "insufficient_vtx",
                "message": f"Need {price} VTX. You have {float(balance):.2f} VTX.",
                "balance": float(balance),
                "price": float(price),
            }

        payload_hash = fatiha_286_hexdigest_from_str(
            f"equip_{equipment_slug}_{user_id}_{datetime.now(timezone.utc).isoformat()}"
        )
        _create_block(cur, "burn", user_id, None, price, payload_hash)
        cur.execute(
            "UPDATE users SET vortex_balance = vortex_balance - %s WHERE id = %s",
            (price, user_id),
        )
        cur.execute(
            "INSERT INTO game_inventory (user_id, equipment_slug) VALUES (%s, %s)",
            (user_id, equipment_slug),
        )
        conn.commit()

        cur.execute("SELECT vortex_balance FROM users WHERE id = %s", (user_id,))
        new_balance = float(cur.fetchone()[0] or 0)
        return {
            "success": True,
            "equipment_slug": equipment_slug,
            "equipment_name": item["name"],
            "vtx_spent": float(price),
            "new_balance": new_balance,
            "multiplier": float(item["multiplier"]),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mint_game_reward(user_id, event_type, event_id=None):
    """
    Grant VTX for in-game events. Enforces a 50 VTX / 24-hour cap per user.
    Applies equipment earning multiplier (best item in inventory wins).
    Returns block dict on success or dict with error/cap_reached key.
    """
    base_amount = GAME_REWARD_TIERS.get(event_type)
    if base_amount is None:
        return {"error": f"Unknown game event type: {event_type}"}
    multiplier = get_earning_multiplier(user_id)
    amount = (base_amount * multiplier).quantize(Decimal("0.0001"))

    conn = _get_db()
    try:
        cur = conn.cursor()

        if event_id:
            dedup_hash = fatiha_286_hexdigest_from_str(f"game_{event_type}_{user_id}_{event_id}")
            cur.execute(
                "SELECT id FROM vortex_ledger WHERE payload_hash = %s AND tx_type = 'mint_game'",
                (dedup_hash,),
            )
            if cur.fetchone():
                conn.close()
                return {"already_minted": True, "event_id": event_id}
        else:
            dedup_hash = fatiha_286_hexdigest_from_str(
                f"game_{event_type}_{user_id}_{datetime.now(timezone.utc).isoformat()}"
            )

        cur.execute(
            """SELECT COALESCE(SUM(amount), 0)
               FROM vortex_ledger
               WHERE to_user_id = %s AND tx_type = 'mint_game'
                 AND timestamp >= NOW() - INTERVAL '24 hours'""",
            (user_id,),
        )
        earned_today = cur.fetchone()[0]
        if earned_today + amount > GAME_DAILY_CAP:
            conn.close()
            return {
                "cap_reached": True,
                "earned_today": float(earned_today),
                "daily_cap": float(GAME_DAILY_CAP),
                "message": "Daily VTX game cap of 50 VTX reached. Come back tomorrow!",
            }

        block = _create_block(cur, "mint_game", None, user_id, amount, dedup_hash)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (amount, user_id),
        )

        stat_col = {
            "vault_discovered": "vaults_opened",
            "glyph_solved": "glyphs_solved",
            "node_built": "nodes_built",
            "level_up": None,
        }.get(event_type)
        if stat_col:
            cur.execute(
                f"UPDATE users SET {stat_col} = COALESCE({stat_col}, 0) + 1 WHERE id = %s",
                (user_id,),
            )

        cur.execute(
            "UPDATE users SET total_game_vtx = COALESCE(total_game_vtx, 0) + %s WHERE id = %s",
            (amount, user_id),
        )

        conn.commit()
        block["vtx_earned"] = float(amount)
        block["base_amount"] = float(base_amount)
        block["multiplier"] = float(multiplier)
        block["event_type"] = event_type
        block["earned_today"] = float(earned_today + amount)
        return block
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_game_stats(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT COALESCE(game_level, 1), COALESCE(nodes_built, 0),
                      COALESCE(vaults_opened, 0), COALESCE(glyphs_solved, 0),
                      COALESCE(total_game_vtx, 0), COALESCE(vortex_balance, 0)
               FROM users WHERE id = %s""",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return {}
        return {
            "level": int(row[0]),
            "nodes_built": int(row[1]),
            "vaults_opened": int(row[2]),
            "glyphs_solved": int(row[3]),
            "total_game_vtx": float(row[4]),
            "vortex_balance": float(row[5]),
        }
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
