"""
Project Void — SQLite Persistence Layer
========================================
Single-file database with WAL mode for concurrent reads.
All timestamps are stored as ISO-8601 UTC strings.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from config import (
    DB_PATH,
    SHOP_ITEMS,
    VTX_BASE_WORKOUT_REWARD,
    VTX_DAILY_CAP,
    VTX_STREAK_MULTIPLIER_CAP,
    VTX_STREAK_MULTIPLIER_STEP,
)

_local = threading.local()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _yesterday_utc() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


# ── Connection Pool (per-thread) ────────────────────────────────────

@contextmanager
def get_db():
    """Yield a thread-local SQLite connection with WAL mode."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        _local.conn = conn
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ── Schema ───────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY,
    username        TEXT,
    first_name      TEXT,
    vtx_balance     REAL    DEFAULT 0.0,
    peace_balance   REAL    DEFAULT 0.0,
    streak_days     INTEGER DEFAULT 0,
    last_workout    TEXT,           -- ISO date (YYYY-MM-DD)
    last_breathe    TEXT,
    vtx_earned_today REAL   DEFAULT 0.0,
    vtx_today_date  TEXT,           -- tracks which day the counter is for
    created_at      TEXT    NOT NULL,
    resonance_freq  REAL    DEFAULT 432.0
);

CREATE TABLE IF NOT EXISTS workouts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id),
    space_analysis  TEXT,           -- JSON blob from photo analysis
    routine         TEXT,           -- JSON blob of generated routine
    vtx_earned      REAL    DEFAULT 0.0,
    completed       INTEGER DEFAULT 0,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id),
    item_id         TEXT    NOT NULL,
    purchased_at    TEXT    NOT NULL,
    UNIQUE(user_id, item_id)
);

CREATE TABLE IF NOT EXISTS peace_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id),
    action_type     TEXT    NOT NULL,   -- breathe, meditate, journal
    peace_earned    REAL    DEFAULT 0.0,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id),
    prompt          TEXT,
    entry           TEXT,
    peace_earned    REAL    DEFAULT 0.0,
    created_at      TEXT    NOT NULL
);
"""


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript(_SCHEMA)


# ── User Operations ──────────────────────────────────────────────────

def get_or_create_user(user_id: int, username: str = "", first_name: str = "") -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, _utcnow()),
        )
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row)


def get_user(user_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


# ── Streak Logic ─────────────────────────────────────────────────────

def _get_streak_shield(user_id: int) -> int:
    """Return extra grace days from Octopus Nerve."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM inventory WHERE user_id = ? AND item_id = 'octopus_nerve'",
            (user_id,),
        ).fetchone()
        return 1 if row else 0


def update_streak(user_id: int) -> int:
    """Update streak based on last workout date. Returns new streak."""
    user = get_user(user_id)
    if not user:
        return 0

    today = _today_utc()
    yesterday = _yesterday_utc()
    last = user["last_workout"]
    shield = _get_streak_shield(user_id)

    if last == today:
        return user["streak_days"]
    elif last == yesterday:
        new_streak = user["streak_days"] + 1
    elif shield > 0 and last:
        # Check if within shield window
        grace_date = (datetime.now(timezone.utc) - timedelta(days=1 + shield)).strftime("%Y-%m-%d")
        if last >= grace_date:
            new_streak = user["streak_days"] + 1
        else:
            new_streak = 1
    else:
        new_streak = 1

    with get_db() as conn:
        conn.execute(
            "UPDATE users SET streak_days = ?, last_workout = ? WHERE user_id = ?",
            (new_streak, today, user_id),
        )
    return new_streak


def get_streak_multiplier(streak_days: int) -> float:
    """Calculate resonance multiplier from streak."""
    mult = 1.0 + (streak_days * VTX_STREAK_MULTIPLIER_STEP)
    return min(mult, VTX_STREAK_MULTIPLIER_CAP)


# ── VTX Economy ──────────────────────────────────────────────────────

def get_equipment_multiplier(user_id: int) -> float:
    """Sum all equipment multiplier bonuses."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT item_id FROM inventory WHERE user_id = ?", (user_id,)
        ).fetchall()
    owned_ids = {r["item_id"] for r in rows}
    bonus = 0.0
    for item in SHOP_ITEMS:
        if item["id"] in owned_ids:
            bonus += item["multiplier"]
    return bonus


def _reset_daily_vtx_if_needed(user_id: int) -> None:
    """Reset today's VTX counter if the date has rolled over."""
    today = _today_utc()
    with get_db() as conn:
        row = conn.execute(
            "SELECT vtx_today_date FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row and row["vtx_today_date"] != today:
            conn.execute(
                "UPDATE users SET vtx_earned_today = 0.0, vtx_today_date = ? WHERE user_id = ?",
                (today, user_id),
            )


def award_vtx(user_id: int, base_amount: float | None = None) -> dict:
    """
    Award VTX for a completed workout, applying streak + equipment multipliers.
    Respects daily cap. Returns dict with details.
    """
    _reset_daily_vtx_if_needed(user_id)
    user = get_user(user_id)
    if not user:
        return {"awarded": 0, "reason": "user_not_found"}

    remaining = VTX_DAILY_CAP - user["vtx_earned_today"]
    if remaining <= 0:
        return {
            "awarded": 0,
            "reason": "daily_cap",
            "balance": user["vtx_balance"],
            "earned_today": user["vtx_earned_today"],
        }

    base = base_amount or VTX_BASE_WORKOUT_REWARD
    streak_mult = get_streak_multiplier(user["streak_days"])
    equip_mult = get_equipment_multiplier(user_id)
    total_mult = streak_mult + equip_mult
    raw = base * total_mult
    awarded = min(raw, remaining)

    with get_db() as conn:
        conn.execute(
            """UPDATE users
               SET vtx_balance = vtx_balance + ?,
                   vtx_earned_today = vtx_earned_today + ?,
                   vtx_today_date = ?
               WHERE user_id = ?""",
            (awarded, awarded, _today_utc(), user_id),
        )

    return {
        "awarded": round(awarded, 2),
        "base": base,
        "streak_mult": round(streak_mult, 2),
        "equip_mult": round(equip_mult, 2),
        "total_mult": round(total_mult, 2),
        "balance": round(user["vtx_balance"] + awarded, 2),
        "earned_today": round(user["vtx_earned_today"] + awarded, 2),
        "daily_cap": VTX_DAILY_CAP,
    }


# ── PEACE Economy ────────────────────────────────────────────────────

def get_peace_bonus(user_id: int) -> int:
    """Extra PEACE from Mycelium Wrap."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM inventory WHERE user_id = ? AND item_id = 'mycelium_wrap'",
            (user_id,),
        ).fetchone()
        return 2 if row else 0


def award_peace(user_id: int, action_type: str, base_amount: float) -> dict:
    """Award PEACE tokens for a non-extractive action."""
    bonus = get_peace_bonus(user_id)
    total = base_amount + bonus

    with get_db() as conn:
        conn.execute(
            "UPDATE users SET peace_balance = peace_balance + ? WHERE user_id = ?",
            (total, user_id),
        )
        conn.execute(
            "INSERT INTO peace_log (user_id, action_type, peace_earned, created_at) VALUES (?, ?, ?, ?)",
            (user_id, action_type, total, _utcnow()),
        )

    user = get_user(user_id)
    return {
        "awarded": round(total, 2),
        "bonus": bonus,
        "balance": round(user["peace_balance"], 2) if user else total,
    }


# ── Workout Persistence ─────────────────────────────────────────────

def save_workout(user_id: int, space_analysis: dict, routine: dict) -> int:
    """Save a generated workout. Returns workout ID."""
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO workouts (user_id, space_analysis, routine, created_at)
               VALUES (?, ?, ?, ?)""",
            (user_id, json.dumps(space_analysis), json.dumps(routine), _utcnow()),
        )
        return cur.lastrowid


def complete_workout(workout_id: int, user_id: int) -> dict:
    """Mark workout complete, update streak, award VTX."""
    with get_db() as conn:
        conn.execute(
            "UPDATE workouts SET completed = 1 WHERE id = ? AND user_id = ?",
            (workout_id, user_id),
        )
    streak = update_streak(user_id)
    reward = award_vtx(user_id)
    reward["streak"] = streak
    reward["workout_id"] = workout_id
    return reward


def get_latest_workout(user_id: int) -> Optional[dict]:
    """Get the most recent workout for a user."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM workouts WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if row:
            d = dict(row)
            d["space_analysis"] = json.loads(d["space_analysis"]) if d["space_analysis"] else {}
            d["routine"] = json.loads(d["routine"]) if d["routine"] else {}
            return d
        return None


# ── Equipment Shop ───────────────────────────────────────────────────

def get_user_inventory(user_id: int) -> list[str]:
    """Return list of owned item IDs."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT item_id FROM inventory WHERE user_id = ?", (user_id,)
        ).fetchall()
        return [r["item_id"] for r in rows]


def purchase_item(user_id: int, item_id: str) -> dict:
    """Attempt to purchase an item. Returns result dict."""
    item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
    if not item:
        return {"success": False, "reason": "Item not found in the Void armoury."}

    user = get_user(user_id)
    if not user:
        return {"success": False, "reason": "User not found."}

    owned = get_user_inventory(user_id)
    if item_id in owned:
        return {"success": False, "reason": "You already own this item."}

    if user["vtx_balance"] < item["cost"]:
        deficit = item["cost"] - user["vtx_balance"]
        return {
            "success": False,
            "reason": f"Not enough VTX. You need {deficit:.0f} more.",
        }

    with get_db() as conn:
        conn.execute(
            "UPDATE users SET vtx_balance = vtx_balance - ? WHERE user_id = ?",
            (item["cost"], user_id),
        )
        conn.execute(
            "INSERT INTO inventory (user_id, item_id, purchased_at) VALUES (?, ?, ?)",
            (user_id, item_id, _utcnow()),
        )

    return {
        "success": True,
        "item": item,
        "new_balance": round(user["vtx_balance"] - item["cost"], 2),
    }


# ── Stats ────────────────────────────────────────────────────────────

def get_user_stats(user_id: int) -> Optional[dict]:
    """Aggregate stats for a user."""
    user = get_user(user_id)
    if not user:
        return None

    with get_db() as conn:
        workout_count = conn.execute(
            "SELECT COUNT(*) as c FROM workouts WHERE user_id = ? AND completed = 1",
            (user_id,),
        ).fetchone()["c"]

        total_vtx_earned = conn.execute(
            "SELECT COALESCE(SUM(vtx_earned), 0) as s FROM workouts WHERE user_id = ? AND completed = 1",
            (user_id,),
        ).fetchone()["s"]

        peace_actions = conn.execute(
            "SELECT COUNT(*) as c FROM peace_log WHERE user_id = ?",
            (user_id,),
        ).fetchone()["c"]

        total_peace_earned = conn.execute(
            "SELECT COALESCE(SUM(peace_earned), 0) as s FROM peace_log WHERE user_id = ?",
            (user_id,),
        ).fetchone()["s"]

    inventory = get_user_inventory(user_id)

    return {
        "user": user,
        "workouts_completed": workout_count,
        "total_vtx_earned": round(total_vtx_earned, 2),
        "peace_actions": peace_actions,
        "total_peace_earned": round(total_peace_earned, 2),
        "inventory": inventory,
        "streak_multiplier": get_streak_multiplier(user["streak_days"]),
        "equipment_multiplier": get_equipment_multiplier(user_id),
    }
