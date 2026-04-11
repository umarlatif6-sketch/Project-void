"""
Stress Battery — 10 Escalating Tests Route
/stress-battery         (GET — results page)
/api/stress-battery/run (POST — fire the battery)
"""

import logging
import threading
from flask import Blueprint, render_template_string, jsonify, request

logger = logging.getLogger(__name__)

stress_battery_bp = Blueprint("stress_battery", __name__)

_battery_result = {}
_battery_lock = threading.Lock()
_battery_running = False


@stress_battery_bp.route("/api/stress-battery/run", methods=["POST"])
def api_run_battery():
    global _battery_running, _battery_result
    with _battery_lock:
        if _battery_running:
            return jsonify({"error": "Battery already running"}), 409

    _battery_running = True
    data = request.get_json(silent=True) or {}
    seed = data.get("seed", "formation_zero")

    def _run():
        global _battery_running, _battery_result
        try:
            from void_engine.stress_battery import run_stress_battery
            result = run_stress_battery(seed=seed)
            with _battery_lock:
                _battery_result = result
        except Exception as e:
            logger.error("Stress battery failed: %s", e)
            with _battery_lock:
                _battery_result = {"error": str(e)}
        finally:
            _battery_running = False

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return jsonify({"status": "running", "message": "Battery started — 10 tests firing."})


@stress_battery_bp.route("/api/stress-battery/status")
def api_battery_status():
    with _battery_lock:
        if _battery_running:
            return jsonify({"status": "running"})
        if _battery_result:
            return jsonify({"status": "complete", "result": _battery_result})
        return jsonify({"status": "idle"})


@stress_battery_bp.route("/stress-battery")
def stress_battery_page():
    with _battery_lock:
        result = _battery_result.copy() if _battery_result else None
        running = _battery_running
    return render_template_string(TEMPLATE, result=result, running=running)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stress Battery — PROJECT VOID</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root { --bg: #060606; --surface: #0c0c0c; --border: #181818; --muted: #444; --text: #c0c0c0; --bright: #e8e8e8; --green: #86efac; --red: #f87171; --amber: #fbbf24; --cyan: #67e8f9; }
  body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; font-size: 13px; min-height: 100vh; }
  .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
  header { border-bottom: 1px solid var(--border); padding: 16px 0; display: flex; justify-content: space-between; align-items: center; }
  .logo { font-size: 16px; letter-spacing: 6px; font-weight: bold; }
  .logo span { color: var(--green); }

  .hero { text-align: center; padding: 40px 0 20px; }
  .hero h1 { font-size: 32px; font-weight: 300; color: var(--bright); }
  .hero h1 span { color: var(--red); }
  .hero .sub { color: var(--muted); font-size: 11px; letter-spacing: 4px; margin-top: 8px; }

  .fire-btn { display: inline-block; background: linear-gradient(135deg, #dc2626, #991b1b); color: white; border: none; padding: 14px 40px; font-family: inherit; font-size: 14px; letter-spacing: 3px; cursor: pointer; margin: 20px 0; }
  .fire-btn:hover { background: linear-gradient(135deg, #ef4444, #dc2626); }
  .fire-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .status-bar { text-align: center; padding: 10px; font-size: 12px; }
  .status-bar.running { color: var(--amber); }
  .status-bar.complete { color: var(--green); }

  .section-label { color: var(--muted); font-size: 11px; letter-spacing: 4px; margin: 30px 0 12px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }

  .verdict-box { background: var(--surface); border: 1px solid var(--border); padding: 24px; margin: 20px 0; text-align: center; }
  .verdict-box .grade { font-size: 64px; font-weight: bold; }
  .verdict-box .grade.A { color: var(--green); }
  .verdict-box .grade.B { color: var(--cyan); }
  .verdict-box .grade.C { color: var(--amber); }
  .verdict-box .grade.D, .verdict-box .grade.F { color: var(--red); }
  .verdict-box .narrative { color: var(--text); font-size: 13px; margin-top: 12px; line-height: 1.6; }

  .overview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin: 16px 0; }
  .ov-card { background: var(--surface); border: 1px solid var(--border); padding: 12px; text-align: center; }
  .ov-card .val { font-size: 24px; color: var(--green); font-weight: bold; }
  .ov-card .lbl { font-size: 9px; color: var(--muted); letter-spacing: 2px; margin-top: 4px; }

  .test-block { background: var(--surface); border: 1px solid var(--border); margin: 16px 0; padding: 16px; }
  .test-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
  .test-name { font-size: 14px; color: var(--bright); font-weight: bold; letter-spacing: 2px; }
  .test-severity { font-size: 11px; padding: 2px 8px; font-weight: bold; }
  .sev-low { background: rgba(134,239,172,0.15); color: var(--green); border: 1px solid rgba(134,239,172,0.3); }
  .sev-med { background: rgba(251,191,36,0.15); color: var(--amber); border: 1px solid rgba(251,191,36,0.3); }
  .sev-high { background: rgba(248,113,113,0.15); color: var(--red); border: 1px solid rgba(248,113,113,0.3); }
  .test-desc { color: var(--muted); font-size: 11px; margin-bottom: 10px; }
  .test-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
  .ts-item { font-size: 11px; }
  .ts-label { color: var(--muted); }
  .ts-val { color: var(--bright); font-weight: bold; }
  .ts-val.broke { color: var(--red); }
  .ts-val.held { color: var(--green); }

  .scar-list { margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }
  .scar-item { font-size: 10px; color: var(--cyan); margin: 2px 0; }
  .scar-hash { color: var(--muted); font-family: monospace; }

  footer { border-top: 1px solid var(--border); padding: 16px 0; margin-top: 30px; text-align: center; }
  footer p { font-size: 11px; color: var(--muted); }
</style>
</head>
<body>
<div class="container">

<header>
  <div class="logo">PROJECT <span>VOID</span></div>
</header>

<div class="hero">
  <h1>Stress <span>Battery</span></h1>
  <div class="sub">10 ESCALATING TESTS — TREMOR TO FORMATION ZERO</div>
</div>

<div style="text-align:center">
  <button class="fire-btn" id="fireBtn" {% if running %}disabled{% endif %} onclick="fireBattery()">
    {% if running %}BATTERY RUNNING...{% else %}FIRE BATTERY{% endif %}
  </button>
</div>

<div class="status-bar {% if running %}running{% elif result %}complete{% endif %}" id="statusBar">
  {% if running %}Battery in progress — testing 10 escalating stress levels...
  {% elif result and result.get('error') %}ERROR: {{ result.error }}
  {% elif result %}Battery complete — {{ result.tests_run }} tests, {{ result.total_scars_generated }} scars. Grade: {{ result.verdict.grade }}
  {% else %}Ready to fire.{% endif %}
</div>

{% if result and not result.get('error') %}

<div class="section-label">VERDICT</div>
<div class="verdict-box">
  <div class="grade {{ result.verdict.grade }}">{{ result.verdict.grade }}</div>
  <div class="narrative">{{ result.verdict.narrative }}</div>
</div>

<div class="section-label">BATTERY OVERVIEW</div>
<div class="overview-grid">
  <div class="ov-card"><div class="val">{{ result.tests_run }}</div><div class="lbl">TESTS</div></div>
  <div class="ov-card"><div class="val">{{ result.total_scars_generated }}</div><div class="lbl">SCARS</div></div>
  <div class="ov-card"><div class="val">{{ result.total_ghost_protocols }}</div><div class="lbl">GHOST PROTOCOLS</div></div>
  <div class="ov-card"><div class="val">{{ result.economy_breaks }}</div><div class="lbl">ECONOMY BREAKS</div></div>
  <div class="ov-card"><div class="val">{{ result.total_execution_time_s }}s</div><div class="lbl">EXECUTION TIME</div></div>
</div>

<div class="section-label">TEST RESULTS (1–10)</div>

{% for test in result.tests %}
<div class="test-block">
  <div class="test-header">
    <div class="test-name">#{{ test.test_index }} — {{ test.name }}</div>
    <div class="test-severity {% if test.severity <= 3 %}sev-low{% elif test.severity <= 6 %}sev-med{% else %}sev-high{% endif %}">
      SEVERITY {{ test.severity }}/10
    </div>
  </div>
  <div class="test-desc">{{ test.description }}</div>
  <div class="test-stats">
    <div class="ts-item"><span class="ts-label">Agents:</span> <span class="ts-val">{{ test.results.total_agents }}</span></div>
    <div class="ts-item"><span class="ts-label">Cockroaches:</span> <span class="ts-val">{{ test.results.cockroach_count }}</span></div>
    <div class="ts-item"><span class="ts-label">Survived stress:</span> <span class="ts-val held">{{ test.results.cockroach_survived_stress_events }}</span></div>
    <div class="ts-item"><span class="ts-label">Ghost protocols:</span> <span class="ts-val">{{ test.results.ghost_protocols_generated }}</span></div>
    <div class="ts-item"><span class="ts-label">Scars:</span> <span class="ts-val">{{ test.results.scars_generated }}</span></div>
    <div class="ts-item"><span class="ts-label">Economy break:</span>
      <span class="ts-val {% if test.results.economy_breaking_rate %}broke{% else %}held{% endif %}">
        {% if test.results.economy_breaking_rate %}{{ test.results.economy_breaking_rate }}x{% else %}HELD{% endif %}
      </span>
    </div>
    <div class="ts-item"><span class="ts-label">Gini:</span> <span class="ts-val">{{ test.results.gini_coefficient }}</span></div>
    <div class="ts-item"><span class="ts-label">Time:</span> <span class="ts-val">{{ test.execution_time_s }}s</span></div>
  </div>
  <div class="scar-list">
    {% for scar in test.scars %}
    <div class="scar-item">{{ scar.title }} <span class="scar-hash">[{{ scar.hex_digest }}]</span></div>
    {% endfor %}
  </div>
</div>
{% endfor %}

{% endif %}

<footer>
  <p>PROJECT VOID — Stress Battery</p>
</footer>

</div>

<script>
function fireBattery() {
  const btn = document.getElementById('fireBtn');
  const status = document.getElementById('statusBar');
  btn.disabled = true;
  btn.textContent = 'BATTERY RUNNING...';
  status.className = 'status-bar running';
  status.textContent = 'Battery in progress — testing 10 escalating stress levels...';

  fetch('/api/stress-battery/run', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({seed: 'formation_zero'}) })
    .then(r => r.json())
    .then(() => { pollStatus(); });
}

function pollStatus() {
  const interval = setInterval(() => {
    fetch('/api/stress-battery/status').then(r => r.json()).then(data => {
      if (data.status === 'complete') {
        clearInterval(interval);
        location.reload();
      }
    });
  }, 3000);
}

{% if running %}
pollStatus();
{% endif %}
</script>
</body>
</html>
"""
