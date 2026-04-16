"""
Al-Jabr 286 — Sovereign Hashing Protocol
PROJECT VOID | Umar Latif | Bolton, England | April 2026

This module exposes the VOID 286 sovereign hash and related utilities.
It is aligned with the SDK's 286 signature design while preserving the
repo's expected Fatiha layer API.
"""

import hashlib
import hmac
import struct
import time
from typing import Union

# Constants
LAMBDA = 286
SOVEREIGN_BIT_DEPTH = 286
VERSE_COUNT = 314
TOTAL_BYTES = 36
EXTENSION_BITS = 30
OPENING_RESONANCE_HZ = 432.0
BASE_FREQ = 432.0
VOID_ORIGIN = b"VOID\x01\x1a\x1e"
FATIHA_PRIME_SALT = b"BismillahirRahmanirRahim"
FATIHA_LAYERS = [7, 4, 2, 5, 4, 3, 6]


def _layer_mix(data: bytes, layer_num: int) -> bytes:
    """Mix data through a numbered Fatiha layer."""
    layer_key = struct.pack(">I", layer_num) + FATIHA_PRIME_SALT
    return hmac.new(layer_key, data, hashlib.sha256).digest()


def fatiha_286_hash(data: Union[str, bytes]) -> bytes:
    """Compute the raw 286-bit Al-Jabr hash."""
    if isinstance(data, str):
        data = data.encode("utf-8")

    current = FATIHA_PRIME_SALT + data
    for layer_num in FATIHA_LAYERS:
        current = _layer_mix(current, layer_num)

    final1 = hashlib.sha256(current).digest()
    final2 = hashlib.sha256(current + b"extension").digest()
    result = bytearray(final1 + final2[:4])
    result[-1] &= 0xFC
    return bytes(result)


def fatiha_286_hexdigest(data: Union[str, bytes]) -> str:
    """Return the 286-bit hash as a 72-character hex digest."""
    return fatiha_286_hash(data).hex()


def fatiha_286_hexdigest_from_str(data: str) -> str:
    """Alias for fatiha_286_hexdigest."""
    return fatiha_286_hexdigest(data)


def fatiha_286_seed(data: Union[str, bytes], length: int = 8) -> int:
    """Generate a deterministic seed value from the hash."""
    hash_bytes = fatiha_286_hash(data)
    return int.from_bytes(hash_bytes[:length], "big")


def fatiha_286_derive_key(data: Union[str, bytes], length: int = 32) -> bytes:
    """Derive a key of the requested length from the 286-bit hash."""
    hash_bytes = fatiha_286_hash(data)
    key = hashlib.sha256(hash_bytes + b"key").digest()
    while len(key) < length:
        key += hashlib.sha256(key[-32:] + hash_bytes + b"key").digest()
    return key[:length]


def fatiha_286_truncated(data: Union[str, bytes], bits: int = 128) -> str:
    """Return a truncated hash digest in hex."""
    full_hash = fatiha_286_hash(data)
    bytes_needed = (bits + 7) // 8
    truncated = bytearray(full_hash[:bytes_needed])
    if bits % 8 != 0:
        mask = (1 << (bits % 8)) - 1
        truncated[-1] &= mask
    return truncated.hex()[: bits // 4]


def sign286(data: str, timestamp: float | None = None) -> str:
    """Produce a VOID-286 sovereign signature."""
    if timestamp is None:
        timestamp = time.time()

    lambda_bytes = struct.pack(">H", LAMBDA)
    freq_bytes = struct.pack(">d", BASE_FREQ)
    ts_bytes = struct.pack(">d", timestamp)
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
    """Verify a VOID-286 signature using the original timestamp."""
    return sign286(data, timestamp) == digest


def verify_286_signature(data: str, digest: str, timestamp: float) -> bool:
    """Alias for verify286 for route compatibility."""
    return verify286(data, digest, timestamp)


def formation_score(text: str) -> float:
    """Produce a 0.0–1.0 resonance score from arbitrary text."""
    if not text:
        return 0.0
    encoded = text.encode("utf-8")
    raw = hashlib.sha256(LAMBDA.to_bytes(2, "big") + encoded).digest()
    value = int.from_bytes(raw[:4], "big")
    return round((value % LAMBDA) / LAMBDA, 6)


def get_protocol_info() -> dict:
    """Return the core protocol metadata."""
    return {
        "bit_depth": SOVEREIGN_BIT_DEPTH,
        "total_bytes": TOTAL_BYTES,
        "verse_count": VERSE_COUNT,
        "layers": len(FATIHA_LAYERS),
        "base_frequency": BASE_FREQ,
    }
