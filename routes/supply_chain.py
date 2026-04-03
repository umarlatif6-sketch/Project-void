"""
Supply Chain Route — PROJECT VOID
Routes for the Physical Supply Chain Intelligence page.
"""

import csv
import io
import logging
from flask import Blueprint, render_template, request, Response

logger = logging.getLogger(__name__)

supply_chain_bp = Blueprint("supply_chain", __name__)


@supply_chain_bp.route("/supply-chain")
def supply_chain_page():
    from void_engine.supply_chain import get_all_categories, SCORE_WEIGHTS
    categories = get_all_categories()
    return render_template(
        "supply_chain.html",
        categories=categories,
        score_weights=SCORE_WEIGHTS,
    )


@supply_chain_bp.route("/supply-chain/rfq.html")
def supply_chain_rfq():
    from void_engine.supply_chain import get_rfq_template, get_all_rfq_templates, ALL_CATEGORIES
    category_id = request.args.get("category", "").strip().lower()
    if category_id:
        template = get_rfq_template(category_id)
        if not template:
            from flask import abort
            abort(404)
        templates = {category_id: template}
        single = True
        cat_name = template["category_name"]
    else:
        templates = get_all_rfq_templates()
        single = False
        cat_name = "All Categories"

    categories = ALL_CATEGORIES
    return render_template(
        "supply_chain_rfq.html",
        templates=templates,
        single=single,
        cat_name=cat_name,
        categories=categories,
        selected_id=category_id,
    )


@supply_chain_bp.route("/supply-chain/export.csv")
def supply_chain_export_csv():
    from void_engine.supply_chain import get_vendor_matrix_rows
    rows = get_vendor_matrix_rows()
    output = io.StringIO()
    fieldnames = [
        "category_id", "category_name", "vendor_name", "location", "specialisation",
        "estimated_cost_range", "lead_time", "compliance",
        "quality_score", "cost_score", "delivery_score",
        "capability_score", "reliability_score", "compliance_score",
        "weighted_total", "role", "recommended",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    csv_bytes = output.getvalue().encode("utf-8")
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=void_vendor_matrix.csv",
            "Content-Length": str(len(csv_bytes)),
        },
    )
