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
    from routes.openclaw_agent import openclaw_agent_bp

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(openclaw_agent_bp)
    with app.test_client() as test_client:
        yield test_client


def test_runtime_status_endpoint_returns_bridge_payload(client, monkeypatch):
    def _fake_status():
        return {"available": True, "source": "test"}

    monkeypatch.setattr("void_engine.openclaw_bridge.get_openclaw_runtime_status", _fake_status)

    response = client.get("/api/openclaw/agent/runtime")
    assert response.status_code == 200
    assert response.get_json() == {"available": True, "source": "test"}


def test_sovereign_browse_requires_query(client):
    response = client.post("/api/openclaw/agent/sovereign-browse", json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "missing_query"


def test_sovereign_browse_success_passthrough(client, monkeypatch):
    expected = {
        "ok": True,
        "chain": 286,
        "query": "mesh",
        "sovereign_lines": ["line1"],
        "noor_length": 5,
    }

    def _fake_browse(query: str, max_results: int, timeout_s: int):
        assert query == "mesh"
        assert max_results == 4
        assert timeout_s == 20
        return expected

    monkeypatch.setattr("void_engine.openclaw_bridge.sovereign_browse", _fake_browse)

    response = client.post(
        "/api/openclaw/agent/sovereign-browse",
        json={"query": "mesh", "max_results": 4, "timeout_s": 20},
    )
    assert response.status_code == 200
    assert response.get_json() == expected


def test_guide_validates_timeout(client):
    response = client.post(
        "/api/openclaw/agent/guide",
        json={"objective": "run", "timeout_s": 3},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_timeout"


def test_guide_success_passthrough(client, monkeypatch):
    expected = {"ok": True, "sovereign_packet": {"chain": 286}}

    def _fake_guide(operator_objective: str, channel: str, timeout_s: int):
        assert operator_objective == "find route"
        assert channel == "primary"
        assert timeout_s == 40
        return expected

    monkeypatch.setattr("void_engine.openclaw_bridge.run_adriana_guided_openclaw", _fake_guide)

    response = client.post(
        "/api/openclaw/agent/guide",
        json={"objective": "find route", "channel": "primary", "timeout_s": 40},
    )
    assert response.status_code == 200
    assert response.get_json() == expected
