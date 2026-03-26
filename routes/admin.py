import os
import math
import logging
from flask import Blueprint, request, redirect, render_template, session
from routes.auth import admin_required
from void_engine.db_pool import get_db

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


def _get_db():
    return get_db()


@admin_bp.route("/admin/market", methods=["GET"])
@admin_required
def admin_market_get():
    conn = _get_db()
    updated = request.args.get("updated")
    error = request.args.get("error")
    yield_error = request.args.get("yield_error")
    yield_posted = request.args.get("yield_posted")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, item_key, display_name, gbp_pence, vtx_cost, is_active, updated_at FROM market_configs ORDER BY id"
        )
        rows = cur.fetchall()
        configs = [
            {
                "id": r[0],
                "item_key": r[1],
                "display_name": r[2],
                "gbp_pence": r[3],
                "gbp_display": f"{r[3] / 100:.2f}",
                "vtx_cost": float(r[4]),
                "is_active": r[5],
                "updated_at": r[6].strftime("%Y-%m-%d %H:%M") if r[6] else "",
            }
            for r in rows
        ]
    except Exception as e:
        logger.error("Failed to load market_configs: %s", e)
        configs = []
    finally:
        conn.close()

    from void_engine.blueprint_nft import get_yield_events
    try:
        yield_events = get_yield_events(10)
    except Exception as e:
        logger.error("Failed to load yield_events: %s", e)
        yield_events = []

    return render_template(
        "admin_market.html",
        configs=configs,
        updated=updated,
        error=error,
        yield_error=yield_error,
        yield_posted=yield_posted,
        yield_events=yield_events,
    )


@admin_bp.route("/admin/market", methods=["POST"])
@admin_required
def admin_market_post():
    item_key = (request.form.get("item_key") or "").strip()
    try:
        gbp_pence = round(float(request.form.get("gbp_pounds", 0)) * 100)
    except (ValueError, TypeError):
        gbp_pence = None

    try:
        vtx_cost = float(request.form.get("vtx_cost", 0))
        if math.isnan(vtx_cost):
            vtx_cost = None
    except (ValueError, TypeError):
        vtx_cost = None

    is_active = request.form.get("is_active") == "1"

    if not item_key or gbp_pence is None or vtx_cost is None or gbp_pence < 0 or vtx_cost < 0:
        return redirect("/admin/market?error=invalid_input")

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE market_configs
               SET gbp_pence = %s, vtx_cost = %s, is_active = %s, updated_at = NOW()
               WHERE item_key = %s""",
            (gbp_pence, vtx_cost, is_active, item_key),
        )
        conn.commit()
        logger.info("Admin updated market_configs[%s]: gbp=%d vtx=%s active=%s", item_key, gbp_pence, vtx_cost, is_active)
    except Exception as e:
        logger.error("Failed to update market_configs: %s", e)
        conn.rollback()
        return redirect(f"/admin/market?error=db_error")
    finally:
        conn.close()

    return redirect(f"/admin/market?updated={item_key}")


@admin_bp.route("/admin/yield", methods=["POST"])
@admin_required
def admin_post_yield():
    from void_engine.blueprint_nft import post_yield_event
    try:
        amount_vtx = float(request.form.get("amount_vtx", 0))
        if math.isnan(amount_vtx):
            raise ValueError("NaN not allowed")
        amount_gbp_str = request.form.get("amount_gbp", "0").replace(",", "").replace("£", "").strip()
        try:
            amount_gbp = round(float(amount_gbp_str) * 100)
        except (ValueError, TypeError):
            amount_gbp = 0
        notes = (request.form.get("notes") or "").strip()
        idempotency_key = (request.form.get("idempotency_key") or "").strip() or None
    except (ValueError, TypeError):
        return redirect("/admin/market?yield_error=invalid_input")

    if amount_vtx <= 0:
        return redirect("/admin/market?yield_error=invalid_input")

    admin_id = session.get("user_id")
    result = post_yield_event(amount_vtx, notes or None, admin_id, amount_gbp, idempotency_key)
    if "error" in result:
        return redirect(f"/admin/market?yield_error={result['error']}")
    return redirect(f"/admin/market?yield_posted={result['event_id']}")
