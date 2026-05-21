"""Runtime bootstrap guard for RecursiveMAS governance and continuity rails."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .continuity_loader import load_continuity_contract, resolve_continuity_sources
from .contract_loader import load_recursive_mas_contract


def continuity_enforce_enabled() -> bool:
    """Return whether continuity enforcement is enabled."""
    raw = (os.getenv("VOID_CONTINUITY_ENFORCE") or "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _validate_timeline_passport(repo_root: Path) -> List[str]:
    errors: List[str] = []
    passport_path = repo_root / "manifest" / "timeline_passport.json"
    if not passport_path.exists():
        return [f"Missing timeline passport: {passport_path}"]

    try:
        with passport_path.open("r", encoding="utf-8") as f:
            passport = json.load(f)
    except Exception as exc:  # pragma: no cover - defensive read path
        return [f"Unreadable timeline passport: {exc}"]

    required = {"passport", "status", "sequence", "stop_gates", "output_card"}
    missing = sorted(required - set(passport.keys()))
    if missing:
        errors.append("Timeline passport missing keys: " + ", ".join(missing))

    if passport.get("passport") != "timeline_passport.v1":
        errors.append(
            "Unsupported timeline passport version: " + str(passport.get("passport"))
        )

    return errors


def run_governance_bootstrap(repo_root: str | Path) -> Dict[str, Any]:
    """Validate governance contracts required for continuity-safe runtime."""
    root = Path(repo_root)
    errors: List[str] = []

    try:
        recursive_contract = load_recursive_mas_contract(root)
    except Exception as exc:
        recursive_contract = None
        errors.append(f"RecursiveMAS contract check failed: {exc}")

    try:
        continuity_contract = load_continuity_contract(root)
    except Exception as exc:
        continuity_contract = None
        errors.append(f"Continuity contract check failed: {exc}")

    sources_missing: List[str] = []
    if continuity_contract is not None:
        sources = resolve_continuity_sources(root)
        sources_missing = [name for name, path in sources.items() if not path.exists()]
        if sources_missing:
            errors.append("Continuity sources missing: " + ", ".join(sorted(sources_missing)))

    errors.extend(_validate_timeline_passport(root))

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "enforce": continuity_enforce_enabled(),
        "recursive_contract": recursive_contract.get("contract") if recursive_contract else None,
        "continuity_contract": continuity_contract.get("contract") if continuity_contract else None,
        "missing_sources": sources_missing,
    }
