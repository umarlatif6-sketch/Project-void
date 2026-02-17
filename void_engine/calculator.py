import wave
import os


HEADER_OVERHEAD = 64
RESONANCE_THRESHOLD_LSB1 = 0.25
RESONANCE_THRESHOLD_LSB2 = 0.15


def analyze_carrier(wav_path: str) -> dict:
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"File not found: {wav_path}")

    with wave.open(wav_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()

    if sampwidth != 2:
        raise ValueError(f"Only 16-bit WAV supported (got {sampwidth * 8}-bit)")

    total_samples = n_frames * n_channels
    duration = n_frames / sample_rate
    file_size = os.path.getsize(wav_path)

    cap_1bit = total_samples // 8
    cap_2bit = (total_samples * 2) // 8

    usable_1bit = max(0, cap_1bit - HEADER_OVERHEAD)
    usable_2bit = max(0, cap_2bit - HEADER_OVERHEAD)

    resonance_1bit = int(usable_1bit * RESONANCE_THRESHOLD_LSB1)
    resonance_2bit = int(usable_2bit * RESONANCE_THRESHOLD_LSB2)

    bitrate_1 = sample_rate * n_channels / 8
    bitrate_2 = sample_rate * n_channels * 2 / 8

    return {
        "filename": os.path.basename(wav_path),
        "file_size": file_size,
        "channels": n_channels,
        "sample_rate": sample_rate,
        "bit_depth": sampwidth * 8,
        "duration": duration,
        "total_samples": total_samples,
        "capacity_1bit": usable_1bit,
        "capacity_2bit": usable_2bit,
        "bitrate_1bit": bitrate_1,
        "bitrate_2bit": bitrate_2,
        "resonance_limit_1bit": resonance_1bit,
        "resonance_limit_2bit": resonance_2bit,
        "header_overhead": HEADER_OVERHEAD,
    }


def format_size(bytes_val: int) -> str:
    if bytes_val >= 1_073_741_824:
        return f"{bytes_val / 1_073_741_824:.2f} GB"
    elif bytes_val >= 1_048_576:
        return f"{bytes_val / 1_048_576:.1f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.1f} KB"
    return f"{bytes_val:,} B"


def print_analysis(info: dict):
    print(f"\n  {'=' * 56}")
    print(f"  RESONANCE METER — Carrier Analysis")
    print(f"  {'=' * 56}")
    print(f"  File:         {info['filename']}")
    print(f"  File size:    {format_size(info['file_size'])}")
    print(f"  Duration:     {info['duration']:.1f} seconds")
    print(f"  Sample rate:  {info['sample_rate']:,} Hz")
    print(f"  Channels:     {info['channels']}")
    print(f"  Bit depth:    {info['bit_depth']}-bit")
    print(f"  Total samples:{info['total_samples']:,}")
    print()
    print(f"  {'─' * 56}")
    print(f"  LSB DEPTH 1 (Stealth Mode)")
    print(f"  {'─' * 56}")
    print(f"  Data rate:        {format_size(int(info['bitrate_1bit']))}/sec")
    print(f"  Max capacity:     {format_size(info['capacity_1bit'])}")
    print(f"  Resonance limit:  {format_size(info['resonance_limit_1bit'])}")
    print(f"  Est. compressed:  ~{format_size(info['resonance_limit_1bit'] * 3)} to ~{format_size(info['resonance_limit_1bit'] * 5)} of real data")
    print()
    print(f"  {'─' * 56}")
    print(f"  LSB DEPTH 2 (High Capacity)")
    print(f"  {'─' * 56}")
    print(f"  Data rate:        {format_size(int(info['bitrate_2bit']))}/sec")
    print(f"  Max capacity:     {format_size(info['capacity_2bit'])}")
    print(f"  Resonance limit:  {format_size(info['resonance_limit_2bit'])}")
    print(f"  Est. compressed:  ~{format_size(info['resonance_limit_2bit'] * 3)} to ~{format_size(info['resonance_limit_2bit'] * 5)} of real data")
    print()
    print(f"  {'─' * 56}")
    print(f"  NOTES")
    print(f"  {'─' * 56}")
    print(f"  - Below resonance limit: audio sounds clean")
    print(f"  - Above limit: distortion may become audible")
    print(f"  - 'Est. compressed' = real file sizes after zlib/lzma")
    print(f"  - Complex audio (noise, music) hides data better")
    print(f"  {'=' * 56}")
