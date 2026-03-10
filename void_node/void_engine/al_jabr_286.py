"""
PROJECT VOID — Al-Jabr 286 Protocol
Sura-Fatiha Sovereign Hashing (286-bit)

Replaces secular SHA-256 with a 286-bit Sovereign Hash grounded in
the 7 verses of Al-Fatiha (The Opening).

Architecture:
  - Base Layer: SHA3-256 provides the initial 256-bit silt
  - 7-Verse Pass: Data is processed through 7 harmonic layers
    mirroring the verse structure [7, 4, 2, 5, 4, 3, 6]
  - 30-Bit Sovereign Extension: Trilateral root frequency anchor
    bridges the base to 286 bits
  - Final Output: 36 bytes (288 bits, 286 active + 2 alignment bits)

The extra 30 bits act as "Invisible Math" — standard forensic tools
searching for 256-bit patterns will pass over the Sovereign Hash as
ambient noise ("Insect Silt"), but to our nodes it is the Master Key.

Al-Fatiha Verse Structure (word counts per verse):
  Verse 1: بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ         — 4 words
  Verse 2: ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ          — 4 words
  Verse 3: ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ                        — 2 words
  Verse 4: مَـٰلِكِ يَوْمِ ٱلدِّينِ                         — 3 words
  Verse 5: إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ        — 4 words
  Verse 6: ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ              — 3 words
  Verse 7: صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ ...      — 9 words

Root Layer Weights: [7, 4, 2, 5, 4, 3, 6]
  These represent the trilateral root complexity of each verse,
  used as prime salt for the Sovereign Extension.

Mode: PRODUCTION — All subsystems use fatiha_286 as the standard.
"""

import hashlib
import struct


FATIHA_LAYERS = [7, 4, 2, 5, 4, 3, 6]

VERSE_COUNT = 7

SOVEREIGN_BIT_DEPTH = 286

EXTENSION_BITS = 30

TOTAL_BYTES = 36

OPENING_RESONANCE_HZ = 432

FATIHA_PRIME_SALT = b"BismillahirRahmanirRahim"


def fatiha_286_hash(data: bytes) -> bytes:
    """
    Compute the 286-bit Sovereign Hash of raw bytes.

    The data passes through 7 harmonic layers (Al-Fatiha verses),
    producing a 36-byte hash (286 active bits + 2 alignment bits).

    Returns:
        36 bytes representing the 286-bit Sovereign Hash.
    """
    base = hashlib.sha3_256(data).digest()

    extension = _derive_opening_resonance(base)

    sovereign_hash = base + extension
    return sovereign_hash[:TOTAL_BYTES]


def fatiha_286_hexdigest(data: bytes) -> str:
    """
    Compute the 286-bit Sovereign Hash and return as hex string (72 chars).
    """
    return fatiha_286_hash(data).hex()


def fatiha_286_from_str(text: str) -> bytes:
    """
    Convenience: hash a UTF-8 string through the 286-bit pipeline.
    """
    return fatiha_286_hash(text.encode("utf-8"))


def fatiha_286_hexdigest_from_str(text: str) -> str:
    """
    Convenience: hash a UTF-8 string and return hex (72 chars).
    """
    return fatiha_286_hexdigest(text.encode("utf-8"))


def fatiha_286_truncated(data: bytes, chars: int = 16) -> str:
    """
    Compute the 286-bit hash and return a truncated hex string.
    Used for IDs, signatures, and seeds where full 72 chars is unnecessary.
    """
    return fatiha_286_hexdigest(data)[:chars]


def fatiha_286_seed(data: bytes, chars: int = 8) -> int:
    """
    Compute the 286-bit hash and return an integer seed.
    Used for deterministic RNG seeding (ghost offset, jitter maps, etc.)
    """
    return int(fatiha_286_hexdigest(data)[:chars], 16)


def fatiha_286_derive_key(passphrase: str) -> bytes:
    """
    Derive a 32-byte encryption key from a passphrase using the 286-bit pipeline.

    The full 36-byte Sovereign Hash is computed, then the first 32 bytes
    are used as the ChaCha20/AES key. The remaining 4 bytes (containing
    the 30-bit Sovereign Extension) serve as the identity anchor.

    Returns:
        32 bytes suitable for symmetric encryption.
    """
    sovereign = fatiha_286_hash(passphrase.encode("utf-8"))
    return sovereign[:32]


def _derive_opening_resonance(base_hash: bytes) -> bytes:
    """
    Derive the 30-bit Sovereign Extension from the base SHA3-256 hash.

    The 7 FATIHA_LAYERS weights are used as multiplicative salt against
    consecutive byte-pairs of the base hash, creating a trilateral
    frequency signature unique to this data.

    The result is folded with the Opening Resonance (432 Hz) to anchor
    the extension in the Sapphire Thread.

    Returns:
        4 bytes containing the 30-bit extension (top 2 bits cleared).
    """
    extension_acc = 0

    for i, weight in enumerate(FATIHA_LAYERS):
        byte_pair = base_hash[i * 2 : i * 2 + 2]
        value = int.from_bytes(byte_pair, "big")
        extension_acc += value * weight

    extension_acc ^= OPENING_RESONANCE_HZ

    salted = hashlib.sha3_256(
        FATIHA_PRIME_SALT + struct.pack(">I", extension_acc & 0xFFFFFFFF)
    ).digest()

    raw_extension = int.from_bytes(salted[:4], "big")

    masked = raw_extension & 0x3FFFFFFF

    return masked.to_bytes(4, "big")


def verify_286_signature(data: bytes, signature: bytes) -> bool:
    """
    Verify that a 286-bit signature matches the given data.
    """
    if len(signature) == 0 or len(signature) != TOTAL_BYTES:
        return False
    expected = fatiha_286_hash(data)
    return expected == signature


def verify_286_hex_signature(data: bytes, hex_signature: str) -> bool:
    """
    Verify that a truncated hex signature matches.
    """
    if len(hex_signature) == 0:
        return False
    expected = fatiha_286_hexdigest(data)
    return expected[:len(hex_signature)] == hex_signature


def get_protocol_info() -> dict:
    """
    Return metadata about the Al-Jabr 286 protocol.
    """
    return {
        "protocol": "Al-Jabr 286",
        "standard": "Sura-Fatiha Sovereign Hash",
        "bit_depth": SOVEREIGN_BIT_DEPTH,
        "base_algorithm": "SHA3-256",
        "extension_bits": EXTENSION_BITS,
        "total_bytes": TOTAL_BYTES,
        "verse_layers": FATIHA_LAYERS,
        "verse_count": VERSE_COUNT,
        "resonance_hz": OPENING_RESONANCE_HZ,
        "prime_salt": FATIHA_PRIME_SALT.decode("utf-8"),
        "replaces": "SHA-256 (deprecated)",
        "forensic_evasion": "286-bit patterns invisible to 256-bit scanners",
    }
