"""
PROJECT VOID — Pricing & License Routes
/pricing          — public pricing page
/api/license/validate  — validate a VOID license key
/api/license/generate  — generate a key (admin/founder only)
/api/license/list      — list all licenses (founder only)
"""

import logging
from flask import Blueprint, render_template, request, jsonify, session
from void_engine.void_license import (
    generate_license, validate_license, list_licenses, revoke_license,
    TIERS, TIER_FEATURES
)

pricing_bp = Blueprint("pricing", __name__)
logger = logging.getLogger(__name__)


FREQUENCY_BANDS = [
    {
        "band": "Seed",
        "glyph": "α",
        "entity": "Individual / researcher / student",
        "capacity": "No revenue",
        "price": "£9",
        "period": "/month",
        "sdk_tier": "SIG",
        "note": "",
    },
    {
        "band": "Signal",
        "glyph": "λ",
        "entity": "Startup, < 10 people",
        "capacity": "< £500k revenue",
        "price": "£49",
        "period": "/month",
        "sdk_tier": "SIG",
        "note": "",
    },
    {
        "band": "Memory",
        "glyph": "ψ",
        "entity": "Growing company, 10–100 people",
        "capacity": "£500k – £5M revenue",
        "price": "£299",
        "period": "/month",
        "sdk_tier": "MEM",
        "note": "",
        "highlight": True,
    },
    {
        "band": "Sovereign",
        "glyph": "σ",
        "entity": "Established company, 100+ people",
        "capacity": "£5M – £50M revenue",
        "price": "£1,500",
        "period": "/month",
        "sdk_tier": "SOV",
        "note": "",
    },
    {
        "band": "Formation",
        "glyph": "φ",
        "entity": "Enterprise / institution",
        "capacity": "> £50M revenue",
        "price": "£8,000",
        "period": "/month",
        "sdk_tier": "SOV",
        "note": "+ SLA",
    },
    {
        "band": "Leviathan",
        "glyph": "Ω",
        "entity": "Billion-dollar company",
        "capacity": "> £1B revenue",
        "price": "Contact",
        "period": "",
        "sdk_tier": "SOV",
        "note": "Negotiated",
    },
]

ARCHITECT_QUOTE = (
    "The price of what you receive should match the amplitude at which you receive it. "
    "A billion-dollar company extracting billion-dollar intelligence from this engine "
    "should pay at that frequency. A student hearing the signal for the first time "
    "should not be priced away from hearing it at all. "
    "This is not charity and it is not greed — it is the only honest model for a sovereign system. "
    "You are charged at the frequency you operate in. Nothing more. Nothing less."
)


@pricing_bp.route("/pricing")
def pricing_page():
    tiers = [
        {
            "code": "SIG",
            "name": "Signal",
            "price": 49,
            "tagline": "Frequency attribution + codon tagging",
            "features": TIER_FEATURES["SIG"],
            "cta": "Install Signal",
        },
        {
            "code": "MEM",
            "name": "Memory",
            "price": 299,
            "tagline": "AI that remembers who your users are",
            "features": TIER_FEATURES["MEM"],
            "cta": "Install Memory",
            "highlight": True,
        },
        {
            "code": "SOV",
            "name": "Sovereign",
            "price": 1500,
            "tagline": "The full engine. Nothing held back.",
            "features": TIER_FEATURES["SOV"],
            "cta": "Install Sovereign",
        },
    ]
    return render_template(
        "pricing.html",
        tiers=tiers,
        bands=FREQUENCY_BANDS,
        architect_quote=ARCHITECT_QUOTE,
    )


@pricing_bp.route("/api/license/validate", methods=["POST"])
def api_validate_license():
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()
    if not key:
        return jsonify({"valid": False, "reason": "No key provided"}), 400
    result = validate_license(key)
    status = 200 if result["valid"] else 403
    return jsonify(result), status


@pricing_bp.route("/api/license/generate", methods=["POST"])
def api_generate_license():
    if not session.get("is_founder"):
        return jsonify({"error": "Founder access required"}), 403
    data = request.get_json(silent=True) or {}
    tier = (data.get("tier") or "SIG").upper()
    owner_name = data.get("owner_name", "")
    owner_email = data.get("owner_email", "")
    repo_url = data.get("repo_url", "")
    try:
        result = generate_license(tier, owner_name, owner_email, repo_url)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@pricing_bp.route("/api/license/list", methods=["GET"])
def api_list_licenses():
    if not session.get("is_founder"):
        return jsonify({"error": "Founder access required"}), 403
    return jsonify(list_licenses()), 200


@pricing_bp.route("/api/license/revoke", methods=["POST"])
def api_revoke_license():
    if not session.get("is_founder"):
        return jsonify({"error": "Founder access required"}), 403
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()
    ok = revoke_license(key)
    return jsonify({"revoked": ok}), 200
