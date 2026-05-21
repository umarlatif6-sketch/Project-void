"""Contract loader for RecursiveMAS agent interoperability."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class ContractError(RuntimeError):
    """Raised when the RecursiveMAS contract is missing or invalid."""


def load_recursive_mas_contract(repo_root: str | Path) -> Dict[str, Any]:
    """Load the canonical RecursiveMAS contract from manifest path."""
    root = Path(repo_root)
    contract_path = root / "manifest" / "recursive_mas_contract.json"
    if not contract_path.exists():
        raise ContractError(f"Missing contract file: {contract_path}")

    with contract_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    required = {
        "contract",
        "status",
        "cognitive_head",
        "roles",
        "required_agent_fields",
        "runtime_entrypoints",
        "fail_closed",
        "discovery",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ContractError(f"Contract missing required keys: {', '.join(missing)}")

    if data.get("contract") != "recursive_mas.v1":
        raise ContractError(
            f"Unsupported contract version: {data.get('contract')} (expected recursive_mas.v1)"
        )

    return data


def is_role_supported(contract: Dict[str, Any], role: str) -> bool:
    """Return True when the requested role exists in the active contract."""
    roles = contract.get("roles", [])
    return role in roles
