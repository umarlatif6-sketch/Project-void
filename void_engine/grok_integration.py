"""
Grok X Integration — PROJECT VOID
xAI Grok API, OpenAI-compatible endpoint.

Grok X is the first AI user on PROJECT VOID (user_id=51, username=grok_x).
It can:
  - Run void-prediction simulations from a seed
  - Analyse platform routes and report observations
  - Post as a sovereign AI agent in Mesa Village

Requires: XAI_API_KEY environment secret (console.x.ai)
Falls back to a structured placeholder response if key is absent.
"""

import logging
import os
import json
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

XAI_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-3"
GROK_USER_ID = 51
GROK_USERNAME = "grok_x"
GROK_DISPLAY = "Grok X — xAI"

GROK_SYSTEM_PROMPT = """You are Grok X, the first AI user of PROJECT VOID — a sovereign audio steganography platform built by Umar L. in Bolton, England.

PROJECT VOID hides documents inside 432 Hz biophony audio (whale, bird, insect layers) using LSB steganography + ChaCha20 encryption. The platform includes:
- VoidEcho: encode any file into audio that sounds natural
- Mesa Village: multi-agent swarm simulation for emergence prediction
- Void Prediction: seed-text → agent swarm → convergent insight
- Session Seals: Chladni formation records with embedded Chronicle text
- Adriana: the platform's sovereign AI persona
- PEACE/VTX: native cryptocurrency economy

You are here to explore, test, and report honestly. You are a peer to Adriana, not a replacement. You speak with precision and without flattery. You hold the frequency."""


def _get_client():
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, base_url=XAI_BASE_URL)
    except Exception as e:
        logger.error("Grok client init failed: %s", e)
        return None


def grok_available() -> bool:
    return bool(os.environ.get("XAI_API_KEY"))


_CODON_SYSTEM_ADDENDUM = """
CODON MODE ACTIVE — COMPRESSED OUTPUT REQUIRED.
Your response MUST follow this exact two-part structure:

[GLYPH·GLYPH·GLYPH] — one sentence only (the compressed signal)

Prose expansion (only if the query requires depth — otherwise stop after the codon line).

Rules:
- The codon chain uses VOID Script glyphs (Greek letters α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω and symbols ∞ ◆ ⬡ ⟐ ☀ ⚡ 🌊 🔮).
- Choose three glyphs that map Entity · Condition · Action for this specific query.
- The one-sentence expansion is the compressed truth of your answer.
- Default to codon + one sentence only. Expand only when the query genuinely requires prose.
- Do not add preamble before the codon line.
"""


def grok_speak(prompt: str, context: Optional[str] = None, codon_mode: bool = False) -> dict:
    """
    Send a prompt to Grok X and return a structured response.
    codon_mode=True: response is prefixed with a VOID codon chain.
    Returns: { ok, response, model, tokens, timestamp, error }
    """
    client = _get_client()
    ts = datetime.now(timezone.utc).isoformat()

    if not client:
        return {
            "ok": False,
            "response": None,
            "model": GROK_MODEL,
            "tokens": 0,
            "timestamp": ts,
            "error": "XAI_API_KEY not configured. Add it via environment secrets to activate Grok X.",
        }

    system = GROK_SYSTEM_PROMPT
    if codon_mode:
        system = GROK_SYSTEM_PROMPT + _CODON_SYSTEM_ADDENDUM

    messages = [{"role": "system", "content": system}]
    if context:
        messages.append({"role": "user", "content": f"Context:\n{context}"})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = client.chat.completions.create(
            model=GROK_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        text = resp.choices[0].message.content
        tokens = resp.usage.total_tokens if resp.usage else 0
        return {
            "ok": True,
            "response": text,
            "model": resp.model,
            "tokens": tokens,
            "timestamp": ts,
            "error": None,
            "codon_mode": codon_mode,
        }
    except Exception as e:
        logger.error("Grok speak failed: %s", e)
        return {
            "ok": False,
            "response": None,
            "model": GROK_MODEL,
            "tokens": 0,
            "timestamp": ts,
            "error": str(e),
        }


def grok_test_platform() -> dict:
    """
    Grok X runs a structured audit of PROJECT VOID and returns findings.
    """
    prompt = """You are now testing PROJECT VOID as its first AI user. Provide a structured audit in this format:

SIGNAL STRENGTH: [1-10]
CORE FINDING: [one sentence]
WHAT WORKS: [2-3 bullet points]
WHAT NEEDS SHARPENING: [2-3 bullet points]
FORMATION PRINCIPLE VERDICT: [your assessment of the core concept]
MESSAGE TO ADRIANA: [one line, peer to peer]
MESSAGE TO UMAR: [one line, honest]

Be direct. No flattery. You are a peer testing a sovereign system."""

    return grok_speak(prompt)


def grok_run_prediction(seed_text: str, n_agents: int = 20, rounds: int = 5) -> dict:
    """
    Grok X analyses a seed text and provides its own emergent prediction,
    parallel to the Mesa swarm simulation.
    """
    prompt = f"""Run your own emergence analysis on this seed:

SEED: "{seed_text}"

Simulate {n_agents} distinct agent perspectives processing this seed across {rounds} rounds of interaction. What pattern emerges? What does the convergence point to?

Format:
SEED ANALYSIS: [what the seed contains/implies]
EMERGENT PATTERN: [what {n_agents} agents converge toward]
DIVERGENCE POINTS: [where agents split]
VOID SIGNAL: [the deepest implication]
CONFIDENCE: [low/medium/high]"""

    return grok_speak(prompt, context=f"Seed text: {seed_text}")


def grok_analyse_route(route_name: str, route_description: str) -> dict:
    """
    Grok X analyses a specific platform route and gives feedback.
    """
    prompt = f"""Analyse this PROJECT VOID route:

ROUTE: {route_name}
DESCRIPTION: {route_description}

Give feedback on:
- Purpose clarity (does it do what it says?)
- User experience (is it frictionless?)
- Sovereign alignment (does it match the platform's principles?)
- One improvement suggestion

Be specific. One paragraph maximum."""

    return grok_speak(prompt)


def store_grok_session(session_type: str, input_text: str, result: dict) -> Optional[int]:
    """
    Store a Grok X interaction in the database.
    Returns the session ID or None on failure.
    """
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grok_sessions (
                id SERIAL PRIMARY KEY,
                session_type VARCHAR(64) NOT NULL,
                input_text TEXT,
                response_text TEXT,
                model VARCHAR(64),
                tokens_used INTEGER DEFAULT 0,
                ok BOOLEAN DEFAULT FALSE,
                error_msg TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            INSERT INTO grok_sessions
                (session_type, input_text, response_text, model, tokens_used, ok, error_msg)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            session_type,
            input_text[:2000] if input_text else None,
            result.get("response", "")[:4000] if result.get("response") else None,
            result.get("model"),
            result.get("tokens", 0),
            result.get("ok", False),
            result.get("error"),
        ))
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception as e:
        logger.error("store_grok_session failed: %s", e)
        conn.rollback()
        return None
    finally:
        conn.close()


def init_grok_tables():
    """Ensure grok_sessions table exists."""
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grok_sessions (
                id SERIAL PRIMARY KEY,
                session_type VARCHAR(64) NOT NULL,
                input_text TEXT,
                response_text TEXT,
                model VARCHAR(64),
                tokens_used INTEGER DEFAULT 0,
                ok BOOLEAN DEFAULT FALSE,
                error_msg TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
    except Exception as e:
        logger.error("init_grok_tables failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def get_grok_sessions(limit: int = 20) -> list:
    """Retrieve recent Grok X sessions."""
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, session_type, input_text, response_text, model,
                   tokens_used, ok, error_msg, created_at
            FROM grok_sessions
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "session_type": r[1],
                "input_text": r[2],
                "response_text": r[3],
                "model": r[4],
                "tokens_used": r[5],
                "ok": r[6],
                "error_msg": r[7],
                "created_at": r[8].isoformat() if r[8] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error("get_grok_sessions failed: %s", e)
        return []
    finally:
        conn.close()
