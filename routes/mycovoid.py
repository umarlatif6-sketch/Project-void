import time
import logging
from flask import Blueprint, render_template, session, jsonify
from routes.auth import login_required

logger = logging.getLogger(__name__)

mycovoid_bp = Blueprint("mycovoid", __name__)

_GRIDUL_COLUMNS_READY: bool = False


@mycovoid_bp.route("/mycovoid")
def mycovoid_page():
    return render_template(
        "mycovoid.html",
        username=session.get("username", ""),
        user_tier=session.get("tier", "ghost"),
    )


@mycovoid_bp.route("/mrb4000")
def mrb4000_page():
    return render_template(
        "mrb4000.html",
        username=session.get("username", ""),
        user_tier=session.get("tier", "ghost"),
    )


@mycovoid_bp.route("/api/mycovoid/status")
@login_required
def mycovoid_status():
    """
    Run one mycelium simulation step and return the current network state as
    a JSON dashboard payload.

    Returns:
      active_nodes, total_resource_flow, strongest_signal_path,
      avg_signal_strength, step_count, uptime_sec, node_breakdown
    """
    try:
        from void_engine.mycelium_service import get_network_status
        status = get_network_status(run_steps=1)

        try:
            _feed_mycelium_to_gridul(
                active_nodes=status["active_nodes"],
                resource_flow=status.get("total_resource_flow", 0.0),
            )
        except Exception:
            pass

        return jsonify({"ok": True, "network": status})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


def _ensure_gridul_columns() -> None:
    """Run ALTER TABLE to add mycelium columns exactly once per process lifetime."""
    global _GRIDUL_COLUMNS_READY
    if _GRIDUL_COLUMNS_READY:
        return
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                ALTER TABLE gridul_grow_zones
                ADD COLUMN IF NOT EXISTS mycelium_resonance NUMERIC(6,4) DEFAULT 0
            """)
            cur.execute("""
                ALTER TABLE gridul_grow_zones
                ADD COLUMN IF NOT EXISTS mycelium_updated_at TIMESTAMPTZ DEFAULT NOW()
            """)
            conn.commit()
            _GRIDUL_COLUMNS_READY = True
            logger.info("gridul_grow_zones mycelium columns ensured")
        finally:
            conn.close()
    except Exception as exc:
        logger.debug("_ensure_gridul_columns failed (will retry): %s", exc)


def _feed_mycelium_to_gridul(active_nodes: int, resource_flow: float = 0.0) -> None:
    """
    Propagate mycelium network activity into GriDul grow zone resonance.

    Columns are ensured once per process; subsequent calls only write to
    rows stale by more than 5 minutes, preventing excessive write amplification
    on unauthenticated polling.
    """
    _ensure_gridul_columns()
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()

            # Compute resonance from network metrics (0–100 scale)
            node_factor = min(active_nodes / 48.0, 1.0)
            flow_factor = min(resource_flow / 50.0, 1.0)
            resonance = round((node_factor * 60.0 + flow_factor * 40.0), 4)

            # Update all grow zones with the current mycelium resonance reading
            cur.execute("""
                UPDATE gridul_grow_zones
                SET mycelium_resonance = %s,
                    mycelium_updated_at = NOW()
                WHERE mycelium_updated_at < NOW() - INTERVAL '5 minutes'
                   OR mycelium_updated_at IS NULL
            """, (resonance,))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
