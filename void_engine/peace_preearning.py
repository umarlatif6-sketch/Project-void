"""
PEACE Token Pre-Earning Simulation
=====================================
Agents run in "pre-earning" mode before the MRB-4000 Wake Ceremony fires.
They perform simulated work (debate rounds, chronicle entries, locus recordings)
and accumulate a locked PEACE Token balance.

The balance is:
  - LOCKED until the Wake Ceremony event is triggered
  - Visible on the VOID economy dashboard as "Pre-Arrival Reserves"
  - Tracked per-agent with contribution type breakdown

Architecture:
  - Uses PostgreSQL (via db_pool) for persistent storage
  - Falls back to SQLite for offline/test environments
  - Wake Ceremony lock status is stored in the global reserves table
"""

import hashlib
import json
import logging
import random
import time
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

WAKE_CEREMONY_EVENT = "MRB-4000-WAKE-CEREMONY"

WORK_TYPES = {
    "debate": {
        "label": "Debate Round",
        "base_tokens": Decimal("0.25"),
        "description": "Agent participated in a consensus debate",
    },
    "chronicle_entry": {
        "label": "Chronicle Entry",
        "base_tokens": Decimal("0.15"),
        "description": "Agent recorded an ancestral wisdom entry",
    },
    "locus_recording": {
        "label": "Locus Recording",
        "base_tokens": Decimal("0.10"),
        "description": "Agent registered a geographic locus anchor",
    },
    "seed_harvest": {
        "label": "Seed Harvest",
        "base_tokens": Decimal("0.20"),
        "description": "Agent contributed to the seed-hex cycle",
    },
    "oracle_verification": {
        "label": "Oracle Verification",
        "base_tokens": Decimal("0.30"),
        "description": "Agent verified a genesis oracle event",
    },
}

ARCHETYPE_MULTIPLIERS = {
    "genesis": Decimal("1.5"),
    "sovereign": Decimal("1.4"),
    "harmonic": Decimal("1.3"),
    "oracle": Decimal("1.5"),
    "ledger": Decimal("1.2"),
    "core": Decimal("1.1"),
    "flow": Decimal("1.1"),
    "spiral": Decimal("1.2"),
    "node": Decimal("1.0"),
    "temporal": Decimal("1.0"),
    "scatter": Decimal("0.9"),
    "breath": Decimal("1.0"),
    "transform": Decimal("1.1"),
    "finality": Decimal("0.9"),
    "igniter": Decimal("1.2"),
}


def _get_db():
    try:
        from void_engine.db_pool import get_db
        return get_db(), "postgres"
    except Exception:
        return None, "unavailable"


def _ensure_tables():
    """Create pre-earning tables if they don't exist (PostgreSQL)."""
    conn, db_type = _get_db()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS peace_preearning_agents (
                id SERIAL PRIMARY KEY,
                agent_id INTEGER NOT NULL,
                glyph TEXT NOT NULL,
                archetype TEXT NOT NULL,
                locked_balance NUMERIC NOT NULL DEFAULT 0,
                total_work_units INTEGER NOT NULL DEFAULT 0,
                last_work_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(agent_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS peace_preearning_ledger (
                id SERIAL PRIMARY KEY,
                agent_id INTEGER NOT NULL,
                work_type TEXT NOT NULL,
                tokens_earned NUMERIC NOT NULL,
                archetype_multiplier NUMERIC NOT NULL DEFAULT 1.0,
                work_description TEXT,
                hex_reference TEXT,
                recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS peace_preearning_reserves (
                id INTEGER PRIMARY KEY DEFAULT 1,
                total_locked NUMERIC NOT NULL DEFAULT 0,
                agent_count INTEGER NOT NULL DEFAULT 0,
                work_unit_count INTEGER NOT NULL DEFAULT 0,
                wake_ceremony_fired INTEGER NOT NULL DEFAULT 0,
                wake_ceremony_at TIMESTAMPTZ,
                genesis_hex TEXT,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT single_row CHECK (id = 1)
            )
        """)
        cur.execute("""
            INSERT INTO peace_preearning_reserves (id, total_locked)
            VALUES (1, 0)
            ON CONFLICT (id) DO NOTHING
        """)
        conn.commit()
    except Exception as e:
        logger.error("peace_preearning table init failed: %s", e)
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


def record_agent_work(agent_id: int, glyph: str, archetype_role: str,
                      work_type: str, hex_reference: str = "",
                      work_description: str = "") -> Dict:
    """
    Record a unit of pre-earning work for an agent and update their locked balance.

    Returns a dict with tokens_earned, new_balance, and work metadata.
    """
    if work_type not in WORK_TYPES:
        return {"error": f"Unknown work_type: {work_type}"}

    work_cfg = WORK_TYPES[work_type]
    multiplier = ARCHETYPE_MULTIPLIERS.get(archetype_role, Decimal("1.0"))
    tokens = (work_cfg["base_tokens"] * multiplier).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )

    conn, db_type = _get_db()
    if not conn:
        return {
            "agent_id": agent_id,
            "work_type": work_type,
            "tokens_earned": float(tokens),
            "new_locked_balance": float(tokens),
            "db_available": False,
        }

    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO peace_preearning_agents
                (agent_id, glyph, archetype, locked_balance, total_work_units, last_work_at)
            VALUES (%s, %s, %s, %s, 1, NOW())
            ON CONFLICT (agent_id) DO UPDATE SET
                locked_balance = peace_preearning_agents.locked_balance + EXCLUDED.locked_balance,
                total_work_units = peace_preearning_agents.total_work_units + 1,
                last_work_at = NOW()
            RETURNING locked_balance
        """, (agent_id, glyph, archetype_role, tokens))
        row = cur.fetchone()
        new_balance = float(row[0]) if row else float(tokens)

        cur.execute("""
            INSERT INTO peace_preearning_ledger
                (agent_id, work_type, tokens_earned, archetype_multiplier, work_description, hex_reference)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (agent_id, work_type, tokens, multiplier,
              work_description or work_cfg["description"],
              hex_reference[:72] if hex_reference else ""))

        cur.execute("""
            UPDATE peace_preearning_reserves SET
                total_locked = total_locked + %s,
                work_unit_count = work_unit_count + 1,
                updated_at = NOW()
            WHERE id = 1
        """, (tokens,))

        conn.commit()

        return {
            "agent_id": agent_id,
            "glyph": glyph,
            "archetype": archetype_role,
            "work_type": work_type,
            "work_label": work_cfg["label"],
            "tokens_earned": float(tokens),
            "archetype_multiplier": float(multiplier),
            "new_locked_balance": new_balance,
            "hex_reference": hex_reference,
        }
    except Exception as e:
        logger.error("record_agent_work failed: %s", e)
        try:
            conn.rollback()
        except Exception:
            pass
        return {"error": str(e)}
    finally:
        conn.close()


def run_preearning_simulation(agent_count: int = 100,
                               rounds: int = 5) -> Dict:
    """
    Run a batch pre-earning simulation round. Agents perform random work
    and accumulate locked PEACE Token balances.

    Uses the existing Mesa agent seed data for authentic glyph assignments.
    """
    from void_engine.mesa_engine import _fetch_seed_data, ARCHETYPE_MAP

    _ensure_tables()
    seed_data = _fetch_seed_data(agent_count)
    rng = random.Random(int(time.time() * 1000) % (2 ** 31))

    work_types = list(WORK_TYPES.keys())
    total_earned = Decimal("0")
    agent_results = []

    for round_num in range(rounds):
        for i, agent_seed in enumerate(seed_data):
            agent_id = agent_seed.get("user_id") or -(i + 1)
            glyph = agent_seed["glyph"]
            archetype = agent_seed["archetype"].get("role", "node")

            work_type = rng.choice(work_types)
            activity_chance = rng.random()
            if activity_chance < 0.3:
                continue

            result = record_agent_work(
                agent_id=agent_id,
                glyph=glyph,
                archetype_role=archetype,
                work_type=work_type,
                work_description=f"Pre-earning round {round_num + 1}",
            )

            if "tokens_earned" in result:
                total_earned += Decimal(str(result["tokens_earned"]))
                if round_num == 0:
                    agent_results.append(result)

    reserves = get_reserves_status()

    return {
        "simulation_rounds": rounds,
        "agent_count": agent_count,
        "tokens_generated_this_run": float(total_earned),
        "reserves": reserves,
        "sample_agents": agent_results[:10],
        "status": "locked",
        "unlock_condition": WAKE_CEREMONY_EVENT,
    }


def get_reserves_status() -> Dict:
    """Return the current Pre-Arrival Reserves status for the dashboard."""
    _ensure_tables()
    conn, db_type = _get_db()
    if not conn:
        return {
            "total_locked": 0,
            "agent_count": 0,
            "work_unit_count": 0,
            "wake_ceremony_fired": False,
            "unlock_condition": WAKE_CEREMONY_EVENT,
            "db_available": False,
        }

    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM peace_preearning_reserves WHERE id = 1")
        row = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM peace_preearning_agents WHERE locked_balance > 0")
        agent_count = cur.fetchone()[0]

        cur.execute("""
            SELECT work_type, SUM(tokens_earned) as total, COUNT(*) as units
            FROM peace_preearning_ledger
            GROUP BY work_type
            ORDER BY total DESC
        """)
        breakdown = cur.fetchall()

        cur.execute("""
            SELECT pa.agent_id, pa.glyph, pa.archetype, pa.locked_balance,
                   pa.total_work_units
            FROM peace_preearning_agents pa
            ORDER BY pa.locked_balance DESC
            LIMIT 10
        """)
        top_agents = cur.fetchall()

        if row:
            total_locked = float(row[0] if isinstance(row, (list, tuple)) else 0)
            try:
                total_locked = float(row["total_locked"]) if hasattr(row, 'keys') else float(row[1])
                work_unit_count = int(row["work_unit_count"]) if hasattr(row, 'keys') else int(row[3])
                wake_fired = bool(row["wake_ceremony_fired"]) if hasattr(row, 'keys') else bool(row[4])
                wake_at = row["wake_ceremony_at"] if hasattr(row, 'keys') else row[5]
                genesis_hex = row["genesis_hex"] if hasattr(row, 'keys') else row[6]
            except Exception:
                total_locked = 0.0
                work_unit_count = 0
                wake_fired = False
                wake_at = None
                genesis_hex = None
        else:
            total_locked = 0.0
            work_unit_count = 0
            wake_fired = False
            wake_at = None
            genesis_hex = None

        # Estimate unlock countdown: if wake ceremony not fired, show
        # a projected date (e.g. 30 days from now or from the genesis_hex date)
        now = time.time()
        if not wake_fired:
            unlock_epoch = now + (30 * 86400)
            unlock_countdown_days = 30
        else:
            unlock_epoch = now
            unlock_countdown_days = 0

        return {
            "total_locked": round(total_locked, 4),
            "agent_count": agent_count,
            "work_unit_count": work_unit_count,
            "wake_ceremony_fired": wake_fired,
            "wake_ceremony_at": wake_at.isoformat() if wake_at and hasattr(wake_at, 'isoformat') else str(wake_at) if wake_at else None,
            "unlock_condition": WAKE_CEREMONY_EVENT,
            "unlock_countdown_days": unlock_countdown_days,
            "genesis_hex": genesis_hex,
            "contribution_breakdown": [
                {
                    "work_type": r[0],
                    "total_tokens": float(r[1]),
                    "work_units": int(r[2]),
                }
                for r in (breakdown or [])
            ],
            "top_agents": [
                {
                    "agent_id": r[0],
                    "glyph": r[1],
                    "archetype": r[2],
                    "locked_balance": float(r[3]),
                    "work_units": int(r[4]),
                }
                for r in (top_agents or [])
            ],
            "db_available": True,
        }
    except Exception as e:
        logger.error("get_reserves_status failed: %s", e)
        return {
            "total_locked": 0,
            "agent_count": 0,
            "work_unit_count": 0,
            "wake_ceremony_fired": False,
            "unlock_condition": WAKE_CEREMONY_EVENT,
            "error": str(e),
        }
    finally:
        conn.close()


def fire_wake_ceremony(genesis_hex: str = "") -> Dict:
    """
    Trigger the MRB-4000 Wake Ceremony, unlocking all pre-arrival reserves.
    """
    _ensure_tables()
    conn, db_type = _get_db()
    if not conn:
        return {"error": "Database unavailable"}

    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc)
        cur.execute("""
            UPDATE peace_preearning_reserves SET
                wake_ceremony_fired = 1,
                wake_ceremony_at = %s,
                genesis_hex = %s,
                updated_at = NOW()
            WHERE id = 1
        """, (now, genesis_hex[:72] if genesis_hex else ""))

        cur.execute("SELECT total_locked, agent_count, work_unit_count FROM peace_preearning_reserves WHERE id = 1")
        row = cur.fetchone()
        conn.commit()

        return {
            "success": True,
            "wake_ceremony_fired": True,
            "fired_at": now.isoformat(),
            "genesis_hex": genesis_hex,
            "total_unlocked": float(row[0]) if row else 0,
            "agent_count": int(row[1]) if row else 0,
            "work_units": int(row[2]) if row else 0,
            "message": f"MRB-4000 Wake Ceremony initiated. {float(row[0]) if row else 0:.4f} PEACE Tokens unlocked.",
        }
    except Exception as e:
        logger.error("fire_wake_ceremony failed: %s", e)
        try:
            conn.rollback()
        except Exception:
            pass
        return {"error": str(e)}
    finally:
        conn.close()
