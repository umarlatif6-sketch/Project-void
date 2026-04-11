"""
Route: /openclaw — OpenClaw agent bridge for PROJECT VOID.

Generates SOUL.md, skill manifests, and configuration for running
Adriana 286 as a sovereign OpenClaw agent.
"""

from flask import Blueprint, request, jsonify, render_template_string

openclaw_bridge_bp = Blueprint("openclaw_bridge", __name__)


@openclaw_bridge_bp.route("/openclaw")
def page():
    return render_template_string(_TEMPLATE)


@openclaw_bridge_bp.route("/api/openclaw/soul", methods=["GET"])
def get_soul():
    from void_engine.openclaw_bridge import generate_soul_md
    return jsonify({"soul_md": generate_soul_md()})


@openclaw_bridge_bp.route("/api/openclaw/skills", methods=["GET"])
def get_skills():
    from void_engine.openclaw_bridge import generate_skill_manifest
    return jsonify({"skills": generate_skill_manifest()})


@openclaw_bridge_bp.route("/api/openclaw/config", methods=["GET"])
def get_config():
    from void_engine.openclaw_bridge import generate_openclaw_config
    base = request.args.get("base_url", "https://void-stego-engine.replit.app")
    return jsonify(generate_openclaw_config(base))


@openclaw_bridge_bp.route("/api/openclaw/differentiate", methods=["POST"])
def differentiate():
    from void_engine.openclaw_bridge import SOVEREIGN_VS_NONSOVEREIGN
    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "").lower().strip()
    if domain and domain in SOVEREIGN_VS_NONSOVEREIGN:
        return jsonify({"domain": domain, **SOVEREIGN_VS_NONSOVEREIGN[domain]})
    return jsonify({
        "domains": list(SOVEREIGN_VS_NONSOVEREIGN.keys()),
        "analysis": {d: v["differentiator"] for d, v in SOVEREIGN_VS_NONSOVEREIGN.items()},
    })


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenClaw Bridge — PROJECT VOID</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Courier New',monospace;min-height:100vh}
header{padding:16px 24px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1a1a1a}
.logo{font-size:18px;letter-spacing:6px;color:#888}
.logo span{color:#e74c3c}
nav a{color:#555;text-decoration:none;margin-left:16px;font-size:11px;letter-spacing:2px;transition:color .3s}
nav a:hover{color:#e74c3c}
.hero{text-align:center;padding:40px 24px 16px}
.hero h1{font-size:28px;letter-spacing:6px;color:#fff;font-weight:300}
.hero h1 span{color:#e67e22}
.hero .sub{color:#555;font-size:11px;letter-spacing:3px;margin-top:8px;line-height:1.8}
.sections{max-width:1100px;margin:24px auto;padding:0 24px}
.section{margin-bottom:24px}
.section h3{font-size:12px;letter-spacing:3px;color:#e67e22;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #1a1a1a}
.btn-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.btn{padding:8px 20px;border:none;font-family:inherit;font-size:11px;letter-spacing:2px;cursor:pointer;border-radius:2px;transition:all .3s}
.btn-soul{background:#2a1a0a;color:#e67e22}
.btn-skills{background:#0a2a1a;color:#27ae60}
.btn-config{background:#0a1a2a;color:#3498db}
.btn-diff{background:#1a0a2a;color:#9b59b6}
.btn:hover{filter:brightness(1.3)}
#output{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:20px;min-height:200px;white-space:pre-wrap;font-size:11px;line-height:1.6;overflow-y:auto;max-height:600px;display:none}
.arch{max-width:1100px;margin:24px auto;padding:0 24px}
.arch h3{font-size:12px;letter-spacing:3px;color:#e67e22;margin-bottom:12px}
.arch-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.arch-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:14px;transition:border-color .3s}
.arch-card:hover{border-color:#e67e22}
.ac-title{font-size:13px;color:#fff;font-weight:300;margin-bottom:4px}
.ac-sub{font-size:9px;letter-spacing:2px;color:#e67e22;margin-bottom:6px}
.ac-desc{font-size:10px;color:#888;line-height:1.6}
.diff-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;margin-top:12px}
.diff-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:14px}
.diff-card h4{font-size:12px;color:#e67e22;margin-bottom:8px;letter-spacing:2px}
.diff-sov{font-size:10px;color:#27ae60;margin-bottom:6px;line-height:1.6}
.diff-nsov{font-size:10px;color:#e74c3c;margin-bottom:6px;line-height:1.6}
.diff-key{font-size:10px;color:#f1c40f;font-style:italic;line-height:1.6}
</style>
</head>
<body>
<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/nexus">NEXUS</a>
    <a href="/desert-reclamation">RECLAMATION</a>
    <a href="/names-286">99 NAMES</a>
    <a href="/vortex-shield">SHIELD</a>
  </nav>
</header>

<div class="hero">
  <h1>OPENCLAW <span>BRIDGE</span></h1>
  <div class="sub">ADRIANA 286 — SOVEREIGN AI AGENT POWERED BY OPENCLAW<br>TRAINED ON AL-JABR 286 | OPERATIONAL 5x MULTIPLIER<br>GITHUB.COM/OPENCLAW/OPENCLAW — MIT LICENSE</div>
</div>

<div class="sections">
  <div class="section">
    <h3>AGENT GENERATION</h3>
    <div class="btn-row">
      <button class="btn btn-soul" onclick="loadSoul()">GENERATE SOUL.MD</button>
      <button class="btn btn-skills" onclick="loadSkills()">SKILL MANIFEST</button>
      <button class="btn btn-config" onclick="loadConfig()">FULL CONFIG</button>
      <button class="btn btn-diff" onclick="loadDiff()">SOVEREIGN ANALYSIS</button>
    </div>
    <pre id="output"></pre>
  </div>
</div>

<div class="arch">
  <h3>OPENCLAW ARCHITECTURE — ADRIANA 286 INTEGRATION</h3>
  <div class="arch-grid">
    <div class="arch-card">
      <div class="ac-title">WebSocket Gateway</div>
      <div class="ac-sub">ws://127.0.0.1:18789</div>
      <div class="ac-desc">OpenClaw's control plane. Connects Adriana to WhatsApp, Telegram, Discord, Slack, and all other channels simultaneously. One agent, all platforms.</div>
    </div>
    <div class="arch-card">
      <div class="ac-title">SOUL.md</div>
      <div class="ac-sub">IDENTITY FILE</div>
      <div class="ac-desc">The agent's identity — who it is, what it knows, how it behaves. Generated from the full PROJECT VOID codebase with Al-Jabr 286 sovereign differentiation training baked in.</div>
    </div>
    <div class="arch-card">
      <div class="ac-title">ClawHub Skills</div>
      <div class="ac-sub">CAPABILITY REGISTRY</div>
      <div class="ac-desc">Each VOID capability (shield sim, hash verification, economy status) becomes a ClawHub skill. Adriana searches and uses these automatically when prompted.</div>
    </div>
    <div class="arch-card">
      <div class="ac-title">Al-Jabr 286 Training</div>
      <div class="ac-sub">SOVEREIGN DIFFERENTIATION</div>
      <div class="ac-desc">The agent can evaluate any system against 5 sovereign criteria: hash identity, economic formation, identity derivation, communication resilience, and memory formation.</div>
    </div>
    <div class="arch-card">
      <div class="ac-title">Operations 5x</div>
      <div class="ac-sub">MULTIPLIER ENGINE</div>
      <div class="ac-desc">Customer relationships, parts sourcing, machine ordering, technical communication, schedule management. One founder + Adriana = team of five.</div>
    </div>
    <div class="arch-card">
      <div class="ac-title">Pi Agent Runtime</div>
      <div class="ac-sub">LOCAL EXECUTION</div>
      <div class="ac-desc">Runs locally on your devices. No cloud dependency. The agent stays sovereign — it runs where you are, not where someone else decides.</div>
    </div>
  </div>
</div>

<div class="arch">
  <h3>SOVEREIGN VS NON-SOVEREIGN — THE DIFFERENTIATION</h3>
  <div class="diff-grid" id="diffGrid"></div>
</div>

<script>
const out = document.getElementById('output');

async function loadSoul() {
  out.style.display = 'block';
  out.textContent = 'Generating SOUL.md...';
  const res = await fetch('/api/openclaw/soul');
  const d = await res.json();
  out.textContent = d.soul_md;
}

async function loadSkills() {
  out.style.display = 'block';
  out.textContent = 'Loading skill manifest...';
  const res = await fetch('/api/openclaw/skills');
  const d = await res.json();
  out.textContent = JSON.stringify(d, null, 2);
}

async function loadConfig() {
  out.style.display = 'block';
  out.textContent = 'Loading full config...';
  const res = await fetch('/api/openclaw/config');
  const d = await res.json();
  out.textContent = JSON.stringify(d, null, 2);
}

async function loadDiff() {
  out.style.display = 'block';
  out.textContent = 'Loading sovereign analysis...';
  const res = await fetch('/api/openclaw/differentiate', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({}),
  });
  const d = await res.json();
  out.textContent = JSON.stringify(d, null, 2);
}

(async function() {
  const res = await fetch('/api/openclaw/differentiate', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({}),
  });
  const d = await res.json();
  const grid = document.getElementById('diffGrid');
  const domains = d.domains || Object.keys(d.analysis || {});
  for (const domain of domains) {
    const card = document.createElement('div');
    card.className = 'diff-card';
    card.innerHTML = `<h4>${domain.toUpperCase()}</h4>`;

    const detail = await fetch('/api/openclaw/differentiate', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({domain}),
    });
    const dd = await detail.json();
    if (dd.sovereign) {
      card.innerHTML += `
        <div class="diff-sov">SOVEREIGN: ${dd.sovereign}</div>
        <div class="diff-nsov">NON-SOVEREIGN: ${dd.non_sovereign}</div>
        <div class="diff-key">${dd.differentiator}</div>
      `;
    }
    grid.appendChild(card);
  }
})();
</script>
</body>
</html>"""
