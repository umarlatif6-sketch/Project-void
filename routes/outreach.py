"""
Sovereign Outreach Engine — PROJECT VOID
==========================================

Routes:
  GET  /outreach                        — Two-panel outreach engine page
  GET  /api/outreach/generate           — JSON outreach text (email|x_thread|whatsapp)
                                          ?prospect=<org_key>&format=<fmt>
"""

import logging
import time
from collections import defaultdict

from flask import Blueprint, render_template, request, jsonify

logger = logging.getLogger(__name__)

outreach_bp = Blueprint("outreach", __name__)

# ── RATE LIMITING ─────────────────────────────────────────────────────────────
# 60 requests / hour per IP (same pattern as cross_ai_verifier.py)
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 60
_RATE_WINDOW = 3600


def _check_rate_limit(ip: str) -> bool:
    """Return True if the request is within the rate limit."""
    now = time.time()
    window_start = now - _RATE_WINDOW
    calls = _rate_store[ip]
    calls[:] = [t for t in calls if t > window_start]
    if len(calls) >= _RATE_LIMIT:
        return False
    calls.append(now)
    return True


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _get_prospects_data():
    from void_engine.outreach_engine import get_all_prospects_with_keys
    from void_engine.sales_intel import ICP_TIERS, PROSPECTS
    return ICP_TIERS, PROSPECTS, get_all_prospects_with_keys()


def _build_prospect_list(icp_tiers, prospects):
    """
    Build an ordered list of prospects grouped by tier.
    InteRussia is guaranteed to appear first.
    """
    grouped = []
    for tier in icp_tiers:
        tier_id = tier["id"]
        tier_prospects = []
        for p in prospects.get(tier_id, []):
            from void_engine.outreach_engine import _make_org_key
            tier_prospects.append({
                **p,
                "tier_id": tier_id,
                "tier_label": tier["label"],
                "tier_color": tier["color"],
                "org_key": _make_org_key(p["org"]),
            })
        grouped.append({
            "tier": tier,
            "prospects": tier_prospects,
        })
    return grouped


# ── PAGE ROUTE ────────────────────────────────────────────────────────────────

@outreach_bp.route("/outreach")
def outreach_page():
    icp_tiers, prospects, all_prospects = _get_prospects_data()
    grouped = _build_prospect_list(icp_tiers, prospects)

    default_prospect_key = request.args.get("prospect", "interussia_smart_cities")
    default_format = request.args.get("format", "email")

    from void_engine.outreach_engine import get_prospect_by_key, generate_outreach
    default_prospect = get_prospect_by_key(default_prospect_key)
    if default_prospect is None:
        default_prospect = all_prospects[0] if all_prospects else None

    default_output = None
    if default_prospect:
        try:
            default_output = generate_outreach(default_prospect, default_format)
        except Exception as e:
            logger.warning("Failed to generate default outreach: %s", e)

    return render_template(
        "outreach.html",
        grouped=grouped,
        default_prospect=default_prospect,
        default_format=default_format,
        default_output=default_output,
    )


# ── API ENDPOINT ──────────────────────────────────────────────────────────────

@outreach_bp.route("/api/outreach/generate")
def api_generate_outreach():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    if not _check_rate_limit(ip):
        return jsonify({"error": "Rate limit exceeded. Max 60 requests per hour."}), 429

    org_key = request.args.get("prospect", "").strip()
    fmt = request.args.get("format", "email").strip().lower()

    if not org_key:
        return jsonify({"error": "Missing required parameter: prospect"}), 400

    if fmt not in ("email", "x_thread", "whatsapp"):
        return jsonify({"error": "format must be one of: email, x_thread, whatsapp"}), 400

    from void_engine.outreach_engine import get_prospect_by_key, generate_outreach
    prospect = get_prospect_by_key(org_key)
    if prospect is None:
        return jsonify({"error": f"Prospect not found: {org_key!r}"}), 404

    try:
        result = generate_outreach(prospect, fmt)
        return jsonify(result)
    except Exception as e:
        logger.error("Outreach generation failed for prospect=%s fmt=%s: %s", org_key, fmt, e)
        return jsonify({"error": "Outreach generation failed. Please try again."}), 500
