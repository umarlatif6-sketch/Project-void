"""
Genesis Hex — Master Canonical Hash Generation
================================================
Combines the 12-day chronicle history, incubation records, locus records,
and pre-arrival agent balance into a single canonical Master Hex digest.

This digest is stored as the project's permanent Genesis Hex — the
origin seal of the VOID system.

Components fed into the Master Hex:
  1. 12-day Chronicle window (successful consensus entries)
  2. Incubation logic records (Mesa simulation rounds)
  3. Locus records (geographic anchors from seed_hex captures)
  4. Pre-arrival agent balance (locked PEACE Token reserves total)
  5. Timestamp + machine identity anchor

The result is computed via Al-Jabr 286 layered hashing, stored in the
seed_hex DB, and optionally sealed into the Pre-Arrival Reserves table.
"""

import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

from void_engine.al_jabr_286 import (
    fatiha_286_hash,
    fatiha_286_hexdigest,
    fatiha_286_truncated,
    fatiha_286_hexdigest_from_str,
    FATIHA_LAYERS,
)

logger = logging.getLogger(__name__)

_GENESIS_HEX_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'genesis_hex.json'
)
DAYS_WINDOW = 12


def _get_chronicle_window(days: int = DAYS_WINDOW) -> List[Dict]:
    """Pull the last N days of successful Chronicle entries (SQLite)."""
    try:
        from void_engine.chronicle import CHRONICLE_DB_PATH
        cutoff = time.time() - (days * 86400)
        db_path = CHRONICLE_DB_PATH
        if not os.path.exists(db_path):
            return []
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("""
                SELECT timestamp, consensus_command, consensus_intent,
                       outcome, success, energy_pct, machine_id
                FROM chronicle
                WHERE success = 1 AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("[GenesisHex] Chronicle window fetch failed: %s", exc)
        return []


def _get_incubation_records() -> List[Dict]:
    """Pull Mesa simulation runs (incubation logic) from PostgreSQL."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT run_id, agent_count, rounds, seed_event, status,
                       started_at, completed_at
                FROM mesa_simulation_runs
                WHERE status = 'complete'
                ORDER BY started_at DESC
                LIMIT 50
            """)
            rows = cur.fetchall()
            return [
                {
                    "run_id": r[0],
                    "agent_count": r[1],
                    "rounds": r[2],
                    "seed_event": r[3],
                    "status": r[4],
                    "started_at": r[5].isoformat() if r[5] else None,
                    "completed_at": r[6].isoformat() if r[6] else None,
                }
                for r in rows
            ]
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("[GenesisHex] Incubation records fetch failed: %s", exc)
        return []


def _get_locus_records() -> List[Dict]:
    """Pull locus records from seed_hex captures."""
    try:
        from void_engine.seed_hex_engine import _get_conn as _shconn, _DB_PATH as _shdb, _ensure_db
        _ensure_db()
        with _shconn() as conn:
            rows = conn.execute("""
                SELECT timestamp, source, hex_digest, transmission_id
                FROM seed_hex_captures
                WHERE source LIKE 'locus%'
                ORDER BY timestamp DESC LIMIT 200
            """).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.warning("[GenesisHex] Locus records fetch failed: %s", exc)
        return []


def _get_preearning_balance() -> float:
    """Get total locked pre-arrival PEACE Token balance."""
    try:
        from void_engine.peace_preearning import get_reserves_status
        reserves = get_reserves_status()
        return reserves.get("total_locked", 0.0)
    except Exception as exc:
        logger.warning("[GenesisHex] Pre-earning balance fetch failed: %s", exc)
        return 0.0


def _hash_component(label: str, data: Any) -> bytes:
    """Hash a single component with Al-Jabr 286."""
    serialized = json.dumps(
        {"component": label, "data": data},
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return fatiha_286_hash(serialized)


def _combine_component_hashes(hashes: List[bytes]) -> bytes:
    """
    Combine multiple component hashes using the FATIHA_LAYERS weights,
    producing a single 36-byte sovereign digest.
    """
    if not hashes:
        return fatiha_286_hash(b"VOID-GENESIS-EMPTY")

    combined = b""
    for i, h in enumerate(hashes):
        layer_weight = FATIHA_LAYERS[i % len(FATIHA_LAYERS)]
        weighted = bytes(b * layer_weight % 256 for b in h)
        combined += weighted

    return fatiha_286_hash(combined)


def generate_master_hex(force: bool = False) -> Dict:
    """
    Compute the Master Hex digest from all seed components and store it.

    Args:
        force: If True, regenerate even if a genesis hex already exists.

    Returns:
        dict with genesis_hex, component_digests, timestamp, and metadata.
    """
    # Check for existing genesis hex
    existing = _load_genesis_hex()
    if existing and not force:
        return {**existing, "regenerated": False}

    logger.info("[GenesisHex] Computing Master Hex...")

    # Gather all components
    chronicle_window = _get_chronicle_window(DAYS_WINDOW)
    incubation_records = _get_incubation_records()
    locus_records = _get_locus_records()
    preearning_balance = _get_preearning_balance()

    machine_id = os.environ.get("REPL_ID", "VOID-LOCAL")
    timestamp = time.time()

    # Hash each component
    components = [
        ("chronicle_12day", chronicle_window),
        ("incubation_records", incubation_records),
        ("locus_records", locus_records),
        ("preearning_balance", preearning_balance),
        ("machine_identity", machine_id),
        ("genesis_timestamp", timestamp),
        ("fatiha_anchor", FATIHA_LAYERS),
    ]

    component_digests = {}
    component_hashes = []
    for label, data in components:
        h = _hash_component(label, data)
        component_digests[label] = h.hex()
        component_hashes.append(h)

    master_hash = _combine_component_hashes(component_hashes)
    genesis_hex = master_hash.hex()

    # Build metadata
    result = {
        "genesis_hex": genesis_hex,
        "component_digests": component_digests,
        "components": {
            "chronicle_entries": len(chronicle_window),
            "chronicle_window_days": DAYS_WINDOW,
            "incubation_runs": len(incubation_records),
            "locus_records": len(locus_records),
            "preearning_balance": preearning_balance,
            "machine_id": machine_id,
        },
        "timestamp": timestamp,
        "timestamp_iso": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp)),
        "protocol": "Al-Jabr 286 — Layered Sovereign Hashing",
        "fatiha_layers": FATIHA_LAYERS,
        "genesis_label": "Master Hex — Project VOID Origin Seal",
        "regenerated": True,
    }

    # Persist to JSON file
    _store_genesis_hex(result)

    # Also seal into pre-earning reserves table
    _seal_into_reserves(genesis_hex)

    # Also seal into seed_hex DB
    _seal_into_seed_hex_db(genesis_hex, result)

    logger.info("[GenesisHex] Master Hex computed: %s...", genesis_hex[:16])
    return result


def get_genesis_hex() -> Optional[Dict]:
    """Return the stored Genesis Hex if it exists."""
    return _load_genesis_hex()


def _load_genesis_hex() -> Optional[Dict]:
    try:
        if os.path.exists(_GENESIS_HEX_PATH):
            with open(_GENESIS_HEX_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as exc:
        logger.warning("[GenesisHex] Load failed: %s", exc)
    return None


def _store_genesis_hex(data: Dict):
    os.makedirs(os.path.dirname(_GENESIS_HEX_PATH), exist_ok=True)
    with open(_GENESIS_HEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def _seal_into_reserves(genesis_hex: str):
    """Write genesis_hex into the pre-earning reserves table."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE peace_preearning_reserves
                SET genesis_hex = %s, updated_at = NOW()
                WHERE id = 1
            """, (genesis_hex[:72],))
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.debug("[GenesisHex] Reserves seal failed: %s", exc)


def _seal_into_seed_hex_db(genesis_hex: str, data: Dict):
    """Store genesis hex into the seed_hex SQLite DB."""
    try:
        from void_engine.seed_hex_engine import _get_conn, _ensure_db
        _ensure_db()
        with _get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO seed_hex_genesis
                    (id, genesis_hex, genesis_timestamp, component_sources, created_at)
                VALUES (1, ?, ?, ?, datetime('now'))
            """, (
                genesis_hex,
                data.get("timestamp"),
                json.dumps(data.get("component_digests", {}), default=str),
            ))
    except Exception as exc:
        logger.debug("[GenesisHex] Seed hex DB seal failed: %s", exc)
