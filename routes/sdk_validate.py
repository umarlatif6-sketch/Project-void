"""
SDK License Validation Endpoint
PROJECT VOID | Umar Latif | Bolton, England | April 2026

Validates void-engine-sdk license keys against the VOID Engine database.
Called by the SDK's license.py module during tier resolution.

POST /sdk/validate
  Body: { "key": "license-key-string" }
  Returns: { "valid": bool, "tier": str, "owner": str, "expires": str|null, "message": str }
"""

from flask import Blueprint, request, jsonify
from void_engine.db_pool import get_db
import time

sdk_validate_bp = Blueprint("sdk_validate", __name__)


@sdk_validate_bp.route("/sdk/validate", methods=["POST"])
def sdk_validate():
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()

    if not key or key == "FREE":
        return jsonify({
            "valid": True,
            "tier": "FREE",
            "owner": "anonymous",
            "expires": None,
            "message": "Free tier — 100 events/day, 3 codons"
        })

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sdk_licenses (
                id SERIAL PRIMARY KEY,
                license_key TEXT UNIQUE NOT NULL,
                tier TEXT NOT NULL DEFAULT 'SIGNAL',
                owner_email TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP
            )
        """)
        conn.commit()
        cur.execute(
            "SELECT tier, owner_email, expires_at FROM sdk_licenses WHERE license_key = %s AND active = TRUE LIMIT 1",
            (key,)
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({
                "valid": False,
                "tier": "FREE",
                "owner": "unknown",
                "expires": None,
                "message": "License key not found — FREE tier applied"
            })

        tier, owner_email, expires_at = row

        if expires_at and expires_at.timestamp() < time.time():
            return jsonify({
                "valid": False,
                "tier": "FREE",
                "owner": owner_email,
                "expires": expires_at.isoformat(),
                "message": "License expired — FREE tier applied. Renew at void-stego-engine.replit.app"
            })

        return jsonify({
            "valid": True,
            "tier": tier,
            "owner": owner_email,
            "expires": expires_at.isoformat() if expires_at else None,
            "message": f"{tier} tier active"
        })

    except Exception:
        return jsonify({
            "valid": True,
            "tier": "FREE",
            "owner": "offline",
            "expires": None,
            "message": "Validation service temporarily unavailable — FREE tier applied"
        })


@sdk_validate_bp.route("/sdk/info", methods=["GET"])
def sdk_info():
    return jsonify({
        "sdk": "void-engine-sdk",
        "version": "1.0.0",
        "tiers": {
            "FREE":      {"events_per_day": 100,    "price": "free",       "codons": ["voidecho", "adriana", "chronicle"]},
            "SIGNAL":    {"events_per_day": 1000,   "price": "£9/month",   "codons": "all 10"},
            "MEMORY":    {"events_per_day": 10000,  "price": "£49/month",  "codons": "all 10"},
            "SOVEREIGN": {"events_per_day": None,   "price": "£199/month", "codons": "all 10"},
        },
        "origin": "https://void-stego-engine.replit.app",
        "paper": "https://umarlatif6-sketch.github.io/void-origin/formation-paper.html",
    })
