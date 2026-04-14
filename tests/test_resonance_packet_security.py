from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from void_engine.resonance_packet import (
    build_packet_manifest,
    check_manifest_freshness,
    is_sector_authorized,
    sign_packet_manifest,
    verify_packet_manifest,
)


def _utc(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_manifest_signature_roundtrip_ed25519() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_hex = private_key.private_bytes_raw().hex()
    public_hex = public_key.public_bytes_raw().hex()

    manifest = build_packet_manifest(
        title="Security Packet",
        markdown="# A",
        payloads=[{"kind": "text", "path": "README.md"}],
        resonance={"allowed_sectors": ["founder", "research"]},
    )

    signed = sign_packet_manifest(manifest, private_key=private_hex, key_id="k1")
    status = verify_packet_manifest(signed, public_keys={"k1": public_hex})

    assert status["ok"] is True
    assert status["reason"] == "verified"


def test_manifest_signature_rejects_tamper() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_hex = private_key.private_bytes_raw().hex()
    public_hex = public_key.public_bytes_raw().hex()

    manifest = build_packet_manifest(
        title="Security Packet",
        markdown="# A",
        payloads=[{"kind": "text", "path": "README.md"}],
    )
    signed = sign_packet_manifest(manifest, private_key=private_hex, key_id="k1")

    signed["title"] = "Tampered"
    status = verify_packet_manifest(signed, public_keys={"k1": public_hex})

    assert status["ok"] is False
    assert status["reason"] == "invalid_signature"


def test_manifest_freshness_window() -> None:
    now = datetime.now(timezone.utc)
    manifest = {
        "created_at": _utc(now - timedelta(seconds=15)),
        "resonance": {"expires_at": _utc(now + timedelta(minutes=5))},
    }
    stale_manifest = {
        "created_at": _utc(now - timedelta(days=2)),
        "resonance": {},
    }

    ok = check_manifest_freshness(manifest, max_age_seconds=120)
    stale = check_manifest_freshness(stale_manifest, max_age_seconds=120)

    assert ok["ok"] is True
    assert ok["reason"] == "fresh"
    assert stale["ok"] is False
    assert stale["reason"] == "stale_manifest"


def test_sector_authorization_policy() -> None:
    manifest = {
        "resonance": {
            "allowed_sectors": ["founder", "research", "research"],
        }
    }

    allowed = is_sector_authorized(manifest, "research")
    denied = is_sector_authorized(manifest, "operator")

    assert allowed["ok"] is True
    assert allowed["reason"] == "sector_allowed"
    assert denied["ok"] is False
    assert denied["reason"] == "sector_denied"
