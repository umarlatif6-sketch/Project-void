import os
import json
from flask import Blueprint, request, jsonify, session, redirect, current_app
from routes.auth import login_required, _set_user_tier, _set_stripe_ids, _get_stripe_customer_id, _get_user_by_stripe_customer, _get_user_by_stripe_subscription
from routes.stripe_client import get_stripe_client, get_publishable_key
from void_engine.vortex_wallet import VTX_PACKS, VTX_UNLOCK_FEATURES

payments_bp = Blueprint("payments", __name__)

TIER_PRICE_MAP = {
    "journalist": 2800,
    "sovereign": 28600,
}

PRICE_TIER_MAP = {}


def _get_or_create_price(stripe_client, tier_name, amount_pence):
    products = stripe_client.Product.search(query=f"name:'VOID {tier_name.title()}'")
    if products.data:
        product = products.data[0]
    else:
        product = stripe_client.Product.create(
            name=f"VOID {tier_name.title()}",
            description=f"PROJECT VOID - {tier_name.title()} Tier monthly subscription",
            metadata={"tier": tier_name},
        )

    prices = stripe_client.Price.list(product=product.id, active=True, type="recurring")
    for p in prices.data:
        if p.unit_amount == amount_pence and p.currency == "gbp" and p.recurring.interval == "month":
            return p.id

    price = stripe_client.Price.create(
        product=product.id,
        unit_amount=amount_pence,
        currency="gbp",
        recurring={"interval": "month"},
    )
    return price.id


def _ensure_stripe_products():
    global PRICE_TIER_MAP
    try:
        sc = get_stripe_client()
        for tier_name, amount in TIER_PRICE_MAP.items():
            price_id = _get_or_create_price(sc, tier_name, amount)
            PRICE_TIER_MAP[price_id] = tier_name
    except Exception as e:
        current_app.logger.error(f"Stripe product setup error: {e}")


@payments_bp.route("/api/stripe/publishable-key")
def stripe_publishable_key():
    try:
        key = get_publishable_key()
        return jsonify({"key": key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payments_bp.route("/api/subscribe/<tier>", methods=["POST"])
@login_required
def create_checkout(tier):
    if tier not in TIER_PRICE_MAP:
        return jsonify({"error": "Invalid tier"}), 400

    try:
        sc = get_stripe_client()
        amount = TIER_PRICE_MAP[tier]
        price_id = _get_or_create_price(sc, tier, amount)

        user_id = session["user_id"]
        username = session.get("username", "")
        customer_id = _get_stripe_customer_id(user_id)

        if not customer_id:
            customer = sc.Customer.create(
                metadata={"user_id": str(user_id), "username": username},
            )
            customer_id = customer.id
            _set_stripe_ids(user_id, customer_id=customer_id)

        domains = os.environ.get("REPLIT_DOMAINS", "localhost:5000").split(",")
        base_url = f"https://{domains[0]}" if domains else "http://localhost:5000"

        checkout_session = sc.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{base_url}/api/subscribe/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/pricing",
            metadata={"tier": tier, "user_id": str(user_id)},
        )

        return jsonify({"url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payments_bp.route("/api/subscribe/success")
@login_required
def checkout_success():
    return redirect("/")


@payments_bp.route("/api/subscribe/portal", methods=["POST"])
@login_required
def customer_portal():
    user_id = session["user_id"]
    customer_id = _get_stripe_customer_id(user_id)
    if not customer_id:
        return jsonify({"error": "No active subscription"}), 400

    try:
        sc = get_stripe_client()
        domains = os.environ.get("REPLIT_DOMAINS", "localhost:5000").split(",")
        base_url = f"https://{domains[0]}" if domains else "http://localhost:5000"

        portal_session = sc.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{base_url}/pricing",
        )
        return jsonify({"url": portal_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payments_bp.route("/api/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        sc = get_stripe_client()
        endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        if not endpoint_secret:
            current_app.logger.error("STRIPE_WEBHOOK_SECRET not configured — rejecting webhook")
            return jsonify({"error": "Webhook not configured"}), 500
        if not sig_header:
            return jsonify({"error": "Missing Stripe-Signature header"}), 400
        event = sc.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except sc.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    event_type = event.get("type", "")
    data_obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        meta = data_obj.get("metadata", {})
        if meta.get("type") == "vtx_purchase":
            vtx_user_id = meta.get("user_id")
            pack_name = meta.get("pack")
            cs_id = data_obj.get("id", "")
            if vtx_user_id and pack_name and pack_name in VTX_PACKS:
                pack = VTX_PACKS[pack_name]
                try:
                    from void_engine.vortex_wallet import mint_purchase
                    mint_purchase(int(vtx_user_id), pack["vtx"], cs_id)
                except Exception as e:
                    current_app.logger.error(f"VTX mint on webhook failed: {e}")
        else:
            tier = meta.get("tier", "journalist")
            user_id_str = meta.get("user_id")
            sub_id = data_obj.get("subscription")
            if user_id_str:
                from datetime import datetime, timedelta, timezone
                expires = datetime.now(timezone.utc) + timedelta(days=31)
                _set_user_tier(int(user_id_str), tier, expires)
                if sub_id:
                    _set_stripe_ids(int(user_id_str), subscription_id=sub_id)

    elif event_type == "invoice.paid":
        sub_id = data_obj.get("subscription")
        if sub_id:
            user = _get_user_by_stripe_subscription(sub_id)
            if user:
                from datetime import datetime, timedelta, timezone
                expires = datetime.now(timezone.utc) + timedelta(days=31)
                current_tier = "journalist"
                lines = data_obj.get("lines", {}).get("data", [])
                for line in lines:
                    amt = line.get("amount", 0)
                    if amt >= 28600:
                        current_tier = "sovereign"
                        break
                _set_user_tier(user["id"], current_tier, expires)

    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        sub_id = data_obj.get("id")
        status = data_obj.get("status", "")
        if sub_id:
            user = _get_user_by_stripe_subscription(sub_id)
            if user:
                if status in ("canceled", "unpaid", "incomplete_expired"):
                    _set_user_tier(user["id"], "ghost")

    return jsonify({"received": True}), 200


@payments_bp.route("/api/vtx/packs")
def vtx_packs():
    packs = []
    for key, pack in VTX_PACKS.items():
        packs.append({
            "id": key,
            "label": pack["label"],
            "vtx": float(pack["vtx"]),
            "price_pence": pack["price_pence"],
            "price_display": f"\u00a3{pack['price_pence'] / 100:.0f}",
            "bonus": pack["bonus"],
        })
    return jsonify({"packs": packs})


@payments_bp.route("/api/vtx/buy/<pack_name>", methods=["POST"])
@login_required
def vtx_buy(pack_name):
    if pack_name not in VTX_PACKS:
        return jsonify({"error": "Invalid VTX pack"}), 400

    pack = VTX_PACKS[pack_name]
    try:
        sc = get_stripe_client()
        user_id = session["user_id"]
        username = session.get("username", "")
        customer_id = _get_stripe_customer_id(user_id)

        if not customer_id:
            customer = sc.Customer.create(
                metadata={"user_id": str(user_id), "username": username},
            )
            customer_id = customer.id
            _set_stripe_ids(user_id, customer_id=customer_id)

        domains = os.environ.get("REPLIT_DOMAINS", "localhost:5000").split(",")
        base_url = f"https://{domains[0]}" if domains else "http://localhost:5000"

        product_name = f"VOID VTX Credits - {pack['label']}"
        products = sc.Product.search(query=f"name:'{product_name}'")
        if products.data:
            product = products.data[0]
        else:
            product = sc.Product.create(
                name=product_name,
                description=f"{int(pack['vtx'])} VTX Credits{' (' + pack['bonus'] + ')' if pack['bonus'] else ''}",
                metadata={"type": "vtx_pack", "pack": pack_name},
            )

        checkout_session = sc.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": pack["price_pence"],
                    "product": product.id,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{base_url}/api/vtx/buy/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/pricing",
            metadata={
                "type": "vtx_purchase",
                "pack": pack_name,
                "user_id": str(user_id),
                "vtx_amount": str(int(pack["vtx"])),
            },
        )

        return jsonify({"url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payments_bp.route("/api/vtx/buy/success")
@login_required
def vtx_buy_success():
    return redirect("/messenger")


@payments_bp.route("/api/vtx/unlocks")
@login_required
def vtx_unlocks_list():
    features = []
    for key, feat in VTX_UNLOCK_FEATURES.items():
        features.append({
            "id": key,
            "label": feat["label"],
            "cost": float(feat["cost"]),
            "hours": feat["hours"],
            "description": feat["description"],
        })

    from void_engine.messenger_auth import _get_db
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT feature, expires_at FROM vtx_unlocks WHERE user_id = %s AND expires_at > NOW()",
            (session["user_id"],),
        )
        active = {}
        for row in cur.fetchall():
            active[row[0]] = row[1].isoformat() if row[1] else None
    except Exception:
        active = {}
    finally:
        conn.close()

    return jsonify({"features": features, "active_unlocks": active})


@payments_bp.route("/api/vtx/spend", methods=["POST"])
@login_required
def vtx_spend():
    data = request.get_json(silent=True) or {}
    feature = (data.get("feature") or "").strip()

    if feature not in VTX_UNLOCK_FEATURES:
        return jsonify({"error": "Invalid feature"}), 400

    feat = VTX_UNLOCK_FEATURES[feature]

    from void_engine.vortex_wallet import spend_vtx_with_unlock
    from datetime import timedelta
    result = spend_vtx_with_unlock(
        session["user_id"], feat["cost"], feature, timedelta(hours=feat["hours"])
    )
    if "error" in result:
        return jsonify(result), 400

    return jsonify({
        "success": True,
        "feature": feature,
        "label": feat["label"],
        "spent": float(feat["cost"]),
        "expires_at": result.get("expires_at", ""),
        "block": result,
    })
