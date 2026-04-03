"""
VOID Audio Steganography — WaveWhisper + Spectrogram Layer

Two steganography modes, both anchored to the 432 Hz carrier:

  1. WAVEWHISPER — 14-segment display samples overlaid onto the 432 Hz tone.
     The message becomes audible as subtle tonal patterns (overlaid at -20 dBFS).
     Hidden at the sample level; decoded by the WaveWhisper decoder.

  2. SPECTROGRAM — The text is literally drawn into the audio spectrogram.
     STFT bins are energised to paint glyphs at the 800–3200 Hz band so that
     any spectrogram viewer shows the message as visible text.
     The 432 Hz carrier is preserved beneath as a resonance anchor.

Both modes return raw WAV bytes (16-bit PCM mono, 44100 Hz).
"""

import io
import math
import logging
import struct
import wave
import numpy as np

logger = logging.getLogger(__name__)

_SAMPLE_RATE = 44100
_CARRIER_HZ = 432.0

# ---------------------------------------------------------------------------
# 5×7 bitmap font (uppercase A–Z, 0–9, space, common punctuation)
# Rows are top→bottom, columns left→right; 1 = pixel on
# ---------------------------------------------------------------------------
_BITMAP_FONT = {
    ' ': [0b00000]*7,
    'A': [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'B': [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    'C': [0b01111, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b01111],
    'D': [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    'E': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    'F': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    'G': [0b01111, 0b10000, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111],
    'H': [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'I': [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    'J': [0b00111, 0b00010, 0b00010, 0b00010, 0b10010, 0b10010, 0b01100],
    'K': [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    'L': [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    'M': [0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001, 0b10001],
    'N': [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    'O': [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'P': [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    'Q': [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    'S': [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    'T': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    'U': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'V': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    'W': [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
    'X': [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    'Y': [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    'Z': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    '0': [0b01110, 0b10011, 0b10101, 0b10101, 0b10101, 0b11001, 0b01110],
    '1': [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    '2': [0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111],
    '3': [0b01110, 0b10001, 0b00001, 0b00110, 0b00001, 0b10001, 0b01110],
    '4': [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    '5': [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
    '6': [0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    '7': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    '8': [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    '9': [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110],
    '!': [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100],
    '?': [0b01110, 0b10001, 0b00001, 0b00110, 0b00100, 0b00000, 0b00100],
    '.': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100],
    '-': [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
    '_': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111],
}
_CHAR_W = 5
_CHAR_H = 7
_CHAR_GAP = 1   # pixel columns between characters


def _text_to_bitmap(text: str) -> np.ndarray:
    """Render text to a 2-D bitmap array (height × width), values 0 or 1."""
    text = text.upper()[:64]  # hard cap to avoid memory blow-up
    cols = []
    for ch in text:
        glyph = _BITMAP_FONT.get(ch, _BITMAP_FONT.get('?', [0]*7))
        char_col = np.zeros((_CHAR_H, _CHAR_W), dtype=np.float32)
        for row_idx, row_bits in enumerate(glyph):
            for col_idx in range(_CHAR_W):
                char_col[row_idx, _CHAR_W - 1 - col_idx] = (row_bits >> col_idx) & 1
        cols.append(char_col)
        cols.append(np.zeros((_CHAR_H, _CHAR_GAP), dtype=np.float32))  # gap
    if not cols:
        return np.zeros((_CHAR_H, 1), dtype=np.float32)
    bitmap = np.concatenate(cols, axis=1)
    # Add one-pixel padding around the bitmap
    bitmap = np.pad(bitmap, pad_width=((1, 1), (1, 1)), constant_values=0)
    return bitmap


def _carrier_tone(n_samples: int) -> np.ndarray:
    """Generate a 432 Hz sine carrier at comfortable amplitude."""
    t = np.linspace(0, n_samples / _SAMPLE_RATE, n_samples, endpoint=False)
    sig = 0.35 * np.sin(2 * np.pi * _CARRIER_HZ * t)
    # Add Schumann 7.83 Hz sub-tone
    sig += 0.08 * np.sin(2 * np.pi * 7.83 * t)
    return sig.astype(np.float32)


def _float_to_wav_bytes(samples: np.ndarray) -> bytes:
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32000).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


# ---------------------------------------------------------------------------
# MODE 1: WaveWhisper — 14-segment display overlay
# ---------------------------------------------------------------------------

def encode_wavewhisper(message: str, duration: float = 10.0) -> bytes:
    """
    Encode *message* into audio using WaveWhisper's 14-segment display method,
    overlaid onto a 432 Hz carrier tone.

    Returns WAV bytes (16-bit PCM mono 44100 Hz).
    """
    n_samples = int(duration * _SAMPLE_RATE)
    carrier = _carrier_tone(n_samples)

    try:
        from wavewhisper.message import Message
        from wavewhisper.audio import Audio

        carrier_wav = _float_to_wav_bytes(carrier)
        with io.BytesIO(carrier_wav) as bio:
            carrier_buf = bio.getvalue()

        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_in:
            tmp_in.write(carrier_wav)
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path.replace('.wav', '_ww.wav')
        try:
            msg = Message(message)
            msg.encrypt(tmp_in_path, tmp_out_path)
            with open(tmp_out_path, 'rb') as f:
                result = f.read()
            logger.info("[VOID-STEGA] WaveWhisper encoded %d chars onto 432 Hz carrier", len(message))
            return result
        finally:
            if os.path.exists(tmp_in_path):
                os.remove(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.remove(tmp_out_path)

    except Exception as exc:
        logger.warning("[VOID-STEGA] WaveWhisper encode failed (%s), returning plain carrier", exc)
        return _float_to_wav_bytes(carrier)


# ---------------------------------------------------------------------------
# MODE 2: Spectrogram — text literally visible in frequency domain
# ---------------------------------------------------------------------------

def encode_spectrogram(message: str, duration: float = 10.0,
                       freq_low: float = 900.0,
                       freq_high: float = 3600.0) -> bytes:
    """
    Synthesise audio where *message* is VISUALLY VISIBLE in the spectrogram.

    The text is mapped to time-frequency energy blobs between freq_low and
    freq_high Hz.  The 432 Hz carrier remains as a resonance anchor beneath.

    Returns WAV bytes (16-bit PCM mono 44100 Hz).
    """
    n_samples = int(duration * _SAMPLE_RATE)
    fft_size = 2048
    hop = 512

    bitmap = _text_to_bitmap(message)   # (H, W) — row 0 = top frequency
    bh, bw = bitmap.shape

    n_frames = (n_samples - fft_size) // hop + 1
    if n_frames < 1:
        n_frames = 1

    bin_count = fft_size // 2 + 1
    bin_low = int(freq_low / (_SAMPLE_RATE / fft_size))
    bin_high = int(freq_high / (_SAMPLE_RATE / fft_size))
    bin_range = max(1, bin_high - bin_low)

    # Build per-frame magnitude spectrum with the bitmap painted in
    spectrogram = np.zeros((bin_count, n_frames), dtype=np.float32)

    # 432 Hz carrier bin — keep it warm throughout
    carrier_bin = round(_CARRIER_HZ / (_SAMPLE_RATE / fft_size))
    schumann_bin = round(7.83 / (_SAMPLE_RATE / fft_size))
    spectrogram[carrier_bin, :] = 1800.0
    if 0 < schumann_bin < bin_count:
        spectrogram[schumann_bin, :] = 600.0

    # Paint the text bitmap across time
    for frame_i in range(n_frames):
        char_col = int(frame_i / n_frames * bw)
        for bit_row in range(bh):
            if char_col < bw and bitmap[bit_row, char_col] > 0:
                # Map bit_row to a frequency bin (top row → high freq)
                bin_pos = bin_low + int((1 - bit_row / bh) * bin_range)
                bin_pos = max(1, min(bin_count - 2, bin_pos))
                # Gaussian blob to soften pixelated artefacts
                for b in range(bin_pos - 2, bin_pos + 3):
                    if 0 <= b < bin_count:
                        weight = math.exp(-0.5 * ((b - bin_pos) / 1.2) ** 2)
                        spectrogram[b, frame_i] += 3200.0 * weight

    # Synthesise audio via ISTFT with random phases
    rng = np.random.default_rng(seed=42)
    audio = np.zeros(n_samples, dtype=np.float32)

    window = np.hanning(fft_size).astype(np.float32)

    for frame_i in range(n_frames):
        phases = rng.uniform(0, 2 * np.pi, bin_count)
        magnitudes = spectrogram[:, frame_i]
        spectrum = magnitudes * np.exp(1j * phases)

        # Build full two-sided spectrum
        full = np.concatenate([spectrum, np.conj(spectrum[-2:0:-1])])
        frame_samples = np.real(np.fft.ifft(full)).astype(np.float32)[:fft_size]
        frame_samples *= window

        start = frame_i * hop
        end = min(start + fft_size, n_samples)
        audio[start:end] += frame_samples[:end - start]

    # Mix with carrier for resonance anchoring
    carrier = _carrier_tone(n_samples)
    audio = 0.7 * audio + 0.3 * carrier * np.max(np.abs(audio) + 1e-8)

    # Normalise
    peak = np.max(np.abs(audio))
    if peak > 1e-8:
        audio = audio / peak * 0.90

    logger.info("[VOID-STEGA] Spectrogram encoded %d chars (%d frames, bins %d–%d)",
                len(message), n_frames, bin_low, bin_high)
    return _float_to_wav_bytes(audio)


# ---------------------------------------------------------------------------
# Pheromonal Metadata Layer — Chemical-Intent Tags for VoidEcho Broadcasts
# ---------------------------------------------------------------------------

PHEROMONAL_TAGS = {
    "ALERT":   "0x50484552",   # PHer prefix — heightened sensitivity
    "PEACE":   "0x50454143",   # PEAC prefix — 432 Hz vortex stable
    "DORMANT": "0x444F524D",   # DORM prefix — low-activity idle
    "STORM":   "0x53544F52",   # STOR prefix — protective/local collapse
}

# Apex Predator dual-tone state — both ALERT and PEACE active simultaneously
_apex_predator_active: bool = False
_pheromonal_intent: str = "PEACE"


def get_pheromonal_tag(intent: str) -> str:
    """Return the hex prefix for a given chemical-intent tag."""
    return PHEROMONAL_TAGS.get(intent.upper(), PHEROMONAL_TAGS["PEACE"])


def set_pheromonal_intent(intent: str) -> str:
    """
    Set the global pheromonal intent for all subsequent VoidEcho broadcasts.
    Accepts: ALERT, PEACE, DORMANT, STORM
    Returns the active intent string.
    """
    global _pheromonal_intent
    intent = intent.upper()
    if intent not in PHEROMONAL_TAGS:
        intent = "PEACE"
    _pheromonal_intent = intent
    logger.info("[VOID-PHERO] Chemical-intent set to %s (%s)", intent, PHEROMONAL_TAGS[intent])
    return _pheromonal_intent


def activate_apex_predator() -> dict:
    """
    Activate Apex Predator dual-tone mode.
    ALERT sharpens sensor sensitivity; PEACE keeps 432 Hz carrier active.
    Returns dual-tone status dict.
    """
    global _apex_predator_active, _pheromonal_intent
    _apex_predator_active = True
    _pheromonal_intent = "ALERT"
    logger.info("[VOID-APEX] Apex Predator mode ACTIVE — ALERT sensitivity + 432 Hz Peace carrier")
    return get_apex_predator_status()


def deactivate_apex_predator() -> dict:
    """Deactivate Apex Predator mode and return to PEACE."""
    global _apex_predator_active, _pheromonal_intent
    _apex_predator_active = False
    _pheromonal_intent = "PEACE"
    logger.info("[VOID-APEX] Apex Predator mode DEACTIVATED — returning to PEACE")
    return get_apex_predator_status()


def activate_storm_override() -> dict:
    """
    Storm Mode override: collapses ALERT + PEACE → Protective/Local instantly.
    Both signals are reduced to STORM (Protective/Local) mode.
    """
    global _apex_predator_active, _pheromonal_intent
    _apex_predator_active = False
    _pheromonal_intent = "STORM"
    logger.info("[VOID-STORM] Storm Mode override ACTIVE — ALERT+PEACE collapsed to STORM/Protective-Local")
    return {
        "storm_active": True,
        "apex_predator": False,
        "pheromonal_intent": "STORM",
        "hex_tag": get_pheromonal_tag("STORM"),
        "mode": "Protective/Local",
        "carrier_hz": _CARRIER_HZ,
    }


def get_apex_predator_status() -> dict:
    """Return the current dual-tone Apex Predator status for dashboard display."""
    return {
        "apex_predator": _apex_predator_active,
        "pheromonal_intent": _pheromonal_intent,
        "alert_hex": get_pheromonal_tag("ALERT"),
        "peace_hex": get_pheromonal_tag("PEACE"),
        "active_hex_tag": get_pheromonal_tag(_pheromonal_intent),
        "carrier_hz": _CARRIER_HZ,
        "dual_tone_active": _apex_predator_active,
        "sensor_sensitivity": "MAXIMUM" if _apex_predator_active else "STANDARD",
        "storm_override": _pheromonal_intent == "STORM",
    }


def build_pheromonal_header(intent: str = None) -> str:
    """
    Build the pheromonal metadata header string for a VoidEcho transmission.

    Format: [PHERO:{HEX_TAG}:{INTENT}:{CARRIER_HZ}]
    This is prepended to the broadcast message so every transmission carries
    its chemical-intent signature.
    """
    if intent is None:
        intent = _pheromonal_intent
    hex_tag = get_pheromonal_tag(intent)
    carrier = "432Hz"
    if _apex_predator_active:
        return f"[PHERO:{hex_tag}:{intent}:APEX-PREDATOR:{carrier}]"
    return f"[PHERO:{hex_tag}:{intent}:{carrier}]"


# ---------------------------------------------------------------------------
# Public helper used by routes
# ---------------------------------------------------------------------------

def encode_message(message: str, method: str = "spectrogram",
                   duration: float = 10.0,
                   pheromonal_intent: str = None) -> bytes:
    """
    Encode *message* via the given method.

    method — "wavewhisper" or "spectrogram"
    pheromonal_intent — optional chemical-intent override (ALERT/PEACE/DORMANT/STORM)
    Returns raw WAV bytes.

    Every broadcast carries a pheromonal metadata header as a hex-prefixed
    chemical-intent tag alongside the audio payload.
    """
    phero_header = build_pheromonal_header(pheromonal_intent)
    tagged_message = f"{phero_header} {message}"
    logger.info("[VOID-STEGA] Encoding with pheromonal tag: %s", phero_header)
    if method == "wavewhisper":
        return encode_wavewhisper(tagged_message, duration)
    return encode_spectrogram(tagged_message, duration)
