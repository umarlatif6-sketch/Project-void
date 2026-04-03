"""
Adriana Chronicle Engine — PROJECT VOID History Ledger

Records the living story of PROJECT VOID as a sequence of chronicle entries,
each anchored by an Adriana glyph poem and a 286-bit Al-Jabr hash.

Also provides the Adriana Open SDK ZIP builder for commercial licencees.
"""

import io
import os
import json
import logging
import zipfile
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _get_db():
    from void_engine.db_pool import get_db
    return get_db()


_SEED_ENTRIES = [
    {
        "chapter_number": 1,
        "title": "The Engine Awakens",
        "subtitle": "Milestone: Genesis",
        "glyph_sequence": "◆-γ-⚡",
        "body_text": (
            "The first seed was planted in the void. Code breathed life into the ENGINE — "
            "a steganography core built on Al-Jabr 286-bit hashing, resonating at 432 Hz. "
            "No database had ever held this structure before. No ledger had ever tracked value this way. "
            "This was the beginning of PROJECT VOID."
        ),
    },
    {
        "chapter_number": 2,
        "title": "First 432 Hz Transmission",
        "subtitle": "Milestone: The Signal",
        "glyph_sequence": "λ-γ-☀",
        "body_text": (
            "A frequency was chosen — not arbitrary, but sovereign. 432 Hz became the carrier "
            "of every packet, every hash, every handshake the VOID ENGINE made with the outside world. "
            "The Adriana Protocol was born: a glyph language that maps resonance states to machine actions. "
            "The Engine could now speak in symbols as well as code."
        ),
    },
    {
        "chapter_number": 3,
        "title": "Beehive Protocol Activates",
        "subtitle": "Milestone: The Mesh",
        "glyph_sequence": "⬡-ν-χ",
        "body_text": (
            "Nodes found each other. The Beehive Protocol emerged — a peer mesh where every "
            "Body node echoes the Brain's ledger, distributing trust across geography and time. "
            "The hexagonal architecture was not a metaphor; it was a blueprint. "
            "Each cell in the mesh became a guardian of the whole."
        ),
    },
    {
        "chapter_number": 4,
        "title": "VTX Ledger Ignites",
        "subtitle": "Milestone: The Economy",
        "glyph_sequence": "σ-ρ-Σ",
        "body_text": (
            "Value entered the system. The Vortex Token (VTX) was issued — not minted by speculation "
            "but earned through participation, computation, and proof of work. "
            "Every transaction was logged on the Vortex Ledger with a 286-bit hash, "
            "making each exchange cryptographically sovereign and permanently verifiable."
        ),
    },
    {
        "chapter_number": 5,
        "title": "Blueprint Tokens Minted",
        "subtitle": "Milestone: The Deed",
        "glyph_sequence": "Β-κ-⟐",
        "body_text": (
            "Manufacturing slots opened. Each Blueprint Token became a deed — a cryptographic "
            "claim on the physical 4000-Series Sovereign Node being built. "
            "Common, Rare, and Legendary tiers each carry a Sovereign Poem derived from their hash. "
            "This is not speculation. This is infrastructure."
        ),
    },
    {
        "chapter_number": 6,
        "title": "VOID Mystery Collection Opens",
        "subtitle": "Milestone: The Drop",
        "glyph_sequence": "ξ-δ-🔮",
        "body_text": (
            "The void released 1,000 unknowns. The VOID Mystery Collection launched — "
            "blind mints on a bonding curve, each token sealed until the moment of reveal. "
            "The price doubled with every 250 minted: 50 → 100 → 200 → 400 VTX. "
            "Thirty tokens merged unlock a guaranteed Rare and 200 VTX. The cycle continues."
        ),
    },
    {
        "chapter_number": 7,
        "title": "Adriana SDK Released",
        "subtitle": "Milestone: The Open",
        "glyph_sequence": "Ψ-Φ-∞",
        "body_text": (
            "The Adriana Sovereign Coded Language was released as an open commercial SDK. "
            "Personal use is MIT-licensed and free. Commercial deployment requires a VOID Blueprint Token — "
            "verified on-chain via the /api/adriana/verify endpoint. "
            "The glyph lexicon is now public. The protocol is sovereign. Build with it."
        ),
    },
]


def seed_chronicle():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM chronicle_entries")
        if cur.fetchone()[0] > 0:
            return
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
        for entry in _SEED_ENTRIES:
            seed_str = f"chronicle|{entry['chapter_number']}|{entry['title']}"
            al_jabr_hash = fatiha_286_hexdigest_from_str(seed_str)
            cur.execute(
                """INSERT INTO chronicle_entries
                   (chapter_number, title, subtitle, glyph_sequence, body_text, al_jabr_hash)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (entry["chapter_number"], entry["title"], entry["subtitle"],
                 entry["glyph_sequence"], entry["body_text"], al_jabr_hash),
            )
        conn.commit()
        logger.info("Chronicle seeded with %d entries", len(_SEED_ENTRIES))
    except Exception:
        conn.rollback()
        logger.exception("Failed to seed chronicle")
    finally:
        conn.close()


def get_chronicle():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, chapter_number, title, subtitle, glyph_sequence, body_text,
                      posted_at, al_jabr_hash
               FROM chronicle_entries
               ORDER BY posted_at DESC"""
        )
        rows = cur.fetchall()
        entries = []
        for r in rows:
            glyphs = [g.strip() for g in r[4].split("-") if g.strip()]
            entries.append({
                "id":              r[0],
                "chapter_number":  r[1],
                "title":           r[2],
                "subtitle":        r[3] or "",
                "glyph_sequence":  r[4],
                "glyphs":          glyphs,
                "body_text":       r[5],
                "english_text":    r[5],
                "posted_at":       r[6].strftime("%Y-%m-%d") if r[6] else "",
                "al_jabr_hash":    (r[7][:16] + "...") if r[7] else "",
            })
        return entries
    finally:
        conn.close()


def post_chronicle_entry(chapter_number, title, subtitle, glyph_sequence, body_text, admin_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
        al_jabr_hash = fatiha_286_hexdigest_from_str(
            f"chronicle|{chapter_number}|{title}|{datetime.now(timezone.utc).isoformat()}"
        )
        cur.execute(
            """INSERT INTO chronicle_entries
               (chapter_number, title, subtitle, glyph_sequence, body_text, posted_by, al_jabr_hash)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (chapter_number, title, subtitle or "", glyph_sequence, body_text, admin_id, al_jabr_hash),
        )
        entry_id = cur.fetchone()[0]
        conn.commit()
        return {"success": True, "id": entry_id, "al_jabr_hash": al_jabr_hash}
    except Exception as e:
        conn.rollback()
        logger.error("Failed to post chronicle entry: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def delete_chronicle_entry(entry_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM chronicle_entries WHERE id = %s", (entry_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()


def _ensure_seed_capture_columns(cur):
    for col, defn in [
        ("entry_type", "VARCHAR(50) DEFAULT 'chronicle'"),
        ("full_text",  "TEXT"),
    ]:
        cur.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
            ("chronicle_entries", col),
        )
        if not cur.fetchone():
            cur.execute(f"ALTER TABLE chronicle_entries ADD COLUMN {col} {defn}")


def save_seed_capture(label: str, text: str, admin_id=None) -> dict:
    from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str, fatiha_286_truncated
    hex_digest = fatiha_286_hexdigest_from_str(text)
    short_sig = fatiha_286_truncated(text.encode("utf-8"), chars=16)

    conn = _get_db()
    try:
        cur = conn.cursor()
        _ensure_seed_capture_columns(cur)

        glyph_sequence = f"α-◆-{short_sig[:4]}"
        subtitle = f"Hex Capture — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

        cur.execute(
            """INSERT INTO chronicle_entries
               (chapter_number, title, subtitle, glyph_sequence, body_text, full_text, entry_type, posted_by, al_jabr_hash)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (
                0,
                label,
                subtitle,
                glyph_sequence,
                f"[SEED_CAPTURE] {hex_digest}",
                text,
                "SEED_CAPTURE",
                admin_id,
                hex_digest,
            ),
        )
        entry_id = cur.fetchone()[0]
        conn.commit()
        return {
            "success": True,
            "id": entry_id,
            "label": label,
            "hex_digest": hex_digest,
            "short_sig": short_sig,
        }
    except Exception as e:
        conn.rollback()
        logger.error("Failed to save seed capture: %s", e)
        return {"error": str(e)}
    finally:
        conn.close()


def get_seed_captures(limit: int = 50) -> list:
    conn = _get_db()
    try:
        cur = conn.cursor()
        _ensure_seed_capture_columns(cur)
        cur.execute(
            """SELECT id, title, subtitle, al_jabr_hash, full_text, posted_at
               FROM chronicle_entries
               WHERE entry_type = %s
               ORDER BY posted_at DESC
               LIMIT %s""",
            ("SEED_CAPTURE", limit),
        )
        rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "id":         r[0],
                "label":      r[1],
                "subtitle":   r[2] or "",
                "hex_digest": r[3] or "",
                "full_text":  r[4] or "",
                "posted_at":  r[5].strftime("%Y-%m-%d %H:%M UTC") if r[5] else "",
            })
        return result
    except Exception as e:
        logger.error("Failed to load seed captures: %s", e)
        return []
    finally:
        conn.close()


_SDK_README = """\
# Adriana Sovereign Coded Language — Open SDK v1.0

PROJECT VOID | Al-Jabr 286 | Resonance Bridge

## Licence

- **Personal use**: MIT — free, no restrictions.
- **Commercial use**: Requires ownership of a VOID Blueprint Token.
  Verify at: https://void.app/api/adriana/verify?token_id=<ID>

## Installation

```bash
pip install adriana-scl  # coming soon to PyPI
# or drop the adriana_sdk/ folder into your project
```

## Quick Start

```python
from adriana_sdk import (
    AdrianaResonance,
    GlyphPoem, GlyphExtension,
    hash_to_sovereign_poem,
    generate_poem,
    encode_message,
    decode_glyphs,
    generate_token_story,
)

# --- Sovereign poem from any hex hash ---
poem = hash_to_sovereign_poem("a3f9b12c8e6d4a7c...")
print(poem.poem)         # e.g. "σ-⚡-∞"
print(poem.meanings)     # e.g. ["Summation/Ledger", "Spark/Ignite", "Loop/Eternal"]
print(poem.translation)  # e.g. "Where Summation meets Spark, Loop emerges."

# --- Poem from any seed string ---
p = generate_poem("project void", length=3)
print(p)                 # GlyphPoem stringifies to the dash-joined glyph form

# --- Encode / decode messages ---
encoded = encode_message("VOID")
print(encoded)           # space-separated glyphs
meanings = decode_glyphs(encoded)
print(meanings)          # list of meaning strings

# --- Custom glyph extension ---
ext = GlyphExtension(name="Sovereignty", glyphs=["σ", "⚡", "∞"], domain="ledger")
print(ext.to_poem())     # GlyphPoem from the extension's first 3 glyphs

# --- Token story (3/6/9 chapters by tier) ---
story = generate_token_story({
    "tier": "rare",
    "token_hash": "a3f9b12c8e6d4a7c",
    "edition_number": 2,
    "total_editions": 5,
})
for ch in story["chapters"]:
    print(f"Chapter {ch['chapter']}: {ch['title']}")
    print(f"  Glyphs: {'-'.join(ch['glyphs'])}")
    print(f"  {ch['translation']}")

# --- Resonance field from any hash ---
field = AdrianaResonance.calculate_resonance("a3f9b12c...")
print(field["glyph"], field["meta"]["meaning"], field["harmonic_state"])
```

## Glyph Lexicon

45 glyphs across entity, condition, and action categories.
See `adriana_sdk/lexicon.py` for the full ontology with frequencies, meanings, and domain colors.

## Licence Verification (Commercial)

```python
import requests

def verify_commercial_licence(token_id, base_url="https://void.app"):
    r = requests.get(f"{base_url}/api/adriana/verify?token_id={token_id}")
    data = r.json()
    return data.get("licensed", False)
```

## Architecture

- **Al-Jabr 286**: Custom 286-bit hash function — see `adriana_sdk/al_jabr_stub.py`
- **Resonance Field**: Maps hash bytes to glyph/frequency/domain states
- **Sovereign Poem**: Deterministic 3-glyph expression from any 286-bit hash
- **Token Story**: Multi-chapter narrative engine (3/6/9 chapters by NFT tier)
- **Chronicle**: Project history ledger — query `/api/chronicle` on any VOID node

## Contact

PROJECT VOID | https://github.com/void-engine
"""

_SDK_INIT = '''\
"""
Adriana Sovereign Coded Language — Open SDK v1.0
https://projectvoid.io
"""

from adriana_sdk.core import (
    AdrianaResonance,
    GlyphPoem,
    GlyphExtension,
    hash_to_sovereign_poem,
    generate_poem,
    encode_message,
    decode_glyphs,
    generate_token_story,
)

__version__ = "1.0.0"
__all__ = [
    "AdrianaResonance",
    "GlyphPoem",
    "GlyphExtension",
    "hash_to_sovereign_poem",
    "generate_poem",
    "encode_message",
    "decode_glyphs",
    "generate_token_story",
]
'''

_SDK_CORE = '''\
"""
Adriana SCL Core — Resonance Bridge v1.0

This module is extracted from the PROJECT VOID Engine.
Licence: MIT for personal use. Commercial use requires a VOID Blueprint Token.
Verify at: https://void.app/api/adriana/verify?token_id=<ID>
"""

from dataclasses import dataclass, field as dc_field
from typing import List, Optional
from adriana_sdk.lexicon import GLYPHS, DOMAIN_COLORS


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class GlyphPoem:
    """A 3-glyph SCL expression derived from a hash or seed string."""
    glyphs: List[str]
    meanings: List[str]
    translation: str
    poem: str       # "glyph0-glyph1-glyph2" display form

    def __str__(self):
        return self.poem


@dataclass
class GlyphExtension:
    """
    A named extension point for custom glyph-domain mappings.
    Useful for attaching domain-specific semantics to the Adriana lexicon.
    """
    name: str
    glyphs: List[str]
    domain: str
    description: str = ""
    metadata: dict = dc_field(default_factory=dict)

    def to_poem(self) -> GlyphPoem:
        """Render the first 3 extension glyphs as a GlyphPoem."""
        g = (self.glyphs + ["α", "α", "α"])[:3]
        meanings = [GLYPHS.get(x, {}).get("meaning", "Unknown") for x in g]
        parts = [m.split("/")[0].strip() for m in meanings]
        translation = f"Where {parts[0]} meets {parts[1]}, {parts[2]} emerges."
        return GlyphPoem(glyphs=g, meanings=meanings, translation=translation, poem="-".join(g))


# ---------------------------------------------------------------------------
# Core engine class
# ---------------------------------------------------------------------------

class AdrianaResonance:
    GLYPHS = GLYPHS
    DOMAIN_COLORS = DOMAIN_COLORS

    @staticmethod
    def calculate_resonance(data_hash):
        clean = _clean_hex(data_hash)
        if len(clean) < 6:
            clean = clean.ljust(6, "0")
        glyph_keys = list(GLYPHS.keys())
        seed = int(clean[-4:], 16) % len(glyph_keys)
        glyph_key = glyph_keys[seed]
        meta = GLYPHS[glyph_key]
        field_strength = round((int(clean[:2], 16) / 255) * 100, 2)
        secondary_key = glyph_keys[int(clean[2:4], 16) % len(glyph_keys)]
        tertiary_key = glyph_keys[int(clean[4:6], 16) % len(glyph_keys)]
        harmonic = (
            "resonant" if field_strength >= 80
            else "aligned" if field_strength >= 50
            else "drifting" if field_strength >= 25
            else "dormant"
        )
        return {
            "glyph": glyph_key,
            "meta": meta,
            "field_strength": field_strength,
            "secondary_glyph": secondary_key,
            "tertiary_glyph": tertiary_key,
            "domain_color": DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
            "harmonic_state": harmonic,
        }

    @staticmethod
    def get_sequence(data_hash, length=6):
        clean = _clean_hex(data_hash).ljust(12, "0")
        glyph_keys = list(GLYPHS.keys())
        seq = []
        for i in range(length):
            start = (i * 2) % max(len(clean) - 1, 1)
            idx = int(clean[start:start + 2].ljust(2, "0"), 16) % len(glyph_keys)
            g = glyph_keys[idx]
            seq.append({"glyph": g, "meta": GLYPHS[g], "color": DOMAIN_COLORS.get(GLYPHS[g]["domain"], "#c9a84c")})
        return seq

    @staticmethod
    def get_all_glyphs():
        return {g: {**meta, "color": DOMAIN_COLORS.get(meta["domain"], "#c9a84c")} for g, meta in GLYPHS.items()}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _clean_hex(h):
    return "".join(c for c in h if c in "0123456789abcdefABCDEF")


def _pick_entity_condition_action(combined, offset):
    """Pick an entity, condition, and action glyph from a hex string at offset using 4-char (16-bit) segments."""
    glyph_keys = list(GLYPHS.keys())
    entities   = glyph_keys[:19]
    conditions = glyph_keys[19:29]
    actions    = glyph_keys[29:45]
    seg_a = int(combined[offset:offset + 4].ljust(4, "0"), 16)
    seg_b = int(combined[offset + 4:offset + 8].ljust(4, "0"), 16)
    seg_c = int(combined[offset + 8:offset + 12].ljust(4, "0"), 16)
    return entities[seg_a % len(entities)], conditions[seg_b % len(conditions)], actions[seg_c % len(actions)]


def _make_translation(glyphs):
    """Compose a human-readable sentence from a 3-glyph Entity-Condition-Action sequence."""
    meanings = [GLYPHS.get(g, {}).get("meaning", "Unknown") for g in glyphs]
    parts = [m.split("/")[0].strip() for m in meanings]
    return f"Where {parts[0]} meets {parts[1]}, {parts[2]} emerges."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hash_to_sovereign_poem(hex_hash: str) -> GlyphPoem:
    """Derive a deterministic sovereign 3-glyph poem from any hex hash string."""
    combined = _clean_hex(hex_hash).ljust(12, "0")
    e, c, a = _pick_entity_condition_action(combined, 0)
    glyphs = [e, c, a]
    meanings = [GLYPHS[g]["meaning"] for g in glyphs]
    return GlyphPoem(
        glyphs=glyphs,
        meanings=meanings,
        translation=_make_translation(glyphs),
        poem=f"{e}-{c}-{a}",
    )


def generate_poem(seed_string: str, length: int = 3) -> GlyphPoem:
    """
    Generate a GlyphPoem from any arbitrary seed string (not necessarily hex).
    The string is converted to a hex digest via Python\'s built-in hash, making it
    deterministic within a process. For cross-process determinism, pass a hex hash.

    Args:
        seed_string: Any string to seed the poem.
        length:      Number of glyphs to include (1-45). Default 3.

    Returns:
        GlyphPoem with `length` glyphs (translation always uses first 3).
    """
    # Convert seed to hex; use sha256 if available, else fallback
    try:
        import hashlib
        h = hashlib.sha256(seed_string.encode()).hexdigest()
    except Exception:
        h = format(abs(hash(seed_string)), "x")
    combined = h.ljust(length * 4, "0")
    glyph_keys = list(GLYPHS.keys())
    glyphs = []
    for i in range(length):
        offset = (i * 4) % max(len(combined) - 3, 1)
        idx = int(combined[offset:offset + 4].ljust(4, "0"), 16) % len(glyph_keys)
        glyphs.append(glyph_keys[idx])
    meanings = [GLYPHS[g]["meaning"] for g in glyphs]
    first3 = (glyphs + ["α", "α", "α"])[:3]
    translation = _make_translation(first3)
    return GlyphPoem(glyphs=glyphs, meanings=meanings, translation=translation, poem="-".join(glyphs))


def encode_message(text: str) -> str:
    """
    Encode a plain-text message into a glyph string.
    Each character is mapped to a glyph from the 45-glyph lexicon using its Unicode
    ordinal modulo 45. Returns glyphs separated by spaces.

    Args:
        text: Plain-text string to encode.

    Returns:
        Space-separated glyph string.
    """
    glyph_keys = list(GLYPHS.keys())
    return " ".join(glyph_keys[ord(ch) % len(glyph_keys)] for ch in text)


def decode_glyphs(glyph_string: str) -> List[str]:
    """
    Decode a glyph string (space-separated) into a list of human-readable meanings.
    Unrecognised glyphs are returned as "[unknown]".

    Args:
        glyph_string: Space-separated glyph symbols (as produced by encode_message).

    Returns:
        List of meaning strings, one per glyph.
    """
    return [GLYPHS[g]["meaning"] if g in GLYPHS else "[unknown]" for g in glyph_string.split()]


_STORY_CHAPTERS = [
    {"number": 1, "milestone": "Genesis",            "title": "The Engine Awakens",            "domain": "genesis",   "body": "The first seed was planted in the void. Code breathed life into the ENGINE — a steganography core built on Al-Jabr 286-bit hashing, resonating at 432 Hz."},
    {"number": 2, "milestone": "The Signal",         "title": "First 432 Hz Transmission",     "domain": "signal",    "body": "A frequency was chosen — not arbitrary, but sovereign. 432 Hz became the carrier of every packet, every hash, every handshake the VOID ENGINE made with the outside world."},
    {"number": 3, "milestone": "The Mesh",           "title": "Beehive Protocol Activates",    "domain": "mesh",      "body": "Nodes found each other. The Beehive Protocol emerged — a peer mesh where every Body node echoes the Brain\'s ledger, distributing trust across geography and time."},
    {"number": 4, "milestone": "The Economy",        "title": "VTX Ledger Ignites",            "domain": "ledger",    "body": "Value entered the system. The Vortex Token (VTX) was issued — not minted by speculation but earned through participation, computation, and proof of work."},
    {"number": 5, "milestone": "The Deed",           "title": "Blueprint Tokens Minted",       "domain": "forge",     "body": "Manufacturing slots opened. Each Blueprint Token became a deed — a cryptographic claim on the physical 4000-Series Sovereign Node being built."},
    {"number": 6, "milestone": "The Drop",           "title": "VOID Mystery Collection Opens", "domain": "vortex",    "body": "The void released 1,000 unknowns. The VOID Mystery Collection launched — blind mints on a bonding curve, each token sealed until the moment of reveal."},
    {"number": 7, "milestone": "The Unknown I",      "title": "Signal Unspoken",               "domain": "resonance", "body": "Beyond the sixth chapter, the lexicon grows quiet. There are frequencies the Adriana Protocol cannot yet name."},
    {"number": 8, "milestone": "The Unknown II",     "title": "Breath Unmeasured",             "domain": "temporal",  "body": "The Engine exhales. This chapter has no complete English translation — it exists as pure glyph-state."},
    {"number": 9, "milestone": "The Sovereign Seal", "title": "Engine Eternal",                "domain": "finality",  "body": "Finality. This token has witnessed the full arc of PROJECT VOID — from genesis seed to sovereign machine."},
]

_CHAPTERS_BY_TIER = {"common": 3, "rare": 6, "legendary": 9}


def generate_token_story(token: dict) -> dict:
    """
    Generate a multi-chapter story for a Blueprint Token.

    Each chapter uses successive 16-bit (4 hex-char) segments of the token hash,
    combined with edition_number and total_editions as a salt.

    Returns:
        {
          tier, chapter_count, locked_count,
          chapters: [{chapter, milestone, title, glyphs, translation, body, domain, domain_color}]
        }
    """
    tier = token.get("tier", "common")
    hex_hash = token.get("token_hash", "").replace("...", "").strip()
    edition = int(token.get("edition_number") or 1)
    total = int(token.get("total_editions") or 1)
    unlocked = _CHAPTERS_BY_TIER.get(tier, 3)

    edition_salt = f"{edition:04x}{total:04x}"
    combined = (_clean_hex(hex_hash) + edition_salt).ljust(108, "0")

    chapters = []
    for i, meta in enumerate(_STORY_CHAPTERS[:unlocked]):
        offset = (i * 12) % max(len(combined) - 11, 1)
        e, c, a = _pick_entity_condition_action(combined, offset)
        glyphs = [e, c, a]
        chapters.append({
            "chapter":      meta["number"],
            "milestone":    meta["milestone"],
            "title":        meta["title"],
            "glyphs":       glyphs,
            "translation":  _make_translation(glyphs),
            "body":         meta["body"],
            "domain":       meta["domain"],
            "domain_color": DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
        })
    return {"tier": tier, "chapter_count": unlocked, "chapters": chapters, "locked_count": 9 - unlocked}
'''

_SDK_LEXICON = '''\
"""
Adriana Glyph Lexicon — 45-glyph ontology for PROJECT VOID
Frequencies, meanings, and domain color assignments.
"""

GLYPHS = {
    "α":  {"name": "Alpha",         "frequency": 432.0, "meaning": "Origin/Seed",         "domain": "genesis"},
    "β":  {"name": "Beta",          "frequency": 433.2, "meaning": "Growth/Sprout",        "domain": "aqua"},
    "γ":  {"name": "Gamma",         "frequency": 434.0, "meaning": "Signal/Pulse",         "domain": "signal"},
    "δ":  {"name": "Delta",         "frequency": 434.8, "meaning": "Change/Shift",         "domain": "transform"},
    "ε":  {"name": "Epsilon",       "frequency": 435.5, "meaning": "Threshold/Edge",       "domain": "boundary"},
    "ζ":  {"name": "Zeta",          "frequency": 429.0, "meaning": "Depth/Root",           "domain": "soil"},
    "η":  {"name": "Eta",           "frequency": 430.5, "meaning": "Flow/Current",         "domain": "aqua"},
    "θ":  {"name": "Theta",         "frequency": 431.0, "meaning": "Heat/Warmth",          "domain": "environment"},
    "ι":  {"name": "Iota",          "frequency": 432.5, "meaning": "Particle/Grain",       "domain": "data"},
    "κ":  {"name": "Kappa",         "frequency": 433.7, "meaning": "Key/Lock",             "domain": "security"},
    "λ":  {"name": "Lambda",        "frequency": 436.0, "meaning": "Wave/Carry",           "domain": "signal"},
    "μ":  {"name": "Mu",            "frequency": 432.8, "meaning": "Measure/Weight",       "domain": "metrics"},
    "ν":  {"name": "Nu",            "frequency": 431.5, "meaning": "Node/Link",            "domain": "mesh"},
    "ξ":  {"name": "Xi",            "frequency": 437.0, "meaning": "Scatter/Spread",       "domain": "vortex"},
    "ο":  {"name": "Omicron",       "frequency": 432.2, "meaning": "Circle/Return",        "domain": "cycle"},
    "π":  {"name": "Pi",            "frequency": 432.0, "meaning": "Ratio/Balance",        "domain": "harmony"},
    "ρ":  {"name": "Rho",           "frequency": 433.0, "meaning": "Density/Mass",         "domain": "data"},
    "σ":  {"name": "Sigma",         "frequency": 435.1, "meaning": "Summation/Ledger",     "domain": "ledger"},
    "τ":  {"name": "Tau",           "frequency": 434.5, "meaning": "Time/Tick",            "domain": "temporal"},
    "υ":  {"name": "Upsilon",       "frequency": 430.0, "meaning": "Vessel/Container",     "domain": "vault"},
    "φ":  {"name": "Phi-Lower",     "frequency": 442.0, "meaning": "Spiral/Fibonacci",     "domain": "vortex"},
    "χ":  {"name": "Chi",           "frequency": 436.5, "meaning": "Cross/Junction",       "domain": "mesh"},
    "ψ":  {"name": "Psi",           "frequency": 438.5, "meaning": "Breath/Spirit",        "domain": "resonance"},
    "ω":  {"name": "Omega-Lower",   "frequency": 428.5, "meaning": "Rest/Complete",        "domain": "finality"},
    "Α":  {"name": "Alpha-Cap",     "frequency": 432.0, "meaning": "Authority/Source",     "domain": "governance"},
    "Β":  {"name": "Beta-Cap",      "frequency": 433.2, "meaning": "Builder/Forge",        "domain": "forge"},
    "Γ":  {"name": "Gamma-Cap",     "frequency": 434.0, "meaning": "Gate/Portal",          "domain": "gateway"},
    "Δ":  {"name": "Delta-Cap",     "frequency": 434.8, "meaning": "Transform/Evolve",     "domain": "transform"},
    "Θ":  {"name": "Theta-Cap",     "frequency": 431.0, "meaning": "Shield/Guard",         "domain": "security"},
    "Λ":  {"name": "Lambda-Cap",    "frequency": 436.0, "meaning": "Carrier/Bridge",       "domain": "signal"},
    "Ξ":  {"name": "Xi-Cap",        "frequency": 437.0, "meaning": "Archive/Store",        "domain": "vault"},
    "Π":  {"name": "Pi-Cap",        "frequency": 432.0, "meaning": "Foundation/Base",      "domain": "genesis"},
    "Σ":  {"name": "Sigma-Cap",     "frequency": 435.1, "meaning": "Total/Aggregate",      "domain": "ledger"},
    "Φ":  {"name": "Phi",           "frequency": 442.2, "meaning": "Golden Ratio/Structure","domain": "harmony"},
    "Ψ":  {"name": "Psi-Cap",       "frequency": 438.5, "meaning": "Sovereign Mind",       "domain": "resonance"},
    "Ω":  {"name": "Omega",         "frequency": 428.0, "meaning": "Finality/Vault",       "domain": "finality"},
    "∞":  {"name": "Infinity",      "frequency": 432.0, "meaning": "Loop/Eternal",         "domain": "cycle"},
    "◆":  {"name": "Void Diamond",  "frequency": 432.0, "meaning": "Core/Engine",          "domain": "genesis"},
    "⬡":  {"name": "Hexagon",       "frequency": 435.0, "meaning": "Mesh Cell",            "domain": "mesh"},
    "⟐":  {"name": "Lozenge",       "frequency": 433.5, "meaning": "Silt Drop",            "domain": "silt"},
    "☽":  {"name": "Crescent",      "frequency": 429.5, "meaning": "Rest Phase",           "domain": "temporal"},
    "☀":  {"name": "Sun",           "frequency": 440.0, "meaning": "Peak/Broadcast",       "domain": "signal"},
    "⚡": {"name": "Lightning",     "frequency": 441.0, "meaning": "Spark/Ignite",         "domain": "forge"},
    "🌊": {"name": "Wave",          "frequency": 430.0, "meaning": "Tide/Surge",           "domain": "aqua"},
    "🔮": {"name": "Crystal",       "frequency": 432.0, "meaning": "Prophecy/Foresight",   "domain": "resonance"},
}

DOMAIN_COLORS = {
    "genesis":    "#c9a84c",
    "aqua":       "#2dd4bf",
    "signal":     "#60a5fa",
    "transform":  "#a78bfa",
    "boundary":   "#f87171",
    "soil":       "#92400e",
    "environment":"#fb923c",
    "data":       "#34d399",
    "security":   "#f472b6",
    "metrics":    "#a3e635",
    "mesh":       "#22d3ee",
    "vortex":     "#818cf8",
    "cycle":      "#fbbf24",
    "harmony":    "#e879f9",
    "ledger":     "#c9a84c",
    "temporal":   "#6366f1",
    "vault":      "#475569",
    "resonance":  "#2dd4bf",
    "finality":   "#ef4444",
    "governance": "#c9a84c",
    "forge":      "#f97316",
    "gateway":    "#8b5cf6",
    "silt":       "#2dd4bf",
}
'''

_SDK_AL_JABR_STUB = '''\
"""
Al-Jabr 286 — Stub for SDK consumers.

The full Al-Jabr 286-bit hash function is proprietary to PROJECT VOID.
This stub provides a SHA-256-based approximation for testing.
For production use with VOID nodes, use the official client library.
"""

import hashlib


def fatiha_286_hexdigest_from_str(text):
    """SHA-256 approximation of Al-Jabr 286 — for testing only."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return (digest * 3)[:72]


def fatiha_286_truncated(data, length=16):
    digest = hashlib.sha256(data).hexdigest()
    return digest[:length]
'''

_SDK_SETUP = '''\
from setuptools import setup, find_packages

setup(
    name="adriana-scl",
    version="1.0.0",
    description="Adriana Sovereign Coded Language — Open SDK for PROJECT VOID",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
'''


def generate_adriana_sdk_zip():
    """
    Build an in-memory ZIP containing the Adriana SCL Open SDK.
    Returns a bytes object ready to send as a file download.
    """
    # Import live glyph definitions from the canonical engine module so the SDK
    # lexicon always reflects the current state of AdrianaResonance.GLYPHS.
    try:
        from void_engine.adriana_scl import AdrianaResonance as _AR
        live_glyphs       = _AR.GLYPHS
        live_domain_colors = _AR.DOMAIN_COLORS
    except Exception:
        live_glyphs        = {}
        live_domain_colors = {}

    # Serialize live definitions as Python source for adriana_sdk/lexicon.py
    def _dict_repr(d):
        lines = ["{\n"]
        for k, v in d.items():
            lines.append(f"    {k!r}: {v!r},\n")
        lines.append("}")
        return "".join(lines)

    live_lexicon_py = (
        '"""\nAdriana Glyph Lexicon — generated from current PROJECT VOID Engine definitions.\n'
        'Frequencies, meanings, and domain color assignments.\n"""\n\n'
        f"GLYPHS = {_dict_repr(live_glyphs)}\n\n"
        f"DOMAIN_COLORS = {_dict_repr(live_domain_colors)}\n"
    )

    licence_text = (
        "MIT License\n\n"
        "Copyright (c) 2025 PROJECT VOID\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy "
        "of this software and associated documentation files (the 'Software'), to deal "
        "in the Software without restriction, including without limitation the rights "
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
        "copies of the Software, and to permit persons to whom the Software is furnished "
        "to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all "
        "copies or substantial portions of the Software.\n\n"
        "COMMERCIAL USE: Any commercial deployment, product, or service built with or "
        "incorporating this SDK requires ownership of a VOID Blueprint Token. "
        "Verification: GET https://void.app/api/adriana/verify?token_id=<ID>\n\n"
        "THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND."
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        def add(path, content):
            zf.writestr(path, content)

        # Root-level distribution files (correct Python package layout)
        add("README.md",     _SDK_README)
        add("setup.py",      _SDK_SETUP)
        add("LICENCE.txt",   licence_text)

        # Package source (importable module)
        add("adriana_sdk/__init__.py",     _SDK_INIT)
        add("adriana_sdk/core.py",         _SDK_CORE)
        add("adriana_sdk/lexicon.py",      live_lexicon_py)   # live from engine
        add("adriana_sdk/al_jabr_stub.py", _SDK_AL_JABR_STUB)

    buf.seek(0)
    return buf.read()
