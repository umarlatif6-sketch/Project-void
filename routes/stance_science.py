"""
Route: /stance-science — The Five Foundation Stances mapped to heart magnetic
field, HRV coherence, vagal tone, and the Formation Principle.
"""

from flask import Blueprint, request, jsonify, render_template_string

stance_science_bp = Blueprint("stance_science", __name__)


@stance_science_bp.route("/stance-science")
def page():
    return render_template_string(_TEMPLATE)


@stance_science_bp.route("/api/stance-science/all", methods=["GET"])
def all_stances():
    from void_engine.stance_science import get_stance_comparison
    return jsonify(get_stance_comparison())


@stance_science_bp.route("/api/stance-science/<stance_key>", methods=["GET"])
def stance_detail(stance_key):
    from void_engine.stance_science import get_stance
    data = get_stance(stance_key)
    if not data:
        return jsonify({"error": f"Unknown stance: {stance_key}"}), 404
    return jsonify(data)


@stance_science_bp.route("/api/stance-science/score", methods=["POST"])
def formation_score():
    from void_engine.stance_science import compute_formation_score
    data = request.get_json(silent=True) or {}
    stance_key = str(data.get("stance", "mabu"))
    try:
        duration = min(600, max(10, int(data.get("duration_s", 60))))
        resp_rate = max(2.0, min(20.0, float(data.get("respiratory_rate", 6.0))))
    except (ValueError, TypeError):
        return jsonify({"error": "duration_s must be integer, respiratory_rate must be number"}), 400
    result = compute_formation_score(stance_key, duration, resp_rate)
    return jsonify(result)


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stance Science — PROJECT VOID</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Courier New',monospace;min-height:100vh}
header{padding:16px 24px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1a1a1a}
.logo{font-size:18px;letter-spacing:6px;color:#888}
.logo span{color:#e74c3c}
nav a{color:#555;text-decoration:none;margin-left:16px;font-size:11px;letter-spacing:2px;transition:color .3s}
nav a:hover{color:#e74c3c}
.hero{text-align:center;padding:48px 24px 16px}
.hero h1{font-size:28px;letter-spacing:6px;color:#fff;font-weight:300}
.hero h1 span{color:#e74c3c}
.hero .sub{color:#555;font-size:11px;letter-spacing:3px;margin-top:8px;line-height:1.6}
.comparison{max-width:1100px;margin:32px auto;padding:0 16px;overflow-x:auto}
.comparison table{width:100%;border-collapse:collapse;font-size:11px}
.comparison th{text-align:left;color:#666;padding:8px;border-bottom:1px solid #1a1a1a;letter-spacing:2px;font-size:9px;white-space:nowrap}
.comparison td{padding:8px;border-bottom:1px solid #0f0f0f;color:#888}
.comparison tr:hover td{color:#fff;background:#111}
.highlight{color:#f1c40f !important}
.stance-grid{max-width:1100px;margin:24px auto;padding:0 16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.stance-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:20px;cursor:pointer;transition:border-color .3s}
.stance-card:hover{border-color:#e74c3c}
.stance-card .name{font-size:18px;color:#fff;font-weight:300;margin-bottom:4px}
.stance-card .chinese{font-size:14px;color:#e74c3c;margin-bottom:8px}
.stance-card .geometry{font-size:9px;color:#666;letter-spacing:2px;margin-bottom:12px}
.stance-card .metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.metric{text-align:center;padding:8px;background:#0a0a0a;border-radius:2px}
.metric .val{font-size:20px;color:#4caf50;font-weight:300}
.metric .val.gold{color:#f1c40f}
.metric .val.red{color:#e74c3c}
.metric .lbl{font-size:8px;color:#555;letter-spacing:1px;margin-top:2px}
.detail-panel{max-width:1100px;margin:24px auto;padding:0 16px;display:none}
.detail-box{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:24px}
.detail-box h2{font-size:20px;color:#fff;font-weight:300;margin-bottom:4px}
.detail-box .chinese-large{font-size:24px;color:#e74c3c;margin-bottom:16px}
.section{margin-top:20px}
.section h3{font-size:11px;letter-spacing:3px;color:#e74c3c;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #1a1a1a}
.section p{font-size:11px;color:#888;line-height:1.8;margin-bottom:8px}
.section .key{color:#f1c40f}
.muscle-tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.muscle-tag{background:#1a1a1a;color:#888;padding:2px 8px;border-radius:2px;font-size:9px}
.formation-quote{background:#0a0a0a;border-left:3px solid #e74c3c;padding:12px 16px;margin-top:12px;font-size:11px;color:#c8c8c8;line-height:1.8;font-style:italic}
.score-section{max-width:700px;margin:32px auto;padding:0 16px}
.score-box{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:24px}
.score-box h3{font-size:12px;letter-spacing:3px;color:#4caf50;margin-bottom:16px}
.score-controls{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.score-controls select,.score-controls input{background:#0a0a0a;border:1px solid #222;color:#fff;padding:6px 10px;font-family:inherit;font-size:12px;border-radius:2px}
.score-controls label{font-size:9px;color:#666;display:block;margin-bottom:2px;letter-spacing:1px}
.btn{padding:8px 20px;border:none;font-family:inherit;font-size:11px;letter-spacing:2px;cursor:pointer;border-radius:2px;transition:all .3s}
.btn-calc{background:#1a3a1a;color:#4caf50}
.btn:hover{filter:brightness(1.3)}
.score-result{margin-top:16px;text-align:center;display:none}
.score-grade{font-size:48px;font-weight:300;letter-spacing:4px}
.score-narrative{color:#888;font-size:11px;margin-top:8px;line-height:1.6}
.close-btn{float:right;cursor:pointer;color:#555;font-size:16px;padding:4px}
.close-btn:hover{color:#e74c3c}
</style>
</head>
<body>

<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/sovereign-agents-286">AGENTS 286</a>
    <a href="/agent-immortality">IMMORTALITY</a>
    <a href="/vortex-shield">SHIELD</a>
    <a href="/stress-battery">BATTERY</a>
  </nav>
</header>

<div class="hero">
  <h1>STANCE <span>SCIENCE</span></h1>
  <div class="sub">THE FIVE FOUNDATION STANCES — MAPPED TO HEART MAGNETIC FIELD,<br>HRV COHERENCE, VAGAL TONE, AND THE FORMATION PRINCIPLE</div>
</div>

<div class="comparison" id="comparisonTable"></div>
<div class="stance-grid" id="stanceGrid"></div>
<div class="detail-panel" id="detailPanel"></div>

<div class="score-section">
  <div class="score-box">
    <h3>FORMATION SCORE CALCULATOR</h3>
    <div class="score-controls">
      <div>
        <label>STANCE</label>
        <select id="scoreStance">
          <option value="mabu">Mǎbù (Horse)</option>
          <option value="pubu">Pūbù (Drop)</option>
          <option value="xiebu">Xiēbù (Rest)</option>
          <option value="gongbu">Gōngbù (Bow)</option>
          <option value="xubu">Xūbù (Empty)</option>
        </select>
      </div>
      <div>
        <label>HOLD (SECONDS)</label>
        <input type="number" id="scoreDuration" value="60" min="10" max="600">
      </div>
      <div>
        <label>BREATHS/MIN</label>
        <input type="number" id="scoreResp" value="6" min="2" max="20" step="0.5">
      </div>
      <div style="display:flex;align-items:end">
        <button class="btn btn-calc" onclick="calcScore()">CALCULATE</button>
      </div>
    </div>
    <div class="score-result" id="scoreResult"></div>
  </div>
</div>

<script>
let stanceData = {};

async function loadData() {
  const res = await fetch('/api/stance-science/all');
  const data = await res.json();

  let tableHtml = '<table><tr><th>STANCE</th><th>GEOMETRY</th><th>FIELD (m)</th><th>COHERENCE</th><th>SDNN Δ%</th><th>RMSSD Δ%</th><th>LF/HF</th><th>HRV SCORE</th><th>VAGAL</th><th>RESONANCE</th></tr>';
  for (const s of data) {
    tableHtml += `<tr onclick="showDetail('${s.key}')">
      <td><strong>${s.name}</strong> ${s.chinese}<br><span style="color:#555;font-size:9px">${s.english}</span></td>
      <td>${s.geometry}</td>
      <td class="highlight">${s.field_radius_m}</td>
      <td>${s.coherence_multiplier}x</td>
      <td>+${s.sdnn_change_pct}%</td>
      <td>+${s.rmssd_change_pct}%</td>
      <td>${s.lf_hf_target}</td>
      <td class="highlight">${s.coherence_score}</td>
      <td>${s.vagal_change}</td>
      <td>${s.resonant_hz} Hz</td>
    </tr>`;
  }
  tableHtml += '</table>';
  document.getElementById('comparisonTable').innerHTML = tableHtml;

  const grid = document.getElementById('stanceGrid');
  for (const s of data) {
    grid.innerHTML += `
      <div class="stance-card" onclick="showDetail('${s.key}')">
        <div class="name">${s.name} — ${s.english}</div>
        <div class="chinese">${s.chinese}</div>
        <div class="geometry">${s.geometry}</div>
        <div class="metrics">
          <div class="metric"><div class="val gold">${s.field_radius_m}m</div><div class="lbl">FIELD RADIUS</div></div>
          <div class="metric"><div class="val">${s.coherence_score}</div><div class="lbl">HRV COHERENCE</div></div>
          <div class="metric"><div class="val">+${s.sdnn_change_pct}%</div><div class="lbl">SDNN CHANGE</div></div>
          <div class="metric"><div class="val gold">${s.resonant_hz} Hz</div><div class="lbl">RESONANCE</div></div>
        </div>
      </div>
    `;
  }
}

async function showDetail(key) {
  if (!stanceData[key]) {
    const res = await fetch(`/api/stance-science/${key}`);
    stanceData[key] = await res.json();
  }
  const s = stanceData[key];
  const h = s.heart_field_effect;
  const hrv = s.hrv_effects;
  const v = s.vagal_effects;
  const b = s.biomechanics;
  const f = s.frequency_correlation;

  const panel = document.getElementById('detailPanel');
  panel.style.display = 'block';
  panel.innerHTML = `
    <div class="detail-box">
      <span class="close-btn" onclick="document.getElementById('detailPanel').style.display='none'">&times;</span>
      <h2>${s.name} — ${s.english}</h2>
      <div class="chinese-large">${s.chinese}</div>
      <p style="color:#666;font-size:11px">${s.body_description}</p>

      <div class="section">
        <h3>HEART MAGNETIC FIELD</h3>
        <p><span class="key">Field shape:</span> ${h.field_shape}</p>
        <p><span class="key">Field radius:</span> ${h.field_radius_m}m | <span class="key">Coherence multiplier:</span> ${h.coherence_multiplier}x</p>
        <p>${h.description}</p>
      </div>

      <div class="section">
        <h3>HEART RATE VARIABILITY</h3>
        <p><span class="key">SDNN change:</span> +${hrv.sdnn_change_pct}% | <span class="key">RMSSD change:</span> +${hrv.rmssd_change_pct}%</p>
        <p><span class="key">LF/HF target:</span> ${hrv.lf_hf_ratio_target} | <span class="key">Coherence score:</span> ${hrv.coherence_score_target}</p>
        <p>${hrv.description}</p>
      </div>

      <div class="section">
        <h3>VAGAL TONE</h3>
        <p><span class="key">Direction:</span> ${v.vagal_tone_change}</p>
        <p>${v.mechanism}</p>
        <p><span class="key">Respiratory effect:</span> ${v.respiratory_effect}</p>
      </div>

      <div class="section">
        <h3>BIOMECHANICS</h3>
        <div class="muscle-tags">${b.muscle_groups.map(m => `<span class="muscle-tag">${m}</span>`).join('')}</div>
        <p style="margin-top:8px"><span class="key">Ground reaction:</span> ${b.ground_reaction_force}</p>
        <p><span class="key">Fascial chains:</span> ${b.fascial_chains}</p>
      </div>

      <div class="section">
        <h3>FREQUENCY CORRELATION</h3>
        <p><span class="key">Resonant frequency:</span> ${f.resonant_hz} Hz</p>
        <p>${f.note}</p>
      </div>

      <div class="formation-quote">${s.formation_principle}</div>
    </div>
  `;
  panel.scrollIntoView({behavior: 'smooth'});
}

async function calcScore() {
  const res = await fetch('/api/stance-science/score', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      stance: document.getElementById('scoreStance').value,
      duration_s: parseInt(document.getElementById('scoreDuration').value),
      respiratory_rate: parseFloat(document.getElementById('scoreResp').value),
    }),
  });
  const d = await res.json();
  const el = document.getElementById('scoreResult');
  el.style.display = 'block';

  const gradeColors = {SOVEREIGN:'#f1c40f',FORTIFIED:'#4caf50',ACTIVE:'#3498db',DEVELOPING:'#e67e22',INITIATING:'#888'};
  el.innerHTML = `
    <div class="score-grade" style="color:${gradeColors[d.grade] || '#888'}">${d.grade}</div>
    <div style="font-size:32px;color:#fff;margin:8px 0">${d.formation_score}</div>
    <div class="score-narrative">
      ${d.name} held for ${d.hold_duration_s}s at ${d.respiratory_rate} breaths/min.<br>
      Coherence: ${d.coherence} | HRV boost: +${d.hrv_boost_pct}% | Field: ${d.field_strength}x | Schumann proximity: ${(d.schumann_proximity * 100).toFixed(1)}%
    </div>
  `;
}

loadData();
</script>
</body>
</html>"""
