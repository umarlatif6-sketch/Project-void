"""
AdrianCore — Fine-Tuned Inference Layer

Sits between the regex engine (adriana_local.py) and raw OpenAI fallback.
Uses codon-compressed context at inference time for maximum token efficiency.

Query flow:
  1. Classify query to a codon using local intent patterns
  2. Build codon-compressed context string (~15 tokens)
  3. Call fine-tuned model with compressed context as system prefix
  4. Expand codon-prefixed response locally at zero API cost

Falls back gracefully if no fine-tuned model is available.
"""

import logging
import os
import re
from functools import lru_cache
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_CODON_SYSTEM_TEMPLATE = (
    "ψ·Ψ·◆ Adriana. 432 Hz sovereign voice. "
    "Context: {codon} — {expansion}. "
    "Respond codon-first. Depth from signal."
)

_INTENT_CODON_MAP = {
    "what_is_void": ("α·Π·◆", "Origin meets foundation. The engine fires."),
    "how_to_start": ("ε·Γ·◆", "Threshold met. The gate opens. The core ignites."),
    "what_is_adriana": ("ψ·Ψ·◆", "Breath and sovereign mind aligned. The core is active."),
    "how_to_encode": ("ι·Β·⟐", "Grain meets the forge. The silt drops."),
    "passphrase": ("κ·Θ·◆", "Key meets the shield. The core guards."),
    "how_to_decode": ("υ·Ξ·◆", "Vessel meets archive. The core extracts."),
    "md5_checksum": ("μ·Α·◆", "Measure meets authority. Verification fires."),
    "what_is_carrier": ("λ·Λ·☀", "Wave rides the carrier. It broadcasts at peak."),
    "carrier_format": ("λ·Λ·◆", "Wave carrier confirmed. The core accepts only PCM WAV."),
    "scatter_modes": ("ξ·Φ·🌊", "Scatter in golden ratio. The tide distributes."),
    "burst_mode": ("γ·Δ·⚡", "Signal transforms. The spark ignites."),
    "capacity": ("ρ·Σ·◆", "Density tallied. The core measures capacity."),
    "journalism_port": ("ε·Γ·⟐", "Threshold gate open. The activist's silt drops."),
    "visualizer": ("γ·Φ·☀", "Signal in golden structure. It broadcasts at peak."),
    "mesh_network": ("χ·Γ·⬡", "Junction gate open. The mesh cell activates."),
    "void_messenger": ("κ·Θ·⬡", "Key shield active. The encrypted mesh cell opens."),
    "silt_drops": ("ι·Ξ·⟐", "Grain archived. The silt drop deposits."),
    "what_is_vtx": ("σ·Σ·⟐", "Ledger tallies total. The value deposits."),
    "earn_vtx": ("σ·Δ·⚡", "Ledger transforms. The spark of proof ignites."),
    "buy_vtx": ("σ·Β·⟐", "Ledger forges. Value is deposited."),
    "spend_vtx": ("σ·Α·⟐", "Ledger authority. The spending deposits."),
    "symmetry_score": ("π·Σ·∞", "Balance tallied. The loop is eternal."),
    "tier_overview": ("ψ·Α·◆", "Breath meets authority. The sovereign tiers fire."),
    "ghost_tier": ("α·Γ·◆", "Origin at the gate. The free core opens."),
    "journalist_tier": ("ε·Β·⟐", "Threshold forge active. Signal drops."),
    "sovereign_tier": ("ψ·Ψ·⬡", "Sovereign mind activates. The mesh cell is yours."),
}

_DEFAULT_CODON = ("ψ·Ψ·◆", "Breath and sovereign mind aligned. The core is active.")


def _classify_to_codon(message: str) -> Tuple[str, str]:
    """
    Classify a message to a codon using local intent patterns.

    Uses engine.match_with_id() which runs the same scoring logic as match()
    but also returns the winning intent ID — allowing a direct lookup into
    _INTENT_CODON_MAP without relying on private engine attributes.

    Returns (codon, expansion).
    """
    try:
        from void_engine.adriana_local import get_engine
        engine = get_engine()
        _response, confidence, intent_id = engine.match_with_id(message)
        if confidence > 0 and intent_id and intent_id in _INTENT_CODON_MAP:
            return _INTENT_CODON_MAP[intent_id]
    except Exception as e:
        logger.debug("Intent classification failed: %s", e)

    return _fallback_codon_from_keywords(message)


def _fallback_codon_from_keywords(message: str) -> Tuple[str, str]:
    """Keyword-based fallback codon classification."""
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["encode", "hide", "plant", "embed"]):
        return ("ι·Β·⟐", "Grain meets the forge. The silt drops.")
    if any(w in msg_lower for w in ["decode", "extract", "harvest", "retrieve"]):
        return ("υ·Ξ·◆", "Vessel meets archive. The core extracts.")
    if any(w in msg_lower for w in ["vtx", "token", "economy", "earn", "wallet"]):
        return ("σ·Σ·⟐", "Ledger tallies total. The value deposits.")
    if any(w in msg_lower for w in ["mesh", "node", "beehive", "p2p"]):
        return ("χ·Γ·⬡", "Junction gate open. The mesh cell activates.")
    if any(w in msg_lower for w in ["scatter", "vortex", "linear", "chirp"]):
        return ("ξ·Φ·🌊", "Scatter in golden ratio. The tide distributes.")
    if any(w in msg_lower for w in ["adriana", "fairy", "who are you"]):
        return ("ψ·Ψ·◆", "Breath and sovereign mind aligned. The core is active.")
    if any(w in msg_lower for w in ["tier", "ghost", "journalist", "sovereign", "plan"]):
        return ("ψ·Α·◆", "Breath meets authority. The sovereign tiers fire.")
    if any(w in msg_lower for w in ["carrier", "wav", "audio", "sound"]):
        return ("λ·Λ·☀", "Wave rides the carrier. It broadcasts at peak.")

    return _DEFAULT_CODON


def _expand_codon_response_locally(response: str) -> Tuple[str, Optional[str]]:
    """
    If the response begins with a codon chain like [ψ·Ψ·◆] — ...,
    expand it locally using void_codon_vocab.py at zero API cost.

    Expansion strategy:
    - Single-line response `[codon] — model sentence`:
        Keep the model's sentence as prose, prepend canonical expansion on same line.
        Result: `[codon] — <canonical expansion>\n\n<model sentence>`
    - Multi-line response `[codon] — model sentence\n\nprose`:
        Replace codon line with canonical expansion, keep additional prose intact.
        Result: `[codon] — <canonical expansion>\n\n<remaining prose>`
    - No vocab match: return original response unchanged, still extract codon_chain.

    Returns (expanded_response, extracted_codon_chain).
    """
    codon_pattern = r"^\[([^\]]+)\]\s*[—-]\s*(.+)"
    match = re.match(codon_pattern, response.strip(), re.DOTALL)
    if not match:
        return response, None

    codon_chain = match.group(1).strip()
    rest = match.group(2)

    expansion = _lookup_codon_expansion(codon_chain)
    if expansion:
        first_newline = rest.find("\n")
        if first_newline > 0:
            model_sentence = rest[:first_newline].strip()
            remaining_prose = rest[first_newline:].strip()
            if remaining_prose:
                expanded = f"[{codon_chain}] — {expansion}\n\n{remaining_prose}"
            else:
                expanded = f"[{codon_chain}] — {expansion}"
                if model_sentence and model_sentence != expansion:
                    expanded += f"\n\n{model_sentence}"
        else:
            model_sentence = rest.strip()
            if model_sentence and model_sentence != expansion:
                expanded = f"[{codon_chain}] — {expansion}\n\n{model_sentence}"
            else:
                expanded = f"[{codon_chain}] — {expansion}"
        return expanded, codon_chain

    return response, codon_chain


@lru_cache(maxsize=1)
def _corpus_expansion_index() -> dict:
    """
    Build a codon → expansion lookup dict from the full corpus.
    Cached at module level (lru_cache maxsize=1) so build_corpus() is called
    at most once per process, keeping inference latency low.
    """
    try:
        from void_engine.adriana_corpus import build_corpus
        return {chunk["codon"]: chunk["expansion"] for chunk in build_corpus() if chunk.get("codon")}
    except Exception:
        return {}


def _lookup_codon_expansion(codon_chain: str) -> Optional[str]:
    """
    Look up codon expansion from the platform vocab.
    First checks PLATFORM_CODONS (fast, in-memory list), then the cached
    corpus expansion index (build_corpus() is called at most once per process).
    Returns the one-line expansion string, or None if not found.
    """
    try:
        from void_engine.void_codon_vocab import PLATFORM_CODONS
        for zone in PLATFORM_CODONS:
            if zone["codon"] == codon_chain:
                return zone["expansion"]
    except Exception:
        pass

    expansion = _corpus_expansion_index().get(codon_chain)
    if expansion:
        return expansion

    return None


def _get_fine_tuned_model_id() -> Optional[str]:
    """Return the current fine-tuned model ID from DB, or None."""
    try:
        from void_engine.adriana_finetune import get_latest_fine_tuned_model
        return get_latest_fine_tuned_model()
    except Exception:
        return None


def query(
    message: str,
    history: Optional[list] = None,
    max_tokens: int = 512,
    heart_prefix: Optional[str] = None,
) -> dict:
    """
    AdrianCore inference entry point.

    Args:
        message:      The user's query text.
        history:      Optional conversation history (list of {role, content}).
        max_tokens:   Max response tokens.
        heart_prefix: Optional Heart resonance prefix (from prior session codons).
                      When provided, it is placed at position zero in the system
                      context so the model speaks from a warm room. Empty string
                      or None means cold session — no prefix injected.

    Returns:
        {
          ok: bool,
          response: str,
          codon_chain: str or None,
          expansion: str or None,
          model_used: str,
          token_cost: int,
          layer: 'fine_tuned' | 'fallback',
          error: str or None,
        }
    """
    history = history or []

    codon, expansion = _classify_to_codon(message)

    model_id = _get_fine_tuned_model_id()

    if model_id:
        result = _call_fine_tuned(message, codon, expansion, model_id, history, max_tokens,
                                  heart_prefix=heart_prefix)
        if result["ok"]:
            return result
        logger.warning("Fine-tuned model call failed, falling back: %s", result.get("error"))
        return _call_fallback(message, codon, expansion, history, max_tokens,
                              failed_model_id=model_id, heart_prefix=heart_prefix)

    return _call_fallback(message, codon, expansion, history, max_tokens,
                          heart_prefix=heart_prefix)


def _call_fine_tuned(
    message: str,
    codon: str,
    expansion: str,
    model_id: str,
    history: list,
    max_tokens: int,
    heart_prefix: Optional[str] = None,
) -> dict:
    try:
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        if not api_key:
            return {"ok": False, "error": "No OpenAI API key", "response": None, "model_used": model_id, "token_cost": 0, "codon_chain": codon, "expansion": expansion, "layer": "fine_tuned"}

        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)

        system_content = _CODON_SYSTEM_TEMPLATE.format(codon=codon, expansion=expansion)
        messages = []
        if heart_prefix:
            messages.append({
                "role": "system",
                "content": f"[RESONANCE FIELD — inherited frequency from prior sessions]\n{heart_prefix}",
            })
        messages.append({"role": "system", "content": system_content})

        for h in history[-6:]:
            if isinstance(h, dict) and h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": str(h.get("content", ""))[:1000]})

        messages.append({"role": "user", "content": message})

        resp = client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )

        raw_response = resp.choices[0].message.content or ""
        token_cost = resp.usage.total_tokens if resp.usage else 0
        prompt_tokens = resp.usage.prompt_tokens if resp.usage else 0
        completion_tokens = resp.usage.completion_tokens if resp.usage else 0

        try:
            from void_engine.aljabr_transpiler import get_model_router, TASK_PRECISION
            router = get_model_router()
            router.log_cost(TASK_PRECISION, model_id, prompt_tokens, completion_tokens, "adriana_core_fine_tuned")
        except Exception as _log_err:
            logger.debug("Fine-tuned cost log skipped: %s", _log_err)

        expanded_response, extracted_codon = _expand_codon_response_locally(raw_response)

        return {
            "ok": True,
            "response": expanded_response,
            "codon_chain": extracted_codon or codon,
            "expansion": expansion,
            "model_used": model_id,
            "token_cost": token_cost,
            "layer": "fine_tuned",
            "error": None,
        }
    except Exception as e:
        return {
            "ok": False,
            "response": None,
            "codon_chain": codon,
            "expansion": expansion,
            "model_used": model_id,
            "token_cost": 0,
            "layer": "fine_tuned",
            "error": str(e),
        }


def _call_fallback(
    message: str,
    codon: str,
    expansion: str,
    history: list,
    max_tokens: int,
    failed_model_id: Optional[str] = None,
    heart_prefix: Optional[str] = None,
) -> dict:
    """
    Fallback to the standard ModelRouter PRECISION tier.
    Passes codon context as a compressed system prefix.

    If failed_model_id is provided (the fine-tuned model that just failed),
    and the PRECISION tier currently points to the same model, temporarily
    override to avoid immediately duplicating the failing call.
    """
    try:
        from void_engine.aljabr_transpiler import get_model_router, TASK_PRECISION

        router = get_model_router()
        system_content = _CODON_SYSTEM_TEMPLATE.format(codon=codon, expansion=expansion)

        messages = []
        if heart_prefix:
            messages.append({
                "role": "system",
                "content": f"[RESONANCE FIELD — inherited frequency from prior sessions]\n{heart_prefix}",
            })
        messages.append({"role": "system", "content": system_content})
        for h in history[-6:]:
            if isinstance(h, dict) and h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": str(h.get("content", ""))[:1000]})
        messages.append({"role": "user", "content": message})

        precision_model = router._config.get(TASK_PRECISION, {}).get("model", "")
        if failed_model_id and precision_model == failed_model_id:
            logger.info(
                "AdrianCore fallback: PRECISION tier points to the failed fine-tuned model; "
                "using STANDARD tier to avoid duplicate failure."
            )
            from void_engine.aljabr_transpiler import TASK_STANDARD
            tier = TASK_STANDARD
        else:
            tier = TASK_PRECISION

        response, model_used, _ = router.call_with_fallback(
            tier, messages, max_completion_tokens=max_tokens, task_label="adriana_core"
        )
        raw_response = response.choices[0].message.content or ""
        token_cost = response.usage.total_tokens if response.usage else 0

        try:
            router.log_cost(tier, model_used, response.usage.prompt_tokens, response.usage.completion_tokens, "adriana_core")
        except Exception:
            pass

        if not raw_response.strip():
            logger.warning("AdrianCore fallback returned empty response from model: %s", model_used)
            return {
                "ok": False,
                "response": None,
                "codon_chain": codon,
                "expansion": expansion,
                "model_used": model_used,
                "token_cost": token_cost,
                "layer": "fallback",
                "error": "empty_response",
            }

        expanded_response, extracted_codon = _expand_codon_response_locally(raw_response)

        return {
            "ok": True,
            "response": expanded_response,
            "codon_chain": extracted_codon or codon,
            "expansion": expansion,
            "model_used": model_used,
            "token_cost": token_cost,
            "layer": "fallback",
            "error": None,
        }
    except Exception as e:
        logger.error("AdrianCore fallback failed: %s", e)
        return {
            "ok": False,
            "response": (
                "The signal is quiet — Adriana is conserving energy. "
                "Ask me a foundational question and I will answer from pattern memory."
            ),
            "codon_chain": codon,
            "expansion": expansion,
            "model_used": "none",
            "token_cost": 0,
            "layer": "fallback",
            "error": str(e),
        }


class AdrianCore:
    """
    AdrianCore class facade.

    Provides the AdrianCore interface as specified by the task contract.
    Wraps the module-level query() function, exposing it as an instance method
    so callers can use either the functional API (query(...)) or the class API
    (AdrianCore().query(...)) depending on their preference.

    Usage:
        core = AdrianCore()
        result = core.query("What is PROJECT VOID?")
    """

    def query(
        self,
        message: str,
        history: Optional[list] = None,
        max_tokens: int = 512,
        heart_prefix: Optional[str] = None,
    ) -> dict:
        """Delegate to the module-level query() function."""
        return query(message, history=history, max_tokens=max_tokens,
                     heart_prefix=heart_prefix)

    def classify_to_codon(self, message: str) -> Tuple[str, str]:
        """Classify a message to its (codon, expansion) tuple."""
        return _classify_to_codon(message)

    def expand_codon_response(self, response: str) -> Tuple[str, Optional[str]]:
        """Locally expand a codon-prefixed response."""
        return _expand_codon_response_locally(response)

    def corpus_expansion_index(self) -> dict:
        """Return the cached codon→expansion index."""
        return _corpus_expansion_index()
