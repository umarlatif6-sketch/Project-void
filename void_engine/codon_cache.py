"""
Codon Response Cache — Platform Token Shield
=============================================
Shared codon-hashed response cache for all skill modules, VoidEcho,
Academy, and Void Language AI calls.

Before any expensive AI call the engine checks whether a codon-hashed
equivalent of that request has been answered before. If yes, the cached
response is returned — zero AI spend.

Cache TTL: 24 hours.
Best-effort: never raises, never blocks.

Usage:
    from void_engine.codon_cache import get_cached_codon_response, set_codon_cache

    cached = get_cached_codon_response(zone_id, input_signal)
    if cached is not None:
        return cached
    result = expensive_ai_call(...)
    set_codon_cache(zone_id, input_signal, result)
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_SCHEMA_ENSURED = False
_CACHE_TTL_HOURS = 24


# ── Schema ────────────────────────────────────────────────────────────────────

def _ensure_schema() -> None:
    global _SCHEMA_ENSURED
    if _SCHEMA_ENSURED:
        return
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS codon_response_cache (
                id           SERIAL PRIMARY KEY,
                codon_hash   TEXT NOT NULL UNIQUE,
                zone_id      TEXT NOT NULL,
                response_json TEXT NOT NULL,
                tokens_saved  INT NOT NULL DEFAULT 0,
                hit_count    INT NOT NULL DEFAULT 0,
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at   TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS codon_response_cache_hash_idx
                ON codon_response_cache (codon_hash, expires_at)
        """)
        conn.commit()
        cur.close()
        conn.close()
        _SCHEMA_ENSURED = True
        logger.info("[CodonCache] Schema ensured: codon_response_cache")
    except Exception as exc:
        logger.error("[CodonCache] Schema migration failed: %s", exc)


# ── Hash ──────────────────────────────────────────────────────────────────────

def _compute_codon_hash(zone_id: str, input_signal: str) -> str:
    """
    Compute a stable hash for a (zone_id, input_signal) pair.
    Uses SHA-256 over the JSON-serialised pair for determinism.
    """
    material = json.dumps({"zone": zone_id, "signal": input_signal}, sort_keys=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


# ── Cache get / set ───────────────────────────────────────────────────────────

def get_cached_codon_response(zone_id: str, input_signal: str) -> Optional[Any]:
    """
    Look up a cached response for (zone_id, input_signal).

    Returns the deserialised response if a non-expired cache entry exists,
    otherwise returns None.  Never raises.
    """
    _ensure_schema()
    codon_hash = _compute_codon_hash(zone_id, input_signal)
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """SELECT id, response_json, tokens_saved
               FROM codon_response_cache
               WHERE codon_hash = %s AND expires_at > NOW()""",
            (codon_hash,),
        )
        row = cur.fetchone()
        if row:
            row_id, response_json, tokens_saved = row[0], row[1], row[2]
            cur.execute(
                "UPDATE codon_response_cache SET hit_count = hit_count + 1 WHERE id = %s",
                (row_id,),
            )
            conn.commit()
            cur.close()
            conn.close()
            logger.info(
                "[CodonCache] HIT zone=%s hash=%s tokens_saved=%d",
                zone_id, codon_hash[:12], tokens_saved,
            )
            _log_cache_hit_to_chronicle(zone_id, codon_hash, tokens_saved)
            return json.loads(response_json)
        cur.close()
        conn.close()
        return None
    except Exception as exc:
        logger.warning("[CodonCache] Cache lookup failed: %s", exc)
        return None


def set_codon_cache(
    zone_id: str,
    input_signal: str,
    response: Any,
    tokens_saved: int = 0,
) -> None:
    """
    Store a response in the codon cache keyed by (zone_id, input_signal).

    token_saved: estimated tokens this cache entry will save on future hits.
    TTL is 24 hours from now.
    Never raises.
    """
    _ensure_schema()
    codon_hash = _compute_codon_hash(zone_id, input_signal)
    try:
        response_json = json.dumps(response, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        logger.warning("[CodonCache] Response serialisation failed: %s", exc)
        return

    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO codon_response_cache
               (codon_hash, zone_id, response_json, tokens_saved, expires_at)
               VALUES (%s, %s, %s, %s, NOW() + INTERVAL '24 hours')
               ON CONFLICT (codon_hash) DO UPDATE
                   SET response_json = EXCLUDED.response_json,
                       tokens_saved  = EXCLUDED.tokens_saved,
                       expires_at    = NOW() + INTERVAL '24 hours'
            """,
            (codon_hash, zone_id, response_json, tokens_saved),
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info(
            "[CodonCache] SET zone=%s hash=%s tokens_saved=%d",
            zone_id, codon_hash[:12], tokens_saved,
        )
    except Exception as exc:
        logger.warning("[CodonCache] Cache write failed: %s", exc)


# ── Chronicle logging ─────────────────────────────────────────────────────────

def _log_cache_hit_to_chronicle(
    zone_id: str,
    codon_hash: str,
    tokens_saved: int,
) -> None:
    """
    Seal a lightweight CODON_CACHE_HIT entry into the Chronicle after each
    cache hit.  Best-effort — never raises, never blocks.
    """
    try:
        from void_engine.db_pool import get_db
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

        seal_data = f"CODON_CACHE_HIT|{zone_id}|{codon_hash}|tokens:{tokens_saved}"
        al_jabr_hash = fatiha_286_hexdigest_from_str(seal_data)

        title = f"CODON CACHE HIT — {zone_id.upper()}"
        subtitle = f"Zone: {zone_id} | Hash: {codon_hash[:16]}... | Tokens saved: {tokens_saved}"
        body = (
            f"[CODON_CACHE_HIT]\n\n"
            f"Zone: {zone_id}\n"
            f"Codon hash: {codon_hash}\n"
            f"Estimated tokens saved: {tokens_saved}\n\n"
            f"Al-Jabr 286: {al_jabr_hash}"
        )

        try:
            from void_engine.void_codon_vocab import get_codon
            zone = get_codon(zone_id)
            glyph_seq = zone["codon"] if zone else "◆·◆·◆"
        except Exception:
            glyph_seq = "◆·◆·◆"

        try:
            from void_engine.chronicle_adriana import _get_current_season
            season = _get_current_season()
        except Exception:
            season = "INCUBATION"

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chronicle_entries
               (chapter_number, title, subtitle, glyph_sequence, body_text,
                al_jabr_hash, entry_type, season)
               VALUES (
                   (SELECT COALESCE(MAX(chapter_number), 0) + 1 FROM chronicle_entries),
                   %s, %s, %s, %s, %s, 'CODON_CACHE_HIT', %s
               )""",
            (title, subtitle, glyph_seq, body, al_jabr_hash, season),
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info(
            "[CodonCache] Chronicle CODON_CACHE_HIT sealed zone=%s tokens_saved=%d",
            zone_id, tokens_saved,
        )
    except Exception as exc:
        logger.debug("[CodonCache] Chronicle seal failed (non-critical): %s", exc)


# ── Cache key helper for skill modules ───────────────────────────────────────

def build_skill_cache_key(skill_id: str, intent: dict) -> str:
    """
    Build a stable, human-readable cache input signal from a skill intent dict.
    Strips unstable fields and serialises deterministically.
    """
    stable_fields = {k: v for k, v in intent.items() if k not in ("_ts", "_session")}
    return json.dumps({"skill": skill_id, "intent": stable_fields}, sort_keys=True)
