#!/usr/bin/env python3
"""Probe heartbeat WAV metrics for quick field validation.

Usage:
  python3 scripts/heartbeat_probe.py
  python3 scripts/heartbeat_probe.py --wav output_audio/heartbeat_432Hz.wav
"""

from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np


def _read_wav_mono(path: Path) -> tuple[np.ndarray, int, int]:
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sample_rate = wf.getframerate()
        frames = wf.getnframes()
        raw = wf.readframes(frames)

    if sampwidth == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth}")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    return data, sample_rate, channels


def dominant_freq(samples: np.ndarray, sample_rate: int) -> float:
    if samples.size < 2048 or sample_rate <= 0:
        return 0.0
    n = min(samples.size, 131072)
    windowed = samples[:n] * np.hanning(n)
    spec = np.fft.rfft(windowed)
    mag = np.abs(spec)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    mag[0] = 0.0
    peak_idx = int(np.argmax(mag))
    return float(freqs[peak_idx])


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe heartbeat WAV metrics")
    parser.add_argument("--wav", default="output_audio/heartbeat_432Hz.wav", help="Path to heartbeat WAV")
    args = parser.parse_args()

    wav_path = Path(args.wav)
    if not wav_path.exists():
        print(f"ERROR: file not found: {wav_path}")
        return 2

    samples, sample_rate, channels = _read_wav_mono(wav_path)
    dom_hz = dominant_freq(samples, sample_rate)
    rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
    duration_s = float(samples.size / sample_rate) if sample_rate > 0 else 0.0

    print("heartbeat_probe")
    print(f"wav={wav_path}")
    print(f"sample_rate={sample_rate}")
    print(f"channels_in_file={channels}")
    print(f"duration_s={duration_s:.3f}")
    print(f"dominant_hz={dom_hz:.3f}")
    print(f"rms={rms:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
