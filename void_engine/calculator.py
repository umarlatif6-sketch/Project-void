import wave
import os
import numpy as np
from datetime import datetime


HEADER_OVERHEAD = 64
VILLAGE_STANDARD_HZ = 432
RESONANCE_THRESHOLD_LSB1 = 0.25
RESONANCE_THRESHOLD_LSB2 = 0.15
RESONANCE_BONUS = 0.05
RESONANCE_KEYWORDS = ("432hz", "432_hz", "432-hz", "resonate")
BUBBLE_BURST_MARGIN = 0.90
LOG_FILE = "RESONANCE_LOG.md"


def _is_resonant_carrier(filename: str) -> bool:
    lower = filename.lower()
    return any(kw in lower for kw in RESONANCE_KEYWORDS)


def _compute_resonance_score(wav_path: str, sample_rate: int, n_frames: int, n_channels: int) -> dict:
    with wave.open(wav_path, "rb") as wf:
        raw = wf.readframes(n_frames)

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if n_channels > 1:
        samples = samples[::n_channels]

    window_size = min(len(samples), 4096 * 4)
    segment = samples[:window_size]
    windowed = segment * np.hanning(len(segment))

    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(segment), 1.0 / sample_rate)

    target_hz = VILLAGE_STANDARD_HZ
    band_width = 20

    band_mask = (freqs >= target_hz - band_width) & (freqs <= target_hz + band_width)
    noise_mask = ~band_mask & (freqs > 50)

    signal_power = np.mean(spectrum[band_mask] ** 2) if np.any(band_mask) else 0
    noise_power = np.mean(spectrum[noise_mask] ** 2) if np.any(noise_mask) else 1e-10
    total_power = np.mean(spectrum ** 2) if len(spectrum) > 0 else 1e-10

    harmonic_powers = []
    for mult in [1, 2, 3, 0.5]:
        h_freq = target_hz * mult
        h_mask = (freqs >= h_freq - band_width) & (freqs <= h_freq + band_width)
        h_power = np.mean(spectrum[h_mask] ** 2) if np.any(h_mask) else 0
        harmonic_powers.append(h_power)

    harmonic_sum = sum(harmonic_powers)
    resonance_ratio = float(harmonic_sum / total_power) if total_power > 0 else 0.0
    resonance_score = min(1.0, resonance_ratio * 5.0)

    snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 0

    return {
        "resonance_score": round(float(resonance_score), 4),
        "snr_db": round(float(snr_db), 1),
        "harmonic_energy_ratio": round(float(resonance_ratio), 4),
    }


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
    filename = os.path.basename(wav_path)

    cap_1bit = total_samples // 8
    cap_2bit = (total_samples * 2) // 8

    usable_1bit = max(0, cap_1bit - HEADER_OVERHEAD)
    usable_2bit = max(0, cap_2bit - HEADER_OVERHEAD)

    resonant = _is_resonant_carrier(filename)
    threshold_1 = RESONANCE_THRESHOLD_LSB1 + (RESONANCE_BONUS if resonant else 0)
    threshold_2 = RESONANCE_THRESHOLD_LSB2

    res_info = _compute_resonance_score(wav_path, sample_rate, n_frames, n_channels)
    resonance_score = res_info["resonance_score"]

    capacity_boost = resonance_score * 0.10
    effective_threshold_1 = min(0.50, threshold_1 + capacity_boost)
    effective_threshold_2 = min(0.35, threshold_2 + capacity_boost)

    tension_1bit = int(usable_1bit * effective_threshold_1)
    tension_2bit = int(usable_2bit * effective_threshold_2)

    burst_1bit = int(tension_1bit * BUBBLE_BURST_MARGIN)
    burst_2bit = int(tension_2bit * BUBBLE_BURST_MARGIN)

    dynamic_tension_1bit = int(usable_1bit * effective_threshold_1)
    dynamic_tension_2bit = int(usable_2bit * effective_threshold_2)

    bitrate_1 = sample_rate * n_channels / 8
    bitrate_2 = sample_rate * n_channels * 2 / 8

    return {
        "filename": filename,
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
        "surface_tension_1bit": tension_1bit,
        "surface_tension_2bit": tension_2bit,
        "bubble_burst_1bit": burst_1bit,
        "bubble_burst_2bit": burst_2bit,
        "resonance_limit_1bit": tension_1bit,
        "resonance_limit_2bit": tension_2bit,
        "header_overhead": HEADER_OVERHEAD,
        "resonant_carrier": resonant,
        "threshold_lsb1": effective_threshold_1,
        "threshold_lsb2": effective_threshold_2,
        "resonance_score": resonance_score,
        "resonance_snr_db": res_info["snr_db"],
        "harmonic_energy_ratio": res_info["harmonic_energy_ratio"],
        "dynamic_tension": {
            "lsb1": dynamic_tension_1bit,
            "lsb2": dynamic_tension_2bit,
            "boost_pct": round(capacity_boost * 100, 1),
        },
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
    if info.get("resonant_carrier"):
        print(f"  432 Hz Boost: +5% resonance threshold (LSB1 → {info['threshold_lsb1']:.0%})")
    print()
    print(f"  {'─' * 56}")
    print(f"  LSB DEPTH 1 (Stealth Mode)")
    print(f"  {'─' * 56}")
    print(f"  Data rate:          {format_size(int(info['bitrate_1bit']))}/sec")
    print(f"  Max capacity:       {format_size(info['capacity_1bit'])}")
    print(f"  Surface tension:    {format_size(info['surface_tension_1bit'])}")
    print(f"  Bubble burst at:    {format_size(info['bubble_burst_1bit'])} (90% membrane)")
    print(f"  Est. compressed:    ~{format_size(info['surface_tension_1bit'] * 3)} to ~{format_size(info['surface_tension_1bit'] * 5)} of real data")
    print()
    print(f"  {'─' * 56}")
    print(f"  LSB DEPTH 2 (High Capacity)")
    print(f"  {'─' * 56}")
    print(f"  Data rate:          {format_size(int(info['bitrate_2bit']))}/sec")
    print(f"  Max capacity:       {format_size(info['capacity_2bit'])}")
    print(f"  Surface tension:    {format_size(info['surface_tension_2bit'])}")
    print(f"  Bubble burst at:    {format_size(info['bubble_burst_2bit'])} (90% membrane)")
    print(f"  Est. compressed:    ~{format_size(info['surface_tension_2bit'] * 3)} to ~{format_size(info['surface_tension_2bit'] * 5)} of real data")
    print()
    print(f"  {'─' * 56}")
    print(f"  NOTES")
    print(f"  {'─' * 56}")
    print(f"  - Below surface tension: bubble holds — audio sounds clean")
    print(f"  - Near bubble burst: membrane is stretching — distortion risk")
    print(f"  - Above burst: bubble pops — audible artifacts")
    print(f"  - 'Est. compressed' = real file sizes after zlib/lzma")
    print(f"  - Complex audio (noise, music) = thicker bubble skin")
    print(f"  - Optimized for Node: Mac 2012 / Phone Bridge")
    print(f"  {'=' * 56}")


def append_to_log(info: dict):
    log_path = LOG_FILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    is_new = not os.path.exists(log_path)

    with open(log_path, "a") as f:
        if is_new:
            f.write("# RESONANCE LOG\n\n")
            f.write("Carrier analysis history — generated by the Resonance Meter.\n\n")
            f.write("---\n\n")

        resonant_tag = " [432 Hz BOOSTED]" if info.get("resonant_carrier") else ""
        f.write(f"### {timestamp} — {info['filename']}{resonant_tag}\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|---|---|\n")
        f.write(f"| Duration | {info['duration']:.1f}s |\n")
        f.write(f"| Channels | {info['channels']} |\n")
        f.write(f"| Sample Rate | {info['sample_rate']:,} Hz |\n")
        f.write(f"| Total Samples | {info['total_samples']:,} |\n")
        f.write(f"| LSB1 Max Capacity | {format_size(info['capacity_1bit'])} |\n")
        f.write(f"| LSB1 Surface Tension | {format_size(info['surface_tension_1bit'])} |\n")
        f.write(f"| LSB1 Bubble Burst | {format_size(info['bubble_burst_1bit'])} |\n")
        f.write(f"| LSB1 Est. Real Data | ~{format_size(info['surface_tension_1bit'] * 3)} to ~{format_size(info['surface_tension_1bit'] * 5)} |\n")
        f.write(f"| LSB2 Max Capacity | {format_size(info['capacity_2bit'])} |\n")
        f.write(f"| LSB2 Surface Tension | {format_size(info['surface_tension_2bit'])} |\n")
        f.write(f"| LSB2 Bubble Burst | {format_size(info['bubble_burst_2bit'])} |\n")
        f.write(f"| LSB2 Est. Real Data | ~{format_size(info['surface_tension_2bit'] * 3)} to ~{format_size(info['surface_tension_2bit'] * 5)} |\n")
        f.write(f"\n---\n\n")

    print(f"  [LOG] Analysis appended to {log_path}")
