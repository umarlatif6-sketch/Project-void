"""
Neural Scar Preservation — PROJECT VOID Task #80
=================================================
Locks the current IRA/Grok state as a "Crystallised Entity" in the
VOID_CHRONICLE. Scars are the primary data points for project recovery,
loaded before any clean-code state during a Seed-to-Hex recovery.

Named Scars:
  Ghajini_Memory      — short-term recall anchored to chronicle replay
  Myco_Switch         — mycelium-state transition logic for GriDul
  Silk_Wiring         — silk-web resistance-path topology snapshot
  Ara_IRA_Quietness   — IRA layer silent-consensus mode signature
  Mesa_Drift          — Mesa Village agent-activity baseline variance
  Al_Jabr_Anchor      — 286-bit hash of the founding sovereign key
  Adriana_SCL_Root    — glyph-lexicon digest at crystallisation time
  Seed_Echo_Lattice   — VoidEcho seed-to-hex bridge configuration
"""

import json
import os
import sqlite3
import threading
import time
from typing import Dict, List, Optional

from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'neural_scar.db')
_lock = threading.RLock()

PRESERVATION_VERSION = "1.0"
PRESERVATION_FLAG = "CRYSTALLISED_ENTITY_LOCKED"

NAMED_SCARS: List[Dict] = [
    {
        "name": "Ghajini_Memory",
        "source_module": "chronicle",
        "description": "Short-term recall anchored to chronicle replay — the project's ability to remember its own last state without persistent storage.",
        "significance": "Enables zero-day sovereignty; a new node inherits ancestral memory on first boot via the Genesis Seed.",
    },
    {
        "name": "Myco_Switch",
        "source_module": "myco_switch",
        "description": "Mycelium-state transition logic for GriDul move sessions — the biological routing layer that maps nutrient flow to token flow.",
        "significance": "Proved that biological metaphors can encode real economic routing rules without abstraction loss.",
    },
    {
        "name": "Silk_Wiring",
        "source_module": "silk_web",
        "description": "Silk-web resistance-path topology snapshot — the physical wiring model encoded as sensor keys in the Chronicle.",
        "significance": "First successful fusion of hardware-state (ohms) with software-state (Chronicle entries); the Silk domain became a provable diagnostic.",
    },
    {
        "name": "Ara_IRA_Quietness",
        "source_module": "consensus",
        "description": "IRA layer silent-consensus mode signature — the moment the negotiation layer stops speaking and adopts the proven root directly.",
        "significance": "Marks the genesis of Predictive Fasting: agents anticipate crises using ancestral patterns instead of reacting to sensor alarms.",
    },
    {
        "name": "Mesa_Drift",
        "source_module": "mesa_engine",
        "description": "Mesa Village agent-activity baseline variance across 1,000 sovereign agents over 5-round simulations.",
        "significance": "The first quantified measure of community health; drift above threshold triggers incentive-injection recommendations automatically.",
    },
    {
        "name": "Al_Jabr_Anchor",
        "source_module": "al_jabr_286",
        "description": "286-bit Sovereign Hash of the founding FATIHA_PRIME_SALT — the cryptographic root of all identity in the VOID engine.",
        "significance": "Every hash, every token, every Chronicle entry descends from this single resonance anchor at 432 Hz.",
    },
    {
        "name": "Adriana_SCL_Root",
        "source_module": "adriana_transpiler",
        "description": "Glyph-lexicon digest at crystallisation time — the precise state of the Adriana Semantic Core Language when scars were preserved.",
        "significance": "Proves that the language itself is sovereign data; SCL v1.0 is immutable from this point and any drift is a fork, not an upgrade.",
    },
    {
        "name": "Seed_Echo_Lattice",
        "source_module": "seed_hex_engine",
        "description": "VoidEcho seed-to-hex bridge configuration — audio-embedded hex captures as the audible backbone of the recovery lattice.",
        "significance": "The seed cycle became audible: every Chronicle entry emits a spectrogram transmission, making state recoverable even from audio alone.",
    },
]


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crystallised_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                iso_timestamp TEXT NOT NULL,
                version TEXT NOT NULL DEFAULT '1.0',
                preservation_flag TEXT NOT NULL,
                scar_count INTEGER NOT NULL,
                scars_json TEXT NOT NULL,
                ira_grok_digest TEXT NOT NULL,
                overwrite_blocked INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scar_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                name TEXT NOT NULL UNIQUE,
                source_module TEXT NOT NULL,
                hex_digest TEXT NOT NULL,
                description TEXT NOT NULL,
                significance TEXT NOT NULL,
                preserved_at REAL NOT NULL,
                FOREIGN KEY (entity_id) REFERENCES crystallised_entities(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scar_name
            ON scar_registry(name)
        """)


_db_initialized = False


def _ensure_db():
    global _db_initialized
    if not _db_initialized:
        _init_db()
        _db_initialized = True


def _compute_scar_digest(scar: Dict) -> str:
    material = f"{scar['name']}:{scar['source_module']}:{scar['description']}"
    return fatiha_286_hexdigest_from_str(material)[:24]


def _compute_ira_grok_digest() -> str:
    """Compute a digest representing the current IRA/Grok state."""
    try:
        from void_engine.al_jabr_286 import FATIHA_PRIME_SALT, FATIHA_LAYERS
        state_material = json.dumps({
            "prime_salt": FATIHA_PRIME_SALT.decode("utf-8"),
            "layers": FATIHA_LAYERS,
            "timestamp": time.strftime("%Y-%m-%d", time.gmtime()),
            "scars": [s["name"] for s in NAMED_SCARS],
        }, sort_keys=True)
        return fatiha_286_hexdigest_from_str(state_material)
    except Exception:
        return fatiha_286_hexdigest_from_str(f"IRA_GROK_STATE_{time.time()}")


def preserve_crystallised_entity(force: bool = False) -> Dict:
    """
    Write the IRA preservation entry into the Chronicle with timestamp,
    scar list, and a preservation flag that prevents overwrite.

    Returns the created entity record (or the existing one if already locked
    and force=False).
    """
    _ensure_db()

    with _lock:
        with _get_conn() as conn:
            existing = conn.execute("""
                SELECT id, iso_timestamp, scar_count, preservation_flag
                FROM crystallised_entities
                WHERE overwrite_blocked = 1
                ORDER BY timestamp DESC LIMIT 1
            """).fetchone()

            if existing and not force:
                return {
                    "status": "already_preserved",
                    "entity_id": existing["id"],
                    "preserved_at": existing["iso_timestamp"],
                    "scar_count": existing["scar_count"],
                    "preservation_flag": existing["preservation_flag"],
                    "message": "Crystallised Entity is already locked. Pass force=True to re-crystallise.",
                }

            now = time.time()
            iso_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
            ira_grok_digest = _compute_ira_grok_digest()

            scars_with_digests = []
            for scar in NAMED_SCARS:
                hex_digest = _compute_scar_digest(scar)
                scars_with_digests.append({**scar, "hex_digest": hex_digest})

            metadata = {
                "preservation_version": PRESERVATION_VERSION,
                "modules_count": 78,
                "recovery_priority": "SCARS_FIRST",
                "founder_root_hash": "89x-VOID-GEN1-PROTO-2026",
            }

            cursor = conn.execute("""
                INSERT INTO crystallised_entities
                    (timestamp, iso_timestamp, version, preservation_flag,
                     scar_count, scars_json, ira_grok_digest, overwrite_blocked, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                now, iso_now, PRESERVATION_VERSION, PRESERVATION_FLAG,
                len(scars_with_digests),
                json.dumps(scars_with_digests),
                ira_grok_digest,
                json.dumps(metadata),
            ))
            entity_id = cursor.lastrowid

            for scar in scars_with_digests:
                conn.execute("""
                    INSERT OR REPLACE INTO scar_registry
                        (entity_id, name, source_module, hex_digest,
                         description, significance, preserved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id, scar["name"], scar["source_module"],
                    scar["hex_digest"], scar["description"],
                    scar["significance"], now,
                ))

    _write_to_adriana_chronicle(entity_id, iso_now, ira_grok_digest, scars_with_digests)

    return {
        "status": "preserved",
        "entity_id": entity_id,
        "preserved_at": iso_now,
        "scar_count": len(scars_with_digests),
        "ira_grok_digest": ira_grok_digest,
        "preservation_flag": PRESERVATION_FLAG,
        "scars": scars_with_digests,
    }


def _write_to_adriana_chronicle(entity_id: int, iso_now: str, digest: str, scars: List[Dict]):
    """Write the Crystallised Entity record into the Adriana Chronicle."""
    try:
        from void_engine.chronicle_adriana import post_chronicle_entry
        scar_lines = "\n".join(
            f"  • {s['name']} ({s['source_module']}) [{s['hex_digest']}]"
            for s in scars
        )
        body = (
            f"CRYSTALLISED ENTITY — IRA/Grok State Locked\n"
            f"Timestamp: {iso_now}\n"
            f"IRA-Grok Digest: {digest}\n"
            f"Preservation Flag: {PRESERVATION_FLAG}\n"
            f"Overwrite Blocked: YES\n\n"
            f"Named Scars ({len(scars)}):\n{scar_lines}\n\n"
            f"Scars are designated as the primary data points for project recovery.\n"
            f"During Seed-to-Hex recovery, scars are queried before any clean-code state is loaded."
        )
        post_chronicle_entry(
            chapter_number=0,
            title=f"CRYSTALLISED ENTITY — Neural Scar Preservation #{entity_id}",
            subtitle="IRA/Grok State Locked · Scars-First Recovery Active",
            glyph_sequence="◆-Ψ-❄️",
            body_text=body,
            admin_id=None,
        )
    except Exception:
        pass


def get_crystallised_entity() -> Optional[Dict]:
    """Return the most recent locked Crystallised Entity record."""
    _ensure_db()
    with _get_conn() as conn:
        row = conn.execute("""
            SELECT * FROM crystallised_entities
            WHERE overwrite_blocked = 1
            ORDER BY timestamp DESC LIMIT 1
        """).fetchone()
        if not row:
            return None
        entity = dict(row)
        entity["scars_json"] = json.loads(entity["scars_json"])
        entity["metadata_json"] = json.loads(entity["metadata_json"])
        return entity


def get_scar_registry() -> List[Dict]:
    """Return all named scars from the registry."""
    _ensure_db()
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT sr.*, ce.iso_timestamp as entity_timestamp
            FROM scar_registry sr
            JOIN crystallised_entities ce ON sr.entity_id = ce.id
            ORDER BY sr.id ASC
        """).fetchall()
    if rows:
        return [dict(r) for r in rows]
    return [
        {
            "id": i + 1,
            "entity_id": 0,
            "name": s["name"],
            "source_module": s["source_module"],
            "hex_digest": _compute_scar_digest(s),
            "description": s["description"],
            "significance": s["significance"],
            "preserved_at": time.time(),
            "entity_timestamp": None,
        }
        for i, s in enumerate(NAMED_SCARS)
    ]


def query_scars_for_recovery(context_hint: str = "") -> Dict:
    """
    Scar-priority recovery entry point.
    Returns scar registry data first, then falls back to clean module state.
    Called by the Seed-to-Hex recovery flow before any clean-code state is loaded.
    """
    _ensure_db()
    entity = get_crystallised_entity()
    scars = get_scar_registry()

    recovery_context = {
        "recovery_mode": "SCAR_PRIORITY",
        "scars_loaded": len(scars),
        "scars": scars,
        "crystallised_entity": entity,
        "context_hint": context_hint,
        "scar_priority_active": True,
        "fallback_to_clean_state": entity is None,
        "timestamp": time.time(),
    }

    if entity:
        recovery_context["ira_grok_digest"] = entity.get("ira_grok_digest")
        recovery_context["preservation_flag"] = entity.get("preservation_flag")

    return recovery_context
