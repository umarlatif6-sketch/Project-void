import logging
from flask import Blueprint, request, jsonify, session, render_template
from routes.auth import login_required
from void_engine.geography_nft import (
    get_unclaimed_geographies,
    get_claimed_geographies,
    mint_geography,
    GEOGRAPHY_MINT_COST,
)

logger = logging.getLogger(__name__)
geography_bp = Blueprint("geography", __name__)

_PAGE_SIZE = 50


@geography_bp.route("/geographies")
@login_required
def geographies_page():
    user_id = session["user_id"]
    return render_template(
        "geographies.html",
        user_id=user_id,
        mint_cost=float(GEOGRAPHY_MINT_COST),
    )


@geography_bp.route("/api/geography/unclaimed")
@login_required
def api_unclaimed():
    user_id = session["user_id"]
    try:
        offset = max(0, int(request.args.get("offset", 0)))
        limit = min(max(1, int(request.args.get("limit", _PAGE_SIZE))), _PAGE_SIZE)
        items = get_unclaimed_geographies(user_id, limit=limit + 1, offset=offset)
        has_more = len(items) > limit
        return jsonify({
            "unclaimed": items[:limit],
            "count": len(items[:limit]),
            "offset": offset,
            "has_more": has_more,
        })
    except Exception as e:
        logger.error("Unclaimed geographies error: %s", e)
        return jsonify({"error": "Failed to load unclaimed geographies"}), 500


@geography_bp.route("/api/geography/claimed")
@login_required
def api_claimed():
    user_id = session["user_id"]
    try:
        offset = max(0, int(request.args.get("offset", 0)))
        limit = min(max(1, int(request.args.get("limit", _PAGE_SIZE))), _PAGE_SIZE)
        items = get_claimed_geographies(user_id, limit=limit + 1, offset=offset)
        has_more = len(items) > limit
        return jsonify({
            "claimed": items[:limit],
            "count": len(items[:limit]),
            "offset": offset,
            "has_more": has_more,
        })
    except Exception as e:
        logger.error("Claimed geographies error: %s", e)
        return jsonify({"error": "Failed to load claimed geographies"}), 500


@geography_bp.route("/api/geography/mint", methods=["POST"])
@login_required
def api_mint():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}
    ledger_hash = (data.get("ledger_hash") or "").strip()
    phase = (data.get("phase") or "").strip()
    if not ledger_hash:
        return jsonify({"error": "ledger_hash required"}), 400
    try:
        result = mint_geography(user_id, ledger_hash, phase)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Geography mint route error: %s", e)
        return jsonify({"error": "Mint failed"}), 500
