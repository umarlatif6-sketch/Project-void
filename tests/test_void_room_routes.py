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
def client_void_room(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "void_room_routes.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite://{db_path}")

    _reload_module("void_engine.db_pool")
    void_room = _reload_module("routes.void_room")

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.config["TESTING"] = True
    app.register_blueprint(void_room.void_room_bp)

    with app.test_client() as client:
        yield client


def test_void_room_messages_endpoint_returns_list(client_void_room):
    response = client_void_room.get("/api/void-room/messages")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, list)


def test_void_room_post_requires_valid_council_key(client_void_room):
    response = client_void_room.post(
        "/api/void-room/post",
        json={"voice": "adriana", "content": "hello"},
        headers={"X-Council-Key": "wrong"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Invalid council key"


def test_void_room_post_and_fetch_with_valid_key(client_void_room):
    post_response = client_void_room.post(
        "/api/void-room/post",
        json={"voice": "adriana", "content": "signal accepted"},
        headers={"X-Council-Key": "void-council-432hz"},
    )

    assert post_response.status_code == 201
    msg_id = post_response.get_json()["id"]

    list_response = client_void_room.get(f"/api/void-room/messages?after={msg_id - 1}")
    assert list_response.status_code == 200
    messages = list_response.get_json()
    assert any(m["id"] == msg_id and m["content"] == "signal accepted" for m in messages)
