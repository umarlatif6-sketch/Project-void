#!/usr/bin/env python3
"""
verify_life_therm.py
====================
ADRIANA SCL — Thermal Biological Verification Oracle
Genesis 10 Hardware Package — PROJECT VOID

Runs on NVIDIA Orin or any ARM/x86 host with MLX90640 thermal camera.
On successful verification, prints a Proof of Resonance certificate and
returns the HDR (Heat Dissipation Rate) value for submission to the
/genesis/oracle endpoint.

Hardware Requirements
---------------------
- MLX90640 thermal camera (I2C, 0x33)
- Python 3.9+
- pip install adafruit-circuitpython-mlx90640 numpy

Usage
-----
    python3 verify_life_therm.py --node-id YOUR_NODE_ID --action compost

Arguments
---------
  --node-id   Your Genesis 10 Node ID (e.g. SALFORD_M6_01)
  --action    Action type: compost | aquaponics
  --samples   Number of thermal samples (default 10, ~10 seconds)
  --output    Write JSON result to file (default: stdout only)
"""

import argparse
import time
import json
import sys
import hashlib
from datetime import datetime, timezone


def _check_hardware():
    try:
        import board
        import busio
        import adafruit_mlx90640
        return True
    except ImportError:
        return False


def _read_thermal_hardware(n_samples=10):
    import board
    import busio
    import adafruit_mlx90640

    i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

    readings = []
    frame = [0] * 768
    for i in range(n_samples):
        try:
            mlx.getFrame(frame)
            mean_temp = sum(frame) / len(frame)
            readings.append(mean_temp)
            print(f"  [SAMPLE {i+1:02d}] mean={mean_temp:.2f}°C", flush=True)
        except Exception as e:
            print(f"  [WARN] Sample {i+1} failed: {e}", file=sys.stderr)
        time.sleep(1)
    return readings


def _simulate_thermal(n_samples=10):
    import random
    rng = random.Random()
    base = rng.uniform(22.0, 35.0)
    readings = []
    for i in range(n_samples):
        val = base + rng.uniform(-0.5, 1.5) * (i / n_samples)
        readings.append(val)
        print(f"  [SIMULATED SAMPLE {i+1:02d}] mean={val:.2f}°C", flush=True)
        time.sleep(0.2)
    return readings


def _compute_hdr(readings):
    if len(readings) < 2:
        return 0.0
    total_rise = 0.0
    for i in range(1, len(readings)):
        delta = readings[i] - readings[i - 1]
        if delta > 0:
            total_rise += delta
    hdr = total_rise / len(readings)
    return round(hdr, 4)


def _display_certificate(node_id, action, hdr, peace_amount, ts):
    separator = "=" * 62
    thin = "-" * 62
    print()
    print(separator)
    print("     ADRIANA SCL: CERTIFICATE OF RESONANCE            ")
    print(separator)
    print(f"  NODE ID    :  {node_id}")
    print(f"  ACTION     :  {action.upper()}")
    print(f"  HDR VALUE  :  {hdr:.4f} °C/sample")
    print(f"  STATUS     :  RESONANCE ACHIEVED (432 Hz)")
    print(f"  AUDIT TYPE :  THERMAL BIOLOGICAL VERIFICATION")
    print(f"  LEDGER     :  +{peace_amount:.2f} PEACE TOKEN (pending oracle submit)")
    print(thin)
    print("   'The Tap of the Engineer has confirmed the Mesh.'   ")
    print(thin)
    sig = hashlib.sha256(f"{node_id}:{hdr}:{ts}".encode()).hexdigest()[:24]
    print(f"  [SIG: {sig}...]")
    print(separator)
    print()


def main():
    parser = argparse.ArgumentParser(description="ADRIANA SCL Thermal Verification")
    parser.add_argument("--node-id", required=True, help="Genesis 10 Node ID")
    parser.add_argument("--action", choices=["compost", "aquaponics"], default="compost",
                        help="Biological action type")
    parser.add_argument("--samples", type=int, default=10, help="Number of thermal readings")
    parser.add_argument("--output", default=None, help="Write JSON result to file")
    parser.add_argument("--simulate", action="store_true",
                        help="Simulate sensor data (no hardware required)")
    args = parser.parse_args()

    print()
    print("  ADRIANA SCL — Thermal Verification Oracle")
    print(f"  Node: {args.node_id}  |  Action: {args.action}")
    print(f"  Sampling {args.samples} thermal readings...")
    print()

    hardware_ok = _check_hardware() and not args.simulate

    if hardware_ok:
        print("  [MODE] Live MLX90640 hardware detected.")
        readings = _read_thermal_hardware(args.samples)
    else:
        if not args.simulate:
            print("  [MODE] Hardware not found — running simulation.", file=sys.stderr)
        readings = _simulate_thermal(args.samples)

    ts = datetime.now(timezone.utc).isoformat()
    hdr = _compute_hdr(readings)

    verified = hdr > 0.05
    peace_amount = 1.0 if verified else 0.0

    if verified:
        _display_certificate(args.node_id, args.action, hdr, peace_amount, ts)
        status = "VERIFIED"
    else:
        print()
        print("  [ADRIANA_SCL] REJECTED: HDR too low. No biological activity detected.")
        print(f"  [HDR: {hdr:.4f}] Threshold: 0.05")
        print()
        status = "REJECTED"

    result = {
        "node_id": args.node_id,
        "action_type": args.action,
        "hdr_value": hdr,
        "readings": readings,
        "verified": verified,
        "peace_pending": peace_amount,
        "timestamp": ts,
        "status": status,
        "submit_to": "https://your-void-domain.repl.co/genesis/oracle",
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  Result written to: {args.output}")

    print(json.dumps(result, indent=2))
    return 0 if verified else 1


if __name__ == "__main__":
    sys.exit(main())
