import os
import logging
from flask import Blueprint, request, jsonify, session, redirect, render_template
from routes.auth import login_required
from routes.stripe_client import get_stripe_client
from void_engine.blueprint_nft import (
    get_marketplace_listings,
    get_user_collection,
    get_token_detail,
    get_manufacturing_fund_status,
    purchase_token_vtx,
    purchase_token_fiat,
    TIER_CONFIG,
)

logger = logging.getLogger(__name__)

marketplace_bp = Blueprint("marketplace", __name__)


@marketplace_bp.route("/marketplace")
def marketplace_page():
    user_id = session.get("user_id")
    collection = []
    if user_id:
        try:
            collection = get_user_collection(user_id)
        except Exception as e:
            logger.error("Failed to load user collection: %s", e)
    return render_template("marketplace.html", collection=collection, user_id=user_id)


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
