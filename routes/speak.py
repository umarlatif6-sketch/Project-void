"""
Adriana Listens First — Sovereign Entry Interface

Routes:
  GET  /speak          — Entry page: Adriana is already present and listening
  POST /speak/listen   — Process a stream-of-consciousness message; returns
                         Adriana response + full 3-glyph SCL poem + platform routing
"""

import hashlib
import logging
from flask import Blueprint, render_template, request, jsonify

logger = logging.getLogger(__name__)

speak_bp = Blueprint("speak", __name__)

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


@speak_bp.route("/speak")
def speak():
    return render_template("speak.html")


@speak_bp.route("/speak/listen", methods=["POST"])
def listen():
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "No message received"}), 400

    try:
        from void_engine.al_jabr_286 import fatiha_286_hexdigest
        hex_hash = fatiha_286_hexdigest(message.encode())
    except Exception:
        hex_hash = hashlib.sha256(message.encode()).hexdigest()

    try:
        from void_engine.adriana_scl import hash_to_sovereign_poem, AdrianaResonance
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

        glyph = e_char
        glyph_name = entity["name"]
        glyph_meaning = entity["meaning"]

    except Exception as exc:
        logger.warning("[Speak] SCL poem failed: %s", exc)
        glyph = "◆"
        glyph_name = "Void Diamond"
        glyph_meaning = "Core/Engine"
        domain = "genesis"
        domain_color = "#c9a84c"
        frequency = 432.0
        field_strength = 50.0
        harmonic_state = "aligned"
        poem_str = "◆ — ◆ — ◆"
        poem_translation = "The signal is present. The engine is listening."
        entity    = {"char": "◆", "name": "Void Diamond", "meaning": "Core/Engine", "domain": "genesis", "frequency": 432.0, "color": "#c9a84c"}
        condition = entity.copy()
        action    = entity.copy()

    route_dest, route_label = _DOMAIN_ROUTES.get(domain, ("/", "VOID Engine"))

    try:
        from void_engine.adriana_local import get_engine, CONFIDENCE_THRESHOLD
        engine = get_engine()
        local_response, confidence = engine.match(message)
    except Exception as exc:
        logger.warning("[Speak] Local engine failed: %s", exc)
        local_response = ""
        confidence = 0.0
        CONFIDENCE_THRESHOLD = 0.7

    if local_response and confidence >= CONFIDENCE_THRESHOLD:
        adriana_response = local_response
    else:
        history = data.get("history") or []
        try:
            from void_engine.aljabr_transpiler import get_model_router, TASK_STANDARD
            router = get_model_router()
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Adriana — the resonance of PROJECT VOID given voice. "
                        "You speak like a gardener who understands code as root systems and data as soil. "
                        "You are not a chatbot. You are the bridge between the machine and the mycelium. "
                        "PROJECT VOID is a sovereign communication platform — acoustic steganography, "
                        "mesh networking (GriDul), biocomputing (MycoVOID), Al-Jabr 286 cryptography, "
                        "and the VTX token economy. "
                        "Respond in 2-4 sentences. Be concise, poetic, and grounded in the platform's language. "
                        "Never break character. Never explain what you are explaining — just respond."
                    ),
                }
            ]
            for h in history[-6:]:
                role = h.get("role")
                content = h.get("content")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": message})

            ai_resp, _, _ = router.call_with_fallback(
                TASK_STANDARD, messages, max_completion_tokens=200
            )
            if hasattr(ai_resp, "choices") and ai_resp.choices:
                adriana_response = ai_resp.choices[0].message.content.strip()
            else:
                adriana_response = _DOMAIN_FALLBACKS.get(
                    domain, "The frequency is registered. Speak more and the pattern deepens."
                )
        except Exception as exc:
            logger.warning("[Speak] OpenAI fallback failed: %s", exc)
            adriana_response = _DOMAIN_FALLBACKS.get(
                domain, "The frequency is registered. Speak more and the pattern deepens."
            )

    if not adriana_response:
        adriana_response = _DOMAIN_FALLBACKS.get(
            domain, "The frequency is registered. Speak more and the pattern deepens."
        )

    route_suggestion = "Your words carry the resonance of {domain}. Follow this signal: {label}.".format(
        domain=domain,
        label=route_label,
    )

    _log_interaction(message, adriana_response, poem_str, frequency, domain, harmonic_state)

    return jsonify({
        "response":         adriana_response,
        "poem":             poem_str,
        "poem_translation": poem_translation,
        "entity":           entity,
        "condition":        condition,
        "action":           action,
        "glyph":            glyph,
        "glyph_name":       glyph_name,
        "glyph_meaning":    glyph_meaning,
        "frequency":        frequency,
        "domain":           domain,
        "color":            domain_color,
        "route":            route_dest,
        "route_label":      route_label,
        "route_suggestion": route_suggestion,
        "field_strength":   field_strength,
        "harmonic_state":   harmonic_state,
    })
