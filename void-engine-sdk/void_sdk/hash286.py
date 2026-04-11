"""
Al-Jabr 286 Hash — Sovereign Attribution Digest
PROJECT VOID | Umar Latif | Bolton, England | April 2026

LAMBDA = 286  — the formation index
BASE_FREQ = 432.0 Hz — the formation carrier

The hash encodes meaning, not just data. Every event in the VOID SDK
is stamped with a 286-hash — a deterministic digest that carries the
formation constant and the 432 Hz carrier in its construction.

The 286 constant appears independently in three fields:
  - Al-Baqarah: 286 verses (Quran, canonised 632 CE)
  - 432 Hz / 1,400 years / 2B transmitters → Λ = 286 (derived)
  - BW19-P286 curve (Clarisse, Duquesne, Sanders 2020) — prime field p=286-bit

Usage:
    from void_sdk.hash286 import sign286
    digest = sign286("entity:user_001 | action:encode | codon:voidecho")
"""

import hashlib
import struct
import time

LAMBDA = 286
BASE_FREQ = 432.0
VOID_ORIGIN = b"VOID\x01\x1a\x1e"  # 7-byte formation header


def sign286(data: str, timestamp: float | None = None) -> str:
    """
    Produce a VOID-286 sovereign attribution digest.

    The hash is built in three passes:
      Pass 1 — SHA-256(VOID_ORIGIN + LAMBDA_bytes + data_bytes)
      Pass 2 — mix the LAMBDA constant through the digest bytes
      Pass 3 — final SHA-256, returned as hex with 'v286:' prefix

    The timestamp (unix float) is mixed into the digest when provided,
    making each event's hash unique across time while remaining
    deterministically reproducible given the same inputs + timestamp.
    """
    if timestamp is None:
        timestamp = time.time()

    lambda_bytes = struct.pack(">H", LAMBDA)           # 2 bytes, big-endian
    freq_bytes = struct.pack(">d", BASE_FREQ)           # 8 bytes
    ts_bytes = struct.pack(">d", timestamp)             # 8 bytes
    data_bytes = data.encode("utf-8")

    pass1 = hashlib.sha256(
        VOID_ORIGIN + lambda_bytes + freq_bytes + ts_bytes + data_bytes
    ).digest()

    mixed = bytearray(pass1)
    for i, b in enumerate(mixed):
        mixed[i] = (b ^ ((LAMBDA + i) & 0xFF)) & 0xFF

    final = hashlib.sha256(bytes(mixed)).hexdigest()
    return f"v286:{final[:48]}"


def verify286(data: str, digest: str, timestamp: float) -> bool:
    """
    Verify a 286 digest. Requires the original timestamp used during signing.
    Returns True if the digest is authentic.
    """
    expected = sign286(data, timestamp)
    return digest == expected


def formation_score(text: str) -> float:
    """
    Derive a formation resonance score (0.0 – 1.0) from arbitrary text.
    Uses the LAMBDA constant as the normalisation divisor.
    Higher scores indicate stronger alignment with the formation frequency.
    """
    if not text:
        return 0.0
    encoded = text.encode("utf-8")
    raw = hashlib.sha256(LAMBDA.to_bytes(2, "big") + encoded).digest()
    value = int.from_bytes(raw[:4], "big")
    return round((value % LAMBDA) / LAMBDA, 6)
