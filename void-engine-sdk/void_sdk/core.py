"""
VoidSDK — Core Event Tracking
PROJECT VOID | Umar Latif | Bolton, England | April 2026

The VOID SDK tracks meaning, not clicks.
Every event is an Entity · Condition · Action triple stamped with:
  - a VOID codon (what kind of meaning)
  - an Al-Jabr 286 hash (sovereign attribution digest)
  - a formation score (0.0–1.0 resonance reading)

Usage:
    from void_sdk import VoidSDK

    sdk = VoidSDK(license_key="your-key")  # or omit for FREE tier

    sdk.track(
        entity="user:abc123",
        condition="frequency:432hz formation_score:0.87",
        action="encode",
        codon="voidecho",
        meta={"chars": 420, "share_link": "/voidmessage/r/abc"}
    )

    records = sdk.recall(entity="user:abc123", codon="voidecho")
    print(sdk.stats())
"""

import time
from typing import Optional

from .hash286 import sign286, formation_score
from .license import validate, check_limit, check_codon, LicenseState
from .memory import VoidMemory
from .codons import get_codon, all_codons


class VoidSDK:
    """
    Drop-in sovereign attribution SDK for Flask (and any Python) applications.

    Args:
        license_key: Your VOID license key. Omit for FREE tier.
        db_path:     Path to local SQLite memory file (default: .void_memory.db)
        pg_dsn:      PostgreSQL DSN for MEMORY/SOVEREIGN tiers. If set, uses PG.
    """

    VERSION = "1.0.0"
    VOID_ORIGIN = "void-stego-engine.replit.app"

    def __init__(
        self,
        license_key: Optional[str] = None,
        db_path: str = ".void_memory.db",
        pg_dsn: Optional[str] = None,
    ):
        self._key = license_key
        self._license: Optional[LicenseState] = None

        if pg_dsn:
            try:
                from .memory import VoidMemoryPG
                self._memory = VoidMemoryPG(pg_dsn)
            except (ImportError, AttributeError):
                self._memory = VoidMemory(db_path)
        else:
            self._memory = VoidMemory(db_path)

    @property
    def license(self) -> LicenseState:
        if self._license is None or (time.time() - self._license.cached_at > 3600):
            self._license = validate(self._key)
        return self._license

    def track(
        self,
        entity: str,
        condition: str,
        action: str,
        codon: str,
        meta: Optional[dict] = None,
    ) -> dict:
        """
        Record an Entity · Condition · Action event.

        Returns a dict with:
          - ok (bool)
          - event_id (int, if ok)
          - digest (str, Al-Jabr 286 hash)
          - formation_score (float)
          - tier (str)
          - reason (str, if not ok)
        """
        lic = self.license

        codon_allowed, codon_reason = check_codon(lic, codon)
        if not codon_allowed:
            return {"ok": False, "reason": codon_reason, "tier": lic.tier}

        events_today = self._memory.events_today(entity)
        limit_ok, limit_reason = check_limit(lic, events_today)
        if not limit_ok:
            return {"ok": False, "reason": limit_reason, "tier": lic.tier}

        ts = time.time()
        raw = f"entity:{entity} | condition:{condition} | action:{action} | codon:{codon}"
        digest = sign286(raw, ts)
        score = formation_score(raw)

        event_id = self._memory.record(
            entity=entity,
            condition=condition,
            action=action,
            codon=codon,
            digest=digest,
            meta=meta,
            ts=ts,
        )

        return {
            "ok": True,
            "event_id": event_id,
            "digest": digest,
            "formation_score": score,
            "tier": lic.tier,
            "codon": codon,
            "ts": ts,
        }

    def recall(
        self,
        entity: Optional[str] = None,
        codon: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Recall formation records from memory."""
        return self._memory.recall(entity=entity, codon=codon, limit=limit)

    def stats(self) -> dict:
        """Return aggregate statistics from the memory store."""
        mem_stats = self._memory.stats()
        return {
            **mem_stats,
            "tier": self.license.tier,
            "sdk_version": self.VERSION,
            "void_origin": self.VOID_ORIGIN,
        }

    def codons(self) -> dict:
        """Return all available codon definitions."""
        return all_codons()

    def sign(self, data: str) -> str:
        """Sign arbitrary data with the Al-Jabr 286 hash."""
        return sign286(data)

    def score(self, text: str) -> float:
        """Return the formation resonance score (0.0–1.0) for arbitrary text."""
        return formation_score(text)
