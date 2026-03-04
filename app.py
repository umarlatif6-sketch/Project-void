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
from void_engine.chaos_test import NitrogenLeakChaosTest
from void_engine.adriana_transpiler import AdrianaTranspiler
from void_engine.aljabr_transpiler import AlJabrTranspiler
from void_engine.consensus import ConsensusEngine
from void_engine.wallet import AlJabrWalletMiddleware
from void_engine.diagnostics import DiagnosticEngine, SOVEREIGN_WARRANTY
from void_engine.rituals import RitualHistory, AutoHealDaemon, RITUAL_TYPES
from void_engine.chronicle import RootChronicle
from void_engine.founder_certs import create_founder_cert, batch_generate_certs, FOUNDER_ROOT_HASH
from void_engine.divided_protocol import DividedProtocol
from void_engine.beehive import BeehiveProtocol, MeshRouter, MeshPacket, simulate_two_node_exchange, _sanitize_for_json
from void_engine.kinetic import KineticTransceiver, EXERCISE_WEIGHTS
from void_engine.biological import BiologicalTransceiver
from void_engine.silt_ledger import SiltLedger
from void_engine.resonance_contract import ResonanceContract
from generate_carriers import generate_custom_carrier, estimate_carrier_capacity, ALL_STYLES

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
    vortex = bool(data.get("vortex", False))
    chirp_sync = bool(data.get("chirp_sync", False))

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
            hash_key = encode_stereo(carrier_path, compressed, name, ext, output_path, lsb_depth, jitter=jitter, vortex=vortex, chirp_sync=chirp_sync)
        else:
            hash_key = encode(carrier_path, compressed, name, ext, output_path, lsb_depth, jitter=jitter, vortex=vortex, chirp_sync=chirp_sync)

        scatter_mode = "chirp_sync" if chirp_sync else ("vortex" if vortex else ("jitter" if jitter else "linear"))
        _log_operation("ENCODE", output_name, hash_key, f"LSB{lsb_depth}/{scatter_mode}")

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

_chaos_test = NitrogenLeakChaosTest(_harness_sim, _harness_checklist, _boundary_hook, _loop_detector)
_adriana = AdrianaTranspiler()
_aljabr = AlJabrTranspiler()
_wallet = AlJabrWalletMiddleware(initial_balance=50.0)
_diagnostics = DiagnosticEngine(_harness_sim, wallet=_wallet)
_ritual_history = RitualHistory(_harness_sim, wallet=_wallet)
_chronicle = RootChronicle(machine_id=_ritual_history.machine_id)
_consensus = ConsensusEngine(_harness_sim, _aljabr, _boundary_hook, _loop_detector, wallet=_wallet, chronicle=_chronicle)
_auto_heal = AutoHealDaemon(_diagnostics, _harness_sim, wallet=_wallet, ritual_history=_ritual_history)
_divided = DividedProtocol(_diagnostics, _harness_sim, chronicle=_chronicle, wallet=_wallet)
_beehive = BeehiveProtocol(machine_id="VOID-4000-PRIMARY")
_mesh_router = MeshRouter(_beehive)
_kinetic = KineticTransceiver(wallet=_wallet, chronicle=_chronicle)
_biological = BiologicalTransceiver()
_silt_ledger = SiltLedger(node_id=_beehive.node_id)
_resonance_contract = ResonanceContract(
    wallet=_wallet,
    kinetic=_kinetic,
    biological=_biological,
    beehive=_beehive,
    silt_ledger=_silt_ledger,
)

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
    "pressure_internal": {"value": 1.0, "unit": "atm"},
    "pressure_external": {"value": 1.0, "unit": "atm"},
    "air_curtain_velocity": {"value": 0.0, "unit": "m/s"},
    "nitrogen_boil_rate": {"value": 0.0, "unit": "rate"},
    "seal_integrity": {"value": 100.0, "unit": "%"},
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


@app.route("/api/harness/pressure")
def harness_pressure():
    state = _harness_sim.get_state()
    return jsonify({
        "success": True,
        "pressure": state.get("pressure", {}),
    })


@app.route("/api/harness/air-curtain", methods=["POST"])
def harness_air_curtain():
    data = request.json or {}
    action = data.get("action", "activate")
    velocity = float(data.get("velocity_ms", 15.0))

    if action == "activate":
        result = _harness_sim.activate_air_curtain(velocity)
        _silk_context.register_sensor("air_curtain_velocity", velocity, "m/s")
        return jsonify({"success": True, **result})
    elif action == "deactivate":
        result = _harness_sim.deactivate_air_curtain()
        _silk_context.register_sensor("air_curtain_velocity", 0.0, "m/s")
        return jsonify({"success": True, **result})
    else:
        return jsonify({"error": "action must be 'activate' or 'deactivate'"}), 400


@app.route("/api/harness/nitrogen-boil", methods=["POST"])
def harness_nitrogen_boil():
    data = request.json or {}
    boil_rate = float(data.get("boil_rate", 0.1))
    result = _harness_sim.simulate_nitrogen_boil(boil_rate)

    _silk_context.register_sensor("pressure_internal", result["internal_pressure_atm"], "atm")
    _silk_context.register_sensor("nitrogen_boil_rate", boil_rate, "rate")
    _silk_context.register_sensor("seal_integrity", result["seal_integrity_pct"], "%")

    return jsonify({"success": True, **result})


@app.route("/api/harness/chaos-test", methods=["POST"])
def harness_chaos_test():
    data = request.json or {}
    steps = int(data.get("steps", 10))
    initial_rate = float(data.get("initial_boil_rate", 0.05))
    escalation = float(data.get("escalation_factor", 1.5))
    auto_respond = bool(data.get("auto_respond", True))

    if _chaos_test.is_running():
        return jsonify({"error": "A chaos test is already running"}), 400

    report = _chaos_test.run_test(
        total_steps=steps,
        initial_boil_rate=initial_rate,
        escalation_factor=escalation,
        auto_respond=auto_respond,
    )

    state = _harness_sim.get_state()
    pressure = state.get("pressure", {})
    _silk_context.register_sensor("pressure_internal", pressure.get("internal_pressure_atm", 1.0), "atm")
    _silk_context.register_sensor("air_curtain_velocity", pressure.get("air_curtain_velocity_ms", 0.0), "m/s")
    _silk_context.register_sensor("seal_integrity", pressure.get("seal_integrity_pct", 100.0), "%")
    _silk_context.register_sensor("nitrogen_boil_rate", pressure.get("nitrogen_boil_rate", 0.0), "rate")

    return jsonify({"success": True, "report": report.to_dict()})


@app.route("/api/harness/chaos-test/reports")
def harness_chaos_reports():
    limit = request.args.get("limit", 10, type=int)
    return jsonify({
        "success": True,
        "reports": _chaos_test.get_reports(limit),
        "latest": _chaos_test.get_latest_report(),
    })


@app.route("/api/harness/pressure/reset", methods=["POST"])
def harness_pressure_reset():
    _harness_sim.set_state("pressure", {
        "internal_pressure_atm": 1.0,
        "external_pressure_atm": 1.0,
        "air_curtain_velocity_ms": 0.0,
        "air_curtain_active": False,
        "nitrogen_boil_rate": 0.0,
        "seal_integrity_pct": 100.0,
    })
    _silk_context.register_sensor("pressure_internal", 1.0, "atm")
    _silk_context.register_sensor("pressure_external", 1.0, "atm")
    _silk_context.register_sensor("air_curtain_velocity", 0.0, "m/s")
    _silk_context.register_sensor("nitrogen_boil_rate", 0.0, "rate")
    _silk_context.register_sensor("seal_integrity", 100.0, "%")
    return jsonify({"success": True, "message": "Pressure system reset to nominal"})


@app.route("/api/harness/adriana/lexicon")
def adriana_lexicon():
    return jsonify({
        "success": True,
        "lexicon": _adriana.lexicon.get_lexicon_map(),
        "size": _adriana.lexicon.size,
        "stats": _adriana.stats,
    })


@app.route("/api/harness/adriana/transpile", methods=["POST"])
def adriana_transpile():
    data = request.json or {}
    expression = data.get("expression", "")
    if not expression:
        return jsonify({"error": "expression required"}), 400

    result = _adriana.transpile(expression)

    state = _harness_sim.get_state()
    dry_runs = []
    for cmd in result.commands:
        action = {"type": cmd.action_type, **cmd.params}
        checklist_report = _harness_checklist.run_checklist(state)
        boundary_check = _boundary_hook.check_boundaries(state)
        dry_runs.append({
            "action": action,
            "checklist_verdict": checklist_report.overall_verdict.value,
            "boundary_allowed": len(boundary_check) == 0 if boundary_check is not None else True,
            "boundary_violations": [{"rule": v.rule_name, "msg": v.message} for v in (boundary_check or [])],
        })

    return jsonify({
        "success": result.success,
        "result": result.to_dict(),
        "dry_runs": dry_runs,
        "dry_run_note": "Static state snapshot — multi-command dry-runs reflect current state, not sequential effects.",
    })


@app.route("/api/harness/adriana/execute", methods=["POST"])
def adriana_execute():
    data = request.json or {}
    expression = data.get("expression", "")
    if not expression:
        return jsonify({"error": "expression required"}), 400

    result = _adriana.transpile(expression)
    if not result.success:
        return jsonify({
            "success": False,
            "errors": result.errors,
            "result": result.to_dict(),
        })

    execution_results = []
    for cmd in result.commands:
        action = {"type": cmd.action_type, **cmd.params}

        state = _harness_sim.get_state()
        boundary_check = _boundary_hook.check_boundaries(state)
        if boundary_check:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "boundary_hook",
                "violations": [{"rule": v.rule_name, "msg": v.message} for v in boundary_check],
                "narrative": cmd.narrative,
            })
            continue

        loop_result = _loop_detector.record_action({"type": cmd.action_type, **cmd.params})
        if loop_result:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "loop_detector",
                "loop_alert": {"message": loop_result.message, "action": loop_result.action_signature},
                "narrative": cmd.narrative,
            })
            continue

        sim_result = _harness_sim.simulate_action(action)
        if sim_result.get("safe_to_execute"):
            _harness_sim.apply_action(action)
            execution_results.append({
                "action": action,
                "executed": True,
                "effects": sim_result.get("effects", []),
                "narrative": cmd.narrative,
            })
        else:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "checklist",
                "verdict": sim_result.get("checklist", {}).get("overall_verdict", "UNKNOWN"),
                "narrative": cmd.narrative,
            })

    all_executed = all(r["executed"] for r in execution_results)
    return jsonify({
        "success": all_executed,
        "result": result.to_dict(),
        "execution": execution_results,
        "partial": not all_executed and any(r["executed"] for r in execution_results),
    })


@app.route("/api/harness/aljabr/roots")
def aljabr_roots():
    return jsonify({
        "manifest": _aljabr.manifest.get_manifest_map(),
        "size": _aljabr.manifest.size,
        "patterns": _aljabr.patterns,
        "stats": _aljabr.stats,
    })


@app.route("/api/harness/aljabr/transpile", methods=["POST"])
def aljabr_transpile():
    data = request.json or {}
    expression = data.get("expression", "")
    if not expression:
        return jsonify({"error": "expression required"}), 400

    result = _aljabr.transpile(expression)

    dry_runs = []
    for cmd in result.commands:
        action = {"type": cmd.action_type, **cmd.params}
        sim_result = _harness_sim.simulate_action(action)

        state = _harness_sim.get_state()
        boundary_check = _boundary_hook.check_boundaries(state)

        dry_runs.append({
            "action": action,
            "narrative": cmd.narrative,
            "root": cmd.root,
            "pattern": cmd.pattern,
            "pattern_name": cmd.pattern_name,
            "checklist_verdict": sim_result.get("checklist", {}).get("overall_verdict", "UNKNOWN"),
            "safe_to_execute": sim_result.get("safe_to_execute", False),
            "boundary_allowed": len(boundary_check) == 0 if boundary_check is not None else True,
            "boundary_violations": [{"rule": v.rule_name, "msg": v.message} for v in (boundary_check or [])],
        })

    return jsonify({
        "success": result.success,
        "result": result.to_dict(),
        "dry_runs": dry_runs,
        "dry_run_note": "Static state snapshot — multi-command dry-runs reflect current state, not sequential effects.",
    })


@app.route("/api/harness/aljabr/execute", methods=["POST"])
def aljabr_execute():
    data = request.json or {}
    expression = data.get("expression", "")
    if not expression:
        return jsonify({"error": "expression required"}), 400

    result = _aljabr.transpile(expression)
    if not result.success:
        return jsonify({
            "success": False,
            "errors": result.errors,
            "result": result.to_dict(),
        })

    execution_results = []
    for cmd in result.commands:
        action = {"type": cmd.action_type, **cmd.params}

        state = _harness_sim.get_state()
        boundary_check = _boundary_hook.check_boundaries(state)
        if boundary_check:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "boundary_hook",
                "violations": [{"rule": v.rule_name, "msg": v.message} for v in boundary_check],
                "narrative": cmd.narrative,
                "root": cmd.root,
                "pattern": cmd.pattern,
            })
            continue

        loop_result = _loop_detector.record_action({"type": cmd.action_type, **cmd.params})
        if loop_result:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "loop_detector",
                "loop_alert": {"message": loop_result.message, "action": loop_result.action_signature},
                "narrative": cmd.narrative,
                "root": cmd.root,
                "pattern": cmd.pattern,
            })
            continue

        sim_result = _harness_sim.simulate_action(action)
        if sim_result.get("safe_to_execute"):
            _harness_sim.apply_action(action)
            execution_results.append({
                "action": action,
                "executed": True,
                "effects": sim_result.get("effects", []),
                "narrative": cmd.narrative,
                "root": cmd.root,
                "pattern": cmd.pattern,
            })
        else:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "checklist",
                "verdict": sim_result.get("checklist", {}).get("overall_verdict", "UNKNOWN"),
                "narrative": cmd.narrative,
                "root": cmd.root,
                "pattern": cmd.pattern,
            })

    all_executed = all(r["executed"] for r in execution_results)
    return jsonify({
        "success": all_executed,
        "result": result.to_dict(),
        "execution": execution_results,
        "partial": not all_executed and any(r["executed"] for r in execution_results),
    })


@app.route("/api/harness/consensus/run", methods=["POST"])
def consensus_run():
    try:
        result = _consensus.run_consensus()
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/harness/consensus/status")
def consensus_status():
    return jsonify({
        "night_cycle": _consensus.night_cycle_status,
        "history": _consensus.history,
    })


@app.route("/api/harness/consensus/night-cycle", methods=["POST"])
def consensus_night_cycle():
    data = request.json or {}
    action = data.get("action", "toggle")
    interval = data.get("interval", 300)

    if action == "start":
        result = _consensus.start_night_cycle(interval)
    elif action == "stop":
        result = _consensus.stop_night_cycle()
    else:
        if _consensus.night_cycle_status["active"]:
            result = _consensus.stop_night_cycle()
        else:
            result = _consensus.start_night_cycle(interval)

    return jsonify(result)


@app.route("/api/harness/wallet/status")
def wallet_status():
    return jsonify(_wallet.get_status())


@app.route("/api/harness/wallet/audit")
def wallet_audit():
    return jsonify(_wallet.audit())


@app.route("/api/harness/wallet/ledger")
def wallet_ledger():
    limit = request.args.get("limit", 20, type=int)
    return jsonify({"ledger": _wallet.get_ledger(limit)})


@app.route("/api/harness/wallet/earn", methods=["POST"])
def wallet_earn():
    data = request.json or {}
    source = data.get("source", "flywheel_excess")
    amount = data.get("amount", 10.0)
    state = _harness_sim.get_state()
    energy_pct = state["flywheel"]["energy_reserve_wh"] / 250.0
    result = _wallet.earn(source, amount, energy_pct, root_command="QSB.A")
    return jsonify(result)


@app.route("/api/harness/wallet/spend", methods=["POST"])
def wallet_spend():
    data = request.json or {}
    target = data.get("target", "ln2_refill")
    amount = data.get("amount")
    result = _wallet.spend(target, amount, root_command="QSB.D")
    return jsonify(result)


@app.route("/api/harness/wallet/freeze", methods=["POST"])
def wallet_freeze():
    data = request.json or {}
    action = data.get("action", "toggle")
    if action == "freeze":
        return jsonify(_wallet.freeze())
    elif action == "unfreeze":
        return jsonify(_wallet.unfreeze())
    else:
        if _wallet.frozen:
            return jsonify(_wallet.unfreeze())
        else:
            return jsonify(_wallet.freeze())


@app.route("/api/harness/diagnostics/scan", methods=["POST"])
def diagnostics_scan():
    try:
        report = _diagnostics.scan()
        return jsonify(report.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/harness/diagnostics/history")
def diagnostics_history():
    return jsonify({"history": _diagnostics.history})


@app.route("/api/harness/warranty")
def warranty():
    w = dict(SOVEREIGN_WARRANTY)
    w["machine_id"] = _ritual_history.machine_id
    return jsonify(w)


@app.route("/api/harness/rituals/perform", methods=["POST"])
def ritual_perform():
    data = request.json or {}
    ritual_type = data.get("ritual_type", "")
    operator_note = data.get("operator_note", "")
    if not ritual_type:
        return jsonify({"error": "ritual_type required"}), 400
    result = _ritual_history.perform_ritual(ritual_type, operator_note)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/harness/rituals/history")
def ritual_history_list():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"history": _ritual_history.get_history(limit), "machine_id": _ritual_history.machine_id})


@app.route("/api/harness/rituals/stats")
def ritual_stats():
    return jsonify(_ritual_history.get_stats())


@app.route("/api/harness/rituals/types")
def ritual_types():
    types = []
    for key, val in RITUAL_TYPES.items():
        types.append({"type": key, "name": val["name"], "root": val["root"], "visual": val["visual"], "color": val["color"], "intent": val["intent"], "description": val["description"]})
    return jsonify({"types": types})


@app.route("/api/harness/autoheal/scan", methods=["POST"])
def autoheal_scan():
    try:
        result = _auto_heal.scan_and_heal()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/harness/autoheal/status")
def autoheal_status():
    return jsonify(_auto_heal.get_status())


@app.route("/api/harness/autoheal/toggle", methods=["POST"])
def autoheal_toggle():
    data = request.json or {}
    interval = data.get("interval", 300)
    if _auto_heal.active:
        result = _auto_heal.stop()
    else:
        result = _auto_heal.start(interval)
    return jsonify(result)


@app.route("/api/harness/autoheal/alerts")
def autoheal_alerts():
    limit = request.args.get("limit", 20, type=int)
    return jsonify({"alerts": _auto_heal.get_alerts(limit)})


@app.route("/api/harness/autoheal/alerts/clear", methods=["POST"])
def autoheal_clear_alerts():
    return jsonify(_auto_heal.clear_alerts())


@app.route("/api/harness/machine-id")
def machine_id():
    return jsonify({"machine_id": _ritual_history.machine_id})


@app.route("/api/harness/chronicle/entries")
def chronicle_entries():
    limit = request.args.get("limit", 50, type=int)
    success_only = request.args.get("success_only", "false").lower() == "true"
    return jsonify({"entries": _chronicle.get_chronicle_entries(limit, success_only)})


@app.route("/api/harness/chronicle/stats")
def chronicle_stats():
    return jsonify(_chronicle.get_stats())


@app.route("/api/harness/chronicle/query", methods=["POST"])
def chronicle_query():
    state = _harness_sim.get_state()
    ancestors = _chronicle.query_ancestors(state)
    return jsonify({"matches": [m.to_dict() for m in ancestors]})


@app.route("/api/harness/chronicle/wisdom")
def chronicle_wisdom():
    state = _harness_sim.get_state()
    wisdom = _chronicle.get_wisdom_context(state)
    return jsonify(wisdom)


@app.route("/api/harness/chronicle/prophecy", methods=["POST"])
def chronicle_prophecy():
    state = _harness_sim.get_state()
    prophecies = _chronicle.predict_crisis(state)
    return jsonify({"prophecies": [p.to_dict() for p in prophecies]})


@app.route("/api/harness/chronicle/episodic")
def chronicle_episodic():
    domain = request.args.get("domain")
    hours = request.args.get("hours", 24, type=float)
    return jsonify({"readings": _chronicle.get_episodic_memory(domain, hours)})


@app.route("/api/harness/chronicle/export")
def chronicle_export():
    mark_founder = request.args.get("mark_founder", "false").lower() == "true"
    seed = _chronicle.export_genesis_seed(mark_founder=mark_founder)
    return jsonify(seed)


@app.route("/api/harness/chronicle/import", methods=["POST"])
def chronicle_import():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No seed data provided"}), 400
    result = _chronicle.import_genesis_seed(data)
    return jsonify(result)


@app.route("/api/harness/founder/status")
def founder_status():
    return jsonify(_chronicle.get_founder_status())


@app.route("/api/harness/founder/mark", methods=["POST"])
def founder_mark():
    result = _chronicle.mark_as_founder_wisdom()
    return jsonify(result)


@app.route("/api/harness/founder/cert", methods=["POST"])
def founder_generate_cert():
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id", 1)
    machine_hash = data.get("machine_hash", _ritual_history.machine_id)
    try:
        result = create_founder_cert(int(customer_id), machine_hash, OUTPUT_DIR)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/harness/founder/batch", methods=["POST"])
def founder_batch_certs():
    data = request.get_json(silent=True) or {}
    count = min(int(data.get("count", 100)), 100)
    base_hash = data.get("base_hash", _ritual_history.machine_id)
    try:
        result = batch_generate_certs(count, base_hash, OUTPUT_DIR)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/harness/founder/genesis-kit", methods=["POST"])
def founder_genesis_kit():
    _chronicle.mark_as_founder_wisdom()
    seed = _chronicle.export_genesis_seed(mark_founder=True)
    return jsonify({
        "success": True,
        "genesis_seed": seed,
        "founder_root_hash": FOUNDER_ROOT_HASH,
        "instructions": "Package this seed with genesis_init.sh and FOUNDER_CERT for each customer.",
    })


@app.route("/api/harness/divided/status")
def divided_status():
    return jsonify(_divided.get_readiness())


@app.route("/api/harness/divided/execute", methods=["POST"])
def divided_execute():
    data = request.json or {}
    carrier = data.get("carrier")
    payload = data.get("payload")
    lsb_depth = int(data.get("lsb_depth", 1))

    if not carrier or not payload:
        return jsonify({"error": "Carrier and payload files are required"}), 400

    carrier_path = os.path.join(INPUT_DIR, carrier)
    payload_path = os.path.join(INPUT_DIR, payload)

    if not os.path.exists(carrier_path):
        return jsonify({"error": f"Carrier file not found: {carrier}"}), 404
    if not os.path.exists(payload_path):
        return jsonify({"error": f"Payload file not found: {payload}"}), 404

    output_name = f"{os.path.splitext(carrier)[0]}_void.wav"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    try:
        result = _divided.execute(
            carrier_path, payload_path,
            lsb_depth=lsb_depth,
            output_path=output_path,
            low_power=_low_power_mode,
        )
        status_code = 200 if result["success"] else 422
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate-carrier", methods=["POST"])
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


@app.route("/api/carrier-estimate")
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


@app.route("/api/mesh/connect", methods=["POST"])
def mesh_connect():
    try:
        _wallet.debit({"type": "mesh_connect"})
        result = _beehive.connect()
        _chronicle.record_consensus(
            {
                "consensus_command": "WSL.A",
                "consensus_intent": "Mesh connect — entering Sovereign Mesh Mode",
                "outcome": f"Node {_beehive.node_id[:8]} connected, state={_beehive.mesh_state}",
                "success": True,
                "timestamp": __import__("time").time(),
                "energy_pct": 0.0,
                "wallet": {"balance": _wallet.balance},
            },
            {},
        )
        return jsonify({"success": True, "node_id": result["node_id"], "state": result["state"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/mesh/disconnect", methods=["POST"])
def mesh_disconnect():
    try:
        _wallet.debit({"type": "mesh_disconnect"})
        result = _beehive.disconnect()
        _chronicle.record_consensus(
            {
                "consensus_command": "WSL.D",
                "consensus_intent": "Mesh disconnect — leaving Sovereign Mesh",
                "outcome": f"Left mesh from {result['previous_state']} state",
                "success": True,
                "timestamp": __import__("time").time(),
                "energy_pct": 0.0,
                "wallet": {"balance": _wallet.balance},
            },
            {},
        )
        return jsonify({"success": True, "previous_state": result["previous_state"], "neighbors_released": result["neighbors_released"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/mesh/status")
def mesh_status():
    try:
        status = _beehive.get_status()
        return jsonify({"success": True, **status})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/mesh/send", methods=["POST"])
def mesh_send():
    data = request.json or {}
    message = data.get("message", "")
    dest_id = data.get("dest_id", "")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        debit_result = _wallet.debit({"type": "mesh_send"})
        payload = message.encode("utf-8")

        if dest_id:
            packet = _mesh_router.create_packet(dest_id, payload)
        else:
            packet = MeshPacket.create_broadcast(_beehive.node_id, payload)
            _beehive.stats["packets_sent"] += 1
            _beehive._log_event("BROADCAST_SENT", f"Broadcast {len(payload)} bytes")

        return jsonify({
            "success": True,
            "packet": packet.to_dict(),
            "wallet": debit_result,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/mesh/neighbors")
def mesh_neighbors():
    try:
        status = _beehive.get_status()
        return jsonify({"success": True, "neighbors": status["neighbors"], "count": status["neighbor_count"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/mesh/handshake", methods=["POST"])
def mesh_handshake():
    try:
        debit_result = _wallet.debit({"type": "mesh_handshake"})
        pulse = _beehive.generate_handshake_pulse(duration=0.5)
        detection = _beehive.detect_neighbor(pulse)
        auth = _beehive.authenticate_phase(pulse)

        return jsonify(_sanitize_for_json({
            "success": True,
            "detection": detection,
            "authentication": auth,
            "pulse_samples": len(pulse),
            "wallet": debit_result,
        }))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/mesh/activity")
def mesh_activity():
    limit = request.args.get("limit", 50, type=int)
    try:
        log = _beehive.get_activity_log(limit)
        return jsonify({"success": True, "activity": log, "count": len(log)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/mesh/simulate", methods=["POST"])
def mesh_simulate():
    try:
        result = simulate_two_node_exchange()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/kinetic/log-set", methods=["POST"])
def kinetic_log_set():
    try:
        data = request.get_json(force=True)
        exercise = data.get("exercise", "push_up")
        reps = int(data.get("reps", 0))
        duration_sec = float(data.get("duration_sec", 30.0))
        heart_rate = int(data.get("heart_rate", 0))
        result = _kinetic.log_set(exercise, reps, duration_sec, heart_rate)
        if "error" in result:
            return jsonify(result), 400
        _silt_ledger.add_block(
            {"type": "kinetic_set", "exercise": exercise, "reps": reps, "cc_earned": result.get("cc_earned", 0)},
            _beehive.node_id,
            _kinetic.get_status().get("stability_score", 0),
            _biological.get_health_score().get("composite_score", 0)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/kinetic/status")
def kinetic_status():
    status = _kinetic.get_status()
    status["exercises"] = list(EXERCISE_WEIGHTS.keys())
    return jsonify(status)


@app.route("/api/kinetic/history")
def kinetic_history():
    return jsonify(_kinetic.get_history())


@app.route("/api/biological/update-sensors", methods=["POST"])
def biological_update_sensors():
    try:
        data = request.get_json(force=True)
        result = _biological.update_sensors(
            water_level=data.get("water_level"),
            temperature=data.get("temperature"),
            ph=data.get("ph"),
            dissolved_oxygen=data.get("dissolved_oxygen")
        )
        if result.get("governance_triggered"):
            for p in result.get("governance_proposals", []):
                desc = p.get("intervention", p.get("proposal", "biological intervention"))
                _silt_ledger.propose_vote(str(desc), _beehive.node_id)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/biological/impedance")
def biological_impedance():
    impedance = _biological.calculate_impedance()
    return jsonify({
        "whale_shelf": impedance.whale_multiplier,
        "bird_shelf": impedance.bird_multiplier,
        "insect_shelf": impedance.insect_multiplier,
        "overall_attenuation": impedance.overall_attenuation,
        "alerts": impedance.alerts,
    })


@app.route("/api/biological/health")
def biological_health():
    return jsonify(_biological.get_health_score())


@app.route("/api/biological/govern", methods=["POST"])
def biological_govern():
    try:
        data = request.get_json(force=True) if request.data else {}
        intervention = data.get("intervention", "water_refill")
        reason = data.get("reason", "Manual governance trigger")
        result = _biological.trigger_governance_vote(intervention, reason)
        if result.get("proposal"):
            desc = result["proposal"].get("intervention", intervention)
            prop_result = _silt_ledger.propose_vote(str(desc), _beehive.node_id)
            result["ledger_proposal"] = prop_result
        _silt_ledger.add_block(
            {"type": "governance_trigger", "intervention": intervention},
            _beehive.node_id,
            _kinetic.get_status().get("stability_score", 0),
            _biological.get_health_score().get("composite_score", 0)
        )
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/ledger/chain")
def ledger_chain():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"blocks": _silt_ledger.get_chain(limit)})


@app.route("/api/ledger/status")
def ledger_status():
    status = _silt_ledger.get_status()
    integrity = status.get("integrity", {})
    kinetic_w = _kinetic.get_status().get("stability_score", 0)
    biological_w = _biological.get_health_score().get("composite_score", 0)
    honor = 1.0
    if status.get("relay_honor_scores"):
        node_honor = status["relay_honor_scores"].get(_beehive.node_id[:8], None)
        if node_honor is not None:
            honor = node_honor
    status["integrity_valid"] = integrity.get("valid", False)
    status["relay_honor"] = status.get("relay_honor_scores", {})
    status["voting_weight"] = {
        "kinetic": kinetic_w,
        "biological": biological_w,
        "relay": honor,
        "total": kinetic_w * 0.4 + biological_w * 0.4 + honor * 0.2,
    }
    return jsonify(status)


@app.route("/api/ledger/vote", methods=["POST"])
def ledger_vote():
    try:
        data = request.get_json(force=True)
        proposal_id = data.get("proposal_id", "")
        vote = data.get("vote", "yes")
        if isinstance(vote, bool):
            vote = "yes" if vote else "no"
        kinetic_w = _kinetic.get_status().get("stability_score", 0)
        biological_w = _biological.get_health_score().get("composite_score", 0)
        result = _silt_ledger.cast_vote(
            proposal_id, _beehive.node_id, vote,
            kinetic_weight=kinetic_w,
            biological_weight=biological_w
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/ledger/votes")
def ledger_votes():
    return jsonify({"proposals": _silt_ledger.get_proposals()})


@app.route("/api/resonance/evaluate")
def resonance_evaluate():
    try:
        state = _resonance_contract.evaluate()
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/resonance/axioms")
def resonance_axioms():
    return jsonify(_resonance_contract.get_axioms())


@app.route("/api/resonance/status")
def resonance_status():
    try:
        return jsonify(_resonance_contract.get_status())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/resonance/harvest-bloom", methods=["POST"])
def resonance_harvest_bloom():
    try:
        result = _resonance_contract.harvest_bloom()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/resonance/history")
def resonance_history():
    limit = request.args.get("limit", 20, type=int)
    return jsonify(_resonance_contract.get_history(limit))


@app.route("/api/blueprint/specs")
def blueprint_specs():
    components = [
        {"name": "304 Brushed Steel sheet (outer skin)", "min": 40, "max": 60, "role": "Whale Shelf carrier @ 108 Hz"},
        {"name": "Aerospace Aluminum frame stock", "min": 30, "max": 50, "role": "Skeleton @ 216 Hz sub-harmonic"},
        {"name": "18mm Plywood (alternative chassis)", "min": 15, "max": 25, "role": "Budget chassis option"},
        {"name": "Polypropylene internal lining", "min": 10, "max": 15, "role": "Insect Silt preservation @ 12 kHz"},
        {"name": "Silk-wrapped silver wiring (1m)", "min": 20, "max": 35, "role": "Sapphire Thread @ 432 Hz"},
        {"name": "15kg Weighted Plate (flywheel)", "min": 25, "max": 40, "role": "Kinetic energy storage / Seismic Antenna"},
        {"name": "High-speed ceramic bearings", "min": 15, "max": 25, "role": "Flywheel mount"},
        {"name": "Brushless DC Motor (BLDC)", "min": 30, "max": 50, "role": "Flywheel driver / generator"},
        {"name": "NVIDIA Jetson Orin Nano", "min": 200, "max": 250, "role": "Real-Time Pose Estimation (The Brain)"},
        {"name": "USB Webcam / CSI Camera", "min": 20, "max": 40, "role": "Calisthenics tracking"},
        {"name": "Piezoelectric Transducers (x10)", "min": 8, "max": 15, "role": "Resonance pulse generation"},
        {"name": "Epoxy adhesive", "min": 5, "max": 10, "role": "Transducer mounting"},
        {"name": "Polyurethane foam insulation", "min": 10, "max": 20, "role": "12 kHz high-pass filter"},
        {"name": "Miscellaneous (screws, solder, connectors)", "min": 15, "max": 25, "role": "Assembly hardware"},
    ]
    total_min = sum(c["min"] for c in components)
    total_max = sum(c["max"] for c in components)
    resonance_table = [
        {"component": "Outer Skin", "material": "304 Brushed Steel", "frequency_hz": 108, "role": "Whale Shelf (Sub-bass)"},
        {"component": "Internal Frame", "material": "Aerospace Aluminum", "frequency_hz": 216, "role": "Skeleton (1st Sub-harmonic)"},
        {"component": "Wiring", "material": "Spun Silk & Silver", "frequency_hz": 432, "role": "Sapphire Thread (Data Core)"},
        {"component": "Liquid Buffer", "material": "Salt Water / Aquaponics", "frequency_hz": 864, "role": "Mid-Shelf (1st Overtone)"},
        {"component": "Insulation", "material": "Polyurethane Foam", "frequency_hz": 12000, "role": "Masking floor for Insect Silt"},
    ]
    return jsonify({
        "components": components,
        "pirate_build_total": {"min": total_min, "max": total_max, "currency": "GBP"},
        "sovereign_price": {"amount": 25000, "currency": "GBP"},
        "resonance_table": resonance_table,
        "quarter_wave_length_cm": 19.8,
        "base_frequency_hz": 432,
    })


@app.route("/api/aljabr/protocol")
def aljabr_protocol():
    from void_engine.al_jabr_286 import get_protocol_info, fatiha_286_hexdigest
    info = get_protocol_info()
    test_hash = fatiha_286_hexdigest(b"PROJECT VOID")
    info["sample_hash"] = test_hash
    info["sample_input"] = "PROJECT VOID"
    info["hash_length_chars"] = len(test_hash)
    info["status"] = "ACTIVE"
    return jsonify(info)


_start_time = __import__("time").time()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
