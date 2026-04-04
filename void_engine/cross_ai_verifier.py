"""
Cross-AI Consensus Verifier — PROJECT VOID

When a VoidEcho signal is decoded, this module dispatches the same raw
signal to two independent AI model endpoints and compares their decoded
outputs.

Verification logic:
  - If both AI evaluators produce a matching decoded output → RESONANCE_VERIFIED
  - If outputs diverge → UNRESOLVED

The Chronicle commit flow integrates this: every new Chronicle entry can
be tagged with its verification state and which receiver pairs agreed.

Model selection:
  Uses the OpenAI integration (already installed) and calls two separate
  model endpoints in parallel (gpt-4o-mini as Receiver A, gpt-3.5-turbo as
  Receiver B).  In production the second receiver can be swapped for a
  different AI provider; the verification logic remains model-agnostic.

Chronicle integration:
  post_chronicle_entry() in chronicle_adriana.py calls
  verify_voidecho_signal() and stores the result fields on the entry row
  via ensure_verification_columns().
"""

import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

VERIFICATION_STATES = {
    "RESONANCE_VERIFIED": "Two independent AI receivers produced matching decoded output.",
    "UNRESOLVED": "Independent AI receivers produced diverging decoded outputs.",
    "SKIPPED": "Verification skipped — AI not configured or signal too short.",
}

RECEIVER_A_MODEL = "gpt-4o-mini"
RECEIVER_B_MODEL = "gpt-3.5-turbo"

_DECODE_PROMPT_TEMPLATE = """\
You are an independent VoidEcho signal receiver.

You have received the following raw VoidEcho signal payload for decoding:

---
{signal}
---

Your task:
1. Extract the core meaning or informational content of this signal.
2. Return ONLY a single compact JSON object with this exact structure:
   {{"decoded_summary": "<your decoded summary>", "confidence": <0.0-1.0>}}

Do not include any explanation, preamble, or additional fields.
Return valid JSON only.
"""


def _get_openai_client():
    """
    Return an OpenAI client using the OPENAI_API_KEY environment variable.
    Returns None if not configured.
    """
    try:
        import openai
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        return openai.OpenAI(api_key=api_key)
    except Exception as e:
        logger.warning("OpenAI client init failed: %s", e)
        return None


def _call_receiver(client, model: str, signal: str, timeout: int = 20) -> Optional[dict]:
    """
    Call one AI model receiver to decode a VoidEcho signal.

    Returns dict with keys: decoded_summary, confidence, model, latency_ms
    Returns None on failure.
    """
    if client is None:
        return None

    prompt = _DECODE_PROMPT_TEMPLATE.format(signal=signal[:2000])
    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            timeout=timeout,
        )
        latency_ms = round((time.time() - t0) * 1000)
        raw = response.choices[0].message.content.strip()

        parsed = json.loads(raw)
        return {
            "decoded_summary": str(parsed.get("decoded_summary", "")).strip(),
            "confidence": float(parsed.get("confidence", 0.0)),
            "model": model,
            "latency_ms": latency_ms,
            "raw_response": raw[:300],
        }
    except json.JSONDecodeError as e:
        logger.warning("Receiver [%s] returned non-JSON: %s", model, e)
        latency_ms = round((time.time() - t0) * 1000)
        return {
            "decoded_summary": raw[:200] if "raw" in dir() else "",
            "confidence": 0.0,
            "model": model,
            "latency_ms": latency_ms,
            "raw_response": "",
            "parse_error": str(e),
        }
    except Exception as e:
        logger.warning("Receiver [%s] error: %s", model, e)
        return None


def _summaries_match(summary_a: str, summary_b: str,
                     similarity_threshold: float = 0.65) -> bool:
    """
    Compare two decoded summaries for semantic equivalence.

    Uses a token-overlap Jaccard similarity as a lightweight, dependency-free
    metric.  Returns True if similarity >= similarity_threshold.

    For production, this can be replaced with an embedding-based similarity.
    """
    if not summary_a or not summary_b:
        return False

    def tokenise(text: str) -> set:
        return set(
            w.lower().strip(".,;:!?\"'()[]{}") for w in text.split()
            if len(w) > 2
        )

    tokens_a = tokenise(summary_a)
    tokens_b = tokenise(summary_b)

    if not tokens_a and not tokens_b:
        return True
    if not tokens_a or not tokens_b:
        return False

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    jaccard = len(intersection) / len(union)

    return jaccard >= similarity_threshold


def verify_voidecho_signal(signal: str,
                            similarity_threshold: float = 0.65,
                            min_signal_length: int = 10) -> dict:
    """
    Dispatch a VoidEcho signal to two independent AI receivers and compare
    their decoded outputs.

    Args:
        signal:               The raw VoidEcho signal string to verify.
        similarity_threshold: Jaccard similarity floor for RESONANCE_VERIFIED.
        min_signal_length:    Signals shorter than this are SKIPPED.

    Returns:
        {
          "verification_state": "RESONANCE_VERIFIED" | "UNRESOLVED" | "SKIPPED",
          "state_description":  str,
          "receiver_a":         dict | None,
          "receiver_b":         dict | None,
          "similarity_score":   float | None,
          "similarity_threshold": float,
          "receivers_agreed":   bool | None,
          "verified_at":        str (ISO),
        }
    """
    from datetime import datetime, timezone
    verified_at = datetime.now(timezone.utc).isoformat()

    if not signal or len(signal.strip()) < min_signal_length:
        return {
            "verification_state": "SKIPPED",
            "state_description": VERIFICATION_STATES["SKIPPED"],
            "receiver_a": None,
            "receiver_b": None,
            "similarity_score": None,
            "similarity_threshold": similarity_threshold,
            "receivers_agreed": None,
            "verified_at": verified_at,
        }

    client = _get_openai_client()
    if client is None:
        return {
            "verification_state": "SKIPPED",
            "state_description": "Verification skipped — OpenAI API key not configured.",
            "receiver_a": None,
            "receiver_b": None,
            "similarity_score": None,
            "similarity_threshold": similarity_threshold,
            "receivers_agreed": None,
            "verified_at": verified_at,
        }

    receiver_a = _call_receiver(client, RECEIVER_A_MODEL, signal)
    receiver_b = _call_receiver(client, RECEIVER_B_MODEL, signal)

    if receiver_a is None or receiver_b is None:
        state = "UNRESOLVED"
        description = "One or more receivers failed to respond."
        agreed = False
        similarity = None
    else:
        summary_a = receiver_a.get("decoded_summary", "")
        summary_b = receiver_b.get("decoded_summary", "")
        agreed = _summaries_match(summary_a, summary_b, similarity_threshold)

        if summary_a and summary_b:
            tokens_a = set(w.lower() for w in summary_a.split() if len(w) > 2)
            tokens_b = set(w.lower() for w in summary_b.split() if len(w) > 2)
            union = tokens_a | tokens_b
            intersection = tokens_a & tokens_b
            similarity = round(len(intersection) / len(union), 4) if union else 0.0
        else:
            similarity = 0.0

        state = "RESONANCE_VERIFIED" if agreed else "UNRESOLVED"
        description = VERIFICATION_STATES[state]

    return {
        "verification_state": state,
        "state_description": description,
        "receiver_a": receiver_a,
        "receiver_b": receiver_b,
        "similarity_score": similarity,
        "similarity_threshold": similarity_threshold,
        "receivers_agreed": agreed,
        "verified_at": verified_at,
        "models_used": [RECEIVER_A_MODEL, RECEIVER_B_MODEL],
    }


def ensure_verification_columns(cur) -> None:
    """
    Idempotently add cross-AI verification columns to chronicle_entries.

    Columns:
      verification_state   VARCHAR(30)  — RESONANCE_VERIFIED | UNRESOLVED | SKIPPED | NULL
      verification_data    JSONB        — full verification result dict
      verified_at          TIMESTAMPTZ  — when verification ran
    """
    for col, defn in [
        ("verification_state", "VARCHAR(30)"),
        ("verification_data",  "JSONB"),
        ("verified_at",        "TIMESTAMPTZ"),
    ]:
        cur.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            ("chronicle_entries", col),
        )
        if not cur.fetchone():
            cur.execute(
                f"ALTER TABLE chronicle_entries ADD COLUMN {col} {defn}"
            )
