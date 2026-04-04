"""
Sales Intelligence — PROJECT VOID
===================================
Routes:
  GET  /sales-intel          — ICP command-room page (no auth required)
  GET  /sales-intel/export.csv — Downloadable prospect grid CSV
"""

import csv
import io
import logging
from flask import Blueprint, render_template, Response

logger = logging.getLogger(__name__)

sales_intel_bp = Blueprint("sales_intel", __name__)

DEADLINE_ISO = "2026-04-06T00:00:00Z"


def _get_data():
    from void_engine.sales_intel import ICP_TIERS, PROSPECTS
    return ICP_TIERS, PROSPECTS


def _enrich_prospects(prospects: dict) -> dict:
    """Add org_key to each prospect dict for outreach link generation."""
    from void_engine.outreach_engine import _make_org_key
    enriched = {}
    for tier_id, tier_prospects in prospects.items():
        enriched[tier_id] = []
        for p in tier_prospects:
            enriched_p = dict(p)
            enriched_p["org_key"] = _make_org_key(p["org"])
            enriched[tier_id].append(enriched_p)
    return enriched


@sales_intel_bp.route("/sales-intel")
def sales_intel_page():
    icp_tiers, prospects = _get_data()
    enriched = _enrich_prospects(prospects)
    return render_template(
        "sales_intel.html",
        icp_tiers=icp_tiers,
        prospects=enriched,
        deadline_iso=DEADLINE_ISO,
    )


@sales_intel_bp.route("/sales-intel/export.csv")
def sales_intel_csv():
    from void_engine.sales_intel import get_all_prospects_flat
    rows = get_all_prospects_flat()

    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    csv_bytes = buf.getvalue().encode("utf-8")
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=void_prospect_grid.csv",
            "Content-Type": "text/csv; charset=utf-8",
        },
    )
