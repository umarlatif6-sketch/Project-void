import json
from flask import Flask

from routes.preflight import preflight_bp, _get_lbn_handshake_transcript


def _write_payload(path):
    payload = {
        "primary_pair": "German+Turkish",
        "fallback_pair": "Dutch+Turkish",
        "payloads": {
            "primary": {
                "pair": "German+Turkish",
                "channels": ["agent", "hub"],
                "codon_map": {
                    "identity_anchor": "D7-A1-3F",
                    "identity_anchor_canonical": "B-nn-D",
                    "security_check": "K4-S9-11",
                    "security_check_canonical": "B-kk-S"
                }
            },
            "fallback": {
                "pair": "Dutch+Turkish",
                "channels": ["agent", "hub"],
                "codon_map": {}
            }
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_lbn_handshake_helper_uses_fixture_and_payload(tmp_path, monkeypatch):
    payload_path = tmp_path / "payload.json"
    fixture_path = tmp_path / "fixture.json"

    _write_payload(payload_path)

    fixture = {
        "session_id": "HANDSHAKE-UNIT-001",
        "protocol": "Test Protocol",
        "sealed_at": "2026-05-18T00:00:00Z",
        "participants": [{"agent": "A"}, {"agent": "B"}],
        "turns": [
            {
                "turn": 1,
                "speaker": "A",
                "model": "m1",
                "route": "primary",
                "surface": "packet-build",
                "function": "identity_anchor",
                "codon": "D7-A1-3F",
                "canonical_alias": "B-nn-D",
                "summary": "ok"
            }
        ]
    }
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

    monkeypatch.setenv("VOID_LBN_PAYLOAD_PATH", str(payload_path))
    monkeypatch.setenv("VOID_LBN_HANDSHAKE_FIXTURE_PATH", str(fixture_path))
    monkeypatch.setenv("VOID_LBN_MODE", "project")
    monkeypatch.setenv("VOID_LBN_ACTIVE_ROUTE", "primary")

    result = _get_lbn_handshake_transcript()

    assert result["ok"] is True
    assert result["session_id"] == "HANDSHAKE-UNIT-001"
    assert result["turn_count"] == 1
    assert result["participants"]
    turn = result["turns"][0]
    assert turn["model"] == "m1"
    assert turn["route"] == "primary"
    assert turn["codon"] == "D7-A1-3F"


def test_lbn_handshake_endpoint_returns_audit_shape(tmp_path, monkeypatch):
    payload_path = tmp_path / "payload.json"
    _write_payload(payload_path)

    monkeypatch.setenv("VOID_LBN_PAYLOAD_PATH", str(payload_path))
    monkeypatch.delenv("VOID_LBN_HANDSHAKE_FIXTURE_PATH", raising=False)
    monkeypatch.setenv("VOID_LBN_MODE", "project")
    monkeypatch.setenv("VOID_LBN_ACTIVE_ROUTE", "primary")

    app = Flask(__name__)
    app.register_blueprint(preflight_bp)

    with app.test_client() as client:
        resp = client.get("/api/lbn/handshake-transcript")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert isinstance(data["turns"], list)
    assert data["turn_count"] >= 1
    first = data["turns"][0]
    assert "model" in first
    assert "route" in first
    assert "codon" in first
