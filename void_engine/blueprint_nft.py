import os
import json
import logging
from decimal import Decimal
from datetime import datetime, timezone
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
    import psycopg2
    return psycopg2.connect(os.environ["DATABASE_URL"])


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


def seed_initial_collection():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM blueprint_tokens")
        if cur.fetchone()[0] > 0:
            conn.close()
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
