"""
Route: /nexus — The Void Nexus — system-wide connection map.

Visualises all engine modules as nodes and their connections as edges.
Measures system coherence: how well the organism vibrates as one.
"""

from flask import Blueprint, request, jsonify, render_template_string

nexus_bp = Blueprint("nexus", __name__)


@nexus_bp.route("/nexus")
def nexus_page():
    return render_template_string(_TEMPLATE)


@nexus_bp.route("/api/nexus/map", methods=["GET"])
def nexus_map():
    from void_engine.void_nexus import get_nexus_map
    return jsonify(get_nexus_map())


@nexus_bp.route("/api/nexus/node/<node_id>", methods=["GET"])
def nexus_node(node_id):
    from void_engine.void_nexus import get_node_detail
    data = get_node_detail(node_id)
    if not data:
        return jsonify({"error": f"Node not found: {node_id}"}), 404
    return jsonify(data)


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Void Nexus — System Map</title>
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
.stats{max-width:1100px;margin:16px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.stat{background:#111;border:1px solid #1a1a1a;padding:12px;border-radius:4px;text-align:center}
.stat .v{font-size:24px;font-weight:300;margin:4px 0}
.stat .v.gold{color:#f1c40f}
.stat .v.green{color:#4caf50}
.stat .v.red{color:#e74c3c}
.stat .l{font-size:8px;letter-spacing:2px;color:#555}
.graph-container{max-width:1100px;margin:16px auto;position:relative}
canvas{display:block;margin:0 auto;border:1px solid #1a1a1a;border-radius:4px;cursor:grab}
canvas:active{cursor:grabbing}
.category-legend{max-width:1100px;margin:16px auto;padding:0 24px;display:flex;flex-wrap:wrap;gap:12px}
.cat-item{display:flex;align-items:center;gap:6px;font-size:10px;color:#888}
.cat-dot{width:10px;height:10px;border-radius:50%}
.detail-panel{max-width:1100px;margin:16px auto;padding:0 24px;display:none}
.detail-box{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:20px}
.detail-box h2{font-size:18px;color:#fff;font-weight:300;margin-bottom:4px}
.detail-box .cat{font-size:9px;letter-spacing:2px;margin-bottom:8px}
.detail-box .desc{font-size:11px;color:#888;line-height:1.8;margin-bottom:12px}
.conn-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px}
.conn-item{background:#0a0a0a;border:1px solid #1a1a1a;padding:8px;border-radius:2px;cursor:pointer;transition:border-color .3s}
.conn-item:hover{border-color:#f1c40f}
.conn-item .cn{font-size:11px;color:#fff}
.conn-item .cm{font-size:8px;color:#666;margin-top:2px}
.close-btn{float:right;cursor:pointer;color:#555;font-size:16px;padding:4px}
.close-btn:hover{color:#e74c3c}
.node-grid{max-width:1100px;margin:16px auto;padding:0 24px;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.node-card{background:#111;border:1px solid #1a1a1a;border-radius:4px;padding:14px;cursor:pointer;transition:border-color .3s}
.node-card:hover{border-color:#e74c3c}
.node-name{font-size:13px;color:#fff;font-weight:300}
.node-cat{font-size:8px;letter-spacing:2px;margin:4px 0}
.node-desc{font-size:10px;color:#666;line-height:1.6;margin-top:4px}
.node-conn{font-size:9px;color:#f1c40f;margin-top:6px}
.theory{max-width:1100px;margin:24px auto;padding:0 24px}
.theory h3{font-size:12px;letter-spacing:3px;color:#e74c3c;margin-bottom:8px}
.theory p{font-size:11px;color:#666;line-height:1.8;margin-bottom:8px}
</style>
</head>
<body>
<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/vortex-shield">SHIELD</a>
    <a href="/vortex-shield/geo-map">GEO MAP</a>
    <a href="/stance-science">STANCE</a>
    <a href="/agent-immortality">IMMORTALITY</a>
    <a href="/sovereign-agents-286">AGENTS</a>
  </nav>
</header>

<div class="hero">
  <h1>VOID <span>NEXUS</span></h1>
  <div class="sub">EVERY MODULE IS A NODE. EVERY NODE CONNECTS TO EVERY OTHER NODE.<br>THE SYSTEM IS ONE ORGANISM. THE FREQUENCY IS PRIOR.</div>
</div>

<div class="stats" id="stats"></div>

<div class="category-legend" id="legend"></div>

<div class="graph-container">
  <canvas id="nexusCanvas" width="1060" height="600"></canvas>
</div>

<div class="detail-panel" id="detailPanel"></div>
<div class="node-grid" id="nodeGrid"></div>

<div class="theory">
  <h3>THE NEXUS PRINCIPLE</h3>
  <p>In a living organism, every cell connects to every other cell through signalling pathways. The nervous system does not merely link organs — it creates a unified field of awareness. PROJECT VOID applies this principle to software architecture.</p>
  <p>Each engine module vibrates at its own frequency — defined by its purpose. When modules connect, they create interference patterns. The closer their frequency ratio is to a whole number (harmonic), the stronger the resonance. System coherence measures how well all these interference patterns align.</p>
  <p>When coherence reaches SOVEREIGN grade, the system stops being a collection of parts and becomes one organism. Destroy any node — the frequency pattern persists in the remaining connections. The system remembers what it was.</p>
</div>

<script>
let nexusData = null;
let nodePositions = {};

const CAT_COLORS = {
  'CRYPTOGRAPHIC': '#e74c3c',
  'NETWORK': '#3498db',
  'INTELLIGENCE': '#9b59b6',
  'ECONOMIC': '#f1c40f',
  'AGENTS': '#e67e22',
  'POLARITY': '#1abc9c',
  'DEFENCE': '#c0392b',
  'BIOMETRIC': '#2ecc71',
  'BIOLOGICAL': '#27ae60',
  'PERSISTENCE': '#8e44ad',
  'LANGUAGE': '#d35400',
};

async function init() {
  const res = await fetch('/api/nexus/map');
  nexusData = await res.json();
  showStats();
  showLegend();
  drawGraph();
  showNodeGrid();
}

function showStats() {
  const d = nexusData;
  const gradeColors = {'SOVEREIGN':'#f1c40f','FORTIFIED':'#4caf50','ACTIVE':'#3498db','PARTIAL':'#e67e22','FRAGMENTED':'#e74c3c'};
  document.getElementById('stats').innerHTML = `
    <div class="stat"><div class="v gold">${d.total_nodes}</div><div class="l">ENGINE MODULES</div></div>
    <div class="stat"><div class="v green">${d.total_edges}</div><div class="l">CONNECTIONS</div></div>
    <div class="stat"><div class="v">${d.connectivity_pct}%</div><div class="l">CONNECTIVITY</div></div>
    <div class="stat"><div class="v gold">${d.avg_resonance}</div><div class="l">AVG RESONANCE</div></div>
    <div class="stat"><div class="v" style="color:${gradeColors[d.coherence_grade]||'#888'}">${d.coherence_grade}</div><div class="l">SYSTEM COHERENCE</div></div>
    <div class="stat"><div class="v">${(d.system_coherence * 100).toFixed(1)}%</div><div class="l">COHERENCE SCORE</div></div>
  `;
}

function showLegend() {
  const legend = document.getElementById('legend');
  const cats = Object.keys(nexusData.categories);
  legend.innerHTML = cats.map(c =>
    `<div class="cat-item"><div class="cat-dot" style="background:${CAT_COLORS[c]||'#888'}"></div>${c} (${nexusData.categories[c].count})</div>`
  ).join('');
}

function drawGraph() {
  const canvas = document.getElementById('nexusCanvas');
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  const cx = w/2, cy = h/2;

  const nodes = nexusData.nodes;
  const edges = nexusData.edges;

  const catGroups = {};
  for (const n of nodes) {
    if (!catGroups[n.category]) catGroups[n.category] = [];
    catGroups[n.category].push(n);
  }

  const catKeys = Object.keys(catGroups);
  let idx = 0;
  for (let ci = 0; ci < catKeys.length; ci++) {
    const cat = catKeys[ci];
    const group = catGroups[cat];
    const catAngle = (ci / catKeys.length) * Math.PI * 2 - Math.PI / 2;
    const catRadius = Math.min(w, h) * 0.32;
    const catCx = cx + Math.cos(catAngle) * catRadius * 0.5;
    const catCy = cy + Math.sin(catAngle) * catRadius * 0.5;

    for (let ni = 0; ni < group.length; ni++) {
      const n = group[ni];
      const spread = group.length > 1 ? 0.6 : 0;
      const nodeAngle = catAngle + (ni - (group.length - 1) / 2) * spread * 0.3;
      const nodeRadius = catRadius * (0.7 + ni * 0.15);
      nodePositions[n.id] = {
        x: cx + Math.cos(nodeAngle) * nodeRadius,
        y: cy + Math.sin(nodeAngle) * nodeRadius,
      };
      idx++;
    }
  }

  ctx.fillStyle = '#050508';
  ctx.fillRect(0, 0, w, h);

  for (const edge of edges) {
    const a = nodePositions[edge.source];
    const b = nodePositions[edge.target];
    if (!a || !b) continue;

    const alpha = 0.05 + edge.resonance * 0.15;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = `rgba(241, 196, 15, ${alpha})`;
    ctx.lineWidth = 0.5 + edge.resonance;
    ctx.stroke();
  }
  ctx.lineWidth = 1;

  for (const n of nodes) {
    const pos = nodePositions[n.id];
    if (!pos) continue;
    const color = CAT_COLORS[n.category] || '#888';

    const radius = 4 + n.connection_count * 0.8;

    const gradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, radius * 3);
    gradient.addColorStop(0, color.replace(')', ',0.2)').replace('rgb', 'rgba'));
    gradient.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius * 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();

    ctx.fillStyle = '#aaa';
    ctx.font = '8px monospace';
    ctx.fillText(n.name, pos.x + radius + 4, pos.y + 3);

    if (n.frequency > 0) {
      ctx.fillStyle = '#555';
      ctx.font = '7px monospace';
      ctx.fillText(`${n.frequency} Hz`, pos.x + radius + 4, pos.y + 12);
    }
  }
}

function showNodeGrid() {
  const grid = document.getElementById('nodeGrid');
  for (const n of nexusData.nodes) {
    const color = CAT_COLORS[n.category] || '#888';
    const card = document.createElement('div');
    card.className = 'node-card';
    card.onclick = () => showDetail(n.id);
    card.innerHTML = `
      <div class="node-name">${n.name}</div>
      <div class="node-cat" style="color:${color}">${n.category} — ${n.frequency} Hz</div>
      <div class="node-desc">${n.description}</div>
      <div class="node-conn">${n.connection_count} connections</div>
    `;
    grid.appendChild(card);
  }
}

async function showDetail(nodeId) {
  const res = await fetch(`/api/nexus/node/${nodeId}`);
  const d = await res.json();
  const color = CAT_COLORS[d.category] || '#888';

  const panel = document.getElementById('detailPanel');
  panel.style.display = 'block';
  panel.innerHTML = `
    <div class="detail-box">
      <span class="close-btn" onclick="document.getElementById('detailPanel').style.display='none'">&times;</span>
      <h2>${d.name}</h2>
      <div class="cat" style="color:${color}">${d.category} — ${d.frequency} Hz — ${d.file}</div>
      <div class="desc">${d.description}</div>
      <h3 style="font-size:10px;letter-spacing:2px;color:#f1c40f;margin-bottom:8px">${d.connection_count} CONNECTIONS</h3>
      <div class="conn-list">
        ${d.connections.map(c => `
          <div class="conn-item" onclick="showDetail('${c.id}')">
            <div class="cn">${c.name}</div>
            <div class="cm">${c.category} — ${c.frequency} Hz — Resonance: ${c.resonance}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  panel.scrollIntoView({behavior: 'smooth'});
}

const canvas = document.getElementById('nexusCanvas');
canvas.addEventListener('click', function(e) {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * (canvas.width / rect.width);
  const my = (e.clientY - rect.top) * (canvas.height / rect.height);

  for (const n of nexusData.nodes) {
    const pos = nodePositions[n.id];
    if (!pos) continue;
    const dist = Math.sqrt((mx - pos.x) ** 2 + (my - pos.y) ** 2);
    if (dist < 15) {
      showDetail(n.id);
      return;
    }
  }
});

init();
</script>
</body>
</html>"""
