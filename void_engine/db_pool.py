import os
import logging
import threading
import sqlite3

logger = logging.getLogger(__name__)

_pool = None
_pool_lock = threading.Lock()
_use_sqlite = False
_sqlite_db_path = None


def _build_sqlite_connection(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _get_pool():
    global _pool, _use_sqlite, _sqlite_db_path
    if _pool is None and _sqlite_db_path is None:
        with _pool_lock:
            if _pool is None and _sqlite_db_path is None:
                dsn = os.environ.get("DATABASE_URL")
                if not dsn:
                    _use_sqlite = True
                    _sqlite_db_path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "data", "void_dev.db")
                    )
                    os.makedirs(os.path.dirname(_sqlite_db_path), exist_ok=True)
                    logger.info("Using SQLite database for development: %s", _sqlite_db_path)
                    return None

                if dsn.startswith("sqlite://"):
                    _use_sqlite = True
                    _sqlite_db_path = dsn.replace("sqlite://", "", 1)
                    sqlite_dir = os.path.dirname(_sqlite_db_path)
                    if sqlite_dir:
                        os.makedirs(sqlite_dir, exist_ok=True)
                    logger.info("Using SQLite database: %s", _sqlite_db_path)
                else:
                    try:
                        from psycopg2 import pool as pg_pool
                        _pool = pg_pool.ThreadedConnectionPool(minconn=1, maxconn=10, dsn=dsn)
                        logger.info("DB connection pool initialised (minconn=1, maxconn=10)")
                    except ImportError:
                        raise RuntimeError("PostgreSQL not available and no DATABASE_URL set. Install psycopg2 or set DATABASE_URL to sqlite://path/to/db")
    return _pool


class _PooledConn:
    """
    Thin wrapper around a database connection.
    For PostgreSQL: returns connection to pool on close.
    For SQLite: just closes the connection.
    """

    def __init__(self, real_conn):
        object.__setattr__(self, "_real_conn", real_conn)
        object.__setattr__(self, "_is_sqlite", _use_sqlite)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real_conn"), name)

    def __setattr__(self, name, value):
        if name in ("_real_conn", "_is_sqlite"):
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, "_real_conn"), name, value)

    def close(self):
        real = object.__getattribute__(self, "_real_conn")
        if object.__getattribute__(self, "_is_sqlite"):
            real.close()
        else:
            try:
                try:
                    if hasattr(real, 'info') and hasattr(real.info, 'transaction_status'):
                        if real.info.transaction_status != 0:  # IDLE
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
    if _use_sqlite:
        if not _sqlite_db_path:
            raise RuntimeError("SQLite database path is not configured")

        conn = _build_sqlite_connection(_sqlite_db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return _PooledConn(conn)
        except Exception:
            conn.close()
            raise

    from psycopg2 import extensions as pg_ext

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
