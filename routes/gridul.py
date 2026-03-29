"""
GriDul — Community Mesh Module
================================
Three pillars:
  1. GriDul Move  — daily calisthenics movement tracker (earns VTX)
  2. GriDul Grow  — home aquaponics planner (up to 3 zones)
  3. GriDul Mesh  — neighbourhood food exchange (postcode-based, no money)

Genesis 10 PEACE token sessions:
  - POST /api/gridul/session-start  — register a biological grow/compost session
  - POST /api/gridul/tick           — report progress
  - POST /api/gridul/session-end    — finalise and mint PEACE tokens
"""

import json
import logging
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
