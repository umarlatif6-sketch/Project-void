import time
import logging
from flask import Blueprint, render_template, jsonify
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
from void_engine.db_pool import get_db
from void_engine.adriana_scl import AdrianaResonance

logger = logging.getLogger(__name__)
sovereign_node_bp = Blueprint("sovereign_node", __name__)


def _get_live_metrics():
    metrics = {
        "total_users": 0,
        "active_nodes": 0,
        "vtx_in_circulation": "0.000",
        "tokens_minted": 0,
        "tokens_sold": 0,
        "yield_distributed": "0.000",
        "total_messages": 0,
        "chronicle_chapters": 0,
    }
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        r = cur.fetchone()
        if r:
            metrics["total_users"] = r[0]

        try:
            cur.execute("SELECT COUNT(*) FROM node_registrations WHERE status = 'active'")
            r = cur.fetchone()
            if r:
                metrics["active_nodes"] = r[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT SUM(balance) FROM vtx_wallets")
            r = cur.fetchone()
            if r and r[0] is not None:
                metrics["vtx_in_circulation"] = f"{float(r[0]):.3f}"
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM blueprint_tokens")
            r = cur.fetchone()
            if r:
                metrics["tokens_minted"] = r[0]
            cur.execute("SELECT COUNT(*) FROM blueprint_tokens WHERE status != 'available'")
            r = cur.fetchone()
            if r:
                metrics["tokens_sold"] = r[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT SUM(amount) FROM yield_distributions WHERE status = 'paid'")
            r = cur.fetchone()
            if r and r[0] is not None:
                metrics["yield_distributed"] = f"{float(r[0]):.3f}"
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM messages")
            r = cur.fetchone()
            if r:
                metrics["total_messages"] = r[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM chronicle_entries")
            r = cur.fetchone()
            if r:
                metrics["chronicle_chapters"] = r[0]
        except Exception:
            pass

    except Exception as e:
        logger.warning("Metrics query failed: %s", e)
    finally:
        conn.close()

    return metrics


@sovereign_node_bp.route("/sovereign-node")
def sovereign_node_portfolio():
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    page_hash = fatiha_286_hexdigest_from_str(f"sovereign-node|{timestamp}")
    metrics = _get_live_metrics()
    try:
        import hashlib
        seed = f"gridul-286|novosibirsk|{timestamp}"
        hex_seed = hashlib.sha256(seed.encode()).hexdigest()
        poem_raw = AdrianaResonance.calculate_resonance(hex_seed)
        from void_engine.adriana_scl import hash_to_sovereign_poem
        poem_dict = hash_to_sovereign_poem(page_hash)
        glyphs = poem_dict["glyphs"]
        meanings = poem_dict["meanings"]
        def _translation(g, m):
            parts = [x.split("/")[0].strip() for x in m]
            return f"Where {parts[0]} meets {parts[1]}, {parts[2]} emerges."
        poem_data = {
            "glyphs": glyphs,
            "meanings": meanings,
            "translation": _translation(glyphs, meanings),
        }
    except Exception:
        poem_data = None
    return render_template(
        "sovereign_node.html",
        page_hash=page_hash,
        timestamp=timestamp,
        metrics=metrics,
        poem=poem_data,
    )


@sovereign_node_bp.route("/api/sovereign-node/metrics")
def api_sovereign_node_metrics():
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    page_hash = fatiha_286_hexdigest_from_str(f"sovereign-node|{timestamp}")
    metrics = _get_live_metrics()
    return jsonify({
        "timestamp": timestamp,
        "al_jabr_hash": page_hash,
        "metrics": metrics,
    })
