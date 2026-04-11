"""
VOID Memory Layer — SQLite (local) + PostgreSQL (production)
PROJECT VOID | Umar Latif | Bolton, England | April 2026

The memory layer stores Entity · Condition · Action events.
Every event is a formation record — not analytics, not telemetry.
The system tracks *meaning*, not clicks.

Event schema:
  id          — auto-increment
  ts          — unix timestamp (float)
  entity      — who/what acted (user_id, ai_name, document_id)
  condition   — the state/context (frequency_hz, formation_score, resonance_level)
  action      — what happened (encode, decode, seal, transmit, form)
  codon       — which platform codon applies (voidecho, adriana, chronicle…)
  digest      — Al-Jabr 286 hash of the event
  meta        — JSON blob for additional context
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional


CREATE_SQL = """
CREATE TABLE IF NOT EXISTS void_events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        REAL NOT NULL,
    entity    TEXT NOT NULL,
    condition TEXT NOT NULL,
    action    TEXT NOT NULL,
    codon     TEXT NOT NULL,
    digest    TEXT NOT NULL,
    meta      TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_void_entity ON void_events(entity);
CREATE INDEX IF NOT EXISTS idx_void_codon  ON void_events(codon);
CREATE INDEX IF NOT EXISTS idx_void_ts     ON void_events(ts);
"""


class VoidMemory:
    """
    Local SQLite memory store. One file, zero dependencies.
    Drop-in — no server, no credentials, no setup.

    For production PostgreSQL, use VoidMemoryPG (requires psycopg2).
    """

    def __init__(self, db_path: str = ".void_memory.db"):
        self.db_path = db_path
        self._init()

    def _init(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(CREATE_SQL)
        conn.commit()
        conn.close()

    def record(
        self,
        entity: str,
        condition: str,
        action: str,
        codon: str,
        digest: str,
        meta: Optional[dict] = None,
        ts: Optional[float] = None,
    ) -> int:
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO void_events (ts, entity, condition, action, codon, digest, meta) VALUES (?,?,?,?,?,?,?)",
            (
                ts or time.time(),
                entity,
                condition,
                action,
                codon,
                digest,
                json.dumps(meta or {}),
            ),
        )
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def recall(
        self,
        entity: Optional[str] = None,
        codon: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        filters, params = [], []
        if entity:
            filters.append("entity = ?")
            params.append(entity)
        if codon:
            filters.append("codon = ?")
            params.append(codon)
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        params.append(limit)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT * FROM void_events {where} ORDER BY ts DESC LIMIT ?",
            params,
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM void_events").fetchone()[0]
        by_codon = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT codon, COUNT(*) FROM void_events GROUP BY codon ORDER BY 2 DESC"
            ).fetchall()
        }
        conn.close()
        return {"total_events": total, "by_codon": by_codon}

    def events_today(self, entity: str) -> int:
        day_start = time.time() - (time.time() % 86400)
        conn = sqlite3.connect(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM void_events WHERE entity=? AND ts>=?",
            (entity, day_start),
        ).fetchone()[0]
        conn.close()
        return count


try:
    import psycopg2
    import psycopg2.extras

    class VoidMemoryPG:
        """
        PostgreSQL memory store for production deployments.
        Requires psycopg2: pip install psycopg2-binary
        """

        CREATE_SQL_PG = """
        CREATE TABLE IF NOT EXISTS void_events (
            id        SERIAL PRIMARY KEY,
            ts        DOUBLE PRECISION NOT NULL,
            entity    TEXT NOT NULL,
            condition TEXT NOT NULL,
            action    TEXT NOT NULL,
            codon     TEXT NOT NULL,
            digest    TEXT NOT NULL,
            meta      JSONB DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_void_entity ON void_events(entity);
        CREATE INDEX IF NOT EXISTS idx_void_codon  ON void_events(codon);
        CREATE INDEX IF NOT EXISTS idx_void_ts     ON void_events(ts);
        """

        def __init__(self, dsn: str):
            self.dsn = dsn
            self._init()

        def _conn(self):
            return psycopg2.connect(self.dsn)

        def _init(self):
            conn = self._conn()
            with conn.cursor() as cur:
                cur.execute(self.CREATE_SQL_PG)
            conn.commit()
            conn.close()

        def record(self, entity, condition, action, codon, digest, meta=None, ts=None):
            conn = self._conn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO void_events (ts,entity,condition,action,codon,digest,meta) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                    (ts or time.time(), entity, condition, action, codon, digest, json.dumps(meta or {})),
                )
                row_id = cur.fetchone()[0]
            conn.commit()
            conn.close()
            return row_id

        def recall(self, entity=None, codon=None, limit=50):
            filters, params = [], []
            if entity:
                filters.append("entity=%s")
                params.append(entity)
            if codon:
                filters.append("codon=%s")
                params.append(codon)
            where = ("WHERE " + " AND ".join(filters)) if filters else ""
            params.append(limit)
            conn = self._conn()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM void_events {where} ORDER BY ts DESC LIMIT %s", params)
                rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return rows

        def stats(self):
            conn = self._conn()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM void_events")
                total = cur.fetchone()[0]
                cur.execute("SELECT codon, COUNT(*) FROM void_events GROUP BY codon ORDER BY 2 DESC")
                by_codon = {r[0]: r[1] for r in cur.fetchall()}
            conn.close()
            return {"total_events": total, "by_codon": by_codon}

        def events_today(self, entity: str) -> int:
            day_start = time.time() - (time.time() % 86400)
            conn = self._conn()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM void_events WHERE entity=%s AND ts>=%s", (entity, day_start))
                count = cur.fetchone()[0]
            conn.close()
            return count

except ImportError:
    pass
