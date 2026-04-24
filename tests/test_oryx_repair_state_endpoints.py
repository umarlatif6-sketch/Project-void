import importlib.util
import sys
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ORYX_BACKEND = ROOT / ".oryx" / "backend"
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


@pytest.fixture
def oryx_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _load_oryx_app_module()
    data_dir = tmp_path / "oryx_data"
    db_path = tmp_path / "oryx.db"

    monkeypatch.setattr(module, "OryxEngine", lambda _path: OryxEngine(data_dir))
    monkeypatch.setattr(module, "AuthStore", lambda _path: AuthStore(db_path))

    app = module.create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _provision_world_with_repair_event(client):
    register_response = client.post(
        "/api/auth/register",
        json={"email": "owner@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"email": "owner@example.com", "password": "strongpass123"},
    )
    assert login_response.status_code == 200
    token = login_response.get_json()["token"]

    world_response = client.post(
        "/api/worlds",
        headers=_auth_headers(token),
        json={"name": "Repair Proof World", "template": "sunsteel_frontier"},
    )
    assert world_response.status_code == 201
    world_id = world_response.get_json()["world"]["id"]

    invite_response = client.post(
        f"/api/worlds/{world_id}/invites",
        headers=_auth_headers(token),
        json={"role": "viewer", "expires_in_hours": 24},
    )
    assert invite_response.status_code == 201
    invite_token = invite_response.get_json()["token"]

    revoke_response = client.post(
        f"/api/worlds/{world_id}/invites/revoke",
        headers=_auth_headers(token),
        json={"token": invite_token},
    )
    assert revoke_response.status_code == 200

    return token, world_id


def _provision_world_with_editor(client):
    client.post(
        "/api/auth/register",
        json={"email": "owner-collab@example.com", "password": "strongpass123"},
    )
    owner_login = client.post(
        "/api/auth/login",
        json={"email": "owner-collab@example.com", "password": "strongpass123"},
    )
    owner_token = owner_login.get_json()["token"]

    client.post(
        "/api/auth/register",
        json={"email": "editor-collab@example.com", "password": "strongpass123"},
    )
    editor_login = client.post(
        "/api/auth/login",
        json={"email": "editor-collab@example.com", "password": "strongpass123"},
    )
    editor_token = editor_login.get_json()["token"]

    world_response = client.post(
        "/api/worlds",
        headers=_auth_headers(owner_token),
        json={"name": "Collab Delegation World", "template": "sunsteel_frontier"},
    )
    world_id = world_response.get_json()["world"]["id"]

    invite_response = client.post(
        f"/api/worlds/{world_id}/invites",
        headers=_auth_headers(owner_token),
        json={"role": "editor", "expires_in_hours": 24},
    )
    invite_token = invite_response.get_json()["token"]
    accept_response = client.post(
        "/api/invites/accept",
        headers=_auth_headers(editor_token),
        json={"token": invite_token},
    )
    assert accept_response.status_code == 200

    return owner_token, editor_token, world_id


def test_world_summary_surfaces_recoverable_repair_state(oryx_client):
    token, world_id = _provision_world_with_repair_event(oryx_client)

    response = oryx_client.get(
        f"/api/worlds/{world_id}/summary",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["repair_state"] == "recoverable"
    assert any(issue["code"] == "recent_repair_events" for issue in payload["issues"])
    assert any(item["repair_state"] == "recoverable" for item in payload["recent_audit"])


def test_world_audit_filters_on_recoverable_repair_state(oryx_client):
    token, world_id = _provision_world_with_repair_event(oryx_client)

    response = oryx_client.get(
        f"/api/worlds/{world_id}/audit?repair_state=recoverable",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] >= 1
    assert payload["items"]
    assert all(item["repair_state"] == "recoverable" for item in payload["items"])
    assert any(item["action"] == "invite_revoked" for item in payload["items"])


def test_world_summary_requires_authorization(oryx_client):
    _, world_id = _provision_world_with_repair_event(oryx_client)

    response = oryx_client.get(f"/api/worlds/{world_id}/summary")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


def test_world_audit_requires_authorization(oryx_client):
    _, world_id = _provision_world_with_repair_event(oryx_client)

    response = oryx_client.get(f"/api/worlds/{world_id}/audit?repair_state=recoverable")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


def test_world_summary_forbids_unassigned_user(oryx_client):
    owner_token, world_id = _provision_world_with_repair_event(oryx_client)
    assert owner_token

    register_response = oryx_client.post(
        "/api/auth/register",
        json={"email": "outsider@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 200

    login_response = oryx_client.post(
        "/api/auth/login",
        json={"email": "outsider@example.com", "password": "strongpass123"},
    )
    outsider_token = login_response.get_json()["token"]

    response = oryx_client.get(
        f"/api/worlds/{world_id}/summary",
        headers=_auth_headers(outsider_token),
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Forbidden"


def test_world_audit_forbids_unassigned_user(oryx_client):
    _, world_id = _provision_world_with_repair_event(oryx_client)

    register_response = oryx_client.post(
        "/api/auth/register",
        json={"email": "outsider@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 200

    login_response = oryx_client.post(
        "/api/auth/login",
        json={"email": "outsider@example.com", "password": "strongpass123"},
    )
    outsider_token = login_response.get_json()["token"]

    response = oryx_client.get(
        f"/api/worlds/{world_id}/audit?repair_state=recoverable",
        headers=_auth_headers(outsider_token),
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Forbidden"


def test_editor_cannot_manage_invites_without_override(oryx_client):
    _, editor_token, world_id = _provision_world_with_editor(oryx_client)

    response = oryx_client.post(
        f"/api/worlds/{world_id}/invites",
        headers=_auth_headers(editor_token),
        json={"role": "viewer", "expires_in_hours": 24},
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Forbidden"


def test_owner_can_delegate_collaboration_admin_permissions(oryx_client):
    owner_token, editor_token, world_id = _provision_world_with_editor(oryx_client)

    permissions_response = oryx_client.post(
        f"/api/worlds/{world_id}/permissions",
        headers=_auth_headers(owner_token),
        json={
            "email": "editor-collab@example.com",
            "can_manage_collaborators": True,
            "can_manage_invites": True,
            "can_manage_permissions": False,
        },
    )
    assert permissions_response.status_code == 200

    create_invite_response = oryx_client.post(
        f"/api/worlds/{world_id}/invites",
        headers=_auth_headers(editor_token),
        json={"role": "viewer", "expires_in_hours": 24},
    )
    assert create_invite_response.status_code == 201

    invite_token = create_invite_response.get_json()["token"]
    revoke_response = oryx_client.post(
        f"/api/worlds/{world_id}/invites/revoke",
        headers=_auth_headers(editor_token),
        json={"token": invite_token},
    )
    assert revoke_response.status_code == 200

    oryx_client.post(
        "/api/auth/register",
        json={"email": "viewer-collab@example.com", "password": "strongpass123"},
    )

    add_collaborator_response = oryx_client.post(
        f"/api/worlds/{world_id}/collaborators",
        headers=_auth_headers(editor_token),
        json={"email": "viewer-collab@example.com", "role": "viewer"},
    )
    assert add_collaborator_response.status_code == 201

    remove_collaborator_response = oryx_client.post(
        f"/api/worlds/{world_id}/collaborators/remove",
        headers=_auth_headers(editor_token),
        json={"email": "viewer-collab@example.com"},
    )
    assert remove_collaborator_response.status_code == 200


def test_editor_cannot_manage_permissions_without_override(oryx_client):
    _, editor_token, world_id = _provision_world_with_editor(oryx_client)

    response = oryx_client.post(
        f"/api/worlds/{world_id}/permissions",
        headers=_auth_headers(editor_token),
        json={
            "email": "editor-collab@example.com",
            "can_manage_collaborators": True,
        },
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Forbidden"