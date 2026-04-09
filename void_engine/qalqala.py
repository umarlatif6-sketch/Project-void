"""
void_engine/qalqala.py
=======================
Digital Qalqala Processor.

Qalqala (قلقلة) — the five echoing letters of tajweed.
The rule: at the five highest-pressure plosive phonemes (Qaf, Ta, Ba, Jim, Dal),
the sound must not terminate dead. It must reverberate. The compression burst
bounces back. A standing wave forms before the sound releases.

This processor applies the same principle to English speech:
it detects sharp transient events in an audio waveform — the acoustic
signature of plosive consonants (p, b, t, d, k, g) — and applies a
decaying echo tail at each one.

The body that hears the processed audio receives the same pressure burst
and reverberation that a trained qari produces deliberately at the
Haroof-e-Qalqala. The formation field precedes the semantic content.
The geometry channel arrives before the meaning channel.

Pipeline position:
    TTS → MP3 → 16-bit WAV → [QALQALA] → LSB stego encode → serve

Named: 9 April 2026. PROJECT VOID.
Mechanism: Haroof-e-Qalqala — sealed in VOID_CHRONICLE.md.
"""

import wave
import numpy as np


def apply_qalqala(
    input_wav_path: str,
    output_wav_path: str,
    echo_delay_ms: float = 26.0,
    echo_decay: float = 0.36,
    echo_count: int = 4,
    transient_threshold: float = 0.10,
    transient_window_ms: float = 6.0,
) -> str:
    """
    Apply Qalqala reverberation to a WAV file.

    Detects transient events (plosive pressure bursts) and adds a series
    of decaying echoes at each — simulating the acoustic bounce that
    tajweed specifies at the Haroof-e-Qalqala.

    Parameters
    ----------
    input_wav_path      : source 16-bit mono WAV path
    output_wav_path     : destination WAV path
    echo_delay_ms       : gap between echo repetitions in milliseconds.
                          26ms ≈ shortest audible discrete echo, matching
                          the natural reverb period of a closed oral cavity.
    echo_decay          : amplitude multiplier per echo repetition.
                          0.36 → 4 echoes reach ~0.017 amplitude (inaudible
                          threshold), clean exponential decay.
    echo_count          : number of decaying repetitions per transient.
    transient_threshold : minimum amplitude rise rate to qualify as a
                          Qalqala event (fraction of normalised scale).
    transient_window_ms : minimum gap between consecutive detected events.

    Returns
    -------
    output_wav_path (str)
    """
    with wave.open(input_wav_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)

    samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)

    peak = float(np.max(np.abs(samples)))
    if peak < 1.0:
        peak = 1.0
    norm = samples / peak

    echo_delay_smp = int(framerate * echo_delay_ms / 1000.0)
    transient_window_smp = int(framerate * transient_window_ms / 1000.0)

    rect = np.abs(norm)
    diff = np.diff(rect, prepend=rect[0])

    candidate_indices = np.where(diff > transient_threshold)[0]

    transient_indices = []
    last = -transient_window_smp
    for idx in candidate_indices:
        if idx - last >= transient_window_smp:
            transient_indices.append(int(idx))
            last = idx

    tail_samples = echo_delay_smp * echo_count
    output = np.concatenate(
        [norm.copy(), np.zeros(tail_samples, dtype=np.float32)]
    )

    for t_idx in transient_indices:
        for e in range(1, echo_count + 1):
            amp = echo_decay ** e
            dst_start = t_idx + echo_delay_smp * e
            dst_end = min(dst_start + echo_delay_smp, len(output))
            src_end = min(t_idx + echo_delay_smp, len(norm))
            src_seg = norm[t_idx:src_end]
            seg_len = min(len(src_seg), dst_end - dst_start)
            if seg_len <= 0:
                continue
            output[dst_start : dst_start + seg_len] += amp * src_seg[:seg_len]

    output = np.clip(output, -1.0, 1.0)
    out_int16 = (output * peak).astype(np.int16)

    with wave.open(output_wav_path, "wb") as wf_out:
        wf_out.setnchannels(n_channels)
        wf_out.setsampwidth(sampwidth)
        wf_out.setframerate(framerate)
        wf_out.writeframes(out_int16.tobytes())

    return output_wav_path
