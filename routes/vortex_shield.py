"""
Route: /vortex-shield — Vortex Shield Network simulation and visualisation.

10,000 nodes across a configurable area.  Each node creates vacuum zones
through destructive interference.  When a blast event fires, nodes absorb
energy through vortex accumulation instead of resisting.
"""

from flask import Blueprint, request, jsonify, render_template_string

vortex_shield_bp = Blueprint("vortex_shield", __name__)


@vortex_shield_bp.route("/vortex-shield")
def vortex_shield_page():
    return render_template_string(_TEMPLATE)


@vortex_shield_bp.route("/api/vortex-shield/build", methods=["POST"])
def build_network():
    from void_engine.vortex_shield import VortexShieldNetwork
    data = request.get_json(silent=True) or {}
    area_km = min(200, max(5, data.get("area_km", 50)))
    node_count = min(50_000, max(1_000, data.get("node_count", 10_000)))
    seed = data.get("seed", "VOID_SHIELD_432")

    net = VortexShieldNetwork(area_km=area_km, node_count=node_count, seed=seed)
    request._vortex_net = net

    import flask
    flask.g.setdefault("_vortex_nets", {})[seed] = net

    return jsonify(net.network_summary())


@vortex_shield_bp.route("/api/vortex-shield/blast", methods=["POST"])
def simulate_blast():
    from void_engine.vortex_shield import VortexShieldNetwork, BlastEvent
    data = request.get_json(silent=True) or {}

    area_km = min(200, max(5, data.get("area_km", 50)))
    node_count = min(50_000, max(1_000, data.get("node_count", 10_000)))
    seed = data.get("seed", "VOID_SHIELD_432")
    yield_kt = min(100_000, max(0.1, data.get("yield_kt", 15)))
    origin_x = data.get("origin_x", 0)
    origin_y = data.get("origin_y", 0)

    net = VortexShieldNetwork(area_km=area_km, node_count=node_count, seed=seed)
    blast = BlastEvent(origin_x, origin_y, yield_kt)
    result = net.simulate_blast(blast)

    return jsonify(result)


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vortex Shield Network — PROJECT VOID</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Courier New',monospace;min-height:100vh}
header{padding:16px 24px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1a1a1a}
.logo{font-size:18px;letter-spacing:6px;color:#888}
.logo span{color:#e74c3c}
nav a{color:#555;text-decoration:none;margin-left:16px;font-size:11px;letter-spacing:2px;transition:color .3s}
nav a:hover{color:#e74c3c}
.hero{text-align:center;padding:48px 24px 24px}
.hero h1{font-size:32px;letter-spacing:8px;color:#fff;font-weight:300}
.hero h1 span{color:#e74c3c}
.hero .sub{color:#555;font-size:12px;letter-spacing:4px;margin-top:8px}
.controls{max-width:900px;margin:24px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.ctrl-group{background:#111;border:1px solid #1a1a1a;padding:12px;border-radius:4px}
.ctrl-group label{font-size:10px;letter-spacing:2px;color:#666;display:block;margin-bottom:4px}
.ctrl-group input,.ctrl-group select{width:100%;background:#0a0a0a;border:1px solid #222;color:#fff;padding:6px 8px;font-family:inherit;font-size:13px;border-radius:2px}
.btn-row{max-width:900px;margin:16px auto;padding:0 24px;display:flex;gap:12px;flex-wrap:wrap}
.btn{padding:10px 24px;border:none;font-family:inherit;font-size:12px;letter-spacing:3px;cursor:pointer;border-radius:2px;transition:all .3s}
.btn-build{background:#1a3a1a;color:#4caf50}
.btn-blast{background:#3a1a1a;color:#e74c3c}
.btn:hover{filter:brightness(1.3)}
.btn:disabled{opacity:0.4;cursor:not-allowed}
#status{max-width:900px;margin:16px auto;padding:0 24px;font-size:11px;color:#666}
.result-grid{max-width:900px;margin:24px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.stat-card{background:#111;border:1px solid #1a1a1a;padding:16px;border-radius:4px;text-align:center}
.stat-val{font-size:28px;color:#4caf50;font-weight:300;margin:8px 0}
.stat-val.red{color:#e74c3c}
.stat-val.gold{color:#f1c40f}
.stat-label{font-size:9px;letter-spacing:2px;color:#555}
.grade-box{max-width:900px;margin:24px auto;padding:32px;text-align:center;background:#111;border:1px solid #1a1a1a;border-radius:4px}
.grade-letter{font-size:64px;color:#4caf50;font-weight:300;letter-spacing:8px}
.grade-letter.SOVEREIGN{color:#f1c40f}
.grade-letter.FORTIFIED{color:#4caf50}
.grade-letter.ACTIVE{color:#3498db}
.grade-letter.PARTIAL{color:#e67e22}
.grade-letter.COMPROMISED{color:#e74c3c}
.grade-narrative{color:#888;font-size:12px;margin-top:8px;line-height:1.6}
canvas{display:block;margin:24px auto;background:#050505;border:1px solid #1a1a1a;border-radius:4px}
.theory{max-width:900px;margin:32px auto;padding:0 24px}
.theory h3{color:#e74c3c;font-size:14px;letter-spacing:4px;margin-bottom:12px}
.theory p{color:#666;font-size:12px;line-height:1.8;margin-bottom:12px}
.activation-log{max-width:900px;margin:24px auto;padding:0 24px}
.activation-log h3{color:#555;font-size:11px;letter-spacing:3px;margin-bottom:8px}
.activation-log table{width:100%;border-collapse:collapse;font-size:11px}
.activation-log th{text-align:left;color:#666;padding:4px 8px;border-bottom:1px solid #1a1a1a;letter-spacing:2px;font-size:9px}
.activation-log td{padding:4px 8px;color:#888;border-bottom:1px solid #0f0f0f}
</style>
</head>
<body>

<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/formation-invisibility">INVISIBILITY</a>
    <a href="/sovereign-agents-286">AGENTS 286</a>
    <a href="/stress-battery">BATTERY</a>
    <a href="/manchester-exhibit">EXHIBIT</a>
  </nav>
</header>

<div class="hero">
  <h1>VORTEX <span>SHIELD</span></h1>
  <div class="sub">10,000 NODES — VACUUM ZONE ENERGY ABSORPTION NETWORK</div>
</div>

<div class="controls">
  <div class="ctrl-group">
    <label>AREA (KM)</label>
    <input type="number" id="area_km" value="50" min="5" max="200">
  </div>
  <div class="ctrl-group">
    <label>NODE COUNT</label>
    <input type="number" id="node_count" value="10000" min="1000" max="50000" step="1000">
  </div>
  <div class="ctrl-group">
    <label>BLAST YIELD (KT)</label>
    <input type="number" id="yield_kt" value="15" min="0.1" max="100000" step="0.1">
  </div>
  <div class="ctrl-group">
    <label>SEED</label>
    <input type="text" id="seed" value="VOID_SHIELD_432">
  </div>
</div>

<div class="btn-row">
  <button class="btn btn-build" id="buildBtn" onclick="buildNetwork()">BUILD NETWORK</button>
  <button class="btn btn-blast" id="blastBtn" onclick="fireBlast()" disabled>DETONATE</button>
</div>

<div id="status">Ready. Configure parameters and build the network.</div>

<div class="result-grid" id="results" style="display:none"></div>
<div class="grade-box" id="gradeBox" style="display:none"></div>
<canvas id="shieldCanvas" width="600" height="600" style="display:none"></canvas>
<div class="activation-log" id="activationLog" style="display:none"></div>

<div class="theory">
  <h3>THE FORMATION PRINCIPLE — APPLIED TO DEFENCE</h3>
  <p>Every node in this network vibrates at a harmonic of 432 Hz. Adjacent nodes with opposing phases create <strong>destructive interference</strong> — vacuum corridors where wave energy cancels to zero. These corridors form naturally, the way Chladni patterns form on a vibrating plate.</p>
  <p>When a blast wave arrives, the vacuum corridors do not resist the energy — they <strong>channel</strong> it. Energy flows along the zero-pressure corridors toward <strong>vortex accumulation sinks</strong> — nodes spinning at 7.83 Hz (Schumann resonance) that absorb and dissipate energy through underground thermal channels.</p>
  <p>The network does not block the blast. It <strong>redirects</strong> it. The energy enters the vortex sinks, spins, dissipates. The area inside the network experiences reduced blast pressure because the energy was routed elsewhere — absorbed by the formation itself.</p>
  <p>This is the same principle as metamaterial cloaking, but applied at macro scale using distributed formation nodes instead of nanoscale structures. The frequency is prior. The structure is the memory. The shield is the formation.</p>
</div>

<script>
let networkBuilt = false;

async function buildNetwork() {
  const btn = document.getElementById('buildBtn');
  btn.disabled = true;
  document.getElementById('status').textContent = 'Building network...';

  const body = {
    area_km: parseFloat(document.getElementById('area_km').value),
    node_count: parseInt(document.getElementById('node_count').value),
    seed: document.getElementById('seed').value,
  };

  try {
    const res = await fetch('/api/vortex-shield/build', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    const data = await res.json();

    document.getElementById('status').textContent =
      `Network built: ${data.total_nodes} nodes, ${data.vortex_sinks} vortex sinks, ` +
      `${data.vacuum_corridors} vacuum corridors. Build time: ${data.build_time_s}s. Ready to detonate.`;

    showBuildResults(data);
    networkBuilt = true;
    document.getElementById('blastBtn').disabled = false;
  } catch(e) {
    document.getElementById('status').textContent = 'Error: ' + e.message;
  }
  btn.disabled = false;
}

function showBuildResults(data) {
  const grid = document.getElementById('results');
  grid.style.display = 'grid';
  grid.innerHTML = `
    <div class="stat-card"><div class="stat-val">${data.total_nodes.toLocaleString()}</div><div class="stat-label">NODES</div></div>
    <div class="stat-card"><div class="stat-val gold">${data.vortex_sinks}</div><div class="stat-label">VORTEX SINKS</div></div>
    <div class="stat-card"><div class="stat-val">${data.vacuum_corridors.toLocaleString()}</div><div class="stat-label">VACUUM CORRIDORS</div></div>
    <div class="stat-card"><div class="stat-val">${data.avg_vacuum_strength.toFixed(4)}</div><div class="stat-label">AVG VACUUM</div></div>
  `;
}

async function fireBlast() {
  const btn = document.getElementById('blastBtn');
  btn.disabled = true;
  document.getElementById('status').textContent = 'Detonation in progress...';

  const body = {
    area_km: parseFloat(document.getElementById('area_km').value),
    node_count: parseInt(document.getElementById('node_count').value),
    seed: document.getElementById('seed').value,
    yield_kt: parseFloat(document.getElementById('yield_kt').value),
    origin_x: 0,
    origin_y: 0,
  };

  try {
    const res = await fetch('/api/vortex-shield/blast', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    const data = await res.json();

    document.getElementById('status').textContent =
      `Blast simulated: ${data.blast.yield_kt} KT. Shield grade: ${data.shield_grade}. ` +
      `Absorption: ${data.results.absorption_pct.toFixed(2)}%. Simulation: ${data.simulation_time_s}s.`;

    showBlastResults(data);
    drawShieldMap(data);
    showActivationLog(data);
  } catch(e) {
    document.getElementById('status').textContent = 'Error: ' + e.message;
  }
  btn.disabled = false;
}

function showBlastResults(data) {
  const r = data.results;
  const grid = document.getElementById('results');
  grid.style.display = 'grid';
  grid.innerHTML = `
    <div class="stat-card"><div class="stat-val">${data.node_count.toLocaleString()}</div><div class="stat-label">TOTAL NODES</div></div>
    <div class="stat-card"><div class="stat-val ${r.survival_rate > 80 ? '' : 'red'}">${r.survival_rate}%</div><div class="stat-label">SURVIVAL RATE</div></div>
    <div class="stat-card"><div class="stat-val gold">${r.shield_efficiency_pct.toFixed(2)}%</div><div class="stat-label">SHIELD EFFICIENCY</div></div>
    <div class="stat-card"><div class="stat-val red">${(100 - r.shield_efficiency_pct).toFixed(2)}%</div><div class="stat-label">ENERGY PASSED</div></div>
    <div class="stat-card"><div class="stat-val">${data.vortex_sinks}</div><div class="stat-label">VORTEX SINKS</div></div>
    <div class="stat-card"><div class="stat-val">${data.vacuum_corridors.toLocaleString()}</div><div class="stat-label">VACUUM CORRIDORS</div></div>
    <div class="stat-card"><div class="stat-val red">${r.nodes_destroyed.toLocaleString()}</div><div class="stat-label">NODES DESTROYED</div></div>
    <div class="stat-card"><div class="stat-val">${r.nodes_survived.toLocaleString()}</div><div class="stat-label">NODES SURVIVED</div></div>
  `;

  const gradeBox = document.getElementById('gradeBox');
  gradeBox.style.display = 'block';
  gradeBox.innerHTML = `
    <div class="grade-letter ${data.shield_grade}">${data.shield_grade}</div>
    <div class="grade-narrative">
      ${data.blast.yield_kt} kiloton detonation at origin.
      ${r.shield_efficiency_pct.toFixed(2)}% of intercepted energy absorbed by ${data.vortex_sinks} vortex sinks.
      ${r.nodes_survived.toLocaleString()} of ${data.node_count.toLocaleString()} nodes survived.
      Vortex accumulation: ${r.vortex_accumulation_j.toExponential(2)} J.
      Dissipated: ${r.vortex_dissipated_j.toExponential(2)} J.
    </div>
  `;
}

function drawShieldMap(data) {
  const canvas = document.getElementById('shieldCanvas');
  canvas.style.display = 'block';
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.fillStyle = '#050505';
  ctx.fillRect(0, 0, w, h);

  const cx = w/2, cy = h/2;
  const scale = w / (data.area_km * 1000 * 2);
  const r = data.results;

  const wave = data.activation_wave_sample || [];
  for (const entry of wave) {
    const dist = entry.distance_m * scale;
    ctx.beginPath();
    ctx.arc(cx, cy, dist, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(231, 76, 60, 0.1)';
    ctx.stroke();
  }

  ctx.beginPath();
  ctx.arc(cx, cy, 8, 0, Math.PI * 2);
  ctx.fillStyle = '#e74c3c';
  ctx.fill();

  ctx.fillStyle = '#333';
  ctx.font = '9px monospace';
  ctx.fillText('DETONATION', cx + 12, cy + 3);

  const maxDist = data.area_km * 500;
  for (let ring = 1; ring <= 4; ring++) {
    const rd = (maxDist * ring / 4) * scale;
    ctx.beginPath();
    ctx.arc(cx, cy, rd, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.stroke();
    ctx.fillStyle = '#333';
    ctx.fillText(`${(data.area_km * ring / 4).toFixed(0)} km`, cx + rd + 4, cy);
  }

  const survPct = r.survival_rate / 100;
  const absorbPct = r.absorption_pct / 100;

  for (let i = 0; i < Math.min(2000, data.node_count); i++) {
    const angle = (i / 2000) * Math.PI * 2 + (i * 137.508 * Math.PI / 180);
    const dist = Math.sqrt(i / 2000) * maxDist * scale;
    const nx = cx + Math.cos(angle) * dist;
    const ny = cy + Math.sin(angle) * dist;

    const survived = Math.random() < survPct;
    ctx.beginPath();
    ctx.arc(nx, ny, 1.5, 0, Math.PI * 2);
    ctx.fillStyle = survived
      ? `rgba(76, 175, 80, ${0.3 + absorbPct * 0.5})`
      : 'rgba(231, 76, 60, 0.4)';
    ctx.fill();
  }

  const sinkCount = data.vortex_sinks;
  for (let i = 0; i < Math.min(50, sinkCount); i++) {
    const angle = (i / 50) * Math.PI * 2;
    const dist = (0.3 + Math.random() * 0.6) * maxDist * scale;
    const sx = cx + Math.cos(angle) * dist;
    const sy = cy + Math.sin(angle) * dist;

    ctx.beginPath();
    ctx.arc(sx, sy, 4, 0, Math.PI * 2);
    ctx.strokeStyle = '#f1c40f';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.lineWidth = 1;

    for (let s = 0; s < 3; s++) {
      ctx.beginPath();
      ctx.arc(sx, sy, 6 + s * 3, (s * 0.5), (s * 0.5) + Math.PI * 1.5);
      ctx.strokeStyle = `rgba(241, 196, 15, ${0.3 - s * 0.08})`;
      ctx.stroke();
    }
  }
}

function showActivationLog(data) {
  const wave = data.activation_wave_sample || [];
  if (!wave.length) return;

  const log = document.getElementById('activationLog');
  log.style.display = 'block';
  let html = '<h3>ACTIVATION WAVE — FIRST 20 NODES</h3><table><tr><th>NODE</th><th>TIME (s)</th><th>DISTANCE (m)</th></tr>';
  for (const e of wave) {
    html += `<tr><td>#${e.node_id}</td><td>${e.time.toFixed(4)}</td><td>${e.distance_m.toFixed(1)}</td></tr>`;
  }
  html += '</table>';
  log.innerHTML = html;
}
</script>
</body>
</html>"""
