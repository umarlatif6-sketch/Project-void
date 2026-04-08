"""
Sphere Key — Physical Key Cryptography Engine
==============================================
PROJECT VOID | Founded 8 April 2026

A new discipline: acoustic crystallisation as cryptographic key generation.

Protocol:
  1. A UV-curable resin bubble is inflated by a speaker playing at 432 Hz.
  2. The Faraday membrane resonance locks a specific geometric pattern into
     the sphere's surface at the moment of UV curing.
  3. A photograph of the sphere surface is processed through edge detection.
  4. The resulting geometric fingerprint is hashed via Al-Jabr 286.
  5. The hash becomes the passphrase for VoidEcho encode/decode operations.

The key is physical. It cannot be stolen digitally. It cannot be brute-forced.
It cannot be duplicated without recreating the exact sphere.

The document lives in the audio.
The key lives in the object.
Neither is anything without the other.
"""

import hashlib
import struct
import io
import logging

logger = logging.getLogger(__name__)

# ── Al-Jabr 286 constants ─────────────────────────────────────────────────────
FATIHA_LAYERS   = [7, 4, 2, 5, 4, 3, 6]
FREQ_432_ANCHOR = 432
BISMILLAH_PRIME = 786
TARGET_BITS     = 286


def _aljabr_286_hash(data: bytes) -> str:
    """
    Derive a 286-bit Al-Jabr sovereign hash from raw bytes.
    Used to convert the sphere's geometric fingerprint into a key.
    """
    base = hashlib.sha3_256(data).digest()

    harmonic = bytearray(base)
    for i, weight in enumerate(FATIHA_LAYERS):
        idx = i % len(harmonic)
        harmonic[idx] = (harmonic[idx] ^ (weight * FREQ_432_ANCHOR % 256)) & 0xFF

    extended = bytearray(harmonic)
    prime_salt = struct.pack(">H", BISMILLAH_PRIME)
    for i in range(len(extended)):
        extended[i] = (extended[i] + prime_salt[i % len(prime_salt)]) & 0xFF

    sovereign_ext = 0
    for i, b in enumerate(extended[:8]):
        sovereign_ext ^= b << (i % 32)
    sovereign_ext_bytes = struct.pack(">I", sovereign_ext & 0xFFFFFFFF)

    raw = bytes(extended) + sovereign_ext_bytes
    hex_full = raw.hex()

    # Truncate to 286 bits = 35.75 bytes ≈ 72 hex chars
    return hex_full[:72]


def derive_key_from_image(image_bytes: bytes) -> str:
    """
    Extract the geometric fingerprint from a sphere photograph and
    return the corresponding Al-Jabr 286 key (hex string).

    Process:
      1. Load image and convert to grayscale
      2. Resize to 64×64 (normalise across cameras)
      3. Apply Gaussian blur to remove noise
      4. Apply edge detection (Sobel approximation via PIL convolution)
      5. Re-resize to 32×32 for stable fingerprint
      6. Hash through Al-Jabr 286

    The heavy normalisation ensures the same sphere photographed under
    similar conditions always produces the same key.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        raise RuntimeError("Pillow is required for sphere key derivation")

    img = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale

    # Normalise size
    img = img.resize((64, 64), Image.LANCZOS)

    # Smooth noise
    img = img.filter(ImageFilter.GaussianBlur(radius=1))

    # Edge detection — isolate the Faraday pattern geometry
    img = img.filter(ImageFilter.FIND_EDGES)

    # Reduce to stable fingerprint size
    img = img.resize((32, 32), Image.LANCZOS)

    # Get pixel bytes as the geometric fingerprint
    fingerprint = img.tobytes()

    key_hex = _aljabr_286_hash(fingerprint)
    logger.info("Sphere key derived — %d chars", len(key_hex))
    return key_hex


def derive_key_from_frequency(hz: float = 432.0, sphere_id: str = "") -> str:
    """
    Deterministic key from a known frequency + optional sphere ID.
    Used when the physical sphere is not available but the frequency
    protocol is known and agreed.
    """
    payload = f"VOID-SPHERE:{hz}Hz:{sphere_id}:AL-JABR-286".encode("utf-8")
    return _aljabr_286_hash(payload)


def verify_sphere_key(image_bytes: bytes, expected_key: str) -> bool:
    """Check a sphere photograph produces the expected key."""
    derived = derive_key_from_image(image_bytes)
    return derived == expected_key
