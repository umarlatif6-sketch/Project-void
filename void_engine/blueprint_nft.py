import os
import json
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str, fatiha_286_truncated
from void_engine.vortex_wallet import _create_block
from void_engine.adriana_scl import hash_to_sovereign_poem

logger = logging.getLogger(__name__)

TIER_CONFIG = {
    "common": {
        "label": "Common",
        "color": "#7c5cff",
        "capex_ratio": Decimal("0.6"),
        "materials_ratio": Decimal("0.3"),
        "assembly_ratio": Decimal("0.1"),
    },
    "rare": {
        "label": "Rare",
        "color": "#00bfa5",
        "capex_ratio": Decimal("0.5"),
        "materials_ratio": Decimal("0.35"),
        "assembly_ratio": Decimal("0.15"),
    },
    "legendary": {
        "label": "Legendary",
        "color": "#c9a84c",
        "capex_ratio": Decimal("0.4"),
        "materials_ratio": Decimal("0.35"),
        "assembly_ratio": Decimal("0.25"),
    },
}

INITIAL_DROP = [
    {
        "tier": "common",
        "title": "Vibe-Coder Access",
        "description": "Software suite access to the Vibe-Coding environment. Grants entry to the steganography engine, 432 Hz carrier tools, and the AI Village.",
        "total_editions": 10,
        "price_gbp": 2800,
        "price_vtx": Decimal("50"),
    },
    {
        "tier": "rare",
        "title": "Fractional Node",
        "description": "Fractional ownership of a Community Machine. Earn yield from the machine's biological output and compute cycles. Includes the Pirate Build blueprint schematics.",
        "total_editions": 5,
        "price_gbp": 66000,
        "price_vtx": Decimal("1000"),
    },
    {
        "tier": "legendary",
        "title": "Sovereign Machine",
        "description": "Full 4000-Series Sovereign Node delivered to your door. Factory-calibrated with 432 Hz resonance tuning, Sapphire Thread wiring, NVIDIA Orin, and a 1-year Sovereign Warranty.",
        "total_editions": 2,
        "price_gbp": 2500000,
        "price_vtx": Decimal("40000"),
    },
]


def _get_db():
    from void_engine.db_pool import get_db
    return get_db()


def _generate_token_hash(tier, title, edition, total):
    seed = f"BLUEPRINT|{tier}|{title}|{edition}/{total}|{datetime.now(timezone.utc).isoformat()}"
    return fatiha_286_hexdigest_from_str(seed)


def mint_token(tier, title, description, edition, total_editions, price_gbp, price_vtx, minted_by=None):
    if tier not in TIER_CONFIG:
        return {"error": f"Invalid tier: {tier}"}

    token_hash = _generate_token_hash(tier, title, edition, total_editions)
    metadata = {
        "tier_config": TIER_CONFIG[tier]["label"],
        "minted_epoch": datetime.now(timezone.utc).isoformat(),
        "edition": f"{edition}/{total_editions}",
        "phase_sig": fatiha_286_truncated(token_hash.encode("utf-8"), 16),
    }

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO blueprint_tokens
               (token_hash, tier, title, description, edition_number, total_editions,
                price_gbp, price_vtx, metadata_json, minted_by, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'available')
               RETURNING id""",
            (token_hash, tier, title, description, edition, total_editions,
             price_gbp, price_vtx, json.dumps(metadata), minted_by),
        )
        token_id = cur.fetchone()[0]
        conn.commit()
        return {
            "token_id": token_id,
            "token_hash": token_hash,
            "tier": tier,
            "title": title,
            "edition": f"{edition}/{total_editions}",
        }
    except Exception as e:
        conn.rollback()
        logger.error("Mint failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def _allocate_manufacturing_fund(cur, token_id, price_gbp, tier):
    cfg = TIER_CONFIG[tier]
    allocations = [
        ("capex", int(price_gbp * cfg["capex_ratio"])),
        ("materials", int(price_gbp * cfg["materials_ratio"])),
        ("assembly", price_gbp - int(price_gbp * cfg["capex_ratio"]) - int(price_gbp * cfg["materials_ratio"])),
    ]
    for purpose, amount in allocations:
        if amount > 0:
            cur.execute(
                """INSERT INTO manufacturing_fund (token_id, amount_gbp, purpose, status)
                   VALUES (%s, %s, %s, 'pledged')""",
                (token_id, amount, purpose),
            )


def purchase_token_vtx(token_id, buyer_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, tier, title, price_vtx, price_gbp, status FROM blueprint_tokens WHERE id = %s FOR UPDATE",
            (token_id,),
        )
        token = cur.fetchone()
        if not token:
            return {"error": "Token not found"}
        if token[5] != "available":
            return {"error": "Token is no longer available"}

        price_vtx = token[3]
        price_gbp = token[4]
        tier = token[1]

        cur.execute(
            "SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE",
            (buyer_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "User not found"}
        balance = row[0]
        if balance < price_vtx:
            return {"error": f"Insufficient VTX. Need {float(price_vtx)}, have {float(balance)}"}

        cur.execute(
            "UPDATE users SET vortex_balance = vortex_balance - %s WHERE id = %s",
            (price_vtx, buyer_id),
        )

        token_hash = fatiha_286_hexdigest_from_str(f"nft_purchase|{token_id}|{buyer_id}|vtx")
        block = _create_block(cur, "nft_purchase", buyer_id, None, price_vtx, token_hash)

        cur.execute(
            "UPDATE blueprint_tokens SET status = 'sold' WHERE id = %s",
            (token_id,),
        )
        cur.execute(
            """INSERT INTO token_ownership
               (token_id, owner_id, purchase_type, vtx_ledger_block_id)
               VALUES (%s, %s, 'vtx', %s)""",
            (token_id, buyer_id, block["block_index"]),
        )

        _allocate_manufacturing_fund(cur, token_id, price_gbp, tier)

        conn.commit()
        return {
            "success": True,
            "token_id": token_id,
            "title": token[2],
            "tier": tier,
            "spent_vtx": float(price_vtx),
            "block": block,
        }
    except Exception as e:
        conn.rollback()
        logger.error("VTX purchase failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def purchase_token_fiat(token_id, buyer_id, stripe_session_id):
    conn = _get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM token_ownership WHERE stripe_session_id = %s",
            (stripe_session_id,),
        )
        if cur.fetchone():
            return {"already_finalized": True, "token_id": token_id}

        cur.execute(
            "SELECT id, tier, title, price_gbp, status FROM blueprint_tokens WHERE id = %s FOR UPDATE",
            (token_id,),
        )
        token = cur.fetchone()
        if not token:
            return {"error": "Token not found"}
        if token[4] not in ("available", "reserved"):
            return {"error": "Token is no longer available"}

        price_gbp = token[3]
        tier = token[1]

        cur.execute(
            "UPDATE blueprint_tokens SET status = 'sold' WHERE id = %s",
            (token_id,),
        )
        cur.execute(
            """INSERT INTO token_ownership
               (token_id, owner_id, purchase_type, stripe_session_id)
               VALUES (%s, %s, 'stripe', %s)""",
            (token_id, buyer_id, stripe_session_id),
        )

        token_hash = fatiha_286_hexdigest_from_str(f"nft_purchase|{token_id}|{buyer_id}|stripe|{stripe_session_id}")
        block = _create_block(cur, "nft_purchase_fiat", None, buyer_id, Decimal(price_gbp) / Decimal(100), token_hash)

        _allocate_manufacturing_fund(cur, token_id, price_gbp, tier)

        conn.commit()
        return {
            "success": True,
            "token_id": token_id,
            "title": token[2],
            "tier": tier,
            "block": block,
        }
    except Exception as e:
        conn.rollback()
        logger.error("Fiat purchase failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def get_marketplace_listings():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, token_hash, tier, title, description, edition_number, total_editions,
                      price_gbp, price_vtx, status, minted_at
               FROM blueprint_tokens
               WHERE collection = 'genesis' OR collection IS NULL
               ORDER BY tier, edition_number"""
        )
        rows = cur.fetchall()
        listings = {"common": [], "rare": [], "legendary": []}
        for r in rows:
            token = {
                "id": r[0],
                "token_hash": r[1][:16] + "...",
                "tier": r[2],
                "title": r[3],
                "description": r[4],
                "edition_number": r[5],
                "total_editions": r[6],
                "price_gbp": r[7],
                "price_display": f"\u00a3{r[7] / 100:,.0f}",
                "price_vtx": float(r[8]),
                "status": r[9],
                "minted_at": r[10].isoformat() if r[10] else None,
                "sovereign_poem": hash_to_sovereign_poem(r[1]),
            }
            if r[2] in listings:
                listings[r[2]].append(token)
        return listings
    finally:
        conn.close()


def get_user_collection(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT bt.id, bt.token_hash, bt.tier, bt.title, bt.description,
                      bt.edition_number, bt.total_editions, bt.price_gbp, bt.price_vtx,
                      tow.purchased_at, tow.purchase_type
               FROM token_ownership tow
               JOIN blueprint_tokens bt ON bt.id = tow.token_id
               WHERE tow.owner_id = %s
               ORDER BY tow.purchased_at DESC""",
            (user_id,),
        )
        rows = cur.fetchall()
        collection = []
        for r in rows:
            collection.append({
                "id": r[0],
                "token_hash": r[1][:16] + "...",
                "tier": r[2],
                "title": r[3],
                "description": r[4],
                "edition": f"{r[5]}/{r[6]}",
                "price_display": f"\u00a3{r[7] / 100:,.0f}",
                "price_vtx": float(r[8]),
                "purchased_at": r[9].isoformat() if r[9] else None,
                "purchase_type": r[10],
            })
        return collection
    finally:
        conn.close()


def get_token_detail(token_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, token_hash, tier, title, description, edition_number, total_editions,
                      price_gbp, price_vtx, metadata_json, minted_at, status
               FROM blueprint_tokens WHERE id = %s""",
            (token_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        token = {
            "id": r[0],
            "token_hash": r[1],
            "tier": r[2],
            "title": r[3],
            "description": r[4],
            "edition_number": r[5],
            "total_editions": r[6],
            "price_gbp": r[7],
            "price_display": f"\u00a3{r[7] / 100:,.0f}",
            "price_vtx": float(r[8]),
            "metadata": json.loads(r[9]) if r[9] else {},
            "minted_at": r[10].isoformat() if r[10] else None,
            "status": r[11],
            "sovereign_poem": hash_to_sovereign_poem(r[1]),
        }

        cur.execute(
            """SELECT tow.id, tow.owner_id, u.username, tow.purchased_at, tow.purchase_type
               FROM token_ownership tow
               JOIN users u ON u.id = tow.owner_id
               WHERE tow.token_id = %s
               ORDER BY tow.purchased_at DESC""",
            (token_id,),
        )
        token["ownership_history"] = [
            {
                "owner": row[2],
                "purchased_at": row[3].isoformat() if row[3] else None,
                "purchase_type": row[4],
            }
            for row in cur.fetchall()
        ]
        return token
    finally:
        conn.close()


def get_manufacturing_fund_status():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT purpose, SUM(amount_gbp), COUNT(*)
               FROM manufacturing_fund
               GROUP BY purpose"""
        )
        breakdown = {}
        total = 0
        for row in cur.fetchall():
            amount = row[1]
            breakdown[row[0]] = {"amount_pence": int(amount), "display": f"\u00a3{int(amount) / 100:,.0f}", "count": row[2]}
            total += int(amount)

        cur.execute("SELECT COUNT(*) FROM blueprint_tokens WHERE status = 'sold'")
        tokens_sold = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM blueprint_tokens")
        tokens_total = cur.fetchone()[0]

        goal_pence = 0
        for drop in INITIAL_DROP:
            goal_pence += drop["price_gbp"] * drop["total_editions"]

        return {
            "total_raised_pence": total,
            "total_raised_display": f"\u00a3{total / 100:,.0f}",
            "goal_pence": goal_pence,
            "goal_display": f"\u00a3{goal_pence / 100:,.0f}",
            "progress_percent": round((total / goal_pence * 100), 1) if goal_pence > 0 else 0,
            "tokens_sold": tokens_sold,
            "tokens_total": tokens_total,
            "breakdown": breakdown,
        }
    finally:
        conn.close()


def post_yield_event(amount_vtx, notes, admin_id, amount_gbp=0, idempotency_key=None):
    amount = Decimal(str(amount_vtx)).quantize(Decimal("0.0001"))
    if amount <= 0:
        return {"error": "amount_vtx must be positive"}

    conn = _get_db()
    try:
        cur = conn.cursor()

        if idempotency_key:
            cur.execute(
                "SELECT id FROM yield_events WHERE idempotency_key = %s",
                (idempotency_key,),
            )
            existing = cur.fetchone()
            if existing:
                logger.info("yield_event idempotency hit: key=%s event_id=%s", idempotency_key, existing[0])
                return {"success": True, "event_id": existing[0], "already_posted": True}

        cur.execute(
            """SELECT tow.owner_id, bt.id, bt.tier
               FROM token_ownership tow
               JOIN blueprint_tokens bt ON bt.id = tow.token_id
               WHERE bt.tier IN ('rare', 'legendary')
               ORDER BY bt.tier, tow.owner_id"""
        )
        rows = cur.fetchall()
        if not rows:
            return {"error": "No Rare or Legendary token holders found"}

        total_units = Decimal("0")
        for (owner_id, token_id, tier) in rows:
            total_units += Decimal("10") if tier == "legendary" else Decimal("1")

        if total_units == 0:
            return {"error": "No eligible token holders"}

        unit_value = amount / total_units

        try:
            cur.execute(
                """INSERT INTO yield_events (amount_gbp, amount_vtx, notes, posted_by, idempotency_key)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (int(amount_gbp), amount, notes, admin_id, idempotency_key),
            )
            event_id = cur.fetchone()[0]
        except Exception as insert_exc:
            conn.rollback()
            if idempotency_key and "unique" in str(insert_exc).lower():
                cur2 = conn.cursor()
                cur2.execute("SELECT id FROM yield_events WHERE idempotency_key = %s", (idempotency_key,))
                row = cur2.fetchone()
                if row:
                    return {"success": True, "event_id": row[0], "already_posted": True}
            raise

        claims_inserted = 0
        for (owner_id, token_id, tier) in rows:
            weight = Decimal("10") if tier == "legendary" else Decimal("1")
            claim_amount = (unit_value * weight).quantize(Decimal("0.0001"))
            if claim_amount <= 0:
                continue
            cur.execute(
                """INSERT INTO yield_claims (owner_id, token_id, event_id, amount_vtx)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (owner_id, token_id, event_id) DO NOTHING""",
                (owner_id, token_id, event_id, claim_amount),
            )
            claims_inserted += 1

        conn.commit()
        return {
            "success": True,
            "event_id": event_id,
            "total_vtx": float(amount),
            "total_units": float(total_units),
            "unit_value": float(unit_value),
            "claims_inserted": claims_inserted,
        }
    except Exception as e:
        conn.rollback()
        logger.error("post_yield_event failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def get_mystery_price():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT minted_count, base_price_vtx, price_step_threshold, step_multiplier, total_supply FROM mystery_collection LIMIT 1")
        row = cur.fetchone()
        if not row:
            return {"error": "Mystery collection not initialized"}
        minted, base_price, threshold, multiplier, total_supply = row
        minted = int(minted)
        total_supply = int(total_supply)
        threshold = int(threshold)
        remaining = total_supply - minted
        sold_out = remaining <= 0
        max_step = (total_supply - 1) // threshold
        step = min(minted // threshold, max_step) if not sold_out else max_step
        price = Decimal(str(base_price)) * (Decimal(str(multiplier)) ** step)
        return {
            "minted_count": minted,
            "total_supply": total_supply,
            "remaining": remaining,
            "current_price_vtx": float(price),
            "step": step,
            "sold_out": sold_out,
            "next_step_at": (step + 1) * threshold if not sold_out and (step + 1) * threshold < total_supply else None,
        }
    finally:
        conn.close()


def buy_mystery_token(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, minted_count, base_price_vtx, price_step_threshold, step_multiplier, total_supply FROM mystery_collection LIMIT 1 FOR UPDATE")
        row = cur.fetchone()
        if not row:
            return {"error": "Mystery collection not initialized"}
        mc_id, minted, base_price, threshold, multiplier, total_supply = row
        if int(minted) >= int(total_supply):
            return {"error": "Mystery collection is sold out"}

        step = int(minted) // int(threshold)
        price = Decimal(str(base_price)) * (Decimal(str(multiplier)) ** step)

        cur.execute("SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE", (user_id,))
        bal_row = cur.fetchone()
        if not bal_row:
            return {"error": "User not found"}
        balance = bal_row[0]
        if balance < price:
            return {"error": f"Insufficient VTX. Need {float(price)}, have {float(balance)}"}

        token_hash = _generate_token_hash("mystery", "VOID Mystery", minted + 1, total_supply)
        metadata = {
            "collection": "mystery",
            "minted_epoch": datetime.now(timezone.utc).isoformat(),
            "edition": f"{minted + 1}/{total_supply}",
            "phase_sig": fatiha_286_truncated(token_hash.encode("utf-8"), 16),
        }
        cur.execute(
            """INSERT INTO blueprint_tokens
               (token_hash, tier, title, description, edition_number, total_editions,
                price_gbp, price_vtx, metadata_json, minted_by, status, collection)
               VALUES (%s, 'mystery', 'VOID Mystery', 'A sealed VOID Mystery token. Click Reveal to discover your tier.', %s, %s, 0, %s, %s, %s, 'sealed', 'mystery')
               RETURNING id""",
            (token_hash, minted + 1, total_supply, price, json.dumps(metadata), user_id),
        )
        token_id = cur.fetchone()[0]

        payload_hash = fatiha_286_hexdigest_from_str(f"mystery_buy|{token_id}|{user_id}")
        block = _create_block(cur, "mystery_buy", user_id, None, price, payload_hash)

        cur.execute("UPDATE users SET vortex_balance = vortex_balance - %s WHERE id = %s", (price, user_id))
        cur.execute("UPDATE mystery_collection SET minted_count = minted_count + 1, updated_at = NOW() WHERE id = %s", (mc_id,))

        cur.execute(
            """INSERT INTO token_ownership (token_id, owner_id, purchase_type, vtx_ledger_block_id)
               VALUES (%s, %s, 'vtx', %s)""",
            (token_id, user_id, block["block_index"]),
        )
        conn.commit()
        return {
            "success": True,
            "token_id": token_id,
            "token_hash": token_hash,
            "spent_vtx": float(price),
            "status": "sealed",
        }
    except Exception as e:
        conn.rollback()
        logger.error("Mystery buy failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def get_pending_yield(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT COALESCE(SUM(amount_vtx), 0)
               FROM yield_claims
               WHERE owner_id = %s AND claimed_at IS NULL""",
            (user_id,),
        )
        total = cur.fetchone()[0]
        return float(total)
    finally:
        conn.close()


def reveal_mystery_token(token_id, user_id):
    import random
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT bt.id, bt.token_hash, bt.tier, bt.status, tow.owner_id
               FROM blueprint_tokens bt
               JOIN token_ownership tow ON tow.token_id = bt.id
               WHERE bt.id = %s AND tow.owner_id = %s AND bt.collection = 'mystery'
               FOR UPDATE""",
            (token_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "Token not found or not owned by you"}
        _, token_hash, current_tier, status, _ = row
        if status == "revealed":
            return {"error": "Token already revealed"}
        if status not in ("sealed",):
            return {"error": f"Cannot reveal token with status '{status}'"}

        reveal_seed = fatiha_286_hexdigest_from_str(f"reveal|{token_hash}|{datetime.now(timezone.utc).isoformat()}")

        if current_tier == "mystery":
            rng = random.Random(int(reveal_seed[:8], 16))
            roll = rng.random()
            if roll < 0.70:
                tier = "common"
            elif roll < 0.95:
                tier = "rare"
            else:
                tier = "legendary"
        else:
            tier = current_tier

        poem = hash_to_sovereign_poem(reveal_seed)
        revealed_at = datetime.now(timezone.utc)

        cur.execute(
            "UPDATE blueprint_tokens SET tier = %s, status = 'revealed', token_hash = %s, revealed_at = %s WHERE id = %s",
            (tier, reveal_seed, revealed_at, token_id),
        )
        conn.commit()
        return {
            "success": True,
            "token_id": token_id,
            "tier": tier,
            "reveal_hash": reveal_seed,
            "revealed_at": revealed_at.isoformat(),
            "sovereign_poem": poem,
        }
    except Exception as e:
        conn.rollback()
        logger.error("Reveal failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def claim_yield(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, amount_vtx
               FROM yield_claims
               WHERE owner_id = %s AND claimed_at IS NULL
               FOR UPDATE""",
            (user_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return {"error": "No pending yield to claim"}

        total = sum(Decimal(str(r[1])) for r in rows).quantize(Decimal("0.0001"))
        if total <= 0:
            return {"error": "No pending yield to claim"}

        from void_engine.vortex_wallet import _create_block
        payload_hash = fatiha_286_hexdigest_from_str(f"yield_claim|{user_id}|{datetime.now(timezone.utc).isoformat()}")
        block = _create_block(cur, "yield_claim", None, user_id, total, payload_hash)

        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (total, user_id),
        )

        claim_ids = [r[0] for r in rows]
        cur.execute(
            "UPDATE yield_claims SET claimed_at = NOW() WHERE id = ANY(%s)",
            (claim_ids,),
        )

        conn.commit()
        return {
            "success": True,
            "claimed_vtx": float(total),
            "block": block,
        }
    except Exception as e:
        conn.rollback()
        logger.error("claim_yield failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def free_daily_mint(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT last_free_mint_at FROM users WHERE id = %s FOR UPDATE", (user_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "User not found"}
        last_mint = row[0]
        now = datetime.now(timezone.utc)
        if last_mint is not None:
            if last_mint.tzinfo is None:
                last_mint = last_mint.replace(tzinfo=timezone.utc)
            elapsed = (now - last_mint).total_seconds()
            cooldown = 86400
            if elapsed < cooldown:
                return {"error": "cooldown", "seconds_remaining": int(cooldown - elapsed)}

        cur.execute("SELECT minted_count, total_supply FROM mystery_collection LIMIT 1 FOR UPDATE")
        mc_row = cur.fetchone()
        if not mc_row:
            return {"error": "Mystery collection not initialized"}
        minted, total_supply = mc_row
        if int(minted) >= int(total_supply):
            return {"error": "Mystery collection is sold out"}

        token_hash = _generate_token_hash("common", "VOID Mystery Free", minted + 1, total_supply)
        metadata = {
            "collection": "mystery",
            "free_mint": True,
            "minted_epoch": now.isoformat(),
            "edition": f"{minted + 1}/{total_supply}",
            "phase_sig": fatiha_286_truncated(token_hash.encode("utf-8"), 16),
        }
        cur.execute(
            """INSERT INTO blueprint_tokens
               (token_hash, tier, title, description, edition_number, total_editions,
                price_gbp, price_vtx, metadata_json, minted_by, status, collection)
               VALUES (%s, 'common', 'VOID Mystery', 'A sealed VOID Mystery token (free daily mint).', %s, %s, 0, 0, %s, %s, 'sealed', 'mystery')
               RETURNING id""",
            (token_hash, minted + 1, total_supply, json.dumps(metadata), user_id),
        )
        token_id = cur.fetchone()[0]

        cur.execute("UPDATE mystery_collection SET minted_count = minted_count + 1, updated_at = NOW()")
        cur.execute("UPDATE users SET last_free_mint_at = %s WHERE id = %s", (now, user_id))

        cur.execute(
            """INSERT INTO token_ownership (token_id, owner_id, purchase_type)
               VALUES (%s, %s, 'free')""",
            (token_id, user_id),
        )
        conn.commit()
        return {
            "success": True,
            "token_id": token_id,
            "token_hash": token_hash,
            "tier": "common",
            "status": "sealed",
        }
    except Exception as e:
        conn.rollback()
        logger.error("Free mint failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def merge_tokens(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT bt.id FROM blueprint_tokens bt
               JOIN token_ownership tow ON tow.token_id = bt.id
               WHERE tow.owner_id = %s
                 AND bt.collection = 'mystery'
                 AND bt.tier = 'common'
                 AND bt.status IN ('sealed', 'revealed')
               ORDER BY tow.purchased_at ASC
               FOR UPDATE OF bt""",
            (user_id,),
        )
        eligible = [r[0] for r in cur.fetchall()]
        if len(eligible) < 30:
            return {"error": f"Need 30 eligible Common tokens to merge. You have {len(eligible)}."}

        burn_ids = eligible[:30]
        cur.execute(
            "UPDATE blueprint_tokens SET status = 'merged' WHERE id = ANY(%s)",
            (burn_ids,),
        )

        cur.execute("SELECT minted_count, total_supply FROM mystery_collection LIMIT 1 FOR UPDATE")
        mc_row = cur.fetchone()
        if not mc_row:
            return {"error": "Mystery collection not initialized"}
        minted, total_supply = mc_row
        if int(minted) >= int(total_supply):
            return {"error": "Mystery collection is sold out — cannot mint merge reward"}

        token_hash = _generate_token_hash("rare", "VOID Mystery Merge Reward", minted + 1, total_supply)
        now = datetime.now(timezone.utc)
        metadata = {
            "collection": "mystery",
            "merge_reward": True,
            "merged_count": 30,
            "minted_epoch": now.isoformat(),
            "edition": f"{minted + 1}/{total_supply}",
            "phase_sig": fatiha_286_truncated(token_hash.encode("utf-8"), 16),
        }
        cur.execute(
            """INSERT INTO blueprint_tokens
               (token_hash, tier, title, description, edition_number, total_editions,
                price_gbp, price_vtx, metadata_json, minted_by, status, collection)
               VALUES (%s, 'rare', 'VOID Mystery', 'A Rare VOID Mystery token earned by merging 30 Common tokens.', %s, %s, 0, 0, %s, %s, 'sealed', 'mystery')
               RETURNING id""",
            (token_hash, minted + 1, total_supply, json.dumps(metadata), user_id),
        )
        new_token_id = cur.fetchone()[0]

        cur.execute("UPDATE mystery_collection SET minted_count = minted_count + 1, updated_at = NOW()")

        cur.execute(
            """INSERT INTO token_ownership (token_id, owner_id, purchase_type)
               VALUES (%s, %s, 'merge')""",
            (new_token_id, user_id),
        )

        bonus_vtx = Decimal("200")
        payload_hash = fatiha_286_hexdigest_from_str(f"merge_bonus|{user_id}|{new_token_id}|{now.isoformat()}")
        block = _create_block(cur, "merge_bonus", None, user_id, bonus_vtx, payload_hash)
        cur.execute(
            "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) + %s WHERE id = %s",
            (bonus_vtx, user_id),
        )

        conn.commit()
        return {
            "success": True,
            "burned": 30,
            "new_token_id": new_token_id,
            "tier": "rare",
            "status": "sealed",
            "vtx_bonus": float(bonus_vtx),
            "block": block,
        }
    except Exception as e:
        conn.rollback()
        logger.error("Merge failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def get_yield_events(limit=20):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT ye.id, ye.amount_gbp, ye.amount_vtx, ye.notes, ye.posted_at, u.username
               FROM yield_events ye
               LEFT JOIN users u ON u.id = ye.posted_by
               ORDER BY ye.posted_at DESC LIMIT %s""",
            (limit,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "amount_gbp_display": f"\u00a3{r[1] / 100:.2f}" if r[1] else "\u00a30.00",
                "amount_vtx": float(r[2]),
                "notes": r[3],
                "posted_at": r[4].strftime("%Y-%m-%d %H:%M") if r[4] else "",
                "posted_by": r[5] or "admin",
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_mystery_collection(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT bt.id, bt.token_hash, bt.tier, bt.title, bt.status,
                      bt.edition_number, bt.total_editions, tow.purchased_at, tow.purchase_type
               FROM token_ownership tow
               JOIN blueprint_tokens bt ON bt.id = tow.token_id
               WHERE tow.owner_id = %s AND bt.collection = 'mystery'
               ORDER BY tow.purchased_at DESC""",
            (user_id,),
        )
        rows = cur.fetchall()
        tokens = []
        for r in rows:
            token_id, token_hash, tier, title, status, edition_num, total_editions, purchased_at, purchase_type = r
            poem = None
            if status == "revealed":
                poem = hash_to_sovereign_poem(token_hash)
            tokens.append({
                "id": token_id,
                "token_hash": token_hash[:16] + "...",
                "tier": tier,
                "title": title,
                "status": status,
                "edition": f"{edition_num}/{total_editions}",
                "purchased_at": purchased_at.isoformat() if purchased_at else None,
                "purchase_type": purchase_type,
                "sovereign_poem": poem,
            })

        cur.execute("SELECT last_free_mint_at FROM users WHERE id = %s", (user_id,))
        user_row = cur.fetchone()
        seconds_remaining = 0
        if user_row and user_row[0]:
            last_free_mint_at = user_row[0]
            if last_free_mint_at.tzinfo is None:
                last_free_mint_at = last_free_mint_at.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - last_free_mint_at).total_seconds()
            seconds_remaining = max(0, int(86400 - elapsed))

        eligible_common = sum(1 for t in tokens if t["tier"] == "common" and t["status"] in ("sealed", "revealed"))

        return {
            "tokens": tokens,
            "seconds_remaining": seconds_remaining,
            "eligible_common_count": eligible_common,
        }
    finally:
        conn.close()


def seed_initial_collection():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM blueprint_tokens")
        if cur.fetchone()[0] > 0:
            logger.info("Blueprint tokens already seeded, skipping")
            return

        for drop in INITIAL_DROP:
            for edition in range(1, drop["total_editions"] + 1):
                token_hash = _generate_token_hash(drop["tier"], drop["title"], edition, drop["total_editions"])
                metadata = {
                    "tier_config": TIER_CONFIG[drop["tier"]]["label"],
                    "minted_epoch": datetime.now(timezone.utc).isoformat(),
                    "edition": f"{edition}/{drop['total_editions']}",
                    "drop": "genesis",
                    "phase_sig": fatiha_286_truncated(token_hash.encode("utf-8"), 16),
                }
                cur.execute(
                    """INSERT INTO blueprint_tokens
                       (token_hash, tier, title, description, edition_number, total_editions,
                        price_gbp, price_vtx, metadata_json, status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'available')""",
                    (token_hash, drop["tier"], drop["title"], drop["description"],
                     edition, drop["total_editions"], drop["price_gbp"], drop["price_vtx"],
                     json.dumps(metadata)),
                )
        conn.commit()
        logger.info("Seeded initial Blueprint Token collection: %d tokens",
                     sum(d["total_editions"] for d in INITIAL_DROP))
    except Exception:
        conn.rollback()
        logger.exception("Failed to seed Blueprint Tokens")
    finally:
        conn.close()


ROYALTY_RATE = Decimal("0.05")

TIER_TO_ACCESS = {
    "common": "journalist",
    "rare": "sovereign",
    "legendary": "sovereign",
}


def list_token_for_sale(token_id, seller_id, price_vtx, price_gbp_pence=None):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM token_ownership WHERE token_id = %s AND owner_id = %s",
            (token_id, seller_id),
        )
        if not cur.fetchone():
            return {"error": "You do not own this token"}

        now = datetime.now(timezone.utc)
        cur.execute(
            "SELECT id FROM token_rentals WHERE token_id = %s AND status IN ('offered', 'active') AND (ends_at IS NULL OR ends_at > %s)",
            (token_id, now),
        )
        if cur.fetchone():
            return {"error": "Cannot list a token that has an active or offered rental"}

        cur.execute(
            "UPDATE token_rentals SET status = 'ended' WHERE token_id = %s AND status = 'active' AND ends_at <= %s",
            (token_id, now),
        )

        price_vtx = Decimal(str(price_vtx)).quantize(Decimal("0.0001"))
        if price_vtx <= 0:
            return {"error": "Price must be greater than zero"}

        cur.execute(
            """INSERT INTO token_listings (token_id, seller_id, price_vtx, price_gbp_pence, status)
               VALUES (%s, %s, %s, %s, 'active')
               ON CONFLICT (token_id) DO UPDATE
               SET seller_id = EXCLUDED.seller_id,
                   price_vtx = EXCLUDED.price_vtx,
                   price_gbp_pence = EXCLUDED.price_gbp_pence,
                   listed_at = NOW(),
                   status = 'active'
               RETURNING id""",
            (token_id, seller_id, price_vtx, price_gbp_pence),
        )
        listing_id = cur.fetchone()[0]
        conn.commit()
        return {"success": True, "listing_id": listing_id, "token_id": token_id, "price_vtx": float(price_vtx)}
    except Exception as e:
        conn.rollback()
        logger.error("list_token_for_sale failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def unlist_token(token_id, seller_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE token_listings SET status = 'cancelled' WHERE token_id = %s AND seller_id = %s AND status = 'active' RETURNING id",
            (token_id, seller_id),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "No active listing found for this token"}
        conn.commit()
        return {"success": True, "token_id": token_id}
    except Exception as e:
        conn.rollback()
        logger.error("unlist_token failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def purchase_secondary(token_id, buyer_id):
    conn = _get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            """SELECT tl.id, tl.seller_id, tl.price_vtx, bt.tier, bt.title
               FROM token_listings tl
               JOIN blueprint_tokens bt ON bt.id = tl.token_id
               WHERE tl.token_id = %s AND tl.status = 'active'
               FOR UPDATE""",
            (token_id,),
        )
        listing = cur.fetchone()
        if not listing:
            return {"error": "No active listing found for this token"}

        listing_id, seller_id, price_vtx, tier, title = listing

        if seller_id == buyer_id:
            return {"error": "You cannot buy your own listing"}

        cur.execute(
            "SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE",
            (buyer_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "Buyer not found"}
        balance = row[0]
        if balance < price_vtx:
            return {"error": f"Insufficient VTX. Need {float(price_vtx)}, have {float(balance)}"}

        cur.execute("SELECT id FROM users WHERE id = %s FOR UPDATE", (seller_id,))
        if not cur.fetchone():
            return {"error": "Seller not found"}

        royalty = (price_vtx * ROYALTY_RATE).quantize(Decimal("0.0001"))
        seller_receives = price_vtx - royalty

        cur.execute(
            "UPDATE users SET vortex_balance = vortex_balance - %s WHERE id = %s",
            (price_vtx, buyer_id),
        )
        cur.execute(
            "UPDATE users SET vortex_balance = vortex_balance + %s WHERE id = %s",
            (seller_receives, seller_id),
        )

        token_hash = fatiha_286_hexdigest_from_str(f"secondary_sale|{token_id}|{buyer_id}|{seller_id}|{datetime.now(timezone.utc).isoformat()}")
        block_buyer = _create_block(cur, "secondary_purchase", buyer_id, seller_id, price_vtx, token_hash)

        royalty_hash = fatiha_286_hexdigest_from_str(f"secondary_royalty|{token_id}|{buyer_id}|{royalty}|{datetime.now(timezone.utc).isoformat()}")
        _create_block(cur, "secondary_royalty", buyer_id, None, royalty, royalty_hash)

        cur.execute(
            "UPDATE token_ownership SET owner_id = %s, purchased_at = NOW(), purchase_type = 'vtx', transfer_from_id = %s WHERE token_id = %s AND owner_id = %s",
            (buyer_id, seller_id, token_id, seller_id),
        )

        cur.execute(
            "UPDATE token_listings SET status = 'sold' WHERE id = %s",
            (listing_id,),
        )

        cur.execute(
            """INSERT INTO manufacturing_fund (token_id, amount_gbp, purpose, status)
               VALUES (%s, %s, 'capex', 'pledged')""",
            (token_id, int(royalty * 100)),
        )

        conn.commit()
        return {
            "success": True,
            "token_id": token_id,
            "title": title,
            "tier": tier,
            "spent_vtx": float(price_vtx),
            "seller_received_vtx": float(seller_receives),
            "royalty_vtx": float(royalty),
            "block": block_buyer,
        }
    except Exception as e:
        conn.rollback()
        logger.error("purchase_secondary failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def offer_token_for_rent(token_id, owner_id, vtx_per_day, max_days=30):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM token_ownership WHERE token_id = %s AND owner_id = %s",
            (token_id, owner_id),
        )
        if not cur.fetchone():
            return {"error": "You do not own this token"}

        cur.execute(
            "SELECT id FROM token_listings WHERE token_id = %s AND status = 'active'",
            (token_id,),
        )
        if cur.fetchone():
            return {"error": "Cannot offer a listed-for-sale token for rent. Remove the listing first."}

        now = datetime.now(timezone.utc)
        cur.execute(
            "UPDATE token_rentals SET status = 'ended' WHERE token_id = %s AND status = 'active' AND ends_at <= %s",
            (token_id, now),
        )

        cur.execute(
            "SELECT id FROM token_rentals WHERE token_id = %s AND status IN ('offered', 'active') AND (ends_at IS NULL OR ends_at > %s)",
            (token_id, now),
        )
        if cur.fetchone():
            return {"error": "This token already has an active or offered rental"}

        vtx_per_day = Decimal(str(vtx_per_day)).quantize(Decimal("0.0001"))
        if vtx_per_day <= 0:
            return {"error": "Daily rate must be greater than zero"}
        max_days = int(max_days)
        if max_days < 1 or max_days > 365:
            return {"error": "max_days must be between 1 and 365"}

        cur.execute(
            "SELECT tier FROM blueprint_tokens WHERE id = %s",
            (token_id,),
        )
        row = cur.fetchone()
        token_tier = row[0] if row else "common"
        access_tier = TIER_TO_ACCESS.get(token_tier, "journalist")

        cur.execute(
            """INSERT INTO token_rentals (token_id, owner_id, vtx_per_day, max_days, status, access_tier)
               VALUES (%s, %s, %s, %s, 'offered', %s)
               RETURNING id""",
            (token_id, owner_id, vtx_per_day, max_days, access_tier),
        )
        rental_id = cur.fetchone()[0]
        conn.commit()
        return {"success": True, "rental_id": rental_id, "token_id": token_id, "vtx_per_day": float(vtx_per_day), "max_days": max_days, "access_tier": access_tier}
    except Exception as e:
        conn.rollback()
        logger.error("offer_token_for_rent failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def book_rental(rental_id, renter_id, days):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT tr.id, tr.token_id, tr.owner_id, tr.vtx_per_day, tr.max_days, tr.status, bt.tier, tr.access_tier
               FROM token_rentals tr
               JOIN blueprint_tokens bt ON bt.id = tr.token_id
               WHERE tr.id = %s AND tr.status = 'offered'
               FOR UPDATE""",
            (rental_id,),
        )
        rental = cur.fetchone()
        if not rental:
            return {"error": "Rental offer not found or not available"}

        _, token_id, owner_id, vtx_per_day, max_days, _, tier, stored_access_tier = rental
        access_tier = stored_access_tier if stored_access_tier else TIER_TO_ACCESS.get(tier, "journalist")

        if owner_id == renter_id:
            return {"error": "You cannot rent your own token"}

        days = int(days)
        if days < 1 or days > max_days:
            return {"error": f"Days must be between 1 and {max_days}"}

        total_cost = (vtx_per_day * Decimal(days)).quantize(Decimal("0.0001"))

        cur.execute(
            "SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE",
            (renter_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "Renter not found"}
        balance = row[0]
        if balance < total_cost:
            return {"error": f"Insufficient VTX. Need {float(total_cost)}, have {float(balance)}"}

        cur.execute(
            "UPDATE users SET vortex_balance = vortex_balance - %s WHERE id = %s",
            (total_cost, renter_id),
        )
        cur.execute(
            "UPDATE users SET vortex_balance = vortex_balance + %s WHERE id = %s",
            (total_cost, owner_id),
        )

        now = datetime.now(timezone.utc)
        ends_at = now + timedelta(days=days)

        payload_hash = fatiha_286_hexdigest_from_str(f"rental_book|{rental_id}|{renter_id}|{days}|{now.isoformat()}")
        _create_block(cur, "rental_payment", renter_id, owner_id, total_cost, payload_hash)

        cur.execute(
            """UPDATE token_rentals
               SET renter_id = %s, starts_at = %s, ends_at = %s, status = 'active', total_vtx_paid = %s, access_tier = %s
               WHERE id = %s""",
            (renter_id, now, ends_at, total_cost, access_tier, rental_id),
        )

        conn.commit()
        return {
            "success": True,
            "rental_id": rental_id,
            "token_id": token_id,
            "tier": tier,
            "access_tier": access_tier,
            "days": days,
            "total_vtx_paid": float(total_cost),
            "starts_at": now.isoformat(),
            "ends_at": ends_at.isoformat(),
        }
    except Exception as e:
        conn.rollback()
        logger.error("book_rental failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def end_rental(rental_id, requesting_user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT tr.id, tr.token_id, tr.owner_id, tr.renter_id, tr.vtx_per_day,
                      tr.starts_at, tr.ends_at, tr.total_vtx_paid, tr.status
               FROM token_rentals tr
               WHERE tr.id = %s AND tr.status = 'active'
               FOR UPDATE""",
            (rental_id,),
        )
        rental = cur.fetchone()
        if not rental:
            return {"error": "Active rental not found"}

        _, token_id, owner_id, renter_id, vtx_per_day, starts_at, ends_at, total_vtx_paid, _ = rental

        if requesting_user_id not in (owner_id, renter_id):
            return {"error": "Only the token owner or renter can end this rental"}

        now = datetime.now(timezone.utc)
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=timezone.utc)
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)

        if now >= ends_at:
            cur.execute(
                "UPDATE token_rentals SET status = 'ended' WHERE id = %s",
                (rental_id,),
            )
            conn.commit()
            return {"success": True, "rental_id": rental_id, "refund_vtx": 0.0, "message": "Rental period already complete"}

        elapsed_days = (now - starts_at).total_seconds() / 86400
        days_used = Decimal(str(elapsed_days)).quantize(Decimal("0.0001"))
        vtx_used = (vtx_per_day * days_used).quantize(Decimal("0.0001"))
        vtx_refund = (total_vtx_paid - vtx_used).quantize(Decimal("0.0001"))
        if vtx_refund < 0:
            vtx_refund = Decimal("0")

        if vtx_refund > 0:
            cur.execute(
                "SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE",
                (owner_id,),
            )
            owner_balance = cur.fetchone()[0]
            actual_refund = min(vtx_refund, owner_balance)

            if actual_refund > 0:
                cur.execute(
                    "UPDATE users SET vortex_balance = vortex_balance - %s WHERE id = %s",
                    (actual_refund, owner_id),
                )
                cur.execute(
                    "UPDATE users SET vortex_balance = vortex_balance + %s WHERE id = %s",
                    (actual_refund, renter_id),
                )
                refund_hash = fatiha_286_hexdigest_from_str(f"rental_refund|{rental_id}|{renter_id}|{actual_refund}|{now.isoformat()}")
                _create_block(cur, "rental_refund", owner_id, renter_id, actual_refund, refund_hash)
                vtx_refund = actual_refund

        cur.execute(
            "UPDATE token_rentals SET status = 'ended', ends_at = %s WHERE id = %s",
            (now, rental_id),
        )
        conn.commit()
        return {
            "success": True,
            "rental_id": rental_id,
            "token_id": token_id,
            "refund_vtx": float(vtx_refund),
        }
    except Exception as e:
        conn.rollback()
        logger.error("end_rental failed: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def get_secondary_listings():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT tl.id, tl.token_id, tl.seller_id, tl.price_vtx, tl.price_gbp_pence, tl.listed_at,
                      bt.token_hash, bt.tier, bt.title, bt.description, bt.edition_number, bt.total_editions,
                      u.username as seller_username
               FROM token_listings tl
               JOIN blueprint_tokens bt ON bt.id = tl.token_id
               JOIN users u ON u.id = tl.seller_id
               WHERE tl.status = 'active'
               ORDER BY tl.listed_at DESC""",
        )
        rows = cur.fetchall()
        listings = []
        for r in rows:
            listings.append({
                "listing_id": r[0],
                "token_id": r[1],
                "seller_id": r[2],
                "price_vtx": float(r[3]),
                "price_gbp_pence": r[4],
                "listed_at": r[5].isoformat() if r[5] else None,
                "token_hash": r[6][:16] + "...",
                "tier": r[7],
                "title": r[8],
                "description": r[9],
                "edition_number": r[10],
                "total_editions": r[11],
                "seller_username": r[12],
                "sovereign_poem": hash_to_sovereign_poem(r[6]),
            })
        return listings
    finally:
        conn.close()


def get_rental_offers():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT tr.id, tr.token_id, tr.owner_id, tr.vtx_per_day, tr.max_days, tr.created_at,
                      bt.token_hash, bt.tier, bt.title, bt.edition_number, bt.total_editions,
                      u.username as owner_username, tr.access_tier
               FROM token_rentals tr
               JOIN blueprint_tokens bt ON bt.id = tr.token_id
               JOIN users u ON u.id = tr.owner_id
               WHERE tr.status = 'offered'
               ORDER BY tr.created_at DESC""",
        )
        rows = cur.fetchall()
        offers = []
        for r in rows:
            stored_access_tier = r[12]
            access_tier = stored_access_tier if stored_access_tier else TIER_TO_ACCESS.get(r[7], "journalist")
            offers.append({
                "rental_id": r[0],
                "token_id": r[1],
                "owner_id": r[2],
                "vtx_per_day": float(r[3]),
                "max_days": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
                "token_hash": r[6][:16] + "...",
                "tier": r[7],
                "title": r[8],
                "edition_number": r[9],
                "total_editions": r[10],
                "owner_username": r[11],
                "access_tier": access_tier,
            })
        return offers
    finally:
        conn.close()


def get_user_collection_extended(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT bt.id, bt.token_hash, bt.tier, bt.title, bt.description,
                      bt.edition_number, bt.total_editions, bt.price_gbp, bt.price_vtx,
                      tow.purchased_at, tow.purchase_type,
                      tl.id as listing_id, tl.price_vtx as listing_price_vtx, tl.status as listing_status,
                      tr.id as rental_id, tr.vtx_per_day, tr.status as rental_status,
                      tr.renter_id, tr.ends_at as rental_ends_at
               FROM token_ownership tow
               JOIN blueprint_tokens bt ON bt.id = tow.token_id
               LEFT JOIN token_listings tl ON tl.token_id = bt.id AND tl.status = 'active'
               LEFT JOIN token_rentals tr ON tr.token_id = bt.id AND tr.status IN ('offered', 'active')
               WHERE tow.owner_id = %s
               ORDER BY tow.purchased_at DESC""",
            (user_id,),
        )
        rows = cur.fetchall()
        collection = []
        for r in rows:
            collection.append({
                "id": r[0],
                "token_hash": r[1][:16] + "...",
                "tier": r[2],
                "title": r[3],
                "description": r[4],
                "edition": f"{r[5]}/{r[6]}",
                "price_display": f"\u00a3{r[7] / 100:,.0f}",
                "price_vtx": float(r[8]),
                "purchased_at": r[9].isoformat() if r[9] else None,
                "purchase_type": r[10],
                "listing_id": r[11],
                "listing_price_vtx": float(r[12]) if r[12] is not None else None,
                "listing_active": r[13] == "active" if r[13] else False,
                "rental_id": r[14],
                "rental_vtx_per_day": float(r[15]) if r[15] is not None else None,
                "rental_status": r[16],
                "rental_renter_id": r[17],
                "rental_ends_at": r[18].isoformat() if r[18] else None,
            })
        return collection

    finally:
        conn.close()


def get_active_rental_for_user(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc)
        cur.execute(
            """SELECT tr.id, tr.token_id, bt.tier, tr.ends_at, tr.access_tier
               FROM token_rentals tr
               JOIN blueprint_tokens bt ON bt.id = tr.token_id
               WHERE tr.renter_id = %s AND tr.status = 'active' AND tr.ends_at > %s
               ORDER BY tr.ends_at DESC
               LIMIT 1""",
            (user_id, now),
        )
        row = cur.fetchone()
        if not row:
            return None
        stored_access_tier = row[4]
        access_tier = stored_access_tier if stored_access_tier else TIER_TO_ACCESS.get(row[2], "journalist")
        return {
            "rental_id": row[0],
            "token_id": row[1],
            "tier": row[2],
            "access_tier": access_tier,
            "ends_at": row[3].isoformat() if row[3] else None,
        }
    finally:
        conn.close()


GENESIS_10_DROP = {
    "tier": "legendary",
    "title": "Sovereign Node Blueprint",
    "description": (
        "Genesis 10 — the first 10 biological mesh nodes. Grants the right to participate "
        "in the VOID biological mesh network, earn PEACE tokens for verified environmental "
        "actions (composting, aquaponics), and be publicly listed as a founding member of "
        "the sovereign biological economy."
    ),
    "total_editions": 10,
    "price_gbp": 250000,
    "price_vtx": Decimal("5000"),
    "collection": "genesis_10",
}


def seed_genesis_10():
    conn = _get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM blueprint_tokens WHERE collection = 'genesis_10'"
        )
        if cur.fetchone()[0] > 0:
            logger.info("Genesis 10 tokens already seeded, skipping")
            return

        drop = GENESIS_10_DROP
        for edition in range(1, drop["total_editions"] + 1):
            token_hash = _generate_token_hash(drop["tier"], drop["title"], edition, drop["total_editions"])
            metadata = {
                "tier_config": TIER_CONFIG[drop["tier"]]["label"],
                "minted_epoch": datetime.now(timezone.utc).isoformat(),
                "edition": f"{edition}/{drop['total_editions']}",
                "drop": "genesis_10",
                "collection": "genesis_10",
                "phase_sig": fatiha_286_truncated(token_hash.encode("utf-8"), 16),
                "biological_mesh": True,
                "peace_eligible": True,
            }
            cur.execute(
                """INSERT INTO blueprint_tokens
                   (token_hash, tier, title, description, edition_number, total_editions,
                    price_gbp, price_vtx, metadata_json, status, collection)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'available', 'genesis_10')""",
                (token_hash, drop["tier"], drop["title"], drop["description"],
                 edition, drop["total_editions"], drop["price_gbp"], drop["price_vtx"],
                 json.dumps(metadata)),
            )
        conn.commit()
        logger.info("Seeded Genesis 10 Blueprint Tokens (10 editions)")
    except Exception:
        conn.rollback()
        logger.exception("Failed to seed Genesis 10 tokens")
    finally:
        conn.close()


def get_genesis_10_listings():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, token_hash, tier, title, description, edition_number, total_editions,
                      price_gbp, price_vtx, status, minted_at
               FROM blueprint_tokens
               WHERE collection = 'genesis_10'
               ORDER BY edition_number"""
        )
        rows = cur.fetchall()
        tokens = []
        for r in rows:
            tokens.append({
                "id": r[0],
                "token_hash": r[1][:16] + "...",
                "tier": r[2],
                "title": r[3],
                "description": r[4],
                "edition_number": r[5],
                "total_editions": r[6],
                "price_gbp": r[7],
                "price_display": f"\u00a3{r[7] / 100:,.0f}",
                "price_vtx": float(r[8]),
                "status": r[9],
                "minted_at": r[10].isoformat() if r[10] else None,
                "sovereign_poem": hash_to_sovereign_poem(r[1]),
            })
        available = sum(1 for t in tokens if t["status"] == "available")
        return {
            "tokens": tokens,
            "total": len(tokens),
            "available": available,
            "sold": len(tokens) - available,
        }
    finally:
        conn.close()


def regenerate_leaders_md():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT bt.edition_number, u.username, tow.purchased_at,
                      bt.token_hash, u.id
               FROM token_ownership tow
               JOIN blueprint_tokens bt ON bt.id = tow.token_id
               JOIN users u ON u.id = tow.owner_id
               WHERE bt.collection = 'genesis_10'
               ORDER BY tow.purchased_at ASC"""
        )
        rows = cur.fetchall()

        user_ids = [r[4] for r in rows] if rows else []
        node_id_map = {}
        if user_ids:
            cur.execute(
                """SELECT DISTINCT ON (user_id) user_id, node_id
                   FROM genesis_oracle_events
                   WHERE user_id = ANY(%s)
                   ORDER BY user_id, submitted_at DESC""",
                (user_ids,),
            )
            for uid, nid in cur.fetchall():
                node_id_map[uid] = nid

        lines = [
            "# GENESIS 10 — Sovereign Node Registry",
            "",
            "> The first 10 biological mesh nodes. Each entry below is a verified Genesis 10 holder —",
            "> a founding participant in the PROJECT VOID biological economy.",
            "",
            "| # | Node ID | Registration |",
            "|---|---------|--------------|",
        ]

        if rows:
            for i, r in enumerate(rows, 1):
                edition = r[0]
                username = r[1] or "anonymous"
                registered = r[2].strftime("%Y-%m-%d") if r[2] else "—"
                user_id = r[4]
                node_id = node_id_map.get(user_id) or f"VOID-G10-{edition:02d}"
                lines.append(f"| {i} | {node_id} ({username}) | {registered} |")
        else:
            lines.append("| — | *Awaiting first claim...* | — |")

        lines += [
            "",
            "---",
            "",
            "*Registry auto-updates as Genesis 10 Blueprint NFTs are claimed.*  ",
            "*Verified by the Al-Jabr 286 Sovereign Hash chain.*",
        ]

        md_content = "\n".join(lines) + "\n"
        with open("GENESIS_LEADERS.md", "w") as f:
            f.write(md_content)
        logger.info("GENESIS_LEADERS.md regenerated (%d holders)", len(rows))
    except Exception as e:
        logger.error("regenerate_leaders_md failed: %s", e)
    finally:
        conn.close()
