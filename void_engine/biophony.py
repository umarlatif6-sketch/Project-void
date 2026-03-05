import numpy as np
import wave
import os

def hilbert(x):
    N = len(x)
    X = np.fft.fft(x)
    h = np.zeros(N)
    if N > 0:
        h[0] = 1
        if N % 2 == 0:
            h[N // 2] = 1
            h[1:N // 2] = 2
        else:
            h[1:(N + 1) // 2] = 2
    return np.fft.ifft(X * h)

VILLAGE_STANDARD_HZ = 432
SAMPLE_RATE = 44100
CHUNK_DURATION = 30.0


class BiophonyMesh:
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr

    def _synthesize_whale_shelf(self, duration, n_whales=10):
        n = int(self.sr * duration)
        t = np.linspace(0, duration, n, endpoint=False)
        whale_mix = np.zeros(n, dtype=np.float64)

        for i in range(n_whales):
            freq_start = 15 + (i * 3.5)
            freq_end = 50 - (i * 2.5)
            freq_start = max(15, min(freq_start, 50))
            freq_end = max(15, min(freq_end, 50))
            freq = np.linspace(freq_start, freq_end, n)
            phase_offset = i * np.pi / n_whales
            lfo = 0.5 * (1 + np.sin(2 * np.pi * 0.03 * t + phase_offset))
            phase = np.cumsum(2 * np.pi * freq / self.sr)
            whale_mix += np.sin(phase) * lfo * (6000 / n_whales)

        return whale_mix

    def _synthesize_bird_shelf(self, duration, n_birds=20, passphrase_seed=432):
        n = int(self.sr * duration)
        bird_mix = np.zeros(n, dtype=np.float64)
        rng = np.random.RandomState(passphrase_seed)

        harmonic_freqs = [
            VILLAGE_STANDARD_HZ,
            VILLAGE_STANDARD_HZ * 3 / 2,
            VILLAGE_STANDARD_HZ * 7 / 4,
        ]

        tap_interval = 2.5
        n_taps_per_bird = int(duration / tap_interval)

        for bird_i in range(n_birds):
            freq = harmonic_freqs[bird_i % len(harmonic_freqs)]
            freq *= (1.0 + rng.uniform(-0.02, 0.02))

            attack_samples = int(0.002 * self.sr)
            decay_samples = int(0.050 * self.sr)
            tap_len = attack_samples + decay_samples

            for tap_j in range(n_taps_per_bird):
                jitter_s = rng.uniform(-0.3, 0.3)
                tap_time = tap_j * tap_interval + (bird_i * tap_interval / n_birds) + jitter_s
                tap_start = int(tap_time * self.sr)
                if tap_start < 0 or tap_start + tap_len >= n:
                    continue

                t_tap = np.arange(tap_len) / self.sr
                envelope = np.zeros(tap_len)
                envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
                envelope[attack_samples:] = np.exp(-np.linspace(0, 5, decay_samples))

                tap_signal = np.sin(2 * np.pi * freq * t_tap) * envelope * 4000
                end_idx = min(tap_start + tap_len, n)
                actual_len = end_idx - tap_start
                bird_mix[tap_start:end_idx] += tap_signal[:actual_len]

        return bird_mix

    def _synthesize_insect_shelf(self, duration, n_insects=970, base_chirp_rate=35):
        n = int(self.sr * duration)
        insect_mix = np.zeros(n, dtype=np.float64)
        chirp_peaks = []

        n_groups = min(n_insects, 50)
        insects_per_group = n_insects // n_groups

        rng = np.random.RandomState(970)

        for g in range(n_groups):
            group_freq = rng.uniform(2000, 12000)
            group_chirp_rate = base_chirp_rate + rng.uniform(-5, 5)
            group_phase = rng.uniform(0, 2 * np.pi)

            chirp_period = self.sr / group_chirp_rate
            attack_samples = int(0.005 * self.sr)
            sustain_samples = int(0.015 * self.sr)
            decay_samples = int(0.010 * self.sr)
            chirp_len = attack_samples + sustain_samples + decay_samples

            chirp_envelope = np.zeros(chirp_len)
            chirp_envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
            chirp_envelope[attack_samples:attack_samples + sustain_samples] = 1.0
            chirp_envelope[attack_samples + sustain_samples:] = np.linspace(1, 0, decay_samples)

            t_chirp = np.arange(chirp_len) / self.sr
            chirp_tone = np.sin(2 * np.pi * group_freq * t_chirp + group_phase)
            single_chirp = chirp_tone * chirp_envelope

            pos = int(rng.uniform(0, chirp_period * 0.5))
            amplitude = insects_per_group * 8.0

            while pos + chirp_len < n:
                end_pos = min(pos + chirp_len, n)
                actual_len = end_pos - pos
                insect_mix[pos:end_pos] += single_chirp[:actual_len] * amplitude

                peak_idx = pos + attack_samples + sustain_samples // 2
                if peak_idx < n:
                    chirp_peaks.append(peak_idx)

                interval = int(chirp_period + rng.uniform(-chirp_period * 0.1, chirp_period * 0.1))
                pos += max(chirp_len, interval)

        chirp_peaks = sorted(set(chirp_peaks))
        return insect_mix, np.array(chirp_peaks, dtype=np.int64)

    def _apply_sympathetic_resonance(self, whale_signal, insect_signal):
        analytic_signal = hilbert(whale_signal)
        amplitude_envelope = np.abs(analytic_signal)

        max_amp = np.max(amplitude_envelope)
        if max_amp > 0:
            norm_envelope = amplitude_envelope / max_amp
        else:
            norm_envelope = amplitude_envelope

        resonant_mesh = insect_signal * (1.0 + (norm_envelope * 0.5))
        return resonant_mesh

    def _apply_shadow_layer(self, signal, shadow_type="nature"):
        n = len(signal)
        rng = np.random.RandomState(432)

        if shadow_type == "nature":
            white_noise = rng.normal(0, 1, n)
            brown_noise = np.cumsum(white_noise)
            brown_max = np.max(np.abs(brown_noise))
            if brown_max > 0:
                shadow = (brown_noise / brown_max) * 0.0316
            else:
                shadow = np.zeros(n)
        elif shadow_type == "tone":
            t = np.linspace(0, n / self.sr, n, endpoint=False)
            shadow = 0.01 * np.sin(2 * np.pi * VILLAGE_STANDARD_HZ * t)
        else:
            shadow = np.zeros(n)

        return signal + shadow

    def synthesize_mesh(self, duration):
        whales = self._synthesize_whale_shelf(duration)
        birds = self._synthesize_bird_shelf(duration)
        insects, chirp_peaks = self._synthesize_insect_shelf(duration)

        coupled_insects = self._apply_sympathetic_resonance(whales, insects)

        left = whales + birds + coupled_insects
        left = self._apply_shadow_layer(left, "nature")

        right = coupled_insects.copy()

        max_val = max(np.max(np.abs(left)), np.max(np.abs(right)), 1.0)
        if max_val > 30000:
            scale = 30000.0 / max_val
            left *= scale
            right *= scale

        left = np.clip(left, -32768, 32767).astype(np.int16)
        right = np.clip(right, -32768, 32767).astype(np.int16)

        stereo = np.empty(len(left) * 2, dtype=np.int16)
        stereo[0::2] = left
        stereo[1::2] = right

        metadata = {
            "n_whales": 10,
            "n_birds": 20,
            "n_insects": 970,
            "shelves": ["whale_15-50Hz", "bird_300-800Hz", "insect_2-12kHz"],
            "sympathetic_resonance": True,
            "shadow_layer": "nature",
            "chirp_peaks_count": len(chirp_peaks),
        }

        return stereo, chirp_peaks, metadata

    def synthesize_cicada_wall(self, duration, n_insects=970, chirp_rate=40):
        insects, chirp_peaks = self._synthesize_insect_shelf(duration, n_insects, chirp_rate)

        max_val = np.max(np.abs(insects))
        if max_val > 30000:
            insects *= 30000.0 / max_val

        signal = np.clip(insects, -32768, 32767).astype(np.int16)
        return signal, chirp_peaks

    def synthesize_cricket_pulse(self, duration, n_insects=200, chirp_rate=10):
        insects, chirp_peaks = self._synthesize_insect_shelf(duration, n_insects, chirp_rate)

        max_val = np.max(np.abs(insects))
        if max_val > 30000:
            insects *= 30000.0 / max_val

        signal = np.clip(insects, -32768, 32767).astype(np.int16)
        return signal, chirp_peaks


def generate_biophony_carrier(output_path, duration_minutes, style="midnight_pond",
                               sample_rate=SAMPLE_RATE, chunk_seconds=CHUNK_DURATION):
    duration = duration_minutes * 60.0
    mesh = BiophonyMesh(sr=sample_rate)
    chirpmap_path = output_path.replace(".wav", ".chirpmap.npy")

    if duration <= chunk_seconds * 2:
        if style in ("midnight_pond", "biophony_mesh"):
            audio, chirp_peaks, metadata = mesh.synthesize_mesh(duration)
            n_channels = 2
        elif style == "cicada_wall":
            audio, chirp_peaks = mesh.synthesize_cicada_wall(duration)
            n_channels = 1
        elif style == "cricket_pulse":
            audio, chirp_peaks = mesh.synthesize_cricket_pulse(duration)
            n_channels = 1
        else:
            audio, chirp_peaks = mesh.synthesize_cicada_wall(duration)
            n_channels = 1

        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())

        np.save(chirpmap_path, chirp_peaks)
        return output_path, chirpmap_path, len(chirp_peaks)

    n_chunks = int(np.ceil(duration / chunk_seconds))
    all_chirp_peaks = []
    samples_written = 0

    is_stereo = style in ("midnight_pond", "biophony_mesh")
    n_channels = 2 if is_stereo else 1

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        for chunk_i in range(n_chunks):
            chunk_dur = min(chunk_seconds, duration - chunk_i * chunk_seconds)
            if chunk_dur <= 0:
                break

            chunk_offset = int(chunk_i * chunk_seconds * sample_rate)

            if is_stereo:
                audio, peaks, _ = mesh.synthesize_mesh(chunk_dur)
            elif style == "cicada_wall":
                audio, peaks = mesh.synthesize_cicada_wall(chunk_dur)
            elif style == "cricket_pulse":
                audio, peaks = mesh.synthesize_cricket_pulse(chunk_dur)
            else:
                audio, peaks = mesh.synthesize_cicada_wall(chunk_dur)

            adjusted_peaks = peaks + chunk_offset
            all_chirp_peaks.extend(adjusted_peaks.tolist())

            wf.writeframes(audio.tobytes())
            samples_written += len(audio) // n_channels

            print(f"  [BIOPHONY] Chunk {chunk_i + 1}/{n_chunks} written ({chunk_dur:.1f}s)")

    all_chirp_peaks = np.array(sorted(all_chirp_peaks), dtype=np.int64)
    np.save(chirpmap_path, all_chirp_peaks)

    print(f"  [BIOPHONY] Generated: {output_path} ({os.path.getsize(output_path):,} bytes)")
    print(f"  [BIOPHONY] Chirp map: {chirpmap_path} ({len(all_chirp_peaks):,} peaks)")
    print(f"  [BIOPHONY] Style: {style} | Duration: {duration:.0f}s | Shelves: {'3-shelf' if is_stereo else 'high-shelf only'}")

    return output_path, chirpmap_path, len(all_chirp_peaks)


def estimate_capacity(duration_minutes, style="midnight_pond", sample_rate=SAMPLE_RATE):
    duration = duration_minutes * 60.0
    n_samples = int(sample_rate * duration)

    is_stereo = style in ("midnight_pond", "biophony_mesh")
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

    chirp_rate = 35 if style in ("cicada_wall", "midnight_pond", "biophony_mesh") else 10
    peaks_per_sec = chirp_rate * (50 if "cicada" in style or "midnight" in style or "biophony" in style else 10)

    result = {
        "duration_minutes": duration_minutes,
        "duration_seconds": duration,
        "style": style,
        "channels": n_channels,
        "wav_size": wav_size,
        "raw_lsb1": raw_lsb1,
        "raw_lsb2": raw_lsb2,
        "density_multiplier": multiplier,
        "effective_lsb1": effective_lsb1,
        "effective_lsb2": effective_lsb2,
        "chirp_rate": chirp_rate,
        "peaks_per_sec": peaks_per_sec,
        "is_biophony": style in ("cicada_wall", "cricket_pulse", "midnight_pond", "biophony_mesh"),
    }

    if style in ("midnight_pond", "biophony_mesh"):
        result["shelf_breakdown"] = {
            "whale_shelf": "10 agents @ 15-50 Hz (LSB1 chassis)",
            "bird_shelf": "20 agents @ 300-800 Hz (Floating Parity Headers)",
            "insect_shelf": "970 agents @ 2-12 kHz (LSB2 silt mask)",
        }

    return result
