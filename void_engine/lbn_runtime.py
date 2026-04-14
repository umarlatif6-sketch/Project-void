"""LBN runtime helpers for active pair lock, validation, and audit enrichment."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _active_mode() -> str:
    mode = (os.getenv("VOID_LBN_MODE") or "project").strip().lower()
    return mode if mode in {"project", "standalone"} else "project"


def _active_route() -> str:
    route = (os.getenv("VOID_LBN_ACTIVE_ROUTE") or "primary").strip().lower()
    return route if route in {"primary", "fallback"} else "primary"


def _payload_path(mode: str) -> Path:
    explicit = (os.getenv("VOID_LBN_PAYLOAD_PATH") or "").strip()
    if explicit:
        return Path(explicit)
    return ROOT / "data" / f"lbn_agent_payloads.{mode}.json"


def load_active_payload() -> Dict[str, Any]:
    mode = _active_mode()
    route = _active_route()
    path = _payload_path(mode)

    if not path.exists() or not path.is_file():
        return {
            "ok": False,
            "reason": "payload_file_missing",
            "mode": mode,
            "route": route,
            "path": str(path),
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "ok": False,
            "reason": "payload_file_invalid_json",
            "mode": mode,
            "route": route,
            "path": str(path),
        }

    slot = ((payload.get("payloads") or {}).get(route) or {})
    codon_map = slot.get("codon_map") or {}
    channels = slot.get("channels") or []

    if not isinstance(codon_map, dict):
        return {
            "ok": False,
            "reason": "invalid_codon_map",
            "mode": mode,
            "route": route,
            "path": str(path),
        }

    return {
        "ok": True,
        "mode": mode,
        "route": route,
        "path": str(path),
        "primary_pair": payload.get("primary_pair"),
        "fallback_pair": payload.get("fallback_pair"),
        "active_pair": slot.get("pair"),
        "codon_map": codon_map,
        "channels": channels if isinstance(channels, list) else [],
    }


def extract_lbn_context(request_data: Dict[str, Any] | None, manifest: Dict[str, Any] | None) -> Dict[str, str]:
    request_data = request_data or {}
    manifest = manifest or {}

    lbn_from_request = request_data.get("lbn") if isinstance(request_data.get("lbn"), dict) else {}
    lbn_from_manifest = ((manifest.get("resonance") or {}).get("lbn")
                         if isinstance((manifest.get("resonance") or {}).get("lbn"), dict)
                         else {})

    merged = dict(lbn_from_manifest)
    merged.update(lbn_from_request)

    out = {
        "function": str(merged.get("function") or "").strip(),
        "codon": str(merged.get("codon") or "").strip(),
        "surface": str(merged.get("surface") or "").strip(),
        "channel": str(merged.get("channel") or "").strip(),
    }
    return out


def validate_lbn_context(lbn: Dict[str, str], strict: bool) -> Dict[str, Any]:
    function = str((lbn or {}).get("function") or "").strip()
    codon = str((lbn or {}).get("codon") or "").strip()
    surface = str((lbn or {}).get("surface") or "").strip()
    channel = str((lbn or {}).get("channel") or "").strip()

    active = load_active_payload()
    result: Dict[str, Any] = {
        "strict": bool(strict),
        "function": function,
        "codon": codon,
        "surface": surface,
        "channel": channel,
    }

    if not active.get("ok"):
        result.update({
            "ok": not strict,
            "reason": active.get("reason"),
            "mode": active.get("mode"),
            "route": active.get("route"),
            "path": active.get("path"),
        })
        return result

    codon_map = active.get("codon_map") or {}
    valid_codons = set(str(v) for v in codon_map.values() if isinstance(v, str) and v)

    result.update({
        "mode": active.get("mode"),
        "route": active.get("route"),
        "active_pair": active.get("active_pair"),
        "primary_pair": active.get("primary_pair"),
        "fallback_pair": active.get("fallback_pair"),
        "payload_path": active.get("path"),
    })

    if strict and not function and not codon:
        result.update({"ok": False, "reason": "missing_lbn_fields"})
        return result

    if function and function not in codon_map:
        result.update({"ok": False if strict else True, "reason": "unknown_function"})
        return result

    if codon and codon not in valid_codons:
        result.update({"ok": False if strict else True, "reason": "unknown_codon"})
        return result

    resolved_codon = codon_map.get(function) if function else None
    canonical_alias = codon_map.get(f"{function}_canonical") if function else None

    if function and codon:
        if codon not in {resolved_codon, canonical_alias}:
            result.update({
                "ok": False if strict else True,
                "reason": "function_codon_mismatch",
                "resolved_codon": resolved_codon,
                "canonical_alias": canonical_alias,
            })
            return result

    result.update({
        "ok": True,
        "reason": "validated" if (function or codon) else "no_lbn_payload",
        "resolved_codon": resolved_codon,
        "canonical_alias": canonical_alias,
    })
    return result


def lbn_validation_enabled() -> bool:
    return _env_bool("VOID_LBN_VALIDATE", default=False)
