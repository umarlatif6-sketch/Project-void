"""Loader for Seed+Chronicle continuity contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class ContinuityContractError(RuntimeError):
    """Raised when continuity contract is unavailable or invalid."""


def load_continuity_contract(repo_root: str | Path) -> Dict[str, Any]:
    """Load continuity contract that unifies RecursiveMAS with Seed/Chronicle rails."""
    root = Path(repo_root)
    contract_path = root / "manifest" / "continuity_chordon_contract.json"
    if not contract_path.exists():
        raise ContinuityContractError(f"Missing continuity contract: {contract_path}")

    with contract_path.open("r", encoding="utf-8") as f:
        contract = json.load(f)

    required_keys = {
        "contract",
        "status",
        "purpose",
        "sources",
        "read_order",
        "continuity_checks",
        "recursive_to_codon_bridge",
        "synergy_lanes",
        "runtime_entrypoints",
        "discovery",
    }
    missing = sorted(required_keys - contract.keys())
    if missing:
        missing_csv = ", ".join(missing)
        raise ContinuityContractError(f"Continuity contract missing keys: {missing_csv}")

    if contract.get("contract") != "continuity_chordon.v1":
        found = contract.get("contract")
        raise ContinuityContractError(
            f"Unsupported continuity contract version: {found}"
        )

    return contract


def resolve_continuity_sources(repo_root: str | Path) -> Dict[str, Path]:
    """Return absolute paths for continuity sources defined by contract."""
    root = Path(repo_root)
    contract = load_continuity_contract(root)
    sources = contract.get("sources", {})
    return {name: (root / rel_path) for name, rel_path in sources.items()}
