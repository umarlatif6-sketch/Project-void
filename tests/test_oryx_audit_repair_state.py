import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORYX_BACKEND = ROOT / ".oryx" / "backend"
if str(ORYX_BACKEND) not in sys.path:
    sys.path.insert(0, str(ORYX_BACKEND))

from oryx_engine.auth_store import AuthStore, audit_repair_state_for_action


def _create_old_schema_without_repair_state(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS world_ownership (
            world_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS world_collaborators (
            world_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(world_id, user_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS world_feature_permissions (
            world_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            can_view_world INTEGER,
            can_step_world INTEGER,
            can_manage_agents INTEGER,
            can_manage_quests INTEGER,
            can_manage_stream INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(world_id, user_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS world_invites (
            token TEXT PRIMARY KEY,
            world_id TEXT NOT NULL,
            role TEXT NOT NULL,
            created_by_user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            used_by_user_id INTEGER,
            used_at DATETIME,
            revoked_at DATETIME
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS world_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            world_id TEXT NOT NULL,
            actor_user_id INTEGER,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT,
            details_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def test_auth_store_migration_adds_repair_state_column(tmp_path: Path) -> None:
    db_path = tmp_path / "oryx_migration.db"
    _create_old_schema_without_repair_state(db_path)

    AuthStore(db_path)

    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(world_audit_log)").fetchall()}
    conn.close()

    assert "repair_state" in cols


def test_log_event_persists_repair_state(tmp_path: Path) -> None:
    db_path = tmp_path / "oryx_store.db"
    store = AuthStore(db_path)

    store.log_event(
        world_id="w1",
        action="invite_revoked",
        target_type="invite",
        target_id="tok1",
        details={"note": "test"},
    )
    store.log_event(
        world_id="w1",
        action="manual_override",
        target_type="world",
        repair_state="quarantined",
        details={"note": "explicit"},
    )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT action, repair_state, details_json FROM world_audit_log ORDER BY id ASC"
    ).fetchall()
    conn.close()

    assert rows[0]["repair_state"] == "recoverable"
    assert "repair_state" in rows[0]["details_json"]
    assert rows[1]["repair_state"] == "quarantined"


def test_list_and_count_filter_on_persisted_repair_state(tmp_path: Path) -> None:
    db_path = tmp_path / "oryx_filters.db"
    store = AuthStore(db_path)

    store.log_event(world_id="w2", action="invite_revoked", target_type="invite")
    store.log_event(world_id="w2", action="stream_tick", target_type="world")
    store.log_event(
        world_id="w2",
        action="manual_review",
        target_type="world",
        repair_state="quarantined",
    )

    recoverable = store.list_audit_log("w2", limit=50, repair_state="recoverable")
    aligned = store.list_audit_log("w2", limit=50, repair_state="aligned")
    quarantined = store.list_audit_log("w2", limit=50, repair_state="quarantined")

    assert len(recoverable) == 1
    assert recoverable[0]["repair_state"] == "recoverable"
    assert len(aligned) == 1
    assert aligned[0]["repair_state"] == "aligned"
    assert len(quarantined) == 1
    assert quarantined[0]["repair_state"] == "quarantined"

    assert store.count_audit_log("w2", repair_state="recoverable") == 1
    assert store.count_audit_log("w2", repair_state="aligned") == 1
    assert store.count_audit_log("w2", repair_state="quarantined") == 1


def test_audit_repair_state_for_action_defaults_to_aligned() -> None:
    assert audit_repair_state_for_action("unknown_action") == "aligned"
