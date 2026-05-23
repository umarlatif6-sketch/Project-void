"""RecursiveMAS core package."""

from .contract_loader import is_role_supported, load_recursive_mas_contract
from .continuity_loader import load_continuity_contract, resolve_continuity_sources
from .bootstrap_guard import continuity_enforce_enabled, run_governance_bootstrap

__all__ = [
	"load_recursive_mas_contract",
	"is_role_supported",
	"load_continuity_contract",
	"resolve_continuity_sources",
	"continuity_enforce_enabled",
	"run_governance_bootstrap",
]
