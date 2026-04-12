"""
Z-Axis Formation Encoder — Dimensional Steganography Protocol.

Routes:
    /z-axis                     (GET — encode/decode UI page)
    /api/z-axis/encode          (POST — encode data into formation card)
    /api/z-axis/decode          (POST — decode data from formation card)
    /api/z-axis/capacity        (GET — capacity calculator)
    /api/z-axis/encode-moment   (POST — encode resonance moment into card)
"""

import io
import base64
import json
import logging
from flask import Blueprint, request, jsonify, render_template_string, send_file

logger = logging.getLogger(__name__)

z_axis_bp = Blueprint("z_axis", __name__)


@z_axis_bp.route("/z-axis")
def page():
    return render_template_string(Z_AXIS_TEMPLATE)


@z_axis_bp.route("/api/z-axis/encode", methods=["POST"])
def encode_data():
    from void_engine.z_axis_encoder import encode, fatiha_286_hexdigest

    content_type = request.content_type or ""

    if "multipart/form-data" in content_type:
        formation_hash = request.form.get("formation_hash", "")
        file = request.files.get("file")
        text = request.form.get("text", "")
        if file:
            payload = file.read()
        elif text:
            payload = text.encode("utf-8")
        else:
            return jsonify({"error": "Provide file or text to encode"}), 400
    else:
        data = request.get_json(silent=True) or {}
        formation_hash = data.get("formation_hash", "")
        text = data.get("text", "")
        file_b64 = data.get("file_b64", "")
        json_data = data.get("json_data")

        if file_b64:
            payload = base64.b64decode(file_b64)
        elif json_data:
            payload = json.dumps(json_data, default=str).encode("utf-8")
        elif text:
            payload = text.encode("utf-8")
        else:
            return jsonify({"error": "Provide text, file_b64, or json_data to encode"}), 400

    MAX_PAYLOAD_BYTES = 90_000
    if len(payload) > MAX_PAYLOAD_BYTES:
        return jsonify({"error": f"Payload too large: {len(payload):,} bytes exceeds {MAX_PAYLOAD_BYTES:,} byte limit"}), 413

    if not formation_hash:
        formation_hash = fatiha_286_hexdigest(payload)

    try:
        width = int(request.args.get("width", 600))
        height = int(request.args.get("height", 800))
        width = max(200, min(width, 2000))
        height = max(200, min(height, 2000))
    except (ValueError, TypeError):
        width, height = 600, 800

    try:
        png_bytes = encode(payload, formation_hash, width=width, height=height)
    except Exception as e:
        logger.error("[Z-Axis] Encode failed: %s", e)
        return jsonify({"error": str(e)}), 500

    image_b64 = base64.b64encode(png_bytes).decode("ascii")

    return jsonify({
        "status": "encoded",
        "formation_hash": formation_hash,
        "payload_size": len(payload),
        "image_size_bytes": len(png_bytes),
        "image_b64": image_b64,
        "layers": 9999,
        "integrity_286": fatiha_286_hexdigest(payload)[:32],
    })


@z_axis_bp.route("/api/z-axis/decode", methods=["POST"])
def decode_data():
    from void_engine.z_axis_encoder import decode

    content_type = request.content_type or ""

    if "multipart/form-data" in content_type:
        formation_hash = request.form.get("formation_hash", "")
        file = request.files.get("image")
        if not file:
            return jsonify({"error": "Provide image file"}), 400
        image_data = file.read()
    else:
        data = request.get_json(silent=True) or {}
        formation_hash = data.get("formation_hash", "")
        image_b64 = data.get("image_b64", "")
        if not image_b64:
            return jsonify({"error": "Provide image_b64"}), 400
        image_data = base64.b64decode(image_b64)

    if not formation_hash:
        return jsonify({"error": "formation_hash is required for decoding"}), 400

    try:
        payload = decode(image_data, formation_hash)
    except ValueError as e:
        error_msg = str(e)
        is_integrity = "integrity" in error_msg.lower() or "checksum" in error_msg.lower()
        logger.error("[Z-Axis] Decode failed: %s", e)
        return jsonify({
            "error": error_msg,
            "integrity_286": "FAILED" if is_integrity else "unknown",
        }), 422 if is_integrity else 500
    except Exception as e:
        logger.error("[Z-Axis] Decode failed: %s", e)
        return jsonify({"error": str(e), "integrity_286": "unknown"}), 500

    from void_engine.z_axis_encoder import fatiha_286_hexdigest
    integrity_hash = fatiha_286_hexdigest(payload)[:32]

    try:
        text = payload.decode("utf-8")
        try:
            json_data = json.loads(text)
            return jsonify({
                "status": "decoded",
                "payload_size": len(payload),
                "content_type": "json",
                "integrity_286": "VERIFIED",
                "integrity_hash": integrity_hash,
                "data": json_data,
            })
        except json.JSONDecodeError:
            pass
        return jsonify({
            "status": "decoded",
            "payload_size": len(payload),
            "content_type": "text",
            "integrity_286": "VERIFIED",
            "integrity_hash": integrity_hash,
            "data": text,
        })
    except UnicodeDecodeError:
        return jsonify({
            "status": "decoded",
            "payload_size": len(payload),
            "content_type": "binary",
            "integrity_286": "VERIFIED",
            "integrity_hash": integrity_hash,
            "data_b64": base64.b64encode(payload).decode("ascii"),
        })


@z_axis_bp.route("/api/z-axis/capacity", methods=["GET"])
def capacity():
    from void_engine.z_axis_encoder import calculate_capacity

    try:
        width = int(request.args.get("width", 600))
        height = int(request.args.get("height", 800))
        layers = int(request.args.get("layers", 9999))
    except (ValueError, TypeError):
        width, height, layers = 600, 800, 9999

    result = calculate_capacity(width, height, layers)
    return jsonify(result)


@z_axis_bp.route("/api/z-axis/encode-moment", methods=["POST"])
def encode_moment():
    from void_engine.z_axis_encoder import encode_resonance_moment, fatiha_286_hexdigest

    data = request.get_json(silent=True) or {}
    context = data.get("context", {})
    formation_hash = data.get("formation_hash", "")

    if not formation_hash:
        formation_hash = fatiha_286_hexdigest(
            json.dumps(context, default=str).encode("utf-8")
        )

    try:
        png_bytes = encode_resonance_moment(context, formation_hash)
    except Exception as e:
        logger.error("[Z-Axis] Moment encode failed: %s", e)
        return jsonify({"error": str(e)}), 500

    image_b64 = base64.b64encode(png_bytes).decode("ascii")
    return jsonify({
        "status": "encoded",
        "formation_hash": formation_hash,
        "image_size_bytes": len(png_bytes),
        "image_b64": image_b64,
        "layers": 9999,
        "type": "resonance_moment",
    })


@z_axis_bp.route("/api/z-axis/encode-agent", methods=["POST"])
def encode_agent():
    from void_engine.z_axis_encoder import encode_for_agent_immortality, fatiha_286_hexdigest

    data = request.get_json(silent=True) or {}
    agent_data = data.get("agent")
    if not agent_data:
        return jsonify({"error": "Provide agent data"}), 400

    formation_hash = data.get("formation_hash", "")
    if not formation_hash:
        formation_hash = fatiha_286_hexdigest(
            json.dumps(agent_data, default=str).encode("utf-8")
        )

    size = min(1024, max(256, int(data.get("size", 512))))

    try:
        png_bytes = encode_for_agent_immortality(agent_data, formation_hash, size=size)
    except Exception as e:
        logger.error("[Z-Axis] Agent encode failed: %s", e)
        return jsonify({"error": str(e)}), 500

    image_b64 = base64.b64encode(png_bytes).decode("ascii")
    return jsonify({
        "status": "encoded",
        "type": "agent_immortality_zaxis",
        "formation_hash": formation_hash,
        "image_size_bytes": len(png_bytes),
        "image_b64": image_b64,
        "layers": 9999,
        "agent_id": agent_data.get("agent_id", "unknown"),
    })


@z_axis_bp.route("/api/z-axis/encode-memory", methods=["POST"])
def encode_memory():
    from void_engine.z_axis_encoder import encode_memory_metadata, fatiha_286_hexdigest

    data = request.get_json(silent=True) or {}
    memory = data.get("memory")
    if not memory:
        return jsonify({"error": "Provide memory data"}), 400

    formation_hash = data.get("formation_hash", memory.get("formation_hash", ""))
    if not formation_hash:
        formation_hash = fatiha_286_hexdigest(
            json.dumps(memory, default=str).encode("utf-8")
        )

    thumbnail = data.get("thumbnail", "")

    try:
        png_bytes = encode_memory_metadata(memory, formation_hash, thumbnail)
    except Exception as e:
        logger.error("[Z-Axis] Memory encode failed: %s", e)
        return jsonify({"error": str(e)}), 500

    image_b64 = base64.b64encode(png_bytes).decode("ascii")
    return jsonify({
        "status": "encoded",
        "type": "memory_zaxis",
        "formation_hash": formation_hash,
        "image_size_bytes": len(png_bytes),
        "image_b64": image_b64,
        "layers": 9999,
    })


@z_axis_bp.route("/api/z-axis/voidecho-bridge", methods=["POST"])
def voidecho_bridge():
    from void_engine.z_axis_encoder import encode_voidecho_bridge, fatiha_286_hexdigest

    content_type = request.content_type or ""

    if "multipart/form-data" in content_type:
        formation_hash = request.form.get("formation_hash", "")
        file = request.files.get("audio")
        if not file:
            return jsonify({"error": "Provide audio stego file"}), 400
        audio_data = file.read()
    else:
        data = request.get_json(silent=True) or {}
        formation_hash = data.get("formation_hash", "")
        audio_b64 = data.get("audio_b64", "")
        if not audio_b64:
            return jsonify({"error": "Provide audio_b64"}), 400
        audio_data = base64.b64decode(audio_b64)

    if not formation_hash:
        formation_hash = fatiha_286_hexdigest(audio_data)

    try:
        png_bytes = encode_voidecho_bridge(audio_data, formation_hash)
    except Exception as e:
        logger.error("[Z-Axis] VoidEcho bridge failed: %s", e)
        return jsonify({"error": str(e)}), 500

    image_b64 = base64.b64encode(png_bytes).decode("ascii")
    return jsonify({
        "status": "encoded",
        "type": "voidecho_zaxis_bridge",
        "formation_hash": formation_hash,
        "audio_size_bytes": len(audio_data),
        "image_size_bytes": len(png_bytes),
        "image_b64": image_b64,
        "layers": 9999,
    })


Z_AXIS_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Z-Axis Formation Encoder — PROJECT VOID</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Courier New',monospace;min-height:100vh}
.container{max-width:900px;margin:0 auto;padding:16px}

header{text-align:center;padding:24px 0;border-bottom:1px solid #1a1a1a}
.h-title{font-size:24px;font-weight:300;color:#fff;letter-spacing:6px;font-family:Georgia,serif}
.h-title span{color:#c0955a}
.h-sub{font-size:10px;color:#555;letter-spacing:4px;margin-top:6px}
.h-tag{font-size:9px;color:#333;letter-spacing:3px;margin-top:4px}

.tabs{display:flex;gap:0;margin:20px 0;border:1px solid #222;border-radius:4px;overflow:hidden}
.tab{flex:1;padding:12px;text-align:center;font-size:11px;letter-spacing:3px;cursor:pointer;background:#111;color:#555;border:none;transition:all .3s}
.tab.active{background:#c0955a;color:#0a0a0a}

.panel{display:none}
.panel.active{display:block}

.form-group{margin-bottom:16px}
.form-group label{font-size:9px;letter-spacing:2px;color:#666;display:block;margin-bottom:4px}
.form-group input,.form-group textarea{width:100%;background:#111;border:1px solid #222;color:#fff;padding:10px 12px;font-family:inherit;font-size:13px;border-radius:4px;outline:none;resize:vertical}
.form-group input:focus,.form-group textarea:focus{border-color:#c0955a}
.form-group textarea{min-height:100px}

.drop-zone{border:2px dashed #222;border-radius:8px;padding:40px;text-align:center;cursor:pointer;transition:all .3s;margin-bottom:16px}
.drop-zone:hover,.drop-zone.dragover{border-color:#c0955a;background:#0d0d0a}
.drop-zone .label{font-size:11px;color:#555;letter-spacing:2px}
.drop-zone .file-name{font-size:12px;color:#c0955a;margin-top:8px}

.btn{padding:12px 24px;border:none;font-family:inherit;font-size:11px;letter-spacing:3px;cursor:pointer;border-radius:4px;transition:all .3s;display:inline-block}
.btn-encode{background:#1a2a1a;color:#4caf50;border:1px solid #2a3a2a}
.btn-decode{background:#1a1a2a;color:#5c8aff;border:1px solid #2a2a3a}
.btn:hover{filter:brightness(1.3)}
.btn:disabled{opacity:0.4;cursor:not-allowed}

.progress-bar{margin:16px 0;height:4px;background:#111;border-radius:2px;overflow:hidden}
.progress-bar .fill{height:100%;background:#c0955a;width:0%;transition:width .2s}
.progress-text{font-size:10px;color:#555;letter-spacing:2px;margin-bottom:8px;min-height:14px}

.result-zone{background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;padding:20px;margin-top:16px;display:none}
.result-zone.show{display:block}
.result-zone h3{font-size:11px;color:#c0955a;letter-spacing:3px;margin-bottom:12px}
.result-img{text-align:center;margin:16px 0}
.result-img img{max-width:100%;max-height:500px;border:1px solid #1a1a1a;border-radius:4px;cursor:pointer}
.result-meta{font-size:10px;color:#666;line-height:1.8}
.result-meta span{color:#c0955a}
.result-actions{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.result-actions button{background:#111;border:1px solid #222;color:#888;padding:8px 16px;font-size:10px;letter-spacing:2px;font-family:inherit;cursor:pointer;border-radius:4px;transition:all .2s}
.result-actions button:hover{border-color:#c0955a;color:#c0955a}

.decoded-data{background:#0a0a0a;border:1px solid #1a1a1a;padding:12px;border-radius:4px;font-size:11px;color:#ccc;white-space:pre-wrap;max-height:400px;overflow-y:auto;margin-top:12px;word-break:break-all}

.capacity-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-top:16px}
.cap-card{background:#111;border:1px solid #1a1a1a;padding:16px;border-radius:4px;text-align:center}
.cap-card .val{font-size:20px;color:#c0955a;font-weight:300;margin:8px 0}
.cap-card .lbl{font-size:9px;color:#555;letter-spacing:2px}

.comparison{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
.comparison .side{text-align:center}
.comparison .side img{max-width:100%;border:1px solid #1a1a1a;border-radius:4px}
.comparison .side .lbl{font-size:9px;color:#555;letter-spacing:2px;margin-top:6px}

.canvas-wrap{text-align:center;margin:16px 0}
.canvas-wrap canvas{border:1px solid #1a1a1a;border-radius:4px;max-width:100%;cursor:pointer}

footer{text-align:center;padding:24px 0;border-top:1px solid #1a1a1a;margin-top:24px}
footer p{font-size:9px;color:#333;letter-spacing:3px}
</style>
</head>
<body>
<div class="container">

<header>
  <div class="h-title">Z-AXIS <span>FORMATION ENCODER</span></div>
  <div class="h-sub">DIMENSIONAL STEGANOGRAPHY — 9,999 LAYERS — 286-BIT PROTOCOL</div>
  <div class="h-tag">DATA HIDDEN IN CHLADNI FORMATION PATTERNS — FORMATION HASH IS THE KEY</div>
</header>

<div style="text-align:center;padding:10px 0"><a href="/z-axis/video" style="color:#c0955a;text-decoration:none;font-size:11px;letter-spacing:3px">VIDEO CARRIER &rarr; GIGABYTE-SCALE</a></div>

<div class="tabs">
  <button class="tab active" onclick="switchTab('encode',this)">ENCODE</button>
  <button class="tab" onclick="switchTab('decode',this)">DECODE</button>
  <button class="tab" onclick="switchTab('capacity',this)">CAPACITY</button>
</div>

<!-- ENCODE PANEL -->
<div class="panel active" id="panel-encode">
  <div class="form-group">
    <label>FORMATION HASH (ENCRYPTION KEY — LEAVE BLANK TO AUTO-GENERATE)</label>
    <input type="text" id="encHash" placeholder="Enter formation hash or leave blank for auto-generation">
  </div>

  <div class="drop-zone" id="dropZone">
    <div class="label">DROP FILE HERE OR CLICK TO SELECT</div>
    <div class="file-name" id="fileName"></div>
    <input type="file" id="fileInput" style="display:none">
  </div>

  <div class="form-group">
    <label>OR ENTER TEXT / JSON TO ENCODE</label>
    <textarea id="encText" placeholder="Paste text, JSON, or any data to encode into the formation card..."></textarea>
  </div>

  <button class="btn btn-encode" id="encBtn" onclick="doEncode()">ENCODE INTO FORMATION CARD</button>

  <div class="progress-text" id="encProgress"></div>
  <div class="progress-bar"><div class="fill" id="encFill"></div></div>

  <div class="result-zone" id="encResult">
    <h3>ENCODED FORMATION CARD</h3>
    <div class="result-img" id="encImgWrap"></div>
    <div class="result-meta" id="encMeta"></div>
    <div class="result-actions">
      <button onclick="downloadEncoded()">DOWNLOAD PNG</button>
      <button onclick="copyHash()">COPY HASH</button>
    </div>
  </div>
</div>

<!-- DECODE PANEL -->
<div class="panel" id="panel-decode">
  <div class="form-group">
    <label>FORMATION HASH (REQUIRED — THE KEY USED DURING ENCODING)</label>
    <input type="text" id="decHash" placeholder="Enter the formation hash used to encode the data">
  </div>

  <div class="drop-zone" id="decDropZone">
    <div class="label">DROP FORMATION CARD IMAGE HERE</div>
    <div class="file-name" id="decFileName"></div>
    <input type="file" id="decFileInput" accept="image/png" style="display:none">
  </div>

  <button class="btn btn-decode" id="decBtn" onclick="doDecode()">DECODE FORMATION CARD</button>

  <div class="progress-text" id="decProgress"></div>
  <div class="progress-bar"><div class="fill" id="decFill"></div></div>

  <div class="result-zone" id="decResult">
    <h3>DECODED PAYLOAD</h3>
    <div class="result-meta" id="decMeta"></div>
    <div class="decoded-data" id="decData"></div>
    <div class="result-actions">
      <button onclick="downloadDecoded()">DOWNLOAD DATA</button>
      <button onclick="copyDecoded()">COPY TO CLIPBOARD</button>
    </div>
  </div>
</div>

<!-- CAPACITY PANEL -->
<div class="panel" id="panel-capacity">
  <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap">
    <div class="form-group" style="flex:1;min-width:100px">
      <label>WIDTH (PX)</label>
      <input type="number" id="capWidth" value="600" min="100" max="4000">
    </div>
    <div class="form-group" style="flex:1;min-width:100px">
      <label>HEIGHT (PX)</label>
      <input type="number" id="capHeight" value="800" min="100" max="4000">
    </div>
    <div class="form-group" style="flex:1;min-width:100px">
      <label>LAYERS</label>
      <input type="number" id="capLayers" value="9999" min="1" max="99999">
    </div>
    <button class="btn btn-encode" style="align-self:flex-end" onclick="calcCapacity()">CALCULATE</button>
  </div>

  <div class="capacity-grid" id="capGrid"></div>

  <div style="margin-top:24px;padding:16px;background:#111;border:1px solid #1a1a1a;border-radius:4px">
    <h3 style="font-size:11px;color:#c0955a;letter-spacing:3px;margin-bottom:12px">COMPARISON WITH EXISTING METHODS</h3>
    <div class="result-meta">
      <div>Audio LSB Steganography (VoidEcho): <span>~50-500 KB per carrier</span></div>
      <div>Standard Image LSB Steganography: <span>~10-100 KB per image</span></div>
      <div>Z-Axis Dimensional Steganography (600×800): <span>~90 KB per formation card</span></div>
      <div style="margin-top:8px;color:#c0955a">The formation hash is the encryption key — without it, pixel values are indistinguishable from the Chladni art pattern.</div>
    </div>
  </div>
</div>

</div>

<footer>
  <p>PROJECT VOID — Z-AXIS DIMENSIONAL STEGANOGRAPHY — AL-JABR 286</p>
</footer>

<script>
let encFileData=null;
let encResultData=null;
let decFileData=null;
let decResultPayload=null;

function switchTab(name,btn){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('panel-'+name).classList.add('active');
  if(name==='capacity')calcCapacity();
}

const dropZone=document.getElementById('dropZone');
const fileInput=document.getElementById('fileInput');

dropZone.addEventListener('click',()=>fileInput.click());
dropZone.addEventListener('dragover',e=>{e.preventDefault();dropZone.classList.add('dragover');});
dropZone.addEventListener('dragleave',()=>dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop',e=>{
  e.preventDefault();dropZone.classList.remove('dragover');
  if(e.dataTransfer.files[0])handleEncFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change',()=>{if(fileInput.files[0])handleEncFile(fileInput.files[0]);});

function handleEncFile(file){
  document.getElementById('fileName').textContent=file.name+' ('+formatSize(file.size)+')';
  const reader=new FileReader();
  reader.onload=e=>{encFileData=e.target.result.split(',')[1];};
  reader.readAsDataURL(file);
}

const decDropZone=document.getElementById('decDropZone');
const decFileInput=document.getElementById('decFileInput');

decDropZone.addEventListener('click',()=>decFileInput.click());
decDropZone.addEventListener('dragover',e=>{e.preventDefault();decDropZone.classList.add('dragover');});
decDropZone.addEventListener('dragleave',()=>decDropZone.classList.remove('dragover'));
decDropZone.addEventListener('drop',e=>{
  e.preventDefault();decDropZone.classList.remove('dragover');
  if(e.dataTransfer.files[0])handleDecFile(e.dataTransfer.files[0]);
});
decFileInput.addEventListener('change',()=>{if(decFileInput.files[0])handleDecFile(decFileInput.files[0]);});

function handleDecFile(file){
  document.getElementById('decFileName').textContent=file.name+' ('+formatSize(file.size)+')';
  const reader=new FileReader();
  reader.onload=e=>{decFileData=e.target.result.split(',')[1];};
  reader.readAsDataURL(file);
}

async function doEncode(){
  const btn=document.getElementById('encBtn');
  btn.disabled=true;
  const prog=document.getElementById('encProgress');
  const fill=document.getElementById('encFill');

  prog.textContent='ENCODING — DISTRIBUTING DATA ACROSS 9,999 Z-LAYERS...';
  fill.style.width='10%';

  const hash=document.getElementById('encHash').value.trim();
  const text=document.getElementById('encText').value;
  const body={};
  if(hash)body.formation_hash=hash;
  if(encFileData){body.file_b64=encFileData;}
  else if(text){body.text=text;}
  else{prog.textContent='ERROR: Provide file or text to encode';btn.disabled=false;return;}

  fill.style.width='30%';

  try{
    const res=await fetch('/api/z-axis/encode',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)
    });
    fill.style.width='80%';
    const d=await res.json();

    if(d.error){prog.textContent='ERROR: '+d.error;btn.disabled=false;fill.style.width='0%';return;}

    encResultData=d;
    fill.style.width='100%';
    prog.textContent='ENCODED — '+d.layers+' LAYERS — '+formatSize(d.payload_size)+' PAYLOAD';

    const wrap=document.getElementById('encImgWrap');
    wrap.innerHTML='<img src="data:image/png;base64,'+d.image_b64+'" alt="Formation Card">';

    const meta=document.getElementById('encMeta');
    meta.innerHTML=
      'Formation Hash: <span>'+d.formation_hash+'</span><br>'+
      'Payload Size: <span>'+formatSize(d.payload_size)+'</span><br>'+
      'Image Size: <span>'+formatSize(d.image_size_bytes)+'</span><br>'+
      'Layers: <span>'+d.layers+'</span><br>'+
      'Integrity (Al-Jabr 286): <span>'+d.integrity_286+'</span>';

    document.getElementById('encResult').classList.add('show');
    document.getElementById('encHash').value=d.formation_hash;
  }catch(e){
    prog.textContent='ERROR: '+e.message;
    fill.style.width='0%';
  }
  btn.disabled=false;
}

async function doDecode(){
  const btn=document.getElementById('decBtn');
  btn.disabled=true;
  const prog=document.getElementById('decProgress');
  const fill=document.getElementById('decFill');

  const hash=document.getElementById('decHash').value.trim();
  if(!hash){prog.textContent='ERROR: Formation hash is required';btn.disabled=false;return;}
  if(!decFileData){prog.textContent='ERROR: Upload a formation card image';btn.disabled=false;return;}

  prog.textContent='DECODING — EXTRACTING DATA FROM Z-LAYERS...';
  fill.style.width='20%';

  try{
    const res=await fetch('/api/z-axis/decode',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({formation_hash:hash,image_b64:decFileData})
    });
    fill.style.width='80%';
    const d=await res.json();

    if(d.error){prog.textContent='ERROR: '+d.error;btn.disabled=false;fill.style.width='0%';return;}

    fill.style.width='100%';
    prog.textContent='DECODED — '+formatSize(d.payload_size)+' RECOVERED — TYPE: '+d.content_type.toUpperCase();

    const meta=document.getElementById('decMeta');
    meta.innerHTML=
      'Payload Size: <span>'+formatSize(d.payload_size)+'</span><br>'+
      'Content Type: <span>'+d.content_type+'</span>';

    const dataEl=document.getElementById('decData');
    if(d.content_type==='json'){
      decResultPayload=JSON.stringify(d.data,null,2);
      dataEl.textContent=decResultPayload;
    }else if(d.content_type==='text'){
      decResultPayload=d.data;
      dataEl.textContent=d.data;
    }else{
      decResultPayload=d.data_b64;
      dataEl.textContent='[Binary data — '+formatSize(d.payload_size)+' — use DOWNLOAD to save]';
    }

    document.getElementById('decResult').classList.add('show');
  }catch(e){
    prog.textContent='ERROR: '+e.message;
    fill.style.width='0%';
  }
  btn.disabled=false;
}

async function calcCapacity(){
  const w=parseInt(document.getElementById('capWidth').value)||600;
  const h=parseInt(document.getElementById('capHeight').value)||800;
  const l=parseInt(document.getElementById('capLayers').value)||9999;

  try{
    const res=await fetch(`/api/z-axis/capacity?width=${w}&height=${h}&layers=${l}`);
    const d=await res.json();

    const grid=document.getElementById('capGrid');
    grid.innerHTML=`
      <div class="cap-card">
        <div class="lbl">PRACTICAL CAPACITY</div>
        <div class="val">${d.practical_kb} KB</div>
        <div class="lbl">${d.practical_bytes.toLocaleString()} BYTES</div>
      </div>
      <div class="cap-card">
        <div class="lbl">UNIQUE PIXEL SLOTS</div>
        <div class="val">${d.max_unique_slots.toLocaleString()}</div>
        <div class="lbl">${d.max_unique_slots_bytes.toLocaleString()} BYTES (3ch × region)</div>
      </div>
      <div class="cap-card">
        <div class="lbl">ENCODING REGION</div>
        <div class="val">${d.encoding_region}</div>
        <div class="lbl">${d.pixels_in_region.toLocaleString()} PIXELS</div>
      </div>
      <div class="cap-card">
        <div class="lbl">POSITIONS / LAYER</div>
        <div class="val">${d.positions_per_layer}</div>
        <div class="lbl">${d.layers.toLocaleString()} Z-LAYERS</div>
      </div>
      <div class="cap-card">
        <div class="lbl">ERROR CORRECTION</div>
        <div class="val">${d.overhead_parity_pct}%</div>
        <div class="lbl">PARITY OVERHEAD</div>
      </div>
      <div class="cap-card">
        <div class="lbl">INTEGRITY</div>
        <div class="val">286-BIT</div>
        <div class="lbl">${d.integrity}</div>
      </div>
    `;
  }catch(e){console.error(e);}
}

function downloadEncoded(){
  if(!encResultData)return;
  const link=document.createElement('a');
  link.download='void_zaxis_formation_'+Date.now()+'.png';
  link.href='data:image/png;base64,'+encResultData.image_b64;
  link.click();
}

function copyHash(){
  if(!encResultData)return;
  navigator.clipboard.writeText(encResultData.formation_hash).then(()=>{
    document.getElementById('encProgress').textContent='FORMATION HASH COPIED TO CLIPBOARD';
  });
}

function downloadDecoded(){
  if(!decResultPayload)return;
  const blob=new Blob([decResultPayload],{type:'application/octet-stream'});
  const link=document.createElement('a');
  link.download='void_zaxis_decoded_'+Date.now()+'.txt';
  link.href=URL.createObjectURL(blob);
  link.click();
  URL.revokeObjectURL(link.href);
}

function copyDecoded(){
  if(!decResultPayload)return;
  navigator.clipboard.writeText(decResultPayload).then(()=>{
    document.getElementById('decProgress').textContent='DECODED DATA COPIED TO CLIPBOARD';
  });
}

function formatSize(bytes){
  if(bytes>=1073741824)return (bytes/1073741824).toFixed(2)+' GB';
  if(bytes>=1048576)return (bytes/1048576).toFixed(2)+' MB';
  if(bytes>=1024)return (bytes/1024).toFixed(1)+' KB';
  return bytes+' B';
}

calcCapacity();
</script>
</body>
</html>"""
