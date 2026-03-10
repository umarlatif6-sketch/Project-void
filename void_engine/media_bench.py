import os
import sys
import time
import zlib
import lzma
import wave
import hashlib
import tracemalloc
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
import datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from void_engine.stega import (
    encode, decode, _generate_jitter_map, _compute_ghost_offset,
    _derive_key, _build_header, check_resonance_purity,
    HEADER_SIZE, JITTER_FLAG_BIT
)
from void_engine.compressor import decompress_data

CHUNK_SIZE = 8 * 1024 * 1024
COOLING_THRESHOLD = 50 * 1024 * 1024
COOLING_PAUSE = 2.0
VILLAGE_HZ = 432
SAMPLE_RATE = 44100
RESONANCE_LOG = "RESONANCE_LOG.md"


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


def _format_time(seconds: float) -> str:
    if seconds >= 1.0:
        return f"{seconds:.3f}s"
    return f"{seconds * 1000:.1f}ms"


def _compress_streaming(file_path: str, file_size: int, algo: str) -> tuple[bytes, float, float]:
    needs_cooling = file_size > COOLING_THRESHOLD

    tracemalloc.start()
    t_start = time.perf_counter()

    if algo == "zlib":
        compressor = zlib.compressobj(level=9)
    else:
        compressor = lzma.LZMACompressor(preset=9)

    chunks = []
    processed = 0
    chunk_num = 0

    with open(file_path, "rb") as f:
        while True:
            block = f.read(CHUNK_SIZE)
            if not block:
                break
            chunks.append(compressor.compress(block))
            processed += len(block)
            chunk_num += 1
            if needs_cooling and processed < file_size:
                print(f"    [COOLING] Chunk {chunk_num} done ({_format_size(processed)}) — pausing {COOLING_PAUSE}s for Mac 2012 CPU...")
                time.sleep(COOLING_PAUSE)

    chunks.append(compressor.flush())
    result = b"".join(chunks)

    t_end = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return result, t_end - t_start, peak_mem


def _generate_carrier(duration_seconds: float, output_path: str) -> str:
    n_samples = int(SAMPLE_RATE * duration_seconds)
    t = np.linspace(0, duration_seconds, n_samples, endpoint=False)
    signal = (16000 * np.sin(2 * np.pi * VILLAGE_HZ * t)).astype(np.int16)

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(signal.tobytes())

    return output_path


def generate_ocean_payload(size_bytes: int, output_path: str) -> str:
    rng = np.random.RandomState(432)
    remaining = size_bytes
    with open(output_path, "wb") as f:
        while remaining > 0:
            block_size = min(remaining, CHUNK_SIZE)
            block = rng.bytes(block_size)
            f.write(block)
            remaining -= block_size
    print(f"  [OCEAN] Synthetic payload generated: {_format_size(size_bytes)} → {output_path}")
    return output_path


def _append_resonance_log(entry: str):
    with open(RESONANCE_LOG, "a") as f:
        f.write("\n" + entry + "\n")


def run_benchmark(media_path: str, output_wav: str = "output_audio/media_test_void.wav",
                  carrier_path_override: str = None):
    if not os.path.exists(media_path):
        print(f"  [ERROR] File not found: {media_path}")
        return

    file_size = os.path.getsize(media_path)
    file_name = os.path.basename(media_path)
    name, ext = os.path.splitext(file_name)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 70)
    print("  VOID MEDIA BENCHMARK — Deep Sea Stress Test")
    print("=" * 70)
    print(f"  Input File:    {file_name}")
    print(f"  File Size:     {_format_size(file_size)}")
    print(f"  Cooling Mode:  {'ACTIVE (>50MB — 2s pause per 8MB chunk)' if file_size > COOLING_THRESHOLD else 'Standby (file under 50MB)'}")
    print()

    print("  PHASE 1: COMPRESSION COMPETITION (ZLIB vs LZMA)")
    print("  " + "-" * 50)

    zlib_result, zlib_time, zlib_peak = _compress_streaming(media_path, file_size, "zlib")
    print(f"    ZLIB Level 9:")
    print(f"      Output Size:    {_format_size(len(zlib_result))}")
    print(f"      Time:           {_format_time(zlib_time)}")
    print(f"      Memory Peak:    {_format_size(int(zlib_peak))}")
    print(f"      Ratio:          {(1 - len(zlib_result) / file_size) * 100:.1f}% reduction")

    lzma_result, lzma_time, lzma_peak = _compress_streaming(media_path, file_size, "lzma")
    print(f"    LZMA Preset 9:")
    print(f"      Output Size:    {_format_size(len(lzma_result))}")
    print(f"      Time:           {_format_time(lzma_time)}")
    print(f"      Memory Peak:    {_format_size(int(lzma_peak))}")
    print(f"      Ratio:          {(1 - len(lzma_result) / file_size) * 100:.1f}% reduction")

    if len(lzma_result) < len(zlib_result):
        winner = "LZMA"
        compressed = b"LZMA" + lzma_result
        win_time = lzma_time
        win_peak = lzma_peak
    else:
        winner = "ZLIB"
        compressed = b"ZLIB" + zlib_result
        win_time = zlib_time
        win_peak = zlib_peak

    print(f"    WINNER: {winner} ({_format_size(len(compressed) - 4)} compressed)")
    print()

    print("  PHASE 2: GHOST HEADER WRAP")
    print("  " + "-" * 50)

    passphrase = fatiha_286_hexdigest_from_str(os.urandom(32).hex())[:32]
    key = _derive_key(passphrase)
    checksum = hashlib.md5(compressed).hexdigest()

    header = _build_header(name, ext, len(compressed), checksum, key, jitter=True)
    total_payload = len(header) + len(compressed)

    print(f"    Header Size:      {HEADER_SIZE} bytes (ChaCha20 encrypted)")
    print(f"    Payload Size:     {_format_size(len(compressed))}")
    print(f"    Total Embedded:   {_format_size(total_payload)}")
    print()

    use_existing_carrier = carrier_path_override and os.path.exists(carrier_path_override)

    if use_existing_carrier:
        carrier_path = carrier_path_override
        print("  PHASE 3: CARRIER LOADING (Existing 432 Hz WAV)")
        print("  " + "-" * 50)

        with wave.open(carrier_path, "rb") as wf:
            carrier_samples = wf.getnframes()
            sr = wf.getframerate()
            carrier_duration = carrier_samples / sr

        carrier_size = os.path.getsize(carrier_path)
    else:
        print("  PHASE 3: CARRIER GENERATION (432 Hz Village Standard)")
        print("  " + "-" * 50)

        ghost_carrier_samples = total_payload * 8 * 4
        carrier_duration = ghost_carrier_samples / SAMPLE_RATE
        carrier_duration = max(carrier_duration, 5.0)

        carrier_path = output_wav + ".tmp_carrier.wav"
        t_carrier_start = time.perf_counter()
        _generate_carrier(carrier_duration, carrier_path)
        t_carrier_end = time.perf_counter()

        carrier_size = os.path.getsize(carrier_path)
        carrier_samples = int(SAMPLE_RATE * carrier_duration)
        sr = SAMPLE_RATE

        print(f"    Generation Time:  {_format_time(t_carrier_end - t_carrier_start)}")

    ghost_offset = _compute_ghost_offset(passphrase, carrier_samples)

    print(f"    Duration:         {carrier_duration:.1f}s")
    print(f"    Sample Rate:      {sr} Hz")
    print(f"    Carrier Size:     {_format_size(carrier_size)}")
    print(f"    Total Samples:    {carrier_samples:,}")
    print()

    print("  PHASE 4: PLANKTON FRAGMENTATION (Fly Jitter)")
    print("  " + "-" * 50)

    bits_per_sample = 1
    header_samples = HEADER_SIZE * 8 // bits_per_sample
    data_samples = len(compressed) * 8 // bits_per_sample

    data_start = ghost_offset + header_samples
    jitter_map = _generate_jitter_map(passphrase, data_samples, data_start, carrier_samples)

    print(f"    Data Samples:     {data_samples:,}")
    print(f"    Fragment Count:   {len(jitter_map)} Plankton packets")
    print()

    plankton_lines = []
    if len(jitter_map) > 1:
        chunk_sizes = [s for _, s in jitter_map]
        gaps = [jitter_map[i+1][0] - (jitter_map[i][0] + jitter_map[i][1]) for i in range(len(jitter_map)-1)]

        print(f"    {'#':>4}  {'Offset':>10}  {'Size':>8}  {'Gap→Next':>10}  {'Depth':>8}")
        print(f"    {'—'*4}  {'—'*10}  {'—'*8}  {'—'*10}  {'—'*8}")

        for i, (offset, size) in enumerate(jitter_map):
            gap_str = f"{gaps[i]:,}" if i < len(gaps) else "—"
            depth_pct = f"{(offset / carrier_samples) * 100:.1f}%"
            line = f"    {i+1:>4}  {offset:>10,}  {size:>8,}  {gap_str:>10}  {depth_pct:>8}"
            print(line)
            plankton_lines.append(f"| {i+1} | {offset:,} | {size:,} | {gap_str} | {depth_pct} |")

        print()
        print(f"    Chunk Stats:      min={min(chunk_sizes):,} / max={max(chunk_sizes):,} / avg={sum(chunk_sizes)//len(chunk_sizes):,}")
        print(f"    Gap Stats:        min={min(gaps):,} / max={max(gaps):,} / avg={sum(gaps)//len(gaps):,}")
        print(f"    Scatter Range:    {jitter_map[0][0]:,} → {jitter_map[-1][0] + jitter_map[-1][1]:,} samples")
        print(f"    Coverage:         {((jitter_map[-1][0] + jitter_map[-1][1]) - jitter_map[0][0]):,} samples span")
    else:
        print(f"    Mode:             Sequential (carrier too full for jitter)")
        plankton_lines.append("| 1 | Sequential | All | — | — |")
    print()

    print("  PHASE 5: FULL ENCODE (Sapphire WAV)")
    print("  " + "-" * 50)

    encode_success = False
    integrity = "UNTESTED"
    purity = {}
    surface_tension = 0
    decoded_name = ""

    t_encode_start = time.perf_counter()
    try:
        returned_key = encode(carrier_path, compressed, name, ext, output_wav,
                              lsb_depth=1, passphrase=passphrase, jitter=True)
        t_encode_end = time.perf_counter()
        encode_success = True

        output_size = os.path.getsize(output_wav)
        effective_capacity = ((carrier_samples - ghost_offset) * bits_per_sample) // 8
        surface_tension = total_payload / effective_capacity if effective_capacity > 0 else 0

        print(f"    Encode Time:      {_format_time(t_encode_end - t_encode_start)}")
        print(f"    Output File:      {output_wav}")
        print(f"    Output Size:      {_format_size(output_size)}")
        print()

        print("  PHASE 6: RESONANCE PURITY (FFT Analysis)")
        print("  " + "-" * 50)

        purity = check_resonance_purity(output_wav)
        print(f"    432 Hz Signal:    {purity.get('snr_db', 0):.1f} dB SNR")
        print(f"    864 Hz Harmonic:  {'Present' if purity.get('harmonic_2_present', False) else 'Absent'}")
        print(f"    Quality Grade:    {purity.get('quality', 'Unknown')}")
        if purity.get('warning'):
            print(f"    WARNING:          {purity['warning']}")
        print(f"    Verdict:          {'432 Hz SURVIVED encoding — Surface Tension held' if purity.get('quality') in ('Clear', 'Acceptable') else '432 Hz degraded — Bubble membrane stressed'}")
        print()

        print("  PHASE 7: DECODE VERIFICATION")
        print("  " + "-" * 50)

        t_decode_start = time.perf_counter()
        decoded_data, decoded_name, decoded_checksum = decode(output_wav, returned_key, lsb_depth=1)
        t_decode_end = time.perf_counter()

        decompressed = decompress_data(decoded_data)
        with open(media_path, "rb") as f:
            original_data = f.read()
        integrity = "VERIFIED" if decompressed == original_data else "FAILED"

        print(f"    Decode Time:      {_format_time(t_decode_end - t_decode_start)}")
        print(f"    Decoded File:     {decoded_name}")
        print(f"    Decoded Size:     {_format_size(len(decompressed))}")
        print(f"    Integrity:        {integrity}")
        print()

    except Exception as e:
        t_encode_end = time.perf_counter()
        print(f"    [ERROR] Pipeline failed: {e}")
        print()

    if not use_existing_carrier and os.path.exists(carrier_path):
        os.remove(carrier_path)

    if surface_tension < 0.25:
        bubble_status = "SAFE — bubble holds firm"
    elif surface_tension < 0.90:
        bubble_status = "STRETCH — membrane under tension"
    else:
        bubble_status = "BURST — exceeding membrane capacity"

    print("=" * 70)
    print("  DEEP SEA BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"  Input:              {file_name} ({_format_size(file_size)})")
    print(f"  Compression:        {winner} won ({_format_time(win_time)}, peak {_format_size(int(win_peak))})")
    print(f"  LZMA CPU Time:      {_format_time(lzma_time)}")
    print(f"  Compressed Size:    {_format_size(len(compressed))}")
    print(f"  Plankton Fragments: {len(jitter_map)} packets")
    print(f"  Surface Tension:    {surface_tension:.4f} ({surface_tension * 100:.2f}%)")
    print(f"  Resonance Purity:   {purity.get('quality', 'N/A')} ({purity.get('snr_db', 0):.1f} dB)")
    print(f"  Integrity:          {integrity}")
    print(f"  Output:             {output_wav}")
    print(f"  Bubble Status:      {bubble_status}")
    print("=" * 70)

    log_entry = f"""### {timestamp} — DEEP SEA STRESS TEST: {file_name}

| Metric | Value |
|---|---|
| Input File | {file_name} |
| Input Size | {_format_size(file_size)} |
| Compression Winner | {winner} ({_format_time(win_time)}) |
| ZLIB Result | {_format_size(len(zlib_result))} in {_format_time(zlib_time)} |
| LZMA Result | {_format_size(len(lzma_result))} in {_format_time(lzma_time)} |
| LZMA Peak Memory | {_format_size(int(lzma_peak))} |
| Compressed Size | {_format_size(len(compressed))} |
| Ghost Offset | {ghost_offset:,} samples |
| Plankton Fragments | {len(jitter_map)} packets |
| Surface Tension | {surface_tension:.4f} ({surface_tension * 100:.2f}%) |
| Bubble Status | {bubble_status} |
| Resonance Purity | {purity.get('quality', 'N/A')} ({purity.get('snr_db', 0):.1f} dB SNR) |
| Integrity | {integrity} |
| Output File | {output_wav} |
| Carrier | {os.path.basename(carrier_path)} |

#### Plankton Map (Fragment Offsets)

| # | Offset | Size | Gap→Next | Depth |
|---|---|---|---|---|
{chr(10).join(plankton_lines)}

---"""

    _append_resonance_log(log_entry)
    print()
    print(f"  [LOG] Results appended to {RESONANCE_LOG}")


def find_burst_point(carrier_path: str, start_kb: int = 10, step_kb: int = 10,
                     max_kb: int = None, snr_floor: float = 15.0):
    if not os.path.exists(carrier_path):
        print(f"  [ERROR] Carrier not found: {carrier_path}")
        return

    with wave.open(carrier_path, "rb") as wf:
        carrier_samples = wf.getnframes()
        sr = wf.getframerate()
        carrier_duration = carrier_samples / sr

    carrier_name = os.path.basename(carrier_path)
    max_capacity_bytes = carrier_samples // 8
    if max_kb is None:
        max_kb = max_capacity_bytes // 1024

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_wav = "output_audio/burst_point_probe.wav"
    temp_payload = "input_files/_burst_probe.bin"

    print("=" * 70)
    print("  BURST POINT FINDER — Sapphire Bubble Pressure Test")
    print("=" * 70)
    print(f"  Carrier:           {carrier_name}")
    print(f"  Duration:          {carrier_duration:.1f}s")
    print(f"  Total Samples:     {carrier_samples:,}")
    print(f"  Max Capacity:      {_format_size(max_capacity_bytes)} (LSB depth 1)")
    print(f"  SNR Floor:         {snr_floor:.1f} dB (below = Muddled)")
    print(f"  Escalation:        {start_kb} KB → {max_kb} KB (step {step_kb} KB)")
    print()

    results = []
    burst_found = False
    last_safe_kb = 0
    last_safe_snr = 0.0

    print(f"  {'Size':>8}  {'Tension':>10}  {'SNR':>8}  {'Grade':>12}  {'Encode':>10}  {'Status':>10}")
    print(f"  {'—'*8}  {'—'*10}  {'—'*8}  {'—'*12}  {'—'*10}  {'—'*10}")

    current_kb = start_kb
    while current_kb <= max_kb:
        size_bytes = current_kb * 1024

        rng = np.random.RandomState(432 + current_kb)
        raw_payload = rng.bytes(size_bytes)

        compressed = b"ZLIB" + zlib.compress(raw_payload, level=1)

        passphrase = fatiha_286_hexdigest_from_str(f"burst_probe_{current_kb}")[:32]

        ghost_offset = _compute_ghost_offset(passphrase, carrier_samples)
        effective_capacity = ((carrier_samples - ghost_offset) * 1) // 8
        total_embedded = HEADER_SIZE + len(compressed)

        if total_embedded > effective_capacity:
            print(f"  {_format_size(size_bytes):>8}  {'—':>10}  {'—':>8}  {'—':>12}  {'—':>10}  {'OVERFLOW':>10}")
            results.append({
                "size_kb": current_kb, "size_bytes": size_bytes,
                "tension": 1.0, "snr": 0.0, "grade": "OVERFLOW",
                "encode_time": 0.0, "status": "OVERFLOW"
            })
            burst_found = True
            break

        try:
            name = f"probe_{current_kb}kb"
            ext = ".bin"
            t_start = time.perf_counter()
            with _SuppressStdout():
                returned_key = encode(carrier_path, compressed, name, ext, output_wav,
                                      lsb_depth=1, passphrase=passphrase, jitter=True)
            t_end = time.perf_counter()
            encode_time = t_end - t_start

            tension = total_embedded / effective_capacity if effective_capacity > 0 else 1.0

            purity = check_resonance_purity(output_wav)
            snr = purity.get("snr_db", 0.0)
            grade = purity.get("quality", "Unknown")

            if snr < snr_floor:
                status = "BURST"
                burst_found = True
            elif tension >= 0.90:
                status = "STRETCH"
            else:
                status = "SAFE"
                last_safe_kb = current_kb
                last_safe_snr = snr

            print(f"  {_format_size(size_bytes):>8}  {tension*100:>9.2f}%  {snr:>7.1f}  {grade:>12}  {_format_time(encode_time):>10}  {status:>10}")

            results.append({
                "size_kb": current_kb, "size_bytes": size_bytes,
                "tension": tension, "snr": snr, "grade": grade,
                "encode_time": encode_time, "status": status
            })

            if burst_found:
                break

        except Exception as e:
            err_msg = str(e)
            if "capacity" in err_msg.lower() or "too large" in err_msg.lower() or "exceed" in err_msg.lower():
                print(f"  {_format_size(size_bytes):>8}  {'—':>10}  {'—':>8}  {'—':>12}  {'—':>10}  {'OVERFLOW':>10}")
                results.append({
                    "size_kb": current_kb, "size_bytes": size_bytes,
                    "tension": 1.0, "snr": 0.0, "grade": "OVERFLOW",
                    "encode_time": 0.0, "status": "OVERFLOW"
                })
            else:
                print(f"  {_format_size(size_bytes):>8}  {'—':>10}  {'—':>8}  {'ERROR':>12}  {'—':>10}  {'FAILED':>10}")
                results.append({
                    "size_kb": current_kb, "size_bytes": size_bytes,
                    "tension": 0, "snr": 0.0, "grade": "ERROR",
                    "encode_time": 0.0, "status": f"ERROR: {e}"
                })
            burst_found = True
            break

        if current_kb < 50:
            current_kb += 10
        elif current_kb < 200:
            current_kb += 20
        else:
            current_kb += 40

    for f in [output_wav, temp_payload]:
        if os.path.exists(f):
            os.remove(f)

    print()
    print("=" * 70)
    print("  BURST POINT ANALYSIS")
    print("=" * 70)

    if burst_found and len(results) >= 2:
        burst_entry = results[-1]
        safe_entry = results[-2] if results[-2]["status"] == "SAFE" else None

        if burst_entry["status"] == "OVERFLOW":
            print(f"  Burst Type:         CAPACITY OVERFLOW at {_format_size(burst_entry['size_bytes'])}")
        else:
            print(f"  Burst Type:         SNR FAILURE at {_format_size(burst_entry['size_bytes'])}")
            print(f"  SNR at Burst:       {burst_entry['snr']:.1f} dB ({burst_entry['grade']})")

        if safe_entry:
            print(f"  Last Safe Payload:  {_format_size(safe_entry['size_bytes'])} ({safe_entry['snr']:.1f} dB, {safe_entry['tension']*100:.1f}% tension)")
        elif last_safe_kb > 0:
            print(f"  Last Safe Payload:  {last_safe_kb} KB ({last_safe_snr:.1f} dB)")
    elif not burst_found:
        print(f"  Result:             BUBBLE NEVER BURST — carrier held all payloads up to {_format_size(results[-1]['size_bytes'])}")
        print(f"  Final SNR:          {results[-1]['snr']:.1f} dB ({results[-1]['grade']})")
        print(f"  Final Tension:      {results[-1]['tension']*100:.2f}%")
    else:
        print(f"  Result:             BURST on first probe ({_format_size(results[0]['size_bytes'])})")

    print(f"  Carrier:            {carrier_name} ({carrier_duration:.1f}s)")
    print(f"  Max Capacity:       {_format_size(max_capacity_bytes)}")
    print(f"  Probes Run:         {len(results)}")
    print("=" * 70)

    log_lines = []
    for r in results:
        log_lines.append(
            f"| {_format_size(r['size_bytes'])} | {r['tension']*100:.1f}% | {r['snr']:.1f} dB | {r['grade']} | {r['status']} |"
        )

    safe_entries = [r for r in results if r["status"] == "SAFE"]
    max_safe = safe_entries[-1] if safe_entries else None

    log_entry = f"""### {timestamp} — BURST POINT TEST: {carrier_name}

| Metric | Value |
|---|---|
| Carrier | {carrier_name} |
| Duration | {carrier_duration:.1f}s |
| Max Capacity | {_format_size(max_capacity_bytes)} |
| Max Safe Payload | {_format_size(max_safe['size_bytes']) + ' (' + f"{max_safe['snr']:.1f}" + ' dB)' if max_safe else 'None'} |
| Burst Point | {_format_size(results[-1]['size_bytes']) if burst_found else 'Not reached'} |
| Probes | {len(results)} |

#### Pressure Curve

| Payload | Tension | SNR | Grade | Status |
|---|---|---|---|---|
{chr(10).join(log_lines)}

---"""

    _append_resonance_log(log_entry)
    print()
    print(f"  [LOG] Burst Point results appended to {RESONANCE_LOG}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m void_engine.media_bench <media_file> [output_wav] [carrier_wav]")
        print("  python -m void_engine.media_bench --ocean <size_kb> [output_wav] [carrier_wav]")
        print("  python -m void_engine.media_bench --burst <carrier_wav> [start_kb] [step_kb]")
        print()
        print("Examples:")
        print("  python -m void_engine.media_bench input_files/test_image.bmp")
        print("  python -m void_engine.media_bench input_files/photo.jpg output_audio/deep_test.wav input_files/ambient_drone_60s.wav")
        print("  python -m void_engine.media_bench --ocean 100 output_audio/ocean_test.wav input_files/ambient_drone_60s.wav")
        print("  python -m void_engine.media_bench --burst input_files/ambient_drone_60s.wav 5 10")
        sys.exit(1)

    if sys.argv[1] == "--burst":
        carrier = sys.argv[2] if len(sys.argv) > 2 else "input_files/ambient_drone_60s.wav"
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        step = int(sys.argv[4]) if len(sys.argv) > 4 else 10
        find_burst_point(carrier, start_kb=start, step_kb=step)
    elif sys.argv[1] == "--ocean":
        size_kb = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        size_bytes = size_kb * 1024
        ocean_path = f"input_files/ocean_payload_{size_kb}kb.bin"
        generate_ocean_payload(size_bytes, ocean_path)
        media_file = ocean_path
        output = sys.argv[3] if len(sys.argv) > 3 else "output_audio/ocean_stress_test.wav"
        carrier = sys.argv[4] if len(sys.argv) > 4 else None
        run_benchmark(media_file, output, carrier_path_override=carrier)
    else:
        media_file = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "output_audio/media_test_void.wav"
        carrier = sys.argv[3] if len(sys.argv) > 3 else None
        run_benchmark(media_file, output, carrier_path_override=carrier)
