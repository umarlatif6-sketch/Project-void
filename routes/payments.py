import os
import json
from flask import Blueprint, request, jsonify, session, redirect, current_app
from routes.auth import login_required, _set_user_tier, _set_stripe_ids, _get_stripe_customer_id, _get_user_by_stripe_customer, _get_user_by_stripe_subscription
from routes.stripe_client import get_stripe_client, get_publishable_key

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
    session_id = request.args.get("session_id")
    if not session_id:
        return redirect("/pricing")

    try:
        sc = get_stripe_client()
        cs = sc.checkout.Session.retrieve(session_id)

        if cs.payment_status == "paid":
            tier = cs.metadata.get("tier", "journalist")
            user_id = int(cs.metadata.get("user_id", session["user_id"]))
            sub_id = cs.subscription

            from datetime import datetime, timedelta, timezone
            expires = datetime.now(timezone.utc) + timedelta(days=31)

            _set_user_tier(user_id, tier, expires)
            if sub_id:
                _set_stripe_ids(user_id, subscription_id=sub_id)

            session["tier"] = tier

        return redirect("/")
    except Exception as e:
        current_app.logger.error(f"Checkout success error: {e}")
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
        if endpoint_secret and sig_header:
            event = sc.Webhook.construct_event(payload, sig_header, endpoint_secret)
        elif endpoint_secret:
            return jsonify({"error": "Missing Stripe-Signature header"}), 400
        else:
            event = json.loads(payload)
    except sc.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    event_type = event.get("type", "")
    data_obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        tier = data_obj.get("metadata", {}).get("tier", "journalist")
        user_id_str = data_obj.get("metadata", {}).get("user_id")
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
