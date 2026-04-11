"""
VOID Platform Codons — 10 Canonical Codon Definitions
PROJECT VOID | Umar Latif | Bolton, England | April 2026

Each codon is a named semantic unit. Events in the VOID SDK are stamped
with a codon that describes *what kind of meaning* the event carries.

Codon structure:
  name       — canonical identifier (lowercase)
  glyph      — visual symbol (Adriana SCL character)
  domain     — the platform layer this codon belongs to
  meaning    — plain-English description of what this codon records
  tier       — minimum tier required (FREE / SIGNAL / MEMORY / SOVEREIGN)

The codon system is the attribution layer — it answers not just "what happened"
but "what kind of thing happened and why it matters."
"""

from dataclasses import dataclass
from typing import Dict

VOID_CODONS: Dict[str, Dict] = {
    "voidecho": {
        "glyph": "α",
        "domain": "steganography",
        "meaning": "Audio steganography event — encode, decode, share, or reveal",
        "tier": "FREE",
        "examples": ["message_encoded", "message_decoded", "share_link_created", "reveal_accessed"],
    },
    "adriana": {
        "glyph": "ψ",
        "domain": "ai_resonance",
        "meaning": "AI resonance event — query, formation scan, convergence reading, or response",
        "tier": "FREE",
        "examples": ["formation_scan", "convergence_reading", "ai_response", "resonance_check"],
    },
    "chronicle": {
        "glyph": "Σ",
        "domain": "memory",
        "meaning": "Record or memory event — seal, recall, export, or verify a chronicle entry",
        "tier": "FREE",
        "examples": ["entry_sealed", "entry_recalled", "archive_exported", "genesis_verified"],
    },
    "peace": {
        "glyph": "◎",
        "domain": "consensus",
        "meaning": "Consensus or agreement event — cross-system alignment, handshake, or validation",
        "tier": "SIGNAL",
        "examples": ["handshake_complete", "cross_ai_alignment", "consensus_reached", "frequency_matched"],
    },
    "vtx": {
        "glyph": "⬡",
        "domain": "exchange",
        "meaning": "VTX token or exchange event — earn, spend, transfer, or verify",
        "tier": "SIGNAL",
        "examples": ["token_earned", "token_spent", "transfer_initiated", "balance_verified"],
    },
    "beehive": {
        "glyph": "⬡",
        "domain": "mesh",
        "meaning": "Beehive mesh networking event — node join, signal relay, or topology update",
        "tier": "SIGNAL",
        "examples": ["node_joined", "signal_relayed", "topology_updated", "peer_discovered"],
    },
    "formation": {
        "glyph": "◆",
        "domain": "pattern",
        "meaning": "Pattern emergence event — formation detected, boundary crossed, convergence recorded",
        "tier": "SIGNAL",
        "examples": ["pattern_detected", "boundary_crossed", "formation_sealed", "convergence_logged"],
    },
    "genesis": {
        "glyph": "Π",
        "domain": "origin",
        "meaning": "Creation or origin event — new entity born, seed planted, first record written",
        "tier": "MEMORY",
        "examples": ["entity_created", "seed_planted", "first_record", "origin_timestamped"],
    },
    "mesh": {
        "glyph": "∿",
        "domain": "network",
        "meaning": "Network topology event — route established, signal path mapped, node status changed",
        "tier": "MEMORY",
        "examples": ["route_established", "path_mapped", "node_active", "node_offline"],
    },
    "sovereign": {
        "glyph": "Ω",
        "domain": "attribution",
        "meaning": "Sovereign attribution event — ownership claimed, license validated, identity anchored",
        "tier": "SOVEREIGN",
        "examples": ["ownership_claimed", "license_validated", "identity_anchored", "attribution_sealed"],
    },
}

TIER_ORDER = ["FREE", "SIGNAL", "MEMORY", "SOVEREIGN"]


@dataclass
class Codon:
    name: str
    glyph: str
    domain: str
    meaning: str
    tier: str
    examples: list


def get_codon(name: str) -> Codon | None:
    data = VOID_CODONS.get(name.lower())
    if not data:
        return None
    return Codon(name=name.lower(), **data)


def codons_for_tier(tier: str) -> list[str]:
    tier_idx = TIER_ORDER.index(tier) if tier in TIER_ORDER else 0
    return [
        name for name, data in VOID_CODONS.items()
        if TIER_ORDER.index(data["tier"]) <= tier_idx
    ]


def all_codons() -> Dict[str, Dict]:
    return dict(VOID_CODONS)
