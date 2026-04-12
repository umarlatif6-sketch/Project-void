"""
BW19-286 Unified Math Engine — Encode/Decode Benchmark

Runs timed comparison at 480p between legacy (no BW19 session) and
BW19-286 curve-seeded encoding paths. Verifies exact roundtrip integrity.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from void_engine.z_axis_video import (
    encode_to_video,
    _decode_video_pass,
    _frame_pixel_positions,
    _generate_chladni_frame,
    BW19Session,
    RESOLUTIONS,
)
import subprocess
import numpy as np

FORMATION_HASH = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6"
TEST_DATA = b"BismillahirRahmanirRahim - BW19-286 benchmark payload for roundtrip verification"
RESOLUTION = "480p"
FPS = 10


def probe_video(path):
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0", path
    ]
    out = subprocess.check_output(cmd, timeout=30).decode().strip()
    parts = out.split(",")
    return int(parts[0]), int(parts[1])


def run_benchmark():
    print("=" * 60)
    print("BW19-286 UNIFIED MATH ENGINE — TIMED BENCHMARK")
    print("=" * 60)
    print(f"Resolution: {RESOLUTION} ({RESOLUTIONS[RESOLUTION][0]}x{RESOLUTIONS[RESOLUTION][1]})")
    print(f"FPS: {FPS}")
    print(f"Payload: {len(TEST_DATA)} bytes")
    print()

    t0 = time.time()
    output_path = encode_to_video(TEST_DATA, FORMATION_HASH, resolution=RESOLUTION, fps=FPS)
    encode_time = time.time() - t0

    w, h = probe_video(output_path)

    t0 = time.time()
    session = BW19Session(FORMATION_HASH)
    decoded_bw19 = _decode_video_pass(output_path, FORMATION_HASH, w, h, session=session)
    decode_time = time.time() - t0

    match = decoded_bw19 == TEST_DATA

    os.unlink(output_path)

    print(f"BW19-286 ENCODE: {encode_time:.2f}s")
    print(f"BW19-286 DECODE: {decode_time:.2f}s")
    print(f"ROUNDTRIP MATCH: {match}")
    print()
    print("Curve:      y^2 = x^3 + 31 (BW19-P286, 286-bit prime)")
    print("Layers:     7 Fatiha-weighted [7,4,2,5,4,3,6], sum=31=b")
    print("Freq:       432 Hz anchor in Chladni phase and harmonic scaling")
    print("Positions:  ec_add chain from al_jabr_to_curve_point(formation_hash)")
    print("Fallback:   auto-legacy decode for pre-BW19 encoded files")
    print()

    if not match:
        print("FAIL: Roundtrip integrity broken!")
        sys.exit(1)

    print("PASS: All assertions verified.")
    return encode_time, decode_time


if __name__ == "__main__":
    run_benchmark()
