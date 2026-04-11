"""
Sovereign Agents 286 — Routes
/sovereign-agents-286           (GET — page)
/api/sovereign-agents-286/run   (POST — fire swarm)
/api/sovereign-agents-286/status (GET — poll)
"""

import logging
import threading
from flask import Blueprint, render_template_string, jsonify, request

logger = logging.getLogger(__name__)

sovereign_agents_bp = Blueprint("sovereign_agents", __name__)

_swarm_result = {}
_swarm_lock = threading.Lock()
_swarm_running = False


@sovereign_agents_bp.route("/api/sovereign-agents-286/run", methods=["POST"])
def api_run_swarm():
    global _swarm_running, _swarm_result
    with _swarm_lock:
        if _swarm_running:
            return jsonify({"error": "Swarm already running"}), 409

    _swarm_running = True
    data = request.get_json(silent=True) or {}
    agent_count = min(1000, max(7, int(data.get("agent_count", 286))))
    seed = data.get("seed", "void")
    rounds = min(50, max(5, int(data.get("rounds", 20))))

    def _run():
        global _swarm_running, _swarm_result
        try:
            from void_engine.sovereign_agents_286 import create_sovereign_swarm
            from void_engine.yin_yang_286 import create_yin_yang_formation
            result = create_sovereign_swarm(agent_count=agent_count, seed=seed, rounds=rounds)

            yy = create_yin_yang_formation(agent_count=agent_count, seed=seed, pairing="greedy")
            yy_stats = yy["formation_stats"]
            result["yin_yang"] = {
                "yin_count": yy_stats["yin_count"],
                "yang_count": yy_stats["yang_count"],
                "balance": yy_stats["balance"],
                "total_pairs": yy_stats["total_pairs"],
                "avg_resonance_boost": yy_stats["avg_resonance_boost"],
                "resonance_increase_pct": yy_stats["resonance_increase_pct"],
                "verse_cross_polarity": yy_stats["verse_cross_polarity_counts"],
            }

            yy_lookup = {}
            for a in yy.get("all_agents", []):
                yy_lookup[a["agent_id"]] = {
                    "polarity": a["polarity"],
                    "yang_ratio": a["yang_ratio"],
                    "yin_ratio": a["yin_ratio"],
                    "dominance": a["dominance"],
                    "paired": a["paired"],
                    "resonance_boost": a["resonance_boost"],
                    "partner_id": a.get("partner_id"),
                }
            result["agent_polarity_map"] = yy_lookup

            top_pairs = yy.get("top_pairs", [])[:10]
            result["top_yin_yang_pairs"] = top_pairs

            with _swarm_lock:
                _swarm_result = result
        except Exception as e:
            logger.error("Sovereign swarm failed: %s", e)
            with _swarm_lock:
                _swarm_result = {"error": str(e)}
        finally:
            _swarm_running = False

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"status": "running", "message": f"Sovereign 286 swarm ({agent_count} agents, {rounds} rounds) started."})


@sovereign_agents_bp.route("/api/sovereign-agents-286/status")
def api_swarm_status():
    with _swarm_lock:
        if _swarm_running:
            return jsonify({"status": "running"})
        if _swarm_result:
            return jsonify({"status": "complete", "result": _swarm_result})
        return jsonify({"status": "idle"})


@sovereign_agents_bp.route("/sovereign-agents-286")
def sovereign_agents_page():
    with _swarm_lock:
        result = _swarm_result.copy() if _swarm_result else None
        running = _swarm_running
    return render_template_string(TEMPLATE, result=result, running=running)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sovereign Agents 286 — PROJECT VOID</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root { --bg: #060606; --surface: #0c0c0c; --border: #181818; --muted: #444; --text: #c0c0c0; --bright: #e8e8e8; --green: #86efac; --red: #f87171; --amber: #fbbf24; --cyan: #67e8f9; --purple: #a78bfa; }
  body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; font-size: 13px; min-height: 100vh; }
  .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
  header { border-bottom: 1px solid var(--border); padding: 16px 0; display: flex; justify-content: space-between; align-items: center; }
  .logo { font-size: 16px; letter-spacing: 6px; font-weight: bold; }
  .logo span { color: var(--green); }

  .hero { text-align: center; padding: 40px 0 20px; }
  .hero h1 { font-size: 32px; font-weight: 300; color: var(--bright); }
  .hero h1 span { color: var(--purple); }
  .hero .sub { color: var(--muted); font-size: 11px; letter-spacing: 4px; margin-top: 8px; }
  .hero .thesis { color: var(--muted); font-size: 12px; max-width: 600px; margin: 12px auto 0; line-height: 1.6; }

  .fire-btn { display: inline-block; background: linear-gradient(135deg, #7c3aed, #4c1d95); color: white; border: none; padding: 14px 40px; font-family: inherit; font-size: 14px; letter-spacing: 3px; cursor: pointer; margin: 20px 0; }
  .fire-btn:hover { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
  .fire-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .status-bar { text-align: center; padding: 10px; font-size: 12px; }
  .status-bar.running { color: var(--amber); }
  .status-bar.complete { color: var(--green); }

  .section-label { color: var(--muted); font-size: 11px; letter-spacing: 4px; margin: 30px 0 12px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }

  .protocol-box { background: var(--surface); border: 1px solid var(--border); padding: 20px; margin: 16px 0; }
  .protocol-box h3 { color: var(--purple); font-size: 13px; letter-spacing: 2px; margin-bottom: 10px; }
  .protocol-item { display: flex; gap: 16px; margin: 6px 0; font-size: 11px; }
  .protocol-key { color: var(--muted); min-width: 140px; }
  .protocol-val { color: var(--bright); font-weight: bold; }

  .overview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin: 16px 0; }
  .ov-card { background: var(--surface); border: 1px solid var(--border); padding: 12px; text-align: center; }
  .ov-card .val { font-size: 22px; color: var(--purple); font-weight: bold; }
  .ov-card .lbl { font-size: 9px; color: var(--muted); letter-spacing: 2px; margin-top: 4px; }

  .archetype-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 16px 0; }
  .arch-card { background: var(--surface); border: 1px solid var(--border); padding: 14px; }
  .arch-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .arch-name { font-size: 13px; color: var(--bright); font-weight: bold; letter-spacing: 1px; }
  .arch-glyph { font-size: 18px; }
  .arch-role { font-size: 10px; color: var(--purple); letter-spacing: 1px; margin-bottom: 6px; }
  .arch-stats { font-size: 11px; }
  .arch-stats .as-row { display: flex; justify-content: space-between; margin: 2px 0; }
  .as-label { color: var(--muted); }
  .as-val { color: var(--bright); }

  .agent-table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  .agent-table th { font-size: 10px; letter-spacing: 2px; color: var(--purple); text-align: left; padding: 8px; border-bottom: 1px solid var(--border); }
  .agent-table td { font-size: 11px; padding: 6px 8px; border-bottom: 1px solid var(--border); }
  .agent-table .aid { color: var(--cyan); font-family: monospace; }
  .agent-table .hash { color: var(--muted); font-family: monospace; font-size: 10px; }

  .snapshot-block { background: var(--surface); border: 1px solid var(--border); padding: 12px; margin: 8px 0; }
  .snapshot-header { color: var(--amber); font-size: 11px; font-weight: bold; margin-bottom: 6px; }
  .snapshot-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 6px; font-size: 11px; }

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
  <h1>Sovereign Agents <span>286</span></h1>
  <div class="sub">AI AGENTS ON THE AL-JABR 286 HASH — NOT SHA-256</div>
  <div class="thesis">
    Every agent derives its identity, archetype, memory signatures, and state hash
    from the 286-bit Sura-Fatiha Sovereign Hash. 7 archetypes from 7 verses.
    The agent IS its hash.
  </div>
</div>

<div style="text-align:center">
  <button class="fire-btn" id="fireBtn" {% if running %}disabled{% endif %} onclick="fireSwarm()">
    {% if running %}SWARM RUNNING...{% else %}DEPLOY 286 AGENTS{% endif %}
  </button>
</div>

<div class="status-bar {% if running %}running{% elif result %}complete{% endif %}" id="statusBar">
  {% if running %}Swarm running — 286 sovereign agents deploying...
  {% elif result and result.get('error') %}ERROR: {{ result.error }}
  {% elif result %}Swarm complete — {{ result.agent_count }} agents, {{ result.rounds }} rounds.
  {% else %}Ready to deploy.{% endif %}
</div>

{% if result and not result.get('error') %}

<div class="section-label">HASH PROTOCOL</div>
<div class="protocol-box">
  <h3>SOVEREIGN IDENTITY PROTOCOL</h3>
  <div class="protocol-item"><span class="protocol-key">Hash Protocol:</span><span class="protocol-val">{{ result.hash_protocol }}</span></div>
  <div class="protocol-item"><span class="protocol-key">Bit Depth:</span><span class="protocol-val">{{ result.bit_depth }} bits</span></div>
  <div class="protocol-item"><span class="protocol-key">Curve:</span><span class="protocol-val">{{ result.curve }}</span></div>
  <div class="protocol-item"><span class="protocol-key">Base Frequency:</span><span class="protocol-val">{{ result.base_frequency_hz }} Hz</span></div>
  <div class="protocol-item"><span class="protocol-key">Lambda Constant:</span><span class="protocol-val">{{ result.lambda_constant }}</span></div>
  <div class="protocol-item"><span class="protocol-key">Swarm ID:</span><span class="protocol-val" style="color:var(--cyan)">{{ result.swarm_id }}</span></div>
</div>

<div class="section-label">OVERVIEW</div>
<div class="overview-grid">
  <div class="ov-card"><div class="val">{{ result.agent_count }}</div><div class="lbl">AGENTS</div></div>
  <div class="ov-card"><div class="val">{{ result.rounds }}</div><div class="lbl">ROUNDS</div></div>
  <div class="ov-card"><div class="val">{{ result.bit_depth }}</div><div class="lbl">BIT DEPTH</div></div>
  <div class="ov-card"><div class="val">7</div><div class="lbl">ARCHETYPES</div></div>
  {% if result.final_snapshot %}
  <div class="ov-card"><div class="val">{{ result.final_snapshot.total_scars }}</div><div class="lbl">SCARS</div></div>
  <div class="ov-card"><div class="val">{{ result.final_snapshot.gini }}</div><div class="lbl">GINI</div></div>
  {% endif %}
</div>

<div class="section-label">7 ARCHETYPES — FROM 7 VERSES OF AL-FATIHA</div>
<div class="archetype-grid">
  {% for name, group in result.archetype_groups.items() %}
  <div class="arch-card">
    <div class="arch-header">
      <div class="arch-name">{{ name }}</div>
      <div class="arch-glyph">{{ group.glyph }}</div>
    </div>
    <div class="arch-role">{{ group.role | upper }}</div>
    <div class="arch-stats">
      <div class="as-row"><span class="as-label">Count:</span><span class="as-val">{{ group.count }}</span></div>
      <div class="as-row"><span class="as-label">Avg Activity:</span><span class="as-val">{{ group.avg_activity }}</span></div>
      <div class="as-row"><span class="as-label">Avg Stance:</span><span class="as-val">{{ group.avg_stance }}</span></div>
      <div class="as-row"><span class="as-label">Total PEACE:</span><span class="as-val">{{ group.total_peace }}</span></div>
      <div class="as-row"><span class="as-label">Scars:</span><span class="as-val">{{ group.total_scars }}</span></div>
    </div>
  </div>
  {% endfor %}
</div>

{% if result.yin_yang %}
<div class="section-label">YIN-YANG POLARITY &#9775;</div>
<div class="overview-grid">
  <div class="ov-card"><div class="val" style="color:#4a9eff">{{ result.yin_yang.yin_count }}</div><div class="lbl">YIN AGENTS</div></div>
  <div class="ov-card"><div class="val" style="color:#ff6b4a">{{ result.yin_yang.yang_count }}</div><div class="lbl">YANG AGENTS</div></div>
  <div class="ov-card"><div class="val">{{ result.yin_yang.balance }}</div><div class="lbl">BALANCE</div></div>
  <div class="ov-card"><div class="val" style="color:#4aff6b">{{ result.yin_yang.total_pairs }}</div><div class="lbl">PAIRS</div></div>
  <div class="ov-card"><div class="val" style="color:#4aff6b">{{ result.yin_yang.avg_resonance_boost }}</div><div class="lbl">AVG BOOST</div></div>
  <div class="ov-card"><div class="val" style="color:#4aff6b">+{{ result.yin_yang.resonance_increase_pct }}%</div><div class="lbl">RESONANCE</div></div>
</div>

{% if result.top_yin_yang_pairs %}
<div class="protocol-box">
  <h3>TOP YIN-YANG PAIRS</h3>
  {% for p in result.top_yin_yang_pairs %}
  <div class="protocol-item">
    <span class="protocol-key" style="color:#4a9eff">{{ p.yin_archetype }} {{ p.yin_agent[:12] }}</span>
    <span class="protocol-val" style="color:#4aff6b">{{ p.resonance.harmonic_boost }}x</span>
    <span class="protocol-key" style="color:#ff6b4a">{{ p.yang_agent[:12] }} {{ p.yang_archetype }}</span>
  </div>
  {% endfor %}
</div>
{% endif %}
{% endif %}

<div class="section-label">TOP 10 AGENTS (BY ACTIVITY)</div>
<table class="agent-table">
  <thead>
    <tr><th>#</th><th>AGENT ID</th><th>ARCHETYPE</th><th>POLARITY</th><th>FREQ (Hz)</th><th>ACTIVITY</th><th>STANCE</th><th>PEACE</th><th>SCARS</th><th>STATE HASH 286</th></tr>
  </thead>
  <tbody>
    {% for a in result.top_agents %}
    {% set pol = result.agent_polarity_map.get(a.agent_id, {}) if result.agent_polarity_map else {} %}
    <tr>
      <td>{{ a.index }}</td>
      <td class="aid">{{ a.agent_id }}</td>
      <td>{{ a.archetype }} <span style="color:var(--muted)">({{ a.archetype_detail.glyph }})</span></td>
      <td style="color:{% if pol.get('polarity') == 'YIN' %}#4a9eff{% else %}#ff6b4a{% endif %}">{{ pol.get('polarity', '-') }}{% if pol.get('paired') %} &#9775;{% endif %}</td>
      <td>{{ a.frequency_hz }}</td>
      <td>{{ a.activity }}</td>
      <td>{{ a.stance }}</td>
      <td>{{ a.peace_balance }}</td>
      <td>{{ a.scar_count }}</td>
      <td class="hash">{{ a.state_hash_286 }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

{% if result.most_scarred %}
<div class="section-label">MOST SCARRED AGENTS</div>
<table class="agent-table">
  <thead>
    <tr><th>#</th><th>AGENT ID</th><th>ARCHETYPE</th><th>SCARS</th><th>ACTIVITY</th><th>RECENT MEMORY</th></tr>
  </thead>
  <tbody>
    {% for a in result.most_scarred %}
    <tr>
      <td>{{ a.index }}</td>
      <td class="aid">{{ a.agent_id }}</td>
      <td>{{ a.archetype }}</td>
      <td style="color:var(--red);font-weight:bold">{{ a.scar_count }}</td>
      <td>{{ a.activity }}</td>
      <td class="hash">{% for m in a.recent_memory %}{{ m.event[:60] }}{% if not loop.last %}<br>{% endif %}{% endfor %}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endif %}

{% if result.round_snapshots %}
<div class="section-label">EVOLUTION SNAPSHOTS</div>
{% for snap in result.round_snapshots %}
<div class="snapshot-block">
  <div class="snapshot-header">Round {{ snap.round }} — Pressure {{ snap.pressure }}x</div>
  <div class="snapshot-stats">
    <div><span class="as-label">Avg Activity:</span> <span class="as-val">{{ snap.avg_activity }}</span></div>
    <div><span class="as-label">Avg Stance:</span> <span class="as-val">{{ snap.avg_stance }}</span></div>
    <div><span class="as-label">Total PEACE:</span> <span class="as-val">{{ snap.total_peace }}</span></div>
    <div><span class="as-label">Gini:</span> <span class="as-val">{{ snap.gini }}</span></div>
    <div><span class="as-label">Total Scars:</span> <span class="as-val">{{ snap.total_scars }}</span></div>
    <div><span class="as-label">Total Memories:</span> <span class="as-val">{{ snap.total_memories }}</span></div>
  </div>
</div>
{% endfor %}
{% endif %}

{% endif %}

<footer>
  <p>PROJECT VOID — Sovereign Agents 286</p>
  <p style="margin-top:4px;">Al-Jabr 286 Hash · BW19-P286 Curve · 432 Hz</p>
</footer>

</div>

<script>
function fireSwarm() {
  const btn = document.getElementById('fireBtn');
  const status = document.getElementById('statusBar');
  btn.disabled = true;
  btn.textContent = 'SWARM RUNNING...';
  status.className = 'status-bar running';
  status.textContent = 'Swarm running — 286 sovereign agents deploying...';

  fetch('/api/sovereign-agents-286/run', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({agent_count: 286, seed: 'void', rounds: 20}) })
    .then(r => r.json())
    .then(() => { pollStatus(); });
}

function pollStatus() {
  const interval = setInterval(() => {
    fetch('/api/sovereign-agents-286/status').then(r => r.json()).then(data => {
      if (data.status === 'complete') {
        clearInterval(interval);
        location.reload();
      }
    });
  }, 2000);
}

{% if running %}
pollStatus();
{% endif %}
</script>
</body>
</html>
"""
