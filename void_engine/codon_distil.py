"""
Codon Distillation Engine — AI Memory Reader
=============================================
Reads large text archives and surfaces:
  1. The strongest stories — narrative moments with emotional truth
  2. The deepest understanding — insights and crystallisations
  3. The most resonant signals — moments worth preserving forever

Each finding becomes a VOID codon: Entity · Condition · Action
using the canonical 45-glyph alphabet from void_script.py.
"""

import json
import logging
import random
from typing import Optional

from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
from void_engine.void_script import CANONICAL_GLYPHS, get_glyphs_by_role

logger = logging.getLogger(__name__)

_ENTITY_GLYPHS = [g for g, m in CANONICAL_GLYPHS.items() if m["role"] == "entity"]
_CONDITION_GLYPHS = [g for g, m in CANONICAL_GLYPHS.items() if m["role"] == "condition"]
_ACTION_GLYPHS = [g for g, m in CANONICAL_GLYPHS.items() if m["role"] == "action"]

_EXTRACT_SYSTEM = """You are an AI memory reader for PROJECT VOID — a sovereign infrastructure system.
Your task: read a passage of text and identify the single most significant moment within it.
Look for:
- Emotional truth: moments of genuine feeling, tension, or revelation
- Narrative power: scenes or events that would be remembered across centuries
- Deep insight: crystallisations of understanding that compress complexity into clarity

Respond ONLY with valid JSON. No preamble. No explanation.

Format:
{
  "entity": "<the subject or agent of this moment, 2-5 words>",
  "condition": "<the state or context in which this occurs, 2-5 words>",
  "action": "<what happens or is understood, 2-5 words>",
  "story_excerpt": "<the most resonant sentence or phrase from the passage, max 200 chars>",
  "resonance": <0-10, emotional depth and truth>,
  "clarity": <0-10, sharpness of insight>,
  "story": <0-10, narrative power and memorability>
}

If the passage contains nothing significant (filler, headers, repetition), return:
{"skip": true}"""


def chunk_text(text: str, max_words: int = 800) -> list[str]:
    """Split text into digestible chunks of max_words words."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + max_words]
        chunks.append(" ".join(chunk_words))
        i += max_words
    return [c for c in chunks if c.strip()]


def extract_moments(chunk: str, openai_client) -> Optional[dict]:
    """
    Call OpenAI to identify the most significant moment in this chunk.
    Returns dict with entity/condition/action/story_excerpt/scores or None.
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _EXTRACT_SYSTEM},
                {"role": "user", "content": chunk[:4000]},
            ],
            temperature=0.3,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        data = json.loads(raw)

        if data.get("skip"):
            return None

        required = ["entity", "condition", "action", "story_excerpt"]
        if not all(k in data for k in required):
            return None

        return {
            "entity": str(data["entity"])[:80],
            "condition": str(data["condition"])[:80],
            "action": str(data["action"])[:80],
            "story_excerpt": str(data["story_excerpt"])[:300],
            "resonance": float(data.get("resonance", 5)),
            "clarity": float(data.get("clarity", 5)),
            "story": float(data.get("story", 5)),
        }

    except json.JSONDecodeError as e:
        logger.warning("JSON decode error in extract_moments: %s", e)
        return None
    except Exception as e:
        logger.error("extract_moments error: %s", e)
        return None


def score_codon(moment: dict) -> float:
    """Score a codon by the geometric mean of Resonance, Clarity, and Story (0–10 each)."""
    r = max(0.1, min(10.0, moment.get("resonance", 5)))
    c = max(0.1, min(10.0, moment.get("clarity", 5)))
    s = max(0.1, min(10.0, moment.get("story", 5)))
    return round((r * c * s) ** (1 / 3), 3)


def map_to_glyphs(entity: str, condition: str, action: str) -> str:
    """
    Map the triadic structure to VOID glyphs.
    Uses a deterministic hash-based selection from the canonical alphabet.
    """
    e_idx = int(fatiha_286_hexdigest_from_str(entity)[:4], 16) % len(_ENTITY_GLYPHS)
    c_idx = int(fatiha_286_hexdigest_from_str(condition)[:4], 16) % len(_CONDITION_GLYPHS)
    a_idx = int(fatiha_286_hexdigest_from_str(action)[:4], 16) % len(_ACTION_GLYPHS)

    e_glyph = _ENTITY_GLYPHS[e_idx]
    c_glyph = _CONDITION_GLYPHS[c_idx]
    a_glyph = _ACTION_GLYPHS[a_idx]

    return f"{e_glyph}·{c_glyph}·{a_glyph}"


def seal_to_chronicle(codon: dict, conn) -> str:
    """
    Seal a top codon into the VOID Chronicle with Al-Jabr 286 hash.
    Returns the chronicle entry ID or raises on failure.
    """
    seal_data = f"{codon['entity']}|{codon['condition']}|{codon['action']}|{codon['glyph_seq']}"
    al_jabr_hash = fatiha_286_hexdigest_from_str(seal_data)

    title = f"CODON SEAL — {codon['glyph_seq']}"
    subtitle = f"{codon['entity']} · {codon['condition']} · {codon['action']}"
    body = (
        f"Entity: {codon['entity']}\n"
        f"Condition: {codon['condition']}\n"
        f"Action: {codon['action']}\n\n"
        f'"{codon["story_excerpt"]}"\n\n'
        f"Resonance: {codon['resonance']}/10 | Clarity: {codon['clarity']}/10 | Story: {codon['story_score']}/10\n"
        f"Total Score: {codon['total_score']}\n\n"
        f"Al-Jabr 286: {al_jabr_hash}"
    )

    try:
        from void_engine.chronicle_adriana import _get_current_season
        season = _get_current_season()
    except Exception:
        season = "distillation"

    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chronicle_entries
                   (chapter_number, title, subtitle, glyph_sequence, body_text,
                    al_jabr_hash, entry_type, season)
                   VALUES (
                       (SELECT COALESCE(MAX(chapter_number), 0) + 1 FROM chronicle_entries),
                       %s, %s, %s, %s, %s, 'CODON_SEAL', %s
                   )
                   RETURNING id""",
                (title, subtitle, codon["glyph_seq"], body, al_jabr_hash, season),
            )
            entry_id = cur.fetchone()[0]
        conn.commit()
        return str(entry_id)
    except Exception as e:
        conn.rollback()
        logger.error("seal_to_chronicle error: %s", e)
        raise


def init_codon_distil_tables(conn):
    """Create the codon distillation tables if they don't exist."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS codon_distil_jobs (
                    id           SERIAL PRIMARY KEY,
                    job_id       VARCHAR(64) UNIQUE NOT NULL,
                    status       VARCHAR(20) DEFAULT 'pending',
                    total_chunks INT DEFAULT 0,
                    done_chunks  INT DEFAULT 0,
                    created_at   TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS codon_distil_results (
                    id            SERIAL PRIMARY KEY,
                    job_id        VARCHAR(64) NOT NULL,
                    entity        TEXT NOT NULL,
                    condition     TEXT NOT NULL,
                    action        TEXT NOT NULL,
                    glyph_seq     VARCHAR(20) NOT NULL,
                    story_excerpt TEXT,
                    resonance     FLOAT DEFAULT 0,
                    clarity       FLOAT DEFAULT 0,
                    story_score   FLOAT DEFAULT 0,
                    total_score   FLOAT DEFAULT 0,
                    sealed        BOOLEAN DEFAULT FALSE,
                    al_jabr_hash  VARCHAR(80),
                    created_at    TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        conn.commit()
        logger.info("Codon distil tables ensured")
    except Exception as e:
        conn.rollback()
        logger.error("init_codon_distil_tables error: %s", e)
        raise
