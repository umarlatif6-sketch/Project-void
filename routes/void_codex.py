"""VOID Codex routes: markdown <-> E·C·A encoding bridge."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path


from flask import Blueprint, jsonify, render_template, request

from void_engine.codex_codec import (
    decode_codex_to_markdown,
    encode_markdown_to_codex,
    markdown_structure_preview,
)
from void_engine.resonance_packet import (
    build_markdown_door,
    build_packet_manifest,
    check_manifest_freshness,
    is_sector_authorized,
    parse_markdown_doors,
    resolve_packet_paths,
    sign_packet_manifest,
    verify_packet_manifest,
)

logger = logging.getLogger(__name__)

void_codex_bp = Blueprint("void_codex", __name__)

ROOT = Path(__file__).resolve().parents[1]
AUDIT_LOG_PATH = ROOT / "data" / "packet_audit.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_verify_keys() -> dict:
    """Load verifier keyring from JSON in env.

    Format:
      VOID_PACKET_VERIFY_KEYS_JSON={"key-id":"<ed25519 pubkey hex or pem>"}
    """
    raw = (os.getenv("VOID_PACKET_VERIFY_KEYS_JSON") or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _append_audit(action: str, status: str, packet_id: str, details: dict | None = None) -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": _utc_now(),
        "action": action,
        "status": status,
        "packet_id": packet_id,
        "details": details or {},
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, separators=(",", ":")) + "\n")


@void_codex_bp.route("/codex")
def codex_page():
    return render_template("void_codex.html")


@void_codex_bp.route("/api/codex/encode", methods=["POST"])
def codex_encode():
    data = request.get_json(silent=True) or {}
    markdown = (data.get("markdown") or "").strip()
    if not markdown:
        return jsonify({"ok": False, "error": "Provide markdown text"}), 400

    try:
        encoded = encode_markdown_to_codex(markdown)
        preview = markdown_structure_preview(markdown)
        return jsonify({
            "ok": True,
            "encoded": encoded,
            "structure_preview": preview,
        })
    except Exception as exc:
        logger.error("Codex encode failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@void_codex_bp.route("/api/codex/decode", methods=["POST"])
def codex_decode():
    data = request.get_json(silent=True) or {}
    codex_text = (data.get("codex") or "").strip()
    if not codex_text:
        return jsonify({"ok": False, "error": "Provide codex text"}), 400

    try:
        decoded = decode_codex_to_markdown(codex_text)
        preview = markdown_structure_preview(decoded["markdown"])
        return jsonify({
            "ok": True,
            "decoded": decoded,
            "structure_preview": preview,
        })
    except Exception as exc:
        logger.error("Codex decode failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 400


@void_codex_bp.route("/api/codex/packet/build", methods=["POST"])
def codex_packet_build():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "VOID Packet").strip()
    markdown = data.get("markdown") or ""
    payloads = data.get("payloads") or []
    resonance = data.get("resonance") or {}
    allowed_sectors = data.get("allowed_sectors")
    expires_at = data.get("expires_at")

    if isinstance(allowed_sectors, list):
        resonance["allowed_sectors"] = [str(s).strip().lower() for s in allowed_sectors if str(s).strip()]
    if isinstance(expires_at, str) and expires_at.strip():
        resonance["expires_at"] = expires_at.strip()

    if not isinstance(payloads, list) or not payloads:
        return jsonify({"ok": False, "error": "Provide payloads[] with kind/path or kind/hex"}), 400

    try:
        manifest = build_packet_manifest(
            title=title,
            markdown=markdown,
            payloads=payloads,
            resonance=resonance,
        )
        private_key = (os.getenv("VOID_PACKET_SIGNING_PRIVATE_KEY") or "").strip()
        key_id = (os.getenv("VOID_PACKET_SIGNING_KEY_ID") or "default").strip()
        if private_key:
            manifest = sign_packet_manifest(manifest, private_key=private_key, key_id=key_id)
        door = build_markdown_door(manifest, heading=title)
        _append_audit(
            action="packet_build",
            status="ok",
            packet_id=str(manifest.get("packet_id") or "unknown"),
            details={
                "payload_count": manifest.get("payload_count", 0),
                "signed": bool(manifest.get("signature")),
            },
        )
        return jsonify({
            "ok": True,
            "manifest": manifest,
            "door_markdown": door,
        })
    except Exception as exc:
        logger.error("Codex packet build failed: %s", exc)
        _append_audit("packet_build", "error", "unknown", {"error": str(exc)})
        return jsonify({"ok": False, "error": str(exc)}), 500


@void_codex_bp.route("/api/codex/packet/parse-door", methods=["POST"])
def codex_packet_parse_door():
    data = request.get_json(silent=True) or {}
    markdown = (data.get("markdown") or "").strip()
    if not markdown:
        return jsonify({"ok": False, "error": "Provide markdown text"}), 400

    doors = parse_markdown_doors(markdown)
    return jsonify({"ok": True, "doors": doors, "count": len(doors)})


@void_codex_bp.route("/api/codex/packet/resolve", methods=["POST"])
def codex_packet_resolve():
    data = request.get_json(silent=True) or {}
    manifest = data.get("manifest") or {}
    if not isinstance(manifest, dict) or not manifest:
        return jsonify({"ok": False, "error": "Provide packet manifest object"}), 400

    try:
        packet_id = str(manifest.get("packet_id") or "unknown")
        sector = (request.headers.get("X-VOID-Sector") or request.args.get("sector") or "").strip().lower()
        strict_sector = (os.getenv("VOID_PACKET_REQUIRE_SECTOR_POLICY") or "false").strip().lower() == "true"

        # Replay protection: reject stale manifests.
        max_age_seconds = int((os.getenv("VOID_PACKET_MAX_AGE_SECONDS") or "86400").strip())
        freshness = check_manifest_freshness(manifest, max_age_seconds=max_age_seconds)
        if not freshness.get("ok"):
            _append_audit("packet_resolve", "denied", packet_id, {"reason": freshness.get("reason")})
            return jsonify({"ok": False, "error": "Manifest freshness check failed", "details": freshness}), 403

        # Signature verification when keyring is configured.
        verify_keys = _load_verify_keys()
        if verify_keys:
            sig_status = verify_packet_manifest(manifest, public_keys=verify_keys)
            if not sig_status.get("ok"):
                _append_audit("packet_resolve", "denied", packet_id, {"reason": sig_status.get("reason")})
                return jsonify({"ok": False, "error": "Manifest signature verification failed", "details": sig_status}), 403

        # Sector authorization policy.
        sector_status = is_sector_authorized(manifest, sector)
        if strict_sector and sector_status.get("reason") == "open_policy":
            _append_audit("packet_resolve", "denied", packet_id, {"reason": "missing_sector_policy"})
            return jsonify({"ok": False, "error": "Sector policy required but missing"}), 403
        if not sector_status.get("ok"):
            _append_audit("packet_resolve", "denied", packet_id, {"reason": sector_status.get("reason")})
            return jsonify({"ok": False, "error": "Sector unauthorized", "details": sector_status}), 403

        resolved = resolve_packet_paths(manifest)
        _append_audit(
            "packet_resolve",
            "ok",
            packet_id,
            {
                "sector": sector,
                "resolved_count": len(resolved),
                "freshness_age_seconds": freshness.get("age_seconds"),
            },
        )
        return jsonify({"ok": True, "resolved": resolved, "count": len(resolved), "security": {
            "freshness": freshness,
            "sector": sector_status,
            "signature_verified": bool(verify_keys),
        }})
    except Exception as exc:
        logger.error("Codex packet resolve failed: %s", exc)
        _append_audit("packet_resolve", "error", str(manifest.get("packet_id") or "unknown"), {"error": str(exc)})
        return jsonify({"ok": False, "error": str(exc)}), 500
