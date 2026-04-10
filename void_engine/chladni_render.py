"""
Chladni Pattern Renderer — Chronicle Seed
==========================================
Performs an FFT on the seed WAV, maps frequency magnitudes to a 2D Chladni
sand pattern (nodal lines rendered as particle density), and exports a PNG image.

The codon chain is embedded into the PNG as a tEXt metadata chunk so it can
be extracted later by /seed/load without relying on any server-side state.

3-6-9 triadic structure:
  - 3 concentric resonance zones (inner/mid/outer)
  - Colour-coded by frequency band (LOW=gold, MID=cyan, HIGH=violet)
  - 9-beat grid layout reflecting the codon chain rhythm structure
"""

import base64
import io
import logging
import math
import struct
import wave
import zlib
import numpy as np

logger = logging.getLogger(__name__)

LOW_COLOR  = (201, 168,  76, 255)
MID_COLOR  = ( 45, 212, 191, 255)
HIGH_COLOR = (167, 139, 250, 255)
SAND_COLOR = (240, 220, 160, 255)
BG_COLOR   = (  5,   5,  10, 255)

LOW_BAND_MAX  = 400
MID_BAND_MAX  = 2000
HIGH_BAND_MIN = 2000

ZONE_THRESHOLDS = [0.35, 0.65]

VOID_SEED_TEXT_KEY = b"VoidSeedChain"


def _chladni_value(x: float, y: float, m: int, n: int) -> float:
    """Square-plate Chladni function: cos(m*pi*x)*cos(n*pi*y) - cos(n*pi*x)*cos(m*pi*y)."""
    return (
        math.cos(m * math.pi * x) * math.cos(n * math.pi * y)
        - math.cos(n * math.pi * x) * math.cos(m * math.pi * y)
    )


def _fft_from_wav(wav_path: str) -> tuple[np.ndarray, np.ndarray, int]:
    """Read a WAV and return (magnitudes, freqs, sample_rate) via FFT."""
    with wave.open(wav_path, "rb") as wf:
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        n_channels = wf.getnchannels()
        raw = wf.readframes(n_frames)

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if n_channels > 1:
        samples = samples[::n_channels]

    fft_size = min(len(samples), 65536)
    segment = samples[:fft_size]
    window = np.hanning(len(segment))
    windowed = segment * window

    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(segment), 1.0 / sample_rate)

    return spectrum, freqs, sample_rate


def _band_energy(spectrum: np.ndarray, freqs: np.ndarray,
                 f_lo: float, f_hi: float) -> float:
    """Mean spectral energy in a frequency band."""
    mask = (freqs >= f_lo) & (freqs < f_hi)
    if not np.any(mask):
        return 0.0
    return float(np.mean(spectrum[mask] ** 2))


def _select_modes_from_fft(spectrum: np.ndarray, freqs: np.ndarray) -> tuple[int, int]:
    """
    Select Chladni modes (m, n) from the FFT spectrum.
    Maps dominant frequency region to a beautiful (m, n) pair.
    """
    MODES = [
        (1, 2), (1, 3), (2, 3), (1, 4), (2, 4), (3, 4),
        (1, 5), (2, 5), (3, 5), (4, 5), (1, 6), (2, 6),
        (3, 6), (4, 6), (5, 6), (2, 7), (3, 7), (4, 7),
        (5, 7), (3, 8), (4, 8), (5, 8), (4, 9), (5, 9),
    ]

    peak_idx = int(np.argmax(spectrum))
    peak_freq = float(freqs[peak_idx]) if peak_idx < len(freqs) else 432.0

    log_f = math.log2(max(peak_freq, 20))
    log_min = math.log2(60)
    log_max = math.log2(6000)
    t = max(0.0, min(1.0, (log_f - log_min) / (log_max - log_min)))
    idx = int(t * (len(MODES) - 1))
    return MODES[idx]


def _radial_distance(px: int, py: int, W: int, H: int) -> float:
    """Normalised radial distance from centre (0=centre, 1=corner)."""
    cx, cy = W / 2.0, H / 2.0
    dx = (px - cx) / (W / 2.0)
    dy = (py - cy) / (H / 2.0)
    return math.sqrt(dx * dx + dy * dy) / math.sqrt(2)


def _zone_color(radius: float,
                low_e: float, mid_e: float, high_e: float) -> tuple[int, int, int, int]:
    """
    Assign zone colour based on radial distance and band energies.
    Inner zone → LOW band colour, mid zone → MID, outer → HIGH.
    """
    total = low_e + mid_e + high_e + 1e-10
    w_low  = low_e  / total
    w_mid  = mid_e  / total
    w_high = high_e / total

    if radius < ZONE_THRESHOLDS[0]:
        dom = LOW_COLOR
        intensity = 0.5 + 0.5 * w_low
    elif radius < ZONE_THRESHOLDS[1]:
        dom = MID_COLOR
        intensity = 0.5 + 0.5 * w_mid
    else:
        dom = HIGH_COLOR
        intensity = 0.5 + 0.5 * w_high

    r = int(dom[0] * intensity)
    g = int(dom[1] * intensity)
    b = int(dom[2] * intensity)
    return (min(255, r), min(255, g), min(255, b), 255)


def _make_text_chunk(key: bytes, value: str) -> bytes:
    """
    Build a PNG tEXt ancillary chunk (keyword: value) with correct CRC.
    The value is base64-encoded so that any Unicode content (including multi-byte
    glyphs like α, ◆, ⚡) survives the Latin-1 constraint of the tEXt chunk.
    """
    encoded_value = base64.b64encode(value.encode("utf-8")).decode("ascii")
    data = key + b"\x00" + encoded_value.encode("ascii")
    chunk_type = b"tEXt"
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def _extract_text_chunk(png_bytes: bytes, key: bytes) -> str | None:
    """
    Extract a tEXt or iTXt chunk value from raw PNG bytes by key.
    Handles both tEXt (Pillow < 10) and iTXt (Pillow 10+) encodings.
    Returns the value string, or None if the key is not found.
    """
    pos = 8
    while pos < len(png_bytes) - 12:
        length = struct.unpack(">I", png_bytes[pos:pos+4])[0]
        chunk_type = png_bytes[pos+4:pos+8]
        data = png_bytes[pos+8:pos+8+length]
        pos += 12 + length

        if chunk_type == b"tEXt":
            null_pos = data.find(b"\x00")
            if null_pos != -1:
                chunk_key = data[:null_pos]
                if chunk_key == key:
                    raw_val = data[null_pos+1:]
                    try:
                        return base64.b64decode(raw_val).decode("utf-8")
                    except Exception:
                        return raw_val.decode("latin-1", errors="replace")

        elif chunk_type == b"iTXt":
            null_pos = data.find(b"\x00")
            if null_pos != -1:
                chunk_key = data[:null_pos]
                if chunk_key == key:
                    rest = data[null_pos+1:]
                    compression_flag = rest[0] if len(rest) > 0 else 0
                    compression_method = rest[1] if len(rest) > 1 else 0
                    rest2 = rest[2:]
                    lang_null = rest2.find(b"\x00")
                    if lang_null == -1:
                        continue
                    rest3 = rest2[lang_null+1:]
                    transl_null = rest3.find(b"\x00")
                    if transl_null == -1:
                        continue
                    text_bytes = rest3[transl_null+1:]
                    if compression_flag == 1:
                        try:
                            text_bytes = zlib.decompress(text_bytes)
                        except Exception:
                            continue
                    try:
                        return text_bytes.decode("utf-8", errors="replace")
                    except Exception:
                        continue

    return None


def extract_codon_chain_from_png(png_bytes: bytes) -> str | None:
    """
    Extract the embedded codon chain from a Chladni PNG's tEXt metadata.

    Returns the codon chain string, or None if not embedded.
    """
    return _extract_text_chunk(png_bytes, VOID_SEED_TEXT_KEY)


def render_chladni_png(
    wav_path: str,
    output_path: str | None = None,
    size: int = 512,
    sand_threshold: float = 0.055,
    codon_chain: str | None = None,
) -> bytes:
    """
    Render a Chladni pattern PNG from a WAV file.

    If codon_chain is provided, it is embedded into the PNG as a tEXt metadata
    chunk under the key "VoidSeedChain", enabling extraction by /seed/load.

    Args:
        wav_path: Path to the WAV file to analyse.
        output_path: If provided, save the PNG here as well.
        size: Canvas size (pixels, square).
        sand_threshold: Nodal line detection threshold.
        codon_chain: Optional codon chain to embed in PNG metadata.

    Returns:
        PNG bytes (with embedded codon chain if provided).
    """
    spectrum, freqs, sample_rate = _fft_from_wav(wav_path)

    low_e  = _band_energy(spectrum, freqs, 20,           LOW_BAND_MAX)
    mid_e  = _band_energy(spectrum, freqs, LOW_BAND_MAX,  MID_BAND_MAX)
    high_e = _band_energy(spectrum, freqs, HIGH_BAND_MIN, sample_rate / 2)

    m, n = _select_modes_from_fft(spectrum, freqs)

    W = H = size

    try:
        import PIL.Image as Image
        import PIL.ImageDraw as ImageDraw
        import PIL.ImageFilter as ImageFilter
        PIL_AVAILABLE = True
    except ImportError:
        PIL_AVAILABLE = False

    if PIL_AVAILABLE:
        img = Image.new("RGBA", (W, H), BG_COLOR)
        pixels = img.load()

        for py in range(H):
            for px in range(W):
                x = px / W
                y = py / H
                val = _chladni_value(x, y, m, n)
                abs_val = abs(val)

                radius = _radial_distance(px, py, W, H)

                if abs_val < sand_threshold:
                    intensity = 1.0 - (abs_val / sand_threshold)
                    brightness = intensity ** 1.8
                    zone_col = _zone_color(radius, low_e, mid_e, high_e)
                    r = int(SAND_COLOR[0] * 0.4 * brightness + zone_col[0] * 0.6 * brightness)
                    g = int(SAND_COLOR[1] * 0.4 * brightness + zone_col[1] * 0.6 * brightness)
                    b = int(SAND_COLOR[2] * 0.4 * brightness + zone_col[2] * 0.6 * brightness)
                    pixels[px, py] = (min(255, r), min(255, g), min(255, b), 255)
                else:
                    pixels[px, py] = BG_COLOR

        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

        _overlay_resonance_rings(img, W, H, low_e, mid_e, high_e)
        _overlay_codon_label(img, W, H, m, n)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        if codon_chain:
            png_bytes = _inject_text_chunk(png_bytes, codon_chain)
    else:
        png_bytes = _render_chladni_raw(W, H, m, n, sand_threshold, low_e, mid_e, high_e)
        if codon_chain:
            png_bytes = _inject_text_chunk(png_bytes, codon_chain)

    if output_path:
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        logger.info("Chladni PNG saved to %s (%d bytes)", output_path, len(png_bytes))

    return png_bytes


def _inject_text_chunk(png_bytes: bytes, codon_chain: str) -> bytes:
    """
    Insert a tEXt chunk with the codon chain into raw PNG bytes,
    placed after the IHDR chunk.
    """
    signature = png_bytes[:8]
    ihdr_length = struct.unpack(">I", png_bytes[8:12])[0]
    ihdr_end = 8 + 12 + ihdr_length

    text_chunk = _make_text_chunk(VOID_SEED_TEXT_KEY, codon_chain)

    return signature + png_bytes[8:ihdr_end] + text_chunk + png_bytes[ihdr_end:]


def _overlay_resonance_rings(img, W: int, H: int,
                              low_e: float, mid_e: float, high_e: float):
    """Draw 3 concentric resonance zone rings on the image."""
    try:
        import PIL.ImageDraw as ImageDraw
        draw = ImageDraw.Draw(img, "RGBA")
        cx, cy = W // 2, H // 2
        for threshold, color in zip(
            ZONE_THRESHOLDS,
            [(*LOW_COLOR[:3], 60), (*MID_COLOR[:3], 50)],
        ):
            r = int(threshold * W / math.sqrt(2))
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                outline=color,
                width=1,
            )
        outer_r = int(0.92 * W / math.sqrt(2))
        draw.ellipse(
            [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r],
            outline=(*HIGH_COLOR[:3], 40),
            width=1,
        )
    except Exception:
        pass


def _overlay_codon_label(img, W: int, H: int, m: int, n: int):
    """Draw the mode label and VOID watermark."""
    try:
        import PIL.ImageDraw as ImageDraw
        draw = ImageDraw.Draw(img, "RGBA")
        label = f"VOID·SEED ({m},{n})"
        draw.text((8, H - 20), label, fill=(80, 80, 80, 180))
    except Exception:
        pass


def _render_chladni_raw(W: int, H: int, m: int, n: int,
                         sand_threshold: float,
                         low_e: float, mid_e: float, high_e: float) -> bytes:
    """
    Fallback PNG renderer using pure Python struct (no PIL).
    Produces a minimal but valid PNG.
    """
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    ihdr_type = b"IHDR"
    ihdr_crc = zlib.crc32(ihdr_type + ihdr_data) & 0xFFFFFFFF
    ihdr = struct.pack(">I", len(ihdr_data)) + ihdr_type + ihdr_data + struct.pack(">I", ihdr_crc)

    raw_rows = []
    for py in range(H):
        row = bytearray([0])
        for px in range(W):
            x = px / W
            y = py / H
            val = _chladni_value(x, y, m, n)
            abs_val = abs(val)
            radius = _radial_distance(px, py, W, H)
            if abs_val < sand_threshold:
                brightness = (1.0 - abs_val / sand_threshold) ** 1.8
                zone_col = _zone_color(radius, low_e, mid_e, high_e)
                r = int(SAND_COLOR[0] * 0.4 * brightness + zone_col[0] * 0.6 * brightness)
                g = int(SAND_COLOR[1] * 0.4 * brightness + zone_col[1] * 0.6 * brightness)
                b = int(SAND_COLOR[2] * 0.4 * brightness + zone_col[2] * 0.6 * brightness)
                row.extend([min(255, r), min(255, g), min(255, b)])
            else:
                row.extend([BG_COLOR[0], BG_COLOR[1], BG_COLOR[2]])
        raw_rows.append(bytes(row))

    compressed = zlib.compress(b"".join(raw_rows), level=6)
    idat_type = b"IDAT"
    idat_crc = zlib.crc32(idat_type + compressed) & 0xFFFFFFFF
    idat = struct.pack(">I", len(compressed)) + idat_type + compressed + struct.pack(">I", idat_crc)

    iend_type = b"IEND"
    iend_crc = zlib.crc32(iend_type) & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + iend_type + struct.pack(">I", iend_crc)

    return signature + ihdr + idat + iend
