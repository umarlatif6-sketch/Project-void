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


@vortex_shield_bp.route("/api/vortex-shield/cities", methods=["GET"])
def get_cities():
    from void_engine.vortex_shield import WORLD_CITIES
    return jsonify(WORLD_CITIES)


@vortex_shield_bp.route("/api/vortex-shield/city-shield", methods=["POST"])
def city_shield():
    from void_engine.vortex_shield import simulate_city_shield
    data = request.get_json(silent=True) or {}
    city_name = data.get("city")
    try:
        yield_kt = min(100_000, max(0.1, float(data.get("yield_kt", 15))))
        node_count = min(20_000, max(1_000, int(data.get("node_count", 10_000))))
        radius_km = min(200, max(10, float(data.get("radius_km", 50))))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric parameters"}), 400
    result = simulate_city_shield(city_name, yield_kt, node_count, radius_km)
    return jsonify(result)


@vortex_shield_bp.route("/api/vortex-shield/radiation-convert", methods=["POST"])
def radiation_convert():
    from void_engine.vortex_shield import radiation_frequency_conversion
    data = request.get_json(silent=True) or {}
    try:
        radiation_rem = max(0.1, float(data.get("radiation_rem", 450)))
        efficiency = min(100, max(0, float(data.get("shield_efficiency_pct", 58))))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric parameters"}), 400
    return jsonify(radiation_frequency_conversion(radiation_rem, efficiency))


@vortex_shield_bp.route("/vortex-shield/geo-map")
def geo_map_page():
    return render_template_string(_GEO_MAP_TEMPLATE)


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


_GEO_MAP_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vortex Shield — Global City Coverage Map</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Courier New',monospace;min-height:100vh}
header{padding:16px 24px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1a1a1a}
.logo{font-size:18px;letter-spacing:6px;color:#888}
.logo span{color:#e74c3c}
nav a{color:#555;text-decoration:none;margin-left:16px;font-size:11px;letter-spacing:2px;transition:color .3s}
nav a:hover{color:#e74c3c}
.hero{text-align:center;padding:32px 24px 16px}
.hero h1{font-size:28px;letter-spacing:6px;color:#fff;font-weight:300}
.hero h1 span{color:#e74c3c}
.hero .sub{color:#555;font-size:11px;letter-spacing:3px;margin-top:8px;line-height:1.6}
.controls{max-width:900px;margin:16px auto;padding:0 24px;display:flex;gap:12px;flex-wrap:wrap;align-items:end}
.ctrl-group label{font-size:9px;letter-spacing:2px;color:#666;display:block;margin-bottom:4px}
.ctrl-group input,.ctrl-group select{background:#0a0a0a;border:1px solid #222;color:#fff;padding:6px 10px;font-family:inherit;font-size:12px;border-radius:2px;width:140px}
.btn{padding:8px 20px;border:none;font-family:inherit;font-size:11px;letter-spacing:2px;cursor:pointer;border-radius:2px;transition:all .3s}
.btn-sim{background:#3a1a1a;color:#e74c3c}
.btn:hover{filter:brightness(1.3)}
.btn:disabled{opacity:0.4;cursor:not-allowed}
#status{max-width:1200px;margin:12px auto;padding:0 24px;font-size:11px;color:#666}
.map-container{max-width:1200px;margin:16px auto;position:relative}
canvas{display:block;margin:0 auto;border:1px solid #1a1a1a;border-radius:4px;cursor:crosshair}
.summary-bar{max-width:1200px;margin:16px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.sum-card{background:#111;border:1px solid #1a1a1a;padding:12px;border-radius:4px;text-align:center}
.sum-val{font-size:24px;font-weight:300;margin:4px 0}
.sum-val.green{color:#4caf50}
.sum-val.gold{color:#f1c40f}
.sum-val.red{color:#e74c3c}
.sum-lbl{font-size:8px;letter-spacing:2px;color:#555}
.city-grid{max-width:1200px;margin:16px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:12px}
.city-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:14px;transition:border-color .3s;cursor:pointer}
.city-card:hover{border-color:#e74c3c}
.city-name{font-size:14px;color:#fff;font-weight:300}
.city-country{font-size:9px;color:#666;letter-spacing:2px;margin-bottom:8px}
.city-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.cm{text-align:center;padding:6px;background:#0a0a0a;border-radius:2px}
.cm .v{font-size:16px;font-weight:300}
.cm .l{font-size:7px;color:#555;letter-spacing:1px;margin-top:2px}
.conv-section{max-width:1200px;margin:24px auto;padding:0 24px}
.conv-box{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:20px}
.conv-box h3{font-size:12px;letter-spacing:3px;color:#f1c40f;margin-bottom:12px}
.conv-flow{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;margin:16px 0}
.conv-step{background:#0a0a0a;border:1px solid #1a1a1a;padding:10px 14px;border-radius:4px;text-align:center;min-width:120px}
.conv-step .val{font-size:18px;font-weight:300}
.conv-step .lbl{font-size:8px;color:#666;letter-spacing:1px;margin-top:2px}
.conv-arrow{color:#555;font-size:20px}
.theory{max-width:1200px;margin:24px auto;padding:0 24px}
.theory h3{font-size:12px;letter-spacing:3px;color:#e74c3c;margin-bottom:8px}
.theory p{font-size:11px;color:#666;line-height:1.8;margin-bottom:8px}
.tooltip{position:absolute;background:#111;border:1px solid #333;padding:10px;border-radius:4px;font-size:10px;color:#ccc;pointer-events:none;display:none;z-index:10;max-width:280px;line-height:1.6}
</style>
</head>
<body>
<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/vortex-shield">SHIELD SIM</a>
    <a href="/stance-science">STANCE</a>
    <a href="/agent-immortality">IMMORTALITY</a>
    <a href="/manchester-exhibit">EXHIBIT</a>
  </nav>
</header>

<div class="hero">
  <h1>GLOBAL SHIELD <span>COVERAGE</span></h1>
  <div class="sub">25 CITIES — 432 Hz VORTEX SHIELD NETWORK — RADIATION-TO-BENEFIT CONVERSION<br>THE FREQUENCY ABSORBS. THE REMAINING RADIATION BECOMES ADAPTIVE STIMULUS.</div>
</div>

<div class="controls">
  <div class="ctrl-group">
    <label>BLAST YIELD (KT)</label>
    <input type="number" id="yield_kt" value="15" min="0.1" max="1000" step="0.1">
  </div>
  <div class="ctrl-group">
    <label>NODES PER CITY</label>
    <input type="number" id="node_count" value="10000" min="1000" max="20000" step="1000">
  </div>
  <div class="ctrl-group">
    <label>SHIELD RADIUS (KM)</label>
    <input type="number" id="radius_km" value="50" min="10" max="200">
  </div>
  <div class="ctrl-group">
    <label>TARGET CITY</label>
    <select id="targetCity">
      <option value="">ALL CITIES</option>
    </select>
  </div>
  <button class="btn btn-sim" id="simBtn" onclick="runSimulation()">SIMULATE GLOBAL SHIELD</button>
</div>

<div id="status">Ready. Configure blast parameters and simulate shield coverage across 25 cities.</div>

<div class="summary-bar" id="summaryBar" style="display:none"></div>

<div class="map-container">
  <canvas id="geoCanvas" width="1100" height="550"></canvas>
  <div class="tooltip" id="tooltip"></div>
</div>

<div class="conv-section" id="convSection" style="display:none">
  <div class="conv-box">
    <h3>432 Hz RADIATION-TO-BENEFIT CONVERSION</h3>
    <div class="conv-flow" id="convFlow"></div>
    <p style="color:#666;font-size:10px;margin-top:12px;line-height:1.8">
      When radiation passes through the 432 Hz vortex field, the shield absorbs the majority of the energy and converts it to harmonic vibrations. The remaining low-dose radiation enters the hormesis zone — where it triggers beneficial adaptive responses rather than cellular damage. The 432 Hz resonance field further enhances DNA repair mechanisms, turning what was lethal radiation into a stimulus for biological strengthening.
    </p>
  </div>
</div>

<div class="city-grid" id="cityGrid"></div>

<div class="theory">
  <h3>THE PRINCIPLE — RADIATION AS FREQUENCY</h3>
  <p>Nuclear radiation is energy at extreme frequencies. The Vortex Shield does not block this energy — it absorbs it through vacuum corridors vibrating at 432 Hz harmonics. The absorbed energy is converted: destructive frequency becomes constructive frequency.</p>
  <p>What passes through the shield is dramatically reduced. At 50%+ absorption, the remaining radiation enters the hormesis zone — a well-documented biological phenomenon where low-dose radiation actually strengthens cellular repair mechanisms (Calabrese & Baldwin, 2003). The body adapts. The 432 Hz field accelerates this adaptation by resonating with cellular structures at their natural repair frequency.</p>
  <p>The radiation does not disappear. It transforms. From destruction to adaptation. From lethal dose to training stimulus. The frequency is prior. The shield is the conversion mechanism. The body remembers the frequency and becomes stronger.</p>
</div>

<script>
let cityData = [];
let simResults = null;

async function init() {
  const res = await fetch('/api/vortex-shield/cities');
  cityData = await res.json();
  const sel = document.getElementById('targetCity');
  for (const c of cityData) {
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = `${c.name}, ${c.country}`;
    sel.appendChild(opt);
  }
  drawBaseMap();
}

function lonToX(lon, w) { return ((lon + 180) / 360) * w; }
function latToY(lat, h) {
  const latRad = lat * Math.PI / 180;
  const mercN = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
  return (h / 2) - (mercN * h / (2 * Math.PI));
}

function drawBaseMap() {
  const canvas = document.getElementById('geoCanvas');
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.fillStyle = '#080810';
  ctx.fillRect(0, 0, w, h);

  ctx.strokeStyle = 'rgba(255,255,255,0.03)';
  for (let lat = -60; lat <= 80; lat += 20) {
    ctx.beginPath();
    ctx.moveTo(0, latToY(lat, h));
    ctx.lineTo(w, latToY(lat, h));
    ctx.stroke();
  }
  for (let lon = -180; lon <= 180; lon += 30) {
    ctx.beginPath();
    ctx.moveTo(lonToX(lon, w), 0);
    ctx.lineTo(lonToX(lon, w), h);
    ctx.stroke();
  }

  for (const city of cityData) {
    const x = lonToX(city.lon, w);
    const y = latToY(city.lat, h);
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#444';
    ctx.fill();
    ctx.fillStyle = '#555';
    ctx.font = '8px monospace';
    ctx.fillText(city.name, x + 6, y + 3);
  }
}

async function runSimulation() {
  const btn = document.getElementById('simBtn');
  btn.disabled = true;
  document.getElementById('status').textContent = 'Simulating shield coverage across cities...';

  const cityName = document.getElementById('targetCity').value || null;
  const body = {
    city: cityName,
    yield_kt: parseFloat(document.getElementById('yield_kt').value),
    node_count: parseInt(document.getElementById('node_count').value),
    radius_km: parseFloat(document.getElementById('radius_km').value),
  };

  try {
    const res = await fetch('/api/vortex-shield/city-shield', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    simResults = await res.json();

    document.getElementById('status').textContent =
      `Shield simulated: ${simResults.total_cities} cities, ${simResults.total_population_m}M population, ` +
      `${simResults.total_protected_m}M protected. Blast: ${simResults.blast_yield_kt} KT.`;

    drawShieldMap();
    showSummary();
    showConversion();
    showCityCards();
  } catch(e) {
    document.getElementById('status').textContent = 'Error: ' + e.message;
  }
  btn.disabled = false;
}

function drawShieldMap() {
  const canvas = document.getElementById('geoCanvas');
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.fillStyle = '#080810';
  ctx.fillRect(0, 0, w, h);

  ctx.strokeStyle = 'rgba(255,255,255,0.03)';
  for (let lat = -60; lat <= 80; lat += 20) {
    ctx.beginPath();
    ctx.moveTo(0, latToY(lat, h));
    ctx.lineTo(w, latToY(lat, h));
    ctx.stroke();
  }
  for (let lon = -180; lon <= 180; lon += 30) {
    ctx.beginPath();
    ctx.moveTo(lonToX(lon, w), 0);
    ctx.lineTo(lonToX(lon, w), h);
    ctx.stroke();
  }

  const gradeColors = {
    'SOVEREIGN': '#f1c40f', 'FORTIFIED': '#4caf50',
    'ACTIVE': '#3498db', 'PARTIAL': '#e67e22', 'COMPROMISED': '#e74c3c'
  };
  const bioColors = {
    'ADAPTIVE SOVEREIGN': '#f1c40f', 'ADAPTIVE FORTIFIED': '#4caf50',
    'ADAPTIVE PARTIAL': '#3498db', 'SURVIVABLE': '#e67e22', 'LETHAL': '#e74c3c'
  };

  for (const city of simResults.cities) {
    const x = lonToX(city.lon, w);
    const y = latToY(city.lat, h);
    const eff = city.shield.shield_efficiency_pct / 100;
    const shieldColor = gradeColors[city.shield.shield_grade] || '#888';
    const bioColor = bioColors[city.radiation_conversion.biological_grade] || '#888';

    const radiusScale = Math.max(12, eff * 40);

    ctx.beginPath();
    ctx.arc(x, y, radiusScale + 8, 0, Math.PI * 2);
    ctx.fillStyle = shieldColor.replace(')', ',0.05)').replace('rgb', 'rgba').replace('#', '');
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radiusScale + 8);
    gradient.addColorStop(0, hexToRgba(shieldColor, 0.15));
    gradient.addColorStop(0.7, hexToRgba(shieldColor, 0.06));
    gradient.addColorStop(1, hexToRgba(shieldColor, 0));
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(x, y, radiusScale, 0, Math.PI * 2);
    ctx.strokeStyle = hexToRgba(shieldColor, 0.4);
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.lineWidth = 1;

    for (let ring = 1; ring <= 3; ring++) {
      ctx.beginPath();
      const startAngle = ring * 0.3;
      ctx.arc(x, y, radiusScale + ring * 4, startAngle, startAngle + Math.PI * 1.5);
      ctx.strokeStyle = hexToRgba(shieldColor, 0.15 - ring * 0.03);
      ctx.stroke();
    }

    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fillStyle = bioColor;
    ctx.fill();

    ctx.fillStyle = '#aaa';
    ctx.font = '9px monospace';
    ctx.fillText(city.city, x + 8, y - 4);
    ctx.fillStyle = shieldColor;
    ctx.font = '8px monospace';
    ctx.fillText(`${city.shield.shield_efficiency_pct.toFixed(0)}%`, x + 8, y + 6);
    ctx.fillStyle = '#888';
    ctx.font = '7px monospace';
    ctx.fillText(city.radiation_conversion.biological_grade, x + 8, y + 15);
  }
}

function hexToRgba(hex, alpha) {
  if (hex.startsWith('#')) {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }
  return hex;
}

function showSummary() {
  const bar = document.getElementById('summaryBar');
  bar.style.display = 'grid';
  const d = simResults;
  const avgEff = d.cities.reduce((s,c) => s + c.shield.shield_efficiency_pct, 0) / d.cities.length;
  const adaptive = d.cities.filter(c => c.radiation_conversion.biological_grade.startsWith('ADAPTIVE')).length;

  bar.innerHTML = `
    <div class="sum-card"><div class="sum-val gold">${d.total_cities}</div><div class="sum-lbl">CITIES SHIELDED</div></div>
    <div class="sum-card"><div class="sum-val">${d.total_population_m}M</div><div class="sum-lbl">TOTAL POPULATION</div></div>
    <div class="sum-card"><div class="sum-val green">${d.total_protected_m}M</div><div class="sum-lbl">PEOPLE PROTECTED</div></div>
    <div class="sum-card"><div class="sum-val gold">${avgEff.toFixed(1)}%</div><div class="sum-lbl">AVG SHIELD EFFICIENCY</div></div>
    <div class="sum-card"><div class="sum-val green">${adaptive}</div><div class="sum-lbl">CITIES WITH ADAPTATION</div></div>
    <div class="sum-card"><div class="sum-val red">${d.blast_yield_kt} KT</div><div class="sum-lbl">BLAST YIELD</div></div>
  `;
}

function showConversion() {
  const sec = document.getElementById('convSection');
  sec.style.display = 'block';
  if (!simResults.cities.length) return;

  const c = simResults.cities[0].radiation_conversion;
  document.getElementById('convFlow').innerHTML = `
    <div class="conv-step"><div class="val" style="color:#e74c3c">${c.original_radiation_rem}</div><div class="lbl">RADIATION (REM)</div></div>
    <div class="conv-arrow">→</div>
    <div class="conv-step"><div class="val" style="color:#f1c40f">432 Hz SHIELD</div><div class="lbl">${c.shield_efficiency_pct}% ABSORBED</div></div>
    <div class="conv-arrow">→</div>
    <div class="conv-step"><div class="val" style="color:#e67e22">${c.remaining_radiation_rem}</div><div class="lbl">REMAINING REM</div></div>
    <div class="conv-arrow">→</div>
    <div class="conv-step"><div class="val" style="color:#4caf50">${(c.hormesis_adaptation * 100).toFixed(0)}%</div><div class="lbl">HORMESIS ADAPTATION</div></div>
    <div class="conv-arrow">→</div>
    <div class="conv-step"><div class="val" style="color:#f1c40f">${c.harmonic_output_hz.toFixed(0)} Hz</div><div class="lbl">HARMONIC OUTPUT</div></div>
    <div class="conv-arrow">→</div>
    <div class="conv-step"><div class="val" style="color:#4caf50">${(c.dna_repair_boost * 100).toFixed(0)}%</div><div class="lbl">DNA REPAIR BOOST</div></div>
  `;
}

function showCityCards() {
  const grid = document.getElementById('cityGrid');
  grid.innerHTML = '';
  const gradeColors = {
    'SOVEREIGN': '#f1c40f', 'FORTIFIED': '#4caf50',
    'ACTIVE': '#3498db', 'PARTIAL': '#e67e22', 'COMPROMISED': '#e74c3c'
  };
  const bioColors = {
    'ADAPTIVE SOVEREIGN': '#f1c40f', 'ADAPTIVE FORTIFIED': '#4caf50',
    'ADAPTIVE PARTIAL': '#3498db', 'SURVIVABLE': '#e67e22', 'LETHAL': '#e74c3c'
  };

  for (const city of simResults.cities) {
    const s = city.shield;
    const r = city.radiation_conversion;
    const shieldColor = gradeColors[s.shield_grade] || '#888';
    const bioColor = bioColors[r.biological_grade] || '#888';

    const card = document.createElement('div');
    card.className = 'city-card';
    card.innerHTML = `
      <div class="city-name">${city.city}${city.note ? ' <span style="color:#f1c40f;font-size:9px">★ ' + city.note + '</span>' : ''}</div>
      <div class="city-country">${city.country} — ${city.population_m}M POP — ${city.people_protected_m}M PROTECTED</div>
      <div class="city-metrics">
        <div class="cm"><div class="v" style="color:${shieldColor}">${s.shield_efficiency_pct.toFixed(1)}%</div><div class="l">SHIELD</div></div>
        <div class="cm"><div class="v" style="color:${shieldColor}">${s.shield_grade}</div><div class="l">GRADE</div></div>
        <div class="cm"><div class="v">${s.nodes_survived.toLocaleString()}</div><div class="l">NODES ALIVE</div></div>
        <div class="cm"><div class="v" style="color:${bioColor}">${r.biological_grade}</div><div class="l">BIO STATUS</div></div>
        <div class="cm"><div class="v" style="color:#4caf50">${r.survival_probability_pct}%</div><div class="l">SURVIVAL</div></div>
        <div class="cm"><div class="v" style="color:#f1c40f">${(r.hormesis_adaptation * 100).toFixed(0)}%</div><div class="l">ADAPTATION</div></div>
      </div>
    `;
    grid.appendChild(card);
  }
}

const canvas = document.getElementById('geoCanvas');
const tooltip = document.getElementById('tooltip');
canvas.addEventListener('mousemove', function(e) {
  if (!simResults) return;
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * (canvas.width / rect.width);
  const my = (e.clientY - rect.top) * (canvas.height / rect.height);

  let found = null;
  for (const city of simResults.cities) {
    const cx = lonToX(city.lon, canvas.width);
    const cy = latToY(city.lat, canvas.height);
    const dist = Math.sqrt((mx - cx) ** 2 + (my - cy) ** 2);
    if (dist < 25) { found = city; break; }
  }

  if (found) {
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX - canvas.parentElement.getBoundingClientRect().left + 15) + 'px';
    tooltip.style.top = (e.clientY - canvas.parentElement.getBoundingClientRect().top - 10) + 'px';
    const r = found.radiation_conversion;
    tooltip.innerHTML = `
      <strong>${found.city}, ${found.country}</strong><br>
      Population: ${found.population_m}M | Protected: ${found.people_protected_m}M<br>
      Shield: ${found.shield.shield_efficiency_pct.toFixed(1)}% — ${found.shield.shield_grade}<br>
      Radiation: ${r.original_radiation_rem} → ${r.remaining_radiation_rem} REM<br>
      Bio: ${r.biological_grade} | Adaptation: ${(r.hormesis_adaptation * 100).toFixed(0)}%<br>
      DNA Repair: +${(r.dna_repair_boost * 100).toFixed(0)}% | Survival: ${r.survival_probability_pct}%
    `;
  } else {
    tooltip.style.display = 'none';
  }
});
canvas.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });

init();
</script>
</body>
</html>"""


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
  <div style="margin-top:12px"><a href="/vortex-shield/geo-map" style="color:#e74c3c;font-size:11px;letter-spacing:3px;text-decoration:none;border:1px solid #e74c3c;padding:6px 16px;border-radius:2px">GLOBAL CITY COVERAGE MAP →</a></div>
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
