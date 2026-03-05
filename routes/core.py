import os
import uuid
import wave
import time as _time
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from void_engine.compressor import compress_file, decompress_data
from void_engine.stega import (encode, decode, encode_burst, check_resonance_purity,
                                encode_stereo, decode_stereo, find_harmonic_pockets)
from void_engine.calculator import analyze_carrier, append_to_log
from generate_carriers import generate_custom_carrier, estimate_carrier_capacity, ALL_STYLES

import routes.shared as shared

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
def index():
    return render_template("index.html")


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


@core_bp.route("/api/files")
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
        "input": get_files(shared.INPUT_DIR),
        "output": get_files(shared.OUTPUT_DIR),
    })


@core_bp.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No filename"}), 400

    filename = secure_filename(f.filename)
    dest = request.form.get("dest", "input")
    directory = shared.INPUT_DIR if dest == "input" else shared.OUTPUT_DIR
    filepath = os.path.join(directory, filename)
    f.save(filepath)

    return jsonify({
        "success": True,
        "filename": filename,
        "size": os.path.getsize(filepath),
    })


@core_bp.route("/api/encode", methods=["POST"])
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

    carrier_path = os.path.join(shared.INPUT_DIR, carrier)
    payload_path = os.path.join(shared.INPUT_DIR, payload)

    if not os.path.exists(carrier_path):
        return jsonify({"error": f"Carrier file not found: {carrier}"}), 404
    if not os.path.exists(payload_path):
        return jsonify({"error": f"Payload file not found: {payload}"}), 404

    try:
        compressed, name, ext, orig_size = compress_file(payload_path, low_power=shared.low_power_mode)

        base_name = os.path.splitext(carrier)[0]
        output_name = f"{base_name}_void.wav"
        output_path = os.path.join(shared.OUTPUT_DIR, output_name)

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
        output_path = os.path.join(shared.OUTPUT_DIR, output_name)

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
def decode_file():
    data = request.json
    stego_file = data.get("stego_file")
    hash_key = data.get("hash_key", "").strip()
    lsb_depth = int(data.get("lsb_depth", 1))
    source = data.get("source", "output")

    if not stego_file or not hash_key:
        return jsonify({"error": "Encoded WAV file and Hash Key are required"}), 400

    directory = shared.OUTPUT_DIR if source == "output" else shared.INPUT_DIR
    stego_path = os.path.join(directory, stego_file)

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

        output_path = os.path.join(shared.OUTPUT_DIR, name_ext)
        with open(output_path, "wb") as f:
            f.write(original_data)

        shared._log_operation("DECODE", name_ext, hash_key, f"size={len(original_data)}")

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
def check_capacity():
    data = request.json
    filename = data.get("filename")
    source = data.get("source", "input")

    if not filename:
        return jsonify({"error": "No file specified"}), 400

    directory = shared.INPUT_DIR if source == "input" else shared.OUTPUT_DIR
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
def download_file(folder, filename):
    if folder not in ("input_files", "output_audio"):
        return jsonify({"error": "Invalid folder"}), 400

    filepath = os.path.join(folder, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    return send_file(filepath, as_attachment=True)


@core_bp.route("/api/delete/<folder>/<filename>", methods=["DELETE"])
def delete_file(folder, filename):
    if folder not in ("input_files", "output_audio"):
        return jsonify({"error": "Invalid folder"}), 400

    filepath = os.path.join(folder, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    os.remove(filepath)
    return jsonify({"success": True})


@core_bp.route("/api/decode/audio", methods=["POST"])
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

    temp_path = os.path.join(shared.OUTPUT_DIR, f"_listener_capture_{uuid.uuid4().hex[:8]}.wav")
    try:
        audio_file.save(temp_path)

        purity = check_resonance_purity(temp_path)

        compressed_data, name_ext, checksum = decode(temp_path, hash_key, 1)
        original_data = decompress_data(compressed_data)

        output_path = os.path.join(shared.OUTPUT_DIR, name_ext)
        with open(output_path, "wb") as f:
            f.write(original_data)

        shared._log_operation("ACOUSTIC_DECODE", name_ext, hash_key, f"size={len(original_data)} snr={purity['snr_db']}dB")

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
def get_default_key():
    return jsonify({
        "has_key": shared.village_default_key is not None,
        "key_tail": "..." + shared.village_default_key[-4:] if shared.village_default_key else None,
    })


@core_bp.route("/api/low-power", methods=["POST"])
def toggle_low_power():
    data = request.json
    shared.low_power_mode = bool(data.get("enabled", False))
    return jsonify({"success": True, "low_power": shared.low_power_mode})


@core_bp.route("/api/low-power")
def get_low_power():
    return jsonify({"low_power": shared.low_power_mode})


@core_bp.route("/api/silk/send", methods=["POST"])
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
def silk_signals():
    limit = request.args.get("limit", 20, type=int)
    signals = shared.silk_ticker.get_signals(limit)
    return jsonify({"success": True, "signals": signals, "count": len(signals)})


@core_bp.route("/api/status")
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
def scan_pockets():
    data = request.json
    filename = data.get("filename")
    source = data.get("source", "input")

    if not filename:
        return jsonify({"error": "No file specified"}), 400

    directory = shared.INPUT_DIR if source == "input" else shared.OUTPUT_DIR
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filename}"}), 404

    try:
        result = find_harmonic_pockets(filepath)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@core_bp.route("/api/purge", methods=["POST"])
def purge_old_files():
    cutoff = _time.time() - 86400
    purged = []
    if os.path.isdir(shared.OUTPUT_DIR):
        for fname in os.listdir(shared.OUTPUT_DIR):
            fpath = os.path.join(shared.OUTPUT_DIR, fname)
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
