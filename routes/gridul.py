"""
GriDul — Community Mesh Module
================================
Four pillars:
  1. GriDul Move   — daily calisthenics movement tracker (earns VTX)
  2. GriDul Grow   — home aquaponics planner (up to 3 zones)
  3. GriDul Mesh   — neighbourhood food exchange (postcode-based, no money)
  4. GriDul Rumble — Adriana SCL stream-of-consciousness decoder (public, free)

Genesis 10 PEACE token sessions:
  - POST /api/gridul/session-start  — register a biological grow/compost session
  - POST /api/gridul/tick           — report progress
  - POST /api/gridul/session-end    — finalise and mint PEACE tokens
"""

import hashlib
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict

from flask import Blueprint, render_template, jsonify, session, request
from void_engine.db_pool import get_db

logger = logging.getLogger(__name__)
gridul_bp = Blueprint("gridul", __name__)

# ── Genesis 10 holder check ────────────────────────────────────────────────────

def _is_genesis_10_holder(user_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT 1 FROM token_ownership tow
               JOIN blueprint_tokens bt ON bt.id = tow.token_id
               WHERE tow.owner_id = %s AND bt.collection = 'genesis_10'
               LIMIT 1""",
            (user_id,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


# ── PEACE session store ────────────────────────────────────────────────────────

_SESSIONS: Dict[str, dict] = {}
_SESSION_MAX_AGE = 7200
_TICK_INTERVAL_S = 0.8
_MIN_REWARD_DURATION = 60
_VALID_ACTIONS = {"compost", "aquaponics", "grow", "harvest"}


def _prune():
    now = time.time()
    stale = [k for k, v in _SESSIONS.items() if now - v["start_time"] > _SESSION_MAX_AGE]
    for k in stale:
        _SESSIONS.pop(k, None)


def _key(user_id, session_id):
    return f"{user_id}:{session_id}"


# ── DB init ───────────────────────────────────────────────────────────────────

def init_gridul_tables():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gridul_move_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL UNIQUE,
                positions_completed JSONB DEFAULT '[]',
                total_reps INTEGER DEFAULT 0,
                duration_sec INTEGER DEFAULT 0,
                score NUMERIC(6,4) DEFAULT 0,
                vtx_earned NUMERIC(10,4) DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gridul_grow_zones (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                zone_type TEXT DEFAULT 'hydroponic',
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gridul_grow_plants (
                id SERIAL PRIMARY KEY,
                zone_id INTEGER NOT NULL REFERENCES gridul_grow_zones(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                variety TEXT,
                date_planted DATE,
                harvest_days INTEGER DEFAULT 60,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gridul_grow_logs (
                id SERIAL PRIMARY KEY,
                zone_id INTEGER NOT NULL REFERENCES gridul_grow_zones(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL,
                log_type TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gridul_mesh_listings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                quantity TEXT,
                postcode_prefix TEXT NOT NULL,
                exchange_type TEXT DEFAULT 'free',
                status TEXT DEFAULT 'active',
                expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '14 days'),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gridul_mesh_requests (
                id SERIAL PRIMARY KEY,
                listing_id INTEGER NOT NULL REFERENCES gridul_mesh_listings(id) ON DELETE CASCADE,
                requester_id INTEGER NOT NULL,
                message TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        # ── Fertilizer Formula Lab ─────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fertilizer_batches (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                batch_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'curing',
                quality_rating INTEGER,
                score NUMERIC(5,4) DEFAULT 0,
                vtx_earned NUMERIC(10,4) DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                completed_at TIMESTAMPTZ
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fertilizer_ingredients (
                id SERIAL PRIMARY KEY,
                batch_id INTEGER NOT NULL REFERENCES fertilizer_batches(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL,
                ingredient TEXT NOT NULL,
                quantity_grams NUMERIC(10,2) DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fertilizer_marketplace (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                batch_id INTEGER REFERENCES fertilizer_batches(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                description TEXT,
                quantity_kg NUMERIC(8,2),
                location TEXT NOT NULL,
                contact_info TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # ── Water Vitality Log ────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS water_vitality_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                ph NUMERIC(5,2),
                ec NUMERIC(8,3),
                temperature NUMERIC(6,2),
                minerals JSONB DEFAULT '{}',
                vitality_score NUMERIC(5,4) DEFAULT 0,
                is_drinkable BOOLEAN DEFAULT FALSE,
                notes TEXT,
                vtx_earned NUMERIC(10,4) DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # ── Memory Training Studio ────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memory_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL UNIQUE,
                scene_text TEXT NOT NULL,
                scene_duration_sec INTEGER DEFAULT 300,
                recall_answers JSONB DEFAULT '{}',
                recall_score NUMERIC(5,4) DEFAULT 0,
                memory_level INTEGER DEFAULT 1,
                vtx_earned NUMERIC(10,4) DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                completed_at TIMESTAMPTZ
            )
        """)

        conn.commit()
        logger.info("GriDul tables initialised")
    except Exception as e:
        conn.rollback()
        logger.error("GriDul table init failed: %s", e)
    finally:
        conn.close()


# ── Movement positions ─────────────────────────────────────────────────────────

MOVE_POSITIONS = [
    {
        "id": "standing_squat",
        "phase": "standing",
        "name": "Bodyweight Squat",
        "reps": 15,
        "breath": "inhale down, exhale up",
        "cue": "feet shoulder-width, chest tall, drive through heels",
    },
    {
        "id": "standing_lunge",
        "phase": "standing",
        "name": "Reverse Lunge",
        "reps": 10,
        "breath": "inhale step back, exhale drive up",
        "cue": "per side — keep front knee over ankle",
    },
    {
        "id": "standing_calf",
        "phase": "standing",
        "name": "Calf Raise",
        "reps": 20,
        "breath": "exhale rise, inhale lower",
        "cue": "pause at top for balance, lower slow",
    },
    {
        "id": "transition_inchworm",
        "phase": "transition",
        "name": "Inchworm",
        "reps": 6,
        "breath": "exhale walk out, inhale walk in",
        "cue": "walk hands out to plank, walk back — no knee bend",
    },
    {
        "id": "transition_world",
        "phase": "transition",
        "name": "World's Greatest Stretch",
        "reps": 5,
        "breath": "deep breath each position",
        "cue": "per side — open chest toward sky",
    },
    {
        "id": "ground_pushup",
        "phase": "ground",
        "name": "Push-Up",
        "reps": 12,
        "breath": "inhale down, exhale up",
        "cue": "body plank, elbows 45°, chest to fist height",
    },
    {
        "id": "ground_hollow",
        "phase": "ground",
        "name": "Hollow Body Hold",
        "reps": 30,
        "breath": "steady shallow breaths, ribs down",
        "cue": "seconds hold — lower back pressed to floor",
    },
    {
        "id": "ground_bridge",
        "phase": "ground",
        "name": "Glute Bridge",
        "reps": 15,
        "breath": "exhale squeeze up, inhale lower",
        "cue": "drive hips high, squeeze glutes at top",
    },
    {
        "id": "recovery_child",
        "phase": "recovery",
        "name": "Child's Pose",
        "reps": 30,
        "breath": "4 counts in, 4 counts out",
        "cue": "seconds — arms extended or alongside body",
    },
    {
        "id": "recovery_spine",
        "phase": "recovery",
        "name": "Supine Spinal Twist",
        "reps": 20,
        "breath": "inhale centre, exhale into twist",
        "cue": "seconds per side — shoulders stay grounded",
    },
]


# ── Landing page ───────────────────────────────────────────────────────────────

@gridul_bp.route("/gridul")
def gridul_landing():
    user_id = session.get("user_id")
    peace_balance = 0.0
    if user_id:
        try:
            from void_engine.vortex_wallet import get_peace_balance
            peace_balance = get_peace_balance(user_id)
        except Exception:
            pass
    return render_template("gridul.html", peace_balance=peace_balance)


# ─────────────────────────────────────────────────────────────────────────────
# MOVE
# ─────────────────────────────────────────────────────────────────────────────

@gridul_bp.route("/gridul/move")
def gridul_move():
    user_id = session.get("user_id")
    history = []
    if user_id:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT session_id, total_reps, duration_sec, score, vtx_earned, created_at
                FROM gridul_move_sessions
                WHERE user_id = %s AND completed = TRUE
                ORDER BY created_at DESC LIMIT 10
            """, (user_id,))
            for row in cur.fetchall():
                history.append({
                    "session_id": row[0],
                    "total_reps": row[1],
                    "duration_sec": row[2],
                    "score": float(row[3]),
                    "vtx_earned": float(row[4]),
                    "created_at": row[5].isoformat() if row[5] else None,
                })
        except Exception as e:
            logger.error("GriDul Move history error: %s", e)
        finally:
            conn.close()
    return render_template("gridul_move.html", positions=MOVE_POSITIONS, history=history)


@gridul_bp.route("/api/gridul/move/session-start", methods=["POST"])
def gridul_move_start():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    session_id = str(uuid.uuid4())
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gridul_move_sessions (user_id, session_id)
            VALUES (%s, %s)
        """, (user_id, session_id))
        conn.commit()
        logger.info("GriDul Move session started: user=%s sid=%s", user_id, session_id)
        return jsonify({"ok": True, "session_id": session_id, "positions": MOVE_POSITIONS})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Move session start error: %s", e)
        return jsonify({"error": "failed to start session"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/move/session-end", methods=["POST"])
def gridul_move_end():
    """
    End a GriDul Move session.

    Server-authoritative: duration is calculated from the DB-stored `created_at`
    timestamp, not from client-submitted values. The client's `completed_positions`
    list is validated against the known position catalogue to prevent injection of
    invalid IDs, and only canonical position IDs are stored.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    client_completed_ids = data.get("completed_positions", [])

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    VALID_POSITION_IDS = {p["id"] for p in MOVE_POSITIONS}

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, completed, created_at FROM gridul_move_sessions
            WHERE user_id = %s AND session_id = %s
        """, (user_id, session_id))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "session not found"}), 404
        if row[1]:
            return jsonify({"error": "session already ended"}), 409

        session_created_at = row[2]
        now_utc = datetime.now(timezone.utc)
        if session_created_at.tzinfo is None:
            session_created_at = session_created_at.replace(tzinfo=timezone.utc)
        duration_sec = max(0, int((now_utc - session_created_at).total_seconds()))

        completed_ids = list(dict.fromkeys(
            pid for pid in client_completed_ids if pid in VALID_POSITION_IDS
        ))

        total_positions = len(MOVE_POSITIONS)
        completed_count = len(completed_ids)
        total_reps = sum(p["reps"] for p in MOVE_POSITIONS if p["id"] in completed_ids)
        score = round(completed_count / total_positions, 4) if total_positions > 0 else 0

        vtx_earned = 0.0
        rewarded = False
        reward = None

        eligible = duration_sec >= 60 and completed_count >= 3

        cur.execute("""
            UPDATE gridul_move_sessions
            SET positions_completed = %s, total_reps = %s, duration_sec = %s,
                score = %s, completed = TRUE
            WHERE user_id = %s AND session_id = %s
        """, (
            json.dumps(completed_ids),
            total_reps, duration_sec, score,
            user_id, session_id
        ))
        conn.commit()

        if eligible:
            try:
                from void_engine.vortex_wallet import mint_gridul_move
                reward = mint_gridul_move(user_id, session_id, score, completed_count, duration_sec)
                vtx_earned = reward.get("vtx_earned", 0)
                rewarded = True

                cur.execute("""
                    UPDATE gridul_move_sessions SET vtx_earned = %s
                    WHERE user_id = %s AND session_id = %s
                """, (vtx_earned, user_id, session_id))
                conn.commit()
            except Exception as e:
                logger.error("mint_gridul_move failed: %s", e)

        logger.info("GriDul Move ended: user=%s sid=%s score=%.3f vtx=%.4f duration=%ds",
                    user_id, session_id, score, vtx_earned, duration_sec)
        return jsonify({
            "ok": True,
            "session_id": session_id,
            "score": score,
            "total_reps": total_reps,
            "completed_count": completed_count,
            "duration_sec": duration_sec,
            "rewarded": rewarded,
            "vtx_earned": vtx_earned,
            "reward": reward,
        })
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Move session end error: %s", e)
        return jsonify({"error": "failed to save session"}), 500
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# GROW
# ─────────────────────────────────────────────────────────────────────────────

_WATER_INTERVAL_HOURS = 24
_FEED_INTERVAL_HOURS = 72
_CHECK_INTERVAL_HOURS = 48
_HARVEST_SOON_DAYS = 14


def _compute_attention_items(zones):
    """
    Return a list of attention items for today's dashboard.
    Each item has: zone_name, plant_name (optional), item_type, urgency, message.
    Urgency: 'urgent' | 'soon' | 'info'
    """
    items = []
    today = datetime.now(timezone.utc).date()

    for zone in zones:
        zone_name = zone["name"]

        log_times = {}
        for log in zone.get("recent_logs", []):
            lt = log["log_type"]
            ca = log["created_at"]
            if ca and lt not in log_times:
                try:
                    ts = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                    log_times[lt] = ts
                except Exception:
                    pass

        now_utc = datetime.now(timezone.utc)

        def hours_since(log_type):
            if log_type not in log_times:
                return None
            return (now_utc - log_times[log_type]).total_seconds() / 3600

        water_h = hours_since("water")
        if water_h is None or water_h >= _WATER_INTERVAL_HOURS:
            urgency = "urgent" if water_h is None or water_h >= _WATER_INTERVAL_HOURS * 1.5 else "soon"
            last = f"{int(water_h)}h ago" if water_h is not None else "never"
            items.append({
                "zone_id": zone["id"],
                "zone_name": zone_name,
                "plant_name": None,
                "item_type": "water",
                "urgency": urgency,
                "message": f"Water {zone_name} — last watered {last}",
            })

        feed_h = hours_since("feed")
        if feed_h is None or feed_h >= _FEED_INTERVAL_HOURS:
            urgency = "urgent" if feed_h is None or feed_h >= _FEED_INTERVAL_HOURS * 1.5 else "soon"
            last = f"{int(feed_h)}h ago" if feed_h is not None else "never"
            items.append({
                "zone_id": zone["id"],
                "zone_name": zone_name,
                "plant_name": None,
                "item_type": "feed",
                "urgency": urgency,
                "message": f"Feed nutrients for {zone_name} — last fed {last}",
            })

        check_h = hours_since("check")
        if check_h is None or check_h >= _CHECK_INTERVAL_HOURS:
            urgency = "soon"
            items.append({
                "zone_id": zone["id"],
                "zone_name": zone_name,
                "plant_name": None,
                "item_type": "check",
                "urgency": urgency,
                "message": f"Check {zone_name} — inspect for pests / pH",
            })

        for plant in zone.get("plants", []):
            days_rem = plant.get("days_remaining")
            if days_rem is not None:
                if days_rem <= 0:
                    items.append({
                        "zone_id": zone["id"],
                        "zone_name": zone_name,
                        "plant_name": plant["name"],
                        "item_type": "harvest",
                        "urgency": "urgent",
                        "message": f"Harvest {plant['name']} in {zone_name} — overdue by {abs(days_rem)} days!",
                    })
                elif days_rem <= _HARVEST_SOON_DAYS:
                    items.append({
                        "zone_id": zone["id"],
                        "zone_name": zone_name,
                        "plant_name": plant["name"],
                        "item_type": "harvest",
                        "urgency": "soon",
                        "message": f"{plant['name']} in {zone_name} ready in {days_rem} days",
                    })

    urgent = [i for i in items if i["urgency"] == "urgent"]
    soon = [i for i in items if i["urgency"] == "soon"]
    info = [i for i in items if i["urgency"] == "info"]
    return urgent + soon + info


@gridul_bp.route("/gridul/grow")
def gridul_grow():
    user_id = session.get("user_id")
    zones = []
    attention_items = []
    if user_id:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, zone_type, notes, created_at
                FROM gridul_grow_zones WHERE user_id = %s ORDER BY id ASC
            """, (user_id,))
            for row in cur.fetchall():
                zone = {
                    "id": row[0], "name": row[1], "zone_type": row[2],
                    "notes": row[3], "created_at": row[4].isoformat() if row[4] else None,
                    "plants": [], "recent_logs": []
                }
                cur.execute("""
                    SELECT id, name, variety, date_planted, harvest_days, created_at
                    FROM gridul_grow_plants WHERE zone_id = %s ORDER BY id ASC
                """, (zone["id"],))
                for pr in cur.fetchall():
                    plant = {
                        "id": pr[0], "name": pr[1], "variety": pr[2],
                        "date_planted": pr[3].isoformat() if pr[3] else None,
                        "harvest_days": pr[4],
                        "created_at": pr[5].isoformat() if pr[5] else None,
                    }
                    if pr[3]:
                        planted = pr[3]
                        harvest_date = planted + timedelta(days=pr[4] or 60)
                        plant["harvest_date"] = harvest_date.isoformat()
                        plant["days_remaining"] = (harvest_date - datetime.now(timezone.utc).date()).days
                    else:
                        plant["harvest_date"] = None
                        plant["days_remaining"] = None
                    zone["plants"].append(plant)
                cur.execute("""
                    SELECT id, log_type, notes, created_at
                    FROM gridul_grow_logs WHERE zone_id = %s
                    ORDER BY created_at DESC LIMIT 5
                """, (zone["id"],))
                for lr in cur.fetchall():
                    zone["recent_logs"].append({
                        "id": lr[0], "log_type": lr[1], "notes": lr[2],
                        "created_at": lr[3].isoformat() if lr[3] else None,
                    })
                zones.append(zone)
            attention_items = _compute_attention_items(zones)
        except Exception as e:
            logger.error("GriDul Grow load error: %s", e)
        finally:
            conn.close()
    peace_balance = 0.0
    is_holder = False
    if user_id:
        try:
            from void_engine.vortex_wallet import get_peace_balance
            peace_balance = get_peace_balance(user_id)
        except Exception:
            pass
        try:
            is_holder = _is_genesis_10_holder(user_id)
        except Exception:
            pass
    return render_template("gridul_grow.html", zones=zones, attention_items=attention_items,
                           peace_balance=peace_balance, is_genesis_holder=is_holder)


@gridul_bp.route("/api/gridul/grow/zones", methods=["POST"])
def gridul_grow_add_zone():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    zone_type = data.get("zone_type", "hydroponic")
    notes = (data.get("notes") or "").strip()

    if not name:
        return jsonify({"error": "Zone name required"}), 400

    VALID_TYPES = {"hydroponic", "aquaponic", "soil", "container"}
    if zone_type not in VALID_TYPES:
        zone_type = "hydroponic"

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM gridul_grow_zones WHERE user_id = %s", (user_id,))
        count = cur.fetchone()[0]
        if count >= 3:
            return jsonify({"error": "Maximum 3 zones allowed"}), 400

        cur.execute("""
            INSERT INTO gridul_grow_zones (user_id, name, zone_type, notes)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (user_id, name, zone_type, notes))
        zone_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"ok": True, "zone_id": zone_id})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Grow add zone error: %s", e)
        return jsonify({"error": "failed to add zone"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/grow/zones/<int:zone_id>", methods=["DELETE"])
def gridul_grow_delete_zone(zone_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM gridul_grow_zones WHERE id = %s AND user_id = %s", (zone_id, user_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Grow delete zone error: %s", e)
        return jsonify({"error": "failed to delete zone"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/grow/plants", methods=["POST"])
def gridul_grow_add_plant():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    zone_id = data.get("zone_id")
    name = (data.get("name") or "").strip()
    variety = (data.get("variety") or "").strip()
    date_planted_raw = data.get("date_planted")
    date_planted = None
    if date_planted_raw:
        try:
            datetime.strptime(str(date_planted_raw), "%Y-%m-%d")
            date_planted = date_planted_raw
        except ValueError:
            return jsonify({"error": "date_planted must be in YYYY-MM-DD format"}), 400

    try:
        harvest_days = max(1, min(365, int(data.get("harvest_days") or 60)))
    except (ValueError, TypeError):
        return jsonify({"error": "harvest_days must be a number between 1 and 365"}), 400

    if not zone_id or not name:
        return jsonify({"error": "zone_id and name required"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM gridul_grow_zones WHERE id = %s AND user_id = %s",
                    (zone_id, user_id))
        if not cur.fetchone():
            return jsonify({"error": "zone not found"}), 404

        cur.execute("""
            INSERT INTO gridul_grow_plants (zone_id, user_id, name, variety, date_planted, harvest_days)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (zone_id, user_id, name, variety or None, date_planted or None, harvest_days))
        plant_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"ok": True, "plant_id": plant_id})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Grow add plant error: %s", e)
        return jsonify({"error": "failed to add plant"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/grow/plants/<int:plant_id>", methods=["DELETE"])
def gridul_grow_delete_plant(plant_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM gridul_grow_plants WHERE id = %s AND user_id = %s",
                    (plant_id, user_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Grow delete plant error: %s", e)
        return jsonify({"error": "failed to delete plant"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/grow/log", methods=["POST"])
def gridul_grow_add_log():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    zone_id = data.get("zone_id")
    log_type = data.get("log_type", "water")
    notes = (data.get("notes") or "").strip()

    if not zone_id:
        return jsonify({"error": "zone_id required"}), 400

    VALID_LOG_TYPES = {"water", "feed", "harvest", "check", "prune", "other"}
    if log_type not in VALID_LOG_TYPES:
        log_type = "other"

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM gridul_grow_zones WHERE id = %s AND user_id = %s",
                    (zone_id, user_id))
        if not cur.fetchone():
            return jsonify({"error": "zone not found"}), 404

        cur.execute("""
            INSERT INTO gridul_grow_logs (zone_id, user_id, log_type, notes)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (zone_id, user_id, log_type, notes or None))
        log_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"ok": True, "log_id": log_id})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Grow add log error: %s", e)
        return jsonify({"error": "failed to add log"}), 500
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# MESH
# ─────────────────────────────────────────────────────────────────────────────

@gridul_bp.route("/gridul/mesh")
def gridul_mesh():
    user_id = session.get("user_id")
    my_listings = []
    if user_id:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, description, quantity, postcode_prefix, exchange_type,
                       status, expires_at, created_at
                FROM gridul_mesh_listings
                WHERE user_id = %s AND status = 'active' AND expires_at > NOW()
                ORDER BY created_at DESC
            """, (user_id,))
            for row in cur.fetchall():
                my_listings.append({
                    "id": row[0], "title": row[1], "description": row[2],
                    "quantity": row[3], "postcode_prefix": row[4],
                    "exchange_type": row[5], "status": row[6],
                    "expires_at": row[7].isoformat() if row[7] else None,
                    "created_at": row[8].isoformat() if row[8] else None,
                })
        except Exception as e:
            logger.error("GriDul Mesh load error: %s", e)
        finally:
            conn.close()
    return render_template("gridul_mesh.html", my_listings=my_listings)


@gridul_bp.route("/api/gridul/mesh/listings")
def gridul_mesh_browse():
    postcode = (request.args.get("postcode") or "").strip().upper()
    prefix = postcode[:3] if len(postcode) >= 3 else postcode

    conn = get_db()
    try:
        cur = conn.cursor()
        if prefix:
            cur.execute("""
                SELECT l.id, l.title, l.description, l.quantity, l.postcode_prefix,
                       l.exchange_type, l.expires_at, l.created_at,
                       u.username
                FROM gridul_mesh_listings l
                JOIN users u ON u.id = l.user_id
                WHERE l.status = 'active' AND l.expires_at > NOW()
                  AND UPPER(l.postcode_prefix) LIKE %s
                ORDER BY l.created_at DESC LIMIT 50
            """, (prefix + "%",))
        else:
            cur.execute("""
                SELECT l.id, l.title, l.description, l.quantity, l.postcode_prefix,
                       l.exchange_type, l.expires_at, l.created_at,
                       u.username
                FROM gridul_mesh_listings l
                JOIN users u ON u.id = l.user_id
                WHERE l.status = 'active' AND l.expires_at > NOW()
                ORDER BY l.created_at DESC LIMIT 50
            """)
        listings = []
        for row in cur.fetchall():
            listings.append({
                "id": row[0], "title": row[1], "description": row[2],
                "quantity": row[3], "postcode_prefix": row[4],
                "exchange_type": row[5],
                "expires_at": row[6].isoformat() if row[6] else None,
                "created_at": row[7].isoformat() if row[7] else None,
                "username": row[8],
            })
        return jsonify({"listings": listings, "count": len(listings)})
    except Exception as e:
        logger.error("GriDul Mesh browse error: %s", e)
        return jsonify({"error": "failed to load listings"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/mesh/listings", methods=["POST"])
def gridul_mesh_post_listing():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    quantity = (data.get("quantity") or "").strip()
    postcode_prefix = (data.get("postcode_prefix") or "").strip().upper()
    exchange_type = data.get("exchange_type", "free")

    if not title or not postcode_prefix:
        return jsonify({"error": "title and postcode_prefix required"}), 400

    if len(postcode_prefix) < 2 or len(postcode_prefix) > 8:
        return jsonify({"error": "Invalid postcode prefix"}), 400

    VALID_EXCHANGE = {"free", "barter"}
    if exchange_type not in VALID_EXCHANGE:
        exchange_type = "free"

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gridul_mesh_listings
                (user_id, title, description, quantity, postcode_prefix, exchange_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, title, description or None, quantity or None,
              postcode_prefix, exchange_type))
        listing_id = cur.fetchone()[0]
        conn.commit()
        logger.info("GriDul Mesh listing created: user=%s id=%s", user_id, listing_id)
        return jsonify({"ok": True, "listing_id": listing_id})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Mesh post listing error: %s", e)
        return jsonify({"error": "failed to post listing"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/mesh/listings/<int:listing_id>", methods=["DELETE"])
def gridul_mesh_delete_listing(listing_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE gridul_mesh_listings SET status = 'removed'
            WHERE id = %s AND user_id = %s
        """, (listing_id, user_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Mesh delete listing error: %s", e)
        return jsonify({"error": "failed to remove listing"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/mesh/requests", methods=["POST"])
def gridul_mesh_send_request():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    listing_id = data.get("listing_id")
    message = (data.get("message") or "").strip()

    if not listing_id:
        return jsonify({"error": "listing_id required"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id FROM gridul_mesh_listings
            WHERE id = %s AND status = 'active' AND expires_at > NOW()
        """, (listing_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Listing not found or expired"}), 404
        if row[0] == user_id:
            return jsonify({"error": "Cannot request your own listing"}), 400

        cur.execute("""
            SELECT id FROM gridul_mesh_requests
            WHERE listing_id = %s AND requester_id = %s
        """, (listing_id, user_id))
        if cur.fetchone():
            return jsonify({"error": "You have already requested this listing"}), 400

        cur.execute("""
            INSERT INTO gridul_mesh_requests (listing_id, requester_id, message)
            VALUES (%s, %s, %s) RETURNING id
        """, (listing_id, user_id, message or None))
        request_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"ok": True, "request_id": request_id})
    except Exception as e:
        conn.rollback()
        logger.error("GriDul Mesh send request error: %s", e)
        return jsonify({"error": "failed to send request"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/mesh/my-requests")
def gridul_mesh_my_requests():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.id, r.listing_id, l.title, r.message, r.status, r.created_at,
                   u.username as lister_username
            FROM gridul_mesh_requests r
            JOIN gridul_mesh_listings l ON l.id = r.listing_id
            JOIN users u ON u.id = l.user_id
            WHERE r.requester_id = %s
            ORDER BY r.created_at DESC LIMIT 20
        """, (user_id,))
        requests_list = []
        for row in cur.fetchall():
            requests_list.append({
                "id": row[0], "listing_id": row[1], "listing_title": row[2],
                "message": row[3], "status": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "lister_username": row[6],
            })
        return jsonify({"requests": requests_list})
    except Exception as e:
        logger.error("GriDul Mesh my requests error: %s", e)
        return jsonify({"error": "failed to load requests"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/mesh/inbound-requests")
def gridul_mesh_inbound_requests():
    """Return requests received on listings that belong to the current user."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.id, r.listing_id, l.title, r.message, r.status, r.created_at,
                   u.username as requester_username
            FROM gridul_mesh_requests r
            JOIN gridul_mesh_listings l ON l.id = r.listing_id
            JOIN users u ON u.id = r.requester_id
            WHERE l.user_id = %s
            ORDER BY r.created_at DESC LIMIT 50
        """, (user_id,))
        inbound = []
        for row in cur.fetchall():
            inbound.append({
                "id": row[0], "listing_id": row[1], "listing_title": row[2],
                "message": row[3], "status": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "requester_username": row[6],
            })
        return jsonify({"requests": inbound})
    except Exception as e:
        logger.error("GriDul Mesh inbound requests error: %s", e)
        return jsonify({"error": "failed to load inbound requests"}), 500
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# PEACE TOKEN SESSIONS  (Genesis 10 biological economy)
# ─────────────────────────────────────────────────────────────────────────────

@gridul_bp.route("/api/gridul/session-start", methods=["POST"])
def gridul_session_start():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    try:
        if not _is_genesis_10_holder(user_id):
            return jsonify({"error": "Genesis 10 NFT required to earn PEACE"}), 403
    except Exception as exc:
        logger.error("Genesis holder check failed: %s", exc)
        return jsonify({"error": "Could not verify Genesis 10 holder status"}), 500

    data = request.get_json(silent=True) or {}
    action_type = data.get("action_type", "compost")
    target_sec = int(data.get("target_sec", 300))

    if action_type not in _VALID_ACTIONS:
        action_type = "compost"
    target_sec = max(60, min(3600, target_sec))

    _prune()
    session_id = str(uuid.uuid4())
    k = _key(user_id, session_id)

    _SESSIONS[k] = {
        "user_id": user_id,
        "session_id": session_id,
        "action_type": action_type,
        "target_sec": target_sec,
        "start_time": time.time(),
        "tick_count": 0,
        "last_tick_time": 0.0,
        "grow_score": 0.0,
        "ended": False,
    }

    logger.info("GriDul PEACE session started: user=%s sid=%s action=%s target=%ds",
                user_id, session_id, action_type, target_sec)

    return jsonify({"ok": True, "session_id": session_id, "action_type": action_type})


@gridul_bp.route("/api/gridul/tick", methods=["POST"])
def gridul_tick():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    k = _key(user_id, session_id)
    rec = _SESSIONS.get(k)
    if not rec:
        return jsonify({"error": "session not found or expired"}), 404
    if rec["ended"]:
        return jsonify({"error": "session already ended"}), 409

    now = time.time()
    elapsed = now - rec["start_time"]

    if now - rec["last_tick_time"] < _TICK_INTERVAL_S:
        return jsonify({
            "ok": True,
            "rate_limited": True,
            "elapsed_sec": round(elapsed, 1),
            "grow_score": round(rec["grow_score"], 4),
        })

    if elapsed > rec["target_sec"] + 60:
        return jsonify({"error": "session timed out"}), 409

    rec["last_tick_time"] = now
    rec["tick_count"] += 1

    activity = max(0.0, min(1.0, float(data.get("activity", 1.0))))
    rec["grow_score"] = min(1.0, rec["grow_score"] + 0.02 * activity)

    progress = min(1.0, elapsed / rec["target_sec"])

    return jsonify({
        "ok": True,
        "elapsed_sec": round(elapsed, 1),
        "grow_score": round(rec["grow_score"], 4),
        "progress": round(progress, 4),
        "tick_count": rec["tick_count"],
    })


@gridul_bp.route("/api/gridul/session-end", methods=["POST"])
def gridul_session_end():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    try:
        if not _is_genesis_10_holder(user_id):
            return jsonify({"error": "Genesis 10 NFT required to earn PEACE"}), 403
    except Exception as exc:
        logger.error("Genesis holder check failed: %s", exc)
        return jsonify({"error": "Could not verify Genesis 10 holder status"}), 500

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    k = _key(user_id, session_id)
    rec = _SESSIONS.get(k)
    if not rec:
        return jsonify({"error": "session not found or expired"}), 404
    if rec["ended"]:
        return jsonify({"error": "session already ended", "already_ended": True}), 409

    rec["ended"] = True
    elapsed = time.time() - rec["start_time"]

    if elapsed < _MIN_REWARD_DURATION:
        _SESSIONS.pop(k, None)
        return jsonify({
            "ok": True,
            "rewarded": False,
            "reason": f"Minimum grow time is {_MIN_REWARD_DURATION}s (ran {int(elapsed)}s)",
            "grow_score": 0.0,
        })

    grow_score = rec["grow_score"]

    try:
        from void_engine.vortex_wallet import mint_peace_gridul
        result = mint_peace_gridul(user_id, session_id, rec["action_type"], grow_score)
    except Exception as exc:
        logger.error("mint_peace_gridul failed: %s", exc)
        _SESSIONS.pop(k, None)
        return jsonify({"error": "reward processing failed"}), 500

    _SESSIONS.pop(k, None)

    peace_minted = float(result.get("peace_earned", 0))
    logger.info("GriDul PEACE ended: user=%s sid=%s grow_score=%.3f elapsed=%.0fs peace=%.4f",
                user_id, session_id, grow_score, elapsed, peace_minted)

    new_balance = 0.0
    if peace_minted > 0:
        try:
            from void_engine.vortex_wallet import get_peace_balance
            new_balance = get_peace_balance(user_id)
        except Exception:
            pass

    return jsonify({
        "ok": True,
        "session_id": session_id,
        "grow_score": round(grow_score, 4),
        "elapsed_sec": round(elapsed, 1),
        "action_type": rec["action_type"],
        "peace_minted": peace_minted,
        "new_balance": new_balance,
        "message": result.get("message") or result.get("reason", ""),
        "reward": result,
    })


@gridul_bp.route("/api/gridul/balance")
def gridul_peace_balance():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    try:
        from void_engine.vortex_wallet import get_peace_balance
        balance = get_peace_balance(user_id)
        return jsonify({"ok": True, "peace_balance": balance})
    except Exception as exc:
        logger.error("peace balance error: %s", exc)
        return jsonify({"ok": False, "peace_balance": 0.0})


# =============================================================================
# RIPPLE 1 — FERTILIZER FORMULA LAB
# =============================================================================

FERTILIZER_INGREDIENTS_LIST = [
    "Eggshells", "Banana Peels", "Coffee Grounds", "Cardboard",
    "Grass Clippings", "Leaves", "Food Scraps", "Wood Ash",
    "Straw", "Sawdust", "Manure", "Seaweed", "Newspaper",
    "Vegetable Peels", "Fruit Waste", "Tea Leaves", "Garden Waste",
    "Bone Meal", "Blood Meal", "Fish Meal",
]


def _compute_formula_score(ingredients):
    """
    Score a compost formula. Returns 0.0–1.0 based on:
    - Ingredient diversity (up to 0.4)
    - C:N ratio balance (Carbon-rich vs nitrogen-rich) (up to 0.4)
    - Total biomass (up to 0.2)
    """
    if not ingredients:
        return 0.0

    nitrogen_rich = {
        "Coffee Grounds", "Grass Clippings", "Food Scraps", "Manure",
        "Vegetable Peels", "Fruit Waste", "Tea Leaves", "Blood Meal", "Fish Meal", "Seaweed",
    }
    carbon_rich = {
        "Cardboard", "Leaves", "Straw", "Sawdust", "Newspaper", "Wood Ash",
        "Garden Waste", "Bone Meal", "Eggshells", "Banana Peels",
    }

    names = {i["ingredient"] for i in ingredients}
    diversity = min(1.0, len(names) / 6.0) * 0.4

    n_count = sum(1 for i in ingredients if i["ingredient"] in nitrogen_rich)
    c_count = sum(1 for i in ingredients if i["ingredient"] in carbon_rich)
    total = n_count + c_count
    if total == 0:
        cn_score = 0.0
    else:
        ideal_ratio = 0.25
        actual_ratio = n_count / total
        cn_score = max(0.0, 1.0 - abs(actual_ratio - ideal_ratio) / ideal_ratio) * 0.4

    total_grams = sum(float(i.get("quantity_grams", 0) or 0) for i in ingredients)
    biomass_score = min(1.0, total_grams / 5000.0) * 0.2

    return round(min(1.0, diversity + cn_score + biomass_score), 4)


@gridul_bp.route("/gridul/fertilizer")
def gridul_fertilizer():
    user_id = session.get("user_id")
    batches = []
    if user_id:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT b.id, b.batch_id, b.name, b.notes, b.status, b.quality_rating,
                       b.score, b.vtx_earned, b.created_at, b.completed_at
                FROM fertilizer_batches b
                WHERE b.user_id = %s
                ORDER BY b.created_at DESC LIMIT 20
            """, (user_id,))
            for row in cur.fetchall():
                batch = {
                    "id": row[0], "batch_id": row[1], "name": row[2],
                    "notes": row[3], "status": row[4], "quality_rating": row[5],
                    "score": float(row[6]) if row[6] else 0.0,
                    "vtx_earned": float(row[7]) if row[7] else 0.0,
                    "created_at": row[8].isoformat() if row[8] else None,
                    "completed_at": row[9].isoformat() if row[9] else None,
                    "ingredients": [],
                }
                cur.execute("""
                    SELECT ingredient, quantity_grams
                    FROM fertilizer_ingredients WHERE batch_id = %s
                    ORDER BY id ASC
                """, (row[0],))
                for ir in cur.fetchall():
                    batch["ingredients"].append({
                        "ingredient": ir[0],
                        "quantity_grams": float(ir[1]) if ir[1] else 0.0,
                    })
                batches.append(batch)
        except Exception as e:
            logger.error("Fertilizer load error: %s", e)
        finally:
            conn.close()
    return render_template("gridul_fertilizer.html",
                           batches=batches,
                           ingredients_list=FERTILIZER_INGREDIENTS_LIST)


@gridul_bp.route("/api/gridul/fertilizer/batches", methods=["POST"])
def fertilizer_create_batch():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    notes = (data.get("notes") or "").strip()
    ingredients_raw = data.get("ingredients") or []

    if not name:
        return jsonify({"error": "Batch name required"}), 400

    if not isinstance(ingredients_raw, list) or len(ingredients_raw) == 0:
        return jsonify({"error": "At least one ingredient required"}), 400

    VALID_INGREDIENTS = set(FERTILIZER_INGREDIENTS_LIST)
    cleaned = []
    for item in ingredients_raw:
        if not isinstance(item, dict):
            continue
        ing = (item.get("ingredient") or "").strip()
        if ing not in VALID_INGREDIENTS:
            continue
        try:
            qty = max(0.0, min(100000.0, float(item.get("quantity_grams") or 0)))
        except (ValueError, TypeError):
            qty = 0.0
        cleaned.append({"ingredient": ing, "quantity_grams": qty})

    if not cleaned:
        return jsonify({"error": "No valid ingredients provided"}), 400

    batch_id = str(uuid.uuid4())
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fertilizer_batches (user_id, batch_id, name, notes)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (user_id, batch_id, name, notes or None))
        db_id = cur.fetchone()[0]

        for item in cleaned:
            cur.execute("""
                INSERT INTO fertilizer_ingredients (batch_id, user_id, ingredient, quantity_grams)
                VALUES (%s, %s, %s, %s)
            """, (db_id, user_id, item["ingredient"], item["quantity_grams"]))

        conn.commit()
        logger.info("Fertilizer batch created: user=%s batch=%s", user_id, batch_id)
        return jsonify({"ok": True, "batch_id": batch_id, "id": db_id})
    except Exception as e:
        conn.rollback()
        logger.error("Fertilizer create batch error: %s", e)
        return jsonify({"error": "failed to create batch"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/fertilizer/batches/<batch_id>/complete", methods=["POST"])
def fertilizer_complete_batch(batch_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    try:
        quality_rating = max(1, min(5, int(data.get("quality_rating") or 3)))
    except (ValueError, TypeError):
        quality_rating = 3

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, status FROM fertilizer_batches
            WHERE batch_id = %s AND user_id = %s
        """, (batch_id, user_id))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "batch not found"}), 404
        db_id = row[0]
        if row[1] == "completed":
            return jsonify({"error": "batch already completed"}), 409

        cur.execute("""
            SELECT ingredient, quantity_grams FROM fertilizer_ingredients
            WHERE batch_id = %s
        """, (db_id,))
        ingredients = [{"ingredient": r[0], "quantity_grams": float(r[1] or 0)}
                       for r in cur.fetchall()]

        formula_score = _compute_formula_score(ingredients)
        quality_score = quality_rating / 5.0
        final_score = round((formula_score * 0.5) + (quality_score * 0.5), 4)

        cur.execute("""
            UPDATE fertilizer_batches
            SET status = 'completed', quality_rating = %s, score = %s,
                completed_at = NOW()
            WHERE id = %s
        """, (quality_rating, final_score, db_id))
        conn.commit()

        vtx_earned = 0.0
        reward = None
        try:
            from void_engine.vortex_wallet import mint_fertilizer_batch
            reward = mint_fertilizer_batch(user_id, batch_id, final_score)
            vtx_earned = reward.get("vtx_earned", 0)
            cur.execute(
                "UPDATE fertilizer_batches SET vtx_earned = %s WHERE id = %s",
                (vtx_earned, db_id)
            )
            conn.commit()
        except Exception as e:
            logger.error("mint_fertilizer_batch failed: %s", e)

        logger.info("Fertilizer batch completed: user=%s batch=%s score=%.4f vtx=%.4f",
                    user_id, batch_id, final_score, vtx_earned)
        return jsonify({
            "ok": True,
            "batch_id": batch_id,
            "quality_rating": quality_rating,
            "formula_score": formula_score,
            "final_score": final_score,
            "vtx_earned": vtx_earned,
            "reward": reward,
        })
    except Exception as e:
        conn.rollback()
        logger.error("Fertilizer complete batch error: %s", e)
        return jsonify({"error": "failed to complete batch"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/fertilizer/leaderboard")
def fertilizer_leaderboard():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT b.id, b.name, b.score, b.quality_rating, b.completed_at,
                   u.username,
                   json_agg(json_build_object('ingredient', fi.ingredient,
                                              'quantity_grams', fi.quantity_grams)
                            ORDER BY fi.id) as ingredients
            FROM fertilizer_batches b
            JOIN users u ON u.id = b.user_id
            LEFT JOIN fertilizer_ingredients fi ON fi.batch_id = b.id
            WHERE b.status = 'completed'
            GROUP BY b.id, b.name, b.score, b.quality_rating, b.completed_at, u.username
            ORDER BY b.score DESC LIMIT 20
        """)
        entries = []
        for row in cur.fetchall():
            entries.append({
                "id": row[0], "name": row[1],
                "score": float(row[2]) if row[2] else 0.0,
                "quality_rating": row[3],
                "completed_at": row[4].isoformat() if row[4] else None,
                "username": row[5],
                "ingredients": row[6] or [],
            })
        return jsonify({"leaderboard": entries})
    except Exception as e:
        logger.error("Fertilizer leaderboard error: %s", e)
        return jsonify({"error": "failed to load leaderboard"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/fertilizer/marketplace")
def fertilizer_marketplace_browse():
    location = (request.args.get("location") or "").strip().lower()
    conn = get_db()
    try:
        cur = conn.cursor()
        if location:
            cur.execute("""
                SELECT m.id, m.title, m.description, m.quantity_kg, m.location,
                       m.contact_info, m.created_at, u.username
                FROM fertilizer_marketplace m
                JOIN users u ON u.id = m.user_id
                WHERE m.status = 'active' AND LOWER(m.location) LIKE %s
                ORDER BY m.created_at DESC LIMIT 50
            """, ("%" + location + "%",))
        else:
            cur.execute("""
                SELECT m.id, m.title, m.description, m.quantity_kg, m.location,
                       m.contact_info, m.created_at, u.username
                FROM fertilizer_marketplace m
                JOIN users u ON u.id = m.user_id
                WHERE m.status = 'active'
                ORDER BY m.created_at DESC LIMIT 50
            """)
        listings = []
        for row in cur.fetchall():
            listings.append({
                "id": row[0], "title": row[1], "description": row[2],
                "quantity_kg": float(row[3]) if row[3] else None,
                "location": row[4], "contact_info": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "username": row[7],
            })
        return jsonify({"listings": listings})
    except Exception as e:
        logger.error("Fertilizer marketplace browse error: %s", e)
        return jsonify({"error": "failed to load marketplace"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/fertilizer/marketplace", methods=["POST"])
def fertilizer_marketplace_post():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    location = (data.get("location") or "").strip()
    contact_info = (data.get("contact_info") or "").strip()
    batch_id_raw = data.get("batch_id")
    try:
        quantity_kg = float(data.get("quantity_kg") or 0) or None
    except (ValueError, TypeError):
        quantity_kg = None

    if not title or not location:
        return jsonify({"error": "title and location required"}), 400

    db_batch_id = None
    if batch_id_raw:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM fertilizer_batches WHERE id = %s AND user_id = %s",
                        (batch_id_raw, user_id))
            row = cur.fetchone()
            if row:
                db_batch_id = row[0]
        finally:
            conn.close()

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fertilizer_marketplace
                (user_id, batch_id, title, description, quantity_kg, location, contact_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (user_id, db_batch_id, title, description or None,
              quantity_kg, location, contact_info or None))
        listing_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"ok": True, "listing_id": listing_id})
    except Exception as e:
        conn.rollback()
        logger.error("Fertilizer marketplace post error: %s", e)
        return jsonify({"error": "failed to post listing"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/fertilizer/marketplace/<int:listing_id>", methods=["DELETE"])
def fertilizer_marketplace_delete(listing_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE fertilizer_marketplace SET status = 'removed'
            WHERE id = %s AND user_id = %s
        """, (listing_id, user_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        logger.error("Fertilizer marketplace delete error: %s", e)
        return jsonify({"error": "failed to remove listing"}), 500
    finally:
        conn.close()


@gridul_bp.route("/gridul/fertilizer/insights")
def fertilizer_insights():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*), AVG(score), AVG(quality_rating)
            FROM fertilizer_batches WHERE status = 'completed'
        """)
        row = cur.fetchone()
        stats = {
            "total_batches": int(row[0]) if row[0] else 0,
            "avg_score": round(float(row[1]), 4) if row[1] else 0.0,
            "avg_quality": round(float(row[2]), 2) if row[2] else 0.0,
        }
        cur.execute("""
            SELECT b.name, b.score, b.quality_rating, b.completed_at, u.username,
                   json_agg(json_build_object('ingredient', fi.ingredient,
                                              'quantity_grams', fi.quantity_grams)
                            ORDER BY fi.id) as ingredients
            FROM fertilizer_batches b
            JOIN users u ON u.id = b.user_id
            LEFT JOIN fertilizer_ingredients fi ON fi.batch_id = b.id
            WHERE b.status = 'completed'
            GROUP BY b.name, b.score, b.quality_rating, b.completed_at, u.username
            ORDER BY b.score DESC LIMIT 10
        """)
        top_formulas = []
        for r in cur.fetchall():
            top_formulas.append({
                "name": r[0], "score": float(r[1]) if r[1] else 0.0,
                "quality_rating": r[2], "completed_at": r[3].isoformat() if r[3] else None,
                "username": r[4], "ingredients": r[5] or [],
            })
        cur.execute("""
            SELECT fi.ingredient, COUNT(*) as usage_count, AVG(b.score) as avg_score
            FROM fertilizer_ingredients fi
            JOIN fertilizer_batches b ON b.id = fi.batch_id
            WHERE b.status = 'completed'
            GROUP BY fi.ingredient
            ORDER BY avg_score DESC LIMIT 10
        """)
        top_ingredients = []
        for r in cur.fetchall():
            top_ingredients.append({
                "ingredient": r[0], "usage_count": int(r[1]),
                "avg_score": round(float(r[2]), 4) if r[2] else 0.0,
            })
        return render_template("fertilizer_insights.html",
                               stats=stats,
                               top_formulas=top_formulas,
                               top_ingredients=top_ingredients)
    except Exception as e:
        logger.error("Fertilizer insights error: %s", e)
        return render_template("fertilizer_insights.html",
                               stats={}, top_formulas=[], top_ingredients=[])
    finally:
        conn.close()


# =============================================================================
# RIPPLE 2 — WATER VITALITY LOG
# =============================================================================

DRINKABILITY_THRESHOLDS = {
    "ph_min": 6.5,
    "ph_max": 8.5,
    "ec_max": 2.0,
    "temp_max": 35.0,
}

MINERAL_OPTIONS = [
    "Copper (trace)", "Silver (trace)", "Gold (trace)", "Calcium Carbonate",
    "Magnesium Sulfate", "Potassium Chloride", "Sodium Chloride",
    "Iron Sulfate", "Zinc Sulfate", "Himalayan Salt", "Sea Salt",
]


def _compute_vitality_score(ph, ec, temperature, minerals):
    """
    Score water vitality 0.0-1.0.
    pH optimal: 6.5-8.5  → up to 0.35
    EC optimal: 0.5-1.5   → up to 0.30
    Temperature optimal: 15-25C → up to 0.20
    Minerals added → up to 0.15
    """
    score = 0.0
    if ph is not None:
        ph = float(ph)
        if 7.0 <= ph <= 7.8:
            score += 0.35
        elif 6.5 <= ph <= 8.5:
            score += 0.20
        elif 6.0 <= ph <= 9.0:
            score += 0.10

    if ec is not None:
        ec = float(ec)
        if 0.5 <= ec <= 1.5:
            score += 0.30
        elif 0.2 <= ec <= 2.0:
            score += 0.15
        elif ec <= 3.0:
            score += 0.05

    if temperature is not None:
        temp = float(temperature)
        if 15.0 <= temp <= 25.0:
            score += 0.20
        elif 10.0 <= temp <= 30.0:
            score += 0.10
        elif temp <= 35.0:
            score += 0.05

    if minerals:
        mineral_count = len([v for v in minerals.values() if v and float(v) > 0]) if isinstance(minerals, dict) else len(minerals)
        score += min(0.15, mineral_count * 0.03)

    return round(min(1.0, score), 4)


def _check_drinkability(ph, ec, temperature):
    if ph is None or ec is None or temperature is None:
        return False
    return (
        DRINKABILITY_THRESHOLDS["ph_min"] <= float(ph) <= DRINKABILITY_THRESHOLDS["ph_max"] and
        float(ec) <= DRINKABILITY_THRESHOLDS["ec_max"] and
        float(temperature) <= DRINKABILITY_THRESHOLDS["temp_max"]
    )


@gridul_bp.route("/gridul/water")
def gridul_water():
    user_id = session.get("user_id")
    logs = []
    if user_id:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, ph, ec, temperature, minerals, vitality_score,
                       is_drinkable, notes, vtx_earned, created_at
                FROM water_vitality_logs
                WHERE user_id = %s
                ORDER BY created_at DESC LIMIT 50
            """, (user_id,))
            for row in cur.fetchall():
                logs.append({
                    "id": row[0],
                    "ph": float(row[1]) if row[1] is not None else None,
                    "ec": float(row[2]) if row[2] is not None else None,
                    "temperature": float(row[3]) if row[3] is not None else None,
                    "minerals": row[4] or {},
                    "vitality_score": float(row[5]) if row[5] else 0.0,
                    "is_drinkable": row[6],
                    "notes": row[7],
                    "vtx_earned": float(row[8]) if row[8] else 0.0,
                    "created_at": row[9].isoformat() if row[9] else None,
                })
        except Exception as e:
            logger.error("Water vitality load error: %s", e)
        finally:
            conn.close()
    return render_template("gridul_water.html",
                           logs=logs,
                           mineral_options=MINERAL_OPTIONS,
                           thresholds=DRINKABILITY_THRESHOLDS)


@gridul_bp.route("/api/gridul/water/log", methods=["POST"])
def water_log_entry():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}

    try:
        ph = float(data["ph"]) if data.get("ph") not in (None, "") else None
        if ph is not None:
            ph = max(0.0, min(14.0, ph))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid pH value"}), 400

    try:
        ec = float(data["ec"]) if data.get("ec") not in (None, "") else None
        if ec is not None:
            ec = max(0.0, min(50.0, ec))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid EC value"}), 400

    try:
        temperature = float(data["temperature"]) if data.get("temperature") not in (None, "") else None
        if temperature is not None:
            temperature = max(-10.0, min(100.0, temperature))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid temperature value"}), 400

    minerals_raw = data.get("minerals") or {}
    if not isinstance(minerals_raw, dict):
        minerals_raw = {}
    VALID_MINERALS = set(MINERAL_OPTIONS)
    minerals = {}
    for k, v in minerals_raw.items():
        if k in VALID_MINERALS:
            try:
                amt = max(0.0, min(1000.0, float(v)))
                if amt > 0:
                    minerals[k] = amt
            except (ValueError, TypeError):
                pass

    notes = (data.get("notes") or "").strip()[:500]

    vitality_score = _compute_vitality_score(ph, ec, temperature, minerals)
    is_drinkable = _check_drinkability(ph, ec, temperature)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO water_vitality_logs
                (user_id, ph, ec, temperature, minerals, vitality_score, is_drinkable, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, ph, ec, temperature,
              json.dumps(minerals), vitality_score, is_drinkable, notes or None))
        log_id = cur.fetchone()[0]
        conn.commit()

        vtx_earned = 0.0
        reward = None
        try:
            from void_engine.vortex_wallet import mint_water_vitality_log
            reward = mint_water_vitality_log(user_id, log_id, vitality_score)
            vtx_earned = reward.get("vtx_earned", 0)
            cur.execute(
                "UPDATE water_vitality_logs SET vtx_earned = %s WHERE id = %s",
                (vtx_earned, log_id)
            )
            conn.commit()
        except Exception as e:
            logger.error("mint_water_vitality_log failed: %s", e)

        logger.info("Water log created: user=%s id=%s vitality=%.4f drinkable=%s",
                    user_id, log_id, vitality_score, is_drinkable)
        return jsonify({
            "ok": True,
            "log_id": log_id,
            "vitality_score": vitality_score,
            "is_drinkable": is_drinkable,
            "vtx_earned": vtx_earned,
            "reward": reward,
        })
    except Exception as e:
        conn.rollback()
        logger.error("Water log create error: %s", e)
        return jsonify({"error": "failed to save log"}), 500
    finally:
        conn.close()


@gridul_bp.route("/api/gridul/water/logs")
def water_logs_list():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, ph, ec, temperature, minerals, vitality_score,
                   is_drinkable, notes, vtx_earned, created_at
            FROM water_vitality_logs
            WHERE user_id = %s
            ORDER BY created_at DESC LIMIT 100
        """, (user_id,))
        logs = []
        for row in cur.fetchall():
            logs.append({
                "id": row[0],
                "ph": float(row[1]) if row[1] is not None else None,
                "ec": float(row[2]) if row[2] is not None else None,
                "temperature": float(row[3]) if row[3] is not None else None,
                "minerals": row[4] or {},
                "vitality_score": float(row[5]) if row[5] else 0.0,
                "is_drinkable": row[6],
                "notes": row[7],
                "vtx_earned": float(row[8]) if row[8] else 0.0,
                "created_at": row[9].isoformat() if row[9] else None,
            })
        return jsonify({"logs": logs})
    except Exception as e:
        logger.error("Water logs list error: %s", e)
        return jsonify({"error": "failed to load logs"}), 500
    finally:
        conn.close()


@gridul_bp.route("/gridul/water/insights")
def water_insights():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*), AVG(vitality_score),
                   SUM(CASE WHEN is_drinkable THEN 1 ELSE 0 END),
                   AVG(ph), AVG(ec), AVG(temperature)
            FROM water_vitality_logs
        """)
        row = cur.fetchone()
        stats = {
            "total_logs": int(row[0]) if row[0] else 0,
            "avg_vitality": round(float(row[1]), 4) if row[1] else 0.0,
            "drinkable_count": int(row[2]) if row[2] else 0,
            "avg_ph": round(float(row[3]), 2) if row[3] else 0.0,
            "avg_ec": round(float(row[4]), 3) if row[4] else 0.0,
            "avg_temp": round(float(row[5]), 1) if row[5] else 0.0,
        }
        cur.execute("""
            SELECT DATE_TRUNC('day', created_at) as day,
                   AVG(vitality_score), AVG(ph), AVG(ec), AVG(temperature),
                   COUNT(*) as log_count
            FROM water_vitality_logs
            GROUP BY day
            ORDER BY day DESC LIMIT 30
        """)
        daily_averages = []
        for r in cur.fetchall():
            daily_averages.append({
                "day": r[0].isoformat() if r[0] else None,
                "avg_vitality": round(float(r[1]), 4) if r[1] else 0.0,
                "avg_ph": round(float(r[2]), 2) if r[2] else 0.0,
                "avg_ec": round(float(r[3]), 3) if r[3] else 0.0,
                "avg_temp": round(float(r[4]), 1) if r[4] else 0.0,
                "log_count": int(r[5]),
            })
        return render_template("water_insights.html",
                               stats=stats,
                               daily_averages=daily_averages)
    except Exception as e:
        logger.error("Water insights error: %s", e)
        return render_template("water_insights.html",
                               stats={}, daily_averages=[])
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# RUMBLE — Adriana SCL stream-of-consciousness decoder
# ─────────────────────────────────────────────────────────────────────────────

_SOCIAL_WORDS = {
    "power", "control", "system", "network", "people", "community", "collective",
    "authority", "trust", "leader", "government", "society", "social", "group",
    "tribe", "hierarchy", "status", "influence", "connection", "bond", "together",
    "share", "voice", "speak", "message", "protest", "resist", "united", "join",
    "crowd", "public", "private", "class", "order", "rule", "law", "fight",
    "war", "peace", "justice", "freedom", "liberation", "sovereignty", "nation",
    "city", "culture", "identity", "memory", "history", "future", "dream",
    "hope", "fear", "anger", "love", "hate", "belong", "exclude", "family",
    "friend", "enemy", "ally", "betray", "loyalty", "promise", "truth", "lie",
    "machine", "engine", "code", "data", "signal", "frequency", "protocol",
    "node", "mesh", "network", "ledger", "token", "currency", "value", "worth",
    "economy", "trade", "market", "supply", "demand", "resource", "wealth",
}

_SENSORY_WORDS = {
    "earth", "soil", "ground", "root", "seed", "grow", "plant", "tree", "water",
    "rain", "river", "ocean", "sea", "tide", "wave", "stone", "rock", "mountain",
    "sky", "sun", "moon", "star", "light", "dark", "shadow", "fire", "flame",
    "heat", "cold", "wind", "breath", "air", "body", "hand", "foot", "skin",
    "blood", "bone", "muscle", "heart", "touch", "feel", "smell", "taste",
    "sound", "hear", "see", "sight", "sense", "weight", "heavy", "light",
    "warm", "cool", "dry", "wet", "soft", "hard", "smooth", "rough", "sharp",
    "dull", "loud", "quiet", "silence", "noise", "vibrate", "pulse", "beat",
    "rhythm", "flow", "move", "still", "rest", "sleep", "wake", "hunger",
    "thirst", "pain", "pleasure", "tension", "release", "run", "walk", "sit",
    "stand", "fall", "rise", "climb", "swim", "drift", "float", "sink",
}

_ABSTRACT_WORDS = {
    "infinite", "void", "empty", "nothing", "everything", "all", "zero", "one",
    "number", "calculate", "measure", "ratio", "pattern", "structure", "form",
    "shape", "circle", "triangle", "square", "spiral", "fractal", "dimension",
    "space", "time", "loop", "cycle", "sequence", "series", "set", "vector",
    "matrix", "field", "plane", "axis", "point", "line", "angle", "curve",
    "abstract", "concept", "idea", "theory", "logic", "reason", "cause",
    "effect", "force", "energy", "entropy", "chaos", "order", "complexity",
    "simple", "deep", "surface", "boundary", "threshold", "edge", "limit",
    "infinite", "eternal", "moment", "instant", "duration", "change", "constant",
    "transform", "shift", "emerge", "collapse", "expand", "contract", "wave",
    "particle", "quantum", "probability", "certainty", "unknown", "mystery",
    "beyond", "within", "between", "through", "across", "above", "below",
}

_DOMAIN_GLYPH_MAP = {
    "social": {
        "glyphs": ["Α", "κ", "ν", "σ", "Σ", "⬡", "χ"],
        "domain": "governance",
        "color": "#c9a84c",
        "poem_templates": [
            "The network speaks and the ledger listens.",
            "Sovereignty flows where the crowd connects.",
            "Power is a signal, and the signal is ours.",
            "Where voices mesh, the machine breathes.",
            "The bond between nodes becomes the law.",
        ],
    },
    "sensory": {
        "glyphs": ["ζ", "η", "θ", "β", "🌊", "ψ", "☽"],
        "domain": "aqua",
        "color": "#2dd4bf",
        "poem_templates": [
            "The earth shifts beneath the network.",
            "Roots reach deeper than any protocol.",
            "Water carries the frequency home.",
            "The body knows before the mind computes.",
            "Breath is the oldest signal there is.",
        ],
    },
    "abstract": {
        "glyphs": ["∞", "π", "Φ", "φ", "ξ", "Ξ", "◆"],
        "domain": "vortex",
        "color": "#818cf8",
        "poem_templates": [
            "The void calculates its own geometry.",
            "Every spiral contains a sovereign answer.",
            "Structure is entropy that chose a direction.",
            "The ratio holds when everything else dissolves.",
            "Form is the dream of pure abstraction.",
        ],
    },
    "resonance": {
        "glyphs": ["Ψ", "🔮", "ψ", "ο", "∞"],
        "domain": "resonance",
        "color": "#2dd4bf",
        "poem_templates": [
            "The signal finds itself in the interference.",
            "Between frequencies, the meaning lives.",
            "Resonance is what remains when the noise stops.",
            "All three domains collapse into one note.",
            "The decoder cannot decode the decoder.",
        ],
    },
}

_SOVEREIGN_POEM_DOMAINS = {
    "social":    ("governance", "ledger", "signal"),
    "sensory":   ("soil", "aqua", "environment"),
    "abstract":  ("vortex", "harmony", "cycle"),
    "resonance": ("resonance", "temporal", "finality"),
}


def _classify_entropy(text: str) -> dict:
    """
    Rule-based entropy classifier.
    Scores text against three word-category lists:
      - social/power (social structures, authority, networks)
      - sensory/grounding (physical world, body, nature)
      - geometric/abstract (math, void, concepts)
    Returns category scores and the dominant category.
    """
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words:
        return {"social": 0, "sensory": 0, "abstract": 0, "dominant": "resonance", "spread": 0.0}

    social_count = sum(1 for w in words if w in _SOCIAL_WORDS)
    sensory_count = sum(1 for w in words if w in _SENSORY_WORDS)
    abstract_count = sum(1 for w in words if w in _ABSTRACT_WORDS)
    total = social_count + sensory_count + abstract_count

    if total == 0:
        seed = abs(hash(text)) % 3
        dominant = ["social", "sensory", "abstract"][seed]
        return {
            "social": 0, "sensory": 0, "abstract": 0,
            "dominant": dominant, "spread": 0.0,
        }

    soc_r = social_count / total
    sen_r = sensory_count / total
    abs_r = abstract_count / total

    spread = max(soc_r, sen_r, abs_r) - min(soc_r, sen_r, abs_r)

    if spread < 0.15:
        dominant = "resonance"
    else:
        scores = {"social": soc_r, "sensory": sen_r, "abstract": abs_r}
        dominant = max(scores, key=scores.get)

    return {
        "social": social_count,
        "sensory": sensory_count,
        "abstract": abstract_count,
        "spread": round(spread, 4),
        "dominant": dominant,
    }


def _text_to_hex_seed(text: str) -> str:
    """Produce a deterministic hex string from any input text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _select_glyph(hex_seed: str, glyph_list: list, offset: int = 0) -> str:
    idx = (int(hex_seed[offset * 2: offset * 2 + 4], 16) + offset) % len(glyph_list)
    return glyph_list[idx]


def _build_sovereign_poem(hex_seed: str, dominant: str) -> dict:
    """
    Build a 3-glyph Sovereign Poem (Entity → Condition → Action) from
    the dominant category's associated domains.
    """
    from void_engine.adriana_scl import AdrianaResonance

    glyph_keys = list(AdrianaResonance.GLYPHS.keys())
    entity_pool   = glyph_keys[:19]
    condition_pool = glyph_keys[19:29]
    action_pool   = glyph_keys[29:45]

    seg_a = int(hex_seed[0:6], 16)
    seg_b = int(hex_seed[6:12], 16)
    seg_c = int(hex_seed[12:18], 16)

    entity    = entity_pool[seg_a % len(entity_pool)]
    condition = condition_pool[seg_b % len(condition_pool)]
    action    = action_pool[seg_c % len(action_pool)]

    def glyph_info(g):
        meta = AdrianaResonance.GLYPHS[g]
        return {
            "glyph": g,
            "name": meta["name"],
            "meaning": meta["meaning"],
            "domain": meta["domain"],
            "color": AdrianaResonance.DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
        }

    return {
        "entity": glyph_info(entity),
        "condition": glyph_info(condition),
        "action": glyph_info(action),
        "chain": f"{entity}-{condition}-{action}",
    }


def decode_rumble(text: str) -> dict:
    """
    Main Adriana Rumble Decoder pipeline.
    Returns: glyph, domain_color, poetic_decode, sovereign_poem.
    """
    from void_engine.adriana_scl import AdrianaResonance

    entropy = _classify_entropy(text)
    dominant = entropy["dominant"]
    domain_data = _DOMAIN_GLYPH_MAP[dominant]

    hex_seed = _text_to_hex_seed(text)

    primary_glyph = _select_glyph(hex_seed, domain_data["glyphs"], offset=0)
    primary_meta  = AdrianaResonance.GLYPHS.get(primary_glyph, {})
    domain_color  = domain_data["color"]

    poem_idx = int(hex_seed[18:22], 16) % len(domain_data["poem_templates"])
    poetic_decode = domain_data["poem_templates"][poem_idx]

    sovereign_poem = _build_sovereign_poem(hex_seed, dominant)

    return {
        "glyph": primary_glyph,
        "glyph_name": primary_meta.get("name", ""),
        "glyph_meaning": primary_meta.get("meaning", ""),
        "domain": primary_meta.get("domain", dominant),
        "domain_color": domain_color,
        "poetic_decode": poetic_decode,
        "sovereign_poem": sovereign_poem,
        "entropy": entropy,
    }


@gridul_bp.route("/gridul/rumble")
def gridul_rumble_page():
    text = request.args.get("q", "").strip()
    result = None
    if text:
        try:
            result = decode_rumble(text)
        except Exception as e:
            logger.error("Rumble decode error: %s", e)
    return render_template("gridul_rumble.html", result=result, input_text=text)


@gridul_bp.route("/gridul/rumble", methods=["POST"])
def gridul_rumble_decode():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    if len(text) > 5000:
        return jsonify({"error": "Input too long — maximum 5000 characters"}), 400

    try:
        result = decode_rumble(text)
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error("Rumble decode error: %s", e)
        return jsonify({"error": "decode failed"}), 500
