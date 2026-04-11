import logging
import threading
from flask import Blueprint, jsonify, render_template_string, request

logger = logging.getLogger(__name__)

yin_yang_bp = Blueprint("yin_yang", __name__)

_yy_lock = threading.Lock()
_yy_running = False
_yy_result = None

YIN_YANG_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YIN-YANG 286 — Polarity Resonance</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Courier New',monospace;min-height:100vh}
.container{max-width:1200px;margin:0 auto;padding:20px}
h1{color:#fff;font-size:1.8rem;text-align:center;margin:30px 0 5px;letter-spacing:4px}
.subtitle{text-align:center;color:#666;margin-bottom:30px;font-size:0.85rem}
.symbol{text-align:center;font-size:3rem;margin:20px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:20px 0}
@media(max-width:768px){.grid{grid-template-columns:1fr}}
.card{background:#111;border:1px solid #222;padding:20px;border-radius:8px}
.card h3{color:#fff;margin-bottom:12px;font-size:1rem;border-bottom:1px solid #222;padding-bottom:8px}
.stat{display:flex;justify-content:space-between;padding:4px 0;font-size:0.85rem}
.stat .label{color:#666}
.stat .value{color:#fff;font-weight:bold}
.yin-color{color:#4a9eff}
.yang-color{color:#ff6b4a}
.boost-color{color:#4aff6b}
.pair-row{display:grid;grid-template-columns:1fr 80px 1fr;gap:10px;align-items:center;padding:8px;margin:4px 0;background:#0d0d0d;border-radius:4px;font-size:0.8rem}
.pair-yin{text-align:right;color:#4a9eff}
.pair-yang{text-align:left;color:#ff6b4a}
.pair-boost{text-align:center;color:#4aff6b;font-weight:bold}
.round-row{display:grid;grid-template-columns:50px 60px 100px 100px 80px;gap:5px;padding:3px 0;font-size:0.8rem}
.round-header{color:#666;border-bottom:1px solid #222;padding-bottom:5px;margin-bottom:5px}
.bar-container{height:16px;background:#1a1a1a;border-radius:3px;overflow:hidden;margin:3px 0}
.bar-yin{height:100%;background:linear-gradient(90deg,#0a2a4a,#4a9eff);border-radius:3px;transition:width 0.5s}
.bar-yang{height:100%;background:linear-gradient(90deg,#4a1a0a,#ff6b4a);border-radius:3px;transition:width 0.5s}
.bar-boost{height:100%;background:linear-gradient(90deg,#0a4a1a,#4aff6b);border-radius:3px;transition:width 0.5s}
.verdict{text-align:center;padding:20px;margin:20px 0;background:#111;border:2px solid #333;border-radius:8px}
.verdict .pct{font-size:2.5rem;font-weight:bold}
.verdict .met{color:#4aff6b}
.verdict .notmet{color:#ff4a4a}
.btn{background:#222;color:#fff;border:1px solid #444;padding:10px 24px;cursor:pointer;border-radius:4px;font-family:inherit;font-size:0.9rem;margin:5px}
.btn:hover{background:#333}
.btn:disabled{opacity:0.4;cursor:not-allowed}
.controls{text-align:center;margin:20px 0}
.loading{text-align:center;color:#666;padding:40px;font-size:0.9rem}
.full-width{grid-column:1/-1}
.verse-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-top:10px}
.verse-cell{text-align:center;padding:8px 4px;border-radius:4px;font-size:0.75rem}
.verse-yin{background:#0a2a4a;color:#4a9eff}
.verse-yang{background:#4a1a0a;color:#ff6b4a}
a.back{color:#666;text-decoration:none;font-size:0.85rem}
a.back:hover{color:#fff}
</style>
</head>
<body>
<div class="container">
<a class="back" href="/">&larr; VOID</a>
<div class="symbol">&#9775;</div>
<h1>YIN-YANG 286</h1>
<p class="subtitle">POLARITY RESONANCE ENGINE &mdash; Every bit is Yin or Yang. Complementary pairs amplify.</p>

<div class="controls">
<button class="btn" id="btnFormation" onclick="runFormation()">MAP FORMATION</button>
<button class="btn" id="btnStress" onclick="runStress()">STRESS TEST</button>
<button class="btn" onclick="checkStatus()">CHECK STATUS</button>
</div>

<div id="output">
<div class="loading">Press MAP FORMATION to classify all 286 agents by Yin-Yang polarity.<br>Press STRESS TEST to prove the 20% resonance target.</div>
</div>
</div>

<script>
function runFormation(){
  document.getElementById('btnFormation').disabled=true;
  document.getElementById('output').innerHTML='<div class="loading">Classifying 286 agents by Yin-Yang polarity...</div>';
  fetch('/api/yin-yang/formation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_count:286,seed:'void',pairing:'greedy'})})
  .then(r=>r.json()).then(d=>{document.getElementById('btnFormation').disabled=false;renderFormation(d)})
  .catch(e=>{document.getElementById('btnFormation').disabled=false;document.getElementById('output').innerHTML='<div class="loading">Error: '+e+'</div>'});
}

function runStress(){
  document.getElementById('btnStress').disabled=true;
  document.getElementById('output').innerHTML='<div class="loading">Running Yin-Yang paired stress test (20 rounds, 10x pressure)...</div>';
  fetch('/api/yin-yang/stress',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_count:100,seed:'yin_yang_proof',rounds:20,pressure_max:10.0})})
  .then(r=>r.json()).then(d=>{document.getElementById('btnStress').disabled=false;if(d.status==='running'){setTimeout(checkStatus,3000)}else{renderStress(d)}})
  .catch(e=>{document.getElementById('btnStress').disabled=false;document.getElementById('output').innerHTML='<div class="loading">Error: '+e+'</div>'});
}

function checkStatus(){
  fetch('/api/yin-yang/status').then(r=>r.json()).then(d=>{
    if(d.status==='running'){document.getElementById('output').innerHTML='<div class="loading">Running... checking again in 2s</div>';setTimeout(checkStatus,2000)}
    else if(d.status==='complete'&&d.result){
      if(d.result.round_data)renderStress(d.result);else renderFormation(d.result);
    }else{document.getElementById('output').innerHTML='<div class="loading">'+JSON.stringify(d)+'</div>'}
  });
}

function renderFormation(d){
  let s=d.formation_stats;
  let h='<div class="grid">';
  h+='<div class="card"><h3>POLARITY BALANCE</h3>';
  h+=stat('Total Agents',s.total_agents);
  h+=stat('YIN Agents','<span class="yin-color">'+s.yin_count+' ('+Math.round(s.yin_ratio*100)+'%)</span>');
  h+=stat('YANG Agents','<span class="yang-color">'+s.yang_count+' ('+Math.round(s.yang_ratio*100)+'%)</span>');
  h+=stat('Balance',s.balance.toFixed(4));
  h+='<div class="bar-container"><div class="bar-yin" style="width:'+Math.round(s.yin_ratio*100)+'%"></div></div>';
  h+='<div class="bar-container"><div class="bar-yang" style="width:'+Math.round(s.yang_ratio*100)+'%"></div></div>';
  h+='</div>';
  h+='<div class="card"><h3>RESONANCE</h3>';
  h+=stat('Total Pairs',s.total_pairs);
  h+=stat('Cross-Polarity',s.cross_polarity_pairs);
  h+=stat('Unpaired',s.unpaired_count);
  h+=stat('Avg Boost','<span class="boost-color">'+s.avg_resonance_boost.toFixed(4)+' (+'+s.resonance_increase_pct.toFixed(1)+'%)</span>');
  h+=stat('Min Boost',s.min_resonance_boost.toFixed(4));
  h+=stat('Max Boost',s.max_resonance_boost.toFixed(4));
  h+=stat('Avg Complementary',s.avg_complementary_ratio.toFixed(4));
  h+='<div class="bar-container"><div class="bar-boost" style="width:'+Math.round(s.resonance_increase_pct)+'%"></div></div>';
  h+='</div>';
  h+='<div class="card full-width"><h3>VERSE CROSS-POLARITY</h3>';
  h+='<div class="verse-grid">';
  let vnames=['Bismillah','Al-Hamd','Ar-Rahman','Malik','Iyyaka','Sirat','An-Amta'];
  for(let i=0;i<7;i++){
    let cnt=s.verse_cross_polarity_counts[i];
    let pct=Math.round(cnt/s.total_pairs*100);
    h+='<div class="verse-cell '+(pct>50?'verse-yang':'verse-yin')+'">V'+(i+1)+'<br>'+vnames[i]+'<br><b>'+cnt+'</b> ('+pct+'%)</div>';
  }
  h+='</div></div>';
  if(d.top_pairs&&d.top_pairs.length){
    h+='<div class="card full-width"><h3>TOP YIN-YANG PAIRS</h3>';
    for(let p of d.top_pairs){
      h+='<div class="pair-row"><div class="pair-yin">'+p.yin_archetype+' '+p.yin_agent.substring(0,10)+'</div>';
      h+='<div class="pair-boost">'+p.resonance.harmonic_boost.toFixed(3)+'x</div>';
      h+='<div class="pair-yang">'+p.yang_agent.substring(0,10)+' '+p.yang_archetype+'</div></div>';
    }
    h+='</div>';
  }
  h+='</div>';
  document.getElementById('output').innerHTML=h;
}

function renderStress(d){
  let h='<div class="verdict"><div class="pct '+(d.target_met?'met':'notmet')+'">'+d.resonance_increase_pct.toFixed(1)+'%</div>';
  h+='<div style="color:#888;margin-top:5px">RESONANCE INCREASE (paired vs unpaired)</div>';
  h+='<div style="margin-top:10px;color:'+(d.target_met?'#4aff6b':'#ff4a4a')+'">'+(d.target_met?'TARGET MET (>=20%)':'TARGET NOT MET (<20%)')+'</div></div>';
  h+='<div class="grid">';
  h+='<div class="card"><h3>STRESS PARAMETERS</h3>';
  h+=stat('Agents',d.agent_count);h+=stat('Rounds',d.rounds);h+=stat('Max Pressure',d.pressure_max+'x');
  h+=stat('Pairs Formed',d.pairs_count);h+=stat('Unpaired',d.unpaired_count);
  h+=stat('Avg Pair Boost','<span class="boost-color">'+d.formation_stats.avg_resonance_boost.toFixed(4)+'</span>');
  h+='</div>';
  h+='<div class="card"><h3>FINAL RESULT</h3>';
  h+=stat('Paired Activity','<span class="boost-color">'+d.final_paired_activity.toFixed(4)+'</span>');
  h+=stat('Unpaired Activity',d.final_unpaired_activity.toFixed(4));
  h+=stat('Resonance Increase','<span class="'+(d.target_met?'met':'notmet')+'">'+d.resonance_increase_pct.toFixed(2)+'%</span>');
  h+='<div class="bar-container"><div class="bar-boost" style="width:'+Math.min(100,d.resonance_increase_pct*2)+'%"></div></div>';
  h+='</div>';
  h+='<div class="card full-width"><h3>ROUND-BY-ROUND</h3>';
  h+='<div class="round-row round-header"><div>Round</div><div>Press</div><div>Paired</div><div>Unpaired</div><div>Gap</div></div>';
  for(let r of d.round_data){
    h+='<div class="round-row"><div>'+r.round+'</div><div>'+r.pressure.toFixed(1)+'x</div>';
    h+='<div class="boost-color">'+r.paired_avg_activity.toFixed(4)+'</div>';
    h+='<div>'+r.unpaired_avg_activity.toFixed(4)+'</div>';
    h+='<div style="color:'+(r.activity_gap>=0?'#4aff6b':'#ff4a4a')+'">'+r.activity_gap.toFixed(4)+'</div></div>';
  }
  h+='</div></div>';
  document.getElementById('output').innerHTML=h;
}

function stat(l,v){return '<div class="stat"><span class="label">'+l+'</span><span class="value">'+v+'</span></div>'}
</script>
</body>
</html>
"""

@yin_yang_bp.route("/yin-yang")
def yin_yang_page():
    return render_template_string(YIN_YANG_HTML)


@yin_yang_bp.route("/api/yin-yang/formation", methods=["POST"])
def api_formation():
    global _yy_running, _yy_result
    with _yy_lock:
        if _yy_running:
            return jsonify({"error": "Already running"}), 409

    data = request.get_json(silent=True) or {}
    agent_count = int(data.get("agent_count", 286))
    seed = data.get("seed", "void")
    pairing = data.get("pairing", "greedy")

    try:
        from void_engine.yin_yang_286 import create_yin_yang_formation
        result = create_yin_yang_formation(agent_count=agent_count, seed=seed, pairing=pairing)
        with _yy_lock:
            _yy_result = result
        return jsonify(result)
    except Exception as e:
        logger.error("Yin-Yang formation failed: %s", e)
        return jsonify({"error": str(e)}), 500


@yin_yang_bp.route("/api/yin-yang/stress", methods=["POST"])
def api_stress():
    global _yy_running, _yy_result
    with _yy_lock:
        if _yy_running:
            return jsonify({"error": "Already running"}), 409

    _yy_running = True
    data = request.get_json(silent=True) or {}
    agent_count = int(data.get("agent_count", 100))
    seed = data.get("seed", "yin_yang_stress")
    rounds = int(data.get("rounds", 20))
    pressure_max = float(data.get("pressure_max", 10.0))

    def _run():
        global _yy_running, _yy_result
        try:
            from void_engine.yin_yang_286 import run_paired_stress_test
            result = run_paired_stress_test(
                agent_count=agent_count, seed=seed,
                rounds=rounds, pressure_max=pressure_max,
            )
            with _yy_lock:
                _yy_result = result
        except Exception as e:
            logger.error("Yin-Yang stress failed: %s", e)
            with _yy_lock:
                _yy_result = {"error": str(e)}
        finally:
            _yy_running = False

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"status": "running", "message": "Yin-Yang stress test started"})


@yin_yang_bp.route("/api/yin-yang/status")
def api_status():
    with _yy_lock:
        if _yy_running:
            return jsonify({"status": "running"})
        if _yy_result:
            return jsonify({"status": "complete", "result": _yy_result})
        return jsonify({"status": "idle"})
