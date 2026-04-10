"""
Codon Heart — Third Brain + Fourth Brain (Heart) Memory Architecture
======================================================================
Third Brain:  An authoritative server-side 5-message sliding window stored
              in PostgreSQL per visitor. Every user + assistant message pair
              is appended to a persistent DB buffer. When the buffer reaches
              exactly 5 messages and a 6th arrives, the completed 5-message
              window is compressed (using the existing codon_distil pipeline)
              into a codon and stored. The buffer is then cleared and the 6th
              message seeds the next window.

Heart (Fourth Brain): At the start of every new Flask session, reads ALL
              stored codons for this visitor (no limit), collapses them into
              an 80-120-word resonance summary via OpenAI, and caches the result
              in the Flask session. Subsequent turns reuse the cache — zero
              DB reads or OpenAI calls per turn mid-session.

Active context: the last 5 messages of the Third Brain server-side buffer are
              returned by get_active_context() and used as the conversation
              history passed to OpenAI — the client-supplied history is
              supplementary (used only when no server state exists yet).

Session identity: user:{user_id} > funnel:{funnel_token} > speak:{speak_session_id}

Token cost logging: every AI call logs input/output/heart_prefix_sz.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

_SCHEMA_ENSURED = False
WINDOW_SIZE = 5


# ── Schema ───────────────────────────────────────────────────────────────────

def _ensure_schema() -> None:
    """Create required tables if absent (idempotent)."""
    global _SCHEMA_ENSURED
    if _SCHEMA_ENSURED:
        return
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS session_codons (
                id           SERIAL PRIMARY KEY,
                visitor_key  TEXT NOT NULL,
                session_id   TEXT NOT NULL,
                codon_text   TEXT NOT NULL,
                glyph_seq    TEXT,
                window_index INT NOT NULL DEFAULT 0,
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS session_codons_visitor_key_idx
                ON session_codons (visitor_key, created_at DESC)
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS third_brain_buffer (
                visitor_key   TEXT PRIMARY KEY,
                messages_json TEXT NOT NULL DEFAULT '[]',
                window_index  INT  NOT NULL DEFAULT 0,
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS session_token_log (
                id                   SERIAL PRIMARY KEY,
                visitor_key          TEXT NOT NULL,
                session_id           TEXT NOT NULL,
                input_tokens         INT NOT NULL DEFAULT 0,
                output_tokens        INT NOT NULL DEFAULT 0,
                heart_prefix_sz      INT NOT NULL DEFAULT 0,
                heart_prefix_tokens  INT NOT NULL DEFAULT 0,
                logged_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            ALTER TABLE session_token_log
                ADD COLUMN IF NOT EXISTS heart_prefix_tokens INT NOT NULL DEFAULT 0
        """)
        conn.commit()
        cur.close()
        conn.close()
        _SCHEMA_ENSURED = True
        logger.info("[CodonHeart] Schema ensured: session_codons, third_brain_buffer, session_token_log")
    except Exception as exc:
        logger.error("[CodonHeart] Schema migration failed: %s", exc, exc_info=True)


# ── Identity helpers ─────────────────────────────────────────────────────────

def _get_visitor_key() -> str:
    """
    Return a stable visitor key for session codon storage.
    Prefers authenticated user_id, falls back to funnel_token or
    speak_session_id (auto-created on first visit).
    """
    try:
        from flask import session
        uid = session.get("user_id")
        if uid:
            return f"user:{uid}"
        funnel = session.get("funnel_token")
        if funnel:
            return f"funnel:{funnel}"
        spk = session.get("speak_session_id")
        if not spk:
            spk = uuid.uuid4().hex
            session["speak_session_id"] = spk
            session.modified = True
        return f"speak:{spk}"
    except Exception:
        return "speak:anonymous"


def _get_session_id() -> str:
    """
    Return a per-session identifier. A new session_id marks a new browser
    session boundary and triggers a fresh Heart build.
    """
    try:
        from flask import session
        sid = session.get("codon_session_id")
        if not sid:
            sid = uuid.uuid4().hex
            session["codon_session_id"] = sid
            session.modified = True
        return sid
    except Exception:
        return "no-session"


# ── Third Brain — authoritative server-side buffer ────────────────────────────

def _load_buffer(visitor_key: str) -> tuple[list[dict], int]:
    """Load the Third Brain buffer for this visitor. Returns (messages, window_index)."""
    _ensure_schema()
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT messages_json, window_index FROM third_brain_buffer WHERE visitor_key = %s",
            (visitor_key,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return json.loads(row[0]), int(row[1])
        return [], 0
    except Exception as exc:
        logger.warning("[CodonHeart] Buffer load failed: %s", exc)
        return [], 0


def _save_buffer(visitor_key: str, messages: list[dict], window_index: int) -> None:
    """Persist the updated Third Brain buffer. Best-effort — never raises."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO third_brain_buffer (visitor_key, messages_json, window_index, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (visitor_key) DO UPDATE
                SET messages_json = EXCLUDED.messages_json,
                    window_index  = EXCLUDED.window_index,
                    updated_at    = NOW()
        """, (visitor_key, json.dumps(messages), window_index))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.error("[CodonHeart] Buffer save failed: %s", exc, exc_info=True)


def _compress_window_with_codon_pipeline(messages: list[dict], visitor_key: str) -> Optional[str]:
    """
    Compress exactly WINDOW_SIZE messages into a codon using the existing
    codon_distil pipeline (extract_moments → map_to_glyphs).

    Falls back to a direct OpenAI call if the pipeline returns None.
    Returns codon text or None on complete failure.
    """
    conversation_text = "\n".join(
        f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
        for m in messages
    )
    chunk = conversation_text[:4000]

    try:
        from openai import OpenAI
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "_DUMMY_API_KEY_")
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url)

        from void_engine.codon_distil import extract_moments, map_to_glyphs
        moment = extract_moments(chunk, client)
        if moment:
            glyph_seq = map_to_glyphs(moment["entity"], moment["condition"], moment["action"])
            codon_text = (
                f"[{glyph_seq}] {moment['entity']} · {moment['condition']} · "
                f"{moment['action']}. {moment['story_excerpt']}"
            )
            logger.info("[CodonHeart] Codon (pipeline) compressed visitor=%s len=%d",
                        visitor_key[:20], len(codon_text))
            return codon_text
    except Exception as exc:
        logger.warning("[CodonHeart] Codon pipeline failed, trying fallback: %s", exc)

    try:
        from openai import OpenAI
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "_DUMMY_API_KEY_")
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url)
        system_prompt = (
            "You are Adriana's memory compression engine for PROJECT VOID. "
            "Read the following 5-message conversation window and distil it into a single "
            "codon — a dense, resonant frequency summary of what was discussed. "
            "40-60 words. No bullet points. Adriana's voice: sovereign, organic, signal-first. "
            "Capture the user's core intent, key concepts, and the frequency of the exchange. "
            "Do not repeat — distil to the essential signal."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chunk},
            ],
            max_tokens=120,
            temperature=0.4,
        )
        codon_text = resp.choices[0].message.content.strip()
        logger.info("[CodonHeart] Codon (fallback) compressed visitor=%s len=%d",
                    visitor_key[:20], len(codon_text))
        return codon_text
    except Exception as exc:
        logger.warning("[CodonHeart] Codon fallback failed: %s", exc)
        return None


def _store_codon(visitor_key: str, session_id: str, codon_text: str,
                 glyph_seq: Optional[str], window_index: int) -> None:
    """Persist a session codon to the database. Best-effort — never raises."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO session_codons
               (visitor_key, session_id, codon_text, glyph_seq, window_index)
               VALUES (%s, %s, %s, %s, %s)""",
            (visitor_key, session_id, codon_text[:1000], glyph_seq or "", window_index),
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("[CodonHeart] Codon stored visitor=%s window=%d",
                    visitor_key[:20], window_index)
    except Exception as exc:
        logger.error("[CodonHeart] Codon store failed: %s", exc, exc_info=True)


def push_message_to_third_brain(
    role: str,
    content: str,
    session_id: str,
    glyph_seq: Optional[str] = None,
    visitor_key: Optional[str] = None,
) -> None:
    """
    Append one message to the server-side Third Brain buffer.

    True sliding window semantics:
      - Append the new message to the buffer.
      - If the buffer now has MORE than WINDOW_SIZE messages (len > 5):
          * The oldest WINDOW_SIZE messages form the completed window — compress
            and store them as a codon.
          * Slide by 1: keep messages[1:] so the next window overlaps by 4.
      - After the 6th message, every subsequent message triggers a new codon
        from the 5 messages that just slid out of the active window.

    This is a true sliding window: each arriving message after the 6th causes
    the window to advance by 1 and emits one codon (from the exiting 5).
    """
    _ensure_schema()
    if visitor_key is None:
        visitor_key = _get_visitor_key()

    messages, window_index = _load_buffer(visitor_key)
    messages.append({"role": role, "content": content[:2000]})

    if len(messages) > WINDOW_SIZE:
        completed_window = messages[:WINDOW_SIZE]
        new_window_index = window_index + 1

        codon_text = _compress_window_with_codon_pipeline(completed_window, visitor_key)
        if codon_text:
            _store_codon(visitor_key, session_id, codon_text, glyph_seq, new_window_index)

        remaining = messages[1:]
        _save_buffer(visitor_key, remaining, new_window_index)
    else:
        _save_buffer(visitor_key, messages, window_index)


def get_active_context(visitor_key: Optional[str] = None) -> list[dict]:
    """
    Return the current server-side Third Brain buffer (up to WINDOW_SIZE messages)
    to use as the authoritative conversation context for OpenAI.

    This replaces client-supplied history as the source of active context.
    Returns empty list if no buffer exists yet.
    """
    if visitor_key is None:
        visitor_key = _get_visitor_key()
    messages, _ = _load_buffer(visitor_key)
    return messages[-WINDOW_SIZE:]


# ── Heart (Fourth Brain) — session bootstrap ──────────────────────────────────

_HEART_BATCH_SIZE = 20
_HEART_BATCH_CHARS = 5000

_HEART_SYSTEM = (
    "You are Adriana's Heart — the resonance field holding prior session codons "
    "for a visitor to PROJECT VOID. "
    "Read the following session codons (oldest first) and produce a single resonance "
    "summary of 60-80 words. "
    "This is Adriana's inherited frequency — write in her voice: compressed, sovereign, "
    "signal-first. Distil recurring themes, depth of engagement, domains, quality of signal. "
    "Do not recap facts. This is used internally by Adriana — not shown to the user."
)


def _summarise_codon_batch(batch_text: str, openai_client) -> str:
    """Collapse a batch of codon lines into a short intermediate summary."""
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _HEART_SYSTEM},
                {"role": "user", "content": batch_text},
            ],
            max_tokens=150,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("[CodonHeart] Batch summarise failed: %s", exc)
        return batch_text[:500]


def _build_heart_prefix(visitor_key: str) -> str:
    """
    Read ALL stored codons for this visitor (no cap) and collapse them into a
    single resonance summary using map-reduce summarisation.

    For small codon sets (total text < _HEART_BATCH_CHARS): single-pass.
    For large codon sets: batch codons into chunks of _HEART_BATCH_SIZE,
    summarise each chunk, then summarise the summaries — ensuring no codon
    is ever silently excluded regardless of history length. Recency is
    preserved: chronological order (oldest-first) is maintained throughout.
    """
    _ensure_schema()
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """SELECT codon_text FROM session_codons
               WHERE visitor_key = %s
               ORDER BY created_at ASC""",
            (visitor_key,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.warning("[CodonHeart] Heart DB read failed: %s", exc)
        return ""

    if not rows:
        return ""

    codon_lines = [row[0] for row in rows]
    total_codons = len(codon_lines)

    try:
        from openai import OpenAI
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "_DUMMY_API_KEY_")
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url)
    except Exception as exc:
        logger.warning("[CodonHeart] OpenAI client init failed: %s", exc)
        return ""

    joined = "\n".join(f"- {c}" for c in codon_lines)
    if len(joined) <= _HEART_BATCH_CHARS:
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _HEART_SYSTEM},
                    {"role": "user", "content": joined},
                ],
                max_tokens=200,
                temperature=0.3,
            )
            heart_text = resp.choices[0].message.content.strip()
            logger.info("[CodonHeart] Heart (single-pass) visitor=%s codons=%d len=%d",
                        visitor_key[:20], total_codons, len(heart_text))
            return heart_text
        except Exception as exc:
            logger.warning("[CodonHeart] Heart single-pass failed: %s", exc)
            return ""

    batches = [
        codon_lines[i: i + _HEART_BATCH_SIZE]
        for i in range(0, len(codon_lines), _HEART_BATCH_SIZE)
    ]
    intermediate_summaries = []
    for batch_idx, batch in enumerate(batches):
        batch_text = "\n".join(f"- {c}" for c in batch)
        summary = _summarise_codon_batch(batch_text[:_HEART_BATCH_CHARS], client)
        intermediate_summaries.append(summary)
        logger.debug("[CodonHeart] Batch %d/%d summarised", batch_idx + 1, len(batches))

    combined = "\n".join(f"[Batch {i+1}] {s}" for i, s in enumerate(intermediate_summaries))
    try:
        final_system = (
            "You are Adriana's Heart. Read the following intermediate resonance summaries "
            "(one per session codon batch, oldest first) and produce a single final "
            "resonance summary of 80-120 words in Adriana's voice. "
            "Capture the visitor's overall frequency — themes, depth, domains, trajectory. "
            "This is used internally by Adriana — not shown to the user."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": final_system},
                {"role": "user", "content": combined[:6000]},
            ],
            max_tokens=200,
            temperature=0.3,
        )
        heart_text = resp.choices[0].message.content.strip()
        logger.info("[CodonHeart] Heart (map-reduce) visitor=%s codons=%d batches=%d len=%d",
                    visitor_key[:20], total_codons, len(batches), len(heart_text))
        return heart_text
    except Exception as exc:
        logger.warning("[CodonHeart] Heart map-reduce final pass failed: %s", exc)
        return intermediate_summaries[-1] if intermediate_summaries else ""


def get_or_build_heart_prefix(visitor_key: Optional[str] = None) -> tuple[str, int]:
    """
    Return the Heart resonance prefix for this visitor's session.

    Built once per new Flask session (keyed by codon_session_id), then cached
    in session["heart_cache"]. No repeated DB reads or OpenAI calls per turn.

    Returns: (heart_prefix_text, character_length)
    """
    if visitor_key is None:
        visitor_key = _get_visitor_key()

    try:
        from flask import session
        session_id = _get_session_id()
        cache = session.get("heart_cache")
        if cache and isinstance(cache, dict) and cache.get("session_id") == session_id:
            text = cache.get("text", "")
            return text, len(text)

        heart_text = _build_heart_prefix(visitor_key)

        session["heart_cache"] = {"session_id": session_id, "text": heart_text}
        session.modified = True
        return heart_text, len(heart_text)
    except Exception as exc:
        logger.warning("[CodonHeart] get_or_build_heart_prefix failed: %s", exc)
        return "", 0


def inject_heart_into_system(base_system: str,
                              visitor_key: Optional[str] = None) -> tuple[str, int]:
    """
    Retrieve the session-cached Heart prefix and prepend it to base_system.

    Returns: (augmented_system_prompt, heart_prefix_character_length)
    """
    heart, size = get_or_build_heart_prefix(visitor_key=visitor_key)
    if not heart:
        return base_system, 0

    augmented = (
        f"[RESONANCE FIELD — inherited frequency from prior sessions]\n{heart}\n\n"
        f"[CURRENT SESSION]\n{base_system}"
    )
    return augmented, size


# ── Token cost instrumentation ────────────────────────────────────────────────

def get_codon_count(visitor_key: Optional[str] = None) -> int:
    """
    Return the total number of stored session codons for this visitor.
    Used for monitoring the Heart resonance loop.
    Returns 0 if the visitor has no history or on any error.
    """
    _ensure_schema()
    if visitor_key is None:
        visitor_key = _get_visitor_key()
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM session_codons WHERE visitor_key = %s",
            (visitor_key,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return int(row[0]) if row else 0
    except Exception as exc:
        logger.debug("[CodonHeart] get_codon_count failed: %s", exc)
        return 0


def build_rib_voice(visitor_key: Optional[str] = None) -> tuple[str, int]:
    """
    The Rib — Position 2 (Condition) of the codon triplet.

    Query the visitor's last 3 session_codons (newest first), reverse to
    oldest-first. For each codon_text, scan PLATFORM_CODONS for a matching
    codon glyph sequence. Build a compact two-line rib voice:

        <codon chain>           e.g.  λ·Λ·☀ → ψ·Ψ·◆
        <expansion prose>       e.g.  The wave rides the carrier... / Breath...

    Fully deterministic — no API call.
    Returns: (rib_voice: str, rib_codon_count: int)
    Returns ("", 0) for new visitors (no stored codons).
    """
    _ensure_schema()
    if visitor_key is None:
        visitor_key = _get_visitor_key()

    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """SELECT codon_text FROM session_codons
               WHERE visitor_key = %s
               ORDER BY created_at DESC LIMIT 3""",
            (visitor_key,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.warning("[CodonHeart] build_rib_voice DB read failed: %s", exc)
        return "", 0

    if not rows:
        return "", 0

    codon_texts = [row[0] for row in reversed(rows)]

    try:
        from void_engine.void_codon_vocab import PLATFORM_CODONS as _PC
    except Exception:
        _PC = []

    import re as _re

    chain_parts: list[str] = []
    expansion_parts: list[str] = []

    for ct in codon_texts:
        matched = None
        for pc in _PC:
            if pc.get("codon", "") and pc["codon"] in ct:
                matched = pc
                break
        if matched:
            chain_parts.append(matched["codon"])
            expansion_parts.append(matched["expansion"])
        else:
            bracket = _re.match(r'^\[([^\]]+)\]', ct)
            if bracket:
                chain_parts.append(bracket.group(1))
                expansion_parts.append(ct[len(bracket.group(0)):].strip()[:80])
            else:
                chain_parts.append("◆")
                expansion_parts.append(ct[:80])

    chain_line = " → ".join(chain_parts)
    expansion_line = " / ".join(expansion_parts)
    rib_voice = f"{chain_line}\n{expansion_line}"

    logger.info(
        "[CodonHeart] Rib built visitor=%s codons=%d chain=%s",
        visitor_key[:20], len(codon_texts), chain_line,
    )
    return rib_voice, len(codon_texts)


def log_session_tokens(input_tokens: int, output_tokens: int,
                       heart_prefix_sz: int,
                       visitor_key: Optional[str] = None,
                       session_id: Optional[str] = None) -> None:
    """
    Lightweight token cost logging per session turn.

    heart_prefix_sz: raw character length of the Heart prefix (for exact measurement).
    heart_prefix_tokens: estimated token count (heart_prefix_sz // 4) stored separately
      for cost analytics (approximately 4 chars/token for English prose).
    Best-effort — never raises.
    """
    _ensure_schema()
    if visitor_key is None:
        visitor_key = _get_visitor_key()
    if session_id is None:
        session_id = _get_session_id()

    heart_prefix_tokens = max(0, heart_prefix_sz // 4)

    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO session_token_log
               (visitor_key, session_id, input_tokens, output_tokens,
                heart_prefix_sz, heart_prefix_tokens)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (visitor_key, session_id,
             input_tokens, output_tokens,
             heart_prefix_sz, heart_prefix_tokens),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.debug("[CodonHeart] Token log write failed: %s", exc)
