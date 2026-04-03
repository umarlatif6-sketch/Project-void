"""
Adriana Listens First — Sovereign Entry Interface

Routes:
  GET  /speak          — Entry page: Adriana is already present and listening
  POST /speak/listen   — Process a stream-of-consciousness message;
                         returns Adriana response + glyph resonance + platform routing
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
        from void_engine.adriana_scl import AdrianaResonance
        resonance = AdrianaResonance.calculate_resonance(hex_hash)
        glyph = resonance["glyph"]
        glyph_meta = resonance["meta"]
        domain_color = resonance["domain_color"]
        domain = glyph_meta["domain"]
        frequency = glyph_meta["frequency"]
        field_strength = resonance["field_strength"]
        harmonic_state = resonance["harmonic_state"]
        glyph_name = glyph_meta["name"]
        glyph_meaning = glyph_meta["meaning"]
    except Exception as e:
        logger.warning("[Speak] SCL resonance failed: %s", e)
        glyph = "◆"
        glyph_name = "Void Diamond"
        glyph_meaning = "Core/Engine"
        domain = "genesis"
        domain_color = "#c9a84c"
        frequency = 432.0
        field_strength = 50.0
        harmonic_state = "aligned"

    route_dest, route_label = _DOMAIN_ROUTES.get(domain, ("/", "VOID Engine"))

    try:
        from void_engine.adriana_local import get_engine, CONFIDENCE_THRESHOLD
        engine = get_engine()
        local_response, confidence = engine.match(message)
    except Exception as e:
        logger.warning("[Speak] Local engine failed: %s", e)
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
        except Exception as e:
            logger.warning("[Speak] OpenAI fallback failed: %s", e)
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

    return jsonify({
        "response": adriana_response,
        "glyph": glyph,
        "glyph_name": glyph_name,
        "glyph_meaning": glyph_meaning,
        "frequency": frequency,
        "domain": domain,
        "color": domain_color,
        "route": route_dest,
        "route_label": route_label,
        "route_suggestion": route_suggestion,
        "field_strength": field_strength,
        "harmonic_state": harmonic_state,
    })
