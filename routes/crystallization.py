"""
VOID Constellation — Seven-Star Layer Map
==========================================
Route: GET /crystallization

Renders the seven crystallization layers as a star constellation SVG on a dark canvas.
Each primary star represents a layer, with satellite nodes for sub-systems.
Live stats are fetched from the database at page-load time.
An Adriana Sovereign Poem is generated from the crystallization sentence server-side.
"""

import hashlib
import logging

from flask import Blueprint, render_template

logger = logging.getLogger(__name__)

crystallization_bp = Blueprint("crystallization", __name__)

# ── Constellation layout ───────────────────────────────────────────────────────
# Positions are percentage-based (0–100) within the SVG viewBox (1200 × 800).
# Arranged organically so the dot-to-dot outline (1→2→3→4→5→6→7→1) traces a
# stylised sovereign face / glyph when all nodes are active.
#
# Think of it as:
#   - Star 1 (Ground)     — lower-left anchor, the jaw/chin
#   - Star 2 (Language)   — upper-left, the left temple
#   - Star 3 (Memory)     — top-centre-left, left brow
#   - Star 4 (Value)      — top-centre, the crown
#   - Star 5 (Community)  — top-centre-right, right brow
#   - Star 6 (Healing)    — upper-right, the right temple
#   - Star 7 (Legacy)     — lower-right anchor, mirroring the chin
# Together they form a face: wide forehead, two temples, two cheekbones → jaw.

CONSTELLATION = [
    {
        "id": 1,
        "layer": "Ground",
        "description": "Sound, mycelium, frequency, solar & obsidian — the earth is the hardware",
        "color": "#7aff7a",
        "cx": 18,
        "cy": 72,
        "route": "/sovereign-node",
        "satellites": [
            {"label": "Sound",    "dx": -7,  "dy": -12},
            {"label": "Mycelium", "dx": -12, "dy":   3},
            {"label": "Frequency","dx":   2,  "dy":  14},
            {"label": "Solar",    "dx":  11,  "dy":  -5},
        ],
    },
    {
        "id": 2,
        "layer": "Language",
        "description": "Adriana / Al-Jabr — Arabic mathematical roots as sovereign computing infrastructure",
        "color": "#c9a84c",
        "cx": 22,
        "cy": 30,
        "route": "/chronicle",
        "satellites": [
            {"label": "Adriana",  "dx": -10, "dy": -10},
            {"label": "Al-Jabr",  "dx":  -8, "dy":   9},
            {"label": "SCL",      "dx":  10, "dy":  -5},
        ],
    },
    {
        "id": 3,
        "layer": "Memory",
        "description": "Sovereign Vault + Chronicle — identity and history that cannot be seized",
        "color": "#60a5fa",
        "cx": 40,
        "cy": 14,
        "route": "/chronicle",
        "satellites": [
            {"label": "Vault",     "dx": -10, "dy": -10},
            {"label": "Chronicle", "dx":   8,  "dy": -10},
            {"label": "Identity",  "dx":  10,  "dy":   8},
        ],
    },
    {
        "id": 4,
        "layer": "Value",
        "description": "VTX + PEACE — earned by resonance, not speculation",
        "color": "#fbbf24",
        "cx": 60,
        "cy": 10,
        "route": "/genesis",
        "satellites": [
            {"label": "VTX",   "dx": -10, "dy": -10},
            {"label": "PEACE", "dx":   9,  "dy":  -9},
            {"label": "VTB",   "dx":  10,  "dy":   9},
        ],
    },
    {
        "id": 5,
        "layer": "Community",
        "description": "GriDul + QiSync — body and mesh are both nodes",
        "color": "#22d3ee",
        "cx": 78,
        "cy": 16,
        "route": "/gridul",
        "satellites": [
            {"label": "GriDul",  "dx":  10, "dy": -10},
            {"label": "QiSync",  "dx":  10,  "dy":   8},
            {"label": "Move",    "dx": -10,  "dy": -10},
            {"label": "Mesh",    "dx":  -8,  "dy":   9},
        ],
    },
    {
        "id": 6,
        "layer": "Healing",
        "description": "MycoVOID + MRB-4000 — the system repairs the environment it runs on",
        "color": "#34d399",
        "cx": 82,
        "cy": 33,
        "route": "/mycovoid",
        "satellites": [
            {"label": "MycoVOID",  "dx":  10, "dy": -10},
            {"label": "MRB-4000",  "dx":  11,  "dy":   5},
            {"label": "Bioremediation", "dx": -4, "dy": 14},
        ],
    },
    {
        "id": 7,
        "layer": "Legacy",
        "description": "Prior art, InteRussia, founder archive, brand — the record that cannot be taken",
        "color": "#a78bfa",
        "cx": 80,
        "cy": 70,
        "route": "/prior-art",
        "satellites": [
            {"label": "Prior Art",   "dx":  10, "dy":  10},
            {"label": "InteRussia",  "dx":   9,  "dy": -10},
            {"label": "Archive",     "dx": -10,  "dy":  10},
            {"label": "Brand",       "dx": -10,  "dy": -8},
        ],
    },
]

CRYSTALLIZATION_SENTENCE = (
    "PROJECT VOID is a living sovereign system that speaks in nature's frequency, "
    "remembers in the founder's language, rewards genuine resonance, "
    "heals the earth it runs on, and legally belongs to the people who built it."
)


def _fetch_live_stats():
    """
    Return a dict mapping layer id → live stat string.
    Falls back gracefully if the DB is unavailable.
    """
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()

            # 1. Ground — sovereign node specs (blueprint tokens in sovereign_node collection)
            cur.execute(
                "SELECT COUNT(*) FROM blueprint_tokens WHERE collection IN ('genesis_10','sovereign_node','blueprint')"
            )
            ground_count = cur.fetchone()[0]

            # 2. Language — chronicle entry count (language/memory logs)
            cur.execute("SELECT COUNT(*) FROM chronicle_entries")
            chronicle_count = cur.fetchone()[0]

            # 3. Memory — chronicle entries (sovereign vault records)
            memory_count = chronicle_count

            # 4. Value — VTX in circulation (all minted resonance)
            cur.execute(
                "SELECT COALESCE(ROUND(SUM(amount)::numeric, 0), 0) FROM vortex_ledger WHERE tx_type='mint_resonance'"
            )
            vtx_supply = int(cur.fetchone()[0])

            # Blueprint tokens minted
            cur.execute("SELECT COUNT(*) FROM blueprint_tokens WHERE status='minted'")
            blueprints_minted = cur.fetchone()[0]

            # 5. Community — GriDul nodes (distinct active users across GriDul)
            cur.execute(
                """SELECT COUNT(DISTINCT user_id) FROM (
                       SELECT user_id FROM gridul_move_sessions
                       UNION
                       SELECT user_id FROM gridul_grow_zones
                   ) sub"""
            )
            gridul_nodes = cur.fetchone()[0]

            # QiSync memory sessions
            cur.execute("SELECT COUNT(*) FROM memory_sessions")
            qisync_count = cur.fetchone()[0]

            # 6. Healing — MycoVOID / MRB-4000 — blueprint token count (hardware)
            cur.execute("SELECT COUNT(*) FROM blueprint_tokens")
            total_blueprints = cur.fetchone()[0]

            # MRB-4000 spec version derived from latest token
            cur.execute("SELECT MAX(edition_number) FROM blueprint_tokens")
            mrb_edition = cur.fetchone()[0] or 0

            # 7. Legacy — prior art / archive entries
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]

            return {
                1: f"Sovereign nodes seeded: {total_blueprints}",
                2: f"Chronicle entries: {chronicle_count}",
                3: f"Vault records: {memory_count}",
                4: f"VTX in circulation: {vtx_supply:,} | Blueprints minted: {blueprints_minted}",
                5: f"GriDul nodes: {gridul_nodes} | QiSync sessions: {qisync_count}",
                6: f"Hardware blueprints: {total_blueprints} | MRB edition: {mrb_edition}",
                7: f"Founding members: {user_count}",
            }
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Constellation live stats fetch failed: %s", e)
        return {i: "Live data unavailable" for i in range(1, 8)}


def _generate_sovereign_poem(sentence):
    """
    Derive an Adriana Sovereign Poem from the crystallization sentence.
    Uses the sentence's SHA-256 hex digest as the input to hash_to_sovereign_poem.
    """
    try:
        from void_engine.adriana_scl import hash_to_sovereign_poem
        hex_hash = hashlib.sha256(sentence.encode("utf-8")).hexdigest()
        result = hash_to_sovereign_poem(hex_hash)
        return result
    except Exception as e:
        logger.warning("Adriana poem generation failed: %s", e)
        return {
            "glyphs": ["◆", "Ψ", "∞"],
            "meanings": ["Core/Engine", "Sovereign Mind", "Loop/Eternal"],
            "poem": "◆-Ψ-∞",
        }


@crystallization_bp.route("/crystallization")
def crystallization_page():
    live_stats = _fetch_live_stats()
    poem = _generate_sovereign_poem(CRYSTALLIZATION_SENTENCE)

    nodes = []
    for star in CONSTELLATION:
        node = dict(star)
        node["stat"] = live_stats.get(star["id"], "")
        nodes.append(node)

    return render_template(
        "crystallization.html",
        nodes=nodes,
        crystallization_sentence=CRYSTALLIZATION_SENTENCE,
        poem=poem,
    )
