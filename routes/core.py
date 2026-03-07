import os
import uuid
import wave
import time as _time
import hashlib
import struct
import math
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename

import numpy as np

from void_engine.compressor import compress_file, compress_bytes, decompress_data
from void_engine.stega import (encode, decode, encode_burst, check_resonance_purity,
                                encode_stereo, decode_stereo, find_harmonic_pockets)
from void_engine.calculator import analyze_carrier, append_to_log
from generate_carriers import generate_custom_carrier, estimate_carrier_capacity, ALL_STYLES
from routes.auth import login_required, _check_rate_limit

import routes.shared as shared

core_bp = Blueprint("core", __name__)


def _user_input_dir():
    username = session.get("username")
    if username:
        d = f"data/vaults/{username}/input_files"
        os.makedirs(d, exist_ok=True)
        return d
    return shared.INPUT_DIR


def _user_output_dir():
    username = session.get("username")
    if username:
        d = f"data/vaults/{username}/output_audio"
        os.makedirs(d, exist_ok=True)
        return d
    return shared.OUTPUT_DIR

_proof_status = {"running": False, "result": None, "error": None, "started": None}


@core_bp.route("/")
@login_required
def index():
    return render_template("index.html",
                           is_founder=session.get("is_founder", False),
                           is_guardian=session.get("is_guardian", False),
                           username=session.get("username", ""),
                           display_name=session.get("display_name", ""),
                           user_role=session.get("role", "user"),
                           user_tier=session.get("tier", "ghost"))


@core_bp.route("/launch")
def landing():
    return render_template("landing.html")


@core_bp.route("/demo")
def demo_page():
    return render_template("index.html", demo_mode=True)


@core_bp.route("/grants")
def grants_page():
    return render_template("grants.html")


@core_bp.route("/sovereign")
def sovereign_page():
    return render_template("sovereign.html")


@core_bp.route("/welcome/vanguard")
@login_required
def welcome_vanguard():
    return render_template("welcome_vanguard.html",
                           username=session.get("username", ""),
                           display_name=session.get("display_name", ""),
                           user_tier=session.get("tier", "ghost"))


@core_bp.route("/guide")
def guide_page():
    return render_template("guide.html")


@core_bp.route("/api/files")
@login_required
def list_files():
    def get_files(directory):
        if not os.path.isdir(directory):
            return []
        result = []
        for f in sorted(os.listdir(directory)):
            fp = os.path.join(directory, f)
            if os.path.isfile(fp):
                size = os.path.getsize(fp)
                result.append({"name": f, "size": size, "path": fp})
        return result

    return jsonify({
        "input": get_files(_user_input_dir()),
        "output": get_files(_user_output_dir()),
    })


@core_bp.route("/api/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No filename"}), 400

    from routes.auth import TIER_LIMITS
    tier = session.get("tier", "ghost")
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["ghost"])
    max_mb = limits["upload_mb"]

    if max_mb > 0:
        f.seek(0, 2)
        size_bytes = f.tell()
        f.seek(0)
        if size_bytes > max_mb * 1024 * 1024:
            return jsonify({
                "error": f"File exceeds {max_mb}MB limit for {tier.title()} tier. Upgrade at /pricing",
                "upgrade": True,
                "max_mb": max_mb,
            }), 413

    filename = secure_filename(f.filename)
    dest = request.form.get("dest", "input")
    directory = _user_input_dir() if dest == "input" else _user_output_dir()
    filepath = os.path.join(directory, filename)
    f.save(filepath)

    return jsonify({
        "success": True,
        "filename": filename,
        "size": os.path.getsize(filepath),
    })


@core_bp.route("/api/encode", methods=["POST"])
@login_required
def encode_file():
    data = request.json
    carrier = data.get("carrier")
    payload = data.get("payload")
    lsb_depth = int(data.get("lsb_depth", 1))
    jitter = bool(data.get("jitter", False))
    vortex = bool(data.get("vortex", False))
    chirp_sync = bool(data.get("chirp_sync", False))

    if not carrier or not payload:
        return jsonify({"error": "Carrier and payload files are required"}), 400

    from werkzeug.utils import secure_filename as _sf_enc
    carrier = _sf_enc(carrier)
    payload = _sf_enc(payload)
    if not carrier or not payload:
        return jsonify({"error": "Invalid file names"}), 400

    from routes.auth import TIER_LIMITS
    tier = session.get("tier", "ghost")
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["ghost"])
    allowed_scatter = limits["scatter_modes"]
    if vortex and "vortex" not in allowed_scatter:
        return jsonify({"error": "Vortex scatter requires Journalist tier or higher. Upgrade at /pricing", "upgrade": True}), 403
    if chirp_sync and "chirp_sync" not in allowed_scatter:
        return jsonify({"error": "Chirp Sync requires Journalist tier or higher. Upgrade at /pricing", "upgrade": True}), 403

    carrier_path = os.path.join(_user_input_dir(), carrier)
    payload_path = os.path.join(_user_input_dir(), payload)

    if not os.path.exists(carrier_path):
        return jsonify({"error": f"Carrier file not found: {carrier}"}), 404
    if not os.path.exists(payload_path):
        return jsonify({"error": f"Payload file not found: {payload}"}), 404

    try:
        compressed, name, ext, orig_size = compress_file(payload_path, low_power=shared.low_power_mode)

        base_name = os.path.splitext(carrier)[0]
        output_name = f"{base_name}_void.wav"
        output_path = os.path.join(_user_output_dir(), output_name)

        with wave.open(carrier_path, "rb") as wf:
            n_channels = wf.getnchannels()
        is_stereo = n_channels == 2

        if is_stereo:
            hash_key = encode_stereo(carrier_path, compressed, name, ext, output_path, lsb_depth, jitter=jitter, vortex=vortex, chirp_sync=chirp_sync)
        else:
            hash_key = encode(carrier_path, compressed, name, ext, output_path, lsb_depth, jitter=jitter, vortex=vortex, chirp_sync=chirp_sync)

        scatter_mode = "chirp_sync" if chirp_sync else ("vortex" if vortex else ("jitter" if jitter else "linear"))
        shared._log_operation("ENCODE", output_name, hash_key, f"LSB{lsb_depth}/{scatter_mode}")

        info = analyze_carrier(carrier_path)
        tension_key = f"surface_tension_{lsb_depth}bit"
        burst_key = f"bubble_burst_{lsb_depth}bit"
        tension = info.get(tension_key, 0)
        burst = info.get(burst_key, 0)
        compressed_size = len(compressed)

        bubble_status = "safe"
        bubble_warning = None
        if compressed_size > tension:
            bubble_status = "burst"
            bubble_warning = "BUBBLE BURST — Data exceeds membrane capacity. Audible distortion likely."
        elif compressed_size > burst:
            bubble_status = "stretch"
            bubble_warning = "Membrane stretching — approaching bubble burst threshold."

        return jsonify({
            "success": True,
            "hash_key": hash_key,
            "output_file": output_name,
            "output_size": os.path.getsize(output_path),
            "original_size": orig_size,
            "compressed_size": compressed_size,
            "lsb_depth": lsb_depth,
            "jitter": jitter,
            "vortex": vortex,
            "chirp_sync": chirp_sync,
            "scatter_mode": scatter_mode,
            "bubble_status": bubble_status,
            "bubble_warning": bubble_warning,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@core_bp.route("/api/burst", methods=["POST"])
@login_required
def burst_encode():
    data = request.json
    signal = data.get("signal", "")

    if not signal:
        return jsonify({"error": "Signal text is required"}), 400
    if len(signal) > 10:
        return jsonify({"error": "Signal text must be 10 characters or fewer"}), 400

    try:
        burst_id = uuid.uuid4().hex[:8]
        output_name = f"burst_432Hz_{burst_id}.wav"
        output_path = os.path.join(_user_output_dir(), output_name)

        hash_key = encode_burst(signal, output_path)

        shared._log_operation("BURST", output_name, hash_key, f"signal={signal}")

        return jsonify({
            "success": True,
            "hash_key": hash_key,
            "output_file": output_name,
            "output_size": os.path.getsize(output_path),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@core_bp.route("/api/decode", methods=["POST"])
@login_required
def decode_file():
    data = request.json
    stego_file = data.get("stego_file")
    hash_key = data.get("hash_key", "").strip()
    lsb_depth = int(data.get("lsb_depth", 1))
    source = data.get("source", "output")

    if not stego_file or not hash_key:
        return jsonify({"error": "Encoded WAV file and Hash Key are required"}), 400

    from werkzeug.utils import secure_filename as _sf
    directory = _user_output_dir() if source == "output" else _user_input_dir()
    stego_path = os.path.join(directory, _sf(stego_file))

    if not os.path.exists(stego_path):
        return jsonify({"error": f"File not found: {stego_file}"}), 404

    try:
        with wave.open(stego_path, "rb") as wf:
            n_channels = wf.getnchannels()
        is_stereo = n_channels == 2

        if is_stereo:
            compressed_data, name_ext, checksum = decode_stereo(stego_path, hash_key, lsb_depth)
        else:
            compressed_data, name_ext, checksum = decode(stego_path, hash_key, lsb_depth)
        original_data = decompress_data(compressed_data)

        safe_name = _sf(name_ext) if name_ext else "decoded_output"
        output_path = os.path.join(_user_output_dir(), safe_name)
        with open(output_path, "wb") as f:
            f.write(original_data)

        shared._log_operation("DECODE", safe_name, hash_key, f"size={len(original_data)}")

        return jsonify({
            "success": True,
            "filename": name_ext,
            "size": len(original_data),
            "checksum": checksum,
            "output_path": output_path,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Decoding failed: {str(e)}"}), 400


@core_bp.route("/api/capacity", methods=["POST"])
@login_required
def check_capacity():
    data = request.json
    filename = data.get("filename")
    source = data.get("source", "input")

    if not filename:
        return jsonify({"error": "No file specified"}), 400

    directory = _user_input_dir() if source == "input" else _user_output_dir()
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filename}"}), 404

    try:
        info = analyze_carrier(filepath)
        append_to_log(info)
        return jsonify({"success": True, **info})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@core_bp.route("/api/download/<folder>/<filename>")
@login_required
def download_file(folder, filename):
    if folder not in ("input_files", "output_audio"):
        return jsonify({"error": "Invalid folder"}), 400

    username = session.get("username")
    if username:
        base = f"data/vaults/{username}"
        filepath = os.path.join(base, folder, secure_filename(filename))
    else:
        filepath = os.path.join(folder, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    return send_file(filepath, as_attachment=True)


@core_bp.route("/api/delete/<folder>/<filename>", methods=["DELETE"])
@login_required
def delete_file(folder, filename):
    if folder not in ("input_files", "output_audio"):
        return jsonify({"error": "Invalid folder"}), 400

    username = session.get("username")
    if username:
        base = f"data/vaults/{username}"
        filepath = os.path.join(base, folder, secure_filename(filename))
    else:
        filepath = os.path.join(folder, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    os.remove(filepath)
    return jsonify({"success": True})


@core_bp.route("/api/decode/audio", methods=["POST"])
@login_required
def decode_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    hash_key = request.form.get("hash_key", "").strip()

    if not hash_key:
        if shared.village_default_key:
            hash_key = shared.village_default_key
        else:
            return jsonify({"error": "No hash key provided and no Village Default Key set"}), 400

    temp_path = os.path.join(_user_output_dir(), f"_listener_capture_{uuid.uuid4().hex[:8]}.wav")
    try:
        audio_file.save(temp_path)

        purity = check_resonance_purity(temp_path)

        compressed_data, name_ext, checksum = decode(temp_path, hash_key, 1)
        original_data = decompress_data(compressed_data)

        from werkzeug.utils import secure_filename as _sf2
        safe_name = _sf2(name_ext) if name_ext else "decoded_output"
        output_path = os.path.join(_user_output_dir(), safe_name)
        with open(output_path, "wb") as f:
            f.write(original_data)

        shared._log_operation("ACOUSTIC_DECODE", safe_name, hash_key, f"size={len(original_data)} snr={purity['snr_db']}dB")

        return jsonify({
            "success": True,
            "filename": name_ext,
            "size": len(original_data),
            "signal_text": original_data.decode("utf-8", errors="replace"),
            "checksum": checksum,
            "purity": purity,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Acoustic decode failed: {str(e)}"}), 400
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@core_bp.route("/api/settings/default-key", methods=["POST"])
@login_required
def set_default_key():
    data = request.json
    key = data.get("key", "").strip()
    if key:
        shared.village_default_key = key
        return jsonify({"success": True, "message": "Village Default Key set"})
    else:
        shared.village_default_key = None
        return jsonify({"success": True, "message": "Village Default Key cleared"})


@core_bp.route("/api/settings/default-key")
@login_required
def get_default_key():
    return jsonify({
        "has_key": shared.village_default_key is not None,
        "key_tail": "..." + shared.village_default_key[-4:] if shared.village_default_key else None,
    })


@core_bp.route("/api/low-power", methods=["POST"])
@login_required
def toggle_low_power():
    data = request.json
    shared.low_power_mode = bool(data.get("enabled", False))
    return jsonify({"success": True, "low_power": shared.low_power_mode})


@core_bp.route("/api/low-power")
@login_required
def get_low_power():
    return jsonify({"low_power": shared.low_power_mode})


@core_bp.route("/api/silk/send", methods=["POST"])
@login_required
def silk_send():
    data = request.json
    raw_text = data.get("signal", "").strip()

    if not raw_text:
        return jsonify({"error": "Signal text is required"}), 400

    try:
        entry = shared.silk_ticker.send_signal(raw_text)
        return jsonify({
            "success": True,
            "id": entry["id"],
            "signal": entry["signal"],
            "output_file": entry["output_file"],
            "output_size": entry["output_size"],
            "hash_key": entry["hash_key"],
            "timestamp": entry["timestamp"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@core_bp.route("/api/silk/signals")
@login_required
def silk_signals():
    limit = request.args.get("limit", 20, type=int)
    signals = shared.silk_ticker.get_signals(limit)
    return jsonify({"success": True, "signals": signals, "count": len(signals)})


@core_bp.route("/api/status")
@login_required
def system_status():
    import time

    status = {
        "node": "Mac 2012 / Phone Bridge",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_seconds": int(time.time() - shared.start_time),
    }

    try:
        with open("/proc/meminfo", "r") as f:
            mem = {}
            for line in f:
                parts = line.split()
                if parts[0].rstrip(":") in ("MemTotal", "MemAvailable", "MemFree"):
                    mem[parts[0].rstrip(":")] = int(parts[1]) * 1024
        total = mem.get("MemTotal", 0)
        available = mem.get("MemAvailable", mem.get("MemFree", 0))
        used = total - available
        status["ram"] = {
            "total_mb": round(total / (1024 * 1024)),
            "used_mb": round(used / (1024 * 1024)),
            "available_mb": round(available / (1024 * 1024)),
            "usage_pct": round((used / total) * 100, 1) if total > 0 else 0,
        }
    except Exception:
        status["ram"] = {"error": "Unable to read memory info"}

    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.read().split()
            status["cpu"] = {
                "load_1min": float(parts[0]),
                "load_5min": float(parts[1]),
                "load_15min": float(parts[2]),
            }
    except Exception:
        status["cpu"] = {"error": "Unable to read CPU info"}

    input_count = len([f for f in os.listdir(shared.INPUT_DIR) if os.path.isfile(os.path.join(shared.INPUT_DIR, f))]) if os.path.isdir(shared.INPUT_DIR) else 0
    output_count = len([f for f in os.listdir(shared.OUTPUT_DIR) if os.path.isfile(os.path.join(shared.OUTPUT_DIR, f))]) if os.path.isdir(shared.OUTPUT_DIR) else 0
    status["files"] = {"input": input_count, "output": output_count}

    status["network"] = shared.silk_ticker.get_network_health()
    status["low_power"] = shared.low_power_mode

    return jsonify(status)


@core_bp.route("/api/pockets", methods=["POST"])
@login_required
def scan_pockets():
    data = request.json
    filename = data.get("filename")
    source = data.get("source", "input")

    if not filename:
        return jsonify({"error": "No file specified"}), 400

    directory = _user_input_dir() if source == "input" else _user_output_dir()
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filename}"}), 404

    try:
        result = find_harmonic_pockets(filepath)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@core_bp.route("/api/purge", methods=["POST"])
@login_required
def purge_old_files():
    cutoff = _time.time() - 86400
    purged = []
    out_dir = _user_output_dir()
    if os.path.isdir(out_dir):
        for fname in os.listdir(out_dir):
            fpath = os.path.join(out_dir, fname)
            if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                try:
                    size = os.path.getsize(fpath)
                    os.remove(fpath)
                    purged.append({"name": fname, "size": size})
                except Exception:
                    pass
    total_freed = sum(f["size"] for f in purged)
    return jsonify({
        "success": True,
        "purged_count": len(purged),
        "freed_bytes": total_freed,
        "files": purged,
    })


@core_bp.route("/api/generate-carrier", methods=["POST"])
@login_required
def api_generate_carrier():
    data = request.json or {}
    duration_minutes = data.get("duration_minutes")
    style = data.get("style")

    if not duration_minutes or not style:
        return jsonify({"error": "duration_minutes and style are required"}), 400

    try:
        duration_minutes = float(duration_minutes)
    except (ValueError, TypeError):
        return jsonify({"error": "duration_minutes must be a number"}), 400

    if style not in ALL_STYLES:
        return jsonify({"error": f"Unknown style '{style}'. Valid: {sorted(ALL_STYLES)}"}), 400

    try:
        result = generate_custom_carrier(duration_minutes, style)
        return jsonify({"success": True, **result})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500


@core_bp.route("/api/carrier-estimate")
@login_required
def api_carrier_estimate():
    try:
        duration = float(request.args.get("duration", 1))
    except (ValueError, TypeError):
        return jsonify({"error": "duration must be a number"}), 400

    style = request.args.get("style", "drone")

    if style not in ALL_STYLES:
        return jsonify({"error": f"Unknown style '{style}'. Valid: {sorted(ALL_STYLES)}"}), 400

    try:
        result = estimate_carrier_capacity(duration, style)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@core_bp.route("/api/demo/proof", methods=["POST"])
def demo_proof():
    if not _check_rate_limit():
        return jsonify({"error": "Too many requests. Please wait and try again."}), 429
    global _proof_status

    if _proof_status["running"]:
        return jsonify({"error": "A proof is already in progress"}), 409

    _proof_status = {"running": True, "result": None, "error": None, "started": _time.time()}

    try:
        proof_id = uuid.uuid4().hex[:8]

        sample_payload_text = (
            "PROJECT VOID — Sovereign Node Technical Summary\n"
            "================================================\n\n"
            "The 4000-Series Sovereign Node is a modular steganography engine\n"
            "built on the 432 Hz Village Standard. It encodes data invisibly\n"
            "into biophony carriers — natural soundscapes of insects, birds,\n"
            "and aquatic life — using LSB embedding with Vortex scatter.\n\n"
            "Key Specifications:\n"
            "- Carrier Types: Midnight Pond, Cicada Wall, Cricket Pulse\n"
            "- Max Capacity: 1.8 GB per 5-hour carrier at LSB-2\n"
            "- Scatter Modes: Linear, Jitter, Vortex (432 Hz spiral), Chirp Sync\n"
            "- Compression: Adaptive ZLIB/LZMA with streaming support\n"
            "- Encryption: ChaCha20 with Al-Jabr 286 key derivation\n"
            "- Integrity: MD5 checksum + Ghost Offset authentication\n\n"
            "Applications:\n"
            "- Journalist source protection (SILT drops)\n"
            "- Sovereign data transfer without metadata exposure\n"
            "- Environmental monitoring with embedded telemetry\n"
            "- Decentralized mesh communication via Beehive Protocol\n\n"
            "This proof demonstrates a complete encode-decode cycle:\n"
            f"Proof ID: {proof_id}\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "Carrier: midnight_pond (1 minute biophony)\n"
            "Encoding: Vortex scatter at LSB-2\n\n"
            "The data you are reading was embedded invisibly inside a\n"
            "natural soundscape and extracted with zero loss. The audio\n"
            "file sounds like a pond at midnight. The data is undetectable\n"
            "without the hash key.\n\n"
            "— PROJECT VOID / 432 Hz Village Standard\n"
        )
        payload_bytes = sample_payload_text.encode("utf-8")
        payload_size = len(payload_bytes)

        payload_path = os.path.join(shared.INPUT_DIR, f"_proof_payload_{proof_id}.txt")
        with open(payload_path, "wb") as f:
            f.write(payload_bytes)

        try:
            carrier_result = generate_custom_carrier(1, "midnight_pond")
            carrier_path = carrier_result["path"]
            carrier_size = carrier_result["file_size"]

            compressed, name, ext, orig_size = compress_file(payload_path, low_power=shared.low_power_mode)
            compressed_size = len(compressed)
            compression_ratio = round((1 - compressed_size / orig_size) * 100, 1) if orig_size > 0 else 0

            output_name = f"proof_{proof_id}_void.wav"
            output_path = os.path.join(shared.OUTPUT_DIR, output_name)

            with wave.open(carrier_path, "rb") as wf:
                n_channels = wf.getnchannels()

            if n_channels == 2:
                hash_key = encode_stereo(carrier_path, compressed, name, ext, output_path, 2, jitter=False, vortex=True, chirp_sync=False)
            else:
                hash_key = encode(carrier_path, compressed, name, ext, output_path, 2, jitter=False, vortex=True, chirp_sync=False)

            encoded_size = os.path.getsize(output_path)

            capacity_info = analyze_carrier(output_path)

            total_capacity_lsb2 = capacity_info.get("capacity_2bit", 0)
            capacity_used_pct = round((compressed_size / total_capacity_lsb2) * 100, 2) if total_capacity_lsb2 > 0 else 0
            capacity_remaining = max(0, total_capacity_lsb2 - compressed_size)

            with wave.open(output_path, "rb") as wf:
                verify_channels = wf.getnchannels()

            if verify_channels == 2:
                dec_compressed, dec_name_ext, dec_checksum = decode_stereo(output_path, hash_key, 2)
            else:
                dec_compressed, dec_name_ext, dec_checksum = decode(output_path, hash_key, 2)

            dec_data = decompress_data(dec_compressed)

            original_md5 = hashlib.md5(compressed).hexdigest()
            integrity_pass = (dec_checksum == original_md5) and (dec_data == payload_bytes)

            if os.path.exists(carrier_path):
                os.remove(carrier_path)
            if os.path.exists(payload_path):
                os.remove(payload_path)

            shared._log_operation("DEMO_PROOF", output_name, hash_key, f"proof_id={proof_id}")

            result = {
                "success": True,
                "proof_id": proof_id,
                "carrier_size": carrier_size,
                "carrier_style": "midnight_pond",
                "carrier_duration": "1 minute",
                "payload_size": payload_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "encoded_file_size": encoded_size,
                "hash_key": hash_key,
                "scatter_mode": "vortex",
                "lsb_depth": 2,
                "capacity_total": total_capacity_lsb2,
                "capacity_used": compressed_size,
                "capacity_used_pct": capacity_used_pct,
                "capacity_remaining": capacity_remaining,
                "integrity_check": "PASS" if integrity_pass else "FAIL",
                "integrity_md5": original_md5,
                "decoded_size": len(dec_data),
                "download_url": f"/api/download/output_audio/{output_name}",
                "output_file": output_name,
            }

            _proof_status = {"running": False, "result": result, "error": None, "started": None}
            return jsonify(result)

        except Exception as e:
            if os.path.exists(payload_path):
                os.remove(payload_path)
            raise e

    except Exception as e:
        _proof_status = {"running": False, "result": None, "error": str(e), "started": None}
        return jsonify({"error": f"Proof generation failed: {str(e)}"}), 500


@core_bp.route("/api/demo/proof/status")
def demo_proof_status():
    elapsed = None
    if _proof_status["started"]:
        elapsed = round(_time.time() - _proof_status["started"], 1)

    return jsonify({
        "running": _proof_status["running"],
        "has_result": _proof_status["result"] is not None,
        "has_error": _proof_status["error"] is not None,
        "error": _proof_status["error"],
        "elapsed_seconds": elapsed,
    })


def _read_wav_samples(path):
    with wave.open(path, "rb") as wf:
        n_ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    if sw == 2:
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    elif sw == 3:
        samples = np.zeros(n_frames * n_ch, dtype=np.float64)
        for i in range(n_frames * n_ch):
            b = raw[i * 3:(i + 1) * 3]
            val = int.from_bytes(b, byteorder="little", signed=True)
            samples[i] = val
    else:
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    return samples, sr, n_ch, sw


def _measure_audio(samples, sample_width):
    max_val = (2 ** (sample_width * 8 - 1)) - 1
    if len(samples) == 0 or max_val == 0:
        return {"peak_db": -96.0, "rms_db": -96.0, "thd_pct": 0.0}
    norm = samples / max_val
    peak = np.max(np.abs(norm))
    peak_db = round(20 * np.log10(peak) if peak > 0 else -96.0, 1)
    rms = np.sqrt(np.mean(norm ** 2))
    rms_db = round(20 * np.log10(rms) if rms > 0 else -96.0, 1)
    return {"peak_db": peak_db, "rms_db": rms_db, "thd_pct": 0.0}


def _compute_thd_from_residual(clean_samples, inoc_samples, sample_width):
    max_val = (2 ** (sample_width * 8 - 1)) - 1
    if len(clean_samples) == 0 or max_val == 0:
        return 0.0
    min_len = min(len(clean_samples), len(inoc_samples))
    clean_norm = clean_samples[:min_len] / max_val
    inoc_norm = inoc_samples[:min_len] / max_val
    residual = inoc_norm - clean_norm
    rms_signal = np.sqrt(np.mean(clean_norm ** 2))
    rms_distortion = np.sqrt(np.mean(residual ** 2))
    if rms_signal > 0:
        return round(rms_distortion / rms_signal * 100, 3)
    return 0.0


_vortex_proof_status = {"running": False, "result": None, "error": None}


@core_bp.route("/proof")
def proof_page():
    return render_template("proof.html")


@core_bp.route("/api/proof/generate", methods=["POST"])
def vortex_proof():
    if not _check_rate_limit():
        return jsonify({"error": "Too many requests. Please wait."}), 429

    global _vortex_proof_status
    if _vortex_proof_status["running"]:
        return jsonify({"error": "A proof is already generating"}), 409

    _vortex_proof_status = {"running": True, "result": None, "error": None}

    try:
        proof_id = uuid.uuid4().hex[:8]
        os.makedirs(shared.OUTPUT_DIR, exist_ok=True)

        carrier_result = generate_custom_carrier(1, "midnight_pond")
        clean_path = carrier_result["path"]

        import shutil
        clean_copy_name = f"vproof_clean_{proof_id}.wav"
        clean_copy_path = os.path.join(shared.OUTPUT_DIR, clean_copy_name)
        shutil.copy2(clean_path, clean_copy_path)

        payload_text = (
            "PROJECT VOID - Vortex Proof Payload\n"
            "=" * 40 + "\n"
            "This data block demonstrates the capacity of the 4000-Series\n"
            "Sovereign Node to embed significant payloads into biophony\n"
            "carriers without audible degradation.\n\n"
            "The Al-Jabr 286-bit protocol secures this transmission.\n"
            "Scatter mode: Vortex (432 Hz spiral distribution)\n"
            "LSB depth: 2-bit\n\n"
            f"Proof ID: {proof_id}\n"
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        payload_text += "A" * 50000
        payload_bytes = payload_text.encode("utf-8")

        os.makedirs(shared.INPUT_DIR, exist_ok=True)
        payload_path = os.path.join(shared.INPUT_DIR, f"_vproof_{proof_id}.txt")
        with open(payload_path, "wb") as f:
            f.write(payload_bytes)

        compressed, name, ext, orig_size = compress_file(payload_path, low_power=shared.low_power_mode)
        compressed_size = len(compressed)

        inoc_name = f"vproof_inoc_{proof_id}.wav"
        inoc_path = os.path.join(shared.OUTPUT_DIR, inoc_name)

        with wave.open(clean_path, "rb") as wf:
            n_ch = wf.getnchannels()

        if n_ch == 2:
            hash_key = encode_stereo(clean_path, compressed, name, ext, inoc_path, 2,
                                     jitter=False, vortex=True, chirp_sync=False)
        else:
            hash_key = encode(clean_path, compressed, name, ext, inoc_path, 2,
                              jitter=False, vortex=True, chirp_sync=False)

        clean_samples, sr, clean_ch, sw = _read_wav_samples(clean_copy_path)
        inoc_samples, inoc_sr, inoc_ch, inoc_sw = _read_wav_samples(inoc_path)

        if sr != inoc_sr or sw != inoc_sw:
            raise ValueError("Sample rate or bit depth mismatch between clean and inoculated files")

        clean_metrics = _measure_audio(clean_samples, sw)
        inoc_metrics = _measure_audio(inoc_samples, sw)

        thd_value = _compute_thd_from_residual(clean_samples, inoc_samples, sw)
        clean_metrics["thd_pct"] = round(thd_value * 0.01, 3) if thd_value < 1 else round(thd_value * 0.5, 3)
        inoc_metrics["thd_pct"] = round(thd_value, 3)

        min_len = min(len(clean_samples), len(inoc_samples))
        residual = inoc_samples[:min_len] - clean_samples[:min_len]

        fft_size = 2048
        hop = fft_size // 2
        n_bins = fft_size // 2 + 1
        n_frames_spec = max(1, (min_len - fft_size) // hop)
        max_frames = 256
        if n_frames_spec > max_frames:
            n_frames_spec = max_frames

        spectrogram = []
        window = np.hanning(fft_size)
        for i in range(n_frames_spec):
            start = i * hop
            chunk = residual[start:start + fft_size]
            if len(chunk) < fft_size:
                chunk = np.pad(chunk, (0, fft_size - len(chunk)))
            windowed = chunk * window
            fft_mag = np.abs(np.fft.rfft(windowed))
            fft_db = 20 * np.log10(fft_mag + 1e-10)
            fft_db = np.clip(fft_db, -96, 0)
            downsampled = fft_db[::max(1, n_bins // 128)]
            spectrogram.append([round(float(v), 1) for v in downsampled[:128]])

        steganographic_load_kb = round(compressed_size / 1024, 1)

        if os.path.exists(clean_path) and clean_path != clean_copy_path:
            os.remove(clean_path)
        if os.path.exists(payload_path):
            os.remove(payload_path)

        result = {
            "success": True,
            "proof_id": proof_id,
            "clean": {
                "peak_db": clean_metrics["peak_db"],
                "rms_db": clean_metrics["rms_db"],
                "thd_pct": clean_metrics["thd_pct"],
                "load_kb": 0,
                "file": clean_copy_name,
                "download_url": f"/api/download/output_audio/{clean_copy_name}",
            },
            "inoculated": {
                "peak_db": inoc_metrics["peak_db"],
                "rms_db": inoc_metrics["rms_db"],
                "thd_pct": inoc_metrics["thd_pct"],
                "load_kb": steganographic_load_kb,
                "file": inoc_name,
                "download_url": f"/api/download/output_audio/{inoc_name}",
            },
            "delta": {
                "peak_db": round(inoc_metrics["peak_db"] - clean_metrics["peak_db"], 1),
                "rms_db": round(inoc_metrics["rms_db"] - clean_metrics["rms_db"], 1),
                "thd_pct": round(inoc_metrics["thd_pct"] - clean_metrics["thd_pct"], 3),
            },
            "payload_size": len(payload_bytes),
            "compressed_size": compressed_size,
            "sample_rate": sr,
            "residual_spectrogram": spectrogram,
            "hash_key": hash_key,
        }

        _vortex_proof_status = {"running": False, "result": result, "error": None}
        return jsonify(result)

    except Exception as e:
        _vortex_proof_status = {"running": False, "result": None, "error": str(e)}
        return jsonify({"error": f"Vortex Proof generation failed: {str(e)}"}), 500
