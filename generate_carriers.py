import wave
import os
import sys
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


def generate_stereo_pocket(path: str, duration: float = 60.0):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    base = VILLAGE_STANDARD_HZ

    left = (
        np.sin(2 * np.pi * base * t) * 8000
        + np.sin(2 * np.pi * (base * 2) * t) * 4000
        + np.sin(2 * np.pi * (base * 3) * t) * 2000
        + np.sin(2 * np.pi * (base * 0.5) * t) * 3000
    )
    lfo = 1.0 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
    left = (left * lfo).astype(np.int16)

    phase_shift = np.pi / 2
    right_base = np.sin(2 * np.pi * base * t + phase_shift) * 6000
    right_h2 = np.sin(2 * np.pi * (base * 2) * t + phase_shift) * 3000
    right_h3 = np.sin(2 * np.pi * (base * 3) * t + phase_shift) * 1500

    breath_lfo = 0.4 + 0.6 * (0.5 * (1 + np.sin(2 * np.pi * 0.08 * t)))
    right = (right_base + right_h2 + right_h3) * breath_lfo

    pocket_depth = np.abs(np.sin(2 * np.pi * 0.05 * t))
    right = right * (1.0 - 0.3 * pocket_depth)
    right = right.astype(np.int16)

    stereo = np.empty(n * 2, dtype=np.int16)
    stereo[0::2] = left
    stereo[1::2] = right

    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(stereo.tobytes())

    print(f"  Generated: {path} ({os.path.getsize(path):,} bytes) — {duration}s stereo pocket @ {base} Hz")
    print(f"             L: 432 Hz body | R: Phase-shifted pocket (Adriana Pocket)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stereo_mode = "--stereo" in sys.argv

    print(f"\n  VILLAGE STANDARD CARRIER GENERATOR")
    print(f"  Base Frequency: {VILLAGE_STANDARD_HZ} Hz")
    if stereo_mode:
        print(f"  Mode: STEREO — Adriana Pocket (L: Body, R: Phase-Shifted Pocket)\n")
    else:
        print(f"  Mode: MONO\n")

    if stereo_mode:
        duration = 60.0
        for arg in sys.argv[1:]:
            try:
                duration = float(arg)
                break
            except ValueError:
                continue
        generate_stereo_pocket(os.path.join(OUTPUT_DIR, f"stereo_pocket_{int(duration)}s.wav"), duration)
    else:
        generate_ambient_drone(os.path.join(OUTPUT_DIR, "ambient_drone_60s.wav"))
        generate_harmonic_mix(os.path.join(OUTPUT_DIR, "harmonic_mix_45s.wav"))
        generate_pink_noise(os.path.join(OUTPUT_DIR, "pink_noise_30s.wav"))

    print(f"\n  All carriers tuned to {VILLAGE_STANDARD_HZ} Hz Village Standard.\n")


CLASSIC_STYLES = {"drone", "harmonic", "pink_noise", "stereo_pocket"}
INSECT_STYLES = {"cicada_wall", "cricket_pulse"}
BIOPHONY_STYLES = {"midnight_pond", "biophony_mesh"}
ALL_STYLES = CLASSIC_STYLES | INSECT_STYLES | BIOPHONY_STYLES


def _stream_classic_carrier(path, duration, style, sample_rate=SAMPLE_RATE, chunk_seconds=30.0):
    n_chunks = max(1, int(np.ceil(duration / chunk_seconds)))
    is_stereo = (style == "stereo_pocket")
    n_channels = 2 if is_stereo else 1

    with wave.open(path, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        for chunk_i in range(n_chunks):
            chunk_dur = min(chunk_seconds, duration - chunk_i * chunk_seconds)
            if chunk_dur <= 0:
                break

            n = int(sample_rate * chunk_dur)
            t_offset = chunk_i * chunk_seconds
            t = np.linspace(t_offset, t_offset + chunk_dur, n, endpoint=False)

            base = VILLAGE_STANDARD_HZ

            if style == "drone":
                signal = (
                    np.sin(2 * np.pi * base * t) * 8000
                    + np.sin(2 * np.pi * (base * 2) * t) * 4000
                    + np.sin(2 * np.pi * (base * 3) * t) * 2000
                    + np.sin(2 * np.pi * (base * 0.5) * t) * 3000
                )
                lfo = 1.0 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
                signal = (signal * lfo).astype(np.int16)
                wf.writeframes(signal.tobytes())

            elif style == "harmonic":
                harmonics = [base, base * 5/4, base * 3/2, base * 2, base * 9/4]
                signal = np.zeros(n, dtype=np.float64)
                for i, freq in enumerate(harmonics):
                    amp = 6000 / (i + 1)
                    phase = np.random.uniform(0, 2 * np.pi)
                    signal += np.sin(2 * np.pi * freq * t + phase) * amp
                signal = np.clip(signal, -32000, 32000).astype(np.int16)
                wf.writeframes(signal.tobytes())

            elif style == "pink_noise":
                np.random.seed(432 + chunk_i)
                white = np.random.randn(n)
                fft = np.fft.rfft(white)
                freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
                freqs[0] = 1.0
                fft /= np.sqrt(freqs)
                pink = np.fft.irfft(fft, n=n)
                t_local = np.linspace(0, chunk_dur, n, endpoint=False)
                tone = np.sin(2 * np.pi * base * (t_local + t_offset)) * 2000
                signal = pink / max(np.max(np.abs(pink)), 1e-10) * 12000 + tone
                signal = np.clip(signal, -32000, 32000).astype(np.int16)
                wf.writeframes(signal.tobytes())

            elif style == "stereo_pocket":
                left = (
                    np.sin(2 * np.pi * base * t) * 8000
                    + np.sin(2 * np.pi * (base * 2) * t) * 4000
                    + np.sin(2 * np.pi * (base * 3) * t) * 2000
                    + np.sin(2 * np.pi * (base * 0.5) * t) * 3000
                )
                lfo = 1.0 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
                left = (left * lfo).astype(np.int16)

                phase_shift = np.pi / 2
                right_base = np.sin(2 * np.pi * base * t + phase_shift) * 6000
                right_h2 = np.sin(2 * np.pi * (base * 2) * t + phase_shift) * 3000
                right_h3 = np.sin(2 * np.pi * (base * 3) * t + phase_shift) * 1500
                breath_lfo = 0.4 + 0.6 * (0.5 * (1 + np.sin(2 * np.pi * 0.08 * t)))
                right = (right_base + right_h2 + right_h3) * breath_lfo
                pocket_depth = np.abs(np.sin(2 * np.pi * 0.05 * t))
                right = right * (1.0 - 0.3 * pocket_depth)
                right = right.astype(np.int16)

                stereo = np.empty(n * 2, dtype=np.int16)
                stereo[0::2] = left
                stereo[1::2] = right
                wf.writeframes(stereo.tobytes())

            print(f"  [CARRIER] Chunk {chunk_i + 1}/{n_chunks} written ({chunk_dur:.1f}s) — {style}")

    print(f"  [CARRIER] Generated: {path} ({os.path.getsize(path):,} bytes) — {duration:.0f}s {style}")
    return path


def generate_custom_carrier(duration_minutes, style, sample_rate=SAMPLE_RATE):
    from void_engine.biophony import generate_biophony_carrier

    if duration_minutes < 1 or duration_minutes > 300:
        raise ValueError(f"Duration must be between 1 and 300 minutes, got {duration_minutes}")

    if style not in ALL_STYLES:
        raise ValueError(f"Unknown style '{style}'. Valid: {sorted(ALL_STYLES)}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    duration = duration_minutes * 60.0

    style_tag = style.replace("_", "-")
    filename = f"carrier_{style_tag}_{duration_minutes}min.wav"
    output_path = os.path.join(OUTPUT_DIR, filename)

    chirpmap_path = None
    chirp_count = 0

    if style in CLASSIC_STYLES:
        _stream_classic_carrier(output_path, duration, style, sample_rate)
    else:
        output_path, chirpmap_path, chirp_count = generate_biophony_carrier(
            output_path, duration_minutes, style=style, sample_rate=sample_rate
        )

    capacity = estimate_carrier_capacity(duration_minutes, style, sample_rate)

    result = {
        "filename": os.path.basename(output_path),
        "path": output_path,
        "file_size": os.path.getsize(output_path),
        "duration_minutes": duration_minutes,
        "style": style,
        "capacity": capacity,
    }

    if chirpmap_path and os.path.exists(chirpmap_path):
        result["chirpmap"] = os.path.basename(chirpmap_path)
        result["chirp_count"] = chirp_count
        result["chirp_rate"] = capacity.get("chirp_rate", 0)

    return result


def estimate_carrier_capacity(duration_minutes, style, sample_rate=SAMPLE_RATE):
    duration = duration_minutes * 60.0
    n_samples = int(sample_rate * duration)

    is_stereo = style in ("midnight_pond", "biophony_mesh", "stereo_pocket")
    n_channels = 2 if is_stereo else 1
    total_samples = n_samples * n_channels

    raw_lsb1 = total_samples // 8 - 64
    raw_lsb2 = (total_samples * 2) // 8 - 64

    density_multipliers = {
        "cicada_wall": 5.0,
        "cricket_pulse": 2.5,
        "midnight_pond": 5.0,
        "biophony_mesh": 5.0,
        "drone": 1.0,
        "harmonic": 1.0,
        "pink_noise": 1.0,
        "stereo_pocket": 1.0,
    }
    multiplier = density_multipliers.get(style, 1.0)

    wav_size = total_samples * 2 + 44

    effective_lsb1 = int(raw_lsb1 * multiplier)
    effective_lsb2 = int(raw_lsb2 * multiplier)

    chirp_rate = 0
    peaks_per_sec = 0
    if style in ("cicada_wall", "midnight_pond", "biophony_mesh"):
        chirp_rate = 35
        peaks_per_sec = chirp_rate * 50
    elif style == "cricket_pulse":
        chirp_rate = 10
        peaks_per_sec = chirp_rate * 10

    is_biophony = style in INSECT_STYLES | BIOPHONY_STYLES

    def _human_size(b):
        for unit in ("B", "KB", "MB", "GB"):
            if abs(b) < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"

    result = {
        "duration_minutes": duration_minutes,
        "duration_seconds": duration,
        "style": style,
        "channels": n_channels,
        "wav_size": wav_size,
        "wav_size_human": _human_size(wav_size),
        "raw_lsb1": raw_lsb1,
        "raw_lsb2": raw_lsb2,
        "raw_lsb1_human": _human_size(raw_lsb1),
        "raw_lsb2_human": _human_size(raw_lsb2),
        "density_multiplier": multiplier,
        "effective_lsb1": effective_lsb1,
        "effective_lsb2": effective_lsb2,
        "effective_lsb1_human": _human_size(effective_lsb1),
        "effective_lsb2_human": _human_size(effective_lsb2),
        "chirp_rate": chirp_rate,
        "peaks_per_sec": peaks_per_sec,
        "is_biophony": is_biophony,
    }

    if style in BIOPHONY_STYLES:
        result["shelf_breakdown"] = {
            "whale_capacity": "10 agents @ 15-50 Hz — LSB1 chassis for heavy data blocks",
            "bird_headers": "20 agents @ 300-800 Hz — Floating Parity Headers (hash-keyed triggers)",
            "insect_silt": "970 agents @ 2-12 kHz — LSB2 silt mask (compressed data layer)",
        }

    return result


if __name__ == "__main__":
    main()
