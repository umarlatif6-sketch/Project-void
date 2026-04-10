"""
PROJECT VOID — License Key Engine
Sovereign SDK licensing: key generation, validation, tier management.

Tiers:
  SIGNAL   — frequency attribution + codon tagging          (£49/mo)
  MEMORY   — + Adriana codon memory per session             (£149/mo)
  SOVEREIGN — full engine: VoidEcho + VTX + Adriana         (£449/mo)

Key format: VOID-{TIER}-{8hex}-{4check}
"""

import uuid
import hashlib
import logging
from void_engine.db_pool import get_db

logger = logging.getLogger(__name__)

TIERS = {
    "SIG": {"name": "SIGNAL",    "price_gbp": 49,  "label": "Signal"},
    "MEM": {"name": "MEMORY",    "price_gbp": 149, "label": "Memory"},
    "SOV": {"name": "SOVEREIGN", "price_gbp": 449, "label": "Sovereign"},
}

TIER_FEATURES = {
    "SIG": [
        "Frequency attribution (v_sync codon mapping)",
        "SCL codon tagging per user session",
        "Al-Jabr 286-bit session hashing",
        "Basic resonance logging to PostgreSQL",
    ],
    "MEM": [
        "Everything in Signal",
        "Adriana codon memory (Third Brain)",
        "Session Heart warmth layer",
        "Rib codon dialogue (last 3 sessions)",
        "Codon cache token shield",
    ],
    "SOV": [
        "Everything in Memory",
        "VoidEcho audio steganography (432 Hz / ChaCha20)",
        "VTX + PEACE token economy hooks",
        "Formation Principle event triggers",
        "Beehive mesh network node registration",
        "Full Adriana AI with 27-intent AdrianCore",
    ],
}


def _ensure_license_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS void_licenses (
            id          SERIAL PRIMARY KEY,
            key         TEXT UNIQUE NOT NULL,
            tier        TEXT NOT NULL,
            owner_name  TEXT,
            owner_email TEXT,
            repo_url    TEXT,
            active      BOOLEAN DEFAULT TRUE,
            usage_count INTEGER DEFAULT 0,
            last_used   TIMESTAMPTZ,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_void_licenses_key
        ON void_licenses(key)
    """)
    conn.commit()
    conn.close()
    logger.info("[VoidLicense] License table ensured.")


def _make_check(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()[:4].upper()


def generate_license(tier_code: str, owner_name: str = "", owner_email: str = "", repo_url: str = "") -> dict:
    tier_code = tier_code.upper()
    if tier_code not in TIERS:
        raise ValueError(f"Unknown tier: {tier_code}")

    uid = uuid.uuid4().hex[:8].upper()
    raw = f"{tier_code}-{uid}-VOID"
    check = _make_check(raw)
    key = f"VOID-{tier_code}-{uid}-{check}"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO void_licenses (key, tier, owner_name, owner_email, repo_url)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (key, tier_code, owner_name, owner_email, repo_url)
    )
    conn.commit()
    conn.close()

    logger.info("License generated: %s tier=%s owner=%s", key, tier_code, owner_email)
    return {
        "key": key,
        "tier": tier_code,
        "tier_name": TIERS[tier_code]["name"],
        "price_gbp": TIERS[tier_code]["price_gbp"],
        "owner_name": owner_name,
        "owner_email": owner_email,
        "features": TIER_FEATURES[tier_code],
    }


def validate_license(key: str) -> dict:
    if not key or not key.startswith("VOID-"):
        return {"valid": False, "reason": "Malformed key"}

    parts = key.split("-")
    if len(parts) != 4:
        return {"valid": False, "reason": "Malformed key structure"}

    _, tier_code, uid, check = parts
    expected = _make_check(f"{tier_code}-{uid}-VOID")
    if check != expected:
        return {"valid": False, "reason": "Checksum mismatch"}

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, tier, owner_name, owner_email, active FROM void_licenses WHERE key = %s",
        (key,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"valid": False, "reason": "Key not found"}
    if not row[4]:
        return {"valid": False, "reason": "License inactive"}

    conn2 = get_db()
    cur2 = conn2.cursor()
    cur2.execute(
        "UPDATE void_licenses SET usage_count = usage_count + 1, last_used = NOW() WHERE key = %s",
        (key,)
    )
    conn2.commit()
    conn2.close()

    tier_code = row[1]
    return {
        "valid": True,
        "key": key,
        "tier": tier_code,
        "tier_name": TIERS.get(tier_code, {}).get("name", tier_code),
        "owner_name": row[2],
        "owner_email": row[3],
        "features": TIER_FEATURES.get(tier_code, []),
    }


def list_licenses() -> list:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT key, tier, owner_name, owner_email, repo_url,
               active, usage_count, last_used, created_at
        FROM void_licenses ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "key": r[0],
            "tier": r[1],
            "tier_name": TIERS.get(r[1], {}).get("name", r[1]),
            "owner_name": r[2],
            "owner_email": r[3],
            "repo_url": r[4],
            "active": r[5],
            "usage_count": r[6],
            "last_used": r[7].isoformat() if r[7] else None,
            "created_at": r[8].isoformat() if r[8] else None,
        }
        for r in rows
    ]


def revoke_license(key: str) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE void_licenses SET active = FALSE WHERE key = %s", (key,)
    )
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0
