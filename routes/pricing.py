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


@pricing_bp.route("/pricing")
def pricing_page():
    tiers = [
        {
            "code": "SIG",
            "name": "Signal",
            "price": 49,
            "tagline": "Your first frequency attribution layer",
            "features": TIER_FEATURES["SIG"],
            "cta": "Install Signal",
        },
        {
            "code": "MEM",
            "name": "Memory",
            "price": 149,
            "tagline": "AI that remembers who your users are",
            "features": TIER_FEATURES["MEM"],
            "cta": "Install Memory",
            "highlight": True,
        },
        {
            "code": "SOV",
            "name": "Sovereign",
            "price": 449,
            "tagline": "The full engine. Nothing held back.",
            "features": TIER_FEATURES["SOV"],
            "cta": "Install Sovereign",
        },
    ]
    return render_template("pricing.html", tiers=tiers)


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
