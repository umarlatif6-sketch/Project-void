from __future__ import annotations

import json

import pytest

from void_engine.packet_security import (
    PacketSecurityConfig,
    read_packet_security_config,
    validate_packet_security_config,
)


def test_validate_packet_security_config_enforced_requires_keys() -> None:
    cfg = PacketSecurityConfig(
        enforce=True,
        signing_key_id="k1",
        signing_private_key="",
        verify_keys={},
        require_sector_policy=True,
        max_age_seconds=86400,
    )
    errors = validate_packet_security_config(cfg)
    assert errors
    assert any("VOID_PACKET_SIGNING_PRIVATE_KEY" in e for e in errors)
    assert any("VOID_PACKET_VERIFY_KEYS_JSON" in e for e in errors)


def test_validate_packet_security_config_key_id_must_exist() -> None:
    cfg = PacketSecurityConfig(
        enforce=True,
        signing_key_id="k2",
        signing_private_key="abc",
        verify_keys={"k1": "pub"},
        require_sector_policy=True,
        max_age_seconds=86400,
    )
    errors = validate_packet_security_config(cfg)
    assert any("VOID_PACKET_SIGNING_KEY_ID must exist" in e for e in errors)


def test_read_packet_security_config_parses_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOID_PACKET_SECURITY_ENFORCE", "true")
    monkeypatch.setenv("VOID_PACKET_SIGNING_KEY_ID", "k1")
    monkeypatch.setenv("VOID_PACKET_SIGNING_PRIVATE_KEY", "deadbeef")
    monkeypatch.setenv("VOID_PACKET_VERIFY_KEYS_JSON", json.dumps({"k1": "cafebabe"}))
    monkeypatch.setenv("VOID_PACKET_REQUIRE_SECTOR_POLICY", "true")
    monkeypatch.setenv("VOID_PACKET_MAX_AGE_SECONDS", "3600")

    cfg = read_packet_security_config()

    assert cfg.enforce is True
    assert cfg.signing_key_id == "k1"
    assert cfg.signing_private_key == "deadbeef"
    assert cfg.verify_keys == {"k1": "cafebabe"}
    assert cfg.require_sector_policy is True
    assert cfg.max_age_seconds == 3600


def test_read_packet_security_config_rejects_bad_max_age(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOID_PACKET_MAX_AGE_SECONDS", "zero")
    with pytest.raises(ValueError):
        read_packet_security_config()
