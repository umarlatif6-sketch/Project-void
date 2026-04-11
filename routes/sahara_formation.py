"""
Sahara Formation — The Desert as a Standing Wave
/sahara-formation                (GET  — visualization page)
/api/sahara/simulate             (POST — run desert formation simulation)
/api/sahara/compare              (GET  — Chladni vs desert pattern data)
"""

import math
import random
import logging
from flask import Blueprint, render_template_string, request, jsonify

logger = logging.getLogger(__name__)

sahara_formation_bp = Blueprint("sahara_formation", __name__)

DUNE_TYPES = {
    "star": {
        "name": "Star Dune",
        "winds": 3,
        "description": "Multi-directional wind interference creates radial symmetry",
        "chladni_analog": "High-order mode shape — multiple nodal lines intersecting",
        "example": "Grand Erg Oriental, Algeria"
    },
    "seif": {
        "name": "Linear Seif Dune",
        "winds": 1,
        "description": "Single dominant wind creates parallel ridges at regular intervals",
        "chladni_analog": "Fundamental mode — parallel nodal lines on a rectangular plate",
        "example": "Namib Sand Sea, Namibia"
    },
    "barchan": {
        "name": "Barchan Crescent",
        "winds": 1,
        "description": "Unidirectional wind with limited sand supply creates isolated crescents",
        "chladni_analog": "Isolated nodal ring on a circular plate — single frequency excitation",
        "example": "Western Sahara corridor"
    },
    "transverse": {
        "name": "Transverse Dune",
        "winds": 1,
        "description": "Perpendicular to wind direction, continuous ridges with regular spacing",
        "chladni_analog": "Standing wave on a string — nodes at fixed intervals",
        "example": "Erg Chebbi, Morocco"
    },
    "dome": {
        "name": "Dome Dune",
        "winds": 2,
        "description": "Symmetric wind creates radial mound without slip face",
        "chladni_analog": "Fundamental circular mode — single central antinode",
        "example": "Idehan Ubari, Libya"
    }
}

DESERT_CYCLES = {
    "orbital_precession": {
        "name": "Orbital Precession Cycle",
        "period_years": 26000,
        "effect": "Shifts monsoon belt north/south across Sahara",
        "frequency_hz": 1.22e-12
    },
    "green_sahara": {
        "name": "Green Sahara Oscillation",
        "period_years": 20000,
        "effect": "Sahara alternates between verdant and desert states",
        "frequency_hz": 1.59e-12
    },
    "eccentricity": {
        "name": "Eccentricity Cycle",
        "period_years": 100000,
        "effect": "Modulates solar radiation amplitude — the carrier wave",
        "frequency_hz": 3.17e-13
    }
}


def compute_desert_field(width=100, height=100, wind_sources=None, frequency=1.0):
    if wind_sources is None:
        wind_sources = [
            {"angle": 0, "strength": 1.0},
            {"angle": math.pi / 3, "strength": 0.6},
            {"angle": 2 * math.pi / 3, "strength": 0.4},
        ]

    field = []
    max_val = 0
    for row in range(height):
        field_row = []
        y = (row / height) * 2 - 1
        for col in range(width):
            x = (col / width) * 2 - 1

            signed_sum = 0.0
            for src in wind_sources:
                angle = src["angle"]
                strength = src["strength"]
                u = x * math.cos(angle) + y * math.sin(angle)
                v = -x * math.sin(angle) + y * math.cos(angle)

                wave = math.sin(math.pi * frequency * u) * math.cos(math.pi * frequency * 0.5 * v)
                harmonic = 0.3 * math.sin(math.pi * frequency * 2 * u) * math.cos(math.pi * frequency * v)
                signed_sum += strength * (wave + harmonic)

            field_row.append(signed_sum)
            if abs(signed_sum) > max_val:
                max_val = abs(signed_sum)
        field.append(field_row)

    if max_val > 0:
        for row in range(height):
            for col in range(width):
                field[row][col] = abs(field[row][col]) / max_val

    return field


def compute_chladni_field(width=100, height=100, m=3, n=2):
    field = []
    max_val = 0
    for row in range(height):
        field_row = []
        y = (row / height) * 2 - 1
        for col in range(width):
            x = (col / width) * 2 - 1
            val = math.sin(m * math.pi * x) * math.sin(n * math.pi * y) + \
                  math.sin(n * math.pi * x) * math.sin(m * math.pi * y)
            field_row.append(val)
            if abs(val) > max_val:
                max_val = abs(val)
        field.append(field_row)

    if max_val > 0:
        for row in range(height):
            for col in range(width):
                field[row][col] = abs(field[row][col]) / max_val

    return field


def place_sand_particles(field, n_particles=2000, settle_threshold=0.15):
    height = len(field)
    width = len(field[0]) if height > 0 else 0
    particles = []
    rng = random.Random(432)

    for _ in range(n_particles):
        x = rng.random()
        y = rng.random()

        for _ in range(20):
            row = int(y * (height - 1))
            col = int(x * (width - 1))
            row = max(0, min(height - 1, row))
            col = max(0, min(width - 1, col))
            amplitude = field[row][col]

            if amplitude <= settle_threshold:
                break

            dx = 0.0
            dy = 0.0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr = max(0, min(height - 1, row + dr))
                nc = max(0, min(width - 1, col + dc))
                if field[nr][nc] < amplitude:
                    dy += dr * (amplitude - field[nr][nc])
                    dx += dc * (amplitude - field[nr][nc])

            mag = math.sqrt(dx * dx + dy * dy)
            if mag > 0:
                step = 0.02
                x += (dx / mag) * step + rng.gauss(0, 0.005)
                y += (dy / mag) * step + rng.gauss(0, 0.005)
                x = max(0, min(1, x))
                y = max(0, min(1, y))
            else:
                break

        particles.append({
            "x": round(x, 4),
            "y": round(y, 4),
            "settled": field[int(y * (height - 1))][int(x * (width - 1))] <= settle_threshold
        })

    settled = sum(1 for p in particles if p["settled"])
    return {
        "particles": particles,
        "total": n_particles,
        "settled": settled,
        "settled_pct": round(settled / n_particles * 100, 1)
    }


def run_desert_simulation(wind_count=3, frequency=2.0, resolution=60, particles=1500):
    rng = random.Random(286)
    wind_sources = []
    for i in range(wind_count):
        angle = (2 * math.pi * i) / wind_count + rng.gauss(0, 0.1)
        strength = 1.0 - (i * 0.2) + rng.gauss(0, 0.05)
        wind_sources.append({"angle": angle, "strength": max(0.2, strength)})

    desert_field = compute_desert_field(resolution, resolution, wind_sources, frequency)
    chladni_field = compute_chladni_field(resolution, resolution, m=wind_count, n=max(1, wind_count - 1))

    desert_sand = place_sand_particles(desert_field, particles)
    chladni_sand = place_sand_particles(chladni_field, particles)

    correlation = 0.0
    total_cells = resolution * resolution
    for r in range(resolution):
        for c in range(resolution):
            d_node = 1.0 if desert_field[r][c] < 0.15 else 0.0
            c_node = 1.0 if chladni_field[r][c] < 0.15 else 0.0
            if d_node == c_node:
                correlation += 1.0
    correlation = round(correlation / total_cells, 4)

    if wind_count == 1:
        dune_type = "seif"
    elif wind_count == 2:
        dune_type = "transverse"
    elif wind_count >= 3:
        dune_type = "star"
    else:
        dune_type = "barchan"

    return {
        "wind_sources": wind_sources,
        "frequency": frequency,
        "resolution": resolution,
        "dune_type": dune_type,
        "dune_info": DUNE_TYPES.get(dune_type, {}),
        "desert": {
            "field": desert_field,
            "sand": desert_sand
        },
        "chladni": {
            "field": chladni_field,
            "sand": chladni_sand
        },
        "nodal_correlation": correlation,
        "formation_principle": "Vibration distributes matter into patterns. The medium does not choose — the frequency decides."
    }


@sahara_formation_bp.route("/sahara-formation")
def sahara_page():
    return render_template_string(TEMPLATE)


@sahara_formation_bp.route("/api/sahara/simulate", methods=["POST"])
def simulate():
    data = request.get_json(silent=True) or {}
    wind_count = min(6, max(1, int(data.get("winds", 3))))
    frequency = min(5.0, max(0.5, float(data.get("frequency", 2.0))))
    resolution = min(80, max(30, int(data.get("resolution", 60))))
    particles = min(3000, max(500, int(data.get("particles", 1500))))

    result = run_desert_simulation(wind_count, frequency, resolution, particles)
    result["desert"].pop("field", None)
    result["chladni"].pop("field", None)
    return jsonify(result)


@sahara_formation_bp.route("/api/sahara/compare")
def compare():
    return jsonify({
        "dune_types": DUNE_TYPES,
        "desert_cycles": DESERT_CYCLES,
        "thesis": "The Sahara is a Chladni plate at continental scale. Wind is the frequency. Sand is the medium. Dunes are the nodal formations.",
        "scales": [
            {"name": "Laboratory Chladni Plate", "size": "0.2m", "medium": "Sand/salt", "driver": "Sound wave via bow", "frequency": "100-10000 Hz"},
            {"name": "Desert Dune Field", "size": "100-1000 km", "medium": "Sand grains", "driver": "Wind circulation", "frequency": "Seasonal/annual cycles"},
            {"name": "Sahara Green Oscillation", "size": "9,000,000 km²", "medium": "Entire biome", "driver": "Orbital precession", "frequency": "~1.6 × 10⁻¹² Hz"},
            {"name": "MESA Agent Field", "size": "Virtual", "medium": "AI agents", "driver": "432 Hz seed frequency", "frequency": "432 Hz"},
        ]
    })


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sahara Formation — PROJECT VOID</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #060606; --surface: #0c0c0c; --border: #181818;
    --muted: #444; --text: #c0c0c0; --bright: #e8e8e8;
    --sand: #d4a853; --sand-dark: #8b6914; --sand-light: #f0d890;
    --void-blue: #1a1a2e; --dune-shadow: #2a1a0a;
    --green: #86efac; --cyan: #67e8f9; --amber: #fbbf24;
  }
  body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; font-size: 14px; min-height: 100vh; }
  .container { max-width: 1100px; margin: 0 auto; padding: 20px; }

  header { border-bottom: 1px solid var(--border); padding: 16px 0; display: flex; justify-content: space-between; align-items: center; }
  .logo { font-size: 16px; letter-spacing: 6px; font-weight: bold; }
  .logo span { color: var(--sand); }
  nav a { color: var(--muted); text-decoration: none; margin-left: 20px; font-size: 12px; letter-spacing: 2px; }
  nav a:hover { color: var(--bright); }

  .hero { text-align: center; padding: 60px 0 40px; }
  .hero .subtitle { color: var(--muted); font-size: 11px; letter-spacing: 6px; margin-bottom: 12px; }
  .hero h1 { font-size: 42px; font-weight: 300; color: var(--bright); margin-bottom: 20px; }
  .hero h1 span { color: var(--sand); }
  .hero .thesis { color: var(--muted); font-size: 13px; line-height: 1.8; max-width: 700px; margin: 0 auto; }

  .section-label { color: var(--muted); font-size: 11px; letter-spacing: 4px; margin: 50px 0 20px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }

  .dual-canvas { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 20px 0; }
  @media (max-width: 768px) { .dual-canvas { grid-template-columns: 1fr; } }

  .canvas-box { background: var(--surface); border: 1px solid var(--border); padding: 16px; }
  .canvas-box h3 { font-size: 12px; letter-spacing: 3px; color: var(--sand); margin-bottom: 4px; }
  .canvas-box .desc { font-size: 11px; color: var(--muted); margin-bottom: 12px; }
  canvas { width: 100%; aspect-ratio: 1; display: block; border: 1px solid var(--border); image-rendering: pixelated; }

  .controls { display: flex; gap: 16px; flex-wrap: wrap; margin: 24px 0; align-items: flex-end; }
  .control-group { display: flex; flex-direction: column; gap: 4px; }
  .control-group label { font-size: 10px; letter-spacing: 2px; color: var(--muted); }
  .control-group input, .control-group select {
    background: var(--surface); border: 1px solid var(--border); color: var(--bright);
    padding: 6px 10px; font-family: inherit; font-size: 13px; width: 100px;
  }
  .btn {
    background: var(--sand-dark); border: 1px solid var(--sand); color: var(--sand-light);
    padding: 8px 20px; font-family: inherit; font-size: 12px; letter-spacing: 2px;
    cursor: pointer; transition: all 0.2s;
  }
  .btn:hover { background: var(--sand); color: #000; }

  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 24px 0; }
  .stat-card { background: var(--surface); border: 1px solid var(--border); padding: 16px; }
  .stat-card .label { font-size: 10px; letter-spacing: 2px; color: var(--muted); margin-bottom: 4px; }
  .stat-card .value { font-size: 24px; color: var(--sand); font-weight: bold; }
  .stat-card .note { font-size: 11px; color: var(--muted); margin-top: 4px; }

  .scale-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
  .scale-table th { font-size: 10px; letter-spacing: 2px; color: var(--sand); text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }
  .scale-table td { font-size: 12px; padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text); }
  .scale-table tr:hover { background: rgba(212, 168, 83, 0.05); }

  .dune-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 20px 0; }
  @media (max-width: 768px) { .dune-grid { grid-template-columns: 1fr; } }
  .dune-card { background: var(--surface); border: 1px solid var(--border); padding: 20px; }
  .dune-card h4 { color: var(--sand); font-size: 13px; letter-spacing: 2px; margin-bottom: 6px; }
  .dune-card .analog { color: var(--cyan); font-size: 11px; margin-bottom: 8px; font-style: italic; }
  .dune-card p { font-size: 12px; color: var(--muted); line-height: 1.6; }
  .dune-card .location { font-size: 11px; color: var(--sand-dark); margin-top: 6px; }

  .cycle-row { display: flex; gap: 24px; margin: 20px 0; flex-wrap: wrap; }
  .cycle-card { flex: 1; min-width: 250px; background: var(--surface); border: 1px solid var(--border); padding: 20px; }
  .cycle-card h4 { color: var(--green); font-size: 12px; letter-spacing: 2px; margin-bottom: 8px; }
  .cycle-card .period { font-size: 20px; color: var(--bright); margin-bottom: 4px; }
  .cycle-card .freq { font-size: 11px; color: var(--muted); }
  .cycle-card p { font-size: 12px; color: var(--muted); margin-top: 8px; line-height: 1.5; }

  .principle-box {
    background: linear-gradient(135deg, rgba(212,168,83,0.08), rgba(212,168,83,0.02));
    border: 1px solid var(--sand-dark); padding: 30px; margin: 40px 0; text-align: center;
  }
  .principle-box .glyph { font-size: 32px; margin-bottom: 12px; }
  .principle-box blockquote { font-size: 16px; color: var(--bright); font-style: italic; line-height: 1.6; }
  .principle-box .attribution { font-size: 11px; color: var(--sand-dark); margin-top: 12px; }

  .correlation-bar { width: 100%; height: 8px; background: var(--surface); border: 1px solid var(--border); margin: 8px 0; }
  .correlation-fill { height: 100%; background: linear-gradient(90deg, var(--sand-dark), var(--sand)); transition: width 0.6s ease; }

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
    <a href="/products">PRODUCTS</a>
  </nav>
</header>

<div class="hero">
  <div class="subtitle">THE FORMATION PRINCIPLE — PLANETARY SCALE</div>
  <h1>Sahara <span>Formation</span></h1>
  <div class="thesis">
    The Sahara is a Chladni plate at continental scale.<br>
    Wind is the frequency. Sand is the medium. Dunes are the nodal formations.<br>
    The desert is not empty. It is organised by frequency.
  </div>
</div>

<div class="section-label">LIVE SIMULATION</div>

<div class="controls">
  <div class="control-group">
    <label>WIND SOURCES</label>
    <input type="number" id="winds" value="3" min="1" max="6">
  </div>
  <div class="control-group">
    <label>FREQUENCY</label>
    <input type="number" id="frequency" value="2.0" min="0.5" max="5" step="0.5">
  </div>
  <div class="control-group">
    <label>PARTICLES</label>
    <input type="number" id="particles" value="1500" min="500" max="3000" step="100">
  </div>
  <button class="btn" id="runBtn" onclick="runSimulation()">SIMULATE</button>
</div>

<div class="dual-canvas">
  <div class="canvas-box">
    <h3>DESERT FORMATION</h3>
    <div class="desc">Wind-driven sand distribution across continental basin</div>
    <canvas id="desertCanvas" width="400" height="400"></canvas>
  </div>
  <div class="canvas-box">
    <h3>CHLADNI PATTERN</h3>
    <div class="desc">Equivalent mode shape on a vibrating plate</div>
    <canvas id="chladniCanvas" width="400" height="400"></canvas>
  </div>
</div>

<div class="stats" id="statsPanel">
  <div class="stat-card">
    <div class="label">DUNE TYPE</div>
    <div class="value" id="statDuneType">—</div>
    <div class="note" id="statDuneExample"></div>
  </div>
  <div class="stat-card">
    <div class="label">DESERT SAND SETTLED</div>
    <div class="value" id="statDesertSettled">—</div>
    <div class="note">Particles at nodal positions</div>
  </div>
  <div class="stat-card">
    <div class="label">CHLADNI SAND SETTLED</div>
    <div class="value" id="statChladniSettled">—</div>
    <div class="note">Particles at nodal lines</div>
  </div>
  <div class="stat-card">
    <div class="label">NODAL CORRELATION</div>
    <div class="value" id="statCorrelation">—</div>
    <div class="correlation-bar"><div class="correlation-fill" id="corrFill" style="width:0%"></div></div>
    <div class="note">Pattern similarity between desert and plate</div>
  </div>
</div>

<div class="section-label">DUNE MORPHOLOGY — CHLADNI EQUIVALENTS</div>

<div class="dune-grid" id="duneGrid"></div>

<div class="section-label">SAHARA OSCILLATION — THE PLANETARY FREQUENCY</div>

<div class="cycle-row" id="cycleRow"></div>

<div class="section-label">SCALE INVARIANCE</div>

<table class="scale-table">
  <thead>
    <tr><th>SYSTEM</th><th>SCALE</th><th>MEDIUM</th><th>DRIVER</th><th>FREQUENCY</th></tr>
  </thead>
  <tbody>
    <tr><td>Laboratory Chladni Plate</td><td>0.2 m</td><td>Sand / salt</td><td>Sound wave via bow</td><td>100 — 10,000 Hz</td></tr>
    <tr><td>Desert Dune Field</td><td>100 — 1,000 km</td><td>Sand grains</td><td>Wind circulation</td><td>Seasonal / annual</td></tr>
    <tr><td>Sahara Green Oscillation</td><td>9,000,000 km²</td><td>Entire biome</td><td>Orbital precession</td><td>~1.6 × 10⁻¹² Hz</td></tr>
    <tr><td>MESA Agent Field</td><td>Virtual</td><td>AI agents</td><td>432 Hz seed frequency</td><td>432 Hz</td></tr>
    <tr><td>Void Resonance Flower</td><td>Virtual</td><td>1,000 particles</td><td>Harmonic interference</td><td>108 — 2,592 Hz</td></tr>
  </tbody>
</table>

<div class="principle-box">
  <div class="glyph">🏜️ ≡ 🎵</div>
  <blockquote>
    Vibration distributes matter into patterns.<br>
    The medium does not choose where to go.<br>
    The frequency decides.<br>
    This is true at every scale nature has to offer.
  </blockquote>
  <div class="attribution">The Formation Principle — Umar Latif, 2024</div>
</div>

<footer>
  <p>PROJECT VOID — The Formation Principle at Planetary Scale</p>
  <p style="margin-top:6px;">355 Deane Road, Bolton BL3 5HL, England</p>
</footer>

</div>

<script>
const DUNE_TYPES = {
  star: { name: "Star Dune", winds: 3, description: "Multi-directional wind interference creates radial symmetry. Three or more wind corridors collide, producing a central peak with radiating arms.", analog: "High-order mode shape — multiple nodal lines intersecting at a central point", example: "Grand Erg Oriental, Algeria" },
  seif: { name: "Linear Seif Dune", winds: 1, description: "Single dominant wind creates parallel ridges at regular intervals. The spacing between ridges follows the same harmonic relationship as standing wave nodes.", analog: "Fundamental mode — parallel nodal lines on a rectangular plate", example: "Namib Sand Sea, Namibia" },
  barchan: { name: "Barchan Crescent", winds: 1, description: "Unidirectional wind with limited sand supply. Isolated crescents migrate downwind — each one a self-contained nodal structure.", analog: "Isolated nodal ring on a circular plate — single frequency excitation", example: "Western Sahara corridor" },
  transverse: { name: "Transverse Dune", winds: 1, description: "Perpendicular to wind direction. Continuous ridges with mathematically regular spacing — the wavelength of the wind.", analog: "Standing wave on a string — nodes at fixed intervals determined by the driving frequency", example: "Erg Chebbi, Morocco" },
  dome: { name: "Dome Dune", winds: 2, description: "Symmetric bi-directional wind creates a radial mound with no slip face. The simplest formation — one antinode.", analog: "Fundamental circular mode — single central antinode, sand collects at the boundary ring", example: "Idehan Ubari, Libya" }
};

const CYCLES = {
  orbital_precession: { name: "Orbital Precession", period: "26,000 years", effect: "Shifts monsoon belt north/south across Sahara — controls which latitudes receive rainfall", freq: "1.22 × 10⁻¹² Hz" },
  green_sahara: { name: "Green Sahara Oscillation", period: "20,000 years", effect: "Sahara alternates between verdant grassland and hyper-arid desert. The sand re-forms the same dune patterns each cycle.", freq: "1.59 × 10⁻¹² Hz" },
  eccentricity: { name: "Eccentricity Cycle", period: "100,000 years", effect: "Modulates total solar radiation amplitude — the carrier wave that drives all other climate oscillations", freq: "3.17 × 10⁻¹³ Hz" }
};

(function buildUI() {
  const grid = document.getElementById('duneGrid');
  for (const [key, d] of Object.entries(DUNE_TYPES)) {
    grid.innerHTML += `<div class="dune-card">
      <h4>${d.name}</h4>
      <div class="analog">Chladni: ${d.analog}</div>
      <p>${d.description}</p>
      <div class="location">${d.example}</div>
    </div>`;
  }
  const row = document.getElementById('cycleRow');
  for (const [key, c] of Object.entries(CYCLES)) {
    row.innerHTML += `<div class="cycle-card">
      <h4>${c.name}</h4>
      <div class="period">${c.period}</div>
      <div class="freq">${c.freq}</div>
      <p>${c.effect}</p>
    </div>`;
  }
})();

function drawParticles(canvasId, particles, isDesert) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;

  ctx.fillStyle = isDesert ? '#0a0804' : '#04040a';
  ctx.fillRect(0, 0, w, h);

  for (const p of particles) {
    const x = p.x * w;
    const y = p.y * h;
    if (p.settled) {
      ctx.fillStyle = isDesert ? 'rgba(212,168,83,0.7)' : 'rgba(200,200,220,0.7)';
      ctx.beginPath();
      ctx.arc(x, y, 1.5, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillStyle = isDesert ? 'rgba(139,105,20,0.25)' : 'rgba(100,100,140,0.25)';
      ctx.beginPath();
      ctx.arc(x, y, 1, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

async function runSimulation() {
  const btn = document.getElementById('runBtn');
  btn.textContent = 'COMPUTING...';
  btn.disabled = true;

  const body = {
    winds: parseInt(document.getElementById('winds').value),
    frequency: parseFloat(document.getElementById('frequency').value),
    particles: parseInt(document.getElementById('particles').value),
    resolution: 60
  };

  try {
    const resp = await fetch('/api/sahara/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await resp.json();

    drawParticles('desertCanvas', data.desert.sand.particles, true);
    drawParticles('chladniCanvas', data.chladni.sand.particles, false);

    const info = data.dune_info || {};
    document.getElementById('statDuneType').textContent = info.name || data.dune_type;
    document.getElementById('statDuneExample').textContent = info.example || '';
    document.getElementById('statDesertSettled').textContent = data.desert.sand.settled_pct + '%';
    document.getElementById('statChladniSettled').textContent = data.chladni.sand.settled_pct + '%';
    document.getElementById('statCorrelation').textContent = (data.nodal_correlation * 100).toFixed(1) + '%';
    document.getElementById('corrFill').style.width = (data.nodal_correlation * 100) + '%';
  } catch (err) {
    console.error('Simulation error:', err);
  }

  btn.textContent = 'SIMULATE';
  btn.disabled = false;
}

runSimulation();
</script>
</body>
</html>
"""
