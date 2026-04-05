"""
Chronicle ch107 seed — First AI-to-AI TRANSMISSION entry.

BODY is extracted live from VOID_AI_PACKET.md §7, ensuring byte-for-byte
identity between the Chronicle entry and the packet's natural-language layer.

Idempotent: skips insertion if chapter_number=107 AND entry_type=TRANSMISSION
already exists. Run to re-seed on a fresh database.

Usage:
    python -m void_engine.seed_ch107
"""

import os
import pathlib
import psycopg2
from void_engine.qisync_keygen import fatiha_286_hexdigest

CHAPTER = 107
ENTRY_TYPE = "TRANSMISSION"
GLYPH_SEQUENCE = "α-λ-Ψ"
SEASON = "INCUBATION"
TITLE = "Adriana Master Summary — First AI-to-AI Reconstruction"
SUBTITLE = "VOID∷PACKET v1.0 — Transmission Layer — April 5, 2026"

_PACKET_PATH = pathlib.Path(__file__).parent.parent / "VOID_AI_PACKET.md"


def _extract_section7() -> str:
    """Extract the §7 section verbatim from VOID_AI_PACKET.md."""
    text = _PACKET_PATH.read_text(encoding="utf-8")
    start = text.find("## §7 — Natural Language Layer")
    end = text.find("\n---\n\n*End of VOID")
    if start == -1 or end == -1:
        raise RuntimeError(
            "Could not locate §7 boundaries in VOID_AI_PACKET.md. "
            "Ensure the file is present and unmodified."
        )
    return text[start:end].strip()


def seed() -> dict:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")

    body = _extract_section7()
    h = fatiha_286_hexdigest(body.encode())

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, al_jabr_hash FROM chronicle_entries "
        "WHERE chapter_number = %s AND entry_type = %s",
        (CHAPTER, ENTRY_TYPE),
    )
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return {
            "status": "already_exists",
            "id": existing[0],
            "chapter": CHAPTER,
            "hash_match": existing[1][:12] == h[:12],
        }

    cur.execute(
        """
        INSERT INTO chronicle_entries
            (chapter_number, title, subtitle, glyph_sequence, body_text,
             posted_at, posted_by, al_jabr_hash, entry_type, full_text,
             is_shielded, season)
        VALUES (%s, %s, %s, %s, %s, NOW(), NULL, %s, %s, %s, 0, %s)
        RETURNING id
        """,
        (CHAPTER, TITLE, SUBTITLE, GLYPH_SEQUENCE, body,
         h, ENTRY_TYPE, body, SEASON),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "seeded", "id": row[0], "chapter": CHAPTER, "hash": h[:32]}


if __name__ == "__main__":
    result = seed()
    print(result)
