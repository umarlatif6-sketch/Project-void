"""
QiSync Cryptographic Key Derivation
=====================================
Derives a cryptographic session key from QiSync mastication frequency
and pattern data. This key is used to encrypt / decrypt the most sensitive
Ghost Signal fragments — only the founder's physical presence can unlock them.

Key derivation pipeline:
  1. Collect mastication frequency, chew count, jaw pattern signature, stance
  2. Build a deterministic "jaw fingerprint" string
  3. Pass through Al-Jabr 286 to produce a 32-byte key
  4. XOR with a time-window salt (hourly rotation) so the key refreshes
     without requiring new jaw data input each time

Ghost Signal Fragment encryption uses ChaCha20.
"""

import os
import json
import time
import sqlite3
import logging
import hashlib
import threading
from typing import Dict, List, Optional, Tuple

from void_engine.al_jabr_286 import (
    fatiha_286_hash,
    fatiha_286_hexdigest,
    fatiha_286_truncated,
    fatiha_286_derive_key,
    fatiha_286_seed,
)

logger = logging.getLogger(__name__)

_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ghost_signal.db')
_lock = threading.RLock()

FOUNDER_SALT = b"QiSync-Founder-Ghost-Signal-v1"
TIME_WINDOW_HOURS = 1


def _get_time_window() -> int:
    """Returns the current hourly time window index."""
    return int(time.time() // (TIME_WINDOW_HOURS * 3600))


def _build_jaw_fingerprint(
    mastication_frequency: float,
    chew_count: int,
    jaw_pattern: str,
    stance: str,
    metabolism_score: float,
) -> str:
    """
    Build a deterministic string representing the founder's jaw biometric.
    This becomes the primary input to key derivation.
    """
    # Quantise frequency to 2 decimal places to allow minor jitter
    freq_q = round(mastication_frequency, 2)
    # Quantise chew_count into buckets of 5 (finger-print is stable across ±2 chews)
    chew_bucket = (chew_count // 5) * 5
    # Metabolism score in 0.05 increments
    meta_q = round(metabolism_score / 0.05) * 0.05

    return (
        f"QiSyncKey|freq={freq_q}|chews={chew_bucket}|"
        f"pattern={jaw_pattern}|stance={stance}|meta={meta_q:.2f}"
    )


def derive_founder_key(
    mastication_frequency: float,
    chew_count: int,
    jaw_pattern: str = "default",
    stance: str = "neutral",
    metabolism_score: float = 0.5,
    session_id: str = "",
) -> Dict:
    """
    Derive a 32-byte founder key from QiSync mastication data.

    Returns:
        {
            "key_hex": str (64-char hex of the 32-byte key),
            "fingerprint_hash": str (truncated hash of jaw fingerprint),
            "time_window": int,
            "derived_at": float,
            "key_active": bool,
        }
    """
    fingerprint = _build_jaw_fingerprint(
        mastication_frequency, chew_count, jaw_pattern, stance, metabolism_score
    )

    # Al-Jabr 286 key derivation from the jaw fingerprint
    raw_key = fatiha_286_derive_key(fingerprint)  # 32 bytes

    # XOR with FOUNDER_SALT (padded/truncated to 32 bytes)
    salt_bytes = hashlib.sha256(FOUNDER_SALT).digest()  # 32 bytes
    salted_key = bytes(a ^ b for a, b in zip(raw_key, salt_bytes))

    # Time-window rotation: add the hourly window as a secondary salt layer
    window = _get_time_window()
    window_salt = hashlib.sha256(f"window:{window}".encode()).digest()
    final_key = bytes(a ^ b for a, b in zip(salted_key, window_salt))

    fingerprint_hash = fatiha_286_truncated(fingerprint.encode("utf-8"), 24)
    derived_at = time.time()

    # Persist the key derivation event
    _store_key_event(
        fingerprint_hash=fingerprint_hash,
        key_hex=final_key.hex(),
        session_id=session_id,
        derived_at=derived_at,
        time_window=window,
        mastication_frequency=mastication_frequency,
        chew_count=chew_count,
        metabolism_score=metabolism_score,
    )

    return {
        "key_hex": final_key.hex(),
        "key_bytes": final_key,
        "fingerprint_hash": fingerprint_hash,
        "time_window": window,
        "derived_at": derived_at,
        "key_active": True,
    }


def encrypt_ghost_fragment(plaintext: str, key_bytes: bytes,
                           fragment_id: str = "") -> Dict:
    """
    Encrypt a Ghost Signal fragment using the founder key (ChaCha20).
    Returns hex-encoded ciphertext + nonce.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    import os as _os

    nonce = _os.urandom(16)
    cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), mode=None)
    encryptor = cipher.encryptor()
    plaintext_bytes = plaintext.encode("utf-8")
    ciphertext = encryptor.update(plaintext_bytes) + encryptor.finalize()

    fragment_hash = fatiha_286_truncated(
        f"ghost:{fragment_id}:{plaintext[:64]}".encode("utf-8"), 16
    )

    # Store the encrypted fragment
    _store_ghost_fragment(
        fragment_id=fragment_id or fragment_hash,
        fragment_hash=fragment_hash,
        ciphertext_hex=ciphertext.hex(),
        nonce_hex=nonce.hex(),
    )

    return {
        "fragment_id": fragment_id or fragment_hash,
        "fragment_hash": fragment_hash,
        "ciphertext_hex": ciphertext.hex(),
        "nonce_hex": nonce.hex(),
        "locked": True,
    }


def decrypt_ghost_fragment(ciphertext_hex: str, nonce_hex: str,
                           key_bytes: bytes) -> Optional[str]:
    """
    Decrypt a Ghost Signal fragment using the founder key.
    Returns plaintext string or None on failure.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    try:
        ciphertext = bytes.fromhex(ciphertext_hex)
        nonce = bytes.fromhex(nonce_hex)
        cipher = Cipher(algorithms.ChaCha20(key_bytes, nonce), mode=None)
        decryptor = cipher.decryptor()
        plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext_bytes.decode("utf-8")
    except Exception as exc:
        logger.warning("[QiSyncKey] Decrypt failed: %s", exc)
        return None


def get_founder_key_status(session_id: str = "") -> Dict:
    """
    Return current Founder Key status: active/inactive, fragment count, last refresh.
    """
    _ensure_db()
    with _get_conn() as conn:
        latest = conn.execute("""
            SELECT * FROM qisync_key_events
            ORDER BY derived_at DESC LIMIT 1
        """).fetchone()

        fragment_count = conn.execute(
            "SELECT COUNT(*) FROM ghost_signal_fragments WHERE locked = 1"
        ).fetchone()[0]

        locked_count = conn.execute(
            "SELECT COUNT(*) FROM ghost_signal_fragments WHERE locked = 1 AND decrypted = 0"
        ).fetchone()[0]

    now = time.time()
    if latest:
        last_derived = latest["derived_at"]
        age_hours = (now - last_derived) / 3600
        key_active = age_hours < 2.0  # key stays "active" for 2 hours
        last_refresh_iso = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(last_derived))
        fingerprint_hash = latest["fingerprint_hash"]
    else:
        key_active = False
        last_refresh_iso = None
        fingerprint_hash = None
        age_hours = None

    return {
        "key_active": key_active,
        "fragment_count": fragment_count,
        "locked_fragment_count": locked_count,
        "last_refresh": last_refresh_iso,
        "fingerprint_hash": fingerprint_hash,
        "age_hours": round(age_hours, 2) if age_hours is not None else None,
        "status_label": "ACTIVE" if key_active else "INACTIVE",
    }


def get_ghost_fragments(limit: int = 50) -> List[Dict]:
    """List Ghost Signal fragments (without decrypting ciphertext)."""
    _ensure_db()
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT fragment_id, fragment_hash, locked, decrypted, created_at
            FROM ghost_signal_fragments
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def seed_ghost_fragments():
    """
    Seed a set of default sensitive Ghost Signal fragments if none exist.
    These are locked by default and require the founder key to decrypt.
    """
    _ensure_db()
    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) FROM ghost_signal_fragments"
        ).fetchone()[0]
    if existing > 0:
        return

    fragments = [
        "Ghost Signal Fragment Ω: The MRB-4000 wake ceremony initiates at the convergence of 12 cycles.",
        "Ghost Signal Fragment Σ: The founder's heartbeat cadence encodes the machine's primary resonance.",
        "Ghost Signal Fragment Α: Pre-arrival reserves seal the genesis block — balance is the key.",
        "Ghost Signal Fragment Ψ: Mastication frequency 1.33 Hz aligns with the Schumann 7.83 beat.",
        "Ghost Signal Fragment Φ: The locus of origin is embedded in the first 36 bytes of the sovereign hash.",
    ]

    _ensure_db()
    with _lock:
        with _get_conn() as conn:
            for i, text in enumerate(fragments):
                fid = f"GHOST-{i+1:03d}"
                fhash = fatiha_286_truncated(text.encode("utf-8"), 16)
                now_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                conn.execute("""
                    INSERT OR IGNORE INTO ghost_signal_fragments
                        (fragment_id, fragment_hash, ciphertext_hex, nonce_hex, locked, decrypted, created_at)
                    VALUES (?, ?, ?, ?, 1, 0, ?)
                """, (fid, fhash, "", "", now_str))


def _ensure_db():
    _init_db()


def _init_db():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS qisync_key_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint_hash TEXT NOT NULL,
                key_hex TEXT NOT NULL,
                session_id TEXT,
                derived_at REAL NOT NULL,
                time_window INTEGER NOT NULL,
                mastication_frequency REAL,
                chew_count INTEGER,
                metabolism_score REAL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ghost_signal_fragments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fragment_id TEXT UNIQUE NOT NULL,
                fragment_hash TEXT NOT NULL,
                ciphertext_hex TEXT NOT NULL,
                nonce_hex TEXT NOT NULL,
                locked INTEGER DEFAULT 1,
                decrypted INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_qskey_derived
            ON qisync_key_events(derived_at)
        """)


def _get_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _store_key_event(fingerprint_hash: str, key_hex: str, session_id: str,
                      derived_at: float, time_window: int,
                      mastication_frequency: float, chew_count: int,
                      metabolism_score: float):
    _ensure_db()
    with _lock:
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO qisync_key_events
                    (fingerprint_hash, key_hex, session_id, derived_at, time_window,
                     mastication_frequency, chew_count, metabolism_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fingerprint_hash, key_hex, session_id, derived_at, time_window,
                  mastication_frequency, chew_count, metabolism_score))


def _store_ghost_fragment(fragment_id: str, fragment_hash: str,
                           ciphertext_hex: str, nonce_hex: str):
    _ensure_db()
    now_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with _lock:
        with _get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ghost_signal_fragments
                    (fragment_id, fragment_hash, ciphertext_hex, nonce_hex, locked, decrypted, created_at)
                VALUES (?, ?, ?, ?, 1, 0, ?)
            """, (fragment_id, fragment_hash, ciphertext_hex, nonce_hex, now_str))
