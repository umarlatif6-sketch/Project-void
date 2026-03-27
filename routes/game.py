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
