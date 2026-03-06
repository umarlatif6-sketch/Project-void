import numpy as np
import wave
import os
import struct

SAMPLE_RATE = 44100
DURATION = 5.0
BASE_FREQ = 432
GOLDEN_RATIO = 1.6180339887


def generate_gift_chime(amount, gift_hash):
    os.makedirs("uploads/chimes", exist_ok=True)

    n = int(SAMPLE_RATE * DURATION)
    t = np.linspace(0, DURATION, n, endpoint=False)

    if amount >= 100:
        signal = _sovereign_chime(t, n)
    elif amount >= 10:
        signal = _medium_chime(t, n)
    else:
        signal = _small_chime(t, n)

    left = signal.copy()
    right = signal.copy()

    stereo = np.empty(n * 2, dtype=np.float64)
    stereo[0::2] = left
    stereo[1::2] = right

    max_val = np.max(np.abs(stereo))
    if max_val > 0:
        stereo = stereo / max_val * 30000.0

    stereo = np.clip(stereo, -32768, 32767).astype(np.int16)

    safe_hash = gift_hash.replace("/", "_").replace("\\", "_")[:32]
    filename = f"chime_{safe_hash}.wav"
    filepath = os.path.join("uploads", "chimes", filename)

    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(stereo.tobytes())

    _embed_watermark(filepath, gift_hash)

    return filepath


def _small_chime(t, n):
    fade_in = np.linspace(0, 1, int(n * 0.1))
    fade_out = np.linspace(1, 0, int(n * 0.3))
    sustain = np.ones(n - len(fade_in) - len(fade_out))
    envelope = np.concatenate([fade_in, sustain, fade_out])

    signal = np.sin(2 * np.pi * BASE_FREQ * t) * envelope * 0.6

    tremolo = 0.5 + 0.5 * np.sin(2 * np.pi * 2.0 * t)
    signal *= tremolo

    return signal


def _medium_chime(t, n):
    fade_in = np.linspace(0, 1, int(n * 0.08))
    fade_out = np.linspace(1, 0, int(n * 0.25))
    sustain = np.ones(n - len(fade_in) - len(fade_out))
    envelope = np.concatenate([fade_in, sustain, fade_out])

    tone1 = np.sin(2 * np.pi * BASE_FREQ * t)
    tone2 = np.sin(2 * np.pi * 648 * t) * 0.5

    am_rate = BASE_FREQ / GOLDEN_RATIO / 100.0
    am = 0.6 + 0.4 * np.sin(2 * np.pi * am_rate * t)

    signal = (tone1 + tone2) * envelope * am * 0.5

    return signal


def _sovereign_chime(t, n):
    fade_in = np.linspace(0, 1, int(n * 0.05))
    fade_out = np.linspace(1, 0, int(n * 0.2))
    sustain = np.ones(n - len(fade_in) - len(fade_out))
    envelope = np.concatenate([fade_in, sustain, fade_out])

    freqs = [432, 648, 864, 1296]
    amps = [1.0, 0.5, 0.3, 0.15]

    signal = np.zeros(n, dtype=np.float64)
    for freq, amp in zip(freqs, amps):
        signal += np.sin(2 * np.pi * freq * t) * amp

    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.5 * t)
    signal *= lfo

    resonance_peak = np.exp(-((t - 2.5) ** 2) / (2 * 0.5 ** 2))
    signal *= (1.0 + resonance_peak * 0.4)

    signal *= envelope * 0.4

    return signal


def _embed_watermark(filepath, gift_hash):
    hash_bytes = gift_hash.encode("utf-8")[:32]
    hash_bytes = hash_bytes.ljust(32, b"\x00")

    with open(filepath, "r+b") as f:
        f.seek(-32, 2)
        f.write(hash_bytes)
