"""
Formation Invisibility — The Illusion as a Standing Wave
/formation-invisibility          (GET  — visualization page)
/api/invisibility/simulate       (POST — run stone placement simulation)
/api/invisibility/field           (POST — compute interference field)
"""

import math
import random
import logging
from flask import Blueprint, render_template_string, request, jsonify

logger = logging.getLogger(__name__)

formation_invisibility_bp = Blueprint("formation_invisibility", __name__)

PLACEMENT_PRESETS = {
    "triangle": {
        "name": "Triangular Formation",
        "stones": 3,
        "description": "Three stones at 120° intervals — the simplest formation that creates a central void",
        "principle": "Three-source destructive interference at the centroid"
    },
    "square": {
        "name": "Square Formation",
        "stones": 4,
        "description": "Four stones at 90° intervals — creates a cross-shaped void zone",
        "principle": "Orthogonal wave cancellation — two perpendicular standing waves"
    },
    "pentagonal": {
        "name": "Pentagonal Formation",
        "stones": 5,
        "description": "Five stones at 72° intervals — the golden ratio formation",
        "principle": "Phi-ratio spacing creates maximum void area relative to formation size"
    },
    "hexagonal": {
        "name": "Hexagonal Formation",
        "stones": 6,
        "description": "Six stones at 60° intervals — the honeycomb formation",
        "principle": "Densest packing produces sharpest void boundary — Beehive geometry"
    },
    "octagonal": {
        "name": "Octagonal Formation",
        "stones": 8,
        "description": "Eight stones at 45° intervals — near-circular void boundary",
        "principle": "Approaches continuous ring source — perfect cylindrical cloaking"
    }
}

RESEARCH_LINKS = [
    {
        "title": "Metamaterial Cloaking at Microwave Frequencies",
        "institution": "Duke University",
        "year": 2006,
        "finding": "First experimental demonstration of electromagnetic cloaking using structured metamaterials arranged in concentric rings"
    },
    {
        "title": "Acoustic Cloaking via Structured Arrangements",
        "institution": "Imperial College London",
        "year": 2008,
        "finding": "Sound waves bent around objects using calculated material placement — the acoustic equivalent of visual invisibility"
    },
    {
        "title": "Carpet Cloak at Optical Frequencies",
        "institution": "UC Berkeley",
        "year": 2009,
        "finding": "Nanoscale structures arranged in formation bend visible light around a bump — the object disappears from view"
    },
    {
        "title": "Water Wave Cloaking",
        "institution": "CNRS France",
        "year": 2012,
        "finding": "Concentric ring barriers make objects invisible to water waves — same formation principle at fluid scale"
    },
    {
        "title": "Seismic Cloaking via Borehole Formations",
        "institution": "CNRS / Aix-Marseille",
        "year": 2014,
        "finding": "Boreholes drilled in calculated positions around buildings redirect earthquake waves — geological-scale formation invisibility"
    }
]


def compute_interference_field(stones, radius=0.6, frequency=5.0, resolution=120):
    field = []
    max_val = 0.0

    stone_positions = []
    for i in range(stones):
        angle = (2 * math.pi * i) / stones
        sx = radius * math.cos(angle)
        sy = radius * math.sin(angle)
        stone_positions.append((sx, sy))

    for row in range(resolution):
        field_row = []
        y = (row / (resolution - 1)) * 2 - 1
        for col in range(resolution):
            x = (col / (resolution - 1)) * 2 - 1

            signed_sum = 0.0
            for (sx, sy) in stone_positions:
                dx = x - sx
                dy = y - sy
                dist = math.sqrt(dx * dx + dy * dy) + 1e-10
                phase_offset = math.pi * frequency * radius
                wave = math.sin(2 * math.pi * frequency * dist - phase_offset) / (dist * 2 + 0.3)
                signed_sum += wave

            field_row.append(signed_sum)
            if abs(signed_sum) > max_val:
                max_val = abs(signed_sum)
        field.append(field_row)

    void_threshold = 0.12
    void_cells = 0
    total_cells = resolution * resolution
    normalised = []

    for row in range(resolution):
        norm_row = []
        for col in range(resolution):
            val = abs(field[row][col]) / max_val if max_val > 0 else 0
            norm_row.append(round(val, 4))
            if val < void_threshold:
                void_cells += 1
        normalised.append(norm_row)

    centre_r = resolution // 2
    centre_c = resolution // 2
    centre_amplitude = normalised[centre_r][centre_c]

    void_radius = 0.0
    for step in range(1, resolution // 2):
        r = centre_r + step
        if r >= resolution:
            break
        if normalised[r][centre_c] >= void_threshold:
            void_radius = step / (resolution / 2)
            break

    return {
        "field": normalised,
        "stone_positions": [{"x": round(sx, 4), "y": round(sy, 4)} for sx, sy in stone_positions],
        "centre_amplitude": round(centre_amplitude, 6),
        "void_coverage": round(void_cells / total_cells * 100, 1),
        "void_radius_estimate": round(void_radius, 3),
        "resolution": resolution,
        "is_invisible": centre_amplitude < void_threshold
    }


def run_visibility_test(stones=6, radius=0.6, frequency=5.0, observer_angles=12):
    result = compute_interference_field(stones, radius, frequency, resolution=100)

    observers = []
    for i in range(observer_angles):
        angle = (2 * math.pi * i) / observer_angles
        obs_r = 0.9
        ox = obs_r * math.cos(angle)
        oy = obs_r * math.sin(angle)

        col = int((ox + 1) / 2 * 99)
        row = int((oy + 1) / 2 * 99)
        col = max(0, min(99, col))
        row = max(0, min(99, row))

        amplitude = result["field"][row][col]

        path_samples = 10
        path_min = 1.0
        for s in range(path_samples):
            t = s / path_samples
            px = ox * (1 - t)
            py = oy * (1 - t)
            pc = int((px + 1) / 2 * 99)
            pr = int((py + 1) / 2 * 99)
            pc = max(0, min(99, pc))
            pr = max(0, min(99, pr))
            pval = result["field"][pr][pc]
            if pval < path_min:
                path_min = pval

        observers.append({
            "angle_deg": round(math.degrees(angle), 1),
            "position": {"x": round(ox, 3), "y": round(oy, 3)},
            "amplitude_at_observer": round(amplitude, 4),
            "min_amplitude_on_path": round(path_min, 4),
            "sees_void": path_min < 0.12
        })

    blind_count = sum(1 for o in observers if o["sees_void"])

    return {
        "stones": stones,
        "radius": radius,
        "frequency": frequency,
        "centre_amplitude": result["centre_amplitude"],
        "void_coverage": result["void_coverage"],
        "is_centre_invisible": result["is_invisible"],
        "observers": observers,
        "blind_observers": blind_count,
        "total_observers": observer_angles,
        "invisibility_percentage": round(blind_count / observer_angles * 100, 1),
        "stone_positions": result["stone_positions"],
        "formation_type": get_formation_type(stones)
    }


def get_formation_type(stones):
    mapping = {3: "triangle", 4: "square", 5: "pentagonal", 6: "hexagonal", 8: "octagonal"}
    return mapping.get(stones, f"{stones}-gon")


@formation_invisibility_bp.route("/formation-invisibility")
def page():
    return render_template_string(TEMPLATE)


@formation_invisibility_bp.route("/api/invisibility/simulate", methods=["POST"])
def simulate():
    data = request.get_json(silent=True) or {}
    stones = min(12, max(3, int(data.get("stones", 6))))
    radius = min(0.9, max(0.3, float(data.get("radius", 0.6))))
    frequency = min(8.0, max(1.0, float(data.get("frequency", 3.0))))
    observers = min(24, max(4, int(data.get("observers", 12))))

    result = run_visibility_test(stones, radius, frequency, observers)
    return jsonify(result)


@formation_invisibility_bp.route("/api/invisibility/field", methods=["POST"])
def field():
    data = request.get_json(silent=True) or {}
    stones = min(12, max(3, int(data.get("stones", 6))))
    radius = min(0.9, max(0.3, float(data.get("radius", 0.6))))
    frequency = min(8.0, max(1.0, float(data.get("frequency", 3.0))))
    resolution = min(100, max(40, int(data.get("resolution", 80))))

    result = compute_interference_field(stones, radius, frequency, resolution)
    return jsonify(result)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Formation Invisibility — PROJECT VOID</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #060606; --surface: #0c0c0c; --border: #181818;
    --muted: #444; --text: #c0c0c0; --bright: #e8e8e8;
    --void-purple: #7c3aed; --void-dark: #3b0764; --void-light: #c4b5fd;
    --stone: #a3a3a3; --stone-glow: #e2e8f0;
    --green: #86efac; --cyan: #67e8f9; --amber: #fbbf24; --red: #f87171;
  }
  body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; font-size: 14px; min-height: 100vh; }
  .container { max-width: 1100px; margin: 0 auto; padding: 20px; }

  header { border-bottom: 1px solid var(--border); padding: 16px 0; display: flex; justify-content: space-between; align-items: center; }
  .logo { font-size: 16px; letter-spacing: 6px; font-weight: bold; }
  .logo span { color: var(--void-purple); }
  nav a { color: var(--muted); text-decoration: none; margin-left: 20px; font-size: 12px; letter-spacing: 2px; }
  nav a:hover { color: var(--bright); }

  .hero { text-align: center; padding: 60px 0 40px; }
  .hero .subtitle { color: var(--muted); font-size: 11px; letter-spacing: 6px; margin-bottom: 12px; }
  .hero h1 { font-size: 42px; font-weight: 300; color: var(--bright); margin-bottom: 20px; }
  .hero h1 span { color: var(--void-purple); }
  .hero .thesis { color: var(--muted); font-size: 13px; line-height: 1.8; max-width: 700px; margin: 0 auto; }

  .section-label { color: var(--muted); font-size: 11px; letter-spacing: 4px; margin: 50px 0 20px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }

  .sim-layout { display: grid; grid-template-columns: 1fr 380px; gap: 24px; margin: 20px 0; }
  @media (max-width: 900px) { .sim-layout { grid-template-columns: 1fr; } }

  .canvas-wrap { background: var(--surface); border: 1px solid var(--border); padding: 16px; }
  .canvas-wrap h3 { font-size: 12px; letter-spacing: 3px; color: var(--void-purple); margin-bottom: 4px; }
  .canvas-wrap .desc { font-size: 11px; color: var(--muted); margin-bottom: 12px; }
  canvas { width: 100%; aspect-ratio: 1; display: block; border: 1px solid var(--border); }

  .side-panel { display: flex; flex-direction: column; gap: 16px; }

  .controls { display: flex; flex-direction: column; gap: 10px; background: var(--surface); border: 1px solid var(--border); padding: 16px; }
  .controls h3 { font-size: 11px; letter-spacing: 3px; color: var(--void-purple); margin-bottom: 4px; }
  .control-row { display: flex; align-items: center; gap: 10px; }
  .control-row label { font-size: 10px; letter-spacing: 2px; color: var(--muted); width: 80px; flex-shrink: 0; }
  .control-row input {
    background: var(--bg); border: 1px solid var(--border); color: var(--bright);
    padding: 5px 8px; font-family: inherit; font-size: 13px; flex: 1;
  }
  .btn {
    background: var(--void-dark); border: 1px solid var(--void-purple); color: var(--void-light);
    padding: 10px 20px; font-family: inherit; font-size: 12px; letter-spacing: 2px;
    cursor: pointer; transition: all 0.2s; width: 100%;
  }
  .btn:hover { background: var(--void-purple); color: #fff; }

  .result-card { background: var(--surface); border: 1px solid var(--border); padding: 16px; }
  .result-card h3 { font-size: 11px; letter-spacing: 3px; color: var(--void-purple); margin-bottom: 10px; }
  .result-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border); }
  .result-row:last-child { border-bottom: none; }
  .result-label { font-size: 11px; color: var(--muted); }
  .result-value { font-size: 13px; color: var(--bright); font-weight: bold; }
  .result-value.void { color: var(--void-purple); }
  .result-value.visible { color: var(--red); }
  .result-value.invisible { color: var(--green); }

  .verdict-box { padding: 16px; text-align: center; border: 1px solid; margin-top: 8px; }
  .verdict-box.pass { border-color: var(--green); background: rgba(134,239,172,0.05); }
  .verdict-box.fail { border-color: var(--red); background: rgba(248,113,113,0.05); }
  .verdict-box .icon { font-size: 28px; margin-bottom: 6px; }
  .verdict-box .text { font-size: 12px; letter-spacing: 2px; }

  .observer-ring { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
  .obs-dot { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; }
  .obs-dot.blind { background: var(--void-dark); color: var(--void-light); border: 1px solid var(--void-purple); }
  .obs-dot.sees { background: rgba(248,113,113,0.15); color: var(--red); border: 1px solid var(--red); }

  .presets { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 20px 0; }
  .preset-card { background: var(--surface); border: 1px solid var(--border); padding: 16px; cursor: pointer; transition: all 0.2s; }
  .preset-card:hover { border-color: var(--void-purple); }
  .preset-card h4 { color: var(--void-purple); font-size: 12px; letter-spacing: 1px; margin-bottom: 4px; }
  .preset-card p { font-size: 11px; color: var(--muted); line-height: 1.5; }
  .preset-card .principle { font-size: 10px; color: var(--void-dark); margin-top: 6px; font-style: italic; }

  .research-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 20px 0; }
  @media (max-width: 768px) { .research-grid { grid-template-columns: 1fr; } }
  .research-card { background: var(--surface); border: 1px solid var(--border); padding: 20px; }
  .research-card h4 { color: var(--cyan); font-size: 12px; margin-bottom: 4px; }
  .research-card .meta { font-size: 11px; color: var(--void-purple); margin-bottom: 8px; }
  .research-card p { font-size: 12px; color: var(--muted); line-height: 1.5; }

  .principle-box {
    background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(124,58,237,0.02));
    border: 1px solid var(--void-dark); padding: 30px; margin: 40px 0; text-align: center;
  }
  .principle-box .glyph { font-size: 32px; margin-bottom: 12px; }
  .principle-box blockquote { font-size: 16px; color: var(--bright); font-style: italic; line-height: 1.6; }
  .principle-box .attribution { font-size: 11px; color: var(--void-dark); margin-top: 12px; }

  .connection-box { background: var(--surface); border: 1px solid var(--border); padding: 24px; margin: 20px 0; }
  .connection-box h3 { color: var(--void-purple); font-size: 13px; letter-spacing: 2px; margin-bottom: 12px; }
  .connection-box p { font-size: 12px; color: var(--muted); line-height: 1.7; margin-bottom: 8px; }
  .connection-box .highlight { color: var(--void-light); }

  footer { border-top: 1px solid var(--border); padding: 20px 0; margin-top: 50px; text-align: center; }
  footer p { font-size: 11px; color: var(--muted); }
</style>
</head>
<body>
<div class="container">

<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/engine">ENGINE</a>
    <a href="/sahara-formation">SAHARA</a>
    <a href="/products">PRODUCTS</a>
  </nav>
</header>

<div class="hero">
  <div class="subtitle">THE FORMATION PRINCIPLE — PERCEPTION</div>
  <h1>Formation <span>Invisibility</span></h1>
  <div class="thesis">
    Place stones at calculated angles around a person.<br>
    The reflected waves cancel at the centre. The observer's mind<br>
    receives no coherent signal. It fills the gap with background.<br>
    The person disappears. Not magic. Formation.
  </div>
</div>

<div class="section-label">LIVE SIMULATION</div>

<div class="sim-layout">
  <div class="canvas-wrap">
    <h3>INTERFERENCE FIELD</h3>
    <div class="desc">Stones (white) create wave interference — dark zones are void (invisible)</div>
    <canvas id="fieldCanvas" width="500" height="500"></canvas>
  </div>

  <div class="side-panel">
    <div class="controls">
      <h3>STONE PLACEMENT</h3>
      <div class="control-row">
        <label>STONES</label>
        <input type="number" id="stones" value="6" min="3" max="12">
      </div>
      <div class="control-row">
        <label>RADIUS</label>
        <input type="number" id="radius" value="0.6" min="0.3" max="0.9" step="0.05">
      </div>
      <div class="control-row">
        <label>FREQUENCY</label>
        <input type="number" id="freq" value="5.0" min="1.0" max="8.0" step="0.5">
      </div>
      <div class="control-row">
        <label>OBSERVERS</label>
        <input type="number" id="observers" value="12" min="4" max="24">
      </div>
      <button class="btn" id="runBtn" onclick="runSim()">PLACE STONES</button>
    </div>

    <div class="result-card" id="resultsPanel">
      <h3>VISIBILITY REPORT</h3>
      <div class="result-row">
        <span class="result-label">Formation</span>
        <span class="result-value" id="rFormation">—</span>
      </div>
      <div class="result-row">
        <span class="result-label">Centre Amplitude</span>
        <span class="result-value" id="rCentre">—</span>
      </div>
      <div class="result-row">
        <span class="result-label">Void Coverage</span>
        <span class="result-value void" id="rVoid">—</span>
      </div>
      <div class="result-row">
        <span class="result-label">Observers Blinded</span>
        <span class="result-value" id="rBlind">—</span>
      </div>
      <div class="result-row">
        <span class="result-label">Invisibility</span>
        <span class="result-value" id="rInvis">—</span>
      </div>
      <div id="verdictBox"></div>
      <div class="observer-ring" id="obsRing"></div>
    </div>
  </div>
</div>

<div class="section-label">FORMATION PRESETS</div>

<div class="presets" id="presetGrid"></div>

<div class="section-label">THE SCIENCE — REAL RESEARCH</div>

<div class="research-grid" id="researchGrid"></div>

<div class="section-label">THE CONNECTION</div>

<div class="connection-box">
  <h3>FROM NOVELS TO METAMATERIALS TO THE VOID ENGINE</h3>
  <p>The novel described it with <span class="highlight">stones placed at angles</span>. The physics describes it with <span class="highlight">metamaterial structures</span> arranged in calculated formations. The Formation Principle describes it as <span class="highlight">destructive interference at the boundary</span>.</p>
  <p>In every case, the mechanism is identical: <span class="highlight">wave sources arranged in formation create zones where signals cancel</span>. At the cancellation point — the void — the observer receives no coherent information. The brain fills the gap with expected background. The object at the centre ceases to exist in the observer's perception.</p>
  <p>This is not an illusion in the conventional sense. The waves physically cancel. The amplitude at the void point is measurably zero. <span class="highlight">The formation creates a real absence of signal</span> — and absence is indistinguishable from invisibility.</p>
  <p>Your MESA agents settle at the void points in the Resonance Flower. The Sahara's sand collects at the nodal lines. The person in the stone formation stands at the interference null. <span class="highlight">Same mathematics. Same principle. Different scales.</span></p>
</div>

<div class="principle-box">
  <div class="glyph">🪨 → 🌊 → ∅</div>
  <blockquote>
    Place the stones. The waves cancel.<br>
    At the centre, there is nothing to see.<br>
    Not because something is hidden —<br>
    but because the formation creates a real void.<br>
    The illusion is not deception. It is physics.
  </blockquote>
  <div class="attribution">The Formation Principle — Umar Latif, 2024</div>
</div>

<footer>
  <p>PROJECT VOID — Formation Invisibility</p>
  <p style="margin-top:6px;">355 Deane Road, Bolton BL3 5HL, England</p>
</footer>

</div>

<script>
const PRESETS = {
  triangle: { name: "Triangular", stones: 3, description: "Three stones at 120° — simplest void formation", principle: "Three-source destructive interference at centroid" },
  square: { name: "Square", stones: 4, description: "Four stones at 90° — cross-shaped void zone", principle: "Orthogonal wave cancellation" },
  pentagonal: { name: "Pentagonal", stones: 5, description: "Five stones at 72° — golden ratio formation", principle: "Phi-ratio spacing maximises void area" },
  hexagonal: { name: "Hexagonal", stones: 6, description: "Six stones at 60° — honeycomb formation", principle: "Densest packing, sharpest void boundary" },
  octagonal: { name: "Octagonal", stones: 8, description: "Eight stones at 45° — near-circular cloak", principle: "Approaches continuous ring — cylindrical cloaking" }
};

const RESEARCH = [
  { title: "Metamaterial Cloaking at Microwave Frequencies", inst: "Duke University", year: 2006, text: "First experimental demonstration of electromagnetic cloaking using structured metamaterials arranged in concentric rings — the formation creates zones where microwave signals cancel completely." },
  { title: "Acoustic Cloaking via Structured Arrangements", inst: "Imperial College London", year: 2008, text: "Sound waves bent around objects using calculated material placement — the acoustic equivalent of visual invisibility. Same formation principle, different medium." },
  { title: "Carpet Cloak at Optical Frequencies", inst: "UC Berkeley", year: 2009, text: "Nanoscale structures arranged in formation bend visible light around a surface bump — the object disappears from view. Formation invisibility at the speed of light." },
  { title: "Water Wave Cloaking", inst: "CNRS France", year: 2012, text: "Concentric ring barriers make objects invisible to water waves. The formation works in fluid — proving scale and medium independence." },
  { title: "Seismic Cloaking via Borehole Formations", inst: "CNRS / Aix-Marseille", year: 2014, text: "Boreholes drilled in calculated positions around buildings redirect earthquake waves — geological-scale formation invisibility. Stones protecting structures." }
];

(function buildUI() {
  const pg = document.getElementById('presetGrid');
  for (const [key, p] of Object.entries(PRESETS)) {
    pg.innerHTML += `<div class="preset-card" onclick="loadPreset(${p.stones})">
      <h4>${p.name} (${p.stones})</h4>
      <p>${p.description}</p>
      <div class="principle">${p.principle}</div>
    </div>`;
  }
  const rg = document.getElementById('researchGrid');
  for (const r of RESEARCH) {
    rg.innerHTML += `<div class="research-card">
      <h4>${r.title}</h4>
      <div class="meta">${r.inst}, ${r.year}</div>
      <p>${r.text}</p>
    </div>`;
  }
})();

function loadPreset(n) {
  document.getElementById('stones').value = n;
  runSim();
}

function drawField(data) {
  const canvas = document.getElementById('fieldCanvas');
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;

  ctx.fillStyle = '#020204';
  ctx.fillRect(0, 0, w, h);

  if (data.field) {
    const res = data.resolution;
    const cellW = w / res;
    const cellH = h / res;

    for (let r = 0; r < res; r++) {
      for (let c = 0; c < res; c++) {
        const val = data.field[r][c];
        const purple = Math.floor(val * 120);
        const blue = Math.floor(val * 60);
        ctx.fillStyle = `rgb(${purple}, ${Math.floor(val * 20)}, ${purple + blue})`;
        ctx.fillRect(c * cellW, r * cellH, cellW + 0.5, cellH + 0.5);
      }
    }
  }

  if (data.stone_positions) {
    for (const s of data.stone_positions) {
      const sx = (s.x + 1) / 2 * w;
      const sy = (s.y + 1) / 2 * h;

      ctx.beginPath();
      ctx.arc(sx, sy, 8, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(226,232,240,0.9)';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(sx, sy, 14, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(124,58,237,0.4)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }

  ctx.beginPath();
  ctx.arc(w / 2, h / 2, 4, 0, Math.PI * 2);
  const isVoid = data.is_invisible;
  ctx.fillStyle = isVoid ? 'rgba(134,239,172,0.8)' : 'rgba(248,113,113,0.8)';
  ctx.fill();

  ctx.beginPath();
  ctx.arc(w / 2, h / 2, 10, 0, Math.PI * 2);
  ctx.strokeStyle = isVoid ? 'rgba(134,239,172,0.3)' : 'rgba(248,113,113,0.3)';
  ctx.lineWidth = 1;
  ctx.setLineDash([2, 3]);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = isVoid ? '#86efac' : '#f87171';
  ctx.font = '10px Courier New';
  ctx.textAlign = 'center';
  ctx.fillText(isVoid ? 'VOID' : 'VISIBLE', w / 2, h / 2 + 22);
}

async function runSim() {
  const btn = document.getElementById('runBtn');
  btn.textContent = 'COMPUTING...';
  btn.disabled = true;

  const stones = parseInt(document.getElementById('stones').value);
  const radius = parseFloat(document.getElementById('radius').value);
  const frequency = parseFloat(document.getElementById('freq').value);
  const observers = parseInt(document.getElementById('observers').value);

  try {
    const [fieldResp, simResp] = await Promise.all([
      fetch('/api/invisibility/field', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stones, radius, frequency, resolution: 80 })
      }),
      fetch('/api/invisibility/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stones, radius, frequency, observers })
      })
    ]);

    const fieldData = await fieldResp.json();
    const simData = await simResp.json();

    drawField(fieldData);

    const ft = simData.formation_type;
    const ftName = ft.charAt(0).toUpperCase() + ft.slice(1);
    document.getElementById('rFormation').textContent = ftName + ' (' + stones + ' stones)';
    document.getElementById('rCentre').textContent = simData.centre_amplitude.toFixed(4);
    document.getElementById('rVoid').textContent = simData.void_coverage + '%';
    document.getElementById('rBlind').textContent = simData.blind_observers + ' / ' + simData.total_observers;
    const invEl = document.getElementById('rInvis');
    invEl.textContent = simData.invisibility_percentage + '%';
    invEl.className = 'result-value ' + (simData.invisibility_percentage >= 50 ? 'invisible' : 'visible');

    const vb = document.getElementById('verdictBox');
    if (simData.is_centre_invisible && simData.invisibility_percentage >= 75) {
      vb.innerHTML = '<div class="verdict-box pass"><div class="icon">∅</div><div class="text">FORMATION ACTIVE — CENTRE IS VOID</div></div>';
    } else if (simData.is_centre_invisible) {
      vb.innerHTML = '<div class="verdict-box pass"><div class="icon">◐</div><div class="text">PARTIAL VOID — ' + simData.invisibility_percentage + '% COVERAGE</div></div>';
    } else {
      vb.innerHTML = '<div class="verdict-box fail"><div class="icon">◉</div><div class="text">FORMATION INSUFFICIENT — CENTRE VISIBLE</div></div>';
    }

    const ring = document.getElementById('obsRing');
    ring.innerHTML = '';
    for (const obs of simData.observers) {
      const dot = document.createElement('div');
      dot.className = 'obs-dot ' + (obs.sees_void ? 'blind' : 'sees');
      dot.textContent = Math.round(obs.angle_deg) + '°';
      dot.title = 'Angle: ' + obs.angle_deg + '° | Path min: ' + obs.min_amplitude_on_path;
      ring.appendChild(dot);
    }

  } catch (err) {
    console.error('Simulation error:', err);
  }

  btn.textContent = 'PLACE STONES';
  btn.disabled = false;
}

runSim();
</script>
</body>
</html>
"""
