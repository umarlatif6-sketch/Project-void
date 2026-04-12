"""
Memory Capture — Record moments, encode them as formation memories.

Camera/video capture → frequency signature → Al-Jabr 286 hash → VOID memory artifact.
A recording becomes a formation — not just a file, but an identity-sealed memory.

/memories                   (GET — capture page)
/api/memories/seal          (POST — seal a memory with formation hash)
/api/memories/list          (GET — list sealed memories)
"""

import time
import hashlib
import logging
import math
import json
from flask import Blueprint, render_template_string, jsonify, request

logger = logging.getLogger(__name__)

memory_capture_bp = Blueprint("memory_capture", __name__)

_sealed_memories = []


def _al_jabr_286_hash(data_bytes: bytes) -> str:
    bismillah = "BismillahirRahmanirRahim"
    salted = bismillah.encode() + data_bytes
    sha = hashlib.sha256(salted).hexdigest()
    extra_30 = hashlib.sha256(data_bytes + b"Al-Latif-30").hexdigest()[:8]
    return sha + extra_30


def _frequency_from_hash(h: str) -> float:
    val = int(h[:8], 16)
    return 432.0 + (val % 14800) / 100.0


def _chladni_mode(freq: float) -> str:
    n = int(freq) % 7
    m = int(freq * 10) % 5
    return f"({n},{m})"


@memory_capture_bp.route("/memories")
def page():
    return render_template_string(TEMPLATE)


@memory_capture_bp.route("/api/memories/seal", methods=["POST"])
def seal():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()[:100] or "Untitled Memory"
    location = data.get("location", "").strip()[:100] or "Unknown"
    media_type = data.get("media_type", "photo")
    duration = data.get("duration", 0)
    size_bytes = data.get("size_bytes", 0)
    timestamp = data.get("timestamp", "")
    thumbnail_data = data.get("thumbnail", "")[:5000]

    content_seed = f"{title}:{location}:{timestamp}:{size_bytes}:{media_type}"
    formation_hash = _al_jabr_286_hash(content_seed.encode())
    freq = _frequency_from_hash(formation_hash)
    mode = _chladni_mode(freq)

    memory = {
        "id": len(_sealed_memories) + 1,
        "title": title,
        "location": location,
        "media_type": media_type,
        "duration_seconds": duration,
        "size_bytes": size_bytes,
        "timestamp": timestamp or time.strftime("%Y-%m-%d %H:%M:%S"),
        "formation_hash": formation_hash,
        "frequency_hz": round(freq, 2),
        "chladni_mode": mode,
        "sealed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "has_thumbnail": bool(thumbnail_data),
    }

    z_axis_card_b64 = None
    try:
        from void_engine.z_axis_encoder import encode_memory_metadata
        import base64 as b64mod
        png_bytes = encode_memory_metadata(memory, formation_hash, thumbnail_data)
        z_axis_card_b64 = b64mod.b64encode(png_bytes).decode("ascii")
        memory["z_axis_encoded"] = True
        memory["z_axis_card_size"] = len(png_bytes)
    except Exception as zex:
        logger.warning(f"Z-axis encoding skipped for memory: {zex}")
        memory["z_axis_encoded"] = False

    _sealed_memories.append(memory)
    logger.info(f"Memory sealed: {title} @ {freq:.2f} Hz — {formation_hash[:16]}...")

    response = {
        "status": "sealed",
        "memory": memory,
        "message_en": f"Memory sealed at {freq:.2f} Hz — Chladni mode {mode}. Formation hash: {formation_hash[:32]}...",
        "message_ur": f"یاد محفوظ ہو گئی — {freq:.2f} Hz پر۔ فارمیشن ہیش: {formation_hash[:16]}...",
    }
    if z_axis_card_b64:
        response["z_axis_card_b64"] = z_axis_card_b64
        response["z_axis_card_size"] = memory.get("z_axis_card_size", 0)

    return jsonify(response)


@memory_capture_bp.route("/api/memories/list")
def list_memories():
    return jsonify({
        "total": len(_sealed_memories),
        "memories": list(reversed(_sealed_memories)),
    })


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Memory Capture — PROJECT VOID</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:Georgia,'Times New Roman',serif;min-height:100vh;display:flex;flex-direction:column}
.container{max-width:600px;margin:0 auto;padding:16px;width:100%;flex:1;display:flex;flex-direction:column}

header{text-align:center;padding:20px 0;border-bottom:1px solid #1a1a1a}
.h-title{font-size:24px;font-weight:300;color:#fff;letter-spacing:6px;margin-bottom:4px}
.h-title span{color:#c0955a}
.h-sub{font-size:11px;color:#888;letter-spacing:3px;font-family:'Courier New',monospace}

.mode-tabs{display:flex;gap:0;margin:16px 0;border:1px solid #222;border-radius:4px;overflow:hidden}
.mode-tab{flex:1;padding:10px;text-align:center;font-size:11px;letter-spacing:2px;font-family:'Courier New',monospace;cursor:pointer;background:#111;color:#555;border:none;transition:all .3s}
.mode-tab.active{background:#c0955a;color:#0a0a0a}

.camera-zone{position:relative;background:#000;border-radius:8px;overflow:hidden;aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;margin-bottom:16px}
.camera-zone video{width:100%;height:100%;object-fit:cover}
.camera-zone canvas{display:none}
.camera-zone .placeholder{text-align:center;color:#333;font-size:12px;letter-spacing:2px;font-family:'Courier New',monospace}
.camera-overlay{position:absolute;bottom:0;left:0;right:0;padding:12px;background:linear-gradient(transparent,rgba(0,0,0,.8));display:flex;justify-content:center;gap:12px;align-items:center}

.cap-btn{width:56px;height:56px;border-radius:50%;border:3px solid #c0955a;background:transparent;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}
.cap-btn:active{transform:scale(.9)}
.cap-btn .inner{width:40px;height:40px;border-radius:50%;background:#c0955a;transition:all .3s}
.cap-btn.recording .inner{background:#e74c3c;border-radius:4px;width:24px;height:24px}

.flip-btn{width:36px;height:36px;border-radius:50%;border:1px solid #333;background:#111;color:#888;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center}

.rec-time{font-size:12px;color:#e74c3c;font-family:'Courier New',monospace;letter-spacing:2px;display:none}
.rec-time.show{display:block}

.title-input{width:100%;background:#111;border:1px solid #222;color:#fff;padding:10px 12px;font-family:inherit;font-size:14px;border-radius:4px;outline:none;margin-bottom:8px}
.title-input:focus{border-color:#c0955a}
.loc-row{display:flex;gap:8px;margin-bottom:16px}
.loc-input{flex:1;background:#111;border:1px solid #222;color:#fff;padding:10px 12px;font-family:inherit;font-size:14px;border-radius:4px;outline:none}
.loc-input:focus{border-color:#c0955a}
.loc-btn{background:#222;border:1px solid #333;color:#888;padding:10px;font-size:12px;cursor:pointer;border-radius:4px;white-space:nowrap;font-family:'Courier New',monospace}

.seal-result{background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;padding:16px;margin-bottom:16px;display:none}
.seal-result.show{display:block}
.seal-hash{font-family:'Courier New',monospace;font-size:10px;color:#c0955a;word-break:break-all;margin:8px 0;line-height:1.6}
.seal-freq{font-size:20px;color:#fff;font-weight:300;text-align:center;margin:8px 0}
.seal-freq span{color:#c0955a}
.seal-mode{text-align:center;font-size:10px;color:#555;letter-spacing:3px;font-family:'Courier New',monospace}
.seal-msg{text-align:center;font-size:13px;color:#888;margin-top:8px;line-height:1.6}
.seal-msg-ur{text-align:center;font-size:15px;color:#888;margin-top:4px;direction:rtl;font-family:'Noto Nastaliq Urdu',serif}

.formation-card-zone{margin:16px 0;text-align:center}
.formation-card-zone canvas{border:1px solid #1a1a1a;border-radius:4px;max-width:100%;cursor:pointer}
.card-progress{font-size:10px;color:#555;font-family:'Courier New',monospace;letter-spacing:2px;margin:8px 0;height:14px}
.card-progress .bar{display:inline-block;width:200px;height:3px;background:#111;border-radius:2px;vertical-align:middle;margin-left:6px;overflow:hidden}
.card-progress .fill{height:100%;background:#c0955a;width:0%;transition:width .1s}
.card-label{font-size:11px;color:#c0955a;letter-spacing:3px;font-family:'Courier New',monospace;margin-bottom:6px}
.card-meta{font-size:9px;color:#444;font-family:'Courier New',monospace;letter-spacing:1px;margin-top:4px}
.card-actions{margin-top:8px;display:flex;gap:8px;justify-content:center}
.card-actions button{background:#111;border:1px solid #222;color:#888;padding:8px 16px;font-size:10px;letter-spacing:2px;font-family:'Courier New',monospace;cursor:pointer;border-radius:4px;transition:all .2s}
.card-actions button:hover{border-color:#c0955a;color:#c0955a}

.memories-section{margin-top:16px}
.memories-title{font-size:11px;letter-spacing:3px;color:#c0955a;font-family:'Courier New',monospace;border-bottom:1px solid #1a1a1a;padding-bottom:6px;margin-bottom:12px}
.mem-card{background:#0d0d0d;border:1px solid #151515;padding:12px;margin-bottom:8px;border-radius:4px;display:flex;gap:12px;align-items:center;cursor:pointer;transition:border-color .2s}
.mem-card:hover{border-color:#222}
.mem-icon{width:40px;height:40px;border-radius:4px;background:#111;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.mem-info{flex:1;min-width:0}
.mem-title{font-size:14px;color:#fff;margin-bottom:2px}
.mem-meta{font-size:10px;color:#555;font-family:'Courier New',monospace;letter-spacing:1px}
.mem-freq{font-size:12px;color:#c0955a;font-family:'Courier New',monospace}
.mem-empty{text-align:center;color:#333;font-size:12px;padding:20px;font-family:'Courier New',monospace;letter-spacing:2px}

.viz-canvas{width:100%;height:80px;border-radius:4px;margin:8px 0}

.card-modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.95);z-index:1000;justify-content:center;align-items:center;flex-direction:column;padding:16px}
.card-modal.show{display:flex}
.card-modal canvas{max-width:90vw;max-height:70vh;border:1px solid #222;border-radius:4px}
.card-modal .close-modal{position:absolute;top:16px;right:20px;color:#555;font-size:24px;cursor:pointer;background:none;border:none}
.card-modal .modal-info{text-align:center;margin-top:12px;color:#888;font-size:11px;font-family:'Courier New',monospace;letter-spacing:2px}

footer{text-align:center;padding:16px 0;border-top:1px solid #1a1a1a;margin-top:16px}
footer p{font-size:10px;color:#333;letter-spacing:3px;font-family:'Courier New',monospace}
</style>
<link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
</head>
<body>
<div class="container">

<header>
  <div class="h-title">MEMORY <span>CAPTURE</span></div>
  <div class="h-sub">RECORD — ENCODE — SEAL INTO FORMATION</div>
</header>

<div class="mode-tabs">
  <button class="mode-tab active" onclick="setMode('photo',this)">PHOTO</button>
  <button class="mode-tab" onclick="setMode('video',this)">VIDEO</button>
</div>

<div class="camera-zone" id="cameraZone">
  <div class="placeholder" id="camPlaceholder">TAP TO OPEN CAMERA</div>
  <video id="camVideo" autoplay playsinline muted style="display:none"></video>
  <canvas id="camCanvas"></canvas>
  <div class="camera-overlay" id="camOverlay" style="display:none">
    <div class="rec-time" id="recTime">00:00</div>
    <button class="flip-btn" onclick="flipCamera()">&#x21BB;</button>
    <button class="cap-btn" id="capBtn" onclick="capture()"><div class="inner"></div></button>
  </div>
</div>

<input class="title-input" id="memTitle" placeholder="Name this memory..." value="">
<div class="loc-row">
  <input class="loc-input" id="memLocation" placeholder="Location (e.g. Blue Mosque, Istanbul)">
  <button class="loc-btn" onclick="autoLocation()">&#x1F4CD; GPS</button>
</div>

<div class="seal-result" id="sealResult">
  <canvas class="viz-canvas" id="vizCanvas"></canvas>
  <div class="seal-freq" id="sealFreq"></div>
  <div class="seal-mode" id="sealMode"></div>

  <div class="formation-card-zone" id="cardZone">
    <div class="card-label">FORMATION IDENTITY CARD</div>
    <div class="card-progress" id="cardProgress"></div>
    <canvas id="formationCard" width="600" height="800"></canvas>
    <div class="card-meta" id="cardMeta"></div>
    <div class="card-actions">
      <button onclick="downloadCard()">DOWNLOAD CARD</button>
      <button onclick="openCardFullscreen()">FULLSCREEN</button>
    </div>
  </div>

  <div class="seal-hash" id="sealHash"></div>
  <div class="seal-msg" id="sealMsg"></div>
  <div class="seal-msg-ur" id="sealMsgUr"></div>
</div>

<div class="memories-section">
  <div class="memories-title">SEALED MEMORIES</div>
  <div id="memList"><div class="mem-empty">NO MEMORIES YET — RECORD YOUR FIRST MOMENT</div></div>
</div>

</div>

<div class="card-modal" id="cardModal">
  <button class="close-modal" onclick="closeModal()">&times;</button>
  <canvas id="modalCanvas"></canvas>
  <div class="modal-info" id="modalInfo"></div>
</div>

<footer>
  <p>PROJECT VOID — MEMORY CAPTURE</p>
</footer>

<script>
const Z_LAYERS=9999;
const RENDER_BATCH=999;
const LAYER_OPACITY=0.003;
const CARD_W=600;
const CARD_H=800;

let mode='photo';
let stream=null;
let mediaRecorder=null;
let recordedChunks=[];
let recording=false;
let recInterval=null;
let recSeconds=0;
let facingMode='environment';
let cameraOpen=false;
let lastSealData=null;
let capturedPhotoData=null;

const video=document.getElementById('camVideo');
const canvas=document.getElementById('camCanvas');
const placeholder=document.getElementById('camPlaceholder');
const overlay=document.getElementById('camOverlay');
const capBtn=document.getElementById('capBtn');

document.getElementById('cameraZone').addEventListener('click',function(e){
  if(!cameraOpen&&!e.target.closest('button')){openCamera();}
});

function setMode(m,btn){
  mode=m;
  document.querySelectorAll('.mode-tab').forEach(t=>t.classList.remove('active'));
  btn.classList.add('active');
  if(recording)stopRecording();
}

async function openCamera(){
  try{
    if(stream){stream.getTracks().forEach(t=>t.stop());}
    stream=await navigator.mediaDevices.getUserMedia({
      video:{facingMode:facingMode,width:{ideal:1280},height:{ideal:960}},
      audio:true
    });
    video.srcObject=stream;
    video.style.display='block';
    placeholder.style.display='none';
    overlay.style.display='flex';
    cameraOpen=true;
  }catch(e){
    placeholder.textContent='CAMERA ACCESS DENIED — CHECK PERMISSIONS';
    console.error(e);
  }
}

async function flipCamera(){
  facingMode=facingMode==='environment'?'user':'environment';
  await openCamera();
}

function capture(){
  if(mode==='photo'){takePhoto();}
  else{recording?stopRecording():startRecording();}
}

function takePhoto(){
  canvas.width=video.videoWidth;
  canvas.height=video.videoHeight;
  const ctx=canvas.getContext('2d');
  ctx.drawImage(video,0,0);
  const dataUrl=canvas.toDataURL('image/jpeg',0.8);
  capturedPhotoData=dataUrl;
  const size=Math.round(dataUrl.length*0.75);
  sealMemory('photo',size,0,dataUrl.substring(0,4000));
}

function startRecording(){
  recordedChunks=[];
  const options={mimeType:'video/webm;codecs=vp8,opus'};
  try{mediaRecorder=new MediaRecorder(stream,options);}
  catch(e){
    try{mediaRecorder=new MediaRecorder(stream);}
    catch(e2){alert('Recording not supported');return;}
  }
  mediaRecorder.ondataavailable=e=>{if(e.data.size>0)recordedChunks.push(e.data);};
  mediaRecorder.onstop=()=>{
    const blob=new Blob(recordedChunks,{type:'video/webm'});
    capturedPhotoData=null;
    sealMemory('video',blob.size,recSeconds,'');
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;a.download=`void_memory_${Date.now()}.webm`;
    a.click();URL.revokeObjectURL(url);
  };
  mediaRecorder.start(1000);
  recording=true;
  recSeconds=0;
  capBtn.classList.add('recording');
  document.getElementById('recTime').classList.add('show');
  recInterval=setInterval(()=>{
    recSeconds++;
    const m=String(Math.floor(recSeconds/60)).padStart(2,'0');
    const s=String(recSeconds%60).padStart(2,'0');
    document.getElementById('recTime').textContent=m+':'+s;
  },1000);
}

function stopRecording(){
  if(mediaRecorder&&mediaRecorder.state!=='inactive'){mediaRecorder.stop();}
  recording=false;
  capBtn.classList.remove('recording');
  document.getElementById('recTime').classList.remove('show');
  clearInterval(recInterval);
}

async function sealMemory(mediaType,sizeBytes,duration,thumbnail){
  const title=document.getElementById('memTitle').value.trim()||'Istanbul Memory';
  const location=document.getElementById('memLocation').value.trim()||'Istanbul';
  try{
    const res=await fetch('/api/memories/seal',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        title:title,location:location,media_type:mediaType,
        duration:duration,size_bytes:sizeBytes,
        timestamp:new Date().toISOString(),
        thumbnail:thumbnail
      })
    });
    const d=await res.json();
    if(d.status==='sealed'){
      lastSealData=d;
      showSealResult(d);
      loadMemories();
    }
  }catch(e){console.error(e);}
}

function showSealResult(d){
  const r=document.getElementById('sealResult');
  r.classList.add('show');
  document.getElementById('sealFreq').innerHTML=d.memory.frequency_hz+' <span>Hz</span>';
  document.getElementById('sealMode').textContent='CHLADNI MODE '+d.memory.chladni_mode;
  document.getElementById('sealHash').textContent=d.memory.formation_hash;
  document.getElementById('sealMsg').textContent=d.message_en;
  document.getElementById('sealMsgUr').textContent=d.message_ur;
  drawViz(d.memory.frequency_hz,d.memory.formation_hash);
  renderFormationCard(d.memory,capturedPhotoData);
}

function drawViz(freq,hash){
  const c=document.getElementById('vizCanvas');
  const ctx=c.getContext('2d');
  c.width=c.offsetWidth*2;c.height=160;
  ctx.fillStyle='#0d0d0d';ctx.fillRect(0,0,c.width,c.height);

  for(let x=0;x<c.width;x+=2){
    const h1=Math.sin(x*0.02*freq/432)*30;
    const h2=Math.sin(x*0.05+parseInt(hash.substring(0,4),16)/1000)*15;
    const h3=Math.sin(x*0.008*freq/286)*20;
    const y=c.height/2+h1+h2+h3;
    const alpha=0.3+Math.abs(Math.sin(x*0.01))*0.5;
    ctx.fillStyle=`rgba(192,149,90,${alpha})`;
    ctx.fillRect(x,y,1.5,2);
  }

  for(let i=0;i<hash.length&&i<64;i++){
    const val=parseInt(hash[i],16);
    const x=(i/64)*c.width;
    const y=c.height-4-val*0.8;
    ctx.fillStyle=`rgba(192,149,90,0.15)`;
    ctx.fillRect(x,y,c.width/64-1,val*0.8+4);
  }
}


function hashToSeed(hash,offset){
  let v=0;
  for(let i=0;i<8;i++){
    v+=parseInt(hash[(offset+i)%hash.length],16);
  }
  return v;
}

function chladniValue(x,y,n,m,phase){
  const nx=x*Math.PI;
  const ny=y*Math.PI;
  return Math.sin(n*nx+phase)*Math.sin(m*ny+phase)
       + Math.sin(m*nx+phase)*Math.sin(n*ny+phase);
}

function renderFormationCard(memory,photoData){
  const fc=document.getElementById('formationCard');
  const ctx=fc.getContext('2d');
  fc.width=CARD_W;fc.height=CARD_H;

  ctx.fillStyle='#050505';
  ctx.fillRect(0,0,CARD_W,CARD_H);

  const hash=memory.formation_hash;
  const baseFreq=memory.frequency_hz;
  const modeStr=memory.chladni_mode;
  const mParts=modeStr.replace(/[()]/g,'').split(',');
  const baseN=parseInt(mParts[0])||3;
  const baseM=parseInt(mParts[1])||2;

  const imgRegionY=60;
  const imgRegionH=440;
  const metaY=imgRegionY+imgRegionH+20;

  let layersDone=0;
  const progressEl=document.getElementById('cardProgress');
  const metaEl=document.getElementById('cardMeta');

  if(photoData){
    const img=new Image();
    img.onload=function(){
      ctx.save();
      ctx.globalAlpha=0.12;
      const aspect=img.width/img.height;
      let dw=CARD_W-40,dh=imgRegionH;
      if(aspect>dw/dh){dh=dw/aspect;}else{dw=dh*aspect;}
      const dx=(CARD_W-dw)/2;
      const dy=imgRegionY+(imgRegionH-dh)/2;
      ctx.drawImage(img,dx,dy,dw,dh);
      ctx.restore();
      startLayering();
    };
    img.src=photoData;
  }else{
    startLayering();
  }

  function startLayering(){
    renderBatch(0);
  }

  function renderBatch(startLayer){
    const end=Math.min(startLayer+RENDER_BATCH,Z_LAYERS);

    for(let z=startLayer;z<end;z++){
      const zNorm=z/Z_LAYERS;
      const seed=hashToSeed(hash,z%60);
      const freqShift=baseFreq+(seed-40)*zNorm*2;
      const n=baseN+Math.sin(z*0.01+seed)*2;
      const m=baseM+Math.cos(z*0.013+seed)*1.5;
      const phase=zNorm*Math.PI*2+seed*0.1;

      const r0=parseInt(hash[(z*3)%hash.length],16);
      const g0=parseInt(hash[(z*3+1)%hash.length],16);
      const b0=parseInt(hash[(z*3+2)%hash.length],16);
      const cr=140+r0*7;
      const cg=100+g0*5;
      const cb=50+b0*4;

      const regionX=20;
      const regionW=CARD_W-40;

      const step=Math.max(2,Math.floor(4-zNorm*2));
      for(let px=0;px<regionW;px+=step){
        for(let py=0;py<imgRegionH;py+=step){
          const nx=px/regionW;
          const ny=py/imgRegionH;
          const val=chladniValue(nx,ny,n,m,phase);
          const absVal=Math.abs(val);

          if(absVal<0.08){
            const a=LAYER_OPACITY*(1+absVal*3);
            ctx.fillStyle=`rgba(${cr},${cg},${cb},${a})`;
            const sz=1+absVal*2;
            ctx.fillRect(regionX+px,imgRegionY+py,sz,sz);
          }
        }
      }

      if(z%50===0){
        const orbX=CARD_W/2+Math.cos(z*0.02)*200*zNorm;
        const orbY=imgRegionY+imgRegionH/2+Math.sin(z*0.017)*180*zNorm;
        ctx.fillStyle=`rgba(${cr},${cg},${cb},0.01)`;
        ctx.beginPath();
        ctx.arc(orbX,orbY,2+zNorm*8,0,Math.PI*2);
        ctx.fill();
      }
    }

    layersDone=end;
    const pct=Math.round((layersDone/Z_LAYERS)*100);
    progressEl.innerHTML=`LAYER ${layersDone}/${Z_LAYERS} <div class="bar"><div class="fill" style="width:${pct}%"></div></div>`;

    if(end<Z_LAYERS){
      requestAnimationFrame(()=>renderBatch(end));
    }else{
      finalizeCard(ctx,memory);
      progressEl.innerHTML=`${Z_LAYERS} LAYERS RENDERED — FORMATION COMPLETE`;
      metaEl.textContent=`${memory.frequency_hz} Hz | ${memory.chladni_mode} | ${hash.substring(0,24)}...`;
    }
  }

  function finalizeCard(ctx,mem){
    ctx.fillStyle='rgba(5,5,5,0.7)';
    ctx.fillRect(0,0,CARD_W,54);
    ctx.fillRect(0,metaY-10,CARD_W,CARD_H-metaY+10);

    ctx.fillStyle='#c0955a';
    ctx.font='300 10px "Courier New",monospace';
    ctx.textAlign='center';
    ctx.fillText('FORMATION IDENTITY CARD',CARD_W/2,16);

    ctx.fillStyle='#fff';
    ctx.font='300 11px "Courier New",monospace';
    ctx.fillText('PROJECT VOID',CARD_W/2,32);

    ctx.fillStyle='#333';
    ctx.font='8px "Courier New",monospace';
    ctx.fillText(Z_LAYERS+' Z-AXIS LAYERS \u2014 '+LAYER_OPACITY*100+'% PER LAYER',CARD_W/2,46);

    ctx.fillStyle='#fff';
    ctx.font='300 18px Georgia,serif';
    ctx.textAlign='center';
    ctx.fillText(mem.title,CARD_W/2,metaY+14);

    ctx.fillStyle='#888';
    ctx.font='12px Georgia,serif';
    ctx.fillText(mem.location,CARD_W/2,metaY+34);

    ctx.fillStyle='#c0955a';
    ctx.font='300 28px "Courier New",monospace';
    ctx.fillText(mem.frequency_hz+' Hz',CARD_W/2,metaY+70);

    ctx.fillStyle='#555';
    ctx.font='10px "Courier New",monospace';
    ctx.fillText('CHLADNI MODE '+mem.chladni_mode,CARD_W/2,metaY+88);

    ctx.fillStyle='#333';
    ctx.font='8px "Courier New",monospace';
    const hashLines=[hash.substring(0,36),hash.substring(36)];
    hashLines.forEach((ln,i)=>{
      ctx.fillText(ln,CARD_W/2,metaY+108+i*12);
    });

    ctx.fillStyle='#222';
    ctx.font='8px "Courier New",monospace';
    ctx.fillText('AL-JABR 286 \u2014 BISMILLAHIRRAHMANIRRAHIM',CARD_W/2,metaY+140);

    ctx.fillStyle='#1a1a1a';
    ctx.font='8px "Courier New",monospace';
    ctx.fillText(mem.media_type.toUpperCase()+' \u2014 '+mem.sealed_at,CARD_W/2,metaY+158);

    ctx.strokeStyle='#1a1a1a';
    ctx.lineWidth=1;
    ctx.strokeRect(0,0,CARD_W,CARD_H);

    ctx.strokeStyle='#c0955a';
    ctx.lineWidth=0.5;
    ctx.strokeRect(8,8,CARD_W-16,CARD_H-16);
  }
}

function downloadCard(){
  const fc=document.getElementById('formationCard');
  const link=document.createElement('a');
  const mem=lastSealData?lastSealData.memory:null;
  const name=mem?mem.title.replace(/[^a-zA-Z0-9]/g,'_'):'memory';
  link.download=`void_formation_${name}_${Date.now()}.png`;
  link.href=fc.toDataURL('image/png');
  link.click();
}

function openCardFullscreen(){
  const src=document.getElementById('formationCard');
  const modal=document.getElementById('cardModal');
  const mc=document.getElementById('modalCanvas');
  mc.width=src.width;mc.height=src.height;
  mc.getContext('2d').drawImage(src,0,0);
  const mem=lastSealData?lastSealData.memory:null;
  if(mem){
    document.getElementById('modalInfo').textContent=
      mem.title+' \u2014 '+mem.frequency_hz+' Hz \u2014 '+Z_LAYERS+' LAYERS \u2014 '+mem.chladni_mode;
  }
  modal.classList.add('show');
}

function closeModal(){
  document.getElementById('cardModal').classList.remove('show');
}

document.getElementById('cardModal').addEventListener('click',function(e){
  if(e.target===this)closeModal();
});

async function loadMemories(){
  try{
    const res=await fetch('/api/memories/list');
    const d=await res.json();
    const list=document.getElementById('memList');
    if(!d.memories||d.memories.length===0){
      list.innerHTML='<div class="mem-empty">NO MEMORIES YET \u2014 RECORD YOUR FIRST MOMENT</div>';
      return;
    }
    list.innerHTML=d.memories.map(m=>`
      <div class="mem-card" onclick="regenerateCard(${m.id})">
        <div class="mem-icon">${m.media_type==='video'?'&#x1F3AC;':'&#x1F4F7;'}</div>
        <div class="mem-info">
          <div class="mem-title">${esc(m.title)}</div>
          <div class="mem-meta">${esc(m.location)} \u2014 ${m.sealed_at}</div>
          <div class="mem-freq">${m.frequency_hz} Hz \u2014 ${m.chladni_mode}</div>
        </div>
      </div>
    `).join('');
  }catch(e){console.error(e);}
}

function regenerateCard(id){
  fetch('/api/memories/list').then(r=>r.json()).then(d=>{
    const mem=d.memories.find(m=>m.id===id);
    if(mem){
      lastSealData={memory:mem};
      capturedPhotoData=null;
      document.getElementById('sealResult').classList.add('show');
      document.getElementById('sealFreq').innerHTML=mem.frequency_hz+' <span>Hz</span>';
      document.getElementById('sealMode').textContent='CHLADNI MODE '+mem.chladni_mode;
      document.getElementById('sealHash').textContent=mem.formation_hash;
      document.getElementById('sealMsg').textContent='Regenerating formation card...';
      document.getElementById('sealMsgUr').textContent='';
      drawViz(mem.frequency_hz,mem.formation_hash);
      renderFormationCard(mem,null);
      document.getElementById('sealResult').scrollIntoView({behavior:'smooth'});
    }
  });
}

function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}

function autoLocation(){
  if(!navigator.geolocation){
    document.getElementById('memLocation').value='Istanbul';return;
  }
  navigator.geolocation.getCurrentPosition(
    pos=>{document.getElementById('memLocation').value=`${pos.coords.latitude.toFixed(4)}\u00B0N, ${pos.coords.longitude.toFixed(4)}\u00B0E`;},
    ()=>{document.getElementById('memLocation').value='Istanbul';}
  );
}

loadMemories();
</script>
</body>
</html>"""
