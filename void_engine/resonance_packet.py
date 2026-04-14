"""Resonance Packet format: markdown doors into hex-addressed multimodal payloads.

This module makes markdown a pointer layer only.
Primary meaning lives in packet manifests with deterministic hex locators.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path(__file__).resolve().parents[1]

DOOR_PATTERN = re.compile(r"^<!--\s*VOID_DOOR:(\{.*\})\s*-->$", re.MULTILINE)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_epoch(ts: str) -> Optional[int]:
    if not ts:
        return None
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    return int(dt.timestamp())


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_manifest_payload(manifest: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(manifest)
    out.pop("signature", None)
    return out


def _load_private_key(key_material: str) -> Ed25519PrivateKey:
    raw = key_material.strip()
    if raw.startswith("-----BEGIN"):
        return serialization.load_pem_private_key(raw.encode("utf-8"), password=None)
    try:
        return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(raw))
    except Exception as exc:
        raise ValueError("Invalid Ed25519 private key material") from exc


def _load_public_key(key_material: str) -> Ed25519PublicKey:
    raw = key_material.strip()
    if raw.startswith("-----BEGIN"):
        return serialization.load_pem_public_key(raw.encode("utf-8"))
    try:
        return Ed25519PublicKey.from_public_bytes(bytes.fromhex(raw))
    except Exception as exc:
        raise ValueError("Invalid Ed25519 public key material") from exc


def _relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def normalize_payload_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a payload descriptor and derive deterministic locator fields.

    Accepted entry fields:
      - kind: z_axis_image | z_axis_video | audio | text | binary
      - path: local file path (preferred)
      - hex: precomputed hex identity (optional)
      - metadata: arbitrary object
    """
    kind = str(entry.get("kind") or "binary").strip() or "binary"
    raw_path = str(entry.get("path") or "").strip()
    metadata = entry.get("metadata") or {}

    resolved_hex = str(entry.get("hex") or "").strip().lower()
    size_bytes: Optional[int] = None
    rel_path: Optional[str] = None

    if raw_path:
        p = Path(raw_path)
        if p.exists() and p.is_file():
            resolved_hex = resolved_hex or _sha256_file(p)
            size_bytes = p.stat().st_size
            rel_path = _relative_path(p)
        else:
            # Keep unresolved paths explicit so callers can see what failed.
            rel_path = raw_path

    if not resolved_hex:
        # Deterministic fallback from entry body when binary/file is absent.
        body = json.dumps({"kind": kind, "path": rel_path, "metadata": metadata}, sort_keys=True)
        resolved_hex = _sha256_bytes(body.encode("utf-8"))

    return {
        "kind": kind,
        "hex": resolved_hex,
        "path": rel_path,
        "size_bytes": size_bytes,
        "metadata": metadata,
    }


def build_packet_manifest(
    *,
    title: str,
    markdown: str,
    payloads: Iterable[Dict[str, Any]],
    resonance: Optional[Dict[str, Any]] = None,
    codec_version: str = "RPK1",
) -> Dict[str, Any]:
    """Build a canonical resonance packet manifest with hex locator map."""
    normalized_payloads = [normalize_payload_entry(p) for p in payloads]

    door_body = {
        "title": title,
        "markdown_sha256": _sha256_bytes(markdown.encode("utf-8")),
        "payload_hexes": [p["hex"] for p in normalized_payloads],
        "resonance": resonance or {},
        "codec": codec_version,
    }
    packet_id = _sha256_bytes(json.dumps(door_body, sort_keys=True).encode("utf-8"))

    hex_locator_map: Dict[str, Dict[str, Any]] = {}
    for p in normalized_payloads:
        hex_locator_map[p["hex"]] = {
            "kind": p["kind"],
            "path": p.get("path"),
            "size_bytes": p.get("size_bytes"),
            "metadata": p.get("metadata") or {},
        }

    return {
        "packet_id": packet_id,
        "codec": codec_version,
        "created_at": _utc_now(),
        "nonce": secrets.token_hex(16),
        "title": title,
        "markdown_sha256": door_body["markdown_sha256"],
        "payload_count": len(normalized_payloads),
        "payload_hexes": door_body["payload_hexes"],
        "resonance": resonance or {},
        "hex_locator_map": hex_locator_map,
    }


def sign_packet_manifest(
    manifest: Dict[str, Any],
    *,
    private_key: str,
    key_id: str = "default",
) -> Dict[str, Any]:
    """Sign a packet manifest using Ed25519 and attach detached signature metadata."""
    key = _load_private_key(private_key)
    payload = _canonical_manifest_payload(manifest)
    signature = key.sign(_canonical_json_bytes(payload)).hex()
    signed = dict(manifest)
    signed["signature"] = {
        "alg": "Ed25519",
        "key_id": key_id,
        "sig": signature,
        "signed_at": _utc_now(),
    }
    return signed


def verify_packet_manifest(
    manifest: Dict[str, Any],
    *,
    public_keys: Dict[str, str],
) -> Dict[str, Any]:
    """Verify signed manifest with a key registry keyed by signature key_id."""
    sig = manifest.get("signature") or {}
    key_id = str(sig.get("key_id") or "").strip()
    hex_sig = str(sig.get("sig") or "").strip().lower()
    alg = str(sig.get("alg") or "")
    if alg != "Ed25519":
        return {"ok": False, "reason": "unsupported_algorithm"}
    if not key_id or not hex_sig:
        return {"ok": False, "reason": "missing_signature"}
    key_material = (public_keys or {}).get(key_id)
    if not key_material:
        return {"ok": False, "reason": "unknown_key_id", "key_id": key_id}
    try:
        key = _load_public_key(key_material)
        key.verify(bytes.fromhex(hex_sig), _canonical_json_bytes(_canonical_manifest_payload(manifest)))
        return {"ok": True, "reason": "verified", "key_id": key_id}
    except InvalidSignature:
        return {"ok": False, "reason": "invalid_signature", "key_id": key_id}
    except Exception:
        return {"ok": False, "reason": "verification_error", "key_id": key_id}


def check_manifest_freshness(manifest: Dict[str, Any], max_age_seconds: int = 86400) -> Dict[str, Any]:
    """Check replay window using created_at timestamp and optional expires_at in resonance block."""
    now = int(datetime.now(timezone.utc).timestamp())
    created_at = str(manifest.get("created_at") or "")
    created_epoch = _utc_epoch(created_at)
    if created_epoch is None:
        return {"ok": False, "reason": "invalid_created_at"}

    age_seconds = now - created_epoch
    if age_seconds < 0:
        return {"ok": False, "reason": "future_timestamp", "age_seconds": age_seconds}
    if age_seconds > max_age_seconds:
        return {"ok": False, "reason": "stale_manifest", "age_seconds": age_seconds}

    expires_at = str((manifest.get("resonance") or {}).get("expires_at") or "")
    if expires_at:
        exp_epoch = _utc_epoch(expires_at)
        if exp_epoch is None:
            return {"ok": False, "reason": "invalid_expires_at"}
        if now > exp_epoch:
            return {"ok": False, "reason": "expired", "age_seconds": age_seconds}

    return {"ok": True, "reason": "fresh", "age_seconds": age_seconds}


def extract_allowed_sectors(manifest: Dict[str, Any]) -> List[str]:
    """Extract allowed sectors from resonance policy metadata.

    Expected location: manifest['resonance']['allowed_sectors'] as list[str].
    """
    raw = (manifest.get("resonance") or {}).get("allowed_sectors") or []
    if not isinstance(raw, list):
        return []
    allowed: List[str] = []
    for item in raw:
        sector = str(item or "").strip().lower()
        if sector:
            allowed.append(sector)
    # Keep deterministic ordering without duplicates.
    return sorted(set(allowed))


def is_sector_authorized(manifest: Dict[str, Any], sector: str) -> Dict[str, Any]:
    """Check whether a sector is authorized by manifest policy."""
    sector_norm = str(sector or "").strip().lower()
    if not sector_norm:
        return {"ok": False, "reason": "missing_sector"}
    allowed = extract_allowed_sectors(manifest)
    # If policy is absent, keep backward compatibility and treat as open.
    if not allowed:
        return {"ok": True, "reason": "open_policy", "allowed": []}
    if sector_norm in allowed:
        return {"ok": True, "reason": "sector_allowed", "allowed": allowed}
    return {"ok": False, "reason": "sector_denied", "allowed": allowed}


def build_markdown_door(manifest: Dict[str, Any], heading: Optional[str] = None) -> str:
    """Render a markdown door comment + optional heading.

    Example output:
      <!-- VOID_DOOR:{...json...} -->
      ## Packet Door: My Payload
    """
    door_json = {
        "packet_id": manifest.get("packet_id"),
        "codec": manifest.get("codec", "RPK1"),
        "title": manifest.get("title", "untitled"),
        "payload_hexes": manifest.get("payload_hexes", []),
        "markdown_sha256": manifest.get("markdown_sha256"),
    }
    comment = f"<!-- VOID_DOOR:{json.dumps(door_json, separators=(',', ':'))} -->"

    if not heading:
        return comment
    return f"{comment}\n\n## Packet Door: {heading}"


def parse_markdown_doors(markdown_text: str) -> List[Dict[str, Any]]:
    """Extract all VOID_DOOR comment payloads from markdown text."""
    doors: List[Dict[str, Any]] = []
    for match in DOOR_PATTERN.finditer(markdown_text):
        blob = match.group(1)
        try:
            doors.append(json.loads(blob))
        except Exception:
            continue
    return doors


def resolve_hex_locator(manifest: Dict[str, Any], hex_id: str) -> Optional[Dict[str, Any]]:
    """Resolve one hex id from packet manifest locator map."""
    h = str(hex_id or "").strip().lower()
    if not h:
        return None
    return (manifest.get("hex_locator_map") or {}).get(h)


def resolve_packet_paths(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Resolve payload paths listed in the manifest with existence metadata."""
    out: List[Dict[str, Any]] = []
    for h in manifest.get("payload_hexes", []) or []:
        entry = resolve_hex_locator(manifest, h)
        if not entry:
            out.append({"hex": h, "exists": False, "error": "missing_locator"})
            continue
        raw_path = entry.get("path")
        if not raw_path:
            out.append({"hex": h, "exists": False, "error": "missing_path", "entry": entry})
            continue
        path = ROOT / raw_path if not Path(raw_path).is_absolute() else Path(raw_path)
        out.append(
            {
                "hex": h,
                "kind": entry.get("kind"),
                "path": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            }
        )
    return out
