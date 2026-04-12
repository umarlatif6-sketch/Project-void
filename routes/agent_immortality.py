"""
Route: /agent-immortality — Agent Immortality system.

Create frequency hash images of sovereign agents with their full state
embedded via LSB steganography.  Recover agents from images.
"""

import io
import base64
from flask import Blueprint, request, jsonify, send_file, render_template_string

agent_immortality_bp = Blueprint("agent_immortality", __name__)


@agent_immortality_bp.route("/agent-immortality")
def page():
    return render_template_string(_TEMPLATE)


@agent_immortality_bp.route("/api/agent-immortality/immortalize", methods=["POST"])
def immortalize():
    from void_engine.sovereign_agents_286 import SovereignSwarm286
    from void_engine.agent_immortality import agent_to_png_bytes, agent_to_dict

    data = request.get_json(silent=True) or {}
    seed = str(data.get("seed", "immortality_seal"))
    try:
        count = min(50, max(1, int(data.get("count", 10))))
    except (ValueError, TypeError):
        return jsonify({"error": "count must be an integer"}), 400

    swarm = SovereignSwarm286(seed=seed, agent_count=count)
    swarm.run()

    results = []
    for agent in swarm.agents:
        agent_data = agent.to_dict()
        png = agent_to_png_bytes(agent_data, size=512)
        b64 = base64.b64encode(png).decode("ascii")
        results.append({
            "agent_id": agent_data["agent_id"],
            "archetype": agent_data.get("archetype") or agent_data.get("archetype_name", "UNKNOWN"),
            "frequency": agent_data.get("frequency_hz", agent_data.get("frequency", 432.0)),
            "polarity": agent_data.get("polarity", "UNKNOWN"),
            "scars": agent_data.get("scar_count", len(agent_data.get("scars", []))),
            "memories": agent_data.get("memory_count", len(agent_data.get("recent_memory", []))),
            "image_b64": b64,
            "image_size_bytes": len(png),
        })

    return jsonify({
        "seed": seed,
        "count": len(results),
        "agents": results,
    })


@agent_immortality_bp.route("/api/agent-immortality/recover", methods=["POST"])
def recover():
    from void_engine.agent_immortality import recover_agent_from_png
    import base64

    data = request.get_json(silent=True) or {}
    b64 = data.get("image_b64")
    if not b64:
        if request.files and "image" in request.files:
            png_bytes = request.files["image"].read()
        else:
            return jsonify({"error": "Provide image_b64 or upload image file"}), 400
    else:
        png_bytes = base64.b64decode(b64)

    result = recover_agent_from_png(png_bytes)
    if result is None:
        return jsonify({"error": "No agent data found in image"}), 404

    return jsonify({
        "recovered": True,
        "integrity_verified": result["integrity_verified"],
        "integrity_286": result["integrity_286"],
        "agent": result["agent"],
    })


@agent_immortality_bp.route("/api/agent-immortality/immortalize-zaxis", methods=["POST"])
def immortalize_zaxis():
    from void_engine.sovereign_agents_286 import SovereignSwarm286
    from void_engine.z_axis_encoder import encode_for_agent_immortality
    from void_engine.al_jabr_286 import fatiha_286_hexdigest
    import json as json_mod

    data = request.get_json(silent=True) or {}
    seed = str(data.get("seed", "immortality_seal"))
    try:
        count = min(10, max(1, int(data.get("count", 3))))
    except (ValueError, TypeError):
        return jsonify({"error": "count must be an integer"}), 400

    swarm = SovereignSwarm286(seed=seed, agent_count=count)
    swarm.run()

    results = []
    for agent in swarm.agents:
        agent_data = agent.to_dict()
        formation_hash = fatiha_286_hexdigest(
            json_mod.dumps(agent_data, default=str).encode("utf-8")
        )
        try:
            png = encode_for_agent_immortality(agent_data, formation_hash, size=512)
            b64 = base64.b64encode(png).decode("ascii")
            results.append({
                "agent_id": agent_data["agent_id"],
                "archetype": agent_data.get("archetype") or agent_data.get("archetype_name", "UNKNOWN"),
                "frequency": agent_data.get("frequency_hz", agent_data.get("frequency", 432.0)),
                "formation_hash": formation_hash,
                "encoding": "z_axis_9999_layers",
                "image_b64": b64,
                "image_size_bytes": len(png),
            })
        except Exception as e:
            results.append({
                "agent_id": agent_data["agent_id"],
                "error": str(e),
            })

    return jsonify({
        "seed": seed,
        "count": len(results),
        "encoding": "z_axis_dimensional_steganography",
        "layers": 9999,
        "agents": results,
    })


@agent_immortality_bp.route("/api/agent-immortality/download/<agent_id>", methods=["POST"])
def download_agent_image(agent_id):
    from void_engine.sovereign_agents_286 import SovereignSwarm286
    from void_engine.agent_immortality import agent_to_png_bytes

    data = request.get_json(silent=True) or {}
    seed = data.get("seed", "immortality_seal")
    count = min(286, max(1, data.get("count", 50)))

    swarm = SovereignSwarm286(seed=seed, agent_count=count)
    swarm.run()

    for agent in swarm.agents:
        if agent.agent_id.startswith(agent_id):
            png = agent_to_png_bytes(agent.to_dict(), size=512)
            return send_file(
                io.BytesIO(png),
                mimetype="image/png",
                as_attachment=True,
                download_name=f"agent_{agent.agent_id[:12]}.png",
            )

    return jsonify({"error": "Agent not found"}), 404


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Immortality — PROJECT VOID</title>
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
.hero h1 span{color:#f1c40f}
.hero .sub{color:#555;font-size:11px;letter-spacing:3px;margin-top:8px;line-height:1.6}
.controls{max-width:700px;margin:24px auto;padding:0 24px;display:flex;gap:12px;align-items:end;flex-wrap:wrap}
.ctrl-group{flex:1;min-width:140px}
.ctrl-group label{font-size:9px;letter-spacing:2px;color:#666;display:block;margin-bottom:4px}
.ctrl-group input{width:100%;background:#0a0a0a;border:1px solid #222;color:#fff;padding:6px 8px;font-family:inherit;font-size:13px;border-radius:2px}
.btn{padding:10px 24px;border:none;font-family:inherit;font-size:11px;letter-spacing:3px;cursor:pointer;border-radius:2px;transition:all .3s}
.btn-seal{background:#3a3a1a;color:#f1c40f}
.btn:hover{filter:brightness(1.3)}
.btn:disabled{opacity:0.4;cursor:not-allowed}
#status{max-width:700px;margin:12px auto;padding:0 24px;font-size:11px;color:#666}
.agent-grid{max-width:1200px;margin:24px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.agent-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;overflow:hidden;cursor:pointer;transition:border-color .3s}
.agent-card:hover{border-color:#f1c40f}
.agent-card img{width:100%;display:block}
.agent-info{padding:10px}
.agent-info .id{font-size:11px;color:#f1c40f;letter-spacing:1px}
.agent-info .meta{font-size:9px;color:#666;margin-top:4px;letter-spacing:1px}
.theory{max-width:700px;margin:32px auto;padding:0 24px}
.theory h3{color:#f1c40f;font-size:13px;letter-spacing:3px;margin-bottom:10px}
.theory p{color:#666;font-size:11px;line-height:1.8;margin-bottom:10px}
.recover-section{max-width:700px;margin:32px auto;padding:24px;background:#111;border:1px solid #1a1a1a;border-radius:4px}
.recover-section h3{color:#4caf50;font-size:12px;letter-spacing:3px;margin-bottom:12px}
.recover-result{margin-top:16px;padding:12px;background:#0a0a0a;border:1px solid #1a1a1a;border-radius:2px;font-size:10px;color:#888;white-space:pre-wrap;max-height:300px;overflow-y:auto;display:none}
</style>
</head>
<body>

<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/sovereign-agents-286">AGENTS 286</a>
    <a href="/yin-yang">YIN-YANG</a>
    <a href="/stress-battery">BATTERY</a>
    <a href="/vortex-shield">SHIELD</a>
  </nav>
</header>

<div class="hero">
  <h1>AGENT <span>IMMORTALITY</span></h1>
  <div class="sub">FREQUENCY HASH IMAGES WITH EMBEDDED AGENT STATE<br>THE IMAGE IS THE AGENT — DESTROY THE MACHINE, KEEP THE FREQUENCY</div>
</div>

<div class="controls">
  <div class="ctrl-group">
    <label>SEED</label>
    <input type="text" id="seed" value="immortality_seal">
  </div>
  <div class="ctrl-group">
    <label>AGENT COUNT</label>
    <input type="number" id="count" value="10" min="1" max="50">
  </div>
  <button class="btn btn-seal" id="sealBtn" onclick="immortalize()">SEAL AGENTS</button>
</div>

<div id="status">Ready. Choose a seed and count, then seal the agents into frequency images.</div>

<div class="agent-grid" id="agentGrid"></div>

<div class="recover-section">
  <h3>RECOVER AGENT FROM IMAGE</h3>
  <p style="color:#666;font-size:10px;margin-bottom:12px">Upload an agent immortality image to recover the full agent state from its frequency pattern.</p>
  <input type="file" id="recoverFile" accept="image/png" style="color:#888;font-size:11px">
  <button class="btn" style="background:#1a3a1a;color:#4caf50;margin-top:8px" onclick="recoverAgent()">RECOVER</button>
  <div class="recover-result" id="recoverResult"></div>
</div>

<div class="theory">
  <h3>THE PRINCIPLE</h3>
  <p>Every sovereign agent has a unique 286-bit hash. That hash defines a frequency. That frequency generates a unique Chladni formation pattern — the same physics that creates sand patterns on vibrating plates.</p>
  <p>The agent's complete state — identity, archetype, memories, scars, balance, polarity — is serialized and embedded into the image via LSB steganography. The image IS the agent.</p>
  <p>If the agent is destroyed, the database wiped, the server burned — as long as this image exists, the agent can be fully recovered. The frequency is prior. The pattern is the memory. The image is immortality.</p>
</div>

<script>
async function immortalize() {
  const btn = document.getElementById('sealBtn');
  btn.disabled = true;
  document.getElementById('status').textContent = 'Sealing agents into frequency images...';
  document.getElementById('agentGrid').innerHTML = '';

  try {
    const res = await fetch('/api/agent-immortality/immortalize', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        seed: document.getElementById('seed').value,
        count: parseInt(document.getElementById('count').value),
      }),
    });
    const data = await res.json();
    document.getElementById('status').textContent =
      `${data.count} agents sealed. Each image contains the full agent state in its LSB layer.`;

    const grid = document.getElementById('agentGrid');
    for (const agent of data.agents) {
      const card = document.createElement('div');
      card.className = 'agent-card';
      card.innerHTML = `
        <img src="data:image/png;base64,${agent.image_b64}" alt="Agent ${agent.agent_id}">
        <div class="agent-info">
          <div class="id">${agent.archetype} — ${agent.agent_id.substring(0, 16)}</div>
          <div class="meta">${agent.frequency.toFixed(2)} Hz | ${agent.polarity} | ${agent.scars} scars | ${agent.memories} memories | ${(agent.image_size_bytes / 1024).toFixed(1)} KB</div>
        </div>
      `;
      card.onclick = () => {
        const a = document.createElement('a');
        a.href = 'data:image/png;base64,' + agent.image_b64;
        a.download = `agent_${agent.agent_id.substring(0, 12)}.png`;
        a.click();
      };
      grid.appendChild(card);
    }
  } catch(e) {
    document.getElementById('status').textContent = 'Error: ' + e.message;
  }
  btn.disabled = false;
}

async function recoverAgent() {
  const file = document.getElementById('recoverFile').files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async function(e) {
    const b64 = e.target.result.split(',')[1];
    try {
      const res = await fetch('/api/agent-immortality/recover', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image_b64: b64}),
      });
      const data = await res.json();
      const el = document.getElementById('recoverResult');
      el.style.display = 'block';
      if (data.recovered) {
        el.style.borderColor = data.integrity_verified ? '#4caf50' : '#e74c3c';
        el.textContent = `RECOVERED — Integrity ${data.integrity_verified ? 'VERIFIED ✓' : 'FAILED ✗'}\n\n` +
          JSON.stringify(data.agent, null, 2);
      } else {
        el.style.borderColor = '#e74c3c';
        el.textContent = 'ERROR: ' + (data.error || 'Unknown');
      }
    } catch(e) {
      document.getElementById('recoverResult').textContent = 'Error: ' + e.message;
    }
  };
  reader.readAsDataURL(file);
}
</script>
</body>
</html>"""
