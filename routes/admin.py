import os
import logging
from flask import Blueprint, request, redirect, render_template
from routes.auth import admin_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


def _get_db():
    import psycopg2
    return psycopg2.connect(os.environ["DATABASE_URL"])


@admin_bp.route("/admin/market", methods=["GET"])
@admin_required
def admin_market_get():
    conn = _get_db()
    updated = request.args.get("updated")
    error = request.args.get("error")
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

    return render_template("admin_market.html", configs=configs, updated=updated, error=error)


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
