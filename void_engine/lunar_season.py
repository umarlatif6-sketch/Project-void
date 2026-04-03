"""
Lunar Season Clock — PROJECT VOID
==================================
Provides the Seed-to-Hex system with seasonal context:

  FAST        — High-focus building (Fasting / Ramadan-period equivalent)
  FEAST       — Expansive growth & fruitification (Eid / celebration period)
  INCUBATION  — Pre-arrival quiet (post-celebration, seeds are gestating)

The season is founder-configured via set_season() and persists in the
chronicle DB as a simple key-value config row.

MRB-4000 Countdown:
  Start date: April 3 2026 (the sync point, 15 days into Incubation)
  Target date: configurable, defaults to 75 days from start (June 17 2026)

HEX_DIGEST lock:
  0x4C756E61725F536561736F6E5F5368696674  +
  0x42696F4D65645F506174656E745F5265616479
  both locked into VOID_CHRONICLE on first call to get_season_status().
"""

from __future__ import annotations

import os
import json
import time
import logging
from datetime import date, datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_SEASON_LABELS = {
    "FAST":       "Fast",
    "FEAST":      "Feast",
    "INCUBATION": "Incubation",
}

_SEASON_COLORS = {
    "FAST":       "#7c5cff",
    "FEAST":      "#2dd4bf",
    "INCUBATION": "#c9a84c",
}

_SEASON_EMOJIS = {
    "FAST":       "🌙",
    "FEAST":      "🌱",
    "INCUBATION": "🥚",
}

_SEASON_DESCRIPTIONS = {
    "FAST":       "High-focus building — stillness & sovereign construction.",
    "FEAST":      "Expansive growth & fruitification — celebrate and distribute.",
    "INCUBATION": "Pre-arrival quiet — seeds are gestating, the machine is listening.",
}

MRB4000_START_DATE  = date(2026, 4, 3)
MRB4000_TOTAL_DAYS  = 75
MRB4000_TARGET_DATE = date(2026, 6, 17)
MRB4000_INCUBATION_ELAPSED_AT_SYNC = 15

HEX_DIGEST_SEASON  = "0x4C756E61725F536561736F6E5F5368696674"
HEX_DIGEST_BIOMED  = "0x42696F4D65645F506174656E745F5265616479"

_LOCKED_DIGESTS_SEEDED = False


def get_current_season() -> str:
    """Return the current season key (FAST / FEAST / INCUBATION)."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            _ensure_season_table(cur)
            cur.execute("SELECT value FROM void_config WHERE key = 'current_season'")
            row = cur.fetchone()
            if row:
                return row[0]
        finally:
            conn.close()
    except Exception as e:
        logger.debug("Season DB read failed: %s", e)
    return "INCUBATION"


def set_season(season: str) -> Dict:
    """Founder-configures the active season.  Records a SEASON_SHIFT Chronicle entry."""
    season = season.upper()
    if season not in _SEASON_LABELS:
        return {"error": f"Unknown season '{season}'. Valid: {list(_SEASON_LABELS.keys())}"}

    prev = get_current_season()

    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            _ensure_season_table(cur)
            cur.execute(
                "INSERT INTO void_config (key, value) VALUES ('current_season', %s) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                (season,),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error("Season DB write failed: %s", e)
        return {"error": str(e)}

    if prev != season:
        _record_season_shift(prev, season)

    return {"success": True, "season": season, "previous": prev}


def get_mrb4000_countdown() -> Dict:
    """Return countdown state for the MRB-4000 physical assembly."""
    today = datetime.now(timezone.utc).date()
    elapsed = (today - MRB4000_START_DATE).days
    remaining = (MRB4000_TARGET_DATE - today).days

    target_date_str = get_config_value("mrb4000_target_date", MRB4000_TARGET_DATE.isoformat())
    try:
        target = date.fromisoformat(target_date_str)
    except Exception:
        target = MRB4000_TARGET_DATE

    total = (target - MRB4000_START_DATE).days
    remaining = (target - today).days
    progress_pct = round(min(100.0, max(0.0, elapsed / total * 100)) if total > 0 else 0.0, 1)

    return {
        "start_date":  MRB4000_START_DATE.isoformat(),
        "target_date": target.isoformat(),
        "total_days":  total,
        "elapsed_days": max(0, elapsed),
        "remaining_days": max(0, remaining),
        "progress_pct": progress_pct,
        "incubation_elapsed_at_sync": MRB4000_INCUBATION_ELAPSED_AT_SYNC,
        "is_past_due": remaining < 0,
        "hex_seal": HEX_DIGEST_SEASON,
    }


def get_season_status() -> Dict:
    """Full season status for dashboard display."""
    global _LOCKED_DIGESTS_SEEDED
    season = get_current_season()

    if not _LOCKED_DIGESTS_SEEDED:
        try:
            _seed_hex_digests()
            _LOCKED_DIGESTS_SEEDED = True
        except Exception as e:
            logger.debug("Hex digest seeding skipped: %s", e)

    return {
        "season": season,
        "label": _SEASON_LABELS.get(season, season),
        "color": _SEASON_COLORS.get(season, "#888"),
        "emoji": _SEASON_EMOJIS.get(season, ""),
        "description": _SEASON_DESCRIPTIONS.get(season, ""),
        "all_seasons": [
            {
                "key": k,
                "label": v,
                "color": _SEASON_COLORS[k],
                "emoji": _SEASON_EMOJIS[k],
                "active": k == season,
            }
            for k, v in _SEASON_LABELS.items()
        ],
        "mrb4000": get_mrb4000_countdown(),
        "hex_digests": [HEX_DIGEST_SEASON, HEX_DIGEST_BIOMED],
    }


def get_config_value(key: str, default: str = "") -> str:
    """Generic void_config table read."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            _ensure_season_table(cur)
            cur.execute("SELECT value FROM void_config WHERE key = %s", (key,))
            row = cur.fetchone()
            return row[0] if row else default
        finally:
            conn.close()
    except Exception:
        return default


def set_config_value(key: str, value: str) -> None:
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            _ensure_season_table(cur)
            cur.execute(
                "INSERT INTO void_config (key, value) VALUES (%s, %s) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error("void_config write failed: %s", e)


def _ensure_season_table(cur) -> None:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS void_config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cur.execute(
        "INSERT INTO void_config (key, value) VALUES ('current_season', 'INCUBATION') "
        "ON CONFLICT (key) DO NOTHING"
    )


def _record_season_shift(prev: str, new: str) -> None:
    """Write a SEASON_SHIFT entry to the Adriana Chronicle."""
    try:
        from void_engine.chronicle_adriana import _get_db
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
        conn = _get_db()
        try:
            cur = conn.cursor()
            from void_engine.chronicle_adriana import _ensure_seed_capture_columns
            _ensure_seed_capture_columns(cur)
            now = datetime.now(timezone.utc)
            title = f"Season Shift: {_SEASON_LABELS.get(prev, prev)} → {_SEASON_LABELS.get(new, new)}"
            subtitle = f"Lunar Clock — {now.strftime('%Y-%m-%d')}"
            body = (
                f"The Seed-to-Hex system has entered a new season.\n\n"
                f"Previous Season: {_SEASON_LABELS.get(prev, prev)} {_SEASON_EMOJIS.get(prev, '')}\n"
                f"New Season: {_SEASON_LABELS.get(new, new)} {_SEASON_EMOJIS.get(new, '')}\n\n"
                f"{_SEASON_DESCRIPTIONS.get(new, '')}\n\n"
                f"HEX_SEAL: {HEX_DIGEST_SEASON}"
            )
            al_jabr_hash = fatiha_286_hexdigest_from_str(f"SEASON_SHIFT|{prev}|{new}|{now.isoformat()}")
            cur.execute(
                """INSERT INTO chronicle_entries
                   (chapter_number, title, subtitle, glyph_sequence, body_text, al_jabr_hash, entry_type, season)
                   VALUES (%s, %s, %s, %s, %s, %s, 'SEASON_SHIFT', %s)""",
                (0, title, subtitle, "τ-🌙-◆", body, al_jabr_hash, new),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Season shift chronicle record failed: %s", e)


def _seed_hex_digests() -> None:
    """Lock HEX_DIGEST entries into the Chronicle once."""
    from void_engine.chronicle_adriana import _get_db
    from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
    conn = _get_db()
    try:
        cur = conn.cursor()
        from void_engine.chronicle_adriana import _ensure_seed_capture_columns
        _ensure_seed_capture_columns(cur)

        cur.execute(
            "SELECT id FROM chronicle_entries WHERE title = %s AND entry_type = %s LIMIT 1",
            ("VOID_CHRONICLE HEX_DIGEST Lock", "SEASON_SHIFT"),
        )
        if cur.fetchone():
            return

        body = (
            "Sovereign hex digest lock — Seasons of the Void & BioMed Patent Readiness.\n\n"
            f"HEX_DIGEST[1]: {HEX_DIGEST_SEASON}\n"
            f"  Decoded: LunarSeason_Shift\n\n"
            f"HEX_DIGEST[2]: {HEX_DIGEST_BIOMED}\n"
            f"  Decoded: BioMed_Patent_Ready\n\n"
            "Both digests are locked into VOID_CHRONICLE as permanent ancestral memory. "
            "The Seed-to-Hex system now carries seasonal intelligence. "
            "The Patent-Loom is production-ready for the UK Biomedical meeting."
        )
        al_jabr_hash = fatiha_286_hexdigest_from_str(f"VOID_CHRONICLE|HEX_DIGEST|LOCK|{HEX_DIGEST_SEASON}|{HEX_DIGEST_BIOMED}")
        seed_season = get_current_season()
        cur.execute(
            """INSERT INTO chronicle_entries
               (chapter_number, title, subtitle, glyph_sequence, body_text, al_jabr_hash, entry_type, season)
               VALUES (%s, %s, %s, %s, %s, %s, 'SEASON_SHIFT', %s)""",
            (
                0,
                "VOID_CHRONICLE HEX_DIGEST Lock",
                "Seasons of the Void + BioMed Patent Ready — April 3, 2026",
                "α-◆-τ",
                body,
                al_jabr_hash,
                seed_season,
            ),
        )
        conn.commit()
        logger.info("HEX_DIGEST lock seeded into VOID_CHRONICLE")
    except Exception as e:
        logger.warning("HEX_DIGEST seeding failed: %s", e)
    finally:
        conn.close()


def seed_initial_season() -> None:
    """Called at startup to initialise DB tables and seed hex digests."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            _ensure_season_table(cur)
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Season table init failed: %s", e)
