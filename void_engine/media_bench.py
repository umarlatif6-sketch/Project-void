import os
import sys
import time
import zlib
import lzma
import wave
import hashlib
import tracemalloc
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from void_engine.stega import (
    encode, decode, _generate_jitter_map, _compute_ghost_offset,
    _derive_key, _build_header, HEADER_SIZE, JITTER_FLAG_BIT
)
from void_engine.compressor import decompress_data

CHUNK_SIZE = 8 * 1024 * 1024
COOLING_THRESHOLD = 50 * 1024 * 1024
COOLING_PAUSE = 2.0
VILLAGE_HZ = 432
SAMPLE_RATE = 44100


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


def run_benchmark(media_path: str, output_wav: str = "output_audio/media_test_void.wav"):
    if not os.path.exists(media_path):
        print(f"  [ERROR] File not found: {media_path}")
        return

    file_size = os.path.getsize(media_path)
    file_name = os.path.basename(media_path)
    name, ext = os.path.splitext(file_name)

    print("=" * 70)
    print("  VOID MEDIA BENCHMARK — Sapphire Pipeline Test")
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

    passphrase = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
    key = _derive_key(passphrase)
    checksum = hashlib.md5(compressed).hexdigest()

    header = _build_header(name, ext, len(compressed), checksum, key, jitter=True)
    total_payload = len(header) + len(compressed)

    ghost_carrier_samples = total_payload * 8 * 4
    carrier_duration = ghost_carrier_samples / SAMPLE_RATE
    carrier_duration = max(carrier_duration, 5.0)

    print(f"    Header Size:      {HEADER_SIZE} bytes (ChaCha20 encrypted)")
    print(f"    Payload Size:     {_format_size(len(compressed))}")
    print(f"    Total Embedded:   {_format_size(total_payload)}")
    print(f"    Hash Key:         {passphrase[:8]}...{passphrase[-4:]}")
    print()

    print("  PHASE 3: CARRIER GENERATION (432 Hz Village Standard)")
    print("  " + "-" * 50)

    carrier_path = output_wav + ".tmp_carrier.wav"
    t_carrier_start = time.perf_counter()
    _generate_carrier(carrier_duration, carrier_path)
    t_carrier_end = time.perf_counter()

    carrier_size = os.path.getsize(carrier_path)
    carrier_samples = int(SAMPLE_RATE * carrier_duration)

    ghost_offset = _compute_ghost_offset(passphrase, carrier_samples)

    print(f"    Duration:         {carrier_duration:.1f}s")
    print(f"    Sample Rate:      {SAMPLE_RATE} Hz")
    print(f"    Carrier Size:     {_format_size(carrier_size)}")
    print(f"    Total Samples:    {carrier_samples:,}")
    print(f"    Ghost Offset:     {ghost_offset:,} samples")
    print(f"    Generation Time:  {_format_time(t_carrier_end - t_carrier_start)}")
    print()

    print("  PHASE 4: FLY JITTER PACKETIZING")
    print("  " + "-" * 50)

    bits_per_sample = 1
    header_samples = HEADER_SIZE * 8 // bits_per_sample
    data_samples = len(compressed) * 8 // bits_per_sample

    data_start = ghost_offset + header_samples
    jitter_map = _generate_jitter_map(passphrase, data_samples, data_start, carrier_samples)

    print(f"    Data Samples:     {data_samples:,}")
    print(f"    Fragment Count:   {len(jitter_map)} Fly packets")

    if len(jitter_map) > 1:
        chunk_sizes = [s for _, s in jitter_map]
        gaps = [jitter_map[i+1][0] - (jitter_map[i][0] + jitter_map[i][1]) for i in range(len(jitter_map)-1)]
        print(f"    Chunk Sizes:      min={min(chunk_sizes):,} / max={max(chunk_sizes):,} / avg={sum(chunk_sizes)//len(chunk_sizes):,}")
        print(f"    Gap Sizes:        min={min(gaps):,} / max={max(gaps):,} / avg={sum(gaps)//len(gaps):,}")
        print(f"    Scatter Range:    {jitter_map[0][0]:,} → {jitter_map[-1][0] + jitter_map[-1][1]:,} samples")
    else:
        print(f"    Mode:             Sequential (carrier too full for jitter)")
    print()

    print("  PHASE 5: FULL ENCODE (Sapphire WAV)")
    print("  " + "-" * 50)

    t_encode_start = time.perf_counter()
    try:
        returned_key = encode(carrier_path, compressed, name, ext, output_wav,
                              lsb_depth=1, passphrase=passphrase, jitter=True)
        t_encode_end = time.perf_counter()

        output_size = os.path.getsize(output_wav)
        effective_capacity = ((carrier_samples - ghost_offset) * bits_per_sample) // 8
        surface_tension = total_payload / effective_capacity if effective_capacity > 0 else 0

        print(f"    Encode Time:      {_format_time(t_encode_end - t_encode_start)}")
        print(f"    Output File:      {output_wav}")
        print(f"    Output Size:      {_format_size(output_size)}")
        print()

        print("  PHASE 6: DECODE VERIFICATION")
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
        print(f"    [ERROR] Encode failed: {e}")
        surface_tension = 0
        print()

    if os.path.exists(carrier_path):
        os.remove(carrier_path)

    print("=" * 70)
    print("  BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"  Input:              {file_name} ({_format_size(file_size)})")
    print(f"  Compression:        {winner} won ({_format_time(win_time)}, peak {_format_size(int(win_peak))})")
    print(f"  Compressed Size:    {_format_size(len(compressed))}")
    print(f"  Fly Fragments:      {len(jitter_map)} packets")
    print(f"  Surface Tension:    {surface_tension:.4f} ({surface_tension * 100:.2f}%)")
    print(f"  Output:             {output_wav}")
    if surface_tension < 0.25:
        print(f"  Bubble Status:      SAFE — bubble holds firm")
    elif surface_tension < 0.90:
        print(f"  Bubble Status:      STRETCH — membrane under tension")
    else:
        print(f"  Bubble Status:      BURST — exceeding membrane capacity")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m void_engine.media_bench <media_file> [output_wav]")
        print("Example: python -m void_engine.media_bench input_files/test_image.bmp")
        sys.exit(1)

    media_file = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "output_audio/media_test_void.wav"
    run_benchmark(media_file, output)
