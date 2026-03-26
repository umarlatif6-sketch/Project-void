import os
import logging
from flask import Blueprint, request, jsonify, session, redirect, render_template
from routes.auth import login_required, _check_rate_limit
from routes.stripe_client import get_stripe_client
from void_engine.db_pool import get_db
from void_engine.blueprint_nft import (
    get_marketplace_listings,
    get_user_collection,
    get_user_collection_extended,
    get_token_detail,
    get_manufacturing_fund_status,
    purchase_token_vtx,
    purchase_token_fiat,
    get_pending_yield,
    claim_yield,
    list_token_for_sale,
    unlist_token,
    purchase_secondary,
    offer_token_for_rent,
    book_rental,
    end_rental,
    get_secondary_listings,
    get_rental_offers,
    get_mystery_price,
    buy_mystery_token,
    reveal_mystery_token,
    free_daily_mint,
    merge_tokens,
    get_mystery_collection,
    TIER_CONFIG,
)
from void_engine.adriana_scl import generate_token_story

logger = logging.getLogger(__name__)

marketplace_bp = Blueprint("marketplace", __name__)


@marketplace_bp.route("/marketplace")
def marketplace_page():
    user_id = session.get("user_id")
    collection = []
    pending_yield = 0.0
    if user_id:
        try:
            collection = get_user_collection_extended(user_id)
        except Exception as e:
            logger.error("Failed to load user collection: %s", e)
        try:
            has_yield_eligible = any(t["tier"] in ("rare", "legendary") for t in collection)
            if has_yield_eligible:
                pending_yield = get_pending_yield(user_id)
        except Exception as e:
            logger.error("Failed to load pending yield: %s", e)
    return render_template("marketplace.html", collection=collection, user_id=user_id, pending_yield=pending_yield)


@marketplace_bp.route("/api/marketplace/listings")
def api_listings():
    try:
        listings = get_marketplace_listings()
        return jsonify({"listings": listings})
    except Exception as e:
        logger.error("Listings error: %s", e)
        return jsonify({"error": "Failed to load listings"}), 500


@marketplace_bp.route("/api/marketplace/token/<int:token_id>")
def api_token_detail(token_id):
    try:
        token = get_token_detail(token_id)
        if not token:
            return jsonify({"error": "Token not found"}), 404
        return jsonify({"token": token})
    except Exception as e:
        logger.error("Token detail error: %s", e)
        return jsonify({"error": "Failed to load token"}), 500


@marketplace_bp.route("/api/marketplace/collection")
@login_required
def api_collection():
    try:
        collection = get_user_collection(session["user_id"])
        return jsonify({"collection": collection})
    except Exception as e:
        logger.error("Collection error: %s", e)
        return jsonify({"error": "Failed to load collection"}), 500


@marketplace_bp.route("/api/marketplace/buy/vtx", methods=["POST"])
@login_required
def buy_with_vtx():
    if not _check_rate_limit():
        return jsonify({"error": "Rate limit exceeded. Please wait before retrying."}), 429
    data = request.get_json(silent=True) or {}
    token_id = data.get("token_id")
    if not token_id:
        return jsonify({"error": "token_id required"}), 400

    try:
        result = purchase_token_vtx(int(token_id), session["user_id"])
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("VTX purchase error: %s", e)
        return jsonify({"error": "Purchase failed"}), 500


@marketplace_bp.route("/api/marketplace/buy/stripe", methods=["POST"])
@login_required
def buy_with_stripe():
    data = request.get_json(silent=True) or {}
    token_id = data.get("token_id")
    if not token_id:
        return jsonify({"error": "token_id required"}), 400

    try:
        from void_engine.blueprint_nft import _get_db
        conn = _get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, tier, title, price_gbp, status FROM blueprint_tokens WHERE id = %s FOR UPDATE",
            (int(token_id),),
        )
        token = cur.fetchone()

        if not token:
            conn.close()
            return jsonify({"error": "Token not found"}), 404
        if token[4] != "available":
            conn.close()
            return jsonify({"error": "Token is no longer available"}), 400

        from void_engine.economy import get_market_price
        item_key = f"nft_{token[1]}"
        try:
            market = get_market_price(item_key)
        except RuntimeError:
            conn.close()
            raise
        if not market:
            conn.close()
            return jsonify({"error": "This NFT tier is not currently available for purchase"}), 404

        cur.execute("UPDATE blueprint_tokens SET status = 'reserved' WHERE id = %s", (int(token_id),))
        conn.commit()
        conn.close()

        sc = get_stripe_client()
        user_id = session["user_id"]
        username = session.get("username", "")

        from routes.auth import _get_stripe_customer_id, _set_stripe_ids
        customer_id = _get_stripe_customer_id(user_id)
        if not customer_id:
            customer = sc.Customer.create(
                metadata={"user_id": str(user_id), "username": username},
            )
            customer_id = customer.id
            _set_stripe_ids(user_id, customer_id=customer_id)

        domains = os.environ.get("REPLIT_DOMAINS", "localhost:5000").split(",")
        base_url = f"https://{domains[0]}" if domains else "http://localhost:5000"

        tier_label = TIER_CONFIG.get(token[1], {}).get("label", token[1])
        product_name = f"VOID Blueprint Token - {tier_label} - {token[2]}"

        checkout_session = sc.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": market["gbp"],
                    "product_data": {
                        "name": product_name,
                        "description": f"Blueprint Token #{token[0]} - {tier_label} Tier - Manufacturing Slot",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{base_url}/api/marketplace/callback?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/marketplace",
            metadata={
                "type": "nft_purchase",
                "token_id": str(token[0]),
                "user_id": str(user_id),
                "tier": token[1],
            },
        )

        return jsonify({"url": checkout_session.url})
    except Exception as e:
        logger.error("Stripe checkout error: %s", e)
        return jsonify({"error": "Checkout creation failed"}), 500


@marketplace_bp.route("/api/marketplace/callback")
@login_required
def stripe_callback():
    session_id = request.args.get("session_id")
    if not session_id:
        return redirect("/marketplace")

    try:
        sc = get_stripe_client()
        cs = sc.checkout.Session.retrieve(session_id)
        meta = cs.get("metadata", {})

        if meta.get("type") == "nft_purchase" and cs.get("payment_status") == "paid":
            token_id = meta.get("token_id")
            meta_user_id = meta.get("user_id")
            current_user_id = str(session.get("user_id", ""))
            if meta_user_id != current_user_id:
                logger.warning("Marketplace callback user mismatch: meta=%s session=%s", meta_user_id, current_user_id)
                return redirect("/marketplace")
            if token_id and meta_user_id:
                result = purchase_token_fiat(int(token_id), int(meta_user_id), session_id)
                if "error" in result:
                    logger.error("Fiat finalization failed: %s", result["error"])
    except Exception as e:
        logger.error("Stripe callback error: %s", e)

    return redirect("/marketplace")


@marketplace_bp.route("/api/marketplace/fund-status")
def api_fund_status():
    try:
        status = get_manufacturing_fund_status()
        return jsonify(status)
    except Exception as e:
        logger.error("Fund status error: %s", e)
        return jsonify({"error": "Failed to load fund status"}), 500


@marketplace_bp.route("/api/marketplace/token/<int:token_id>/story")
def api_token_story(token_id):
    try:
        token = get_token_detail(token_id)
        if not token:
            return jsonify({"error": "Token not found"}), 404
        story = generate_token_story(token)
        return jsonify({"story": story, "token_id": token_id})
    except Exception as e:
        logger.error("Token story error: %s", e)
        return jsonify({"error": "Failed to generate story"}), 500


@marketplace_bp.route("/api/marketplace/yield/pending")
@login_required
def api_yield_pending():
    try:
        pending = get_pending_yield(session["user_id"])
        return jsonify({"pending_vtx": pending})
    except Exception as e:
        logger.error("Yield pending error: %s", e)
        return jsonify({"error": "Failed to load pending yield"}), 500


@marketplace_bp.route("/api/marketplace/yield/claim", methods=["POST"])
@login_required
def api_yield_claim():
    try:
        result = claim_yield(session["user_id"])
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Yield claim error: %s", e)
        return jsonify({"error": "Claim failed"}), 500


@marketplace_bp.route("/api/marketplace/secondary-listings")
def api_secondary_listings():
    try:
        listings = get_secondary_listings()
        return jsonify({"listings": listings})
    except Exception as e:
        logger.error("Secondary listings error: %s", e)
        return jsonify({"error": "Failed to load secondary listings"}), 500


@marketplace_bp.route("/api/marketplace/rental-offers")
def api_rental_offers():
    try:
        offers = get_rental_offers()
        return jsonify({"offers": offers})
    except Exception as e:
        logger.error("Rental offers error: %s", e)
        return jsonify({"error": "Failed to load rental offers"}), 500


@marketplace_bp.route("/api/marketplace/list", methods=["POST"])
@login_required
def api_list_token():
    data = request.get_json(silent=True) or {}
    token_id = data.get("token_id")
    price_vtx = data.get("price_vtx")
    price_gbp_pence = data.get("price_gbp_pence")

    if not token_id or price_vtx is None:
        return jsonify({"error": "token_id and price_vtx required"}), 400

    try:
        result = list_token_for_sale(int(token_id), session["user_id"], price_vtx, price_gbp_pence)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("List token error: %s", e)
        return jsonify({"error": "Failed to list token"}), 500


@marketplace_bp.route("/mystery")
def mystery_page():
    user_id = session.get("user_id")
    return render_template("mystery.html", user_id=user_id)


@marketplace_bp.route("/api/mystery/price")
def api_mystery_price():
    try:
        price_data = get_mystery_price()
        if "error" in price_data:
            return jsonify(price_data), 500
        return jsonify(price_data)
    except Exception as e:
        logger.error("Mystery price error: %s", e)
        return jsonify({"error": "Failed to load price"}), 500


@marketplace_bp.route("/api/mystery/buy", methods=["POST"])
@login_required
def api_mystery_buy():
    if not _check_rate_limit():
        return jsonify({"error": "Rate limit exceeded. Please wait before retrying."}), 429
    try:
        result = buy_mystery_token(session["user_id"])
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Mystery buy error: %s", e)
        return jsonify({"error": "Purchase failed"}), 500


@marketplace_bp.route("/api/marketplace/unlist", methods=["POST"])
@login_required
def api_unlist_token():
    data = request.get_json(silent=True) or {}
    token_id = data.get("token_id")
    if not token_id:
        return jsonify({"error": "token_id required"}), 400

    try:
        result = unlist_token(int(token_id), session["user_id"])
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Unlist token error: %s", e)
        return jsonify({"error": "Failed to unlist token"}), 500


@marketplace_bp.route("/api/marketplace/buy/secondary", methods=["POST"])
@login_required
def api_buy_secondary():
    if not _check_rate_limit():
        return jsonify({"error": "Rate limit exceeded. Please wait before retrying."}), 429
    data = request.get_json(silent=True) or {}
    token_id = data.get("token_id")
    if not token_id:
        return jsonify({"error": "token_id required"}), 400

    try:
        result = purchase_secondary(int(token_id), session["user_id"])
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Secondary purchase error: %s", e)
        return jsonify({"error": "Purchase failed"}), 500


@marketplace_bp.route("/api/mystery/reveal/<int:token_id>", methods=["POST"])
@login_required
def api_mystery_reveal(token_id):
    try:
        result = reveal_mystery_token(token_id, session["user_id"])
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Mystery reveal error: %s", e)
        return jsonify({"error": "Reveal failed"}), 500


@marketplace_bp.route("/api/marketplace/rent/offer", methods=["POST"])
@login_required
def api_rent_offer():
    data = request.get_json(silent=True) or {}
    token_id = data.get("token_id")
    vtx_per_day = data.get("vtx_per_day")
    max_days = data.get("max_days", 30)

    if not token_id or vtx_per_day is None:
        return jsonify({"error": "token_id and vtx_per_day required"}), 400

    try:
        result = offer_token_for_rent(int(token_id), session["user_id"], vtx_per_day, max_days)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Rent offer error: %s", e)
        return jsonify({"error": "Failed to create rental offer"}), 500


@marketplace_bp.route("/api/marketplace/rent/book", methods=["POST"])
@login_required
def api_rent_book():
    if not _check_rate_limit():
        return jsonify({"error": "Rate limit exceeded. Please wait before retrying."}), 429
    data = request.get_json(silent=True) or {}
    rental_id = data.get("rental_id")
    days = data.get("days")

    if not rental_id or days is None:
        return jsonify({"error": "rental_id and days required"}), 400

    try:
        result = book_rental(int(rental_id), session["user_id"], int(days))
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Rent book error: %s", e)
        return jsonify({"error": "Failed to book rental"}), 500


@marketplace_bp.route("/api/mystery/free-mint", methods=["POST"])
@login_required
def api_mystery_free_mint():
    if not _check_rate_limit():
        return jsonify({"error": "Rate limit exceeded. Please wait before retrying."}), 429
    try:
        result = free_daily_mint(session["user_id"])
        if "error" in result:
            if result.get("error") == "cooldown":
                return jsonify(result), 429
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Free mint error: %s", e)
        return jsonify({"error": "Free mint failed"}), 500


@marketplace_bp.route("/api/mystery/merge", methods=["POST"])
@login_required
def api_mystery_merge():
    if not _check_rate_limit():
        return jsonify({"error": "Rate limit exceeded. Please wait before retrying."}), 429
    try:
        result = merge_tokens(session["user_id"])
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Merge error: %s", e)
        return jsonify({"error": "Merge failed"}), 500


@marketplace_bp.route("/api/marketplace/rent/end", methods=["POST"])
@login_required
def api_rent_end():
    data = request.get_json(silent=True) or {}
    rental_id = data.get("rental_id")
    if not rental_id:
        return jsonify({"error": "rental_id required"}), 400

    try:
        result = end_rental(int(rental_id), session["user_id"])
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error("Rent end error: %s", e)
        return jsonify({"error": "Failed to end rental"}), 500


@marketplace_bp.route("/api/mystery/collection")
@login_required
def api_mystery_collection():
    try:
        data = get_mystery_collection(session["user_id"])
        return jsonify(data)
    except Exception as e:
        logger.error("Mystery collection error: %s", e)
        return jsonify({"error": "Failed to load collection"}), 500


@marketplace_bp.route("/api/adriana/verify")
def api_adriana_verify():
    """
    Public commercial-licence check for a VOID Blueprint Token.

    Query: ?token_id=<int>
    Returns: {licensed, tier, edition, token_hash, sdk_url}

    licensed=true when the token has an owner regardless of its mutable lifecycle
    status (sold/revealed/sealed/merged are all valid owned-token states).
    """
    token_id = request.args.get("token_id")
    if not token_id:
        return jsonify({"licensed": False, "error": "token_id required"}), 400
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT bt.id, bt.tier, bt.token_hash,
                          bt.edition_number, bt.total_editions, bt.status,
                          tow.owner_id
                   FROM blueprint_tokens bt
                   LEFT JOIN token_ownership tow ON tow.token_id = bt.id
                   WHERE bt.id = %s
                   ORDER BY tow.purchased_at DESC
                   LIMIT 1""",
                (int(token_id),),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return jsonify({"licensed": False, "error": "Token not found"})

        licensed = row[6] is not None   # has an owner
        return jsonify({
            "licensed":   licensed,
            "tier":       row[1],
            "edition":    f"{row[3]}/{row[4]}" if row[3] and row[4] else None,
            "token_hash": row[2][:16] + "..." if row[2] else None,
            "sdk_url":    "/download/adriana-sdk",
        })
    except Exception as e:
        logger.error("Adriana verify error: %s", e)
        return jsonify({"licensed": False, "error": "Verification failed"}), 500
