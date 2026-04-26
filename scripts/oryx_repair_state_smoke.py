#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ORYX_BACKEND = REPO_ROOT / ".oryx" / "backend"
REPORT_PATH = REPO_ROOT / "data" / "oryx_repair_state_smoke.json"

if str(ORYX_BACKEND) not in sys.path:
    sys.path.insert(0, str(ORYX_BACKEND))

from oryx_engine import OryxEngine
from oryx_engine.auth_store import AuthStore


def _load_oryx_app_module():
    module_name = f"oryx_backend_app_{uuid.uuid4().hex}"
    app_path = ORYX_BACKEND / "app.py"
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client, *, email: str, password: str = "strongpass123") -> str:
    register_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    if register_response.status_code != 200:
        raise RuntimeError(
            f"register failed for {email}: {register_response.status_code} {register_response.get_data(as_text=True)}"
        )

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    if login_response.status_code != 200:
        raise RuntimeError(
            f"login failed for {email}: {login_response.status_code} {login_response.get_data(as_text=True)}"
        )
    return login_response.get_json()["token"]


def _create_world(client, *, token: str, name: str) -> str:
    world_response = client.post(
        "/api/worlds",
        headers=_auth_headers(token),
        json={"name": name, "template": "sunsteel_frontier"},
    )
    if world_response.status_code != 201:
        raise RuntimeError(
            f"world create failed: {world_response.status_code} {world_response.get_data(as_text=True)}"
        )
    return world_response.get_json()["world"]["id"]


def _run_recoverable_scenario(client, *, run_tag: str) -> dict:
    owner_token = _register_and_login(client, email=f"owner_{run_tag}@example.com")
    world_id = _create_world(client, token=owner_token, name="Repair Smoke World")

    invite_response = client.post(
        f"/api/worlds/{world_id}/invites",
        headers=_auth_headers(owner_token),
        json={"role": "viewer", "expires_in_hours": 24},
    )
    if invite_response.status_code != 201:
        raise RuntimeError(f"invite create failed: {invite_response.status_code} {invite_response.get_data(as_text=True)}")
    invite_token = invite_response.get_json()["token"]

    revoke_response = client.post(
        f"/api/worlds/{world_id}/invites/revoke",
        headers=_auth_headers(owner_token),
        json={"token": invite_token},
    )
    if revoke_response.status_code != 200:
        raise RuntimeError(f"invite revoke failed: {revoke_response.status_code} {revoke_response.get_data(as_text=True)}")

    summary_response = client.get(
        f"/api/worlds/{world_id}/summary",
        headers=_auth_headers(owner_token),
    )
    if summary_response.status_code != 200:
        raise RuntimeError(f"summary failed: {summary_response.status_code} {summary_response.get_data(as_text=True)}")
    summary_payload = summary_response.get_json()

    audit_response = client.get(
        f"/api/worlds/{world_id}/audit?repair_state=recoverable",
        headers=_auth_headers(owner_token),
    )
    if audit_response.status_code != 200:
        raise RuntimeError(f"audit failed: {audit_response.status_code} {audit_response.get_data(as_text=True)}")
    audit_payload = audit_response.get_json()

    return {
        "scenario": "recoverable",
        "ok": True,
        "world_id": world_id,
        "summary_repair_state": summary_payload["repair_state"],
        "issue_codes": [item["code"] for item in summary_payload["issues"]],
        "audit_total": audit_payload["total"],
        "audit_actions": [item["action"] for item in audit_payload["items"]],
        "audit_states": [item["repair_state"] for item in audit_payload["items"]],
    }


def _run_quarantined_scenario(client, *, db_path: Path, run_tag: str) -> dict:
    owner_token = _register_and_login(client, email=f"owner_q_{run_tag}@example.com")
    editor_token = _register_and_login(client, email=f"editor_q_{run_tag}@example.com")
    world_id = _create_world(client, token=owner_token, name="Quarantine Smoke World")

    invite_response = client.post(
        f"/api/worlds/{world_id}/invites",
        headers=_auth_headers(owner_token),
        json={"role": "editor", "expires_in_hours": 24},
    )
    if invite_response.status_code != 201:
        raise RuntimeError(f"invite create failed: {invite_response.status_code} {invite_response.get_data(as_text=True)}")
    invite_token = invite_response.get_json()["token"]

    accept_response = client.post(
        "/api/invites/accept",
        headers=_auth_headers(editor_token),
        json={"token": invite_token},
    )
    if accept_response.status_code != 200:
        raise RuntimeError(f"invite accept failed: {accept_response.status_code} {accept_response.get_data(as_text=True)}")

    # Simulate owner identity fracture while preserving editor access.
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM world_ownership WHERE world_id = ?", (world_id,))
        conn.commit()

    summary_response = client.get(
        f"/api/worlds/{world_id}/summary",
        headers=_auth_headers(editor_token),
    )
    if summary_response.status_code != 200:
        raise RuntimeError(
            f"quarantined summary failed: {summary_response.status_code} {summary_response.get_data(as_text=True)}"
        )
    summary_payload = summary_response.get_json()

    return {
        "scenario": "quarantined",
        "ok": True,
        "world_id": world_id,
        "summary_repair_state": summary_payload["repair_state"],
        "issue_codes": [item["code"] for item in summary_payload["issues"]],
    }


def _validate_recoverable(result: dict) -> None:
    if result["summary_repair_state"] != "recoverable":
        raise RuntimeError(f"expected recoverable summary state, got {result['summary_repair_state']}")
    if "recent_repair_events" not in result["issue_codes"]:
        raise RuntimeError("recent_repair_events issue missing from summary")
    if result["audit_total"] < 1:
        raise RuntimeError("recoverable audit filter returned no items")
    if "invite_revoked" not in result["audit_actions"]:
        raise RuntimeError("invite_revoked not present in recoverable audit actions")
    if not all(state == "recoverable" for state in result["audit_states"]):
        raise RuntimeError("non-recoverable state returned by recoverable audit filter")


def _validate_quarantined(result: dict) -> None:
    if result["summary_repair_state"] != "quarantined":
        raise RuntimeError(f"expected quarantined summary state, got {result['summary_repair_state']}")
    if "owner_missing" not in result["issue_codes"]:
        raise RuntimeError("owner_missing issue missing from quarantined summary")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ORYX repair-state smoke test")
    parser.add_argument(
        "--mode",
        choices=["recoverable", "quarantined", "both"],
        default="both",
        help="Which repair-state scenario to run.",
    )
    parser.add_argument(
        "--persist-db",
        action="store_true",
        help="Persist smoke-test SQLite DB to data/oryx_repair_state_smoke.db instead of temp storage.",
    )
    parser.add_argument(
        "--db-path",
        default="",
        help="Optional explicit SQLite path when --persist-db is enabled.",
    )
    return parser.parse_args()


def _resolve_db_path(args: argparse.Namespace, temp_dir: Path) -> Path:
    if not args.persist_db:
        return temp_dir / "oryx.db"
    if args.db_path:
        db_path = Path(args.db_path).expanduser().resolve()
    else:
        db_path = REPO_ROOT / "data" / "oryx_repair_state_smoke.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def _collect_persistence_summary(db_path: Path) -> dict:
    if not db_path.exists():
        return {
            "db_path": str(db_path),
            "exists": False,
            "audit_log_rows": 0,
            "repair_state_counts": {},
        }

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        total_row = conn.execute("SELECT COUNT(*) AS total FROM world_audit_log").fetchone()
        state_rows = conn.execute(
            "SELECT repair_state, COUNT(*) AS count FROM world_audit_log GROUP BY repair_state"
        ).fetchall()

    return {
        "db_path": str(db_path),
        "exists": True,
        "audit_log_rows": int(total_row["total"] if total_row else 0),
        "repair_state_counts": {
            str(row["repair_state"]): int(row["count"]) for row in state_rows if row["repair_state"]
        },
    }


def main() -> int:
    args = _parse_args()
    module = _load_oryx_app_module()

    with tempfile.TemporaryDirectory(prefix="oryx-repair-smoke-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        data_dir = temp_dir / "oryx_data"
        db_path = _resolve_db_path(args, temp_dir)

        module.OryxEngine = lambda _path: OryxEngine(data_dir)
        module.AuthStore = lambda _path: AuthStore(db_path)

        app = module.create_app()
        app.config["TESTING"] = True

        with app.test_client() as client:
            scenario_results = []
            run_tag = uuid.uuid4().hex[:10]

            if args.mode in {"recoverable", "both"}:
                recoverable = _run_recoverable_scenario(client, run_tag=run_tag)
                _validate_recoverable(recoverable)
                scenario_results.append(recoverable)

            if args.mode in {"quarantined", "both"}:
                quarantined = _run_quarantined_scenario(client, db_path=db_path, run_tag=run_tag)
                _validate_quarantined(quarantined)
                scenario_results.append(quarantined)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": True,
        "mode": args.mode,
        "scenarios": scenario_results,
        "persistence": _collect_persistence_summary(db_path),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())