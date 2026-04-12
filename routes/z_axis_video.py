"""
Z-Axis Video Carrier — Gigabyte-Scale Dimensional Steganography.

Routes:
    /z-axis/video                    (GET — encode/decode/capacity UI page)
    /api/z-axis/video/encode         (POST — encode data into video carrier)
    /api/z-axis/video/decode         (POST — decode data from video carrier)
    /api/z-axis/video/capacity       (GET — capacity calculator)
"""

import os
import io
import base64
import json
import time
import logging
import tempfile
from flask import Blueprint, request, jsonify, render_template_string, send_file, Response

logger = logging.getLogger(__name__)

z_axis_video_bp = Blueprint("z_axis_video", __name__)

_rate = {}
RATE_WINDOW = 30


def _rate_check(ip, window=RATE_WINDOW):
    now = time.time()
    if now - _rate.get(ip, 0) < window:
        return True
    _rate[ip] = now
    return False


@z_axis_video_bp.route("/z-axis/video")
def page():
    return render_template_string(Z_AXIS_VIDEO_TEMPLATE)


@z_axis_video_bp.route("/api/z-axis/video/capacity", methods=["GET"])
def capacity():
    from void_engine.z_axis_video import calculate_video_capacity

    resolution = request.args.get("resolution", "1080p")
    try:
        fps = int(request.args.get("fps", 30))
        duration = int(request.args.get("duration", 60))
    except (ValueError, TypeError):
        fps, duration = 30, 60

    fps = max(1, min(fps, 120))
    duration = max(1, min(duration, 3600))

    result = calculate_video_capacity(resolution, fps, duration)
    return jsonify(result)


@z_axis_video_bp.route("/api/z-axis/video/encode", methods=["POST"])
def encode_video():
    ip = request.remote_addr or "unknown"
    if _rate_check(ip):
        return jsonify({"error": "Rate limited — please wait before encoding again"}), 429

    from void_engine.z_axis_video import encode_to_video, calculate_video_capacity
    from void_engine.al_jabr_286 import fatiha_286_hexdigest

    formation_hash = request.form.get("formation_hash", "")
    resolution = request.form.get("resolution", "1080p")
    try:
        fps = int(request.form.get("fps", 30))
    except (ValueError, TypeError):
        fps = 30

    file = request.files.get("file")
    text = request.form.get("text", "")

    if file:
        payload = file.read()
    elif text:
        payload = text.encode("utf-8")
    else:
        return jsonify({"error": "Provide file or text to encode"}), 400

    MAX_DEMO_BYTES = 5 * 1024 * 1024
    if len(payload) > MAX_DEMO_BYTES:
        return jsonify({
            "error": f"Demo limit: {len(payload):,} bytes exceeds {MAX_DEMO_BYTES:,} byte limit. "
                     f"Use the Python API for larger payloads."
        }), 413

    if not formation_hash:
        formation_hash = fatiha_286_hexdigest(payload)

    try:
        output_path = encode_to_video(
            payload, formation_hash,
            resolution=resolution, fps=fps,
        )
    except Exception as e:
        logger.error("[Z-Video] Encode failed: %s", e)
        return jsonify({"error": str(e)}), 500

    video_size = os.path.getsize(output_path)
    integrity_hash = fatiha_286_hexdigest(payload)[:32]
    short_hash = formation_hash[:8]

    response = send_file(
        output_path,
        mimetype="video/x-matroska",
        as_attachment=True,
        download_name=f"z-axis-video-{short_hash}.mkv",
    )
    response.headers["X-Formation-Hash"] = formation_hash
    response.headers["X-Payload-Size"] = str(len(payload))
    response.headers["X-Video-Size"] = str(video_size)
    response.headers["X-Integrity-286"] = integrity_hash
    response.headers["X-Resolution"] = resolution
    response.headers["X-FPS"] = str(fps)

    @response.call_on_close
    def _cleanup():
        try:
            os.unlink(output_path)
        except Exception:
            pass

    return response


@z_axis_video_bp.route("/api/z-axis/video/decode", methods=["POST"])
def decode_video():
    ip = request.remote_addr or "unknown"
    if _rate_check(ip):
        return jsonify({"error": "Rate limited — please wait before decoding again"}), 429

    from void_engine.z_axis_video import decode_from_video
    from void_engine.al_jabr_286 import fatiha_286_hexdigest

    formation_hash = request.form.get("formation_hash", "")
    if not formation_hash:
        return jsonify({"error": "formation_hash is required for decoding"}), 400

    file = request.files.get("video")
    if not file:
        return jsonify({"error": "Provide video file"}), 400

    fd, tmp_path = tempfile.mkstemp(suffix=".mkv")
    try:
        os.close(fd)
        file.save(tmp_path)

        payload = decode_from_video(tmp_path, formation_hash)
    except ValueError as e:
        error_msg = str(e)
        is_integrity = "integrity" in error_msg.lower() or "checksum" in error_msg.lower()
        logger.error("[Z-Video] Decode failed: %s", e)
        return jsonify({
            "error": error_msg,
            "integrity_286": "FAILED" if is_integrity else "unknown",
        }), 422 if is_integrity else 500
    except Exception as e:
        logger.error("[Z-Video] Decode failed: %s", e)
        return jsonify({"error": str(e), "integrity_286": "unknown"}), 500
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

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


Z_AXIS_VIDEO_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Z-Axis Video Carrier — PROJECT VOID</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Courier New',monospace;min-height:100vh}
.container{max-width:960px;margin:0 auto;padding:16px}

header{text-align:center;padding:24px 0;border-bottom:1px solid #1a1a1a}
.h-title{font-size:22px;font-weight:300;color:#fff;letter-spacing:5px;font-family:Georgia,serif}
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
.form-group input,.form-group textarea,.form-group select{width:100%;background:#111;border:1px solid #222;color:#fff;padding:10px 12px;font-family:inherit;font-size:13px;border-radius:4px;outline:none;resize:vertical}
.form-group input:focus,.form-group textarea:focus,.form-group select:focus{border-color:#c0955a}
.form-group textarea{min-height:80px}
.form-group select option{background:#111;color:#fff}

.row{display:flex;gap:12px;flex-wrap:wrap}
.row .form-group{flex:1;min-width:120px}

.drop-zone{border:2px dashed #222;border-radius:8px;padding:40px;text-align:center;cursor:pointer;transition:all .3s;margin-bottom:16px}
.drop-zone:hover,.drop-zone.dragover{border-color:#c0955a;background:#0d0d0a}
.drop-zone .label{font-size:11px;color:#555;letter-spacing:2px}
.drop-zone .file-name{font-size:12px;color:#c0955a;margin-top:8px}

.btn{padding:12px 24px;border:none;font-family:inherit;font-size:11px;letter-spacing:3px;cursor:pointer;border-radius:4px;transition:all .3s;display:inline-block}
.btn-encode{background:#1a2a1a;color:#4caf50;border:1px solid #2a3a2a}
.btn-decode{background:#1a1a2a;color:#5c8aff;border:1px solid #2a2a3a}
.btn-calc{background:#2a1a1a;color:#c0955a;border:1px solid #3a2a1a}
.btn:hover{filter:brightness(1.3)}
.btn:disabled{opacity:0.4;cursor:not-allowed}

.progress-text{font-size:10px;color:#555;letter-spacing:2px;margin:8px 0;min-height:14px}
.progress-bar{margin:8px 0;height:4px;background:#111;border-radius:2px;overflow:hidden}
.progress-bar .fill{height:100%;background:#c0955a;width:0%;transition:width .3s}

.result-zone{background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;padding:20px;margin-top:16px;display:none}
.result-zone.show{display:block}
.result-zone h3{font-size:11px;color:#c0955a;letter-spacing:3px;margin-bottom:12px}
.result-meta{font-size:10px;color:#666;line-height:1.8}
.result-meta span{color:#c0955a}
.result-actions{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.result-actions button{background:#111;border:1px solid #222;color:#888;padding:8px 16px;font-size:10px;letter-spacing:2px;font-family:inherit;cursor:pointer;border-radius:4px;transition:all .2s}
.result-actions button:hover{border-color:#c0955a;color:#c0955a}

.decoded-data{background:#0a0a0a;border:1px solid #1a1a1a;padding:12px;border-radius:4px;font-size:11px;color:#ccc;white-space:pre-wrap;max-height:400px;overflow-y:auto;margin-top:12px;word-break:break-all}

.cap-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-top:16px}
.cap-card{background:#111;border:1px solid #1a1a1a;padding:16px;border-radius:4px;text-align:center}
.cap-card .val{font-size:20px;color:#c0955a;font-weight:300;margin:8px 0}
.cap-card .lbl{font-size:9px;color:#555;letter-spacing:2px}

.cap-table{width:100%;border-collapse:collapse;margin-top:16px;font-size:11px}
.cap-table th{text-align:left;color:#c0955a;padding:8px;border-bottom:1px solid #222;letter-spacing:2px;font-size:9px}
.cap-table td{padding:8px;border-bottom:1px solid #111;color:#aaa}
.cap-table tr:hover td{color:#fff}

.link-row{text-align:center;margin:20px 0}
.link-row a{color:#555;font-size:10px;letter-spacing:3px;text-decoration:none;border-bottom:1px solid #222;padding-bottom:2px;transition:all .3s}
.link-row a:hover{color:#c0955a;border-color:#c0955a}

footer{text-align:center;padding:24px 0;border-top:1px solid #1a1a1a;margin-top:24px}
footer p{font-size:9px;color:#333;letter-spacing:3px}
</style>
</head>
<body>
<div class="container">

<header>
  <div class="h-title">Z-AXIS <span>VIDEO CARRIER</span></div>
  <div class="h-sub">GIGABYTE-SCALE DIMENSIONAL STEGANOGRAPHY</div>
  <div class="h-tag">HIDE MOVIES, BOOKS, DATABASES INSIDE NORMAL-LOOKING VIDEOS</div>
</header>

<div class="link-row"><a href="/z-axis">&larr; IMAGE ENCODER</a></div>

<div class="tabs">
  <button class="tab active" onclick="switchTab('encode',this)">ENCODE</button>
  <button class="tab" onclick="switchTab('decode',this)">DECODE</button>
  <button class="tab" onclick="switchTab('capacity',this)">CAPACITY</button>
</div>

<!-- ENCODE -->
<div class="panel active" id="panel-encode">
  <div class="form-group">
    <label>FORMATION HASH (ENCRYPTION KEY — LEAVE BLANK TO AUTO-GENERATE)</label>
    <input type="text" id="encHash" placeholder="Enter formation hash or leave blank">
  </div>

  <div class="row">
    <div class="form-group">
      <label>RESOLUTION</label>
      <select id="encRes">
        <option value="480p">480p (854×480)</option>
        <option value="720p">720p (1280×720)</option>
        <option value="1080p" selected>1080p (1920×1080)</option>
        <option value="2k">2K (2560×1440)</option>
        <option value="4k">4K (3840×2160)</option>
      </select>
    </div>
    <div class="form-group">
      <label>FPS</label>
      <input type="number" id="encFps" value="30" min="1" max="120">
    </div>
  </div>

  <div class="drop-zone" id="encDropZone">
    <div class="label">DROP FILE HERE OR CLICK TO SELECT</div>
    <div class="file-name" id="encFileName"></div>
    <input type="file" id="encFileInput" style="display:none">
  </div>

  <div class="form-group">
    <label>OR ENTER TEXT TO ENCODE</label>
    <textarea id="encText" placeholder="Paste text to encode into the video carrier..."></textarea>
  </div>

  <button class="btn btn-encode" id="encBtn" onclick="doEncode()">ENCODE INTO VIDEO</button>

  <div class="progress-text" id="encProgress"></div>
  <div class="progress-bar"><div class="fill" id="encFill"></div></div>

  <div class="result-zone" id="encResult">
    <h3>ENCODED VIDEO</h3>
    <div id="encVideoWrap" style="text-align:center;margin:16px 0"></div>
    <div class="result-meta" id="encMeta"></div>
    <div class="result-actions">
      <button onclick="downloadEncoded()">DOWNLOAD VIDEO</button>
      <button onclick="copyHash()">COPY HASH</button>
    </div>
  </div>
</div>

<!-- DECODE -->
<div class="panel" id="panel-decode">
  <div class="form-group">
    <label>FORMATION HASH (REQUIRED — THE KEY USED DURING ENCODING)</label>
    <input type="text" id="decHash" placeholder="Enter the formation hash used to encode">
  </div>

  <div class="drop-zone" id="decDropZone">
    <div class="label">DROP ENCODED VIDEO HERE</div>
    <div class="file-name" id="decFileName"></div>
    <input type="file" id="decFileInput" accept="video/*" style="display:none">
  </div>

  <button class="btn btn-decode" id="decBtn" onclick="doDecode()">DECODE VIDEO</button>

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

<!-- CAPACITY -->
<div class="panel" id="panel-capacity">
  <div class="row">
    <div class="form-group">
      <label>RESOLUTION</label>
      <select id="capRes">
        <option value="480p">480p</option>
        <option value="720p">720p</option>
        <option value="1080p" selected>1080p</option>
        <option value="2k">2K</option>
        <option value="4k">4K</option>
      </select>
    </div>
    <div class="form-group">
      <label>FPS</label>
      <input type="number" id="capFps" value="30" min="1" max="120">
    </div>
    <div class="form-group">
      <label>DURATION (SEC)</label>
      <input type="number" id="capDur" value="60" min="1" max="3600">
    </div>
    <div style="display:flex;align-items:flex-end">
      <button class="btn btn-calc" onclick="calcCapacity()">CALCULATE</button>
    </div>
  </div>

  <div class="cap-grid" id="capGrid"></div>

  <h3 style="font-size:11px;color:#c0955a;letter-spacing:3px;margin:24px 0 12px">REFERENCE TABLE</h3>
  <table class="cap-table">
    <thead>
      <tr><th>CARRIER</th><th>DURATION</th><th>CAPACITY</th></tr>
    </thead>
    <tbody id="capTableBody"></tbody>
  </table>

  <div style="margin-top:24px;padding:16px;background:#111;border:1px solid #1a1a1a;border-radius:4px">
    <h3 style="font-size:11px;color:#c0955a;letter-spacing:3px;margin-bottom:12px">COMPARISON</h3>
    <div class="result-meta">
      <div>Audio LSB Stega (5s clip): <span>~54 KB</span></div>
      <div>Z-Axis Image Card (600×800): <span>~85 KB</span></div>
      <div>Z-Axis Video (1min 1080p): <span>~1.3 GB</span></div>
      <div>Z-Axis Video (5min 4K): <span>~26 GB</span></div>
      <div style="margin-top:8px;color:#c0955a">VIDEO CARRIER = 15,000x MORE CAPACITY THAN IMAGE CARD</div>
    </div>
  </div>
</div>

<footer>
  <p>Z-AXIS VIDEO CARRIER — PROJECT VOID — AL-JABR 286 — BISMILLAHIRRAHMANIRRAHIM</p>
</footer>

</div>

<script>
let encFile=null, decFile=null, lastEncBlob=null, lastEncHash='', lastDecPayload='', lastDecType='';

function switchTab(name,el){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('panel-'+name).classList.add('active');
  if(name==='capacity')calcCapacity();
}

const encDZ=document.getElementById('encDropZone');
const encFI=document.getElementById('encFileInput');
encDZ.addEventListener('click',()=>encFI.click());
encDZ.addEventListener('dragover',e=>{e.preventDefault();encDZ.classList.add('dragover')});
encDZ.addEventListener('dragleave',()=>encDZ.classList.remove('dragover'));
encDZ.addEventListener('drop',e=>{e.preventDefault();encDZ.classList.remove('dragover');if(e.dataTransfer.files.length){encFile=e.dataTransfer.files[0];document.getElementById('encFileName').textContent=encFile.name+' ('+fmt(encFile.size)+')'}});
encFI.addEventListener('change',()=>{if(encFI.files.length){encFile=encFI.files[0];document.getElementById('encFileName').textContent=encFile.name+' ('+fmt(encFile.size)+')'}});

const decDZ=document.getElementById('decDropZone');
const decFI=document.getElementById('decFileInput');
decDZ.addEventListener('click',()=>decFI.click());
decDZ.addEventListener('dragover',e=>{e.preventDefault();decDZ.classList.add('dragover')});
decDZ.addEventListener('dragleave',()=>decDZ.classList.remove('dragover'));
decDZ.addEventListener('drop',e=>{e.preventDefault();decDZ.classList.remove('dragover');if(e.dataTransfer.files.length){decFile=e.dataTransfer.files[0];document.getElementById('decFileName').textContent=decFile.name+' ('+fmt(decFile.size)+')'}});
decFI.addEventListener('change',()=>{if(decFI.files.length){decFile=decFI.files[0];document.getElementById('decFileName').textContent=decFile.name+' ('+fmt(decFile.size)+')'}});

function fmt(b){
  if(b>=1073741824)return (b/1073741824).toFixed(2)+' GB';
  if(b>=1048576)return (b/1048576).toFixed(2)+' MB';
  if(b>=1024)return (b/1024).toFixed(1)+' KB';
  return b+' B';
}

async function doEncode(){
  const btn=document.getElementById('encBtn');
  const prog=document.getElementById('encProgress');
  const fill=document.getElementById('encFill');
  const result=document.getElementById('encResult');
  const text=document.getElementById('encText').value.trim();

  if(!encFile && !text){prog.textContent='ERROR: Provide a file or text';return}

  btn.disabled=true;
  prog.textContent='ENCODING — generating Chladni carrier video + embedding payload...';
  fill.style.width='20%';
  result.classList.remove('show');

  const fd=new FormData();
  fd.append('formation_hash',document.getElementById('encHash').value.trim());
  fd.append('resolution',document.getElementById('encRes').value);
  fd.append('fps',document.getElementById('encFps').value);
  if(encFile)fd.append('file',encFile);
  else fd.append('text',text);

  try{
    fill.style.width='40%';
    const res=await fetch('/api/z-axis/video/encode',{method:'POST',body:fd});
    fill.style.width='80%';

    if(!res.ok){
      let errMsg='Encode failed';
      try{const d=await res.json();errMsg=d.error||errMsg;}catch(e){}
      prog.textContent='ERROR: '+errMsg;btn.disabled=false;fill.style.width='0%';return;
    }

    const blob=await res.blob();
    lastEncBlob=blob;
    lastEncHash=res.headers.get('X-Formation-Hash')||document.getElementById('encHash').value.trim();
    const payloadSize=res.headers.get('X-Payload-Size')||'?';
    const videoSize=res.headers.get('X-Video-Size')||blob.size;
    const integrity=res.headers.get('X-Integrity-286')||'';
    const resolution=res.headers.get('X-Resolution')||'';

    const wrap=document.getElementById('encVideoWrap');
    wrap.innerHTML='<div style="padding:16px;text-align:center;color:#555;font-size:11px">MKV/FFV1 lossless video — browser preview not available<br>Use DOWNLOAD to save the encoded video</div>';

    document.getElementById('encMeta').innerHTML=
      '<div>Formation Hash: <span>'+lastEncHash+'</span></div>'+
      '<div>Payload Size: <span>'+fmt(parseInt(payloadSize))+'</span></div>'+
      '<div>Video Size: <span>'+fmt(parseInt(videoSize))+'</span></div>'+
      '<div>Resolution: <span>'+resolution+'</span></div>'+
      '<div>Integrity 286: <span>'+integrity+'</span></div>';

    result.classList.add('show');
    fill.style.width='100%';
    prog.textContent='ENCODED SUCCESSFULLY — '+fmt(parseInt(payloadSize))+' hidden in '+fmt(parseInt(videoSize))+' video';
  }catch(e){
    prog.textContent='ERROR: '+e.message;
    fill.style.width='0%';
  }
  btn.disabled=false;
}

async function doDecode(){
  const btn=document.getElementById('decBtn');
  const prog=document.getElementById('decProgress');
  const fill=document.getElementById('decFill');
  const result=document.getElementById('decResult');
  const hash=document.getElementById('decHash').value.trim();

  if(!decFile){prog.textContent='ERROR: Provide an encoded video';return}
  if(!hash){prog.textContent='ERROR: Formation hash is required';return}

  btn.disabled=true;
  prog.textContent='DECODING — extracting payload from video frames...';
  fill.style.width='20%';
  result.classList.remove('show');

  const fd=new FormData();
  fd.append('formation_hash',hash);
  fd.append('video',decFile);

  try{
    fill.style.width='40%';
    const res=await fetch('/api/z-axis/video/decode',{method:'POST',body:fd});
    fill.style.width='80%';
    const d=await res.json();
    if(!res.ok){prog.textContent='ERROR: '+d.error;btn.disabled=false;fill.style.width='0%';return}

    lastDecType=d.content_type;
    const dataEl=document.getElementById('decData');
    if(d.content_type==='json'){
      lastDecPayload=JSON.stringify(d.data,null,2);
      dataEl.textContent=lastDecPayload;
    }else if(d.content_type==='text'){
      lastDecPayload=d.data;
      dataEl.textContent=d.data;
    }else{
      lastDecPayload=d.data_b64;
      dataEl.textContent='[Binary data — '+fmt(d.payload_size)+' — use DOWNLOAD]';
    }

    document.getElementById('decMeta').innerHTML=
      '<div>Payload Size: <span>'+fmt(d.payload_size)+'</span></div>'+
      '<div>Content Type: <span>'+d.content_type+'</span></div>'+
      '<div>Integrity 286: <span style="color:'+(d.integrity_286==='VERIFIED'?'#4caf50':'#f44336')+'">'+d.integrity_286+'</span></div>'+
      '<div>Integrity Hash: <span>'+d.integrity_hash+'</span></div>';

    result.classList.add('show');
    fill.style.width='100%';
    prog.textContent='DECODED — '+fmt(d.payload_size)+' extracted — Al-Jabr 286: '+d.integrity_286;
  }catch(e){
    prog.textContent='ERROR: '+e.message;
    fill.style.width='0%';
  }
  btn.disabled=false;
}

function downloadEncoded(){
  if(!lastEncBlob)return;
  const url=URL.createObjectURL(lastEncBlob);
  const a=document.createElement('a');
  a.href=url;
  a.download='z-axis-video-'+lastEncHash.substring(0,8)+'.mkv';
  a.click();
  setTimeout(()=>URL.revokeObjectURL(url),5000);
}

function copyHash(){
  if(lastEncHash)navigator.clipboard.writeText(lastEncHash);
}

function downloadDecoded(){
  if(!lastDecPayload)return;
  let blob;
  if(lastDecType==='binary'){
    const raw=atob(lastDecPayload);
    const arr=new Uint8Array(raw.length);
    for(let i=0;i<raw.length;i++)arr[i]=raw.charCodeAt(i);
    blob=new Blob([arr],{type:'application/octet-stream'});
  }else{
    blob=new Blob([lastDecPayload],{type:'text/plain'});
  }
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='z-axis-decoded'+(lastDecType==='json'?'.json':lastDecType==='text'?'.txt':'.bin');
  a.click();
}

function copyDecoded(){
  if(lastDecPayload)navigator.clipboard.writeText(lastDecPayload);
}

async function calcCapacity(){
  const res=document.getElementById('capRes').value;
  const fps=document.getElementById('capFps').value;
  const dur=document.getElementById('capDur').value;
  const r=await fetch(`/api/z-axis/video/capacity?resolution=${res}&fps=${fps}&duration=${dur}`);
  const d=await r.json();
  const grid=document.getElementById('capGrid');
  grid.innerHTML=
    '<div class="cap-card"><div class="lbl">RESOLUTION</div><div class="val">'+d.width+'×'+d.height+'</div></div>'+
    '<div class="cap-card"><div class="lbl">TOTAL FRAMES</div><div class="val">'+d.total_frames.toLocaleString()+'</div></div>'+
    '<div class="cap-card"><div class="lbl">BITS PER FRAME</div><div class="val">'+d.bits_per_frame.toLocaleString()+'</div></div>'+
    '<div class="cap-card"><div class="lbl">PRACTICAL CAPACITY</div><div class="val">'+(d.practical_gb>=1?d.practical_gb+' GB':d.practical_mb+' MB')+'</div></div>'+
    '<div class="cap-card"><div class="lbl">ENCRYPTION</div><div class="val" style="font-size:12px">ChaCha20</div></div>'+
    '<div class="cap-card"><div class="lbl">INTEGRITY</div><div class="val" style="font-size:12px">Al-Jabr 286</div></div>';

  const refs=[
    ['480p','10s',10],['480p','30s',30],['480p','1min',60],['480p','5min',300],
    ['720p','10s',10],['720p','30s',30],['720p','1min',60],['720p','5min',300],
    ['1080p','10s',10],['1080p','30s',30],['1080p','1min',60],['1080p','5min',300],['1080p','10min',600],
    ['4k','10s',10],['4k','30s',30],['4k','1min',60],['4k','5min',300],['4k','10min',600],
  ];
  const tbody=document.getElementById('capTableBody');
  tbody.innerHTML='';
  for(const [r2,label,sec] of refs){
    const cr=await fetch(`/api/z-axis/video/capacity?resolution=${r2}&fps=30&duration=${sec}`);
    const cd=await cr.json();
    const cap=cd.practical_gb>=1?cd.practical_gb.toFixed(2)+' GB':cd.practical_mb.toFixed(1)+' MB';
    tbody.innerHTML+='<tr><td>'+r2.toUpperCase()+' 30fps</td><td>'+label+'</td><td>'+cap+'</td></tr>';
  }
}
</script>
</body>
</html>"""
