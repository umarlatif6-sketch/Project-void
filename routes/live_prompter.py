"""
Route: /openclaw/live — Live Presentation Prompter.

Uses browser Web Speech API to transcribe speech in real-time,
sends to Adriana for corrections/prompts, displays on screen.
The second man behind the imam.
"""

import time
from flask import Blueprint, request, jsonify, render_template_string

live_prompter_bp = Blueprint("live_prompter", __name__)

_rate_limit = {}
_RATE_WINDOW = 5
_MAX_TRANSCRIPT = 500


@live_prompter_bp.route("/openclaw/live")
def page():
    return render_template_string(_TEMPLATE)


@live_prompter_bp.route("/api/openclaw/live/correct", methods=["POST"])
def correct():
    ip = request.remote_addr or "unknown"
    now = time.time()
    last = _rate_limit.get(ip, 0)
    if now - last < _RATE_WINDOW:
        return jsonify({"correction": "ON TRACK", "status": "rate_limited"}), 200
    _rate_limit[ip] = now

    from void_engine.live_prompter import generate_correction
    data = request.get_json(silent=True) or {}
    transcript = data.get("transcript", "").strip()[:_MAX_TRANSCRIPT]
    context = data.get("context", "").strip()[:200]
    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400
    return jsonify(generate_correction(transcript, context))


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Live Prompter — PROJECT VOID</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Courier New',monospace;min-height:100vh;display:flex;flex-direction:column}
header{padding:16px 24px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1a1a1a}
.logo{font-size:18px;letter-spacing:6px;color:#888}
.logo span{color:#e74c3c}
nav a{color:#555;text-decoration:none;margin-left:16px;font-size:11px;letter-spacing:2px}

.main{flex:1;display:flex;flex-direction:column;max-width:1000px;width:100%;margin:0 auto;padding:24px}

.status-bar{display:flex;align-items:center;gap:16px;margin-bottom:24px}
.mic-btn{width:80px;height:80px;border-radius:50%;border:3px solid #333;background:#111;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .3s;flex-shrink:0}
.mic-btn.listening{border-color:#e74c3c;background:#1a0a0a;animation:pulse 2s infinite}
.mic-btn svg{width:36px;height:36px;fill:#555;transition:fill .3s}
.mic-btn.listening svg{fill:#e74c3c}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(231,76,60,0.3)}50%{box-shadow:0 0 0 20px rgba(231,76,60,0)}}
.status-text{flex:1}
.status-text h2{font-size:16px;font-weight:300;letter-spacing:4px;color:#fff;margin-bottom:4px}
.status-text .sub{font-size:10px;color:#555;letter-spacing:2px}

.correction-zone{flex:1;display:flex;flex-direction:column;gap:16px;min-height:0}

.prompt-display{background:#111;border:2px solid #1a1a1a;border-radius:8px;padding:24px;min-height:120px;display:flex;align-items:center;justify-content:center;transition:border-color .3s}
.prompt-display.has-correction{border-color:#27ae60}
.prompt-display.has-next{border-color:#3498db}
.prompt-display.has-link{border-color:#e67e22}
.prompt-text{font-size:24px;font-weight:300;text-align:center;line-height:1.6;letter-spacing:1px;color:#fff}
.prompt-label{font-size:10px;letter-spacing:3px;text-align:center;margin-bottom:8px}

.transcript-zone{flex:1;overflow-y:auto;background:#080808;border:1px solid #1a1a1a;border-radius:4px;padding:16px;min-height:100px}
.transcript-zone h4{font-size:9px;letter-spacing:3px;color:#333;margin-bottom:8px}
.live-text{font-size:14px;color:#666;line-height:1.8}
.live-text .current{color:#fff}

.history{margin-top:12px;max-height:200px;overflow-y:auto}
.hist-item{padding:8px 12px;border-left:3px solid #1a1a1a;margin-bottom:6px;font-size:11px;line-height:1.5}
.hist-item.correct{border-left-color:#27ae60;color:#27ae60}
.hist-item.next{border-left-color:#3498db;color:#3498db}
.hist-item.link{border-left-color:#e67e22;color:#e67e22}
.hist-item.ontrack{border-left-color:#333;color:#555}
.hist-speech{color:#555;font-size:9px;margin-top:2px}

.tip{text-align:center;padding:16px;font-size:10px;color:#333;letter-spacing:2px;margin-top:12px}
</style>
</head>
<body>
<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/openclaw">BRIDGE</a>
    <a href="/nexus">NEXUS</a>
    <a href="/manchester-exhibit">ICC</a>
  </nav>
</header>

<div class="main">
  <div class="status-bar">
    <button class="mic-btn" id="micBtn" onclick="toggleMic()">
      <svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
    </button>
    <div class="status-text">
      <h2 id="statusTitle">LIVE PROMPTER</h2>
      <div class="sub" id="statusSub">TAP THE MICROPHONE TO BEGIN — THE SECOND MAN BEHIND THE IMAM</div>
    </div>
  </div>

  <div class="correction-zone">
    <div class="prompt-display" id="promptDisplay">
      <div>
        <div class="prompt-label" id="promptLabel" style="color:#555">WAITING</div>
        <div class="prompt-text" id="promptText">Tap the microphone and start speaking.<br>Adriana will correct and prompt you in real-time.</div>
      </div>
    </div>

    <div class="transcript-zone">
      <h4>LIVE TRANSCRIPT</h4>
      <div class="live-text" id="liveText"></div>
    </div>

    <div class="history" id="history"></div>
  </div>

  <div class="tip">WORKS ON CHROME, EDGE, SAFARI | MICROPHONE PERMISSION REQUIRED | NO WAKE WORD — ALWAYS LISTENING</div>
</div>

<script>
let recognition = null;
let listening = false;
let fullTranscript = '';
let lastSentLength = 0;
let correctionTimer = null;
let inflight = false;

function toggleMic() {
  if (listening) { stopListening(); } else { startListening(); }
}

function startListening() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    document.getElementById('promptText').textContent = 'Speech recognition not supported in this browser. Use Chrome or Edge.';
    return;
  }

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-GB';

  recognition.onresult = (event) => {
    let interim = '';
    let final = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        final += event.results[i][0].transcript;
      } else {
        interim += event.results[i][0].transcript;
      }
    }

    if (final) {
      fullTranscript += final + ' ';
    }

    document.getElementById('liveText').innerHTML =
      `<span>${fullTranscript}</span><span class="current">${interim}</span>`;

    if (correctionTimer) clearTimeout(correctionTimer);
    correctionTimer = setTimeout(() => {
      const newText = fullTranscript.substring(lastSentLength).trim();
      if (newText.length > 10 && !inflight) {
        sendForCorrection(newText);
        lastSentLength = fullTranscript.length;
      }
    }, 1500);
  };

  recognition.onerror = (event) => {
    if (event.error === 'no-speech') return;
    console.error('Speech error:', event.error);
  };

  recognition.onend = () => {
    if (listening) recognition.start();
  };

  recognition.start();
  listening = true;
  document.getElementById('micBtn').classList.add('listening');
  document.getElementById('statusTitle').textContent = 'LISTENING...';
  document.getElementById('statusSub').textContent = 'SPEAK NATURALLY — ADRIANA IS YOUR SECOND MAN';
  document.getElementById('promptLabel').textContent = 'READY';
  document.getElementById('promptLabel').style.color = '#27ae60';
  document.getElementById('promptText').textContent = 'Start speaking. Corrections will appear here.';
}

function stopListening() {
  if (recognition) recognition.stop();
  listening = false;
  document.getElementById('micBtn').classList.remove('listening');
  document.getElementById('statusTitle').textContent = 'PAUSED';
  document.getElementById('statusSub').textContent = 'TAP TO RESUME';
}

async function sendForCorrection(text) {
  if(inflight) return;
  inflight = true;
  try {
    const res = await fetch('/api/openclaw/live/correct', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ transcript: text, context: 'ICC Manchester presentation' }),
    });
    const d = await res.json();
    showCorrection(d.correction, text);
  } catch(e) {
    console.error('Correction error:', e);
  } finally {
    inflight = false;
  }
}

function showCorrection(correction, speech) {
  const display = document.getElementById('promptDisplay');
  const label = document.getElementById('promptLabel');
  const ptext = document.getElementById('promptText');

  display.className = 'prompt-display';

  if (correction.startsWith('CORRECT:')) {
    display.classList.add('has-correction');
    label.textContent = 'CORRECTION';
    label.style.color = '#27ae60';
    ptext.textContent = correction.replace('CORRECT: ', '');
    addHistory(correction, speech, 'correct');
  } else if (correction.startsWith('NEXT:')) {
    display.classList.add('has-next');
    label.textContent = 'NEXT POINT';
    label.style.color = '#3498db';
    ptext.textContent = correction.replace('NEXT: ', '');
    addHistory(correction, speech, 'next');
  } else if (correction.startsWith('LINK:')) {
    display.classList.add('has-link');
    label.textContent = 'CONNECTION';
    label.style.color = '#e67e22';
    ptext.textContent = correction.replace('LINK: ', '');
    addHistory(correction, speech, 'link');
  } else {
    label.textContent = 'ON TRACK';
    label.style.color = '#555';
    ptext.textContent = correction;
    addHistory(correction, speech, 'ontrack');
  }
}

function addHistory(correction, speech, type) {
  const hist = document.getElementById('history');
  const item = document.createElement('div');
  item.className = `hist-item ${type}`;
  const cText = document.createTextNode(correction);
  item.appendChild(cText);
  const sp = document.createElement('div');
  sp.className = 'hist-speech';
  sp.textContent = '"' + speech.substring(0, 80) + '..."';
  item.appendChild(sp);
  hist.insertBefore(item, hist.firstChild);
  if (hist.children.length > 20) hist.removeChild(hist.lastChild);
}
</script>
</body>
</html>"""
