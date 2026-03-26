import os
import logging
from void_engine.db_pool import get_db

logger = logging.getLogger(__name__)


def _get_db():
    return get_db()


def get_market_price(item_key):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT gbp_pence, vtx_cost, display_name FROM market_configs WHERE item_key = %s AND is_active = TRUE",
            (item_key,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "gbp": row[0],
            "vtx": row[1],
            "display_name": row[2],
        }
    except Exception as e:
        logger.error("get_market_price(%s) DB error: %s", item_key, e)
        raise RuntimeError(f"Market price lookup failed for {item_key!r}: {e}") from e
    finally:
        conn.close()
