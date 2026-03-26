import os
import logging
import threading
from psycopg2 import pool as pg_pool
from psycopg2 import extensions as pg_ext

logger = logging.getLogger(__name__)

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                dsn = os.environ.get("DATABASE_URL")
                if not dsn:
                    raise RuntimeError("DATABASE_URL environment variable is not set")
                _pool = pg_pool.ThreadedConnectionPool(minconn=1, maxconn=10, dsn=dsn)
                logger.info("DB connection pool initialised (minconn=1, maxconn=10)")
    return _pool


class _PooledConn:
    """
    Thin wrapper around a psycopg2 connection drawn from the pool.
    Calling .close() returns the connection to the pool rather than
    closing it, so all existing `conn.close()` call sites continue to
    work without modification.
    """

    def __init__(self, real_conn):
        object.__setattr__(self, "_real_conn", real_conn)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real_conn"), name)

    def __setattr__(self, name, value):
        if name == "_real_conn":
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, "_real_conn"), name, value)

    def close(self):
        real = object.__getattribute__(self, "_real_conn")
        try:
            try:
                if real.info.transaction_status != pg_ext.TRANSACTION_STATUS_IDLE:
                    real.rollback()
            except Exception:
                pass
            _get_pool().putconn(real)
        except Exception as e:
            logger.warning("Failed to return connection to pool: %s", e)
            try:
                real.close()
            except Exception:
                pass


def get_db() -> _PooledConn:
    """
    Get a live connection from the pool. If the checked-out connection is
    stale (e.g. killed by the database server after an idle period in an
    autoscale environment), discard it and obtain a fresh one.
    """
    pool = _get_pool()
    for attempt in range(3):
        conn = pool.getconn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            if conn.info.transaction_status != pg_ext.TRANSACTION_STATUS_IDLE:
                conn.rollback()
            return _PooledConn(conn)
        except Exception as e:
            logger.warning("Stale connection discarded (attempt %d): %s", attempt + 1, e)
            try:
                pool.putconn(conn, close=True)
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
    raise RuntimeError("Could not obtain a live database connection after 3 attempts")
