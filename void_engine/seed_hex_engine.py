"""
Seed-to-Hex Engine with VoidEcho Bridge
=========================================
Captures Seed-to-Hex digests and automatically broadcasts them as VoidEcho
transmission signals. Every new hex capture is:
  1. Recorded as a Seed capture event in the seed_hex_captures SQLite table
  2. Encoded as a spectrogram audio transmission via audio_stega
  3. Logged as a VoidEcho broadcast transmission in the chronicle

The hex digest becomes an audio-embedded transmission, not just a database
entry — the seed cycle is audible and archivable.
"""

import os
import json
import time
import sqlite3
import threading
import logging
from typing import Dict, List, Optional
from void_engine.al_jabr_286 import (
    fatiha_286_hexdigest,
    fatiha_286_truncated,
    fatiha_286_hexdigest_from_str,
)

logger = logging.getLogger(__name__)

_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'seed_hex.db')
_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output_audio', 'seed_hex')

_lock = threading.RLock()


def _init_db():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seed_hex_captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                source TEXT NOT NULL,
                input_data TEXT NOT NULL,
                hex_digest TEXT NOT NULL,
                voidecho_path TEXT,
                voidecho_broadcast INTEGER DEFAULT 0,
                chronicle_logged INTEGER DEFAULT 0,
                transmission_id TEXT,
                created_at TEXT NOT NULL,
                qisync_salt TEXT,
                origin_verified INTEGER DEFAULT 0
            )
        """)
        try:
            conn.execute("ALTER TABLE seed_hex_captures ADD COLUMN qisync_salt TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE seed_hex_captures ADD COLUMN origin_verified INTEGER DEFAULT 0")
        except Exception:
            pass
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_shc_timestamp
            ON seed_hex_captures(timestamp)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seed_hex_genesis (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                genesis_hex TEXT,
                genesis_timestamp REAL,
                component_sources TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)


def _get_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


_db_initialized = False


def _ensure_db():
    global _db_initialized
    if not _db_initialized:
        _init_db()
        _db_initialized = True


def _generate_qisync_salt(timestamp: float, source: str) -> str:
    """
    Origin Anchor (Task #81): Generate a QiSync biometric timestamp salt.

    The salt is derived from:
      - The current Unix timestamp (millisecond precision)
      - The source label
      - A QiSync-specific prefix

    On recovery queries, callers must present this salt to prove the entry
    originated from a live system interaction rather than a simulated sandbox.
    Entries lacking a valid salt are flagged as "Simulated / Unverified".
    """
    raw = f"QiSync:OriginAnchor:{timestamp:.6f}:{source}".encode("utf-8")
    return fatiha_286_truncated(raw, 32)


def verify_origin_anchor(capture_id: int, presented_salt: str) -> Dict:
    """
    Origin Anchor (Task #81): Verify that a hex entry's salt matches the
    presented value.  Returns a dict with:
      - verified: bool
      - status: 'ANCHORED' | 'SIMULATED_UNVERIFIED' | 'NOT_FOUND'
    """
    _ensure_db()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT qisync_salt, origin_verified FROM seed_hex_captures WHERE id = ?",
            (capture_id,),
        ).fetchone()

    if not row:
        return {"verified": False, "status": "NOT_FOUND", "capture_id": capture_id}

    stored_salt = row["qisync_salt"] or ""
    if stored_salt and presented_salt and presented_salt == stored_salt:
        return {"verified": True, "status": "ANCHORED", "capture_id": capture_id}
    return {"verified": False, "status": "SIMULATED_UNVERIFIED", "capture_id": capture_id}


def capture_seed_hex(source: str, input_data: str,
                     broadcast: bool = True) -> Dict:
    """
    Compute the Al-Jabr 286-bit hex digest for input_data, record the capture,
    and optionally broadcast it as a VoidEcho transmission.

    Args:
        source:     A label for what produced this capture (e.g. 'chronicle', 'locus', 'agent')
        input_data: The raw string to hash
        broadcast:  If True, encode the hex digest into audio and log as VoidEcho

    Returns:
        dict with hex_digest, capture_id, voidecho_path, broadcast status
    """
    _ensure_db()

    hex_digest = fatiha_286_hexdigest_from_str(input_data)
    now = time.time()
    created_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))

    qisync_salt = _generate_qisync_salt(now, source)

    with _lock:
        with _get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO seed_hex_captures
                    (timestamp, source, input_data, hex_digest, created_at, qisync_salt, origin_verified)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (now, source, input_data[:2000], hex_digest, created_at, qisync_salt))
            capture_id = cursor.lastrowid

    result = {
        "capture_id": capture_id,
        "hex_digest": hex_digest,
        "source": source,
        "timestamp": now,
        "voidecho_broadcast": False,
        "voidecho_path": None,
        "transmission_id": None,
        "qisync_salt": qisync_salt,
        "origin_anchor": "ANCHORED",
    }

    if broadcast:
        try:
            broadcast_result = _broadcast_as_voidecho(capture_id, hex_digest, source, now)
            result.update(broadcast_result)
        except Exception as exc:
            logger.warning("[SeedHex] VoidEcho broadcast failed for capture %s: %s", capture_id, exc)

    return result


def _broadcast_as_voidecho(capture_id: int, hex_digest: str, source: str, timestamp: float) -> Dict:
    """
    Encode the hex digest into spectrogram audio and log as VoidEcho broadcast.

    Lead Shield (Task #81): If the social resonance monitor reports that
    broadcasting is paused (Gone Dark), skip the audio emission and return
    a suppressed result.  The capture is still recorded; only the outgoing
    signal is withheld.
    """
    try:
        from void_engine.lead_shield import is_broadcast_paused, feed_shield_from_engine
        feed_shield_from_engine()
        if is_broadcast_paused():
            logger.info("[SeedHex] Lead Shield GONE_DARK — broadcast suppressed for capture %s", capture_id)
            return {
                "voidecho_broadcast": False,
                "voidecho_path": None,
                "transmission_id": None,
                "lead_shield_suppressed": True,
            }
    except Exception:
        pass

    transmission_id = fatiha_286_truncated(
        f"seedhex:{capture_id}:{hex_digest}".encode("utf-8"), 16
    )
    message = f"VOID-SEED:{hex_digest[:32]}"

    voidecho_path = None
    try:
        from void_engine.audio_stega import encode_spectrogram
        output_name = f"seed_hex_{transmission_id}.wav"
        output_path = os.path.join(_OUTPUT_DIR, output_name)
        wav_bytes = encode_spectrogram(message, duration=8.0)
        with open(output_path, "wb") as f:
            f.write(wav_bytes)
        voidecho_path = output_path
        logger.info("[SeedHex] VoidEcho audio written: %s", output_name)
    except Exception as exc:
        logger.warning("[SeedHex] Audio encode failed: %s", exc)

    _log_to_voidecho_db(transmission_id, hex_digest, source, timestamp, voidecho_path)

    with _lock:
        with _get_conn() as conn:
            conn.execute("""
                UPDATE seed_hex_captures
                SET voidecho_path = ?, voidecho_broadcast = 1,
                    transmission_id = ?, chronicle_logged = 1
                WHERE id = ?
            """, (voidecho_path, transmission_id, capture_id))

    return {
        "voidecho_broadcast": True,
        "voidecho_path": voidecho_path,
        "transmission_id": transmission_id,
        "lead_shield_suppressed": False,
    }


def _log_to_voidecho_db(transmission_id: str, hex_digest: str, source: str,
                         timestamp: float, audio_path: Optional[str]):
    """Log the VoidEcho broadcast into the VoidEcho SQLite database."""
    try:
        ve_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'voidecho.db')
        if not os.path.exists(ve_db_path):
            return
        conn = sqlite3.connect(ve_db_path)
        conn.row_factory = sqlite3.Row
        try:
            # Check if voidecho_codes table exists
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            if 'voidecho_codes' not in tables:
                return

            created_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))
            conn.execute("""
                INSERT OR IGNORE INTO voidecho_codes
                    (id, retrieval_code, original_filename, file_extension,
                     output_path, created_at, is_paid)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (
                transmission_id,
                f"SEED-{transmission_id[:4]}-{transmission_id[4:8]}-{transmission_id[8:12]}",
                f"seed_hex_{source}",
                ".wav",
                audio_path or "",
                created_at,
            ))
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.debug("[SeedHex] VoidEcho DB log failed: %s", exc)


def get_recent_captures(limit: int = 50) -> List[Dict]:
    """Return the most recent seed-hex captures."""
    _ensure_db()
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM seed_hex_captures
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_capture_stats() -> Dict:
    """Return aggregate stats about captures."""
    _ensure_db()
    with _get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM seed_hex_captures").fetchone()[0]
        broadcast = conn.execute(
            "SELECT COUNT(*) FROM seed_hex_captures WHERE voidecho_broadcast = 1"
        ).fetchone()[0]
        sources = conn.execute("""
            SELECT source, COUNT(*) as cnt FROM seed_hex_captures
            GROUP BY source ORDER BY cnt DESC
        """).fetchall()
        latest = conn.execute("""
            SELECT hex_digest, source, timestamp FROM seed_hex_captures
            ORDER BY timestamp DESC LIMIT 1
        """).fetchone()
    return {
        "total_captures": total,
        "broadcast_count": broadcast,
        "broadcast_rate": round(broadcast / total * 100, 1) if total > 0 else 0,
        "source_breakdown": [{"source": r[0], "count": r[1]} for r in sources],
        "latest_digest": dict(latest) if latest else None,
    }


def auto_capture_chronicle_entry(chronicle_data: Dict) -> Optional[Dict]:
    """
    Called automatically when a new Chronicle entry is recorded.
    Produces a hex capture and VoidEcho broadcast.
    """
    material = json.dumps(chronicle_data, sort_keys=True, default=str)
    return capture_seed_hex(
        source="chronicle",
        input_data=material,
        broadcast=True,
    )


def auto_capture_locus_entry(locus_data: Dict) -> Optional[Dict]:
    """Called when a locus / location record is made."""
    material = json.dumps(locus_data, sort_keys=True, default=str)
    return capture_seed_hex(
        source="locus",
        input_data=material,
        broadcast=True,
    )


def auto_capture_agent_work(agent_id: int, work_type: str, work_data: Dict) -> Optional[Dict]:
    """Called when a Mesa agent completes a work unit."""
    material = json.dumps({
        "agent_id": agent_id,
        "work_type": work_type,
        "data": work_data,
        "timestamp": time.time(),
    }, sort_keys=True, default=str)
    return capture_seed_hex(
        source=f"agent_{work_type}",
        input_data=material,
        broadcast=True,
    )


def recover_project_context(context_hint: str = "") -> Dict:
    """
    Seed-to-Hex recovery entry point — Neural Scar Priority.

    Scars are queried FIRST before any clean module state is loaded.
    This ensures that project context is reconstructed from lived
    experience (scars) rather than initialised from zero.

    Recovery priority:
      1. Scar Registry — named scars with hex digests and significance
      2. Crystallised Entity — locked IRA/Grok state snapshot
      3. Recent Seed-Hex captures — latest VoidEcho broadcast chain
      4. Clean capture stats — fallback aggregate state

    Args:
        context_hint: Optional label for what triggered the recovery.

    Returns:
        Dict with scar context, recent captures, and recovery metadata.
    """
    _ensure_db()

    recovery = {
        "recovery_mode": "SCAR_PRIORITY",
        "context_hint": context_hint,
        "timestamp": time.time(),
        "stages": [],
    }

    try:
        from void_engine.neural_scar import query_scars_for_recovery
        scar_context = query_scars_for_recovery(context_hint=context_hint)
        recovery["scar_context"] = scar_context
        recovery["stages"].append({
            "stage": 1,
            "name": "scar_registry",
            "status": "loaded",
            "scars_count": scar_context.get("scars_loaded", 0),
        })
        logger.info(
            "[Recovery] Stage 1 complete — %d scars loaded from Scar Registry",
            scar_context.get("scars_loaded", 0),
        )
    except Exception as exc:
        recovery["scar_context"] = None
        recovery["stages"].append({"stage": 1, "name": "scar_registry", "status": "failed", "error": str(exc)})
        logger.warning("[Recovery] Stage 1 failed — Scar Registry unavailable: %s", exc)

    try:
        recent = get_recent_captures(limit=20)
        recovery["recent_captures"] = recent
        recovery["stages"].append({
            "stage": 2,
            "name": "seed_hex_captures",
            "status": "loaded",
            "captures_count": len(recent),
        })
        logger.info("[Recovery] Stage 2 complete — %d seed-hex captures loaded", len(recent))
    except Exception as exc:
        recovery["recent_captures"] = []
        recovery["stages"].append({"stage": 2, "name": "seed_hex_captures", "status": "failed", "error": str(exc)})
        logger.warning("[Recovery] Stage 2 failed — capture fetch error: %s", exc)

    try:
        stats = get_capture_stats()
        recovery["capture_stats"] = stats
        recovery["stages"].append({
            "stage": 3,
            "name": "capture_stats",
            "status": "loaded",
        })
    except Exception as exc:
        recovery["capture_stats"] = {}
        recovery["stages"].append({"stage": 3, "name": "capture_stats", "status": "failed", "error": str(exc)})

    recovery["recovery_complete"] = True
    recovery["primary_source"] = (
        "scar_registry" if recovery.get("scar_context") and
        recovery["scar_context"].get("scars_loaded", 0) > 0
        else "seed_hex_captures"
    )

    return recovery
