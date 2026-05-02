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
    from routes.google_earth_engine import gee_bp

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.config["TESTING"] = True
    app.register_blueprint(gee_bp)

    with app.test_client() as test_client:
        yield test_client


def test_gee_status_route_returns_payload(client, monkeypatch):
    monkeypatch.setattr(
        "routes.google_earth_engine.get_gee_status",
        lambda: {"configured": True, "initialized": False, "project": "p"},
    )

    response = client.get("/api/gee/status")
    assert response.status_code == 200
    assert response.get_json()["configured"] is True


def test_gee_ndvi_requires_authentication(client):
    response = client.post("/api/gee/ndvi", json={"lat": 51.5, "lon": -0.1})
    assert response.status_code == 401


def test_gee_ndvi_requires_lat_lon(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.post("/api/gee/ndvi", json={"lat": 51.5})
    assert response.status_code == 400
    assert response.get_json()["error"] == "lat_lon_required"


def test_gee_ndvi_success(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    monkeypatch.setattr(
        "routes.google_earth_engine.compute_ndvi_snapshot",
        lambda **_: {"ok": True, "ndvi_mean": 0.42, "image_count": 3},
    )

    response = client.post(
        "/api/gee/ndvi",
        json={
            "lat": 51.5,
            "lon": -0.1,
            "start_date": "2025-01-01",
            "end_date": "2025-02-01",
            "buffer_m": 300,
            "max_cloud_pct": 15,
            "scale": 10,
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["ndvi_mean"] == 0.42


def test_gee_ndvi_value_error_maps_to_400(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    def _raise(**_):
        raise ValueError("invalid_lat")

    monkeypatch.setattr("routes.google_earth_engine.compute_ndvi_snapshot", _raise)

    response = client.post("/api/gee/ndvi", json={"lat": 100, "lon": 0})
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_lat"
