from __future__ import annotations

import importlib
import os
import sys

import pytest
from flask import Flask


ROOT = os.path.join(os.path.dirname(__file__), "..")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _reload_module(name: str):
    if name in sys.modules:
        del sys.modules[name]
    return importlib.import_module(name)


@pytest.fixture
def codon_module(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "codon_distil_routes.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite://{db_path}")

    _reload_module("void_engine.db_pool")
    _reload_module("void_engine.codon_distil")
    return _reload_module("routes.codon_distil")


@pytest.fixture
def client_codon(codon_module):
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.config["TESTING"] = True
    app.register_blueprint(codon_module.codon_distil_bp)

    with app.test_client() as client:
        yield client


def test_codon_process_requires_auth(client_codon):
    response = client_codon.post("/api/codon-distil/process", json={"text": "hello"})

    assert response.status_code == 401
    assert response.get_json()["error"] == "auth required"


def test_codon_process_requires_admin_or_founder(client_codon):
    with client_codon.session_transaction() as session:
        session["user_id"] = 101
        session["role"] = "user"

    response = client_codon.post("/api/codon-distil/process", json={"text": "hello"})

    assert response.status_code == 403
    assert response.get_json()["error"] == "admin/founder required"


def test_codon_process_starts_job_for_admin(client_codon, codon_module, monkeypatch: pytest.MonkeyPatch):
    started = {"value": False}

    class _DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            self.target = target
            self.args = args
            self.daemon = daemon

        def start(self):
            started["value"] = True

    monkeypatch.setattr(codon_module.threading, "Thread", _DummyThread)
    monkeypatch.setattr(codon_module, "chunk_text", lambda text, max_words=800: ["chunk-a", "chunk-b"])

    with client_codon.session_transaction() as session:
        session["user_id"] = 202
        session["role"] = "admin"

    response = client_codon.post("/api/codon-distil/process", json={"text": "hello world"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "running"
    assert payload["total_chunks"] == 2
    assert isinstance(payload["job_id"], str)
    assert started["value"] is True


def test_codon_results_requires_auth(client_codon):
    response = client_codon.get("/api/codon-distil/results/example-job")

    assert response.status_code == 401
    assert response.get_json()["error"] == "auth required"


def test_codon_seal_requires_founder(client_codon):
    with client_codon.session_transaction() as session:
        session["user_id"] = 303
        session["role"] = "admin"
        session["is_founder"] = False

    response = client_codon.post("/api/codon-distil/seal", json={"codon_id": 1})

    assert response.status_code == 403
    assert response.get_json()["error"] == "founder auth required"
