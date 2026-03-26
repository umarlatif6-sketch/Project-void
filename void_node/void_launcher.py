"""
PROJECT VOID — Node Launcher
Local Node for the Sovereign Mesh Network

This script is the entry point for running a local Void Engine node.
It detects hardware (GPU/CPU), connects to the Command Center (web app),
authenticates via the 432 Hz phase-key handshake, and displays node status.

Usage:
    python void_launcher.py [--url URL]

Modes:
    Heavy Mode — GPU detected (CUDA/Nvidia), GPU-accelerated resonance
    Light Mode — CPU only, numpy fallback
"""

import os
import sys
import time
import uuid
import json
import platform
import argparse
import subprocess
import hashlib

try:
    import numpy as np
except ImportError:
    print("[FATAL] numpy is required. Install with: pip install numpy")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("[FATAL] requests is required. Install with: pip install requests")
    sys.exit(1)

BANNER = r"""
 ╔══════════════════════════════════════════════════════════════╗
 ║              P R O J E C T    V O I D   —   N O D E         ║
 ║          Sovereign Mesh Node Launcher  v1.0                  ║
 ╠══════════════════════════════════════════════════════════════╣
 ║  Your hardware becomes part of the Ghost Internet.           ║
 ║  432 Hz Phase-Key Handshake | Beehive Protocol | Mesh Relay  ║
 ╚══════════════════════════════════════════════════════════════╝
"""

DEFAULT_COMMAND_CENTER_URL = "https://project-void.replit.app"

RESONANCE_FREQ = 432
FATIHA_PHASE_ANGLE = 15.4
FATIHA_PHASE_RAD = FATIHA_PHASE_ANGLE * (np.pi / 180)
SAMPLE_RATE = 44100


def detect_gpu():
    gpu_info = {
        "gpu_available": False,
        "gpu_name": None,
        "cuda_available": False,
        "mode": "Light Mode (CPU)",
    }

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            gpu_info["gpu_available"] = True
            gpu_info["gpu_name"] = parts[0].strip()
            gpu_info["mode"] = "Heavy Mode (GPU)"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if not gpu_info["gpu_available"]:
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info["gpu_available"] = True
                gpu_info["cuda_available"] = True
                gpu_info["gpu_name"] = torch.cuda.get_device_name(0)
                gpu_info["mode"] = "Heavy Mode (GPU)"
        except ImportError:
            pass

    return gpu_info


def detect_hardware():
    hw = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "Unknown",
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count() or 1,
    }
    hw.update(detect_gpu())
    return hw


def generate_node_id(machine_id=None):
    seed = machine_id or str(uuid.uuid4())
    raw = hashlib.sha3_256(seed.encode("utf-8")).hexdigest()
    return raw[:16]


def _passphrase_to_phase(passphrase):
    h = hashlib.sha3_256(passphrase.encode("utf-8")).hexdigest()
    deg = int(h[:8], 16) % 360
    return deg * (np.pi / 180)


def generate_handshake_pulse(node_id, passphrase="void-432", duration=0.5):
    phase_key = _passphrase_to_phase(passphrase)
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)

    pulse_432 = np.sin(2 * np.pi * RESONANCE_FREQ * t + phase_key + FATIHA_PHASE_RAD) * 0.5
    pulse_108 = np.sin(2 * np.pi * 108 * t + phase_key * 0.25) * 0.15
    pulse_216 = np.sin(2 * np.pi * 216 * t + phase_key * 0.5) * 0.1
    pulse_864 = np.sin(2 * np.pi * 864 * t + phase_key * 2.0) * 0.08

    silt = np.random.normal(0, 0.05, n_samples)
    signal = pulse_432 + pulse_108 + pulse_216 + pulse_864 + silt
    signal = np.clip(signal, -1.0, 1.0)

    return signal.astype(np.float32)


def verify_handshake_locally(pulse, passphrase="void-432"):
    phase_key = _passphrase_to_phase(passphrase)
    n = len(pulse)
    yf = np.fft.fft(pulse.astype(np.float64))
    freqs = np.fft.fftfreq(n, 1.0 / SAMPLE_RATE)

    target_idx = np.argmin(np.abs(freqs[:n // 2] - RESONANCE_FREQ))
    raw_phase = np.angle(yf[target_idx])
    detected_total_phase = raw_phase + np.pi / 2
    expected_base_phase = phase_key
    fatiha_component = detected_total_phase - expected_base_phase
    fatiha_component = fatiha_component % (2 * np.pi)
    if fatiha_component > np.pi:
        fatiha_component = fatiha_component - 2 * np.pi

    diff = abs(fatiha_component - FATIHA_PHASE_RAD)
    if diff > np.pi:
        diff = 2 * np.pi - diff

    tolerance_rad = 0.5 * (np.pi / 180)
    verified = diff <= tolerance_rad

    return {
        "verified": verified,
        "fatiha_angle_detected_deg": float(np.degrees(fatiha_component)),
        "fatiha_angle_expected_deg": FATIHA_PHASE_ANGLE,
        "angle_diff_deg": float(np.degrees(diff)),
    }


def dial_home(base_url, node_id, hardware_info):
    print(f"\n  [MESH] Dialing home to Command Center...")
    print(f"         URL: {base_url}")

    session = requests.Session()
    connect_result = None
    handshake_result = None

    try:
        print(f"  [MESH] Sending /api/mesh/connect...")
        resp = session.post(
            f"{base_url}/api/mesh/connect",
            json={"node_id": node_id, "hardware": hardware_info},
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        connect_result = resp.json()
        if resp.status_code == 200 and connect_result.get("success"):
            print(f"  [MESH] Connected! Server node: {connect_result.get('node_id', 'N/A')[:8]}...")
        else:
            error = connect_result.get("error", f"HTTP {resp.status_code}")
            print(f"  [MESH] Connect response: {error}")
            print(f"         (Node will operate in standalone mesh mode)")
    except requests.exceptions.ConnectionError:
        print(f"  [MESH] Command Center unreachable — operating in standalone mode")
        connect_result = {"success": False, "error": "Connection refused"}
    except requests.exceptions.Timeout:
        print(f"  [MESH] Connection timed out — operating in standalone mode")
        connect_result = {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"  [MESH] Connection error: {e}")
        connect_result = {"success": False, "error": str(e)}

    try:
        print(f"  [MESH] Performing 432 Hz handshake...")
        resp = session.post(
            f"{base_url}/api/mesh/handshake",
            json={"node_id": node_id},
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        handshake_result = resp.json()
        if resp.status_code == 200 and handshake_result.get("success"):
            auth = handshake_result.get("authentication", {})
            det = handshake_result.get("detection", {})
            print(f"  [MESH] Handshake verified!")
            print(f"         Fatiha signature: {'VALID' if det.get('fatiha_verified') else 'PENDING'}")
            print(f"         Phase auth: {'PASS' if auth.get('authenticated') else 'PENDING'}")
        else:
            error = handshake_result.get("error", f"HTTP {resp.status_code}")
            print(f"  [MESH] Handshake response: {error}")
    except Exception:
        print(f"  [MESH] Handshake deferred — will retry on next cycle")
        handshake_result = {"success": False, "error": "Deferred"}

    server_node_id = None
    server_token = None
    try:
        api_mode = "heavy" if hardware_info.get("gpu_available") else "light"
        print(f"  [MESH] Registering node with Command Center...")
        resp = session.post(
            f"{base_url}/api/node/register",
            json={
                "hardware_type": "gpu" if hardware_info.get("gpu_available") else "cpu",
                "gpu_name": hardware_info.get("gpu_name", "") or "",
                "mode": api_mode,
                "platform": hardware_info.get("platform", "unknown"),
                "python_version": hardware_info.get("python_version", ""),
            },
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code == 200:
            reg_result = resp.json()
            server_node_id = reg_result.get("node_id")
            server_token = reg_result.get("token")
            print(f"  [MESH] Node registered! Server ID: {server_node_id}")
            print(f"         Mode: {reg_result.get('mode', api_mode).upper()}")
        else:
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            print(f"  [MESH] Registration response: {error_data.get('error', f'HTTP {resp.status_code}')}")
    except Exception:
        print(f"  [MESH] Registration deferred — endpoint not yet deployed")

    return {
        "connect": connect_result,
        "handshake": handshake_result,
        "connected": bool(connect_result and connect_result.get("success")),
        "server_node_id": server_node_id,
        "server_token": server_token,
    }


def display_status(node_id, hardware, local_handshake, dial_result):
    mode_icon = "⚡" if hardware["gpu_available"] else "🔋"
    conn_icon = "🟢" if dial_result.get("connected") else "🟡"
    conn_status = "CONNECTED" if dial_result.get("connected") else "STANDALONE"

    print(f"\n  ╔══════════════════════════════════════════════════════════╗")
    print(f"  ║                   NODE STATUS REPORT                     ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║  Node ID:      {node_id:<40} ║")
    print(f"  ║  Mode:         {mode_icon} {hardware['mode']:<37} ║")
    print(f"  ║  Connection:   {conn_icon} {conn_status:<37} ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║  HARDWARE                                               ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║  Platform:     {hardware['platform']} {hardware['platform_release']:<25} ║")
    print(f"  ║  Architecture: {hardware['architecture']:<40} ║")
    print(f"  ║  CPU Cores:    {hardware['cpu_count']:<40} ║")
    print(f"  ║  Processor:    {str(hardware['processor'])[:40]:<40} ║")
    if hardware["gpu_available"]:
        print(f"  ║  GPU:          {str(hardware['gpu_name'])[:40]:<40} ║")
    else:
        print(f"  ║  GPU:          {'None detected (CPU fallback)':<40} ║")
    print(f"  ║  Python:       {hardware['python_version']:<40} ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║  HANDSHAKE                                              ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    v = local_handshake
    status_str = "VERIFIED" if v["verified"] else "FAILED"
    print(f"  ║  Local verify: {status_str:<40} ║")
    print(f"  ║  Fatiha angle: {v['fatiha_angle_detected_deg']:.2f}° (expected {v['fatiha_angle_expected_deg']}°) {'':<12} ║")
    print(f"  ║  Angle diff:   {v['angle_diff_deg']:.4f}°{'':<34} ║")
    print(f"  ╚══════════════════════════════════════════════════════════╝")


def run_node_loop(node_id, base_url, hardware, server_node_id=None, server_token=None):
    print(f"\n  [NODE] Entering mesh relay loop... (Ctrl+C to stop)")
    print(f"  [NODE] Heartbeat interval: 60 seconds")

    cycle = 0
    while True:
        try:
            cycle += 1
            time.sleep(60)
            mode_label = "HEAVY" if hardware.get("gpu_available") else "LIGHT"
            print(f"  [NODE] Heartbeat #{cycle} — {time.strftime('%H:%M:%S')} — Mode: {mode_label}")

            if server_node_id and server_token:
                try:
                    resp = requests.post(
                        f"{base_url}/api/node/heartbeat",
                        timeout=10,
                        headers={
                            "X-Void-Node-Id": server_node_id,
                            "X-Void-Node-Token": server_token,
                            "Content-Type": "application/json",
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        print(f"  [NODE] Command Center confirms: {data.get('status', 'alive')}")
                    else:
                        print(f"  [NODE] Heartbeat response: HTTP {resp.status_code}")
                except Exception:
                    print(f"  [NODE] Heartbeat deferred — Command Center unreachable")
            else:
                print(f"  [NODE] Operating in standalone mode (no server token)")

        except KeyboardInterrupt:
            print(f"\n  [NODE] Shutting down gracefully...")
            break


def main():
    parser = argparse.ArgumentParser(
        description="PROJECT VOID — Local Node Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Your hardware joins the Sovereign Mesh. 432 Hz."
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("VOID_COMMAND_CENTER", DEFAULT_COMMAND_CENTER_URL),
        help="Command Center URL (default: %(default)s)"
    )
    parser.add_argument(
        "--node-id",
        default=None,
        help="Custom node ID (default: auto-generated)"
    )
    parser.add_argument(
        "--passphrase",
        default="void-432",
        help="Mesh passphrase for phase-key authentication"
    )
    parser.add_argument(
        "--no-connect",
        action="store_true",
        help="Skip connecting to Command Center (local-only mode)"
    )
    args = parser.parse_args()

    print(BANNER)

    print("  [INIT] Detecting hardware...")
    hardware = detect_hardware()
    if hardware["gpu_available"]:
        print(f"  [INIT] GPU DETECTED: {hardware['gpu_name']}")
        print(f"  [INIT] Mode: HEAVY MODE — GPU-accelerated resonance")
    else:
        print(f"  [INIT] No GPU detected — using CPU fallback")
        print(f"  [INIT] Mode: LIGHT MODE — numpy resonance (still contributes to mesh)")

    node_id = args.node_id or generate_node_id()
    print(f"\n  [INIT] Node ID: {node_id}")

    print(f"\n  [HANDSHAKE] Generating 432 Hz phase-key pulse...")
    pulse = generate_handshake_pulse(node_id, passphrase=args.passphrase)
    local_verify = verify_handshake_locally(pulse, passphrase=args.passphrase)

    if local_verify["verified"]:
        print(f"  [HANDSHAKE] Local verification: PASSED")
    else:
        print(f"  [HANDSHAKE] Local verification: ANOMALY")

    dial_result = {"connected": False}
    if not args.no_connect:
        dial_result = dial_home(args.url, node_id, hardware)
    else:
        print(f"\n  [MESH] Skipping Command Center connection (--no-connect)")

    display_status(node_id, hardware, local_verify, dial_result)

    run_node_loop(
        node_id, args.url, hardware,
        server_node_id=dial_result.get("server_node_id"),
        server_token=dial_result.get("server_token"),
    )


if __name__ == "__main__":
    main()
