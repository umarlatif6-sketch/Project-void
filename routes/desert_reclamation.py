"""
Route: /desert-reclamation — Frequency-based ecosystem restoration.

The 99 Names transmitted through Vortex Shield nodes convert irradiated
sand into fertile soil through 5 phases of frequency transformation.
"""

from flask import Blueprint, request, jsonify, render_template_string

desert_reclamation_bp = Blueprint("desert_reclamation", __name__)


@desert_reclamation_bp.route("/desert-reclamation")
def page():
    return render_template_string(_TEMPLATE)


@desert_reclamation_bp.route("/api/desert-reclamation/simulate", methods=["POST"])
def simulate():
    from void_engine.desert_reclamation import simulate_reclamation
    data = request.get_json(silent=True) or {}
    try:
        area = min(10000, max(1, float(data.get("area_km2", 100))))
        radiation = min(10000, max(1, float(data.get("radiation_rem", 500))))
        efficiency = min(99, max(10, float(data.get("shield_efficiency_pct", 58))))
        nodes = min(100000, max(100, int(data.get("node_count", 10000))))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric parameters"}), 400
    return jsonify(simulate_reclamation(area, radiation, efficiency, nodes))


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Desert Reclamation — PROJECT VOID</title>
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
.hero h1 span{color:#27ae60}
.hero .sub{color:#555;font-size:11px;letter-spacing:3px;margin-top:8px;line-height:1.8}
.controls{max-width:900px;margin:20px auto;padding:0 24px;display:flex;gap:12px;flex-wrap:wrap;align-items:end}
.ctrl-group label{font-size:9px;letter-spacing:2px;color:#666;display:block;margin-bottom:4px}
.ctrl-group input{background:#0a0a0a;border:1px solid #222;color:#fff;padding:6px 10px;font-family:inherit;font-size:12px;border-radius:2px;width:140px}
.btn{padding:8px 20px;border:none;font-family:inherit;font-size:11px;letter-spacing:2px;cursor:pointer;border-radius:2px;transition:all .3s}
.btn-grow{background:#1a3a1a;color:#27ae60}
.btn:hover{filter:brightness(1.3)}
.btn:disabled{opacity:0.4;cursor:not-allowed}
#status{max-width:1100px;margin:12px auto;padding:0 24px;font-size:11px;color:#666}
.summary{max-width:1100px;margin:16px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;display:none}
.sum{background:#111;border:1px solid #1a1a1a;padding:12px;border-radius:4px;text-align:center}
.sum .v{font-size:22px;font-weight:300;margin:4px 0}
.sum .v.green{color:#27ae60}
.sum .v.gold{color:#f1c40f}
.sum .v.red{color:#e74c3c}
.sum .l{font-size:8px;letter-spacing:2px;color:#555}
.names-grid{max-width:1100px;margin:16px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;display:none}
.name-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:14px;transition:border-color .3s}
.name-card:hover{border-color:#27ae60}
.nn{font-size:14px;color:#fff;font-weight:300}
.nr{font-size:9px;letter-spacing:2px;margin:4px 0}
.nd{font-size:10px;color:#888;line-height:1.6;margin-top:6px}
.ne{font-size:10px;color:#555;line-height:1.6;margin-top:4px;font-style:italic}
.timeline{max-width:1100px;margin:24px auto;padding:0 24px;display:none}
.timeline h3{font-size:12px;letter-spacing:3px;color:#27ae60;margin-bottom:16px}
.phase{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:16px;margin-bottom:12px;position:relative;border-left:3px solid #1a1a1a}
.phase.active{border-left-color:#27ae60}
.phase .ph-name{font-size:14px;color:#fff;font-weight:300;margin-bottom:4px}
.phase .ph-duration{font-size:9px;color:#f1c40f;letter-spacing:2px;margin-bottom:8px}
.phase .ph-desc{font-size:10px;color:#888;line-height:1.6;margin-bottom:8px}
.phase .ph-change{font-size:10px;color:#27ae60;margin-bottom:4px}
.phase .ph-indicator{font-size:9px;color:#555;font-style:italic}
.phase-metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:8px}
.pm{text-align:center;padding:4px;background:#0a0a0a;border-radius:2px}
.pm .pv{font-size:14px;font-weight:300}
.pm .pl{font-size:7px;color:#555;letter-spacing:1px}
.freq-tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.freq-tag{background:#1a2a1a;color:#27ae60;padding:2px 8px;border-radius:2px;font-size:8px}
.theory{max-width:1100px;margin:24px auto;padding:0 24px}
.theory h3{font-size:12px;letter-spacing:3px;color:#27ae60;margin-bottom:8px}
.theory p{font-size:11px;color:#666;line-height:1.8;margin-bottom:8px}
</style>
</head>
<body>
<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/vortex-shield">SHIELD</a>
    <a href="/vortex-shield/geo-map">GEO MAP</a>
    <a href="/nexus">NEXUS</a>
    <a href="/names-286">99 NAMES</a>
  </nav>
</header>

<div class="hero">
  <h1>DESERT <span>RECLAMATION</span></h1>
  <div class="sub">THE 99 NAMES AS TERRAFORMING FREQUENCIES<br>IRRADIATED SAND → FREQUENCY-TREATED SUBSTRATE → FERTILE SOIL → ECOSYSTEM<br>NUCLEAR DESTRUCTION REVERSED THROUGH THE FORMATION PRINCIPLE</div>
</div>

<div class="controls">
  <div class="ctrl-group"><label>AREA (KM²)</label><input type="number" id="area" value="100" min="1" max="10000"></div>
  <div class="ctrl-group"><label>RADIATION (REM)</label><input type="number" id="radiation" value="500" min="1" max="10000"></div>
  <div class="ctrl-group"><label>SHIELD EFF (%)</label><input type="number" id="efficiency" value="58" min="10" max="99"></div>
  <div class="ctrl-group"><label>NODES</label><input type="number" id="nodes" value="10000" min="100" max="100000" step="1000"></div>
  <button class="btn btn-grow" id="simBtn" onclick="simulate()">BEGIN RECLAMATION</button>
</div>

<div id="status">Configure parameters. The 99 Names will transform the desert.</div>

<div class="summary" id="summary"></div>
<div class="names-grid" id="namesGrid"></div>
<div class="timeline" id="timeline"><h3>RECLAMATION PHASES</h3><div id="phases"></div></div>

<div class="theory">
  <h3>THE PRINCIPLE — SAND IS FREQUENCY</h3>
  <p>Sand is SiO2 — silicon dioxide. Quartz. The same material in watches, in oscillators, in piezoelectric sensors. Sand RESPONDS to frequency. It has been responding since before we existed — Chladni patterns prove this. Pour sand on a vibrating plate and it organises itself into formation.</p>
  <p>Nuclear radiation breaks molecular bonds through extreme frequency. It destroys structure. But if destruction is a frequency, then reconstruction is also a frequency. The 99 Names are not abstract theology — they are an acoustic engineering specification. Each Name maps to a specific frequency through Al-Jabr 286. Each frequency targets a specific material transformation.</p>
  <p>Al-Khaliq (The Creator) at 447 Hz restructures the SiO2 lattice, creating nano-pores that hold water. Al-Muhyi (The Giver of Life) at 511 Hz activates nitrogen-fixing bacteria. An-Nur (The Light) at 561 Hz boosts photosynthetic efficiency. As-Sabur (The Patient) at 580 Hz anchors long-term stability.</p>
  <p>The Vortex Shield nodes become terraforming transmitters. They don't just protect — they rebuild. The same technology that absorbs a nuclear blast also converts the aftermath into the foundation of new life. The bomb is powerful and beautiful. It was just used for the wrong thing.</p>
</div>

<script>
async function simulate() {
  const btn = document.getElementById('simBtn');
  btn.disabled = true;
  document.getElementById('status').textContent = 'Transmitting the 99 Names...';

  try {
    const res = await fetch('/api/desert-reclamation/simulate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        area_km2: parseFloat(document.getElementById('area').value),
        radiation_rem: parseFloat(document.getElementById('radiation').value),
        shield_efficiency_pct: parseFloat(document.getElementById('efficiency').value),
        node_count: parseInt(document.getElementById('nodes').value),
      }),
    });
    const d = await res.json();

    document.getElementById('status').textContent =
      `Reclamation complete: ${d.total_reclamation_days} days, ${d.active_names_count} Names active, ` +
      `${d.final_state.species_count} species, ${d.final_state.ecosystem_status}`;

    showSummary(d);
    showNames(d);
    showPhases(d);
  } catch(e) {
    document.getElementById('status').textContent = 'Error: ' + e.message;
  }
  btn.disabled = false;
}

function showSummary(d) {
  const s = document.getElementById('summary');
  s.style.display = 'grid';
  const f = d.final_state;
  const gradeColors = {'SOVEREIGN':'#f1c40f','FORTIFIED':'#4caf50','ACTIVE':'#3498db','PARTIAL':'#e67e22','MINIMAL':'#e74c3c'};
  s.innerHTML = `
    <div class="sum"><div class="v gold">${d.area_km2}</div><div class="l">AREA (KM²)</div></div>
    <div class="sum"><div class="v red">${d.initial_radiation_rem}</div><div class="l">INITIAL RAD (REM)</div></div>
    <div class="sum"><div class="v green">${f.radiation_rem}</div><div class="l">FINAL RAD (REM)</div></div>
    <div class="sum"><div class="v green">${f.water_retention_pct}%</div><div class="l">WATER RETENTION</div></div>
    <div class="sum"><div class="v green">${f.soil_fertility_pct}%</div><div class="l">SOIL FERTILITY</div></div>
    <div class="sum"><div class="v gold">${f.species_count}</div><div class="l">SPECIES</div></div>
    <div class="sum"><div class="v" style="color:${gradeColors[d.coverage_grade]||'#888'}">${d.coverage_grade}</div><div class="l">COVERAGE GRADE</div></div>
    <div class="sum"><div class="v green">${f.ecosystem_status}</div><div class="l">ECOSYSTEM</div></div>
  `;
}

function showNames(d) {
  const grid = document.getElementById('namesGrid');
  grid.style.display = 'grid';
  grid.innerHTML = '';
  const roleColors = {
    'BASE CARRIER':'#f1c40f','RADIATION NEUTRALISER':'#e74c3c','SILICATE RESTRUCTURING':'#e67e22',
    'POROSITY EXPANSION':'#3498db','SUBTLE CATALYST':'#9b59b6','RESURRECTION TRIGGER':'#27ae60',
    'LIFE ACTIVATION':'#2ecc71','NUTRIENT CYCLING':'#1abc9c','PHOTOSYNTHETIC TRIGGER':'#f39c12',
    'SUCCESSION TRIGGER':'#2980b9','STABILITY ANCHOR':'#8e44ad'
  };

  for (const n of d.active_names) {
    const color = roleColors[n.role] || '#888';
    grid.innerHTML += `
      <div class="name-card">
        <div class="nn">${n.name} — ${n.attribute}</div>
        <div class="nr" style="color:${color}">${n.role} — ${n.frequency_hz} Hz</div>
        <div class="nd">${n.material_effect}</div>
        <div class="ne">${n.ecosystem_effect}</div>
      </div>
    `;
  }
}

function showPhases(d) {
  const tl = document.getElementById('timeline');
  tl.style.display = 'block';
  const phases = document.getElementById('phases');
  phases.innerHTML = '';

  let totalDays = 0;
  for (const p of d.phases) {
    totalDays += p.duration_days;
    const el = document.createElement('div');
    el.className = 'phase active';
    el.innerHTML = `
      <div class="ph-name">PHASE ${p.phase}: ${p.name}</div>
      <div class="ph-duration">DAY ${totalDays - p.duration_days + 1} → DAY ${totalDays} (${p.duration_days} days)</div>
      <div class="ph-desc">${p.description}</div>
      <div class="ph-change">${p.soil_change}</div>
      <div class="ph-indicator">${p.indicator}</div>
      <div class="freq-tags">${p.names_active.map(n => `<span class="freq-tag">${n}</span>`).join('')}</div>
      <div class="phase-metrics">
        <div class="pm"><div class="pv" style="color:#e74c3c">${p.radiation_rem}</div><div class="pl">RAD (REM)</div></div>
        <div class="pm"><div class="pv" style="color:#3498db">${p.water_retention_pct}%</div><div class="pl">WATER</div></div>
        <div class="pm"><div class="pv" style="color:#27ae60">${p.soil_fertility_pct}%</div><div class="pl">FERTILITY</div></div>
        <div class="pm"><div class="pv" style="color:#f1c40f">${p.biomass_kg_m2}</div><div class="pl">BIOMASS</div></div>
        <div class="pm"><div class="pv" style="color:#27ae60">${p.species_count}</div><div class="pl">SPECIES</div></div>
      </div>
    `;
    phases.appendChild(el);
  }
}
</script>
</body>
</html>"""
