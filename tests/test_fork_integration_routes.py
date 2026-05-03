from __future__ import annotations

import os
import sys

import pytest
from flask import Flask


ROOT = os.path.join(os.path.dirname(__file__), "..")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def client():
    from routes.fork_integration import fork_integration_bp

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.config["TESTING"] = True
    app.register_blueprint(fork_integration_bp)

    with app.test_client() as test_client:
        yield test_client


def test_ai_agents_index_requires_authentication(client):
    response = client.get("/api/integrations/ai-agents/index")
    assert response.status_code == 401


def test_ai_agents_delta_pack_requires_authentication(client):
    response = client.get("/api/integrations/ai-agents/delta-pack")
    assert response.status_code == 401


def test_ai_agents_index_success(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    monkeypatch.setattr("routes.auth._get_effective_tier", lambda _uid: "journalist")
    monkeypatch.setattr(
        "routes.fork_integration.load_fork_index",
        lambda: {
            "ok": True,
            "source_dir": "external/AI-Agents-Projects-Tutorials",
            "file_count": 2,
            "entries": [{"path": "agents/a2a.py", "tags": ["tool"]}],
        },
    )

    response = client.get("/api/integrations/ai-agents/index")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["file_count"] == 2


def test_ai_agents_delta_pack_success(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    monkeypatch.setattr("routes.auth._get_effective_tier", lambda _uid: "journalist")
    monkeypatch.setattr(
        "routes.fork_integration.load_delta_pack",
        lambda: {
            "ok": True,
            "entry_count": 1,
            "focus_areas": {"orchestration": 1},
            "entries": [{"path": "agents/a2a.py", "focus_area": "orchestration"}],
        },
    )

    response = client.get("/api/integrations/ai-agents/delta-pack")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["entry_count"] == 1
    assert payload["focus_areas"]["orchestration"] == 1


def test_ai_agents_sync_requires_admin(client):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "user"

    response = client.post("/api/integrations/ai-agents/sync", json={})
    assert response.status_code == 403


def test_ai_agents_sync_success(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "admin"

    monkeypatch.setattr(
        "routes.fork_integration.sync_index_and_build_delta",
        lambda **_: {
            "ok": True,
            "sync": {"action": "updated"},
            "index": {"file_count": 120, "tool_count": 70, "equipment_count": 5},
            "delta": {"entry_count": 48, "focus_areas": {"tooling": 20, "memory": 10}},
        },
    )

    response = client.post(
        "/api/integrations/ai-agents/sync",
        json={"repo_url": "https://github.com/example/repo", "max_files": 1200, "max_delta_entries": 48},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["delta"]["entry_count"] == 48


def test_register_blueprints_includes_fork_integration():
    from routes import register_blueprints

    class _FakeApp:
        def __init__(self):
            self.names = []

        def register_blueprint(self, blueprint):
            self.names.append(blueprint.name)

    app = _FakeApp()
    register_blueprints(app)
    assert "fork_integration" in app.names