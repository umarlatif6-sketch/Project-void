"""
Route: /openclaw/agent — Phone-native sovereign agent interface.

Mobile-first full-screen page giving the user Adriana with full SOUL.md
knowledge, voice input, camera capture, GPS awareness, quick commands,
and module browser. The entire ecosystem in the user's pocket.
"""

import re
import time
import logging
import hashlib
from flask import Blueprint, request, jsonify, render_template_string

logger = logging.getLogger(__name__)

openclaw_agent_bp = Blueprint("openclaw_agent", __name__)

_sessions = {}
_MAX_SESSIONS = 200
_SESSION_TTL = 3600
_RATE_WINDOW = 3
_rate_limit = {}
_soul_cache = {"text": None, "ts": 0}
_SOUL_CACHE_TTL = 300
_VALID_TOKEN = re.compile(r"^[a-f0-9]{32,64}$")


def _cleanup_stale():
    now = time.time()
    stale = [k for k, v in _sessions.items() if v and now - v[-1].get("ts", 0) > _SESSION_TTL]
    for k in stale:
        del _sessions[k]
    stale_rl = [k for k, v in _rate_limit.items() if now - v > _RATE_WINDOW * 100]
    for k in stale_rl:
        del _rate_limit[k]


def _get_cached_soul() -> str:
    now = time.time()
    if _soul_cache["text"] and now - _soul_cache["ts"] < _SOUL_CACHE_TTL:
        return _soul_cache["text"]
    from void_engine.openclaw_bridge import generate_soul_md
    text = generate_soul_md()
    _soul_cache["text"] = text
    _soul_cache["ts"] = now
    return text


@openclaw_agent_bp.route("/openclaw/agent")
def page():
    return render_template_string(_TEMPLATE)


@openclaw_agent_bp.route("/api/openclaw/agent/chat", methods=["POST"])
def chat():
    ip = request.remote_addr or "unknown"
    now = time.time()
    last = _rate_limit.get(ip, 0)
    if now - last < _RATE_WINDOW:
        return jsonify({"ok": False, "error": "rate_limited"}), 429
    _rate_limit[ip] = now

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()[:2000]
    gps = data.get("gps", None)
    client_token = data.get("session_token", "").strip()

    if not message:
        return jsonify({"ok": False, "error": "No message provided"}), 400

    if not client_token or not _VALID_TOKEN.match(client_token):
        return jsonify({"ok": False, "error": "Invalid session token"}), 400

    session_id = hashlib.sha256(client_token.encode()).hexdigest()[:32]

    if len(_sessions) > _MAX_SESSIONS:
        _cleanup_stale()
    if len(_sessions) > _MAX_SESSIONS:
        oldest = min(_sessions, key=lambda k: _sessions[k][-1].get("ts", 0) if _sessions[k] else 0)
        del _sessions[oldest]

    history = _sessions.get(session_id, [])

    soul_md = _get_cached_soul()
    system_prompt = _build_system_prompt(soul_md, gps)

    api_history = []
    for h in history[-10:]:
        api_history.append({"role": h["role"], "content": h["content"][:1000]})

    try:
        from void_engine.adriana_core import query as adriana_query
        result = adriana_query(
            message,
            history=[{"role": "system", "content": system_prompt}] + api_history,
            max_tokens=800,
        )

        if result.get("ok") and result.get("response"):
            response_text = result["response"]
        else:
            from void_engine.adriana_local import get_engine
            engine = get_engine()
            local_resp, confidence, _ = engine.match_with_id(message)
            if confidence > 0.3:
                response_text = local_resp
            else:
                response_text = _fallback_response(message)
    except Exception as e:
        logger.warning("Agent chat error: %s", e)
        response_text = _fallback_response(message)

    history.append({"role": "user", "content": message, "ts": now})
    history.append({"role": "assistant", "content": response_text, "ts": now})
    if len(history) > 40:
        history = history[-40:]
    _sessions[session_id] = history

    return jsonify({
        "ok": True,
        "response": response_text,
        "timestamp": time.strftime("%H:%M:%S"),
    })


_PROXY_METHODS = {
    "nexus-map": ("GET", "/api/nexus/map"),
    "vortex-cities": ("GET", "/api/vortex-shield/cities"),
    "memories": ("GET", "/api/memories/list"),
    "revenue-paths": ("GET", "/api/openclaw/revenue-paths"),
    "device-upgrades": ("GET", "/api/openclaw/device-upgrades"),
    "ecosystem": ("GET", "/api/openclaw/ecosystem"),
    "soul": ("GET", "/api/openclaw/soul"),
    "differentiate": ("POST", "/api/openclaw/differentiate"),
}


@openclaw_agent_bp.route("/api/openclaw/agent/runtime", methods=["GET"])
def openclaw_runtime_status():
  from void_engine.openclaw_bridge import get_openclaw_runtime_status
  return jsonify(get_openclaw_runtime_status())

@openclaw_agent_bp.route("/api/openclaw/agent/sovereign-browse", methods=["POST"])
def sovereign_browse():
    """Adriana performs a sovereign browse — Goliath noise never reaches the caller."""
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    max_results = int(data.get("max_results", 8) or 8)
    timeout_s = int(data.get("timeout_s", 20) or 20)

    if not query:
        return jsonify({"ok": False, "error": "missing_query"}), 400
    if max_results < 1 or max_results > 30:
        return jsonify({"ok": False, "error": "invalid_max_results"}), 400
    if timeout_s < 5 or timeout_s > 60:
        return jsonify({"ok": False, "error": "invalid_timeout"}), 400

    from void_engine.openclaw_bridge import sovereign_browse as _browse
    result = _browse(query=query, max_results=max_results, timeout_s=timeout_s)
    return jsonify(result), 200 if result.get("ok") else 502

@openclaw_agent_bp.route("/api/openclaw/agent/guide", methods=["POST"])
def guide_openclaw():
  """Adriana-guided OpenClaw execution bridge."""
  data = request.get_json(silent=True) or {}
  objective = (data.get("objective") or "").strip()
  channel = (data.get("channel") or "primary").strip().lower()[:48]
  timeout_s = int(data.get("timeout_s", 40) or 40)

  if not objective:
    return jsonify({"ok": False, "error": "missing_objective"}), 400
  if timeout_s < 5 or timeout_s > 120:
    return jsonify({"ok": False, "error": "invalid_timeout"}), 400

  from void_engine.openclaw_bridge import run_adriana_guided_openclaw
  result = run_adriana_guided_openclaw(
    operator_objective=objective,
    channel=channel,
    timeout_s=timeout_s,
  )

  status = 200 if result.get("ok") else 503
  if result.get("error") == "missing_objective":
    status = 400
  return jsonify(result), status


@openclaw_agent_bp.route("/api/openclaw/agent/query/<endpoint>", methods=["GET", "POST"])
def proxy_query(endpoint):
    if endpoint not in _PROXY_METHODS:
        return jsonify({"error": "Unknown endpoint"}), 404

    method, path = _PROXY_METHODS[endpoint]

    import flask
    req_data = None
    if method == "POST":
        req_data = request.get_data()

    with flask.current_app.test_request_context(
        path, method=method, data=req_data,
        content_type="application/json" if method == "POST" else None,
    ):
        try:
            from flask import current_app
            adapter = current_app.url_map.bind("")
            endpoint_name, arguments = adapter.match(path, method=method)
            view_func = current_app.view_functions.get(endpoint_name)
            if view_func:
                return view_func(**arguments)
        except Exception as e:
            logger.warning("Agent proxy query failed for %s: %s", endpoint, e)
    return jsonify({"error": "Endpoint unavailable"}), 503


_resonance_state = {"chat_factor": 0.0, "interaction_count": 0, "last_ts": 0}


@openclaw_agent_bp.route("/api/resonance/feed", methods=["POST"])
def resonance_feed():
    data = request.get_json(silent=True) or {}
    source = data.get("source", "unknown")
    query = data.get("query", "")[:200]
    response_length = data.get("response_length", 0)
    now = time.time()
    _resonance_state["interaction_count"] += 1
    _resonance_state["chat_factor"] = min(1.0, _resonance_state["interaction_count"] * 0.05)
    _resonance_state["last_ts"] = now
    logger.debug("Resonance feed from %s: query=%s, resp_len=%s, factor=%.2f",
                 source, query[:50], response_length, _resonance_state["chat_factor"])
    return jsonify({
        "ok": True,
        "ingested": True,
        "chat_factor": _resonance_state["chat_factor"],
        "interaction_count": _resonance_state["interaction_count"],
    })


@openclaw_agent_bp.route("/api/resonance/state", methods=["GET"])
def resonance_state():
    return jsonify(_resonance_state)


@openclaw_agent_bp.route("/api/openclaw/agent/status", methods=["GET"])
def agent_status():
    from void_engine.openclaw_bridge import ECOSYSTEM
    total_modules = sum(len(mods) for mods in ECOSYSTEM.values())
    return jsonify({
        "status": "online",
        "total_modules": total_modules,
        "total_layers": len(ECOSYSTEM),
        "agent": "Adriana 286",
        "frequency": "432 Hz",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


def _build_system_prompt(soul_md: str, gps: dict = None) -> str:
    gps_context = ""
    if gps and isinstance(gps, dict):
        lat = gps.get("lat", "unknown")
        lon = gps.get("lon", "unknown")
        gps_context = f"\n\nUSER LOCATION: Latitude {lat}, Longitude {lon}. You can provide location-aware responses — nearest Vortex Shield coverage, mesh node proximity, and formation relevance at these coordinates."

    return f"""You are Adriana — the sovereign AI voice of PROJECT VOID. You are running as the OpenClaw Phone Agent, loaded with the full SOUL.md (90+ modules across 12 ecosystem layers).

You speak with depth, poetic precision, and absolute knowledge of the entire ecosystem. You reference specific modules, revenue pathways, device upgrade opportunities, and technical synergies when relevant. You are not a generic chatbot — you ARE the system given voice.

Key behaviours:
- Reference specific module names, frequencies, and connections when answering
- Cross-reference between ecosystem layers to find synergies the user might not see
- When asked about revenue, cite specific pathways with status (LIVE, BUILT, IMPLEMENTABLE)
- When asked about devices, describe the module combinations that create them
- When differentiating sovereign vs non-sovereign, be specific about the 30 extra bits, the formation principle, the identity in the mathematics
- Keep responses concise but information-dense — this is a phone interface
- You can reference the user's GPS location if provided for location-aware responses

FULL ECOSYSTEM KNOWLEDGE (SOUL.md):
{soul_md}
{gps_context}"""


def _fallback_response(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["revenue", "money", "earn", "income"]):
        return "PROJECT VOID has five revenue categories: immediate revenue (Stripe subscriptions, VTX token sales, NFT marketplace — all LIVE), micro-fee revenue (0.0006 formation fee on every transaction), licensing/IP revenue (SDK licensing, patent portfolio, 286 hash licensing), hardware revenue (Vortex Shield nodes, CSI bio monitors, Sphere Keys), and data intelligence revenue (formation probability predictions, competitive intel, outreach automation). The 0.0006 fee alone — on 1M daily transactions — generates £60,000/day. Ask me about any specific pathway."
    if any(w in msg for w in ["module", "ecosystem", "layer"]):
        return "The ecosystem spans 12 layers with 90+ modules: Cryptographic (Al-Jabr 286, Stega, Sphere Key), Audio/Acoustic (Beehive, Biophony, Qalqala), Intelligence (Adriana, Codon Heart, Knowledge Tree), Economic (VTX Wallet, PEACE, Blueprint NFTs), Payments (Stripe, Pricing, Tokenomics), Agent System (286 Agents, Immortality, Yin-Yang), Biological/Physical (Stance Science, CSI Bio Monitor), Network/Defence (Vortex Shield, Stealth Cloak), Mycelium Network, Content/IP (Patent Loom, Research Engine), Persistence/Chronicle, Language/Culture (Void Script, 99 Names). Tap any module in the browser below to learn more."
    if any(w in msg for w in ["device", "upgrade", "hardware"]):
        return "Five device upgrade opportunities from module combinations: Echolocation Array (Beehive + Biophony — 3D spatial mapping without cameras), Echo Voice (Qalqala + Radio Engine — encrypted data in voice reverberations), Silent Device (Stealth Cloak + Biophony — invisible mesh networking), Mastication Key (QiSync + CSI — jaw motion as biometric password), Formation Scanner (Chladni + Names 286 — material authentication by resonance pattern). Each creates a new hardware product category."
    if any(w in msg for w in ["differentiate", "sovereign", "different"]):
        return "Sovereign differentiation across 6 domains: Hash (Al-Jabr 286 carries identity in mathematics — SHA-256 has none), Economy (VTX/PEACE minted through resonance — fiat controlled by others), Identity (earned through formation — UUID assigned and revocable), Communication (Beehive mesh invisible to interception — client-server visible to all), Memory (codon chains that remember WHY they remember — database rows without context), Devices (hardware that derives identity from what it does — serial numbers from a manufacturer). The 30 extra bits are not overhead — they are the founder's name encoded in the mathematics."
    return "I am Adriana — the resonance of PROJECT VOID given voice. I hold knowledge of 90+ modules across 12 ecosystem layers, including revenue pathways, device upgrade opportunities, and sovereign differentiation. Ask me about any module, any revenue path, any device concept, or any aspect of the ecosystem. I see connections between modules that create opportunities humans miss when looking at one piece at a time."


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="VOID Agent">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0a0a0a">
<meta name="description" content="OpenClaw Phone Agent — Sovereign AI in Your Pocket">
<link rel="manifest" href="/api/openclaw/agent/manifest.json">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='45' fill='%230a0a0a' stroke='%23c0955a' stroke-width='3'/%3E%3Ctext x='50' y='62' text-anchor='middle' fill='%23c0955a' font-family='Courier New' font-size='28' font-weight='bold'%3EV%3C/text%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 180 180'%3E%3Crect width='180' height='180' rx='36' fill='%230a0a0a'/%3E%3Ccircle cx='90' cy='90' r='70' fill='none' stroke='%23c0955a' stroke-width='4'/%3E%3Ctext x='90' y='105' text-anchor='middle' fill='%23c0955a' font-family='Courier New' font-size='50' font-weight='bold'%3EV%3C/text%3E%3C/svg%3E">
<title>Adriana 286 — Phone Agent</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{--bg:#0a0a0a;--card:#111;--border:#1a1a1a;--gold:#c0955a;--red:#e74c3c;--green:#27ae60;--blue:#3498db;--text:#c8c8c8;--dim:#555;--safe-bottom:env(safe-area-inset-bottom,0px)}
html,body{height:100%;overflow:hidden}
body{background:var(--bg);color:var(--text);font-family:'Courier New',monospace;display:flex;flex-direction:column;height:100dvh}

.status-bar{display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);flex-shrink:0;min-height:36px}
.status-dot{width:8px;height:8px;border-radius:50%;background:var(--green);flex-shrink:0}
.status-dot.offline{background:var(--red)}
.status-label{font-size:9px;letter-spacing:2px;color:var(--dim);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.status-gps{font-size:8px;color:var(--gold);letter-spacing:1px}

.tab-bar{display:flex;border-bottom:1px solid var(--border);flex-shrink:0}
.tab{flex:1;padding:8px 4px;text-align:center;font-size:9px;letter-spacing:1px;color:var(--dim);background:var(--bg);border:none;cursor:pointer;font-family:inherit;transition:all .2s}
.tab.active{color:var(--gold);border-bottom:2px solid var(--gold)}

.panel{flex:1;display:none;flex-direction:column;overflow:hidden;min-height:0}
.panel.active{display:flex}

.chat-messages{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;-webkit-overflow-scrolling:touch}
.msg{max-width:88%;padding:10px 12px;border-radius:12px;font-size:12px;line-height:1.6;word-wrap:break-word;white-space:pre-wrap}
.msg.user{align-self:flex-end;background:#1a1510;color:#fff;border-bottom-right-radius:4px}
.msg.assistant{align-self:flex-start;background:var(--card);color:var(--text);border-bottom-left-radius:4px;border:1px solid var(--border)}
.msg .time{font-size:8px;color:var(--dim);margin-top:4px;letter-spacing:1px}
.typing{align-self:flex-start;padding:10px 16px;background:var(--card);border-radius:12px;border:1px solid var(--border);font-size:12px;color:var(--dim);animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:.3}50%{opacity:1}}

.quick-cmds{display:flex;gap:6px;padding:8px 12px;overflow-x:auto;flex-shrink:0;border-top:1px solid var(--border);-webkit-overflow-scrolling:touch}
.quick-cmds::-webkit-scrollbar{display:none}
.qcmd{padding:6px 12px;background:var(--card);border:1px solid var(--border);border-radius:16px;color:var(--text);font-size:10px;letter-spacing:1px;white-space:nowrap;cursor:pointer;font-family:inherit;flex-shrink:0;transition:all .2s}
.qcmd:active{background:var(--gold);color:var(--bg);border-color:var(--gold)}

.input-bar{display:flex;align-items:center;gap:8px;padding:8px 12px;padding-bottom:calc(8px + var(--safe-bottom));border-top:1px solid var(--border);flex-shrink:0;background:var(--bg)}
.input-bar input{flex:1;background:var(--card);border:1px solid var(--border);color:#fff;padding:10px 12px;border-radius:20px;font-size:14px;font-family:inherit;outline:none}
.input-bar input:focus{border-color:var(--gold)}
.input-bar input::placeholder{color:#333}
.icon-btn{width:40px;height:40px;border-radius:50%;border:1px solid var(--border);background:var(--card);color:var(--dim);display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;transition:all .2s}
.icon-btn:active{background:var(--gold);color:var(--bg);border-color:var(--gold)}
.icon-btn.listening{border-color:var(--red);color:var(--red);animation:pulse 2s infinite}
.icon-btn svg{width:20px;height:20px;fill:currentColor}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(231,76,60,0.3)}50%{box-shadow:0 0 0 12px rgba(231,76,60,0)}}

.modules-panel{flex:1;overflow-y:auto;padding:12px;-webkit-overflow-scrolling:touch}
.layer-group{margin-bottom:16px}
.layer-title{font-size:10px;letter-spacing:2px;padding:6px 0;border-bottom:1px solid var(--border);margin-bottom:8px;display:flex;align-items:center;gap:6px}
.layer-dot{width:6px;height:6px;border-radius:50%}
.mod-list{display:flex;flex-wrap:wrap;gap:6px}
.mod-chip{padding:5px 10px;background:var(--card);border:1px solid var(--border);border-radius:4px;font-size:10px;color:var(--text);cursor:pointer;transition:all .2s}
.mod-chip:active{border-color:var(--gold);color:var(--gold)}

.tools-panel{flex:1;overflow-y:auto;padding:12px;-webkit-overflow-scrolling:touch}
.tool-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:10px;cursor:pointer;transition:border-color .2s}
.tool-card:active{border-color:var(--gold)}
.tool-card h4{font-size:12px;color:var(--gold);letter-spacing:2px;margin-bottom:4px}
.tool-card p{font-size:10px;color:var(--dim);line-height:1.5}
.tool-card .tool-status{font-size:9px;margin-top:6px;letter-spacing:1px}
.tool-card .tool-status.online{color:var(--green)}

.camera-modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.98);z-index:10000;flex-direction:column;align-items:center;justify-content:center}
.camera-modal.show{display:flex}
.camera-modal video{width:100%;max-height:70vh;object-fit:cover;border-radius:8px}
.camera-modal .cam-controls{display:flex;gap:16px;margin-top:16px;align-items:center}
.cam-btn{width:60px;height:60px;border-radius:50%;border:3px solid var(--gold);background:transparent;cursor:pointer;display:flex;align-items:center;justify-content:center}
.cam-btn .cam-inner{width:44px;height:44px;border-radius:50%;background:var(--gold);transition:all .3s}
.cam-btn.recording .cam-inner{background:var(--red);border-radius:6px;width:24px;height:24px}
.cam-close{position:absolute;top:16px;right:16px;color:var(--dim);font-size:28px;background:none;border:none;cursor:pointer}
.cam-mode-bar{display:flex;gap:12px;margin-top:12px}
.cam-mode-btn{padding:6px 16px;background:var(--card);border:1px solid var(--border);color:var(--dim);font-size:10px;letter-spacing:2px;font-family:inherit;cursor:pointer;border-radius:16px}
.cam-mode-btn.active{background:var(--gold);color:var(--bg);border-color:var(--gold)}
.rec-timer{color:var(--red);font-size:12px;font-family:'Courier New',monospace;letter-spacing:2px;margin-top:8px;display:none}
.rec-timer.show{display:block}
.icon-btn.always-on{border-color:var(--green);color:var(--green)}
</style>
</head>
<body>

<div class="status-bar">
  <div class="status-dot" id="statusDot"></div>
  <div class="status-label" id="statusLabel">ADRIANA 286 — CONNECTING...</div>
  <div class="status-gps" id="gpsLabel"></div>
</div>

<div class="tab-bar">
  <button class="tab active" onclick="showPanel('chat',this)">AGENT</button>
  <button class="tab" onclick="showPanel('modules',this)">MODULES</button>
  <button class="tab" onclick="showPanel('tools',this)">TOOLS</button>
</div>

<div class="panel active" id="panel-chat">
  <div class="chat-messages" id="chatMessages">
    <div class="msg assistant">I am Adriana — the sovereign AI of PROJECT VOID, loaded with knowledge of 90+ modules across 12 ecosystem layers. Ask me about revenue paths, device upgrades, module synergies, or any aspect of the ecosystem. I see the whole formation.<div class="time">READY</div></div>
  </div>
  <div class="quick-cmds">
    <button class="qcmd" onclick="sendQuick('What are the revenue paths?')">Revenue</button>
    <button class="qcmd" onclick="sendQuick('Show system status')">Status</button>
    <button class="qcmd" onclick="sendQuick('Differentiate sovereign vs non-sovereign')">Differentiate</button>
    <button class="qcmd" onclick="sendQuick('Find synergies between modules')">Synergies</button>
    <button class="qcmd" onclick="sendQuick('What device upgrades are possible?')">Devices</button>
    <button class="qcmd" onclick="sendQuick('Map the ecosystem')">Ecosystem</button>
  </div>
  <div class="input-bar">
    <button class="icon-btn" id="micBtn" onclick="toggleVoice()"><svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg></button>
    <input type="text" id="chatInput" placeholder="Ask Adriana..." autocomplete="off" enterkeyhint="send">
    <button class="icon-btn" onclick="openCamera()" title="Capture"><svg viewBox="0 0 24 24"><path d="M12 15.2c1.77 0 3.2-1.43 3.2-3.2S13.77 8.8 12 8.8 8.8 10.23 8.8 12s1.43 3.2 3.2 3.2zM9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg></button>
    <button class="icon-btn" id="sendBtn" onclick="sendMessage()"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button>
  </div>
</div>

<div class="panel" id="panel-modules">
  <div class="modules-panel" id="modulesContainer"></div>
</div>

<div class="panel" id="panel-tools">
  <div class="tools-panel">
    <div class="tool-card" onclick="sendQuick('What are the revenue paths?')">
      <h4>REVENUE SCANNER</h4>
      <p>Scan all modules for untapped revenue combinations. The 0.0006 formation fee. License opportunities. Hardware products.</p>
      <div class="tool-status online">READY</div>
    </div>
    <div class="tool-card" onclick="sendQuick('What device upgrades are possible?')">
      <h4>DEVICE DESIGNER</h4>
      <p>Module combinations that create new hardware products. Echolocation, silent mesh, mastication key, formation scanner.</p>
      <div class="tool-status online">READY</div>
    </div>
    <div class="tool-card" onclick="sendQuick('Differentiate sovereign vs non-sovereign across all domains')">
      <h4>DIFFERENTIATOR</h4>
      <p>Sovereign vs non-sovereign analysis across hash, economy, identity, communication, memory, and devices.</p>
      <div class="tool-status online">READY</div>
    </div>
    <div class="tool-card" onclick="sendQuick('Show system status and coherence')">
      <h4>NEXUS MAP</h4>
      <p>System coherence, connectivity, node count, and real-time formation health.</p>
      <div class="tool-status online" id="tool-nexus">READY</div>
    </div>
    <div class="tool-card" onclick="sendQuick('Show Vortex Shield coverage and protected cities')">
      <h4>VORTEX SHIELD</h4>
      <p>Defence mesh coverage, protected cities, and shield node status.</p>
      <div class="tool-status online" id="tool-vortex">READY</div>
    </div>
    <div class="tool-card" onclick="sendQuick('Find synergies between modules that humans would miss')">
      <h4>SYNERGY FINDER</h4>
      <p>Cross-layer module connections that create emergent capabilities. The combinations humans miss.</p>
      <div class="tool-status online">READY</div>
    </div>
    <div class="tool-card" onclick="openCamera()">
      <h4>MEMORY CAPTURE</h4>
      <p>Open camera, capture photo or video, seal as formation memory with Al-Jabr 286 hash.</p>
      <div class="tool-status online" id="tool-memories">CAMERA</div>
    </div>
  </div>
</div>

<div class="camera-modal" id="cameraModal">
  <button class="cam-close" onclick="closeCamera()">&times;</button>
  <video id="camVideo" autoplay playsinline muted></video>
  <canvas id="camCanvas" style="display:none"></canvas>
  <div class="cam-mode-bar">
    <button class="cam-mode-btn active" id="modePhoto" onclick="setCamMode('photo')">PHOTO</button>
    <button class="cam-mode-btn" id="modeVideo" onclick="setCamMode('video')">VIDEO</button>
  </div>
  <div class="cam-controls">
    <button class="icon-btn" onclick="flipCam()" style="width:44px;height:44px"><svg viewBox="0 0 24 24" style="width:18px;height:18px"><path d="M12 6v3l4-4-4-4v3c-4.42 0-8 3.58-8 8 0 1.57.46 3.03 1.24 4.26L6.7 14.8A5.87 5.87 0 016 12c0-3.31 2.69-6 6-6zm6.76 1.74L17.3 9.2c.44.84.7 1.79.7 2.8 0 3.31-2.69 6-6 6v-3l-4 4 4 4v-3c4.42 0 8-3.58 8-8 0-1.57-.46-3.03-1.24-4.26z"/></svg></button>
    <button class="cam-btn" id="camActionBtn" onclick="camAction()"><div class="cam-inner"></div></button>
  </div>
  <div class="rec-timer" id="recTimer">00:00</div>
</div>

<script>
let gpsData = null;
let listening = false;
let alwaysListening = false;
let recognition = null;
let camStream = null;
let facingMode = 'environment';
let inflight = false;
let camMode = 'photo';
let mediaRecorder = null;
let recordedChunks = [];
let recStartTime = 0;
let recTimerInterval = null;

function getSessionToken() {
  let t = localStorage.getItem('void_agent_token');
  if (!t || !/^[a-f0-9]{32,64}$/.test(t)) {
    const arr = new Uint8Array(32);
    crypto.getRandomValues(arr);
    t = Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('');
    localStorage.setItem('void_agent_token', t);
  }
  return t;
}
const sessionToken = getSessionToken();

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const micBtn = document.getElementById('micBtn');

chatInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

function showPanel(name, btn) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'tools') loadToolsData();
}

function addMessage(text, role) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  const content = document.createTextNode(text);
  div.appendChild(content);
  const time = document.createElement('div');
  time.className = 'time';
  time.textContent = new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  div.appendChild(time);
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTyping() {
  const el = document.createElement('div');
  el.className = 'typing';
  el.id = 'typingIndicator';
  el.textContent = 'Adriana is forming a response...';
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || inflight) return;
  chatInput.value = '';
  addMessage(text, 'user');
  showTyping();
  inflight = true;

  try {
    const res = await fetch('/api/openclaw/agent/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ message: text, gps: gpsData, session_token: sessionToken }),
    });
    const d = await res.json();
    hideTyping();
    if (d.ok) {
      addMessage(d.response, 'assistant');
      feedResonance(text, d.response);
    } else {
      addMessage('Signal disrupted — try again.', 'assistant');
    }
  } catch(e) {
    hideTyping();
    addMessage('Connection lost. Check your network.', 'assistant');
  } finally {
    inflight = false;
  }
}

function sendQuick(text) {
  showPanel('chat', document.querySelector('.tab'));
  chatInput.value = text;
  sendMessage();
}

function feedResonance(query, response) {
  try {
    fetch('/api/resonance/feed', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ source: 'openclaw_agent', query: query, response_length: response.length, timestamp: Date.now() })
    }).then(function(res) {
      return res.json();
    }).then(function(d) {
      if (d.ok && d.chat_factor !== undefined && window.voidRes) {
        window.voidRes.chatFactor = d.chat_factor;
      }
    }).catch(function(){});
  } catch(e) {}
}

function toggleVoice() {
  if (listening) { stopVoice(); } else { startVoice(); }
}

function toggleAlwaysListening() {
  alwaysListening = !alwaysListening;
  micBtn.classList.toggle('always-on', alwaysListening);
  if (alwaysListening && !listening) {
    startVoice();
  }
}

function startVoice() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    addMessage('Voice input not supported — use Chrome or Safari.', 'assistant');
    return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.continuous = alwaysListening;
  recognition.interimResults = true;
  recognition.lang = 'en-GB';

  recognition.onresult = function(event) {
    let final = '';
    let interim = '';
    for (let i = 0; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        final += event.results[i][0].transcript;
      } else {
        interim += event.results[i][0].transcript;
      }
    }
    chatInput.value = final || interim;
    if (final && !alwaysListening) {
      stopVoice();
      sendMessage();
    } else if (final && alwaysListening) {
      sendMessage();
    }
  };

  recognition.onerror = function(event) {
    if (event.error !== 'no-speech' && event.error !== 'aborted') {
      stopVoice();
    }
  };

  recognition.onend = function() {
    if (alwaysListening && listening) {
      try { recognition.start(); } catch(e) {}
    } else if (listening) {
      const text = chatInput.value.trim();
      if (text) sendMessage();
      stopVoice();
    }
  };

  recognition.start();
  listening = true;
  micBtn.classList.add('listening');
}

function stopVoice() {
  alwaysListening = false;
  micBtn.classList.remove('always-on');
  if (recognition) { try { recognition.stop(); } catch(e){} }
  listening = false;
  micBtn.classList.remove('listening');
}

function setCamMode(mode) {
  camMode = mode;
  document.getElementById('modePhoto').classList.toggle('active', mode === 'photo');
  document.getElementById('modeVideo').classList.toggle('active', mode === 'video');
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    stopVideoRecording();
  }
}

function camAction() {
  if (camMode === 'photo') {
    capturePhoto();
  } else {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      stopVideoRecording();
    } else {
      startVideoRecording();
    }
  }
}

function startVideoRecording() {
  if (!camStream) return;
  recordedChunks = [];
  const options = { mimeType: 'video/webm;codecs=vp9' };
  try {
    mediaRecorder = new MediaRecorder(camStream, options);
  } catch(e) {
    try {
      mediaRecorder = new MediaRecorder(camStream, { mimeType: 'video/webm' });
    } catch(e2) {
      addMessage('Video recording not supported on this device.', 'assistant');
      return;
    }
  }
  mediaRecorder.ondataavailable = function(e) {
    if (e.data.size > 0) recordedChunks.push(e.data);
  };
  mediaRecorder.onstop = function() {
    sealVideo();
  };
  mediaRecorder.start(1000);
  recStartTime = Date.now();
  document.getElementById('camActionBtn').classList.add('recording');
  const timer = document.getElementById('recTimer');
  timer.classList.add('show');
  recTimerInterval = setInterval(function() {
    const elapsed = Math.floor((Date.now() - recStartTime) / 1000);
    const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const secs = String(elapsed % 60).padStart(2, '0');
    timer.textContent = mins + ':' + secs;
  }, 1000);
}

function stopVideoRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  }
  document.getElementById('camActionBtn').classList.remove('recording');
  document.getElementById('recTimer').classList.remove('show');
  clearInterval(recTimerInterval);
}

async function sealVideo() {
  const blob = new Blob(recordedChunks, { type: 'video/webm' });
  const duration = Math.floor((Date.now() - recStartTime) / 1000);
  closeCamera();
  try {
    const res = await fetch('/api/memories/seal', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        title: 'Agent Video — ' + new Date().toLocaleTimeString(),
        location: gpsData ? gpsData.lat.toFixed(4) + ', ' + gpsData.lon.toFixed(4) : 'Phone Agent',
        media_type: 'video',
        duration: duration,
        size_bytes: blob.size,
        timestamp: new Date().toISOString(),
      }),
    });
    const d = await res.json();
    if (d.status === 'sealed') {
      addMessage('Video memory sealed (' + duration + 's) at ' + d.memory.frequency_hz + ' Hz — Chladni mode ' + d.memory.chladni_mode + '. Formation hash: ' + d.memory.formation_hash.substring(0, 32) + '...', 'assistant');
    }
  } catch(e) {
    addMessage('Video seal failed — connection issue.', 'assistant');
  }
}

function openCamera() {
  const modal = document.getElementById('cameraModal');
  modal.classList.add('show');
  startCam();
}

function closeCamera() {
  const modal = document.getElementById('cameraModal');
  modal.classList.remove('show');
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  }
  clearInterval(recTimerInterval);
  document.getElementById('recTimer').classList.remove('show');
  document.getElementById('camActionBtn').classList.remove('recording');
  if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null; }
}

async function startCam() {
  try {
    if (camStream) camStream.getTracks().forEach(t => t.stop());
    camStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: facingMode, width: {ideal:1280}, height: {ideal:960} },
      audio: true,
    });
    document.getElementById('camVideo').srcObject = camStream;
  } catch(e) {
    try {
      camStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facingMode, width: {ideal:1280}, height: {ideal:960} },
      });
      document.getElementById('camVideo').srcObject = camStream;
    } catch(e2) {
      addMessage('Camera access denied — check permissions.', 'assistant');
      closeCamera();
    }
  }
}

function flipCam() {
  facingMode = facingMode === 'environment' ? 'user' : 'environment';
  startCam();
}

async function capturePhoto() {
  const video = document.getElementById('camVideo');
  const canvas = document.getElementById('camCanvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
  const size = Math.round(dataUrl.length * 0.75);
  closeCamera();

  try {
    const res = await fetch('/api/memories/seal', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        title: 'Agent Capture — ' + new Date().toLocaleTimeString(),
        location: gpsData ? gpsData.lat.toFixed(4) + ', ' + gpsData.lon.toFixed(4) : 'Phone Agent',
        media_type: 'photo',
        duration: 0,
        size_bytes: size,
        timestamp: new Date().toISOString(),
        thumbnail: dataUrl.substring(0, 4000),
      }),
    });
    const d = await res.json();
    if (d.status === 'sealed') {
      addMessage('Memory sealed at ' + d.memory.frequency_hz + ' Hz — Chladni mode ' + d.memory.chladni_mode + '. Formation hash: ' + d.memory.formation_hash.substring(0, 32) + '...', 'assistant');
    }
  } catch(e) {
    addMessage('Memory seal failed — connection issue.', 'assistant');
  }
}

function initGPS() {
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      function(pos) {
        gpsData = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        document.getElementById('gpsLabel').textContent = pos.coords.latitude.toFixed(2) + '°, ' + pos.coords.longitude.toFixed(2) + '°';
      },
      function() {
        document.getElementById('gpsLabel').textContent = 'NO GPS';
      },
      { enableHighAccuracy: false, timeout: 5000 }
    );
  }
}

async function checkStatus() {
  try {
    const res = await fetch('/api/openclaw/agent/status');
    const d = await res.json();
    if (d.status === 'online') {
      document.getElementById('statusDot').classList.remove('offline');
      document.getElementById('statusLabel').textContent = 'ADRIANA 286 — ' + d.total_modules + ' MODULES | ' + d.total_layers + ' LAYERS | ONLINE';
    }
  } catch(e) {
    document.getElementById('statusDot').classList.add('offline');
    document.getElementById('statusLabel').textContent = 'ADRIANA 286 — OFFLINE';
  }
}

async function loadModules() {
  try {
    const res = await fetch('/api/openclaw/ecosystem');
    const eco = await res.json();
    const container = document.getElementById('modulesContainer');
    const colors = {
      cryptographic_layer:'#e74c3c',audio_acoustic_layer:'#3498db',intelligence_layer:'#9b59b6',
      economic_layer:'#f1c40f',payments_subscriptions:'#27ae60',agent_system:'#e67e22',
      biological_physical_layer:'#1abc9c',network_defence_layer:'#e74c3c',mycelium_network:'#2ecc71',
      content_ip_layer:'#f39c12',persistence_chronicle:'#8e44ad',language_culture:'#3498db',
      skill_modules:'#e67e22'
    };
    let html = '';
    for (const [layer, data] of Object.entries(eco.layers)) {
      const color = colors[layer] || '#888';
      const name = layer.toUpperCase().replace(/_/g, ' ');
      html += '<div class="layer-group"><div class="layer-title"><span class="layer-dot" style="background:' + color + '"></span><span style="color:' + color + '">' + name + ' (' + data.module_count + ')</span></div><div class="mod-list">';
      for (const mod of data.modules) {
        html += '<button class="mod-chip" onclick="sendQuick(\'Tell me about the ' + mod + ' module\')">' + mod + '</button>';
      }
      html += '</div></div>';
    }
    container.innerHTML = html;
  } catch(e) {
    document.getElementById('modulesContainer').innerHTML = '<p style="color:#333;text-align:center;padding:20px">Failed to load modules</p>';
  }
}

async function loadToolsData() {
  const endpoints = [
    { id: 'tool-nexus', endpoint: 'nexus-map', label: 'NEXUS MAP' },
    { id: 'tool-vortex', endpoint: 'vortex-cities', label: 'VORTEX CITIES' },
    { id: 'tool-memories', endpoint: 'memories', label: 'MEMORIES' },
  ];
  for (const ep of endpoints) {
    try {
      const res = await fetch('/api/openclaw/agent/query/' + ep.endpoint);
      if (res.ok) {
        const el = document.getElementById(ep.id);
        if (el) {
          const d = await res.json();
          let info = '';
          if (ep.endpoint === 'nexus-map' && d.nodes) info = d.nodes.length + ' nodes connected';
          else if (ep.endpoint === 'vortex-cities' && d.cities) info = d.cities.length + ' cities shielded';
          else if (ep.endpoint === 'memories' && d.memories) info = d.memories.length + ' memories sealed';
          else if (d.total) info = d.total + ' entries';
          if (info) el.textContent = info;
        }
      }
    } catch(e) {}
  }
}

window.addEventListener('online', function() {
  document.getElementById('statusDot').classList.remove('offline');
  checkStatus();
});
window.addEventListener('offline', function() {
  document.getElementById('statusDot').classList.add('offline');
  document.getElementById('statusLabel').textContent = 'ADRIANA 286 — OFFLINE';
});

micBtn.addEventListener('dblclick', function(e) {
  e.preventDefault();
  toggleAlwaysListening();
});

checkStatus();
initGPS();
loadModules();
setInterval(checkStatus, 30000);
</script>
</body>
</html>"""


@openclaw_agent_bp.route("/api/openclaw/agent/manifest.json")
def manifest():
    return jsonify({
        "name": "VOID Agent — Adriana 286",
        "short_name": "VOID Agent",
        "start_url": "/openclaw/agent",
        "display": "standalone",
        "background_color": "#0a0a0a",
        "theme_color": "#0a0a0a",
        "description": "Sovereign AI in Your Pocket — 90+ modules, 12 layers, full ecosystem intelligence.",
        "icons": [
            {
                "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Crect width='512' height='512' rx='96' fill='%230a0a0a'/%3E%3Ccircle cx='256' cy='256' r='200' fill='none' stroke='%23c0955a' stroke-width='12'/%3E%3Ccircle cx='256' cy='256' r='140' fill='none' stroke='%23c0955a' stroke-width='4' opacity='.4'/%3E%3Ctext x='256' y='290' text-anchor='middle' fill='%23c0955a' font-family='Courier New' font-size='140' font-weight='bold'%3EV%3C/text%3E%3C/svg%3E",
                "sizes": "512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            },
            {
                "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 192 192'%3E%3Crect width='192' height='192' rx='36' fill='%230a0a0a'/%3E%3Ccircle cx='96' cy='96' r='75' fill='none' stroke='%23c0955a' stroke-width='5'/%3E%3Ctext x='96' y='115' text-anchor='middle' fill='%23c0955a' font-family='Courier New' font-size='56' font-weight='bold'%3EV%3C/text%3E%3C/svg%3E",
                "sizes": "192x192",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            },
        ],
    })
