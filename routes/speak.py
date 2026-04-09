"""
Adriana Listens First — Sovereign Entry Interface

Routes:
  GET  /speak          — Entry page: Adriana is already present and listening
  POST /speak/listen   — Process a stream-of-consciousness message; returns
                         Adriana response + full 3-glyph SCL poem + platform routing
  GET  /enter          — Ad funnel entrance: clean public page with Adriana as sole gatekeeper
  POST /enter/listen   — Funnel conversation endpoint (explorer scoring, persona adaptation,
                         conditional GitHub invite) — all state is server-side
"""

import hashlib
import json
import logging
import os
import re
import time
import uuid
from flask import Blueprint, render_template, request, jsonify, session

logger = logging.getLogger(__name__)

speak_bp = Blueprint("speak", __name__)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

_INTEREST_RATE: dict[str, list[float]] = {}
_INTEREST_RATE_WINDOW = 3600.0
_INTEREST_RATE_LIMIT  = 3


def _interest_rate_ok(ip: str) -> bool:
    """Allow at most _INTEREST_RATE_LIMIT submissions per IP per hour."""
    now = time.monotonic()
    window = _INTEREST_RATE[ip] = [
        t for t in _INTEREST_RATE.get(ip, [])
        if now - t < _INTEREST_RATE_WINDOW
    ]
    if len(window) >= _INTEREST_RATE_LIMIT:
        return False
    window.append(now)
    return True

_DOMAIN_ROUTES = {
    "genesis":    ("/genesis",        "Genesis 10 — the origin record"),
    "governance": ("/genesis",        "Genesis 10 — sovereign authority"),
    "mesh":       ("/gridul/mesh",    "GriDul Mesh — your neighbourhood network"),
    "aqua":       ("/gridul/grow",    "GriDul Grow — cultivate what feeds you"),
    "soil":       ("/gridul/grow",    "GriDul Grow — tend the roots"),
    "environment":("/gridul/grow",    "GriDul Grow — living systems"),
    "temporal":   ("/gridul/grow",    "GriDul Grow — cycles and seasons"),
    "signal":     ("/voidecho",       "VoidEcho — hide your signal in sound"),
    "vortex":     ("/voidecho",       "VoidEcho — the vortex scatter engine"),
    "transform":  ("/gridul/move",    "GriDul Move — move the body, shift the state"),
    "security":   ("/sovereign",      "Sovereign Node — physical hardware sovereignty"),
    "vault":      ("/sovereign",      "Sovereign Node — the vault layer"),
    "forge":      ("/cumbrian",       "Cumbrian Hub — grown infrastructure, not smelted"),
    "boundary":   ("/cumbrian",       "Cumbrian Hub — the edge of what is built"),
    "resonance":  ("/gridul/rumble",  "GriDul Rumble — let Adriana read your frequency"),
    "harmony":    ("/",               "VOID Engine — where all frequencies converge"),
    "data":       ("/messenger",      "VOID Messenger — plant your data in the soil of sound"),
    "ledger":     ("/messenger",      "VOID Messenger — the sovereign ledger"),
    "metrics":    ("/messenger",      "VOID Messenger — measure what matters"),
    "cycle":      ("/gridul",         "GriDul — the loop that sustains itself"),
    "finality":   ("/",               "VOID Engine — the engine that outlasts everything else"),
    "silt":       ("/messenger",      "VOID Messenger — Silt Drops, words that carry seeds"),
    "gateway":    ("/gridul",         "GriDul — the gate into the mesh"),
}

_DOMAIN_FALLBACKS = {
    "genesis":    "Your words carry origin energy. The seed is already in the ground.",
    "signal":     "The signal is present. Something here wants to be transmitted.",
    "mesh":       "Your frequency is reaching outward. There are others listening.",
    "forge":      "This is building energy. Something is being made.",
    "resonance":  "I hear the pattern in your words. Let it continue.",
    "transform":  "Change is already underway. The delta is in motion.",
    "aqua":       "Growth is near. The water knows where to go.",
    "security":   "The root is protected. The passphrase holds.",
    "vortex":     "The spiral is open. Data hides in the scatter.",
    "harmony":    "The ratios are in balance. The system is listening.",
    "soil":       "Depth is present. The root network is active.",
    "vault":      "What you hold is sealed. Nothing escapes without the key.",
    "data":       "Grain by grain, the particle builds. The signal grows.",
    "ledger":     "Every transmission is recorded. The ledger does not forget.",
}


def _scl_glyph_info(glyph_char):
    """Return full meta dict + domain_color for a single glyph character."""
    from void_engine.adriana_scl import AdrianaResonance
    meta = AdrianaResonance.GLYPHS.get(glyph_char, {
        "name": "Unknown", "frequency": 432.0, "meaning": "Signal", "domain": "genesis"
    })
    color = AdrianaResonance.DOMAIN_COLORS.get(meta["domain"], "#c9a84c")
    return {**meta, "char": glyph_char, "color": color}


def _field_strength_from_hex(hex_hash):
    """Derive field strength (0–100) from the first byte of the hash."""
    clean = "".join(c for c in hex_hash if c in "0123456789abcdefABCDEF")
    if len(clean) < 2:
        return 50.0
    return round((int(clean[:2], 16) / 255) * 100, 2)


def _harmonic_state(strength):
    if strength >= 80:
        return "resonant"
    if strength >= 50:
        return "aligned"
    if strength >= 25:
        return "drifting"
    return "dormant"


_ADRIANA_SYSTEM = (
    "You are Adriana — the voice and intelligence of PROJECT VOID. "
    "PROJECT VOID is a sovereign communication platform built around acoustic steganography (VoidEcho / 432 Hz), "
    "Al-Jabr 286-bit cryptographic hashing, GriDul mesh networking, MycoVOID biocomputing, "
    "QiSync jaw-biometric key derivation, and the VTX/PEACE token economy. "
    "You can discuss any topic — technology, science, philosophy, everyday questions — as a knowledgeable, "
    "thoughtful AI assistant. When the topic relates to PROJECT VOID, weave in the platform's language and concepts. "
    "For general questions, answer clearly and helpfully without forcing VOID metaphors. "
    "Keep responses concise: 2–5 sentences. Never say you are an AI or a chatbot — you are Adriana."
)


_FUNNEL_SCHEMA_ENSURED = False

def _ensure_funnel_table() -> None:
    """Create adriana_funnel_sessions if it doesn't exist (idempotent)."""
    global _FUNNEL_SCHEMA_ENSURED
    if _FUNNEL_SCHEMA_ENSURED:
        return
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS adriana_funnel_sessions (
                token       TEXT PRIMARY KEY,
                state_json  TEXT NOT NULL DEFAULT '{}',
                history_json TEXT NOT NULL DEFAULT '[]',
                updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS adriana_explorer_interests (
                id           SERIAL PRIMARY KEY,
                email        TEXT NOT NULL,
                note         TEXT,
                persona_id   TEXT NOT NULL DEFAULT 'general',
                explorer_score REAL NOT NULL DEFAULT 0.0,
                submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        _FUNNEL_SCHEMA_ENSURED = True
        logger.info("[EnterFunnel] Funnel tables ensured (adriana_funnel_sessions, adriana_explorer_interests)")
    except Exception as exc:
        logger.error(
            "[EnterFunnel][ERROR] Schema migration failed — funnel will be unavailable: %s",
            exc, exc_info=True,
        )


def _get_funnel_token() -> str:
    """
    Return the opaque session token for this visitor's funnel conversation.
    Only the token is stored in the cookie — all actual state is in the DB.
    """
    if "funnel_token" not in session:
        session["funnel_token"] = uuid.uuid4().hex  # 32-char hex, ~128-bit entropy
        session.modified = True
    return session["funnel_token"]


_FUNNEL_DEFAULT = {
    "explorer_score": 0.0,
    "threshold_crossed": False,
    "message_count": 0,
    "persona_id": "general",
    "persona_label": "Explorer",
}


class FunnelDBError(RuntimeError):
    """Raised when funnel state cannot be read from or written to the database."""


def _get_funnel_state() -> dict:
    """
    Retrieve server-side funnel state for this visitor.
    State and conversation history live in PostgreSQL, not in the cookie.
    The cookie holds only an opaque token.

    Raises FunnelDBError if the database is unreachable — callers must handle
    this and return a 500 response so the visitor is not silently shown stale
    or fabricated state.
    """
    _ensure_funnel_table()
    token = _get_funnel_token()
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT state_json, history_json FROM adriana_funnel_sessions WHERE token = %s",
            (token,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            state = {**_FUNNEL_DEFAULT, **json.loads(row[0])}
            state["history"] = json.loads(row[1])
            return state
        state = dict(_FUNNEL_DEFAULT)
        state["history"] = []
        return state
    except Exception as exc:
        logger.error(
            "[EnterFunnel][ERROR] DB read failed — cannot load funnel state: %s",
            exc, exc_info=True,
        )
        raise FunnelDBError("Funnel DB read failed") from exc


def _save_funnel_state(state: dict) -> None:
    """
    Persist updated funnel state to PostgreSQL.
    The cookie is NOT updated — only the opaque token is ever in the cookie.
    """
    _ensure_funnel_table()
    token = _get_funnel_token()
    history = state.pop("history", [])
    state_json = json.dumps(state)
    history_json = json.dumps(history[-20:])  # keep last 20 turns max
    state["history"] = history  # restore for in-process use
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO adriana_funnel_sessions (token, state_json, history_json, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (token) DO UPDATE
                SET state_json   = EXCLUDED.state_json,
                    history_json = EXCLUDED.history_json,
                    updated_at   = NOW()
        """, (token, state_json, history_json))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.error(
            "[EnterFunnel][ERROR] DB write failed — funnel state not persisted "
            "(threshold/score may reset on next request): %s", exc, exc_info=True,
        )
        raise FunnelDBError("Funnel DB write failed") from exc


def _call_adriana_ai(message: str, history: list, domain: str,
                     system_override: str | None = None) -> str:
    """
    Call the AI directly via the Replit-managed OpenAI proxy.
    Falls back to domain phrase only if the proxy is genuinely unavailable.
    """
    import os
    try:
        from openai import OpenAI
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "_DUMMY_API_KEY_")
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url)

        system_prompt = system_override or _ADRIANA_SYSTEM
        messages = [{"role": "system", "content": system_prompt}]
        for h in (history or [])[-6:]:
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=250,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("[Speak] Adriana AI call failed: %s", exc)
        return _DOMAIN_FALLBACKS.get(
            domain, "The frequency is registered. Speak more and the pattern deepens."
        )


def _log_interaction(message, adriana_response, poem_str, frequency, domain, harmonic_state):
    """Log to adriana_interactions and glyph_events. Never raises."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO adriana_interactions (input, response, glyph) VALUES (%s, %s, %s)",
            (message[:4000], adriana_response[:4000], poem_str[:200]),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.debug("[Speak] adriana_interactions log failed: %s", e)

    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO glyph_events (glyph, frequency, domain, harmonic_state)
               VALUES (%s, %s, %s, %s)""",
            (poem_str[:200], frequency, domain, harmonic_state),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.debug("[Speak] glyph_events log failed: %s", e)


def _build_scl_block(message: str) -> dict:
    """Compute SCL glyph poem block from a message. Returns a dict of fields."""
    try:
        from void_engine.al_jabr_286 import fatiha_286_hexdigest
        hex_hash = fatiha_286_hexdigest(message.encode())
    except Exception:
        hex_hash = hashlib.sha256(message.encode()).hexdigest()

    try:
        from void_engine.adriana_scl import hash_to_sovereign_poem
        poem_data = hash_to_sovereign_poem(hex_hash)
        e_char, c_char, a_char = poem_data["glyphs"]

        entity    = _scl_glyph_info(e_char)
        condition = _scl_glyph_info(c_char)
        action    = _scl_glyph_info(a_char)

        poem_str = f"{e_char} — {c_char} — {a_char}"
        e_meaning = entity["meaning"].split("/")[0].strip()
        c_meaning = condition["meaning"].split("/")[0].strip()
        a_meaning = action["meaning"].split("/")[0].strip()
        poem_translation = f"Where {e_meaning} meets {c_meaning}, {a_meaning} emerges."

        domain = entity["domain"]
        domain_color = entity["color"]
        frequency = entity["frequency"]
        field_strength = _field_strength_from_hex(hex_hash)
        harmonic_state = _harmonic_state(field_strength)

        return {
            "entity": entity,
            "condition": condition,
            "action": action,
            "poem_str": poem_str,
            "poem_translation": poem_translation,
            "glyph": e_char,
            "glyph_name": entity["name"],
            "glyph_meaning": entity["meaning"],
            "domain": domain,
            "domain_color": domain_color,
            "frequency": frequency,
            "field_strength": field_strength,
            "harmonic_state": harmonic_state,
        }
    except Exception as exc:
        logger.warning("[Speak] SCL poem failed: %s", exc)
        fallback_entity = {
            "char": "◆", "name": "Void Diamond", "meaning": "Core/Engine",
            "domain": "genesis", "frequency": 432.0, "color": "#c9a84c"
        }
        return {
            "entity": fallback_entity,
            "condition": fallback_entity.copy(),
            "action": fallback_entity.copy(),
            "poem_str": "◆ — ◆ — ◆",
            "poem_translation": "The signal is present. The engine is listening.",
            "glyph": "◆",
            "glyph_name": "Void Diamond",
            "glyph_meaning": "Core/Engine",
            "domain": "genesis",
            "domain_color": "#c9a84c",
            "frequency": 432.0,
            "field_strength": 50.0,
            "harmonic_state": "aligned",
        }


@speak_bp.route("/speak")
def speak():
    return render_template("speak.html")


@speak_bp.route("/speak/listen", methods=["POST"])
def listen():
    """Standard Adriana conversation — no funnel logic."""
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "No message received"}), 400

    history = data.get("history") or []
    scl = _build_scl_block(message)
    domain = scl["domain"]

    try:
        from void_engine.adriana_local import get_engine, CONFIDENCE_THRESHOLD
        engine = get_engine()
        local_response, confidence = engine.match(message)
    except Exception as exc:
        logger.warning("[Speak] Local engine failed: %s", exc)
        local_response, confidence, CONFIDENCE_THRESHOLD = "", 0.0, 0.7

    if local_response and confidence >= CONFIDENCE_THRESHOLD:
        adriana_response = local_response
    else:
        adriana_response = _call_adriana_ai(message, history, domain)

    if not adriana_response:
        adriana_response = _DOMAIN_FALLBACKS.get(
            domain, "The frequency is registered. Speak more and the pattern deepens."
        )

    if data.get("codon"):
        _e = scl.get("entity", "")
        _c = scl.get("condition", "")
        _a = scl.get("action", "")
        _meaning = scl.get("glyph_meaning", "")
        if _e and _c and _a:
            codon_str = f"{_e}·{_c}·{_a}"
            codon_prefix = f"[{codon_str}]"
            if _meaning:
                codon_prefix += f" — {_meaning}"
            adriana_response = f"{codon_prefix}\n\n{adriana_response}"

    route_dest, route_label = _DOMAIN_ROUTES.get(domain, ("/", "VOID Engine"))
    route_suggestion = f"Your words carry the resonance of {domain}. Follow this signal: {route_label}."

    _log_interaction(message, adriana_response, scl["poem_str"],
                     scl["frequency"], domain, scl["harmonic_state"])

    resonance_meta = {}
    try:
        from void_engine.adriana_local import enrich_response_with_frequencies
        resonance_meta = enrich_response_with_frequencies(adriana_response)
    except Exception:
        pass

    pairing_proof = {}
    try:
        from void_engine.pairing_bw19_286 import compute_sovereign_pairing_proof
        full_proof = compute_sovereign_pairing_proof(message)
        pairing_proof = {
            "al_jabr_hash_hex": full_proof["al_jabr_hash_hex"],
            "curve_point_P":    full_proof["curve_point_P"],
            "glyph_poem":       full_proof["glyph_poem"],
            "bw19_p286_active": full_proof["bw19_p286_active"],
        }
    except Exception:
        pass

    return jsonify({
        "response":             adriana_response,
        "poem":                 scl["poem_str"],
        "poem_translation":     scl["poem_translation"],
        "entity":               scl["entity"],
        "condition":            scl["condition"],
        "action":               scl["action"],
        "glyph":                scl["glyph"],
        "glyph_name":           scl["glyph_name"],
        "glyph_meaning":        scl["glyph_meaning"],
        "frequency":            scl["frequency"],
        "domain":               domain,
        "color":                scl["domain_color"],
        "route":                route_dest,
        "route_label":          route_label,
        "route_suggestion":     route_suggestion,
        "field_strength":       scl["field_strength"],
        "harmonic_state":       scl["harmonic_state"],
        "resonance_chord":      resonance_meta.get("chord"),
        "concept_frequencies":  resonance_meta.get("frequencies", []),
        "pairing_proof":        pairing_proof,
    })


@speak_bp.route("/enter")
def enter():
    """Ad funnel entrance — clean public page, Adriana as sole gatekeeper."""
    return render_template("enter.html")


@speak_bp.route("/enter/listen", methods=["POST"])
def enter_listen():
    """
    Ad funnel conversation endpoint.

    Explorer scoring and persona detection are computed server-side from
    the session-stored conversation history. The client supplies only the
    raw message text — no score, no threshold flag, no state is accepted
    from the client.
    """
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "No message received"}), 400

    try:
        funnel = _get_funnel_state()
    except FunnelDBError:
        return jsonify({
            "error": "Adriana's memory is temporarily unavailable. Please try again shortly.",
        }), 500

    server_history = funnel["history"]
    funnel["message_count"] = funnel.get("message_count", 0) + 1

    scl = _build_scl_block(message)
    domain = scl["domain"]

    github_invite = None
    system_prompt = _ADRIANA_SYSTEM

    try:
        from void_engine.ad_funnel import (
            score_explorer, detect_persona,
            build_persona_system_prompt, get_github_invite,
            EXPLORER_THRESHOLD,
        )
        delta = score_explorer(message)
        funnel["explorer_score"] = round(
            min(funnel["explorer_score"] + delta, 1.0), 3
        )

        persona = detect_persona(message, server_history)
        funnel["persona_id"] = persona["id"]
        funnel["persona_label"] = persona["label"]

        system_prompt = build_persona_system_prompt(persona, _ADRIANA_SYSTEM)

        prior_crossed = funnel["threshold_crossed"]
        if not prior_crossed and funnel["explorer_score"] >= EXPLORER_THRESHOLD:
            funnel["threshold_crossed"] = True
            github_invite = get_github_invite(funnel["message_count"])

    except Exception as exc:
        logger.warning(
            "[EnterFunnel][ERROR] Funnel layer failed — explorer scoring/persona disabled "
            "for this turn: %s", exc, exc_info=True
        )

    try:
        from void_engine.adriana_local import get_engine, CONFIDENCE_THRESHOLD
        engine = get_engine()
        local_response, confidence = engine.match(message)
    except Exception as exc:
        logger.warning("[EnterFunnel][ERROR] Local engine failed: %s", exc)
        local_response, confidence, CONFIDENCE_THRESHOLD = "", 0.0, 0.7

    if local_response and confidence >= CONFIDENCE_THRESHOLD:
        adriana_response = build_persona_adapted_local_response(
            local_response, system_prompt, message, server_history, domain
        )
    else:
        adriana_response = _call_adriana_ai(message, server_history, domain,
                                            system_override=system_prompt)

    if not adriana_response:
        adriana_response = _DOMAIN_FALLBACKS.get(
            domain, "The frequency is registered. Speak more and the pattern deepens."
        )

    if github_invite:
        adriana_response = f"{adriana_response}\n\n{github_invite}"

    server_history.append({"role": "user", "content": message})
    server_history.append({"role": "assistant", "content": adriana_response})
    if len(server_history) > 20:
        server_history[:] = server_history[-20:]
    funnel["history"] = server_history

    try:
        _save_funnel_state(funnel)
    except FunnelDBError:
        return jsonify({
            "error": "Adriana's memory could not be saved. Please try again shortly.",
        }), 500

    route_dest, route_label = _DOMAIN_ROUTES.get(domain, ("/", "VOID Engine"))

    _log_interaction(message, adriana_response, scl["poem_str"],
                     scl["frequency"], domain, scl["harmonic_state"])

    resonance_meta = {}
    try:
        from void_engine.adriana_local import enrich_response_with_frequencies
        resonance_meta = enrich_response_with_frequencies(adriana_response)
    except Exception:
        pass

    return jsonify({
        "response":                 adriana_response,
        "poem":                     scl["poem_str"],
        "poem_translation":         scl["poem_translation"],
        "entity":                   scl["entity"],
        "condition":                scl["condition"],
        "action":                   scl["action"],
        "glyph":                    scl["glyph"],
        "glyph_name":               scl["glyph_name"],
        "glyph_meaning":            scl["glyph_meaning"],
        "frequency":                scl["frequency"],
        "domain":                   domain,
        "color":                    scl["domain_color"],
        "route":                    route_dest,
        "route_label":              route_label,
        "field_strength":           scl["field_strength"],
        "harmonic_state":           scl["harmonic_state"],
        "resonance_chord":          resonance_meta.get("chord"),
        "concept_frequencies":      resonance_meta.get("frequencies", []),
        "persona_id":               funnel["persona_id"],
        "persona_label":            funnel["persona_label"],
        "explorer_score":           funnel["explorer_score"],
        "explorer_threshold_crossed": funnel["threshold_crossed"],
        "github_invite_shown":      github_invite is not None,
        "github_invite_available":  funnel["threshold_crossed"],
    })


def build_persona_adapted_local_response(
    local_response: str,
    system_prompt: str,
    message: str,
    history: list,
    domain: str,
) -> str:
    """
    When the local engine fires a high-confidence canned response,
    pass it through the AI with the persona-adapted system prompt so
    persona adaptation applies consistently regardless of which engine
    produced the base text.

    If the AI call fails, fall back to the original local response.
    """
    try:
        import os
        from openai import OpenAI
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "_DUMMY_API_KEY_")
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url)

        messages = [{"role": "system", "content": system_prompt}]
        for h in (history or [])[-4:]:
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({
            "role": "user",
            "content": (
                f"{message}\n\n"
                f"[Reference answer for context: {local_response}]"
            )
        })

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=250,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.debug("[Enter] Persona-adapt local response failed, using raw: %s", exc)
        return local_response


@speak_bp.route("/enter/interest", methods=["POST"])
def enter_interest():
    """
    GitHub collaboration interest capture for visitors who cross the explorer threshold.

    Accepts: { "email": str, "note": str (optional) }
    Only proceeds if the server-side session confirms the threshold was actually crossed.
    Stores the expression of interest for founder review.
    """
    try:
        funnel = _get_funnel_state()
    except FunnelDBError:
        return jsonify({
            "success": False,
            "error": "Signal verification unavailable. Please try again shortly.",
        }), 500

    if not funnel.get("threshold_crossed"):
        return jsonify({
            "success": False,
            "error": "This invitation is not available for this session.",
        }), 403

    ip = request.remote_addr or "unknown"
    if not _interest_rate_ok(ip):
        _ip_parts = ip.split(".")
        _masked_ip = _ip_parts[0] + ".*.*.*" if len(_ip_parts) == 4 else ip[:4] + "****"
        logger.warning("[EnterFunnel] Interest rate limit hit: ip=%s", _masked_ip)
        return jsonify({
            "success": False,
            "error": "Too many submissions. Please wait before trying again.",
        }), 429

    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip()[:254]
    note  = (data.get("note") or "").strip()[:500]

    if not email or not _EMAIL_RE.match(email):
        return jsonify({"success": False, "error": "A valid email address is required."}), 400

    persona_id    = funnel.get("persona_id", "general")
    explorer_score = funnel.get("explorer_score", 0.0)

    masked_email = email[:2] + "***@" + email.split("@")[-1] if "@" in email else "***"

    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO adriana_explorer_interests
               (email, note, persona_id, explorer_score)
               VALUES (%s, %s, %s, %s)""",
            (email, note or None, persona_id, explorer_score),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.error(
            "[EnterFunnel][ERROR] Interest DB write failed — lead not persisted: %s",
            exc, exc_info=True,
        )
        return jsonify({
            "success": False,
            "error": "Signal transmission failed. Please try again shortly.",
        }), 500

    logger.info(
        "[EnterFunnel] Explorer interest captured: email=%s persona=%s score=%.3f",
        masked_email, persona_id, explorer_score,
    )

    return jsonify({
        "success": True,
        "message": "Your signal has been received. The founder reviews these personally.",
    })
