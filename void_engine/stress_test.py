import os
import sys
import time
import zlib
import wave
import datetime
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from void_engine.stega import (
    encode, check_resonance_purity, _compute_ghost_offset, HEADER_SIZE
)

SAMPLE_RATE = 44100
VILLAGE_HZ = 432
BURST_REPORT = "BURST_REPORT.md"
SNR_FLOOR = 15.0
TENSION_CEILING = 0.40


class _SuppressStdout:
    def __enter__(self):
        self._original = sys.stdout
        sys.stdout = open(os.devnull, "w")
        return self

    def __exit__(self, *args):
        sys.stdout.close()
        sys.stdout = self._original


def _format_size(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024*1024):.2f} MB"
    elif n >= 1024:
        return f"{n / 1024:.2f} KB"
    return f"{n} B"


def _generate_carrier(duration: float = 60.0) -> str:
    path = "output_audio/_stress_carrier.wav"
    os.makedirs("output_audio", exist_ok=True)
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    signal = (
        np.sin(2 * np.pi * VILLAGE_HZ * t) * 8000
        + np.sin(2 * np.pi * (VILLAGE_HZ * 2) * t) * 4000
        + np.sin(2 * np.pi * (VILLAGE_HZ * 3) * t) * 2000
        + np.sin(2 * np.pi * (VILLAGE_HZ * 0.5) * t) * 3000
    )
    lfo = 1.0 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
    signal = (signal * lfo).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(signal.tobytes())
    return path


def _generate_ocean_payload(size_mb: int) -> bytes:
    size_bytes = size_mb * 1024 * 1024
    rng = np.random.RandomState(432 + size_mb)
    return rng.bytes(size_bytes)


def run_stress_test(carrier_path: str = None, duration: float = 60.0):
    if carrier_path and os.path.exists(carrier_path):
        print(f"  Using existing carrier: {carrier_path}")
    else:
        print(f"  Generating {duration:.0f}s carrier @ {VILLAGE_HZ} Hz...")
        carrier_path = _generate_carrier(duration)
        print(f"  Carrier ready: {carrier_path}")

    with wave.open(carrier_path, "rb") as wf:
        carrier_samples = wf.getnframes()
        sr = wf.getframerate()
        carrier_duration = carrier_samples / sr

    carrier_name = os.path.basename(carrier_path)
    max_capacity_bytes = carrier_samples // 8
    output_wav = "output_audio/_stress_probe.wav"
    os.makedirs("output_audio", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print()
    print("=" * 70)
    print("  VOID STRESS TEST — Sapphire Bubble Pressure Escalation")
    print("=" * 70)
    print(f"  Carrier:           {carrier_name}")
    print(f"  Duration:          {carrier_duration:.1f}s")
    print(f"  Total Samples:     {carrier_samples:,}")
    print(f"  Max Capacity:      {_format_size(max_capacity_bytes)} (LSB depth 1)")
    print(f"  SNR Floor:         {SNR_FLOOR:.1f} dB")
    print(f"  Tension Ceiling:   {TENSION_CEILING*100:.0f}%")
    print(f"  Increment:         1 MB")
    print()

    results = []
    breakpoint_mb = None
    breakpoint_reason = None

    print(f"  {'Payload':>10}  {'Tension':>10}  {'SNR':>8}  {'Grade':>12}  {'Encode':>10}  {'Status':>10}")
    print(f"  {'—'*10}  {'—'*10}  {'—'*8}  {'—'*12}  {'—'*10}  {'—'*10}")

    current_mb = 1
    while True:
        size_bytes = current_mb * 1024 * 1024

        raw_payload = _generate_ocean_payload(current_mb)
        compressed = b"ZLIB" + zlib.compress(raw_payload, level=1)

        passphrase = fatiha_286_hexdigest_from_str(f"stress_{current_mb}mb")[:32]

        ghost_offset = _compute_ghost_offset(passphrase, carrier_samples)
        effective_capacity = ((carrier_samples - ghost_offset) * 1) // 8
        total_embedded = HEADER_SIZE + len(compressed)
        tension = total_embedded / effective_capacity if effective_capacity > 0 else 1.0

        if total_embedded > effective_capacity:
            print(f"  {current_mb:>7} MB  {'—':>10}  {'—':>8}  {'—':>12}  {'—':>10}  {'OVERFLOW':>10}")
            results.append({
                "size_mb": current_mb, "tension": 1.0,
                "snr": 0.0, "grade": "OVERFLOW", "encode_time": 0.0
            })
            breakpoint_mb = current_mb
            breakpoint_reason = "CAPACITY OVERFLOW"
            break

        if tension > TENSION_CEILING:
            print(f"  {current_mb:>7} MB  {tension*100:>9.1f}%  {'—':>8}  {'—':>12}  {'—':>10}  {'TENSION':>10}")
            results.append({
                "size_mb": current_mb, "tension": tension,
                "snr": 0.0, "grade": "EXCEEDED", "encode_time": 0.0
            })
            breakpoint_mb = current_mb
            breakpoint_reason = f"SURFACE TENSION exceeded {TENSION_CEILING*100:.0f}% (reached {tension*100:.1f}%)"
            break

        try:
            name = f"stress_{current_mb}mb"
            ext = ".bin"
            t_start = time.perf_counter()
            with _SuppressStdout():
                encode(carrier_path, compressed, name, ext, output_wav,
                       lsb_depth=1, passphrase=passphrase, jitter=True)
            t_end = time.perf_counter()
            encode_time = t_end - t_start

            purity = check_resonance_purity(output_wav)
            snr = purity.get("snr_db", 0.0)
            grade = purity.get("quality", "Unknown")

            status = "SAFE"
            if snr < SNR_FLOOR:
                status = "BURST"
                breakpoint_mb = current_mb
                breakpoint_reason = f"SNR dropped below {SNR_FLOOR:.1f} dB (reached {snr:.1f} dB)"

            print(f"  {current_mb:>7} MB  {tension*100:>9.1f}%  {snr:>7.1f}  {grade:>12}  {encode_time:>9.1f}s  {status:>10}")

            results.append({
                "size_mb": current_mb, "tension": tension,
                "snr": snr, "grade": grade, "encode_time": encode_time
            })

            if status == "BURST":
                break

        except Exception as e:
            err_msg = str(e).lower()
            if "capacity" in err_msg or "too large" in err_msg or "exceed" in err_msg:
                print(f"  {current_mb:>7} MB  {'—':>10}  {'—':>8}  {'—':>12}  {'—':>10}  {'OVERFLOW':>10}")
                results.append({
                    "size_mb": current_mb, "tension": 1.0,
                    "snr": 0.0, "grade": "OVERFLOW", "encode_time": 0.0
                })
                breakpoint_mb = current_mb
                breakpoint_reason = "CAPACITY OVERFLOW"
            else:
                print(f"  {current_mb:>7} MB  {'—':>10}  {'—':>8}  {'ERROR':>12}  {'—':>10}  {'FAILED':>10}")
                results.append({
                    "size_mb": current_mb, "tension": 0.0,
                    "snr": 0.0, "grade": "ERROR", "encode_time": 0.0
                })
                breakpoint_mb = current_mb
                breakpoint_reason = f"ENCODE ERROR: {e}"
            break

        current_mb += 1

    cleanup_files = [output_wav]
    if carrier_path == "output_audio/_stress_carrier.wav":
        cleanup_files.append(carrier_path)
    for f in cleanup_files:
        if os.path.exists(f):
            os.remove(f)

    print()
    print("=" * 70)
    if breakpoint_mb:
        print(f"  [BREAKPOINT FOUND]: The Sapphire Bubble bursts at {breakpoint_mb}MB")
        print(f"                      for a {carrier_duration:.0f}s carrier.")
        print(f"  Reason:             {breakpoint_reason}")
    else:
        print(f"  No breakpoint found within tested range.")
    print("=" * 70)

    _write_burst_report(results, carrier_name, carrier_duration, carrier_samples,
                        max_capacity_bytes, breakpoint_mb, breakpoint_reason, timestamp)


def _write_burst_report(results, carrier_name, duration, samples,
                        max_cap, breakpoint_mb, reason, timestamp):
    lines = []
    lines.append(f"\n## Stress Test — {timestamp}\n")
    lines.append(f"- **Carrier**: {carrier_name}")
    lines.append(f"- **Duration**: {duration:.1f}s")
    lines.append(f"- **Samples**: {samples:,}")
    lines.append(f"- **Max Capacity**: {_format_size(max_cap)} (LSB depth 1)")
    lines.append(f"- **SNR Floor**: {SNR_FLOOR:.1f} dB")
    lines.append(f"- **Tension Ceiling**: {TENSION_CEILING*100:.0f}%")
    lines.append(f"- **Probes**: {len(results)}")
    lines.append("")
    lines.append("| Payload (MB) | Surface Tension % | SNR (dB) | Encode Time (s) | Grade |")
    lines.append("|:---:|:---:|:---:|:---:|:---:|")

    for r in results:
        t_str = f"{r['tension']*100:.1f}%" if r['tension'] < 1.0 else "OVERFLOW"
        s_str = f"{r['snr']:.1f}" if r['snr'] > 0 else "—"
        e_str = f"{r['encode_time']:.1f}" if r['encode_time'] > 0 else "—"
        lines.append(f"| {r['size_mb']} | {t_str} | {s_str} | {e_str} | {r['grade']} |")

    lines.append("")
    if breakpoint_mb:
        lines.append(f"**[BREAKPOINT FOUND]**: The Sapphire Bubble bursts at **{breakpoint_mb}MB** for a {duration:.0f}s carrier.")
        lines.append(f"- **Reason**: {reason}")
    lines.append("")
    lines.append("---")

    header_needed = not os.path.exists(BURST_REPORT)
    with open(BURST_REPORT, "a") as f:
        if header_needed:
            f.write("# BURST REPORT — Void Stress Test Results\n")
        f.write("\n".join(lines))
        f.write("\n")

    print(f"\n  [LOG] Results appended to {BURST_REPORT}")


if __name__ == "__main__":
    carrier = None
    duration = 60.0

    if len(sys.argv) > 1:
        carrier = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            duration = float(sys.argv[2])
        except ValueError:
            pass

    run_stress_test(carrier_path=carrier, duration=duration)
