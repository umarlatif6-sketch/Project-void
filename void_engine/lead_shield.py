"""
Lead Shield — Al-Jabr 286 Master Logic Encryption Layer
        + Social Resonance Monitor (Task #81)

This module provides two distinct but complementary shielding functions:

1. ENCRYPTION SHIELD (Task #79):
   Wraps the Seed-to-Hex pipeline with a second encryption pass on "Master
   Logic" fields (the Why and How of the 286 Al-Jabr units) so the outside
   world sees only results, never the mechanics.
   Architecture:
     - Derives a 32-byte encryption key from the founder's QiSync salt using
       the Al-Jabr 286 Sovereign Hash pipeline.
     - Encrypts plaintext Master Logic fields with ChaCha20 (nonce-prefixed).
     - Stores only ciphertext + is_shielded = 1 flag in the Chronicle.
     - A founder-key holder can decrypt; the public sees only the Al-Jabr hash.

   HEX_DIGEST markers locked into VOID_CHRONICLE:
     0x4F62667573636174696F6E5F536869656C64   (Obfuscation_Shield)
     0x31385F536F6369616C5F5363617273         (18_Social_Scars)

2. SOCIAL RESONANCE MONITOR (Task #81):
   Watches for VOID-related external signal spikes (approximated from internal
   signal metrics when no real social API is wired).  When volatility crosses a
   configurable threshold, all VoidEcho broadcasting pauses and a "Gone Dark"
   status is displayed until conditions normalise.
   Design:
     - SignalSample objects accumulate in a rolling window.
     - Volatility is computed as the coefficient of variation (σ/μ) over the
       window so that both noisy and calm periods are handled proportionally.
     - When volatility > VOLATILITY_THRESHOLD the shield ACTIVATES:
         VoidEcho broadcast_paused flag is set to True; status → "GONE_DARK"
     - When volatility falls back below RECOVERY_THRESHOLD it DEACTIVATES:
         broadcast_paused is cleared; status → "CLEAR"
   Internal metrics fed to the monitor (no real social API):
     - Mycelium avg_signal_strength
     - Buffer Spore confidence
"""

import math
import os
import secrets
import threading
import time
import logging
from collections import deque
from typing import Dict, List, Optional

from void_engine.al_jabr_286 import (
    fatiha_286_derive_key,
    fatiha_286_hexdigest_from_str,
)

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── Encryption Shield constants ──────────────────────────────────────────────
SHIELD_NONCE_BYTES = 16
VOID_HEX_SEAL_1 = "4F62667573636174696F6E5F536869656C64"
VOID_HEX_SEAL_2 = "31385F536F6369616C5F5363617273"

_DEFAULT_QISYNC_SALT = os.environ.get(
    "LEAD_SHIELD_FOUNDER_KEY",
    "QiSync-Founder-Salt-VOID-286-Sovereign"
)

# ── Social Resonance Monitor constants ───────────────────────────────────────
VOLATILITY_THRESHOLD = 0.35
RECOVERY_THRESHOLD = 0.20
WINDOW_SIZE = 30
MIN_SAMPLES = 5


# ═══════════════════════════════════════════════════════════════════════════
# PART 1 — Encryption Shield (Task #79)
# ═══════════════════════════════════════════════════════════════════════════

def _derive_shield_key(passphrase: str = None) -> bytes:
    if not _CRYPTO_AVAILABLE:
        raise ImportError("cryptography package is required for Lead Shield encryption")
    salt = passphrase or _DEFAULT_QISYNC_SALT
    return fatiha_286_derive_key(salt)


def encrypt_master_logic(plaintext: str, founder_passphrase: str = None) -> dict:
    """
    Encrypt a Master Logic field using the Lead Shield.

    Returns a dict with:
      - ciphertext_hex: hex-encoded encrypted bytes (nonce + ciphertext)
      - public_hash:    Al-Jabr 286 hex digest of the plaintext (always visible)
      - is_shielded:    True
    """
    key = _derive_shield_key(founder_passphrase)
    nonce = secrets.token_bytes(SHIELD_NONCE_BYTES)
    data = plaintext.encode("utf-8")
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    enc = cipher.encryptor()
    ciphertext = enc.update(data) + enc.finalize()
    raw = nonce + ciphertext
    public_hash = fatiha_286_hexdigest_from_str(plaintext)
    return {
        "ciphertext_hex": raw.hex(),
        "public_hash": public_hash,
        "is_shielded": True,
        "void_seal_1": VOID_HEX_SEAL_1,
        "void_seal_2": VOID_HEX_SEAL_2,
    }


def decrypt_master_logic(ciphertext_hex: str, founder_passphrase: str = None) -> str:
    """
    Decrypt a Lead Shield-protected field using the founder key.

    Raises ValueError if the key is wrong or the data is malformed.
    """
    key = _derive_shield_key(founder_passphrase)
    raw = bytes.fromhex(ciphertext_hex)
    if len(raw) < SHIELD_NONCE_BYTES + 1:
        raise ValueError("Lead Shield: ciphertext too short")
    nonce = raw[:SHIELD_NONCE_BYTES]
    ciphertext = raw[SHIELD_NONCE_BYTES:]
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    dec = cipher.decryptor()
    plaintext = dec.update(ciphertext) + dec.finalize()
    return plaintext.decode("utf-8")


def shield_chronicle_field(plaintext: str, founder_passphrase: str = None) -> tuple:
    """
    Shield a chronicle entry field for Lead Shield storage.

    Returns (ciphertext_hex, public_hash, is_shielded=True).
    Used when writing shielded entries to the VOID_CHRONICLE.
    """
    result = encrypt_master_logic(plaintext, founder_passphrase)
    return result["ciphertext_hex"], result["public_hash"], True


def get_shield_status_summary(entries: list) -> dict:
    """
    Given a list of chronicle entry dicts, return an encryption shield status summary.

    Each entry dict should have an 'is_shielded' key (bool or 0/1).

    Returns:
      {
        "total": int,
        "open": int,
        "locked": int,
        "locked_pct": float,
        "void_seal_1": str,
        "void_seal_2": str,
      }
    """
    total = len(entries)
    locked = sum(1 for e in entries if e.get("is_shielded"))
    open_count = total - locked
    locked_pct = round(locked / total * 100, 1) if total else 0.0
    return {
        "total": total,
        "open": open_count,
        "locked": locked,
        "locked_pct": locked_pct,
        "void_seal_1": VOID_HEX_SEAL_1,
        "void_seal_2": VOID_HEX_SEAL_2,
    }


# ═══════════════════════════════════════════════════════════════════════════
# PART 2 — Social Resonance Monitor (Task #81)
# ═══════════════════════════════════════════════════════════════════════════

class SignalSample:
    __slots__ = ("value", "ts")

    def __init__(self, value: float):
        self.value = value
        self.ts = time.time()


class SocialResonanceShield:
    """
    Social resonance monitor that auto-pauses VoidEcho broadcasting when
    signal volatility exceeds the configured threshold.
    """

    def __init__(
        self,
        volatility_threshold: float = VOLATILITY_THRESHOLD,
        recovery_threshold: float = RECOVERY_THRESHOLD,
        window_size: int = WINDOW_SIZE,
    ):
        self._threshold = volatility_threshold
        self._recovery = recovery_threshold
        self._window: deque = deque(maxlen=window_size)
        self._lock = threading.RLock()
        self._broadcast_paused: bool = False
        self._status: str = "INITIALISING"
        self._activated_at: Optional[float] = None
        self._cleared_at: Optional[float] = None
        self._total_activations: int = 0
        self._last_volatility: float = 0.0

    def ingest(self, signal_value: float) -> None:
        """Feed a normalised [0, 1] signal reading into the rolling window."""
        with self._lock:
            self._window.append(SignalSample(signal_value))
            self._evaluate()

    def _evaluate(self) -> None:
        samples = list(self._window)
        if len(samples) < MIN_SAMPLES:
            self._status = "WARMING_UP"
            return

        values = [s.value for s in samples]
        mean = sum(values) / len(values)
        if mean < 1e-9:
            volatility = 0.0
        else:
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            volatility = math.sqrt(variance) / mean

        self._last_volatility = round(volatility, 4)

        if not self._broadcast_paused and volatility > self._threshold:
            self._broadcast_paused = True
            self._status = "GONE_DARK"
            self._activated_at = time.time()
            self._total_activations += 1
            logger.warning(
                "[LeadShield] Signal volatility %.4f > threshold %.4f — VoidEcho PAUSED",
                volatility, self._threshold,
            )
        elif self._broadcast_paused and volatility < self._recovery:
            self._broadcast_paused = False
            self._status = "CLEAR"
            self._cleared_at = time.time()
            logger.info(
                "[LeadShield] Volatility %.4f < recovery %.4f — VoidEcho RESUMED",
                volatility, self._recovery,
            )
        elif not self._broadcast_paused:
            self._status = "CLEAR"

    @property
    def broadcast_paused(self) -> bool:
        return self._broadcast_paused

    @property
    def status(self) -> str:
        return self._status

    @property
    def volatility(self) -> float:
        return self._last_volatility

    def get_status(self) -> Dict:
        with self._lock:
            return {
                "status": self._status,
                "broadcast_paused": self._broadcast_paused,
                "volatility": self._last_volatility,
                "volatility_threshold": self._threshold,
                "recovery_threshold": self._recovery,
                "window_samples": len(self._window),
                "total_activations": self._total_activations,
                "activated_at": self._activated_at,
                "cleared_at": self._cleared_at,
                "gone_dark": self._broadcast_paused,
            }

    def set_thresholds(self, volatility: float, recovery: float) -> Dict:
        """Update thresholds at runtime."""
        with self._lock:
            self._threshold = max(0.01, min(1.0, volatility))
            self._recovery = max(0.01, min(self._threshold, recovery))
            self._evaluate()
        return {
            "success": True,
            "volatility_threshold": self._threshold,
            "recovery_threshold": self._recovery,
        }

    def force_clear(self) -> Dict:
        """Manually clear the Gone Dark state (admin override)."""
        with self._lock:
            self._broadcast_paused = False
            self._status = "CLEAR"
            self._cleared_at = time.time()
            self._window.clear()
        return {"success": True, "status": "CLEAR"}


_shield_instance: Optional[SocialResonanceShield] = None
_shield_lock = threading.Lock()
_FEED_INTERVAL_S = 15.0
_last_feed_time: float = 0.0


def get_shield() -> SocialResonanceShield:
    global _shield_instance
    with _shield_lock:
        if _shield_instance is None:
            _shield_instance = SocialResonanceShield()
    return _shield_instance


def feed_shield_from_engine() -> None:
    """
    Pull internal signal metrics and feed them into the social resonance monitor.

    Called opportunistically — throttled to once every 15 seconds.
    Internal metrics used (no real social API):
      - Mycelium avg_signal_strength
      - Buffer Spore confidence
    """
    global _last_feed_time
    now = time.time()
    if now - _last_feed_time < _FEED_INTERVAL_S:
        return
    _last_feed_time = now

    shield = get_shield()
    try:
        from void_engine.mycelium_service import get_network_status
        status = get_network_status(run_steps=0)
        raw_signal = float(status.get("avg_signal_strength", 0.5))
        spore = status.get("buffer_spore", {})
        confidence = float(spore.get("confidence", 1.0))
        combined = (raw_signal * 0.6 + confidence * 0.4)
        shield.ingest(combined)
    except Exception as exc:
        logger.debug("[LeadShield] feed failed: %s", exc)


def get_shield_status() -> Dict:
    """Public convenience wrapper — feeds the shield then returns status."""
    feed_shield_from_engine()
    return get_shield().get_status()


def is_broadcast_paused() -> bool:
    """Return True when VoidEcho broadcasting should be suppressed."""
    return get_shield().broadcast_paused
