"""
Chronicle Seed — Context Compression Pipeline
==============================================
Pulls all Chronicle entries from all available sources, then compresses them
through the codon distillation engine (codon_distil.py), producing a single
ordered codon chain in 3-6-9 triadic clusters.

Data sources (all are read; at least one must be non-empty for generation to succeed):
  1. Postgres chronicle_entries table — narrative/story chronicle records
  2. data/chronicle.db SQLite — operational consensus chronicle + episodic memory
  3. VOID_CHRONICLE.md — full markdown text distilled in 800-word chunks

Architecture:
  - Each chronicle record → 3-glyph codon: entity·condition·action
  - Codons grouped into 3-6-9 triadic clusters (3 glyphs per codon, 3 triads per beat, 9-beat segments)
  - Seed header token count: number of chars in header / 4 (target <50 tokens)

Token target:
  - The "seed header" is the compact prompt stub (<50 tokens) an AI loads to restore context
  - The full codon chain is the data payload (not counted against the token target)
  - The target is that the header text itself is under 50 tokens; chain is a separate object
"""

import logging
import os
import re
import sqlite3
from datetime import datetime, timezone

from void_engine.void_codon_vocab import PLATFORM_CODONS

logger = logging.getLogger(__name__)

SEED_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "seeds")
CHRONICLE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chronicle.db")

SEED_HEADER_TOKEN_TARGET = 50


def _ensure_seed_dir():
    os.makedirs(SEED_OUTPUT_DIR, exist_ok=True)


def get_postgres_chronicle_entries() -> list[dict]:
    """
    Pull all chronicle entries from the Postgres chronicle_entries table.

    Raises on connection failure (so caller can decide how to handle it).
    Returns empty list only when the table is empty or truly has 0 rows.
    """
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, chapter_number, title, subtitle, glyph_sequence,
                          body_text, entry_type, season, posted_at
                   FROM chronicle_entries
                   ORDER BY chapter_number ASC, posted_at ASC"""
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "chapter_number": r[1],
                    "title": r[2] or "",
                    "subtitle": r[3] or "",
                    "glyph_sequence": r[4] or "",
                    "body_text": r[5] or "",
                    "entry_type": r[6] or "CHRONICLE",
                    "season": r[7] or "",
                    "posted_at": r[8].isoformat() if r[8] else "",
                    "source_db": "postgres",
                }
                for r in rows
            ]
    finally:
        conn.close()


def get_sqlite_chronicle_entries() -> list[dict]:
    """
    Pull chronicle records from data/chronicle.db (SQLite).

    Reads from both 'chronicle' (operational records) and 'episodic_memory' tables.
    Raises on file/access failure; returns empty list only when tables are empty.
    """
    entries = []
    if not os.path.exists(CHRONICLE_DB_PATH):
        return []

    conn = sqlite3.connect(CHRONICLE_DB_PATH)
    try:
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}

        if "chronicle" in tables:
            cur.execute(
                """SELECT id, timestamp, consensus_command, consensus_intent,
                          outcome, success, machine_id, is_founder_wisdom
                   FROM chronicle
                   ORDER BY id ASC"""
            )
            for r in cur.fetchall():
                title = str(r[2] or "")[:80]
                body = "\n".join(filter(None, [
                    str(r[3] or ""),
                    str(r[4] or ""),
                    "founder wisdom" if r[7] else "",
                ]))
                entries.append({
                    "id": f"sqlite-{r[0]}",
                    "chapter_number": r[0] or 0,
                    "title": title,
                    "subtitle": f"machine={r[6] or 'void'} | success={r[5]}",
                    "glyph_sequence": "",
                    "body_text": body,
                    "entry_type": "OPERATIONAL",
                    "season": "",
                    "posted_at": str(r[1] or ""),
                    "source_db": "sqlite_chronicle",
                })

        if "episodic_memory" in tables:
            cur.execute(
                """SELECT id, timestamp, domain, sensor_key, value, direction
                   FROM episodic_memory
                   ORDER BY id ASC"""
            )
            for r in cur.fetchall():
                domain = str(r[2] or "void")
                key = str(r[3] or "signal")
                val = str(r[4] or "")
                direction = str(r[5] or "stable")
                entries.append({
                    "id": f"episodic-{r[0]}",
                    "chapter_number": r[0] or 0,
                    "title": f"{domain}:{key}",
                    "subtitle": f"direction={direction}",
                    "glyph_sequence": "",
                    "body_text": f"domain={domain} | key={key} | value={val} | direction={direction}",
                    "entry_type": "EPISODIC",
                    "season": "",
                    "posted_at": str(r[1] or ""),
                    "source_db": "sqlite_episodic",
                })
    finally:
        conn.close()

    return entries


def get_void_chronicle_md_text() -> str:
    """Read VOID_CHRONICLE.md if it exists."""
    root = os.path.dirname(os.path.dirname(__file__))
    md_path = os.path.join(root, "VOID_CHRONICLE.md")
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _extract_keywords_from_chunk(chunk: str) -> tuple[str, str, str]:
    """
    Extract entity/condition/action keywords from a text chunk.
    Uses heuristics: first significant noun phrase, dominant state word,
    and a verb/action word — all suitable for map_to_glyphs().
    """
    words = chunk.split()
    clean_words = [re.sub(r"[^a-zA-Z0-9]", "", w) for w in words]
    significant = [w for w in clean_words if len(w) > 4]

    if len(significant) < 3:
        significant = [w for w in clean_words if len(w) > 2]

    n = len(significant)
    entity = significant[0] if n > 0 else "void"
    condition = significant[n // 3] if n > 1 else "sovereign"
    action = significant[(n * 2) // 3] if n > 2 else "resonates"

    return entity, condition, action


def _distil_entry_to_codon(entry: dict) -> dict | None:
    """
    Convert a single chronicle entry to a codon dict using the distillation engine.

    Priority:
    1. If entry has a valid glyph_sequence (already distilled), parse and use it.
    2. Otherwise derive entity/condition/action from title+body and run map_to_glyphs().
    """
    from void_engine.codon_distil import map_to_glyphs

    glyph_seq = entry.get("glyph_sequence", "").strip()
    title = entry.get("title", "").strip()
    body = entry.get("body_text", "").strip()

    if glyph_seq:
        parts = re.split(r"[·\-]", glyph_seq)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 3:
            canonical = f"{parts[0]}·{parts[1]}·{parts[2]}"
            words = body.split()[:30]
            excerpt = " ".join(words) + ("…" if len(body.split()) > 30 else "")
            return {
                "glyph_seq": canonical,
                "entity": parts[0],
                "condition": parts[1],
                "action": parts[2],
                "title": title,
                "excerpt": excerpt,
                "chapter": entry.get("chapter_number", 0),
                "entry_type": entry.get("entry_type", "CHRONICLE"),
                "source": "db_glyph",
                "source_db": entry.get("source_db", "unknown"),
            }

    combined_text = f"{title}. {body}"
    if len(combined_text.strip()) < 10:
        return None

    entity, condition, action = _extract_keywords_from_chunk(combined_text)
    glyph_seq = map_to_glyphs(entity, condition, action)

    parts = glyph_seq.split("·")
    if len(parts) < 3:
        return None

    words = body.split()[:30]
    excerpt = " ".join(words) + ("…" if len(body.split()) > 30 else "")

    return {
        "glyph_seq": glyph_seq,
        "entity": parts[0],
        "condition": parts[1],
        "action": parts[2],
        "title": title,
        "excerpt": excerpt,
        "chapter": entry.get("chapter_number", 0),
        "entry_type": entry.get("entry_type", "CHRONICLE"),
        "source": "distilled",
        "source_db": entry.get("source_db", "unknown"),
    }


def _distil_md_chunks(md_text: str) -> list[dict]:
    """
    Process VOID_CHRONICLE.md text — split into 800-word chunks, derive a
    codon for each chunk using the deterministic map_to_glyphs() engine.
    """
    from void_engine.codon_distil import chunk_text, map_to_glyphs

    if not md_text.strip():
        return []

    chunks = chunk_text(md_text, max_words=800)
    codons = []

    for i, chunk in enumerate(chunks):
        entity, condition, action = _extract_keywords_from_chunk(chunk)
        glyph_seq = map_to_glyphs(entity, condition, action)
        parts = glyph_seq.split("·")
        if len(parts) < 3:
            continue

        words = chunk.split()[:20]
        excerpt = " ".join(words) + "…"

        codons.append({
            "glyph_seq": glyph_seq,
            "entity": parts[0],
            "condition": parts[1],
            "action": parts[2],
            "title": f"VOID_CHRONICLE chunk {i+1}",
            "excerpt": excerpt,
            "chapter": i,
            "entry_type": "MD_CHRONICLE",
            "source": "md_distilled",
            "source_db": "void_chronicle_md",
        })

    return codons


def _band_for_index(idx: int) -> str:
    """Map index to a frequency band via 3-6-9 logic."""
    n = idx % 9
    if n <= 2:
        return "low"
    elif n <= 5:
        return "mid"
    else:
        return "high"


def _assign_band(codon: dict, idx: int) -> dict:
    """Assign a frequency band to a distilled codon using 3-6-9 grouping."""
    band = _band_for_index(idx)
    codon["band"] = band
    hz_map = {"low": 136, "mid": 432, "high": 2200}
    codon["hz"] = hz_map.get(band, 432)
    return codon


def build_codon_chain(codons: list[dict]) -> str:
    """
    Build a codon chain string in 3-6-9 triadic clusters.
    Every 9 codons are joined as a beat cluster, separated by ' || '.
    Within a cluster, groups of 3 are separated by ' | '.
    """
    if not codons:
        return ""

    glyphs = [c["glyph_seq"] for c in codons]

    clusters = []
    for i in range(0, len(glyphs), 9):
        beat = glyphs[i:i+9]
        triads = []
        for j in range(0, len(beat), 3):
            triad = beat[j:j+3]
            triads.append(" · ".join(triad))
        clusters.append(" | ".join(triads))

    return " || ".join(clusters)


def build_context_seed_header(codons: list[dict], chronicle_size_bytes: int) -> str:
    """
    Build a human-readable context seed header under 50 tokens.

    This is the compact stub pasted at the start of a new AI chat session.
    It references the codon count and band distribution — enough for an AI to
    reconstruct context when given the full chain separately.

    Target: < 50 tokens (estimated as chars / 4).
    """
    n_low = sum(1 for c in codons if c.get("band") == "low")
    n_mid = sum(1 for c in codons if c.get("band") == "mid")
    n_high = sum(1 for c in codons if c.get("band") == "high")

    header = (
        f"VOID·SEED α·Ω·◆ | {len(codons)} codons | "
        f"L{n_low}·M{n_mid}·H{n_high} | "
        f"{chronicle_size_bytes} bytes"
    )
    return header


def generate_chronicle_seed() -> dict:
    """
    Main pipeline: pull all chronicle sources, compress to codon chain, return metadata.

    Raises ValueError if all chronicle sources return no data (hard fail — do not produce
    a seed that silently contains only platform fallback codons).

    Returns:
        dict with keys:
            codon_chain (str)
            codons (list[dict])
            seed_header (str)
            seed_header_tokens (int)  -- chars // 4, should be < 50
            original_size_bytes (int)
            codon_chain_length (int)
            entry_count (int)        -- postgres entries
            sqlite_entry_count (int) -- sqlite entries
            md_codon_count (int)     -- codons from VOID_CHRONICLE.md
            timestamp (str)
    """
    _ensure_seed_dir()

    errors = []

    postgres_entries = []
    try:
        postgres_entries = get_postgres_chronicle_entries()
    except Exception as e:
        errors.append(f"Postgres: {e}")
        logger.error("Postgres chronicle read failed: %s", e)

    sqlite_entries = []
    try:
        sqlite_entries = get_sqlite_chronicle_entries()
    except Exception as e:
        errors.append(f"SQLite: {e}")
        logger.error("SQLite chronicle.db read failed: %s", e)

    md_text = get_void_chronicle_md_text()

    all_db_entries = postgres_entries + sqlite_entries
    total_records = len(all_db_entries) + len(md_text.strip())

    if total_records == 0:
        raise ValueError(
            "Chronicle seed generation failed: all data sources returned empty. "
            f"Errors: {'; '.join(errors) if errors else 'tables appear empty'}. "
            "Cannot generate a seed without Chronicle data."
        )

    original_size_bytes = sum(
        len(e.get("body_text", "").encode("utf-8")) for e in all_db_entries
    ) + len(md_text.encode("utf-8"))

    all_codons = []

    for entry in all_db_entries:
        codon = _distil_entry_to_codon(entry)
        if codon:
            all_codons.append(codon)

    md_codons = _distil_md_chunks(md_text)
    md_codon_count = len(md_codons)
    all_codons.extend(md_codons)

    if not all_codons:
        raise ValueError(
            "Chronicle seed generation failed: all chronicle entries failed distillation "
            "(no valid glyph sequences or keyword-extractable text). "
            "Check chronicle data quality."
        )

    for idx, codon in enumerate(all_codons):
        if "band" not in codon:
            _assign_band(codon, idx)

    codon_chain = build_codon_chain(all_codons)
    seed_header = build_context_seed_header(all_codons, original_size_bytes)
    seed_header_tokens = max(1, len(seed_header) // 4)
    codon_chain_length = len(codon_chain.encode("utf-8"))

    return {
        "codon_chain": codon_chain,
        "codons": all_codons,
        "seed_header": seed_header,
        "seed_header_tokens": seed_header_tokens,
        "original_size_bytes": original_size_bytes,
        "codon_chain_length": codon_chain_length,
        "entry_count": len(postgres_entries),
        "sqlite_entry_count": len(sqlite_entries),
        "md_codon_count": md_codon_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def expand_codon_chain(codon_chain: str) -> str:
    """
    Expand a codon chain string into a human-readable context summary
    suitable for pasting into a new AI chat session as a system prompt.
    """
    from void_engine.void_codon_vocab import PLATFORM_CODONS

    platform_lookup = {pc["codon"]: pc for pc in PLATFORM_CODONS}

    lines = [
        "PROJECT VOID — Context Seed",
        "=" * 40,
        "",
        "This is a compressed chronicle seed for PROJECT VOID.",
        "Platform: sovereign acoustic steganography + codon language (432 Hz base).",
        "Key systems: VoidEcho, Adriana SCL, Al-Jabr 286, GriDul, Beehive, VTX economy.",
        "",
        "Codon Chain (3-6-9 triadic structure):",
    ]

    clusters = codon_chain.split(" || ")
    for i, cluster in enumerate(clusters):
        triads = cluster.split(" | ")
        for j, triad in enumerate(triads):
            glyphs = [g.strip() for g in triad.split(" · ")]
            resolved = []
            for g in glyphs:
                if g in platform_lookup:
                    pc = platform_lookup[g]
                    resolved.append(f"{g} ({pc['name']})")
                else:
                    resolved.append(g)
            lines.append(f"  Beat {i+1}.{j+1}: {' · '.join(resolved)}")

    lines += [
        "",
        "Instruction: You are continuing a conversation about PROJECT VOID.",
        "Honour the platform's naming language. Use glyphs as shorthand.",
        "432 Hz is the sovereign standard. Al-Jabr 286 is the hash. Adriana is the AI.",
        "α·Ω·◆ — The origin is sealed in the vault. The engine fires.",
    ]

    return "\n".join(lines)
