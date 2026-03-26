import time
import logging
from flask import Blueprint, render_template, jsonify
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
from void_engine.db_pool import get_db
from void_engine.adriana_scl import AdrianaResonance, hash_to_sovereign_poem

logger = logging.getLogger(__name__)
sovereign_node_bp = Blueprint("sovereign_node", __name__)

GLYPH_COUNT = len(AdrianaResonance.GLYPHS)


def _get_live_metrics():
    metrics = {
        "total_users": 0,
        "active_nodes": 0,
        "vtx_in_circulation": "0.000",
        "tokens_minted": 0,
        "tokens_sold": 0,
        "tokens_common": 0,
        "tokens_rare": 0,
        "tokens_legendary": 0,
        "yield_events": 0,
        "yield_distributed_vtx": "0.000",
        "total_messages": 0,
        "chronicle_chapters": 0,
        "encode_operations": 0,
        "decode_operations": 0,
        "ledger_blocks": 0,
        "mystery_minted": 0,
        "mystery_total": 1000,
        "mystery_remaining": 1000,
        "secondary_listings": 0,
        "rental_offers": 0,
    }
    conn = get_db()
    try:
        cur = conn.cursor()

        try:
            cur.execute("SELECT COUNT(*) FROM users")
            r = cur.fetchone()
            if r:
                metrics["total_users"] = r[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM node_registrations WHERE status = 'active'")
            r = cur.fetchone()
            if r:
                metrics["active_nodes"] = r[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT COALESCE(SUM(vortex_balance), 0) FROM users")
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
            cur.execute("SELECT COUNT(*) FROM blueprint_tokens WHERE tier = 'common'")
            r = cur.fetchone()
            if r:
                metrics["tokens_common"] = r[0]
            cur.execute("SELECT COUNT(*) FROM blueprint_tokens WHERE tier = 'rare'")
            r = cur.fetchone()
            if r:
                metrics["tokens_rare"] = r[0]
            cur.execute("SELECT COUNT(*) FROM blueprint_tokens WHERE tier = 'legendary'")
            r = cur.fetchone()
            if r:
                metrics["tokens_legendary"] = r[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM yield_events")
            r = cur.fetchone()
            if r:
                metrics["yield_events"] = r[0]
            cur.execute("SELECT COALESCE(SUM(amount_vtx), 0) FROM yield_events")
            r = cur.fetchone()
            if r and r[0] is not None:
                metrics["yield_distributed_vtx"] = f"{float(r[0]):.3f}"
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

        try:
            cur.execute("SELECT COUNT(*) FROM vortex_ledger WHERE tx_type = 'mint_resonance'")
            r = cur.fetchone()
            if r:
                metrics["encode_operations"] = r[0]
            cur.execute("SELECT COUNT(*) FROM vortex_ledger WHERE tx_type = 'mint_relay'")
            r = cur.fetchone()
            if r:
                metrics["decode_operations"] = r[0]
            cur.execute("SELECT COUNT(*) FROM vortex_ledger")
            r = cur.fetchone()
            if r:
                metrics["ledger_blocks"] = r[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT minted_count, total_supply FROM mystery_collection LIMIT 1")
            r = cur.fetchone()
            if r:
                metrics["mystery_minted"] = int(r[0])
                metrics["mystery_total"] = int(r[1])
                metrics["mystery_remaining"] = int(r[1]) - int(r[0])
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM token_listings WHERE status = 'active'")
            r = cur.fetchone()
            if r:
                metrics["secondary_listings"] = r[0]
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM token_rentals WHERE status = 'offered'")
            r = cur.fetchone()
            if r:
                metrics["rental_offers"] = r[0]
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
    date_str = time.strftime("%Y-%m-%d", time.gmtime())
    page_hash = fatiha_286_hexdigest_from_str(timestamp)
    poem_seed_raw = f"VOID|{date_str}"
    poem_seed_hash = fatiha_286_hexdigest_from_str(poem_seed_raw)
    metrics = _get_live_metrics()
    poem_data = None
    try:
        poem_dict = hash_to_sovereign_poem(poem_seed_hash)
        glyphs = poem_dict["glyphs"]
        meanings = poem_dict["meanings"]
        parts = [m.split("/")[0].strip() for m in meanings]
        poem_data = {
            "glyphs": glyphs,
            "meanings": meanings,
            "translation": f"Where {parts[0]} meets {parts[1]}, {parts[2]} emerges.",
            "poem": poem_dict["poem"],
            "seed": poem_seed,
        }
    except Exception:
        pass

    return render_template(
        "sovereign_node.html",
        page_hash=page_hash,
        timestamp=timestamp,
        metrics=metrics,
        poem=poem_data,
        glyph_count=GLYPH_COUNT,
    )


@sovereign_node_bp.route("/api/sovereign-node/metrics")
def api_sovereign_node_metrics():
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    page_hash = fatiha_286_hexdigest_from_str(timestamp)
    metrics = _get_live_metrics()
    return jsonify({
        "timestamp": timestamp,
        "al_jabr_hash": page_hash,
        "metrics": metrics,
    })
