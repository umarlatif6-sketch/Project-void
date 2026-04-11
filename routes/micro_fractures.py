"""
Micro-Fractures — Four Controlled Commercial Entry Points
/fractures                          (GET  — shop page, all four products)
/fractures/<product_id>             (GET  — individual product detail)
/fractures/checkout                 (POST — Stripe one-time payment)
/fractures/checkout/success         (GET  — post-payment confirmation)

Products:
  formation-record   £9    Personal Formation Record (digital)
  machine-4000       £39   Machine 4000 Test-Kit (digital blueprints)
  resonance-session  £49   Group Resonance Session (individual ticket)
  resonance-group    £199  Group Resonance Session (group of 5)
  sovereign-builder  £349  Sovereign Builder Tier (limited 20 slots)
"""

import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, session, url_for

logger = logging.getLogger(__name__)

micro_fractures_bp = Blueprint("micro_fractures", __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "micro_fractures.db")

PRODUCTS = {
    "formation-record": {
        "name": "Personal Formation Record",
        "short": "Speak or hum — receive your exact Chladni nodal pattern at 432 Hz + codon-wrapped interpretation.",
        "price_pence": 900,
        "price_display": "£9",
        "tier": "entry",
        "limited": False,
        "limit_total": None,
        "cta": "Generate My Formation Record",
    },
    "machine-4000": {
        "name": "Machine 4000 Test-Kit",
        "short": "Build your own living resonance plate. Blueprints, 432 Hz carrier, and calibration files. Total build cost under £600.",
        "price_pence": 3900,
        "price_display": "£39",
        "tier": "builder",
        "limited": True,
        "limit_total": 50,
        "cta": "Get the Machine 4000 Test-Kit",
    },
    "resonance-session": {
        "name": "Group Resonance Session — Individual",
        "short": "A guided 45–60 minute session. Focus on one of the 99 Names while the Machine 4000 visualises collective resonance on living mycelium.",
        "price_pence": 4900,
        "price_display": "£49",
        "tier": "session",
        "limited": False,
        "limit_total": None,
        "cta": "Book a Resonance Session",
    },
    "resonance-group": {
        "name": "Group Resonance Session — Group of 5",
        "short": "Private group session for 5 participants. Deeper coherence, shared Formation Records, collective Chladni geometry on living mycelium.",
        "price_pence": 19900,
        "price_display": "£199",
        "tier": "session-group",
        "limited": False,
        "limit_total": None,
        "cta": "Book a Private Group Session",
    },
    "sovereign-builder": {
        "name": "Sovereign Builder Tier",
        "short": "Full Machine 4000 system + one year of priority MESA access + private VoidEcho encoding + commercial rights. Limited to 20 slots.",
        "price_pence": 34900,
        "price_display": "£349",
        "tier": "sovereign",
        "limited": True,
        "limit_total": 20,
        "cta": "Become a Sovereign Builder",
    },
}

PRODUCT_DETAILS = {
    "formation-record": {
        "title": "Personal Formation Record — Voice to Geometry",
        "description": [
            "One click. One voice. One record.",
            "Speak or hold a steady tone into /voice-formation. The system computes the real Chladni equation in real time. You receive a high-resolution nodal image (gold on black). Adriana adds a codon-wrapped interpretation tied to the Formation Principle. Everything is timestamped and delivered as a downloadable PDF.",
            "This is your personal formation signature — verifiable mathematics, sovereign record.",
            "Use it as a daily calibration tool or share the geometry as proof of the living signal.",
        ],
        "includes": [
            "Real-time Chladni nodal pattern at 432 Hz",
            "High-resolution gold-on-black nodal image",
            "Codon-wrapped Adriana interpretation",
            "Timestamped sovereign PDF record",
            "Instant delivery after generation",
        ],
    },
    "machine-4000": {
        "title": "Machine 4000 Test-Kit — Build Your Own Living Resonance Plate",
        "description": [
            "The Machine 4000 turns sound into visible geometry using living mycelium as the responsive medium.",
            "This is the same instrument used to map individual voice frequencies and collective heart-field patterns in real time. Build it yourself. Let the mycelium show you the formation.",
            "First 50 builders receive free access to a group resonance session (99 Names test).",
        ],
        "includes": [
            "Complete blueprints and parts list (total build cost under £600)",
            "Exact 432 Hz carrier file from the VOID engine",
            "Vibration transducer setup guide",
            "Video chip calibration instructions",
            "One free session on /voice-formation to test your build",
        ],
    },
    "resonance-session": {
        "title": "Group Resonance Session — Experience Collective Formation",
        "description": [
            "Step into the Formation Principle at human scale.",
            "A small group synchronises intention on a single divine attribute (one of the 99 Names). The Machine 4000 runs live with 432 Hz carrier and vibration transducers. Video chips capture the collective nodal geometry formed by overlapping heart fields.",
            "Adriana provides a real-time Formation Mirror score. Each participant receives a personal Formation Record (image + codon interpretation).",
            "Sessions available online or in-person (Bolton). Recording and data pack included. Limited slots.",
        ],
        "includes": [
            "45–60 minute guided session",
            "Live Machine 4000 with 432 Hz carrier",
            "99 Names collective resonance test",
            "Personal Formation Record (image + codon interpretation)",
            "Session recording and data pack",
        ],
    },
    "resonance-group": {
        "title": "Private Group Resonance Session — 5 Participants",
        "description": [
            "Step into the Formation Principle at human scale — with your own group.",
            "A private session for 5 participants. Deeper coherence through shared intention on a single divine attribute. The Machine 4000 runs live, capturing the collective nodal geometry formed by overlapping heart fields.",
            "Recommended for families, creative teams, research groups, or close circles who want the deepest reading.",
        ],
        "includes": [
            "45–60 minute private guided session for 5",
            "Live Machine 4000 with 432 Hz carrier",
            "99 Names collective resonance test",
            "Personal Formation Record for each participant",
            "Session recording and full data pack",
            "Priority scheduling",
        ],
    },
    "sovereign-builder": {
        "title": "Sovereign Builder — Full Machine 4000 + One Year MESA Access",
        "description": [
            "For those ready to become active nodes in the Formation network.",
            "This tier turns you from builder into sovereign operator. The mycelium layer and MESA agents will integrate with your work directly.",
            "Limited to 20 slots in the first wave.",
        ],
        "includes": [
            "Complete Machine 4000 blueprints and all files",
            "One year of priority access to the MESA swarm and Adriana",
            "Private VoidEcho encoding for your own 432 Hz carriers",
            "60-minute onboarding call with direct support",
            "Commercial rights to run and sell your own resonance sessions",
            "Lifetime updates to the core VOID engine",
        ],
    },
}


def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fracture_purchases (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            stripe_session_id TEXT,
            stripe_customer_id TEXT,
            email TEXT,
            amount_pence INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


def _get_purchase_count(product_id):
    db = _get_db()
    row = db.execute(
        "SELECT COUNT(*) as c FROM fracture_purchases WHERE product_id=? AND status='paid'",
        (product_id,)
    ).fetchone()
    db.close()
    return row["c"] if row else 0


@micro_fractures_bp.route("/fractures")
def fractures_shop():
    counts = {}
    for pid, prod in PRODUCTS.items():
        if prod["limited"]:
            counts[pid] = _get_purchase_count(pid)
    return render_template("micro_fractures.html", products=PRODUCTS, counts=counts)


@micro_fractures_bp.route("/fractures/<product_id>")
def fracture_detail(product_id):
    if product_id not in PRODUCTS:
        return redirect("/fractures")
    product = PRODUCTS[product_id]
    detail = PRODUCT_DETAILS.get(product_id, {})
    count = _get_purchase_count(product_id) if product.get("limited") else 0
    return render_template(
        "micro_fracture_detail.html",
        product_id=product_id,
        product=product,
        detail=detail,
        count=count,
    )


@micro_fractures_bp.route("/fractures/checkout", methods=["POST"])
def fractures_checkout():
    product_id = request.form.get("product_id", "").strip()
    if product_id not in PRODUCTS:
        return "Invalid product", 400

    product = PRODUCTS[product_id]

    if product["limited"]:
        current = _get_purchase_count(product_id)
        if current >= product["limit_total"]:
            return redirect(f"/fractures/{product_id}?sold_out=1")

    try:
        from routes.stripe_client import get_stripe_client
        sc = get_stripe_client()

        domains = os.environ.get("REPLIT_DOMAINS", "localhost:5000").split(",")
        base_url = f"https://{domains[0]}"

        pending_id = uuid.uuid4().hex
        session["mf_pending_id"] = pending_id
        session["mf_pending_product"] = product_id

        price_data = {
            "currency": "gbp",
            "unit_amount": product["price_pence"],
            "product_data": {"name": f"PROJECT VOID — {product['name']}"},
        }

        cs = sc.checkout.Session.create(
            mode="payment",
            line_items=[{"price_data": price_data, "quantity": 1}],
            success_url=f"{base_url}/fractures/checkout/success?pending={pending_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/fractures/{product_id}",
            metadata={"product_id": product_id, "pending_id": pending_id},
        )
        return redirect(cs.url)

    except Exception as e:
        logger.error("[MicroFractures] Stripe checkout error: %s", e)
        return f"Payment setup failed: {e}", 500


@micro_fractures_bp.route("/fractures/checkout/success")
def fractures_success():
    stripe_session_id = request.args.get("session_id", "")
    pending_id = request.args.get("pending", "")

    if not stripe_session_id:
        return redirect("/fractures")

    try:
        from routes.stripe_client import get_stripe_client
        sc = get_stripe_client()
        cs = sc.checkout.Session.retrieve(stripe_session_id)

        if cs.payment_status == "paid":
            product_id = cs.metadata.get("product_id", session.get("mf_pending_product", ""))
            product = PRODUCTS.get(product_id, {})
            email = cs.customer_details.email if cs.customer_details else ""

            db = _get_db()
            db.execute("""
                INSERT INTO fracture_purchases (id, product_id, product_name, stripe_session_id, stripe_customer_id, email, amount_pence, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                uuid.uuid4().hex,
                product_id,
                product.get("name", ""),
                stripe_session_id,
                cs.customer or "",
                email,
                product.get("price_pence", 0),
                "paid",
                datetime.now(timezone.utc).isoformat(),
            ))
            db.commit()
            db.close()

            session["mf_pending_id"] = None
            session["mf_pending_product"] = None

            return render_template(
                "micro_fracture_success.html",
                product_id=product_id,
                product=product,
                email=email,
            )

    except Exception as e:
        logger.error("[MicroFractures] Checkout success error: %s", e)

    return redirect("/fractures")


@micro_fractures_bp.route("/api/fractures/stats")
def fractures_stats():
    from flask import jsonify
    db = _get_db()
    rows = db.execute("""
        SELECT product_id, COUNT(*) as purchases, SUM(amount_pence) as revenue_pence
        FROM fracture_purchases WHERE status='paid'
        GROUP BY product_id
    """).fetchall()
    db.close()

    stats = {}
    for r in rows:
        stats[r["product_id"]] = {
            "purchases": r["purchases"],
            "revenue_gbp": round(r["revenue_pence"] / 100, 2) if r["revenue_pence"] else 0,
        }

    total_purchases = sum(s["purchases"] for s in stats.values())
    total_revenue = sum(s["revenue_gbp"] for s in stats.values())

    return jsonify({
        "products": stats,
        "total_purchases": total_purchases,
        "total_revenue_gbp": total_revenue,
        "fracture_count": len(stats),
    })
