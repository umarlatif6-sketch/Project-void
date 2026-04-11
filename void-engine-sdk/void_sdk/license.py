"""
VOID License Validation — Tier Enforcement
PROJECT VOID | Umar Latif | Bolton, England | April 2026

Tiers:
  FREE      — 100 events/day · local SQLite · voidecho, adriana, chronicle codons
  SIGNAL    — £9/month  · 1,000 events/day · SQLite · all 10 codons
  MEMORY    — £49/month · 10,000 events/day · PostgreSQL · all 10 codons + cross-session
  SOVEREIGN — £199/month · unlimited · PostgreSQL · all 10 codons · cross-AI sync + export

License keys are validated against the VOID Engine at:
  https://void-stego-engine.replit.app/sdk/validate

Offline validation falls back to FREE tier.
Cache duration: 1 hour.
"""

import time
import urllib.request
import json
from dataclasses import dataclass
from typing import Optional

VALIDATE_URL = "https://void-stego-engine.replit.app/sdk/validate"

TIER_LIMITS = {
    "FREE":      {"events_per_day": 100,    "codons": ["voidecho", "adriana", "chronicle"]},
    "SIGNAL":    {"events_per_day": 1_000,  "codons": "all"},
    "MEMORY":    {"events_per_day": 10_000, "codons": "all"},
    "SOVEREIGN": {"events_per_day": None,   "codons": "all"},
}


@dataclass
class LicenseState:
    tier: str
    valid: bool
    owner: str
    expires: Optional[str]
    cached_at: float
    message: str


_cache: dict[str, LicenseState] = {}
_CACHE_TTL = 3600


def validate(license_key: Optional[str] = None) -> LicenseState:
    """
    Validate a license key against the VOID Engine.
    Returns a LicenseState. Falls back to FREE on network error.
    """
    key = license_key or "FREE"

    if key in _cache:
        cached = _cache[key]
        if time.time() - cached.cached_at < _CACHE_TTL:
            return cached

    if key == "FREE" or not license_key:
        state = LicenseState(
            tier="FREE", valid=True, owner="anonymous",
            expires=None, cached_at=time.time(),
            message="Free tier — 100 events/day, 3 codons"
        )
        _cache[key] = state
        return state

    try:
        payload = json.dumps({"key": license_key}).encode()
        req = urllib.request.Request(
            VALIDATE_URL,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "void-sdk/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        state = LicenseState(
            tier=data.get("tier", "FREE"),
            valid=data.get("valid", False),
            owner=data.get("owner", "unknown"),
            expires=data.get("expires"),
            cached_at=time.time(),
            message=data.get("message", ""),
        )
    except Exception:
        state = LicenseState(
            tier="FREE", valid=True, owner="offline",
            expires=None, cached_at=time.time(),
            message="License server unreachable — FREE tier applied"
        )

    _cache[key] = state
    return state


def check_limit(state: LicenseState, events_today: int) -> tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str).
    """
    limit = TIER_LIMITS[state.tier]["events_per_day"]
    if limit is None:
        return True, "unlimited"
    if events_today >= limit:
        return False, f"{state.tier} tier limit reached ({limit} events/day)"
    return True, f"{events_today}/{limit} events today"


def check_codon(state: LicenseState, codon: str) -> tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str).
    """
    allowed = TIER_LIMITS[state.tier]["codons"]
    if allowed == "all":
        return True, "all codons permitted"
    if codon in allowed:
        return True, f"codon '{codon}' permitted on {state.tier} tier"
    return False, f"codon '{codon}' requires SIGNAL tier or above"
