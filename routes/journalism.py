import os
import uuid
import wave
import math
import hashlib as _hl
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from void_engine.compressor import compress_file, decompress_data
from void_engine.stega import encode, decode, encode_stereo, decode_stereo
from void_engine.calculator import analyze_carrier
from generate_carriers import generate_custom_carrier, ALL_STYLES
from routes.auth import login_required, tier_required

import routes.shared as shared

journalism_bp = Blueprint("journalism", __name__)


@journalism_bp.route("/api/journalism/encode", methods=["POST"])
@login_required
@tier_required("journalist")
def journalism_encode():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"error": "Empty filename"}), 400

    style = request.form.get("style", "biophony_mesh")
    if style not in ALL_STYLES:
        style = "biophony_mesh"

    safe_name = secure_filename(uploaded.filename)
    payload_path = os.path.join(shared.INPUT_DIR, safe_name)
    uploaded.save(payload_path)

    try:
        payload_size = os.path.getsize(payload_path)
        if payload_size > 50 * 1024 * 1024:
            os.remove(payload_path)
            return jsonify({"error": "File exceeds 50 MB limit"}), 400

        compressed, name, ext, orig_size = compress_file(payload_path, low_power=shared.low_power_mode)
        compressed_size = len(compressed)

        sample_rate = 44100
        is_stereo = style in ("midnight_pond", "biophony_mesh", "stereo_pocket")
        channels = 2 if is_stereo else 1
        bits_needed = (compressed_size + 64) * 8
        samples_needed = bits_needed
        seconds_needed = samples_needed / (sample_rate * channels)
        duration_minutes = max(1, math.ceil((seconds_needed * 2.5) / 60))
        duration_minutes = min(duration_minutes, 300)

        carrier_result = generate_custom_carrier(duration_minutes, style)
        carrier_path = carrier_result["path"]

        drop_id = uuid.uuid4().hex[:8]
        output_name = f"silt_{drop_id}_{safe_name.rsplit('.', 1)[0]}.wav"
        output_path = os.path.join(shared.SILT_DIR, output_name)

        with wave.open(carrier_path, "rb") as wf:
            n_channels = wf.getnchannels()

        if n_channels == 2:
            hash_key = encode_stereo(carrier_path, compressed, name, ext, output_path, 2, jitter=False, vortex=True, chirp_sync=False)
        else:
            hash_key = encode(carrier_path, compressed, name, ext, output_path, 2, jitter=False, vortex=True, chirp_sync=False)

        if os.path.exists(carrier_path):
            os.remove(carrier_path)

        shared._log_operation("SILT_JOURNALISM", output_name, hash_key, f"style={style}")

        return jsonify({
            "success": True,
            "hash_key": hash_key,
            "output_file": output_name,
            "output_size": os.path.getsize(output_path),
            "original_size": orig_size,
            "compressed_size": compressed_size,
            "carrier_style": style,
            "carrier_duration_min": duration_minutes,
            "scatter_mode": "vortex",
            "lsb_depth": 2,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Encoding failed — file may be too large for carrier capacity"}), 400


@journalism_bp.route("/api/journalism/decode", methods=["POST"])
@login_required
def journalism_decode():
    data = request.json
    filename = data.get("filename", "")
    hash_key = data.get("hash_key", "")

    if not filename or not hash_key:
        return jsonify({"error": "filename and hash_key are required"}), 400

    silt_path = os.path.join(shared.SILT_DIR, secure_filename(filename))
    if not os.path.exists(silt_path):
        return jsonify({"error": f"Silt drop not found: {filename}"}), 404

    try:
        with wave.open(silt_path, "rb") as wf:
            n_channels = wf.getnchannels()

        if n_channels == 2:
            compressed_data, name_ext, checksum = decode_stereo(silt_path, hash_key, 2)
        else:
            compressed_data, name_ext, checksum = decode(silt_path, hash_key, 2)

        original_data = decompress_data(compressed_data)

        computed_md5 = _hl.md5(compressed_data).hexdigest()
        if computed_md5 != checksum:
            return jsonify({"error": "Data integrity check failed — checksum mismatch"}), 400

        safe_out = secure_filename(name_ext)
        if not safe_out:
            safe_out = f"silt_decoded_{uuid.uuid4().hex[:6]}.bin"
        out_path = os.path.join(shared.OUTPUT_DIR, safe_out)
        with open(out_path, "wb") as f:
            f.write(original_data)

        return jsonify({
            "success": True,
            "filename": safe_out,
            "size": len(original_data),
            "download_url": f"/api/download/output_audio/{safe_out}",
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Decoding failed — invalid key or corrupted silt drop"}), 400


@journalism_bp.route("/api/journalism/drops")
@login_required
def journalism_drops():
    drops = []
    if os.path.isdir(shared.SILT_DIR):
        for f in sorted(os.listdir(shared.SILT_DIR)):
            fp = os.path.join(shared.SILT_DIR, f)
            if os.path.isfile(fp):
                stat = os.stat(fp)
                drops.append({
                    "name": f,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
    return jsonify({"drops": drops})


@journalism_bp.route("/api/journalism/download/<filename>")
@login_required
def journalism_download(filename):
    safe = secure_filename(filename)
    path = os.path.join(shared.SILT_DIR, safe)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True)


@journalism_bp.route("/api/journalism/delete/<filename>", methods=["DELETE"])
@login_required
def journalism_delete(filename):
    safe = secure_filename(filename)
    path = os.path.join(shared.SILT_DIR, safe)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"success": True, "deleted": safe})
    return jsonify({"error": "File not found"}), 404


@journalism_bp.route("/api/journalism/purge", methods=["DELETE"])
@login_required
def journalism_purge():
    count = 0
    if os.path.isdir(shared.SILT_DIR):
        for f in os.listdir(shared.SILT_DIR):
            fp = os.path.join(shared.SILT_DIR, f)
            if os.path.isfile(fp):
                os.remove(fp)
                count += 1
    return jsonify({"success": True, "purged": count})
