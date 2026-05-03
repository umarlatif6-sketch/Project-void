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
    payload = response.get_json()
    assert payload["configured"] is True
    assert payload["chain"] == 286
    assert payload["base_frequency_hz"] == 432.0
    assert payload["bridge_mode"] == "sovereign_opaque_transport"
    assert payload["sovereign_packet_id"]
    assert payload["al_jabr_286_hash"]


def test_gee_district_presets_defaults_to_pakistan(client):
    response = client.get("/api/gee/district-presets")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["country"] == "Pakistan"
    assert "lahore" in payload["presets"]


def test_gee_dataset_catalog_route(client):
    response = client.get("/api/gee/datasets")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert "ndvi_sentinel2" in payload["catalog"]
    assert payload["chain"] == 286


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
    assert payload["chain"] == 286


def test_gee_ndvi_value_error_maps_to_400(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    def _raise(**_):
        raise ValueError("invalid_lat")

    monkeypatch.setattr("routes.google_earth_engine.compute_ndvi_snapshot", _raise)

    response = client.post("/api/gee/ndvi", json={"lat": 100, "lon": 0})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "invalid_lat"
    assert payload["chain"] == 286


def test_gee_water_table_trend_requires_authentication(client):
    response = client.post("/api/gee/water-table-trend", json={})
    assert response.status_code == 401


def test_gee_water_table_trend_defaults_to_pakistan(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    def _fake_trend(**kwargs):
        assert kwargs["country"] == "Pakistan"
        return {
            "ok": True,
            "area": "country:Pakistan",
            "trend_direction": "declining",
            "trend_slope_cm_per_year": -0.3,
            "sample_count": 24,
        }

    monkeypatch.setattr("routes.google_earth_engine.compute_water_table_trend", _fake_trend)

    response = client.post("/api/gee/water-table-trend", json={})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["area"] == "country:Pakistan"
    assert payload["chain"] == 286


def test_gee_water_table_trend_invalid_lat_lon(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.post(
        "/api/gee/water-table-trend",
        json={"lat": "north", "lon": 72.0},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_lat_lon"


def test_gee_anomaly_thresholds_requires_authentication(client):
    response = client.post("/api/gee/anomaly-thresholds", json={"water_trend_slope_cm_per_year": -0.8})
    assert response.status_code == 401


def test_gee_anomaly_thresholds_warning_442hz(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.post(
        "/api/gee/anomaly-thresholds",
        json={"water_trend_slope_cm_per_year": -0.8, "ndvi_mean": 0.2},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["severity"] in {"warning", "critical"}
    assert payload["resonance_alert_hz"] == 442
    assert payload["chain"] == 286


def test_gee_rfq_state_requires_authentication(client):
    response = client.post("/api/gee/rfq-state", json={"district_key": "soan_valley"})
    assert response.status_code == 401


def test_gee_rfq_state_success(client, monkeypatch, tmp_path):
    with client.session_transaction() as session:
        session["user_id"] = 1

    monkeypatch.setattr("routes.auth._get_effective_tier", lambda _uid: "journalist")
    monkeypatch.setattr("routes.google_earth_engine._RFQ_AUDIT_LOG_PATH", tmp_path / "rfq_state_log.jsonl")

    monkeypatch.setattr(
        "routes.google_earth_engine.calculate_grace_correlation_proxy",
        lambda **_: 0.9,
    )
    monkeypatch.setattr(
        "routes.google_earth_engine.trigger_rfq_on_melt",
        lambda **_: {
            "ok": True,
            "district_key": "soan_valley",
            "rfq_triggered": True,
            "rfq_profile": "heavy_weave",
            "recommended_silk_to_zinc_ratio": "66:34",
        },
    )

    response = client.post(
        "/api/gee/rfq-state",
        json={"district_key": "soan_valley", "water_trend_slope_cm_per_year": -1.2},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["district_key"] == "soan_valley"
    assert payload["rfq_triggered"] is True
    assert payload["chain"] == 286


def test_gee_rfq_state_forbidden_for_ghost_tier(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    monkeypatch.setattr("routes.auth._get_effective_tier", lambda _uid: "ghost")

    response = client.post(
        "/api/gee/rfq-state",
        json={"district_key": "soan_valley", "water_trend_slope_cm_per_year": -1.2},
    )
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["required_tier"] == "journalist"


def test_gee_rfq_audit_requires_admin(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.get("/api/gee/rfq-audit")
    assert response.status_code == 403


def test_gee_rfq_audit_success(client, monkeypatch, tmp_path):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "admin"

    log_path = tmp_path / "rfq_audit_log.jsonl"
    monkeypatch.setattr("routes.google_earth_engine._RFQ_AUDIT_LOG_PATH", log_path)

    log_path.write_text(
        "{\"timestamp\":\"2026-05-03T00:00:00Z\",\"district_key\":\"soan_valley\",\"rfq_triggered\":true}\n",
        encoding="utf-8",
    )

    response = client.get("/api/gee/rfq-audit?limit=10")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["event_count"] == 1
    assert payload["events"][0]["district_key"] == "soan_valley"


def test_ion_resurrection_sim_requires_authentication(client):
    response = client.post("/api/energy/ion-resurrection/simulate", json={})
    assert response.status_code == 401


def test_ion_resurrection_sim_forbidden_for_ghost_tier(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    monkeypatch.setattr("routes.auth._get_effective_tier", lambda _uid: "ghost")

    response = client.post("/api/energy/ion-resurrection/simulate", json={})
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["required_tier"] == "journalist"


def test_ion_resurrection_sim_success(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1

    monkeypatch.setattr("routes.auth._get_effective_tier", lambda _uid: "journalist")

    class _FakeModule:
        class BatterySample:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class EnvironmentProfile:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class IonResurrector:
            def __init__(self, target_frequency_hz=432.0):
                self.target_frequency_hz = target_frequency_hz

            def execute_protocol(self, **_kwargs):
                return {
                    "ok": True,
                    "state": "RE-ANIMATED",
                    "drift_score": 0.91,
                    "target_frequency_hz": 436.2,
                    "pwm_plan": {"profile": "resurrection_heavy"},
                }

    monkeypatch.setattr("routes.google_earth_engine._get_ion_resurrection_module", lambda: _FakeModule)

    response = client.post(
        "/api/energy/ion-resurrection/simulate",
        json={
            "district_key": "soan_valley",
            "water_trend_slope_cm_per_year": -1.1,
            "sample": {
                "chemistry": "li_ion",
                "open_circuit_voltage_v": 2.9,
                "nominal_voltage_v": 3.7,
                "internal_resistance_mohm": 210,
                "state_of_health_pct": 58,
            },
            "environment": {
                "temperature_c": 33,
                "relative_humidity_pct": 67,
                "region": "Pakistan",
            },
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["state"] == "RE-ANIMATED"
    assert payload["chain"] == 286


def test_gee_orchestrate_exploration_requires_admin(client):
    response = client.post("/api/gee/orchestrate-exploration", json={})
    assert response.status_code == 401


def test_gee_orchestrate_exploration_success_without_agents(client, monkeypatch):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "admin"

    monkeypatch.setattr(
        "routes.google_earth_engine.run_gee_exploration_orchestration",
        lambda **_: {
            "ok": True,
            "district_count": 3,
            "warning_or_critical_count": 1,
            "district_results": [],
            "catalog": {},
        },
    )

    response = client.post(
        "/api/gee/orchestrate-exploration",
        json={"run_agents": False, "run_adriana_synthesis": False},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["gee"]["district_count"] == 3
    assert payload["chain"] == 286
