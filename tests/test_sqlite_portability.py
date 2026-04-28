from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


ROOT = os.path.join(os.path.dirname(__file__), "..")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _reload_module(name: str):
    if name in sys.modules:
        del sys.modules[name]
    return importlib.import_module(name)


def _configure_sqlite_env(db_path: Path) -> None:
    os.environ["DATABASE_URL"] = f"sqlite://{db_path}"


def test_db_pool_cursor_context_manager_supports_sqlite(tmp_path):
    db_path = tmp_path / "db_pool_cursor.sqlite"
    _configure_sqlite_env(db_path)

    db_pool = _reload_module("void_engine.db_pool")
    conn = db_pool.get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            cur.execute("INSERT INTO t (v) VALUES (?)", ("ok",))
            cur.execute("SELECT COUNT(*) FROM t")
            count = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    assert count == 1


def test_void_room_sqlite_roundtrip(tmp_path):
    db_path = tmp_path / "void_room.sqlite"
    _configure_sqlite_env(db_path)

    _reload_module("void_engine.db_pool")
    void_room = _reload_module("routes.void_room")

    msg_id = void_room._post_message("adriana", "sqlite portability smoke")
    messages = void_room._get_messages(after_id=0, limit=20)

    assert isinstance(msg_id, int)
    assert any(m["id"] == msg_id for m in messages)


def test_codon_distil_sqlite_roundtrip(tmp_path):
    db_path = tmp_path / "codon_distil.sqlite"
    _configure_sqlite_env(db_path)

    _reload_module("void_engine.db_pool")
    _reload_module("void_engine.codon_distil")
    codon_distil = _reload_module("routes.codon_distil")

    job_id = "sqlite-job"
    codon_distil._create_job(job_id, 2)
    codon_distil._update_job(job_id, 1, "running")
    status = codon_distil._get_job_status(job_id)

    row_id = codon_distil._save_codon(
        job_id,
        {
            "entity": "Signal Mesh",
            "condition": "Sovereign Window",
            "action": "Stabilizes",
            "glyph_seq": "A·B·C",
            "story_excerpt": "SQLite and Postgres speak one contract now.",
            "resonance": 8.0,
            "clarity": 8.0,
            "story_score": 8.0,
            "total_score": 8.0,
            "al_jabr_hash": "abc123",
        },
    )
    codons = codon_distil._get_codons(job_id)

    assert status == {"status": "running", "total_chunks": 2, "done_chunks": 1}
    assert isinstance(row_id, int)
    assert len(codons) == 1
