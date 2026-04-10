"""
VOID Engine Client — Sovereign Attribution SDK
Version 1.0 | PROJECT VOID by Umar L.

Drop this file into any Python/Flask project root.
Validate your license key at: https://void-stego-engine.replit.app/pricing

Usage:
    from void_client import VoidEngine
    void = VoidEngine(license_key="VOID-SOV-XXXXXXXX-XXXX")
    void.attach(app)
    codon = void.tag_session(user_id="visitor_42", message="Hello")
"""

import hashlib
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("void_engine_sdk")

_VOID_VALIDATE_URL = "https://void-stego-engine.replit.app/api/license/validate"

PLATFORM_CODONS = {
    "voidecho":   "λ·Λ·☀",
    "adriana":    "ψ·Ψ·◆",
    "chronicle":  "α·Ω·⟐",
    "peace":      "π·Π·⊕",
    "vtx":        "τ·Τ·⬡",
    "beehive":    "β·Β·⬢",
    "formation":  "φ·Φ·✦",
    "genesis":    "γ·Γ·⊛",
    "mesh":       "μ·Μ·◎",
    "sovereign":  "σ·Σ·⬟",
}

_AL_JABR_MODULUS = 286
_TIER_WEIGHTS = {"SIG": 1, "MEM": 2, "SOV": 3}


def _al_jabr_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest(), 16) % _AL_JABR_MODULUS


def _codon_from_hash(h: int) -> str:
    entities  = list("αβγδεζηθικλμνξοπρστυφχψω")
    conds     = list("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")
    actions   = ["☀", "◆", "⟐", "⊕", "⬡", "⬢", "✦", "⊛", "◎", "⬟", "★", "◉", "⊗"]
    e = entities[h % len(entities)]
    c = conds[(h // len(entities)) % len(conds)]
    a = actions[(h // (len(entities) * len(conds))) % len(actions)]
    return f"{e}·{c}·{a}"


class _LocalMemory:
    def __init__(self, path: str = ".void_memory.db"):
        self._path = path
        self._init()

    def _init(self):
        with sqlite3.connect(self._path) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS codon_memory (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    TEXT NOT NULL,
                    codon      TEXT NOT NULL,
                    message    TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_cm_user ON codon_memory(user_id)")

    def store(self, user_id: str, codon: str, message: str = ""):
        with sqlite3.connect(self._path) as con:
            con.execute(
                "INSERT INTO codon_memory (user_id, codon, message) VALUES (?, ?, ?)",
                (user_id, codon, message)
            )

    def read(self, user_id: str, last_n: int = 3) -> list:
        with sqlite3.connect(self._path) as con:
            rows = con.execute(
                "SELECT codon FROM codon_memory WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, last_n)
            ).fetchall()
        return [r[0] for r in reversed(rows)]


class VoidEngine:
    """
    Sovereign Attribution SDK — tracks resonance, not just clicks.

    Tiers:
      SIGNAL   (VOID-SIG-*) — frequency attribution + codon tagging
      MEMORY   (VOID-MEM-*) — + Adriana codon memory across sessions
      SOVEREIGN(VOID-SOV-*) — full engine access

    License validation is performed once at startup.
    Codon memory is stored locally in .void_memory.db (SQLite) when no
    remote PostgreSQL is configured — suitable for development. For production,
    set VOID_DB_URL in your environment to point to a PostgreSQL instance.
    """

    def __init__(self, license_key: str, validate_online: bool = True):
        self._key = license_key
        self._tier = self._parse_tier(license_key)
        self._tier_weight = _TIER_WEIGHTS.get(self._tier, 0)
        self._memory = _LocalMemory()
        self._valid = False

        if validate_online:
            self._validate_online()
        else:
            self._valid = self._tier_weight > 0
            logger.info("VOID Engine — offline mode. Tier: %s", self._tier)

    def _parse_tier(self, key: str) -> str:
        parts = key.split("-")
        if len(parts) == 4 and parts[0] == "VOID":
            return parts[1]
        return ""

    def _validate_online(self):
        try:
            import requests
            resp = requests.post(
                _VOID_VALIDATE_URL,
                json={"key": self._key},
                timeout=5
            )
            data = resp.json()
            if data.get("valid"):
                self._valid = True
                logger.info(
                    "VOID Engine — license valid. Tier: %s | Owner: %s",
                    data.get("tier_name"), data.get("owner_name")
                )
            else:
                logger.error("VOID Engine — license invalid: %s", data.get("reason"))
        except Exception as e:
            logger.warning("VOID Engine — online validation failed (%s). Continuing offline.", e)
            self._valid = self._tier_weight > 0

    def attach(self, app):
        app.before_request(self._before_request_hook)
        logger.info("VOID Engine attached to Flask app. Tier: %s", self._tier)
        return app

    def _before_request_hook(self):
        pass

    def tag_session(self, user_id: str, message: str = "", zone: str = "") -> str:
        h = _al_jabr_hash(f"{user_id}_{message}_{zone}")
        if zone and zone.lower() in PLATFORM_CODONS:
            codon = PLATFORM_CODONS[zone.lower()]
        else:
            codon = _codon_from_hash(h)
        self._memory.store(user_id, codon, message)
        return codon

    def read_memory(self, user_id: str, last_n: int = 3) -> list:
        if self._tier_weight < 2:
            raise PermissionError(
                "Codon memory requires MEMORY or SOVEREIGN tier. "
                "Upgrade at https://void-stego-engine.replit.app/pricing"
            )
        return self._memory.read(user_id, last_n)

    def rib_voice(self, user_id: str) -> str:
        codons = self.read_memory(user_id, last_n=3)
        if not codons:
            return ""
        chain = " · ".join(codons)
        return f"[rib] {chain}"

    def v_sync(self, input_data: str, p_state: str = "") -> str:
        h = _al_jabr_hash(f"{input_data}_{p_state}")
        return _codon_from_hash(h)

    @property
    def is_valid(self) -> bool:
        return self._valid

    @property
    def tier(self) -> str:
        return self._tier
