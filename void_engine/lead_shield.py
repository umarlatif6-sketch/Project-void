"""
Lead Shield — Al-Jabr 286 Master Logic Encryption Layer

The Lead Shield wraps the Seed-to-Hex pipeline with a second encryption pass
on "Master Logic" fields (the Why and How of the 286 Al-Jabr units) so the
outside world sees only results, never the mechanics.

Architecture:
  - Derives a 32-byte encryption key from the founder's QiSync salt using
    the Al-Jabr 286 Sovereign Hash pipeline.
  - Encrypts plaintext Master Logic fields with ChaCha20 (nonce-prefixed).
  - Stores only ciphertext + is_shielded = 1 flag in the Chronicle.
  - A founder-key holder can decrypt; the public sees only the Al-Jabr hash.

HEX_DIGEST markers locked into VOID_CHRONICLE:
  0x4F62667573636174696F6E5F536869656C64   (Obfuscation_Shield)
  0x31385F536F6369616C5F5363617273         (18_Social_Scars)
"""

import os
import secrets
from void_engine.al_jabr_286 import fatiha_286_derive_key, fatiha_286_hexdigest_from_str

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
except ImportError:
    raise ImportError("cryptography package is required for Lead Shield")

SHIELD_NONCE_BYTES = 16
VOID_HEX_SEAL_1 = "4F62667573636174696F6E5F536869656C64"
VOID_HEX_SEAL_2 = "31385F536F6369616C5F5363617273"

_DEFAULT_QISYNC_SALT = os.environ.get(
    "LEAD_SHIELD_FOUNDER_KEY",
    "QiSync-Founder-Salt-VOID-286-Sovereign"
)


def _derive_shield_key(passphrase: str = None) -> bytes:
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


def shield_chronicle_field(plaintext: str, founder_passphrase: str = None) -> tuple[str, str, bool]:
    """
    Shield a chronicle entry field for Lead Shield storage.

    Returns (ciphertext_hex, public_hash, is_shielded=True).
    Used when writing shielded entries to the VOID_CHRONICLE.
    """
    result = encrypt_master_logic(plaintext, founder_passphrase)
    return result["ciphertext_hex"], result["public_hash"], True


def get_shield_status_summary(entries: list) -> dict:
    """
    Given a list of chronicle entry dicts, return a shield status summary.

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
