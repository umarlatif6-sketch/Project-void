"""SQLite-backed creator account, collaboration, permissions, and audit store."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from secrets import token_hex
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash


FEATURE_KEYS = [
    "can_view_world",
    "can_step_world",
    "can_manage_agents",
    "can_manage_quests",
    "can_manage_stream",
    "can_manage_collaborators",
    "can_manage_invites",
    "can_manage_permissions",
]

RECOVERABLE_AUDIT_ACTIONS = {
    "collaborator_removed",
    "invite_revoked",
    "permissions_updated",
}

QUARANTINED_AUDIT_ACTIONS = {
    "stream_error",
}


def audit_repair_state_for_action(action: str) -> str:
    if action in QUARANTINED_AUDIT_ACTIONS:
        return "quarantined"
    if action in RECOVERABLE_AUDIT_ACTIONS:
        return "recoverable"
    return "aligned"

ROLE_DEFAULTS: dict[str, dict[str, bool]] = {
    "owner": {
        "can_view_world": True,
        "can_step_world": True,
        "can_manage_agents": True,
        "can_manage_quests": True,
        "can_manage_stream": True,
        "can_manage_collaborators": True,
        "can_manage_invites": True,
        "can_manage_permissions": True,
    },
    "editor": {
        "can_view_world": True,
        "can_step_world": True,
        "can_manage_agents": True,
        "can_manage_quests": True,
        "can_manage_stream": True,
        "can_manage_collaborators": False,
        "can_manage_invites": False,
        "can_manage_permissions": False,
    },
    "viewer": {
        "can_view_world": True,
        "can_step_world": False,
        "can_manage_agents": False,
        "can_manage_quests": False,
        "can_manage_stream": False,
        "can_manage_collaborators": False,
        "can_manage_invites": False,
        "can_manage_permissions": False,
    },
}


class AuthStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
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
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS world_ownership (
                    world_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS world_collaborators (
                    world_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('editor', 'viewer')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(world_id, user_id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
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
                    can_manage_collaborators INTEGER,
                    can_manage_invites INTEGER,
                    can_manage_permissions INTEGER,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(world_id, user_id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS world_invites (
                    token TEXT PRIMARY KEY,
                    world_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('editor', 'viewer')),
                    created_by_user_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    used_by_user_id INTEGER,
                    used_at DATETIME,
                    revoked_at DATETIME,
                    FOREIGN KEY(created_by_user_id) REFERENCES users(id),
                    FOREIGN KEY(used_by_user_id) REFERENCES users(id)
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
                    repair_state TEXT DEFAULT 'aligned',
                    details_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(actor_user_id) REFERENCES users(id)
                )
                """
            )
            self._run_migrations(conn)
            conn.commit()

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        invite_columns = {row['name'] for row in conn.execute("PRAGMA table_info(world_invites)").fetchall()}
        if 'expires_at' not in invite_columns:
            conn.execute("ALTER TABLE world_invites ADD COLUMN expires_at DATETIME")
        if 'used_by_user_id' not in invite_columns:
            conn.execute("ALTER TABLE world_invites ADD COLUMN used_by_user_id INTEGER")
        if 'used_at' not in invite_columns:
            conn.execute("ALTER TABLE world_invites ADD COLUMN used_at DATETIME")
        if 'revoked_at' not in invite_columns:
            conn.execute("ALTER TABLE world_invites ADD COLUMN revoked_at DATETIME")

        feature_columns = {row['name'] for row in conn.execute("PRAGMA table_info(world_feature_permissions)").fetchall()}
        if 'can_manage_collaborators' not in feature_columns:
            conn.execute("ALTER TABLE world_feature_permissions ADD COLUMN can_manage_collaborators INTEGER")
        if 'can_manage_invites' not in feature_columns:
            conn.execute("ALTER TABLE world_feature_permissions ADD COLUMN can_manage_invites INTEGER")
        if 'can_manage_permissions' not in feature_columns:
            conn.execute("ALTER TABLE world_feature_permissions ADD COLUMN can_manage_permissions INTEGER")

        audit_columns = {row['name'] for row in conn.execute("PRAGMA table_info(world_audit_log)").fetchall()}
        if 'repair_state' not in audit_columns:
            conn.execute("ALTER TABLE world_audit_log ADD COLUMN repair_state TEXT DEFAULT 'aligned'")

        default_expiry = (datetime.now(UTC) + timedelta(hours=72)).isoformat()
        conn.execute("UPDATE world_invites SET expires_at = COALESCE(expires_at, ?)", (default_expiry,))
        conn.execute("UPDATE world_audit_log SET repair_state = COALESCE(repair_state, 'aligned')")

    def create_user(self, *, email: str, password: str) -> int:
        with self._connect() as conn:
            exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if exists is not None:
                raise ValueError("Email already exists.")

            password_hash = generate_password_hash(password)
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def authenticate_and_issue_token(self, *, email: str, password: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
            if row is None:
                return None
            if not check_password_hash(row["password_hash"], password):
                return None

            token = token_hex(24)
            conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, row["id"]))
            conn.commit()
            return token

    def get_user_by_token(self, token: str) -> dict[str, Any] | None:
        if not token:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT users.id, users.email
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token = ?
                """,
                (token,),
            ).fetchone()
            return dict(row) if row else None

    def assign_world_to_user(self, *, user_id: int, world_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO world_ownership (world_id, user_id) VALUES (?, ?)",
                (world_id, user_id),
            )
            conn.commit()

    def owner_for_world(self, world_id: str) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id FROM world_ownership WHERE world_id = ?",
                (world_id,),
            ).fetchone()
            return int(row["user_id"]) if row else None

    def user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()
            return dict(row) if row else None

    def role_for_world(self, *, user_id: int, world_id: str) -> str | None:
        owner_id = self.owner_for_world(world_id)
        if owner_id == user_id:
            return "owner"
        with self._connect() as conn:
            row = conn.execute(
                "SELECT role FROM world_collaborators WHERE world_id = ? AND user_id = ?",
                (world_id, user_id),
            ).fetchone()
            return str(row["role"]) if row else None

    def get_effective_permissions(self, *, user_id: int, world_id: str) -> dict[str, bool]:
        role = self.role_for_world(user_id=user_id, world_id=world_id)
        if role is None:
            return {key: False for key in FEATURE_KEYS}

        permissions = dict(ROLE_DEFAULTS[role])
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT can_view_world, can_step_world, can_manage_agents, can_manage_quests, can_manage_stream,
                       can_manage_collaborators, can_manage_invites, can_manage_permissions
                FROM world_feature_permissions
                WHERE world_id = ? AND user_id = ?
                """,
                (world_id, user_id),
            ).fetchone()
            if row is not None:
                for key in FEATURE_KEYS:
                    value = row[key]
                    if value is not None:
                        permissions[key] = bool(value)
        return permissions

    def add_collaborator(self, *, world_id: str, email: str, role: str) -> dict[str, Any]:
        if role not in {"editor", "viewer"}:
            raise ValueError("Role must be 'editor' or 'viewer'.")

        user = self.user_by_email(email)
        if user is None:
            raise ValueError("Collaborator email is not registered.")

        owner_id = self.owner_for_world(world_id)
        if owner_id is None:
            raise ValueError("World not found.")
        if int(user["id"]) == owner_id:
            raise ValueError("Owner already has implicit full access.")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO world_collaborators (world_id, user_id, role)
                VALUES (?, ?, ?)
                ON CONFLICT(world_id, user_id) DO UPDATE SET role = excluded.role
                """,
                (world_id, int(user["id"]), role),
            )
            conn.commit()
        return self._collaborator_record(world_id=world_id, user_id=int(user["id"]), email=user["email"], role=role)

    def remove_collaborator(self, *, world_id: str, email: str) -> bool:
        user = self.user_by_email(email)
        if user is None:
            return False

        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM world_collaborators WHERE world_id = ? AND user_id = ?",
                (world_id, int(user["id"])),
            )
            conn.execute(
                "DELETE FROM world_feature_permissions WHERE world_id = ? AND user_id = ?",
                (world_id, int(user["id"])),
            )
            conn.commit()
            return cursor.rowcount > 0

    def set_feature_permissions(self, *, world_id: str, email: str, permissions: dict[str, bool]) -> dict[str, Any]:
        user = self.user_by_email(email)
        if user is None:
            raise ValueError("Collaborator email is not registered.")

        role = self.role_for_world(user_id=int(user["id"]), world_id=world_id)
        if role is None or role == "owner":
            raise ValueError("Permissions can only be set for collaborators.")

        values = {key: permissions.get(key) for key in FEATURE_KEYS}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO world_feature_permissions (
                    world_id,
                    user_id,
                    can_view_world,
                    can_step_world,
                    can_manage_agents,
                    can_manage_quests,
                    can_manage_stream,
                    can_manage_collaborators,
                    can_manage_invites,
                    can_manage_permissions,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(world_id, user_id) DO UPDATE SET
                    can_view_world = excluded.can_view_world,
                    can_step_world = excluded.can_step_world,
                    can_manage_agents = excluded.can_manage_agents,
                    can_manage_quests = excluded.can_manage_quests,
                    can_manage_stream = excluded.can_manage_stream,
                    can_manage_collaborators = excluded.can_manage_collaborators,
                    can_manage_invites = excluded.can_manage_invites,
                    can_manage_permissions = excluded.can_manage_permissions,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    world_id,
                    int(user["id"]),
                    self._as_db_bool(values["can_view_world"]),
                    self._as_db_bool(values["can_step_world"]),
                    self._as_db_bool(values["can_manage_agents"]),
                    self._as_db_bool(values["can_manage_quests"]),
                    self._as_db_bool(values["can_manage_stream"]),
                    self._as_db_bool(values["can_manage_collaborators"]),
                    self._as_db_bool(values["can_manage_invites"]),
                    self._as_db_bool(values["can_manage_permissions"]),
                ),
            )
            conn.commit()
        return self._collaborator_record(world_id=world_id, user_id=int(user["id"]), email=user["email"], role=role)

    def create_invite(
        self,
        *,
        world_id: str,
        role: str,
        created_by_user_id: int,
        expires_in_hours: int = 72,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        if role not in {"editor", "viewer"}:
            raise ValueError("Role must be 'editor' or 'viewer'.")
        if self.owner_for_world(world_id) is None:
            raise ValueError("World not found.")

        expires_at = datetime.now(UTC) + timedelta(hours=max(1, expires_in_hours))
        token = token_hex(16)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO world_invites (token, world_id, role, created_by_user_id, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (token, world_id, role, created_by_user_id, expires_at.isoformat()),
            )
            conn.commit()
        return self._invite_record(token=token, world_id=world_id, role=role, expires_at=expires_at.isoformat(), base_url=base_url)

    def accept_invite(self, *, token: str, user_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            invite = conn.execute(
                """
                SELECT token, world_id, role, expires_at, used_by_user_id, revoked_at
                FROM world_invites
                WHERE token = ?
                """,
                (token,),
            ).fetchone()
            if invite is None:
                raise ValueError("Invite not found.")
            if invite["revoked_at"] is not None:
                raise ValueError("Invite has been revoked.")
            if invite["used_by_user_id"] is not None:
                raise ValueError("Invite has already been used.")
            if datetime.fromisoformat(str(invite["expires_at"])) < datetime.now(UTC):
                raise ValueError("Invite has expired.")

            role = str(invite["role"])
            world_id = str(invite["world_id"])
            owner_id = self.owner_for_world(world_id)
            if owner_id == user_id:
                raise ValueError("Owner does not need an invite.")

            conn.execute(
                """
                INSERT INTO world_collaborators (world_id, user_id, role)
                VALUES (?, ?, ?)
                ON CONFLICT(world_id, user_id) DO UPDATE SET role = excluded.role
                """,
                (world_id, user_id, role),
            )
            conn.execute(
                """
                UPDATE world_invites
                SET used_by_user_id = ?, used_at = CURRENT_TIMESTAMP
                WHERE token = ?
                """,
                (user_id, token),
            )
            conn.commit()
            return {"world_id": world_id, "user_id": user_id, "role": role}

    def revoke_invite(self, *, token: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE world_invites
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE token = ? AND revoked_at IS NULL AND used_by_user_id IS NULL
                """,
                (token,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_invites(self, world_id: str, *, base_url: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT token, role, created_at, expires_at, used_at, revoked_at
                FROM world_invites
                WHERE world_id = ?
                ORDER BY created_at DESC
                """,
                (world_id,),
            ).fetchall()
            return [
                self._invite_record(
                    token=str(row["token"]),
                    world_id=world_id,
                    role=str(row["role"]),
                    created_at=str(row["created_at"]),
                    expires_at=str(row["expires_at"]),
                    used_at=row["used_at"],
                    revoked_at=row["revoked_at"],
                    base_url=base_url,
                )
                for row in rows
            ]

    def list_collaborators(self, world_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            owner = conn.execute(
                """
                SELECT users.id AS user_id, users.email, 'owner' AS role
                FROM world_ownership
                JOIN users ON users.id = world_ownership.user_id
                WHERE world_ownership.world_id = ?
                """,
                (world_id,),
            ).fetchone()
            rows = conn.execute(
                """
                SELECT users.id AS user_id, users.email, world_collaborators.role
                FROM world_collaborators
                JOIN users ON users.id = world_collaborators.user_id
                WHERE world_collaborators.world_id = ?
                ORDER BY users.email
                """,
                (world_id,),
            ).fetchall()

            output = []
            if owner is not None:
                output.append(self._collaborator_record(world_id=world_id, user_id=int(owner["user_id"]), email=str(owner["email"]), role="owner"))
            output.extend(
                self._collaborator_record(world_id=world_id, user_id=int(row["user_id"]), email=str(row["email"]), role=str(row["role"]))
                for row in rows
            )
            return output

    def list_worlds_for_user(self, user_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT world_id, created_at, 'owner' AS role
                FROM world_ownership
                WHERE user_id = ?
                UNION
                SELECT world_id, created_at, role
                FROM world_collaborators
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id, user_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def log_event(
        self,
        *,
        world_id: str,
        action: str,
        target_type: str,
        target_id: str | None = None,
        actor_user_id: int | None = None,
        repair_state: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        persisted_repair_state = repair_state or audit_repair_state_for_action(action)
        payload_details = dict(details or {})
        payload_details.setdefault("repair_state", persisted_repair_state)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO world_audit_log (world_id, actor_user_id, action, target_type, target_id, repair_state, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (world_id, actor_user_id, action, target_type, target_id, persisted_repair_state, json.dumps(payload_details)),
            )
            conn.commit()

    def list_audit_log(
        self,
        world_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        action: str | None = None,
        actor_email: str | None = None,
        repair_state: str | None = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT world_audit_log.id, world_audit_log.action, world_audit_log.target_type, world_audit_log.target_id,
                   world_audit_log.repair_state, world_audit_log.details_json, world_audit_log.created_at, users.email AS actor_email
            FROM world_audit_log
            LEFT JOIN users ON users.id = world_audit_log.actor_user_id
            WHERE world_audit_log.world_id = ?
        """
        params: list[Any] = [world_id]

        if action:
            query += " AND world_audit_log.action = ?"
            params.append(action)
        if actor_email:
            query += " AND users.email = ?"
            params.append(actor_email)
        if repair_state:
            query += " AND world_audit_log.repair_state = ?"
            params.append(repair_state)

        query += " ORDER BY world_audit_log.id DESC LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(max(0, offset))

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            output = []
            for row in rows:
                item = dict(row)
                item["details"] = json.loads(item.pop("details_json") or "{}")
                item["repair_state"] = item.get("repair_state") or audit_repair_state_for_action(str(item["action"]))
                output.append(item)
            return output

    def count_audit_log(
        self,
        world_id: str,
        *,
        action: str | None = None,
        actor_email: str | None = None,
        repair_state: str | None = None,
    ) -> int:
        query = """
            SELECT COUNT(*) AS total
            FROM world_audit_log
            LEFT JOIN users ON users.id = world_audit_log.actor_user_id
            WHERE world_audit_log.world_id = ?
        """
        params: list[Any] = [world_id]

        if action:
            query += " AND world_audit_log.action = ?"
            params.append(action)
        if actor_email:
            query += " AND users.email = ?"
            params.append(actor_email)
        if repair_state:
            query += " AND world_audit_log.repair_state = ?"
            params.append(repair_state)

        with self._connect() as conn:
            row = conn.execute(query, tuple(params)).fetchone()
            return int(row["total"]) if row else 0

    def _collaborator_record(self, *, world_id: str, user_id: int, email: str, role: str) -> dict[str, Any]:
        return {
            "world_id": world_id,
            "user_id": user_id,
            "email": email,
            "role": role,
            "permissions": self.get_effective_permissions(user_id=user_id, world_id=world_id),
        }

    def _invite_record(
        self,
        *,
        token: str,
        world_id: str,
        role: str,
        expires_at: str,
        base_url: str | None = None,
        created_at: str | None = None,
        used_at: str | None = None,
        revoked_at: str | None = None,
    ) -> dict[str, Any]:
        share_url = None
        if base_url:
            share_url = f"{base_url.rstrip('/')}/editor?invite={token}"
        return {
            "token": token,
            "world_id": world_id,
            "role": role,
            "created_at": created_at,
            "expires_at": expires_at,
            "used_at": used_at,
            "revoked_at": revoked_at,
            "share_url": share_url,
        }

    @staticmethod
    def _as_db_bool(value: bool | None) -> int | None:
        if value is None:
            return None
        return 1 if value else 0
