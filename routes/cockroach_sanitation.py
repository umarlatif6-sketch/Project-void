"""
Cockroach Sanitation Protocol — Routes
/cockroach-sanitation              (GET  — public demo page)
/api/cockroach/demo                (POST — run sanitation demo)
/api/cockroach/bin                 (POST — run single bin cycle)
/api/cockroach/network             (GET  — network status)
"""

import json
import logging
from flask import Blueprint, render_template_string, request, jsonify

logger = logging.getLogger(__name__)

cockroach_sanitation_bp = Blueprint("cockroach_sanitation", __name__)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cockroach Sanitation Protocol — PROJECT VOID</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #060606; --surface: #0c0c0c; --border: #181818;
    --muted: #444; --text: #c0c0c0; --bright: #e8e8e8;
    --cyan: #67e8f9; --amber: #fbbf24; --green: #86efac; --red: #f87171;
  }
  body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; font-size: 14px; min-height: 100vh; }

  nav { display: flex; align-items: center; justify-content: space-between; padding: 20px 32px; border-bottom: 1px solid var(--border); max-width: 960px; margin: 0 auto; }
  .nav-logo { font-size: 0.78rem; letter-spacing: 0.3em; color: var(--bright); text-transform: uppercase; }
  .nav-logo span { color: var(--cyan); }
  .nav-links a { font-size: 0.68rem; letter-spacing: 0.15em; color: var(--muted); text-decoration: none; text-transform: uppercase; margin-left: 16px; }
  .nav-links a:hover { color: var(--cyan); }

  header { max-width: 960px; margin: 0 auto; padding: 60px 32px 20px; text-align: center; }
  .eyebrow { font-size: 0.65rem; letter-spacing: 0.35em; color: var(--muted); text-transform: uppercase; margin-bottom: 18px; }
  h1 { font-size: clamp(1.4rem, 3.5vw, 2rem); font-weight: 400; color: var(--bright); margin-bottom: 14px; }
  h1 span { color: var(--green); }
  .sub { font-size: 0.82rem; color: var(--muted); max-width: 560px; margin: 0 auto; line-height: 1.9; }

  main { max-width: 960px; margin: 0 auto; padding: 40px 32px 80px; }

  .section-label { font-size: 0.65rem; letter-spacing: 0.3em; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }

  .protocol-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--border); margin-bottom: 40px; }
  .protocol-step { background: var(--surface); padding: 24px; }
  .step-num { font-size: 0.6rem; color: var(--green); letter-spacing: 0.3em; margin-bottom: 10px; }
  .step-title { font-size: 0.9rem; color: var(--bright); margin-bottom: 8px; }
  .step-desc { font-size: 0.75rem; color: var(--muted); line-height: 1.7; }

  .research-block { background: var(--surface); border: 1px solid var(--border); padding: 24px; margin-bottom: 40px; }
  .research-title { font-size: 0.78rem; color: var(--bright); margin-bottom: 12px; }
  .research-list { list-style: none; }
  .research-list li { font-size: 0.75rem; color: var(--muted); padding: 6px 0; border-bottom: 1px solid #0e0e0e; line-height: 1.6; }
  .research-list li::before { content: "— "; color: var(--green); }

  .demo-panel { background: var(--surface); border: 1px solid var(--border); padding: 32px; margin-bottom: 40px; }
  .demo-controls { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; align-items: end; }
  .demo-field { display: flex; flex-direction: column; gap: 4px; }
  .demo-field label { font-size: 0.65rem; letter-spacing: 0.15em; color: var(--muted); text-transform: uppercase; }
  .demo-field input, .demo-field select { background: var(--bg); border: 1px solid var(--border); color: var(--text); font-family: 'Courier New', monospace; font-size: 0.78rem; padding: 8px 12px; width: 140px; }

  .btn-run {
    padding: 10px 24px; background: #030f03; border: 1px solid rgba(134, 239, 172, 0.3);
    color: var(--green); font-family: 'Courier New', monospace; font-size: 0.72rem;
    letter-spacing: 0.15em; text-transform: uppercase; cursor: pointer; transition: all 0.2s;
  }
  .btn-run:hover { border-color: var(--green); }
  .btn-run:disabled { opacity: 0.3; cursor: wait; }

  #results { margin-top: 20px; }
  .result-zone { background: var(--bg); border: 1px solid var(--border); padding: 16px; margin-bottom: 8px; }
  .zone-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .zone-name { font-size: 0.82rem; color: var(--bright); }
  .zone-status { font-size: 0.72rem; letter-spacing: 0.15em; padding: 3px 10px; }
  .zone-status.clean { color: var(--green); border: 1px solid rgba(134, 239, 172, 0.3); }
  .zone-status.residue { color: var(--amber); border: 1px solid rgba(251, 191, 36, 0.3); }
  .zone-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  .metric { text-align: center; }
  .metric-value { font-size: 1.1rem; color: var(--bright); }
  .metric-label { font-size: 0.6rem; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; }

  .network-summary { background: var(--surface); border-top: 2px solid var(--green); padding: 20px; margin-top: 20px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; text-align: center; }
  .summary-metric { }
  .summary-value { font-size: 1.4rem; color: var(--green); }
  .summary-label { font-size: 0.6rem; color: var(--muted); letter-spacing: 0.15em; text-transform: uppercase; margin-top: 4px; }

  .cycle-viz { margin-top: 30px; }
  .cycle-bar-container { display: flex; gap: 2px; margin-bottom: 6px; }
  .cycle-bar { height: 20px; transition: width 0.5s; }
  .cycle-bar.waste { background: var(--amber); }
  .cycle-bar.clean { background: var(--green); }
  .cycle-bar.empty { background: var(--border); }

  footer { max-width: 960px; margin: 0 auto; padding: 24px 32px; border-top: 1px solid var(--border); font-size: 0.65rem; color: #2a2a2a; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
  footer a { color: #333; text-decoration: none; }
  footer a:hover { color: var(--cyan); }

  @media (max-width: 700px) {
    .protocol-grid { grid-template-columns: 1fr; }
    .zone-metrics, .network-summary { grid-template-columns: 1fr 1fr; }
    .demo-controls { flex-direction: column; }
    .demo-field input { width: 100%; }
  }
</style>
</head>
<body>

<nav>
  <div class="nav-logo">PROJECT <span>VOID</span></div>
  <div class="nav-links">
    <a href="/">Engine</a>
    <a href="/fractures">Products</a>
  </div>
</nav>

<header>
  <div class="eyebrow">Bio-Inspired Sanitation Protocol</div>
  <h1>Cockroach <span>Sanitation</span></h1>
  <p class="sub">Neural-controlled cockroach colonies deployed into contained bins. Dark cycle: they eat everything. Light cycle: the bin is spotless. Zero chemicals. Zero energy cost. The cockroach IS the cleaning mechanism.</p>
</header>

<main>
  <div class="section-label">The Protocol</div>
  <div class="protocol-grid">
    <div class="protocol-step">
      <div class="step-num">01 — CONTAINMENT</div>
      <div class="step-title">Deploy the Bin</div>
      <div class="step-desc">Cockroach colony is housed in a single-layer containment vessel. One layer for the substance, one layer to contain the colony. The bin is the boundary.</div>
    </div>
    <div class="protocol-step">
      <div class="step-num">02 — DARK CYCLE</div>
      <div class="step-title">Lights Off — They Eat</div>
      <div class="step-desc">When the bin closes and it goes dark, the cockroaches activate. They eat everything organic — every trace of waste, every residue. Complete consumption. They sanitise as they go.</div>
    </div>
    <div class="protocol-step">
      <div class="step-num">03 — LIGHT CYCLE</div>
      <div class="step-title">Lights On — They Hide</div>
      <div class="step-desc">When light returns, the cockroaches retreat back into the walls of the containment. The bin is empty, clean, spotless. Ready for the next deposit.</div>
    </div>
    <div class="protocol-step">
      <div class="step-num">04 — NEURAL CONTROL</div>
      <div class="step-title">The System Controls Them</div>
      <div class="step-desc">Electrodes on the antenna nerves allow wireless steering. The cockroaches never operate unsupervised. The system decides when they activate. University-validated, open-source compatible.</div>
    </div>
  </div>

  <div class="research-block">
    <div class="research-title">Real Research — This Technology Exists</div>
    <ul class="research-list">
      <li>University of Connecticut (2012) — wireless neural control of cockroaches via antenna nerve stimulation</li>
      <li>Backyard Brains RoboRoach — commercially available electrode kit for neural steering of live cockroaches</li>
      <li>Texas A&M University (2015) — autonomous navigation of cyborg cockroaches via neural implants</li>
      <li>Nanyang Technological University, Singapore (2022) — solar-cell-powered cyborg cockroaches for sustained deployment</li>
      <li>RIKEN, Japan (2022) — ultra-thin flexible electronics mounted on living cockroaches for search and rescue</li>
    </ul>
  </div>

  <div class="section-label">Live Demonstration</div>
  <div class="demo-panel">
    <p style="font-size:0.78rem;color:var(--muted);margin-bottom:16px;line-height:1.7;">Deploy cockroach sanitation bins across commercial zones. Fill them with waste. Watch the dark cycle consume everything. Inspect the results.</p>

    <div class="demo-controls">
      <div class="demo-field">
        <label>Zones</label>
        <select id="zones">
          <option value="5">5 zones (standard)</option>
          <option value="3">3 zones (small)</option>
          <option value="8">8 zones (large)</option>
        </select>
      </div>
      <div class="demo-field">
        <label>Waste per zone</label>
        <input type="number" id="waste" value="80" min="10" max="100" step="5">
      </div>
      <div class="demo-field">
        <label>Cockroaches / bin</label>
        <input type="number" id="cockroaches" value="6" min="2" max="20" step="1">
      </div>
      <div class="demo-field">
        <label>Dark rounds</label>
        <input type="number" id="darkRounds" value="4" min="1" max="10" step="1">
      </div>
      <div class="demo-field" style="justify-content:flex-end;">
        <button class="btn-run" id="runBtn" onclick="runDemo()">Run Dark Cycle →</button>
      </div>
    </div>

    <div id="results"></div>
  </div>

  <div class="section-label">Commercial Applications</div>
  <div class="protocol-grid">
    <div class="protocol-step">
      <div class="step-num">FOOD RETAIL</div>
      <div class="step-title">Supermarket Waste Bins</div>
      <div class="step-desc">Organic waste from produce, bakery, deli. The bin closes at end of day. Dark cycle runs overnight. Morning: spotless bin, zero landfill cost.</div>
    </div>
    <div class="protocol-step">
      <div class="step-num">MEAT PROCESSING</div>
      <div class="step-title">Processing Plant Sanitation</div>
      <div class="step-desc">Offal, trimmings, residue. Contained bins with cockroach colonies consume everything biological. No chemical wash required for the bin itself.</div>
    </div>
    <div class="protocol-step">
      <div class="step-num">FOOD STORAGE</div>
      <div class="step-title">Cold Storage Cleanup</div>
      <div class="step-desc">Expired stock, spillage, contamination. Deploy bins in storage areas. Cockroaches handle the biological decomposition. The facility stays clean.</div>
    </div>
    <div class="protocol-step">
      <div class="step-num">HOSPITALITY</div>
      <div class="step-title">Restaurant & Market Stalls</div>
      <div class="step-desc">End-of-service waste. Street food residue. Market stall cleanup. The cockroach bin replaces the need for chemical waste processing entirely.</div>
    </div>
  </div>
</main>

<footer>
  <span>PROJECT VOID · Umar Latif · 355 Deane Road, Bolton BL3 5HL</span>
  <span><a href="/">Home</a> · <a href="/fractures">Products</a></span>
</footer>

<script>
async function runDemo() {
  const btn = document.getElementById('runBtn');
  const resultsDiv = document.getElementById('results');
  btn.disabled = true;
  btn.textContent = 'DARK CYCLE RUNNING...';
  resultsDiv.innerHTML = '<p style="color:var(--muted);font-size:0.75rem;">Cockroaches activating... consuming waste...</p>';

  try {
    const zones = parseInt(document.getElementById('zones').value);
    const waste = parseFloat(document.getElementById('waste').value);
    const cockroaches = parseInt(document.getElementById('cockroaches').value);
    const darkRounds = parseInt(document.getElementById('darkRounds').value);

    const res = await fetch('/api/cockroach/demo', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({zones, waste_per_zone: waste, cockroaches_per_bin: cockroaches, dark_rounds: darkRounds})
    });
    const data = await res.json();

    let html = '';

    const cycle = data.cycle_result || {};
    const summary = {
      processed: cycle.bins_processed || 0,
      clean: cycle.bins_clean || 0,
      residue: cycle.bins_with_residue || 0,
      consumed: cycle.total_consumed || 0,
      rate: cycle.network_sanitation_rate || 0,
    };

    html += '<div class="network-summary">';
    html += '<div class="summary-metric"><div class="summary-value">' + summary.processed + '</div><div class="summary-label">Bins Processed</div></div>';
    html += '<div class="summary-metric"><div class="summary-value">' + summary.clean + '</div><div class="summary-label">Spotless</div></div>';
    html += '<div class="summary-metric"><div class="summary-value">' + summary.consumed.toFixed(1) + '</div><div class="summary-label">Waste Consumed</div></div>';
    html += '<div class="summary-metric"><div class="summary-value">' + (summary.rate * 100).toFixed(0) + '%</div><div class="summary-label">Sanitation Rate</div></div>';
    html += '</div>';

    const binResults = cycle.bin_results || {};
    for (const [zoneId, zr] of Object.entries(binResults)) {
      const light = zr.light_cycle || {};
      const dark = zr.dark_cycle || {};
      const deposit = zr.deposit || {};
      const isClean = zr.result === 'SPOTLESS';

      html += '<div class="result-zone">';
      html += '<div class="zone-header">';
      html += '<span class="zone-name">' + zoneId.replace(/_/g, ' ') + '</span>';
      html += '<span class="zone-status ' + (isClean ? 'clean' : 'residue') + '">' + zr.result + '</span>';
      html += '</div>';

      const wasteRem = dark.waste_remaining || 0;
      const deposited = deposit.deposited || 0;
      const pctClean = deposited > 0 ? Math.max(0, ((deposited - wasteRem) / deposited) * 100) : 100;

      html += '<div class="cycle-viz"><div class="cycle-bar-container">';
      html += '<div class="cycle-bar clean" style="width:' + pctClean + '%;"></div>';
      if (pctClean < 100) html += '<div class="cycle-bar waste" style="width:' + (100 - pctClean) + '%;"></div>';
      html += '</div></div>';

      html += '<div class="zone-metrics">';
      html += '<div class="metric"><div class="metric-value">' + (deposit.deposited || 0).toFixed(1) + '</div><div class="metric-label">Deposited</div></div>';
      html += '<div class="metric"><div class="metric-value">' + (dark.consumed || 0).toFixed(1) + '</div><div class="metric-label">Consumed</div></div>';
      html += '<div class="metric"><div class="metric-value">' + (wasteRem).toFixed(1) + '</div><div class="metric-label">Remaining</div></div>';
      html += '<div class="metric"><div class="metric-value">' + ((light.sanitation_score || 0) * 100).toFixed(0) + '%</div><div class="metric-label">Sanitation</div></div>';
      html += '</div></div>';
    }

    resultsDiv.innerHTML = html;
  } catch (err) {
    resultsDiv.innerHTML = '<p style="color:var(--red);font-size:0.75rem;">Error: ' + err.message + '</p>';
  }

  btn.disabled = false;
  btn.textContent = 'Run Dark Cycle \\u2192';
}
</script>
</body>
</html>"""


@cockroach_sanitation_bp.route("/cockroach-sanitation")
def sanitation_page():
    return render_template_string(TEMPLATE)


@cockroach_sanitation_bp.route("/api/cockroach/demo", methods=["POST"])
def run_demo():
    data = request.get_json(silent=True) or {}

    zone_count = int(data.get("zones", 5))
    waste = float(data.get("waste_per_zone", 80))
    cockroaches = int(data.get("cockroaches_per_bin", 6))
    dark_rounds = int(data.get("dark_rounds", 4))

    zone_count = max(1, min(12, zone_count))
    waste = max(10, min(100, waste))
    cockroaches = max(2, min(20, cockroaches))
    dark_rounds = max(1, min(10, dark_rounds))

    zone_names = [
        "supermarket_organic", "meat_processing", "food_storage",
        "restaurant_waste", "market_stall", "bakery_residue",
        "deli_counter", "cold_storage", "fish_market", "produce_dock",
        "catering_facility", "street_food_station",
    ][:zone_count]

    from void_engine.cockroach_sanitation import run_sanitation_demo
    result = run_sanitation_demo(
        zones=zone_names,
        waste_per_zone=waste,
        cockroaches_per_bin=cockroaches,
        dark_rounds=dark_rounds,
    )

    return jsonify(result)


@cockroach_sanitation_bp.route("/api/cockroach/bin", methods=["POST"])
def run_single_bin():
    data = request.get_json(silent=True) or {}
    bin_id = data.get("bin_id", "test_bin")
    waste = float(data.get("waste", 80))
    cockroaches = int(data.get("cockroaches", 6))
    dark_rounds = int(data.get("dark_rounds", 4))

    from void_engine.cockroach_sanitation import SanitationBin
    b = SanitationBin(bin_id, capacity=100.0, n_cockroaches=cockroaches)
    result = b.run_full_sanitation_cycle(waste, dark_rounds=dark_rounds)
    return jsonify(result)
