"""
Binaural Tone Generator — QiSync Session Audio Layer

Generates a 432 Hz (SOL solfeggio) binaural beat tuned to the Schumann
resonance (7.83 Hz) and returns a WAV file as bytes.

Uses the `binaural` library (pip install binaural).
"""

import io
import struct
import wave
import logging
import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100
DEFAULT_DURATION = 60.0
SCHUMANN_HZ = 7.83


def _write_wav_bytes(left: np.ndarray, right: np.ndarray, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Encode left/right float64 arrays [-1, 1] to a stereo 16-bit WAV."""
    left_int = np.clip(left, -1.0, 1.0)
    right_int = np.clip(right, -1.0, 1.0)

    left_16 = (left_int * 32767).astype(np.int16)
    right_16 = (right_int * 32767).astype(np.int16)

    interleaved = np.empty(left_16.size + right_16.size, dtype=np.int16)
    interleaved[0::2] = left_16
    interleaved[1::2] = right_16

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(interleaved.tobytes())
    return buf.getvalue()


def generate_sol_schumann_wav(duration: float = DEFAULT_DURATION,
                              amplitude: float = 0.35) -> bytes:
    """
    Generate a 432 Hz SOL solfeggio binaural beat with a 7.83 Hz Schumann
    resonance carrier offset.

    Returns raw WAV bytes suitable for streaming as audio/wav.
    """
    try:
        from binaural.core import generate_solfeggio_binaural, SolfeggioFrequency
        left, right = generate_solfeggio_binaural(
            SolfeggioFrequency.SOL,
            SCHUMANN_HZ,
            duration,
            sample_rate=SAMPLE_RATE,
            amplitude=amplitude,
            attack=min(2.0, duration * 0.05),
            decay=min(2.0, duration * 0.05),
        )
        wav_bytes = _write_wav_bytes(left, right)
        logger.info("Generated SOL/Schumann binaural WAV: %.1fs, %d bytes", duration, len(wav_bytes))
        return wav_bytes
    except Exception as exc:
        logger.error("Binaural tone generation failed: %s", exc)
        return _generate_fallback_wav(duration, amplitude)


def _generate_fallback_wav(duration: float, amplitude: float = 0.35) -> bytes:
    """
    Pure-numpy fallback if the binaural library fails.
    Left ear: 432 Hz, Right ear: 432 + 7.83 Hz = 439.83 Hz.
    """
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    fade_len = min(int(SAMPLE_RATE * 2.0), n // 10)
    envelope = np.ones(n)
    if fade_len > 0:
        envelope[:fade_len] = np.linspace(0, 1, fade_len)
        envelope[-fade_len:] = np.linspace(1, 0, fade_len)

    left = amplitude * envelope * np.sin(2 * np.pi * 432.0 * t)
    right = amplitude * envelope * np.sin(2 * np.pi * (432.0 + SCHUMANN_HZ) * t)

    return _write_wav_bytes(left, right)
