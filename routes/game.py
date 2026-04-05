import logging
from flask import Blueprint, render_template, request, jsonify, session
from routes.auth import login_required
from void_engine.vortex_wallet import (
    mint_game_reward,
    get_game_stats,
    spend_on_equipment,
    get_inventory,
    get_earning_multiplier,
    EQUIPMENT_CATALOG,
)

logger = logging.getLogger(__name__)

game_bp = Blueprint("game", __name__)

VALID_EVENTS = {"vault_discovered", "glyph_solved", "node_built", "level_up"}


@game_bp.route("/game")
@login_required
def game_page():
    user_id = session.get("user_id")
    username = session.get("username", "")
    user_tier = session.get("tier", "ghost")
    stats = get_game_stats(user_id)
    inventory = get_inventory(user_id)
    multiplier = float(get_earning_multiplier(user_id))
    return render_template(
        "game.html",
        username=username,
        user_tier=user_tier,
        stats=stats,
        inventory=inventory,
        multiplier=multiplier,
    )


@game_bp.route("/game/shop")
@login_required
def game_shop():
    user_id = session.get("user_id")
    username = session.get("username", "")
    stats = get_game_stats(user_id)
    inventory = get_inventory(user_id)
    catalog = []
    for slug, item in EQUIPMENT_CATALOG.items():
        catalog.append({
            "slug": slug,
            "name": item["name"],
            "vtx_price": float(item["vtx_price"]),
            "multiplier": float(item["multiplier"]),
            "description": item["description"],
            "icon": item["icon"],
            "tier": item["tier"],
            "unlocks": item["unlocks"],
            "owned": slug in inventory,
        })
    catalog.sort(key=lambda x: x["tier"])
    multiplier = float(get_earning_multiplier(user_id))
    return render_template(
        "game_shop.html",
        username=username,
        stats=stats,
        catalog=catalog,
        inventory=inventory,
        multiplier=multiplier,
    )


@game_bp.route("/api/game/reward", methods=["POST"])
@login_required
def game_reward():
    user_id = session.get("user_id")
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json(silent=True) or {}
    event_type = data.get("event_type", "").strip()
    event_id = data.get("event_id")

    if event_type not in VALID_EVENTS:
        return jsonify({"error": f"Invalid event_type: {event_type}"}), 400

    try:
        result = mint_game_reward(user_id, event_type, event_id=event_id)
    except Exception as exc:
        logger.exception("Game reward mint failed for user %s event %s: %s", user_id, event_type, exc)
        return jsonify({"error": "Internal error processing reward"}), 500

    if "error" in result:
        return jsonify(result), 400

    if result.get("already_minted"):
        stats = get_game_stats(user_id)
        return jsonify({"already_minted": True, "stats": stats}), 200

    if result.get("cap_reached"):
        stats = get_game_stats(user_id)
        result["stats"] = stats
        return jsonify(result), 200

    stats = get_game_stats(user_id)

    if stats.get("nodes_built", 0) + stats.get("vaults_opened", 0) + stats.get("glyphs_solved", 0) >= stats.get("level", 1) * 3:
        try:
            level_result = mint_game_reward(user_id, "level_up", event_id=f"level_{stats['level'] + 1}")
            if "vtx_earned" in level_result:
                from void_engine.db_pool import get_db
                conn = get_db()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE users SET game_level = COALESCE(game_level, 1) + 1 WHERE id = %s",
                        (user_id,),
                    )
                    conn.commit()
                finally:
                    conn.close()
                stats = get_game_stats(user_id)
                result["level_up"] = level_result
        except Exception as exc:
            logger.warning("Level-up reward failed: %s", exc)

    result["stats"] = stats
    return jsonify(result), 200


@game_bp.route("/api/game/equip", methods=["POST"])
@login_required
def game_equip():
    user_id = session.get("user_id")
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json(silent=True) or {}
    slug = data.get("equipment_slug", "").strip()

    if not slug:
        return jsonify({"error": "equipment_slug required"}), 400

    try:
        result = spend_on_equipment(user_id, slug)
    except Exception as exc:
        logger.exception("Equipment purchase failed for user %s slug %s: %s", user_id, slug, exc)
        return jsonify({"error": "Internal error processing purchase"}), 500

    if "error" in result:
        status = 400
        if result["error"] == "insufficient_vtx":
            status = 402
        return jsonify(result), status

    stats = get_game_stats(user_id)
    result["stats"] = stats
    return jsonify(result), 200


@game_bp.route("/api/game/inventory")
@login_required
def game_inventory_api():
    user_id = session.get("user_id")
    try:
        inventory = get_inventory(user_id)
        multiplier = float(get_earning_multiplier(user_id))
        stats = get_game_stats(user_id)
        return jsonify({"inventory": inventory, "multiplier": multiplier, "stats": stats}), 200
    except Exception as exc:
        logger.exception("Inventory fetch failed: %s", exc)
        return jsonify({"error": "Could not fetch inventory"}), 500


@game_bp.route("/api/game/stats")
@login_required
def game_stats_api():
    user_id = session.get("user_id")
    try:
        stats = get_game_stats(user_id)
        return jsonify(stats), 200
    except Exception as exc:
        logger.exception("Game stats fetch failed: %s", exc)
        return jsonify({"error": "Could not fetch stats"}), 500


VALID_YS_MILESTONES = {
    "first_vault": {
        "chapter": 100,
        "title": "Young Sovereign — First Vault",
        "subtitle": "VOID-Station Milestone: First Discovery",
        "glyph_sequence": "◆-α-⭐",
        "body_template": (
            "Young Sovereign {username} opened their first Vault on {date}.\n\n"
            "The VOID-Station console recorded this moment in the sovereign ledger. "
            "A child stepped into the VOID and found something real — a signal waiting in the dark. "
            "This is how every great explorer begins."
        ),
    },
    "first_glyph": {
        "chapter": 101,
        "title": "Young Sovereign — First Glyph Touched",
        "subtitle": "VOID-Station Milestone: First Resonance",
        "glyph_sequence": "◆-λ-✨",
        "body_template": (
            "Young Sovereign {username} touched their first Glyph on {date}.\n\n"
            "A sovereign symbol glowed for the first time under a child's hand. "
            "The Adriana Protocol registered the resonance: a new voice has entered the SCL. "
            "The glyph remembers who first awoke it."
        ),
    },
    "first_save": {
        "chapter": 102,
        "title": "Young Sovereign — First Save to Chronicle",
        "subtitle": "VOID-Station Milestone: The Living Ledger Grows",
        "glyph_sequence": "◆-σ-📖",
        "body_template": (
            "Young Sovereign {username} made their first save to the Chronicle on {date}.\n\n"
            "The sovereign ledger accepted a child's first mark. "
            "From this day forward, the Chronicle carries their name — not as a user, "
            "but as a sovereign presence in the VOID. "
            "The record is immutable. The memory is alive."
        ),
    },
    "five_vaults": {
        "chapter": 103,
        "title": "Young Sovereign — Five Vaults Found",
        "subtitle": "VOID-Station Milestone: Explorer Rising",
        "glyph_sequence": "◆-γ-🌟",
        "body_template": (
            "Young Sovereign {username} discovered their fifth Vault on {date}.\n\n"
            "Five signals pulled from the void. Five moments of discovery. "
            "The Chronicle grows with every sovereign step a child takes in this realm. "
            "The VOID-Station console noted: the young explorer's resonance is strengthening."
        ),
    },
    "ten_vaults": {
        "chapter": 104,
        "title": "Young Sovereign — Ten Vaults, Legend Status",
        "subtitle": "VOID-Station Milestone: Sovereign Explorer",
        "glyph_sequence": "◆-Ψ-💎",
        "body_template": (
            "Young Sovereign {username} reached ten Vaults discovered on {date}.\n\n"
            "Ten sovereign signals collected. The VOID-Station console recognized a Legend. "
            "This child has proven that the realm is navigable — that the void yields its secrets "
            "to those who are patient, curious, and brave enough to explore. "
            "The ledger is updated. The name is written. The Chronicle remembers."
        ),
    },
}


@game_bp.route("/api/game/young-sovereign/milestone", methods=["POST"])
@login_required
def young_sovereign_milestone():
    user_id = session.get("user_id")
    username = session.get("username", "Sovereign")

    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json(silent=True) or {}
    milestone_key = data.get("milestone", "").strip()

    if milestone_key not in VALID_YS_MILESTONES:
        return jsonify({"error": "Invalid milestone"}), 400

    ms = VALID_YS_MILESTONES[milestone_key]

    try:
        from datetime import date
        today = date.today().strftime("%B %d, %Y")
        body = ms["body_template"].format(username=username, date=today)

        from void_engine.chronicle_adriana import post_chronicle_entry
        result = post_chronicle_entry(
            ms["chapter"],
            ms["title"],
            ms["subtitle"],
            ms["glyph_sequence"],
            body,
            user_id,
        )

        if "error" in result:
            logger.error("Young Sovereign chronicle entry failed: %s", result["error"])
            return jsonify({"error": "Chronicle write failed", "detail": result["error"]}), 500

        return jsonify({
            "success": True,
            "milestone": milestone_key,
            "chronicle_entry": ms["title"],
            "entry_id": result.get("id"),
        }), 200

    except Exception as exc:
        logger.exception("Young Sovereign milestone failed for user %s milestone %s: %s", user_id, milestone_key, exc)
        return jsonify({"error": "Internal error"}), 500
