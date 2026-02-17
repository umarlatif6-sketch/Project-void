import wave
import os
import numpy as np

VILLAGE_STANDARD_HZ = 432
SAMPLE_RATE = 44100
OUTPUT_DIR = "input_files"


def generate_ambient_drone(path: str, duration: float = 60.0):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    base = VILLAGE_STANDARD_HZ
    signal = (
        np.sin(2 * np.pi * base * t) * 8000
        + np.sin(2 * np.pi * (base * 2) * t) * 4000
        + np.sin(2 * np.pi * (base * 3) * t) * 2000
        + np.sin(2 * np.pi * (base * 0.5) * t) * 3000
    )

    lfo = 1.0 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
    signal = (signal * lfo).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(signal.tobytes())

    print(f"  Generated: {path} ({os.path.getsize(path):,} bytes) — {duration}s ambient drone @ {base} Hz")


def generate_harmonic_mix(path: str, duration: float = 45.0):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    base = VILLAGE_STANDARD_HZ
    harmonics = [base, base * 5/4, base * 3/2, base * 2, base * 9/4]
    signal = np.zeros(n, dtype=np.float64)

    for i, freq in enumerate(harmonics):
        amp = 6000 / (i + 1)
        phase = np.random.uniform(0, 2 * np.pi)
        signal += np.sin(2 * np.pi * freq * t + phase) * amp

    signal = np.clip(signal, -32000, 32000).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(signal.tobytes())

    print(f"  Generated: {path} ({os.path.getsize(path):,} bytes) — {duration}s harmonic mix @ {base} Hz")


def generate_pink_noise(path: str, duration: float = 30.0):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    np.random.seed(432)
    white = np.random.randn(n)

    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE)
    freqs[0] = 1.0
    fft /= np.sqrt(freqs)
    pink = np.fft.irfft(fft, n=n)

    base = VILLAGE_STANDARD_HZ
    tone = np.sin(2 * np.pi * base * t) * 2000
    signal = pink / np.max(np.abs(pink)) * 12000 + tone

    signal = np.clip(signal, -32000, 32000).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(signal.tobytes())

    print(f"  Generated: {path} ({os.path.getsize(path):,} bytes) — {duration}s pink noise + {base} Hz tone")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n  VILLAGE STANDARD CARRIER GENERATOR")
    print(f"  Base Frequency: {VILLAGE_STANDARD_HZ} Hz\n")

    generate_ambient_drone(os.path.join(OUTPUT_DIR, "ambient_drone_60s.wav"))
    generate_harmonic_mix(os.path.join(OUTPUT_DIR, "harmonic_mix_45s.wav"))
    generate_pink_noise(os.path.join(OUTPUT_DIR, "pink_noise_30s.wav"))

    print(f"\n  All carriers tuned to {VILLAGE_STANDARD_HZ} Hz Village Standard.\n")


if __name__ == "__main__":
    main()
