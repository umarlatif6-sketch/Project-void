"""
VOID Plane — Star Map & Territory System
==========================================
A full-screen SVG star map showing the VOID constellation as fixed navigation stars,
with claimable territory zones between them. Zones are earned via VTX, maintained
through activity, and resonate based on the owner's engagement across the platform.

Seven stars correspond to the seven VOID crystallization layers:
  Ground · Language · Memory · Value · Community · Healing · Legacy
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, jsonify, session, request
from void_engine.db_pool import get_db
from routes.auth import login_required

logger = logging.getLogger(__name__)

plane_bp = Blueprint("plane", __name__)

ZONE_CLAIM_COST = 25.0

CRYSTALLIZATION_SENTENCE = (
    "In the ground of language, memory holds value — "
    "community heals the legacy."
)

CONSTELLATION_STARS = [
    {
        "id": "ground",
        "layer": 1,
        "name": "Ground",
        "x": 200,
        "y": 500,
        "description": "The foundation. Physical sovereignty, body, earth.",
        "page": "/gridul",
        "color": "#92400e",
    },
    {
        "id": "language",
        "layer": 2,
        "name": "Language",
        "x": 420,
        "y": 200,
        "description": "The code. Adriana SCL, sovereign naming, glyph systems.",
        "page": "/gridul/rumble",
        "color": "#818cf8",
    },
    {
        "id": "memory",
        "layer": 3,
        "name": "Memory",
        "x": 700,
        "y": 150,
        "description": "The archive. Chronicle, steganography, hidden history.",
        "page": "/chronicle",
        "color": "#60a5fa",
    },
    {
        "id": "value",
        "layer": 4,
        "name": "Value",
        "x": 950,
        "y": 320,
        "description": "The ledger. VTX economy, Blueprint tokens, VTX wallet.",
        "page": "/marketplace",
        "color": "#c9a84c",
    },
    {
        "id": "community",
        "layer": 5,
        "name": "Community",
        "x": 880,
        "y": 580,
        "description": "The mesh. GriDul network, messenger, neighbourhood exchange.",
        "page": "/gridul/mesh",
        "color": "#2dd4bf",
    },
    {
        "id": "healing",
        "layer": 6,
        "name": "Healing",
        "x": 580,
        "y": 720,
        "description": "The restoration. Water vitality, movement, aquaponics.",
        "page": "/gridul/water",
        "color": "#4caf50",
    },
    {
        "id": "legacy",
        "layer": 7,
        "name": "Legacy",
        "x": 300,
        "y": 680,
        "description": "The continuity. Sovereign Node, Genesis 10, founder archive.",
        "page": "/genesis",
        "color": "#e879f9",
    },
]

ZONE_SEEDS = [
    ("Ashveil", [(260,390),(350,340),(430,380),(390,460),(290,470)]),
    ("Thornmere", [(350,340),(430,380),(520,310),(460,240),(390,270)]),
    ("Dunbrace", [(430,380),(520,310),(610,360),(560,440),(470,450)]),
    ("Callowen", [(460,240),(520,310),(610,360),(650,270),(570,190)]),
    ("Erewhon", [(570,190),(650,270),(750,220),(720,160),(660,140)]),
    ("Veldthorn", [(650,270),(750,220),(840,260),(820,340),(730,350)]),
    ("Skaldrift", [(750,220),(840,260),(920,230),(900,160),(810,145)]),
    ("Normark", [(840,260),(920,230),(980,290),(960,370),(870,380)]),
    ("Cinderhollow", [(820,340),(870,380),(960,370),(1000,450),(890,470)]),
    ("Duskwall", [(730,350),(820,340),(890,470),(820,530),(730,510)]),
    ("Fenwraith", [(560,440),(610,360),(730,350),(730,510),(650,540)]),
    ("Greymount", [(470,450),(560,440),(650,540),(620,620),(530,620)]),
    ("Ashenford", [(390,460),(470,450),(530,620),(470,680),(380,650)]),
    ("Brackenvast", [(290,470),(390,460),(380,650),(300,650),(240,580)]),
    ("Mirefall", [(200,500),(290,470),(240,580),(200,580),(180,540)]),
    ("Stonewatch", [(180,380),(260,390),(290,470),(200,500),(160,460)]),
    ("Ironveil", [(180,380),(260,390),(350,340),(320,270),(240,280)]),
    ("Coldthorn", [(320,270),(350,340),(460,240),(440,170),(360,160)]),
    ("Wraithspur", [(360,160),(440,170),(570,190),(560,140),(450,120)]),
    ("Bloodmere", [(450,120),(560,140),(660,140),(680,90),(560,80)]),
    ("Gildenscar", [(560,80),(680,90),(810,145),(800,80),(680,60)]),
    ("Ashenvault", [(800,80),(810,145),(900,160),(930,100),(850,70)]),
    ("Nighthollow", [(930,100),(900,160),(980,290),(1020,230),(1000,130)]),
    ("Emberglass", [(1000,130),(1020,230),(980,290),(1060,340),(1050,240)]),
    ("Thornvast", [(960,370),(1060,340),(1100,430),(1050,510),(980,490)]),
    ("Valdris", [(1000,450),(1100,430),(1100,520),(1010,580),(980,490)]),
    ("Siltmere", [(890,470),(1000,450),(980,490),(920,540),(870,530)]),
    ("Driftmere", [(820,530),(890,470),(920,540),(870,600),(800,610)]),
    ("Coldmere", [(730,510),(820,530),(800,610),(730,630),(680,600)]),
    ("Grimholt", [(650,540),(730,510),(730,630),(680,680),(600,670)]),
    ("Fenwatch", [(620,620),(650,540),(680,680),(650,730),(590,730)]),
    ("Bramblekeep", [(530,620),(620,620),(590,730),(540,750),(480,720)]),
    ("Morvane", [(470,680),(530,620),(480,720),(430,740),(390,700)]),
    ("Ashford", [(380,650),(470,680),(390,700),(340,730),(310,680)]),
    ("Coldbrook", [(300,650),(380,650),(340,730),(290,730),(260,680)]),
    ("Duskreach", [(240,580),(300,650),(260,680),(220,660),(200,610)]),
    ("Stonecroft", [(200,580),(240,580),(220,660),(190,650),(180,600)]),
    ("Greywold", [(160,460),(200,500),(200,580),(180,560),(150,510)]),
    ("Ashwood", [(150,400),(180,380),(160,460),(140,450),(130,410)]),
    ("Mistfall", [(130,410),(140,450),(150,510),(120,490),(110,440)]),
    ("Veilmark", [(110,440),(120,490),(180,600),(150,620),(100,560)]),
    ("Thornwick", [(100,560),(150,620),(190,650),(160,680),(100,640)]),
    ("Irongate", [(100,640),(160,680),(220,660),(200,710),(140,710)]),
    ("Darkhollow", [(200,710),(220,660),(260,680),(290,730),(240,730)]),
    ("Bleakwood", [(240,730),(290,730),(340,730),(320,770),(270,770)]),
    ("Ashfall", [(320,770),(340,730),(430,740),(430,790),(370,800)]),
    ("Coldvast", [(430,790),(430,740),(480,720),(510,760),(480,800)]),
    ("Driftveil", [(480,800),(510,760),(540,750),(570,780),(530,810)]),
    ("Grimwood", [(530,810),(570,780),(590,730),(650,730),(620,780)]),
    ("Wraithvault", [(620,780),(650,730),(680,680),(730,680),(710,740)]),
    ("Stonehaven", [(710,740),(730,680),(800,610),(830,650),(790,700)]),
    ("Nightfall", [(790,700),(830,650),(870,600),(920,640),(880,690)]),
    ("Embervast", [(880,690),(920,640),(1010,580),(1020,650),(960,700)]),
    ("Valdrift", [(960,700),(1020,650),(1100,520),(1110,600),(1060,660)]),
    ("Ashenveil", [(1060,660),(1110,600),(1110,680),(1060,730),(1010,700)]),
    ("Coldmark", [(1010,700),(1060,730),(1040,780),(980,760),(990,710)]),
    ("Dunscar", [(980,760),(1040,780),(1020,830),(960,810),(970,760)]),
]


def init_plane_tables():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS void_plane_zones (
                id SERIAL PRIMARY KEY,
                zone_key TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                polygon_coords JSONB NOT NULL,
                owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                claimed_at TIMESTAMPTZ,
                resonance_score NUMERIC(6,4) DEFAULT 0,
                dungeon_description TEXT,
                dungeon_published BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
        logger.info("void_plane_zones table created/verified")
        _seed_zones(conn)
    except Exception as e:
        conn.rollback()
        logger.error("Plane table init failed: %s", e)
    finally:
        conn.close()


def _seed_zones(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM void_plane_zones")
        count = cur.fetchone()[0]
        if count >= len(ZONE_SEEDS):
            return
        for name, coords in ZONE_SEEDS:
            zone_key = name.lower().replace(" ", "_")
            cur.execute("""
                INSERT INTO void_plane_zones (zone_key, name, polygon_coords)
                VALUES (%s, %s, %s)
                ON CONFLICT (zone_key) DO NOTHING
            """, (zone_key, name, __import__('json').dumps(coords)))
        conn.commit()
        logger.info("Seeded %d VOID Plane zones", len(ZONE_SEEDS))
    except Exception as e:
        conn.rollback()
        logger.error("Zone seeding failed: %s", e)


def _calculate_resonance(user_id, conn):
    """Calculate a resonance score for a user based on recent activity across the app."""
    try:
        import json
        cur = conn.cursor()
        score = 0.0
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        try:
            cur.execute("""
                SELECT COUNT(*) FROM vortex_ledger
                WHERE (from_user_id = %s OR to_user_id = %s)
                AND timestamp > %s
            """, (user_id, user_id, cutoff))
            row = cur.fetchone()
            if row:
                score += min(float(row[0]) * 0.5, 30.0)
        except Exception:
            pass

        try:
            cur.execute("""
                SELECT COUNT(*) FROM gridul_move_sessions
                WHERE user_id = %s AND completed = TRUE AND created_at > %s
            """, (user_id, cutoff))
            row = cur.fetchone()
            if row:
                score += min(float(row[0]) * 2.0, 20.0)
        except Exception:
            pass

        try:
            cur.execute("""
                SELECT COUNT(*) FROM gridul_mesh_listings
                WHERE user_id = %s AND created_at > %s
            """, (user_id, cutoff))
            row = cur.fetchone()
            if row:
                score += min(float(row[0]) * 3.0, 15.0)
        except Exception:
            pass

        try:
            cur.execute("""
                SELECT COUNT(*) FROM token_ownership
                WHERE owner_id = %s
            """, (user_id,))
            row = cur.fetchone()
            if row:
                score += min(float(row[0]) * 1.0, 10.0)
        except Exception:
            pass

        try:
            cur.execute("""
                SELECT COUNT(*) FROM messages
                WHERE sender_id = %s AND created_at > %s
            """, (user_id, cutoff))
            row = cur.fetchone()
            if row:
                score += min(float(row[0]) * 0.3, 15.0)
        except Exception:
            pass

        try:
            cur.execute("""
                SELECT COUNT(*) FROM water_vitality_logs
                WHERE user_id = %s AND created_at > %s
            """, (user_id, cutoff))
            row = cur.fetchone()
            if row:
                score += min(float(row[0]) * 2.0, 10.0)
        except Exception:
            pass

        score = min(score, 100.0)
        return round(score, 4)
    except Exception as e:
        logger.error("Resonance calculation error for user %s: %s", user_id, e)
        return 0.0


@plane_bp.route("/plane")
def plane_page():
    user_id = session.get("user_id")
    username = session.get("username", "")
    display_name = session.get("display_name", "")
    vtx_balance = 0.0
    user_zones = []

    if user_id:
        try:
            from void_engine.vortex_wallet import get_balance
            vtx_balance = get_balance(user_id)
        except Exception as e:
            logger.error("VTX balance error: %s", e)

        try:
            conn = get_db()
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT z.id, z.name, z.zone_key, z.resonance_score,
                           z.dungeon_description, z.dungeon_published
                    FROM void_plane_zones z
                    WHERE z.owner_id = %s
                    ORDER BY z.claimed_at ASC
                """, (user_id,))
                for row in cur.fetchall():
                    user_zones.append({
                        "id": row[0],
                        "name": row[1],
                        "zone_key": row[2],
                        "resonance_score": float(row[3] or 0),
                        "dungeon_description": row[4] or "",
                        "dungeon_published": row[5],
                    })
            finally:
                conn.close()
        except Exception as e:
            logger.error("User zones error: %s", e)

    return render_template(
        "plane.html",
        stars=CONSTELLATION_STARS,
        crystallization=CRYSTALLIZATION_SENTENCE,
        vtx_balance=vtx_balance,
        user_id=user_id,
        username=username,
        display_name=display_name,
        user_zones=user_zones,
        zone_claim_cost=ZONE_CLAIM_COST,
    )


@plane_bp.route("/api/plane/zones")
def api_plane_zones():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT z.id, z.zone_key, z.name, z.polygon_coords,
                   z.owner_id, u.username, u.display_name,
                   z.claimed_at, z.resonance_score,
                   z.dungeon_description, z.dungeon_published
            FROM void_plane_zones z
            LEFT JOIN users u ON u.id = z.owner_id
            ORDER BY z.id ASC
        """)
        zones = []
        owner_ids_seen = {}
        user_id = session.get("user_id")

        for row in cur.fetchall():
            zone_id, zone_key, name, polygon_coords, owner_id, username, display_name, \
                claimed_at, resonance_score, dungeon_description, dungeon_published = row

            zones.append({
                "id": zone_id,
                "zone_key": zone_key,
                "name": name,
                "polygon": polygon_coords if isinstance(polygon_coords, list) else [],
                "owner_id": owner_id,
                "owner_username": username or None,
                "owner_display_name": display_name or username or None,
                "claimed_at": claimed_at.isoformat() if claimed_at else None,
                "resonance_score": float(resonance_score or 0),
                "dungeon_description": dungeon_description or None,
                "dungeon_published": dungeon_published or False,
                "is_mine": (owner_id == user_id) if user_id else False,
            })

        return jsonify({"zones": zones, "stars": CONSTELLATION_STARS})
    except Exception as e:
        logger.error("Plane zones API error: %s", e)
        return jsonify({"error": "Failed to load zones"}), 500
    finally:
        conn.close()


@plane_bp.route("/api/plane/claim", methods=["POST"])
@login_required
def api_plane_claim():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    zone_key = (data.get("zone_key") or "").strip()

    if not zone_key:
        return jsonify({"error": "zone_key required"}), 400

    from void_engine.vortex_wallet import get_balance
    balance = get_balance(user_id)
    if balance < ZONE_CLAIM_COST:
        return jsonify({
            "error": f"Insufficient VTX. You need {ZONE_CLAIM_COST} VTX to claim a zone.",
            "balance": balance,
            "cost": ZONE_CLAIM_COST,
        }), 402

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, owner_id, name FROM void_plane_zones
            WHERE zone_key = %s FOR UPDATE
        """, (zone_key,))
        row = cur.fetchone()

        if not row:
            return jsonify({"error": "Zone not found"}), 404

        zone_id, owner_id, zone_name = row

        if owner_id is not None:
            return jsonify({"error": "Zone is already claimed"}), 409

        resonance = _calculate_resonance(user_id, conn)

        cur.execute("""
            UPDATE void_plane_zones
            SET owner_id = %s, claimed_at = NOW(), resonance_score = %s, updated_at = NOW()
            WHERE id = %s
        """, (user_id, resonance, zone_id))

        cur.execute("""
            UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) - %s
            WHERE id = %s
        """, (ZONE_CLAIM_COST, user_id))

        try:
            from void_engine.vortex_wallet import _get_last_block, _create_block
            cur.execute(
                "INSERT INTO vortex_ledger (block_index, previous_hash, tx_type, from_user_id, to_user_id, amount, block_hash, phase_key_signature, node_id) "
                "VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                ("0" * 72, "plane_claim", user_id, None, ZONE_CLAIM_COST, "0" * 72, "0" * 32, "plane")
            )
        except Exception:
            pass

        conn.commit()

        new_balance = get_balance(user_id)
        return jsonify({
            "ok": True,
            "zone_key": zone_key,
            "zone_name": zone_name,
            "vtx_spent": ZONE_CLAIM_COST,
            "new_balance": new_balance,
            "resonance_score": resonance,
        })
    except Exception as e:
        conn.rollback()
        logger.error("Plane claim error: %s", e)
        return jsonify({"error": "Claim failed"}), 500
    finally:
        conn.close()


@plane_bp.route("/api/plane/dungeon", methods=["POST"])
@login_required
def api_plane_dungeon():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    zone_key = (data.get("zone_key") or "").strip()
    description = (data.get("description") or "").strip()[:1000]
    publish = bool(data.get("publish", False))

    if not zone_key:
        return jsonify({"error": "zone_key required"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE void_plane_zones
            SET dungeon_description = %s, dungeon_published = %s, updated_at = NOW()
            WHERE zone_key = %s AND owner_id = %s
            RETURNING id
        """, (description, publish, zone_key, user_id))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Zone not found or not yours"}), 404
        conn.commit()
        return jsonify({"ok": True, "published": publish})
    except Exception as e:
        conn.rollback()
        logger.error("Dungeon update error: %s", e)
        return jsonify({"error": "Update failed"}), 500
    finally:
        conn.close()


@plane_bp.route("/api/plane/resonance/refresh", methods=["POST"])
@login_required
def api_plane_resonance_refresh():
    user_id = session["user_id"]
    conn = get_db()
    try:
        resonance = _calculate_resonance(user_id, conn)
        cur = conn.cursor()
        cur.execute("""
            UPDATE void_plane_zones
            SET resonance_score = %s, updated_at = NOW()
            WHERE owner_id = %s
        """, (resonance, user_id))
        conn.commit()
        return jsonify({"ok": True, "resonance_score": resonance})
    except Exception as e:
        conn.rollback()
        logger.error("Resonance refresh error: %s", e)
        return jsonify({"error": "Refresh failed"}), 500
    finally:
        conn.close()
