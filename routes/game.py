import logging
from flask import Blueprint, render_template, request, jsonify, session
from routes.auth import login_required
from void_engine.vortex_wallet import mint_game_reward, get_game_stats

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
    return render_template(
        "game.html",
        username=username,
        user_tier=user_tier,
        stats=stats,
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
