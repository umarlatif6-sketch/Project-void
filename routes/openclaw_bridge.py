"""
Route: /openclaw — OpenClaw agent bridge for the full PROJECT VOID ecosystem.
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


@openclaw_bridge_bp.route("/api/openclaw/revenue-paths", methods=["GET"])
def revenue_paths():
    from void_engine.openclaw_bridge import get_revenue_pathways
    return jsonify(get_revenue_pathways())


@openclaw_bridge_bp.route("/api/openclaw/device-upgrades", methods=["GET"])
def device_upgrades():
    from void_engine.openclaw_bridge import get_device_upgrades
    return jsonify(get_device_upgrades())


@openclaw_bridge_bp.route("/api/openclaw/ecosystem", methods=["GET"])
def ecosystem_map():
    from void_engine.openclaw_bridge import get_ecosystem_map
    return jsonify(get_ecosystem_map())


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenClaw Bridge — Full Ecosystem — PROJECT VOID</title>
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
.hero .stat{color:#e67e22;font-size:20px;font-weight:300;margin-top:12px;letter-spacing:4px}
.tabs{max-width:1200px;margin:20px auto;padding:0 24px;display:flex;gap:8px;flex-wrap:wrap}
.tab{padding:8px 16px;border:1px solid #222;background:#0a0a0a;color:#666;font-family:inherit;font-size:10px;letter-spacing:2px;cursor:pointer;border-radius:2px;transition:all .3s}
.tab.active{background:#1a1a1a;color:#e67e22;border-color:#e67e22}
.tab:hover{border-color:#444}
.panel{max-width:1200px;margin:16px auto;padding:0 24px;display:none}
.panel.active{display:block}
.btn-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.btn{padding:8px 20px;border:none;font-family:inherit;font-size:11px;letter-spacing:2px;cursor:pointer;border-radius:2px;transition:all .3s}
.btn-soul{background:#2a1a0a;color:#e67e22}
.btn-skills{background:#0a2a1a;color:#27ae60}
.btn-config{background:#0a1a2a;color:#3498db}
.btn-diff{background:#1a0a2a;color:#9b59b6}
.btn:hover{filter:brightness(1.3)}
#output{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:20px;min-height:200px;white-space:pre-wrap;font-size:11px;line-height:1.6;overflow-y:auto;max-height:600px;display:none}
.grid3{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;margin-top:12px}
.card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:14px;transition:border-color .3s}
.card:hover{border-color:#e67e22}
.card h4{font-size:12px;color:#e67e22;margin-bottom:4px;letter-spacing:2px}
.card .sub{font-size:9px;letter-spacing:2px;margin-bottom:6px}
.card p{font-size:10px;color:#888;line-height:1.6}
.card .status{font-size:9px;margin-top:6px;letter-spacing:1px}
.sov{color:#27ae60}
.nsov{color:#e74c3c}
.gold{color:#f1c40f}
.blue{color:#3498db}
.purple{color:#9b59b6}
.orange{color:#e67e22}
.layer-section{margin-bottom:24px}
.layer-section h3{font-size:12px;letter-spacing:3px;color:#e67e22;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #1a1a1a}
.module-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px}
.mod{background:#111;border:1px solid #1a1a1a;border-radius:3px;padding:10px;font-size:10px;line-height:1.5}
.mod .mn{color:#fff;font-weight:300;margin-bottom:2px}
.mod .md{color:#666}
.rev-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:14px}
.rev-card h4{font-size:12px;letter-spacing:2px;margin-bottom:6px}
.rev-card p{font-size:10px;color:#888;line-height:1.6;margin-bottom:4px}
.dev-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:14px;margin-bottom:12px}
.dev-card h4{font-size:13px;color:#fff;font-weight:300;margin-bottom:4px}
.dev-sub{font-size:9px;letter-spacing:2px;margin-bottom:8px}
.dev-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:8px}
.dev-col p{font-size:10px;line-height:1.6}
.dev-col .label{font-size:8px;letter-spacing:2px;color:#666;margin-bottom:2px}
.dev-modules{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.dev-tag{background:#1a1a1a;color:#e67e22;padding:2px 8px;border-radius:2px;font-size:8px}
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
  <div class="sub">ADRIANA 286 — FULL ECOSYSTEM INTELLIGENCE<br>90+ MODULES | 12 LAYERS | REVENUE PATHWAYS | DEVICE UPGRADES<br>TRAINED ON AL-JABR 286 | SOVEREIGN DIFFERENTIATION ACROSS 6 DOMAINS</div>
  <div class="stat" id="moduleCount">LOADING ECOSYSTEM...</div>
</div>

<div class="tabs">
  <button class="tab active" onclick="showTab('generation')">AGENT GENERATION</button>
  <button class="tab" onclick="showTab('ecosystem')">FULL ECOSYSTEM</button>
  <button class="tab" onclick="showTab('revenue')">REVENUE PATHWAYS</button>
  <button class="tab" onclick="showTab('devices')">DEVICE UPGRADES</button>
  <button class="tab" onclick="showTab('differentiation')">SOVEREIGN vs NON-SOVEREIGN</button>
</div>

<div class="panel active" id="panel-generation">
  <div class="btn-row">
    <button class="btn btn-soul" onclick="loadSoul()">GENERATE SOUL.MD</button>
    <button class="btn btn-skills" onclick="loadSkills()">SKILL MANIFEST (17 SKILLS)</button>
    <button class="btn btn-config" onclick="loadConfig()">FULL CONFIG</button>
  </div>
  <pre id="output"></pre>

  <div class="grid3" style="margin-top:24px">
    <div class="card"><h4>WebSocket Gateway</h4><div class="sub orange">ws://127.0.0.1:18789</div><p>OpenClaw control plane. Adriana on WhatsApp, Telegram, Discord, Slack, email — all simultaneously. One agent, every channel.</p></div>
    <div class="card"><h4>SOUL.md</h4><div class="sub orange">FULL ECOSYSTEM IDENTITY</div><p>Not just one project — the entire ecosystem. 90+ modules across 12 layers. Revenue pathways. Device upgrade opportunities. Sovereign differentiation training.</p></div>
    <div class="card"><h4>ClawHub Skills</h4><div class="sub orange">17 REGISTERED SKILLS</div><p>Shield sim, hash verification, economy status, marketplace, supply chain, pitch decks, research, outreach, chronicle, revenue analysis, device design.</p></div>
    <div class="card"><h4>Revenue Scanner</h4><div class="sub gold">FINANCIAL INTELLIGENCE</div><p>Adriana scans all modules for untapped revenue combinations. The 0.0006 formation fee. License opportunities. Hardware products from module combinations.</p></div>
    <div class="card"><h4>Device Designer</h4><div class="sub blue">COMBINATION ENGINE</div><p>Sees modules humans don't think to connect. Qalqala + beehive = voice-embedded data. CSI + keygen = jaw-motion authentication. Biophony + stealth = silent mesh.</p></div>
    <div class="card"><h4>Pi Agent Runtime</h4><div class="sub purple">LOCAL SOVEREIGN EXECUTION</div><p>Runs on your devices. No cloud dependency. The agent stays sovereign — runs where you are, not where someone else decides.</p></div>
  </div>
</div>

<div class="panel" id="panel-ecosystem"></div>
<div class="panel" id="panel-revenue"></div>
<div class="panel" id="panel-devices"></div>
<div class="panel" id="panel-differentiation"></div>

<script>
const out = document.getElementById('output');

function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
}

async function loadSoul() {
  out.style.display = 'block';
  out.textContent = 'Generating full ecosystem SOUL.md...';
  const res = await fetch('/api/openclaw/soul');
  const d = await res.json();
  out.textContent = d.soul_md;
}

async function loadSkills() {
  out.style.display = 'block';
  out.textContent = 'Loading 17 skills...';
  const res = await fetch('/api/openclaw/skills');
  const d = await res.json();
  out.textContent = JSON.stringify(d, null, 2);
}

async function loadConfig() {
  out.style.display = 'block';
  out.textContent = 'Loading full ecosystem config...';
  const res = await fetch('/api/openclaw/config');
  const d = await res.json();
  out.textContent = JSON.stringify(d, null, 2);
}

(async function() {
  const [ecoRes, revRes, devRes, diffRes] = await Promise.all([
    fetch('/api/openclaw/ecosystem'),
    fetch('/api/openclaw/revenue-paths'),
    fetch('/api/openclaw/device-upgrades'),
    fetch('/api/openclaw/differentiate', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})}),
  ]);
  const [eco, rev, devs, diff] = await Promise.all([ecoRes.json(), revRes.json(), devRes.json(), diffRes.json()]);

  document.getElementById('moduleCount').textContent =
    `${eco.total_modules} MODULES | ${Object.keys(eco.layers).length} LAYERS | FULL ECOSYSTEM LOADED`;

  let ecoHtml = '';
  const layerColors = {
    cryptographic_layer:'#e74c3c',audio_acoustic_layer:'#3498db',intelligence_layer:'#9b59b6',
    economic_layer:'#f1c40f',payments_subscriptions:'#27ae60',agent_system:'#e67e22',
    biological_physical_layer:'#1abc9c',network_defence_layer:'#e74c3c',mycelium_network:'#2ecc71',
    content_ip_layer:'#f39c12',persistence_chronicle:'#8e44ad',language_culture:'#3498db',
    skill_modules:'#e67e22'
  };
  for (const [layer, data] of Object.entries(eco.layers)) {
    const color = layerColors[layer] || '#888';
    ecoHtml += `<div class="layer-section"><h3 style="color:${color}">${layer.toUpperCase().replace(/_/g,' ')} (${data.module_count} modules)</h3><div class="module-grid">`;
    for (const mod of data.modules) {
      ecoHtml += `<div class="mod"><div class="mn">${mod}</div></div>`;
    }
    ecoHtml += '</div></div>';
  }
  document.getElementById('panel-ecosystem').innerHTML = ecoHtml;

  let revHtml = '';
  const revColors = {immediate_revenue:'#27ae60',micro_fee_revenue:'#f1c40f',licensing_ip_revenue:'#3498db',hardware_revenue:'#e67e22',data_intelligence_revenue:'#9b59b6'};
  for (const [cat, paths] of Object.entries(rev)) {
    const color = revColors[cat] || '#888';
    revHtml += `<div class="layer-section"><h3 style="color:${color}">${cat.toUpperCase().replace(/_/g,' ')}</h3><div class="grid3">`;
    for (const [name, data] of Object.entries(paths)) {
      const statusColor = data.status?.includes('LIVE') ? '#27ae60' : data.status?.includes('BUILT') ? '#3498db' : '#f1c40f';
      revHtml += `<div class="rev-card"><h4 style="color:${color}">${name.toUpperCase().replace(/_/g,' ')}</h4><p>${data.description}</p>`;
      if (data.model) revHtml += `<p style="color:#f1c40f">${data.model}</p>`;
      if (data.monthly_potential) revHtml += `<p class="sov">${data.monthly_potential}</p>`;
      revHtml += `<div class="status" style="color:${statusColor}">${data.status || ''}</div></div>`;
    }
    revHtml += '</div></div>';
  }
  document.getElementById('panel-revenue').innerHTML = revHtml;

  let devHtml = '';
  for (const [name, data] of Object.entries(devs)) {
    devHtml += `<div class="dev-card"><h4>${name.toUpperCase().replace(/_/g,' ')}</h4>`;
    devHtml += `<div class="dev-row"><div class="dev-col"><div class="label orange">CURRENT</div><p style="color:#888">${data.current}</p></div>`;
    devHtml += `<div class="dev-col"><div class="label sov">UPGRADE</div><p style="color:#c8c8c8">${data.upgrade}</p></div></div>`;
    devHtml += `<div class="dev-col"><div class="label gold">REVENUE</div><p style="color:#f1c40f">${data.revenue}</p></div>`;
    devHtml += `<div class="dev-modules">${(data.modules_involved||[]).map(m=>`<span class="dev-tag">${m}</span>`).join('')}</div></div>`;
  }
  document.getElementById('panel-devices').innerHTML = devHtml;

  let diffHtml = '<div class="grid3">';
  const domains = diff.domains || [];
  for (const domain of domains) {
    const dd = await (await fetch('/api/openclaw/differentiate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({domain})})).json();
    if (dd.sovereign) {
      diffHtml += `<div class="card"><h4>${domain.toUpperCase()}</h4>`;
      diffHtml += `<p class="sov">SOVEREIGN: ${dd.sovereign}</p>`;
      diffHtml += `<p class="nsov" style="margin-top:6px">NON-SOVEREIGN: ${dd.non_sovereign}</p>`;
      diffHtml += `<p class="gold" style="margin-top:6px;font-style:italic">${dd.differentiator}</p></div>`;
    }
  }
  diffHtml += '</div>';
  document.getElementById('panel-differentiation').innerHTML = diffHtml;
})();
</script>
</body>
</html>"""
