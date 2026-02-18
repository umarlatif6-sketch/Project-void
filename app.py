import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

import wave

from void_engine.compressor import compress_file, decompress_data
from void_engine.stega import (encode, decode, encode_burst, check_resonance_purity,
                                encode_stereo, decode_stereo, find_harmonic_pockets)
from void_engine.calculator import analyze_carrier, append_to_log
from void_engine.silk_web import SignalTicker
from void_engine.harness import PreCompletionChecklistMiddleware, VirtualVoidSimulator
from void_engine.nervous_system import SilkLinkContextMiddleware, AquaponicsBoundaryHook
from void_engine.loop_detector import LoopDetectionMiddleware

LOG_FILE = "RESONANCE_LOG.md"


def _log_operation(op_type: str, filename: str, hash_key: str, extra: str = ""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hash_tail = hash_key[-4:] if hash_key else "????"
    with open(LOG_FILE, "a") as f:
        line = f"| {timestamp} | {op_type} | {filename} | ...{hash_tail} |"
        if extra:
            line += f" {extra} |"
        f.write(line + "\n")

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "void-engine-dev-key")

INPUT_DIR = "input_files"
OUTPUT_DIR = "output_audio"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

_low_power_mode = False
_village_default_key = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/files")
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
        "input": get_files(INPUT_DIR),
        "output": get_files(OUTPUT_DIR),
    })


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No filename"}), 400

    filename = secure_filename(f.filename)
    dest = request.form.get("dest", "input")
    directory = INPUT_DIR if dest == "input" else OUTPUT_DIR
    filepath = os.path.join(directory, filename)
    f.save(filepath)

    return jsonify({
        "success": True,
        "filename": filename,
        "size": os.path.getsize(filepath),
    })


@app.route("/api/encode", methods=["POST"])
def encode_file():
    data = request.json
    carrier = data.get("carrier")
    payload = data.get("payload")
    lsb_depth = int(data.get("lsb_depth", 1))
    jitter = bool(data.get("jitter", False))

    if not carrier or not payload:
        return jsonify({"error": "Carrier and payload files are required"}), 400

    carrier_path = os.path.join(INPUT_DIR, carrier)
    payload_path = os.path.join(INPUT_DIR, payload)

    if not os.path.exists(carrier_path):
        return jsonify({"error": f"Carrier file not found: {carrier}"}), 404
    if not os.path.exists(payload_path):
        return jsonify({"error": f"Payload file not found: {payload}"}), 404

    try:
        compressed, name, ext, orig_size = compress_file(payload_path, low_power=_low_power_mode)

        base_name = os.path.splitext(carrier)[0]
        output_name = f"{base_name}_void.wav"
        output_path = os.path.join(OUTPUT_DIR, output_name)

        with wave.open(carrier_path, "rb") as wf:
            n_channels = wf.getnchannels()
        is_stereo = n_channels == 2

        if is_stereo:
            hash_key = encode_stereo(carrier_path, compressed, name, ext, output_path, lsb_depth, jitter=jitter)
        else:
            hash_key = encode(carrier_path, compressed, name, ext, output_path, lsb_depth, jitter=jitter)

        _log_operation("ENCODE", output_name, hash_key, f"LSB{lsb_depth}")

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
            "bubble_status": bubble_status,
            "bubble_warning": bubble_warning,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/burst", methods=["POST"])
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
        output_path = os.path.join(OUTPUT_DIR, output_name)

        hash_key = encode_burst(signal, output_path)

        _log_operation("BURST", output_name, hash_key, f"signal={signal}")

        return jsonify({
            "success": True,
            "hash_key": hash_key,
            "output_file": output_name,
            "output_size": os.path.getsize(output_path),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/decode", methods=["POST"])
def decode_file():
    data = request.json
    stego_file = data.get("stego_file")
    hash_key = data.get("hash_key", "").strip()
    lsb_depth = int(data.get("lsb_depth", 1))
    source = data.get("source", "output")

    if not stego_file or not hash_key:
        return jsonify({"error": "Encoded WAV file and Hash Key are required"}), 400

    directory = OUTPUT_DIR if source == "output" else INPUT_DIR
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

        output_path = os.path.join(OUTPUT_DIR, name_ext)
        with open(output_path, "wb") as f:
            f.write(original_data)

        _log_operation("DECODE", name_ext, hash_key, f"size={len(original_data)}")

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


@app.route("/api/capacity", methods=["POST"])
def check_capacity():
    data = request.json
    filename = data.get("filename")
    source = data.get("source", "input")

    if not filename:
        return jsonify({"error": "No file specified"}), 400

    directory = INPUT_DIR if source == "input" else OUTPUT_DIR
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filename}"}), 404

    try:
        info = analyze_carrier(filepath)
        append_to_log(info)
        return jsonify({"success": True, **info})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download/<folder>/<filename>")
def download_file(folder, filename):
    if folder not in ("input_files", "output_audio"):
        return jsonify({"error": "Invalid folder"}), 400

    filepath = os.path.join(folder, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    return send_file(filepath, as_attachment=True)


@app.route("/api/delete/<folder>/<filename>", methods=["DELETE"])
def delete_file(folder, filename):
    if folder not in ("input_files", "output_audio"):
        return jsonify({"error": "Invalid folder"}), 400

    filepath = os.path.join(folder, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    os.remove(filepath)
    return jsonify({"success": True})


silk_ticker = SignalTicker()
silk_ticker.start_heartbeat()


@app.route("/api/decode/audio", methods=["POST"])
def decode_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    hash_key = request.form.get("hash_key", "").strip()

    if not hash_key:
        global _village_default_key
        if _village_default_key:
            hash_key = _village_default_key
        else:
            return jsonify({"error": "No hash key provided and no Village Default Key set"}), 400

    temp_path = os.path.join(OUTPUT_DIR, f"_listener_capture_{uuid.uuid4().hex[:8]}.wav")
    try:
        audio_file.save(temp_path)

        purity = check_resonance_purity(temp_path)

        compressed_data, name_ext, checksum = decode(temp_path, hash_key, 1)
        original_data = decompress_data(compressed_data)

        output_path = os.path.join(OUTPUT_DIR, name_ext)
        with open(output_path, "wb") as f:
            f.write(original_data)

        _log_operation("ACOUSTIC_DECODE", name_ext, hash_key, f"size={len(original_data)} snr={purity['snr_db']}dB")

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


@app.route("/api/settings/default-key", methods=["POST"])
def set_default_key():
    global _village_default_key
    data = request.json
    key = data.get("key", "").strip()
    if key:
        _village_default_key = key
        return jsonify({"success": True, "message": "Village Default Key set"})
    else:
        _village_default_key = None
        return jsonify({"success": True, "message": "Village Default Key cleared"})


@app.route("/api/settings/default-key")
def get_default_key():
    global _village_default_key
    return jsonify({
        "has_key": _village_default_key is not None,
        "key_tail": "..." + _village_default_key[-4:] if _village_default_key else None,
    })


@app.route("/api/low-power", methods=["POST"])
def toggle_low_power():
    global _low_power_mode
    data = request.json
    _low_power_mode = bool(data.get("enabled", False))
    return jsonify({"success": True, "low_power": _low_power_mode})


@app.route("/api/low-power")
def get_low_power():
    return jsonify({"low_power": _low_power_mode})


@app.route("/api/silk/send", methods=["POST"])
def silk_send():
    data = request.json
    raw_text = data.get("signal", "").strip()

    if not raw_text:
        return jsonify({"error": "Signal text is required"}), 400

    try:
        entry = silk_ticker.send_signal(raw_text)
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


@app.route("/api/silk/signals")
def silk_signals():
    limit = request.args.get("limit", 20, type=int)
    signals = silk_ticker.get_signals(limit)
    return jsonify({"success": True, "signals": signals, "count": len(signals)})


@app.route("/api/status")
def system_status():
    import time

    status = {
        "node": "Mac 2012 / Phone Bridge",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_seconds": int(time.time() - _start_time),
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

    input_count = len([f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]) if os.path.isdir(INPUT_DIR) else 0
    output_count = len([f for f in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, f))]) if os.path.isdir(OUTPUT_DIR) else 0
    status["files"] = {"input": input_count, "output": output_count}

    status["network"] = silk_ticker.get_network_health()
    status["low_power"] = _low_power_mode

    return jsonify(status)


@app.route("/api/pockets", methods=["POST"])
def scan_pockets():
    data = request.json
    filename = data.get("filename")
    source = data.get("source", "input")

    if not filename:
        return jsonify({"error": "No file specified"}), 400

    directory = INPUT_DIR if source == "input" else OUTPUT_DIR
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filename}"}), 404

    try:
        result = find_harmonic_pockets(filepath)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/purge", methods=["POST"])
def purge_old_files():
    import time as _time
    cutoff = _time.time() - 86400
    purged = []
    if os.path.isdir(OUTPUT_DIR):
        for fname in os.listdir(OUTPUT_DIR):
            fpath = os.path.join(OUTPUT_DIR, fname)
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


_harness_checklist = PreCompletionChecklistMiddleware()
_harness_sim = VirtualVoidSimulator()
_silk_context = SilkLinkContextMiddleware()
_boundary_hook = AquaponicsBoundaryHook()
_loop_detector = LoopDetectionMiddleware(max_attempts=5)

_silk_context.bulk_update({
    "silk_strand_0_resistance": {"value": 3.1, "unit": "ohm"},
    "silk_strand_1_resistance": {"value": 3.2, "unit": "ohm"},
    "silk_strand_2_resistance": {"value": 3.0, "unit": "ohm"},
    "silk_strand_3_resistance": {"value": 3.2, "unit": "ohm"},
    "silk_strand_4_resistance": {"value": 3.4, "unit": "ohm"},
    "silk_strand_5_resistance": {"value": 3.1, "unit": "ohm"},
    "silk_total_resistance": {"value": 12.5, "unit": "ohm"},
    "aqua_ph": {"value": 6.8, "unit": "pH"},
    "aqua_temperature": {"value": 22.0, "unit": "°C"},
    "aqua_dissolved_oxygen": {"value": 7.5, "unit": "ppm"},
    "aqua_ammonia": {"value": 0.1, "unit": "ppm"},
    "aqua_pump_cycles": {"value": 0, "unit": "cycles/hr"},
    "aqua_water_level": {"value": 85.0, "unit": "%"},
    "flywheel_rpm": {"value": 3500, "unit": "RPM"},
    "flywheel_energy": {"value": 120.0, "unit": "Wh"},
    "flywheel_temperature": {"value": 38.0, "unit": "°C"},
    "flywheel_vibration": {"value": 0.8, "unit": "g"},
})


@app.route("/api/harness/status")
def harness_status():
    state = _harness_sim.get_state()
    checklist_report = _harness_checklist.run_checklist(state)
    return jsonify({
        "success": True,
        "environment_state": state,
        "checklist": checklist_report.to_dict(),
        "loop_detector": _loop_detector.get_stats(),
        "boundary_hook": _boundary_hook.get_stats(),
        "context": _silk_context.get_context_stats(),
    })


@app.route("/api/harness/check", methods=["POST"])
def harness_check():
    data = request.json or {}
    action = data.get("action", {})
    sim_result = _harness_sim.simulate_action(action)
    loop_check = _loop_detector.check_action(action)
    boundary_check = _boundary_hook.intercept_action(action, _harness_sim.get_state())

    return jsonify({
        "success": True,
        "simulation": sim_result,
        "loop_risk": loop_check,
        "boundary_check": boundary_check,
    })


@app.route("/api/harness/execute", methods=["POST"])
def harness_execute():
    data = request.json or {}
    action = data.get("action", {})

    boundary_check = _boundary_hook.intercept_action(action, _harness_sim.get_state())
    if not boundary_check["allowed"]:
        return jsonify({
            "success": False,
            "blocked_by": "boundary_hook",
            "boundary_check": boundary_check,
        }), 400

    loop_check = _loop_detector.check_action(action)
    if loop_check["risk_level"] == "blocked":
        return jsonify({
            "success": False,
            "blocked_by": "loop_detector",
            "loop_check": loop_check,
        }), 400

    checklist_report = _harness_checklist.run_checklist(_harness_sim.get_state(), action)
    if checklist_report.overall_verdict.value != "PASS":
        return jsonify({
            "success": False,
            "blocked_by": "checklist",
            "checklist": checklist_report.to_dict(),
        }), 400

    result = _harness_sim.apply_action(action)
    loop_alert = _loop_detector.record_action(
        action,
        result_value=action.get("result_value"),
    )

    response = {
        "success": result["applied"],
        "result": result,
        "checklist": checklist_report.to_dict(),
    }
    if loop_alert:
        response["loop_alert"] = loop_alert.to_dict()

    return jsonify(response)


@app.route("/api/harness/loops")
def harness_loops():
    return jsonify({
        "success": True,
        "active_alerts": _loop_detector.get_active_alerts(),
        "stats": _loop_detector.get_stats(),
    })


@app.route("/api/harness/loops/resolve", methods=["POST"])
def harness_resolve_loop():
    data = request.json or {}
    alert_id = data.get("alert_id", "")
    resolved = _loop_detector.resolve_alert(alert_id)
    return jsonify({"success": resolved})


@app.route("/api/harness/sensors")
def harness_sensors():
    return jsonify({
        "success": True,
        "sensors": _silk_context.get_all_readings(),
        "context_stats": _silk_context.get_context_stats(),
    })


@app.route("/api/harness/sensors/update", methods=["POST"])
def harness_update_sensor():
    data = request.json or {}
    sensor_id = data.get("sensor_id", "")
    value = data.get("value")
    unit = data.get("unit", "")

    if not sensor_id or value is None:
        return jsonify({"error": "sensor_id and value required"}), 400

    _silk_context.register_sensor(sensor_id, float(value), unit)

    section = None
    updates = {}
    if "aqua" in sensor_id.lower():
        section = "aquaponics"
        if "ph" in sensor_id.lower():
            updates["ph"] = float(value)
        elif "temp" in sensor_id.lower():
            updates["temperature_c"] = float(value)
        elif "oxygen" in sensor_id.lower():
            updates["dissolved_oxygen_ppm"] = float(value)
        elif "ammonia" in sensor_id.lower():
            updates["ammonia_ppm"] = float(value)
        elif "pump" in sensor_id.lower():
            updates["pump_cycles_this_hour"] = int(value)
        elif "water" in sensor_id.lower():
            updates["water_level_pct"] = float(value)
    elif "flywheel" in sensor_id.lower():
        section = "flywheel"
        if "rpm" in sensor_id.lower():
            updates["rpm"] = float(value)
        elif "energy" in sensor_id.lower():
            updates["energy_reserve_wh"] = float(value)
        elif "temp" in sensor_id.lower():
            updates["temperature_c"] = float(value)
        elif "vibration" in sensor_id.lower():
            updates["vibration_g"] = float(value)
    elif "silk" in sensor_id.lower():
        section = "silk_wiring"
        if "total" in sensor_id.lower():
            updates["total_resistance_ohm"] = float(value)
        elif "delta" in sensor_id.lower():
            updates["resistance_delta_ohm"] = float(value)

    if section and updates:
        _harness_sim.set_state(section, updates)

    return jsonify({"success": True, "sensor_id": sensor_id, "value": float(value)})


@app.route("/api/harness/context", methods=["POST"])
def harness_context():
    data = request.json or {}
    base_prompt = data.get("prompt", "You are a Plankton EA agent operating on the Orin.")
    injected = _silk_context.inject_context(base_prompt)
    return jsonify({"success": True, "injected_prompt": injected})


@app.route("/api/harness/params")
def harness_params():
    return jsonify({
        "success": True,
        "params": _harness_checklist.get_params(),
    })


@app.route("/api/harness/params/update", methods=["POST"])
def harness_update_params():
    data = request.json or {}
    section = data.get("section", "")
    updates = data.get("updates", {})
    if not section or not updates:
        return jsonify({"error": "section and updates required"}), 400
    ok = _harness_checklist.update_params(section, updates)
    return jsonify({"success": ok})


_start_time = __import__("time").time()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
