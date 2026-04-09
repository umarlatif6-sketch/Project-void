"""
VOID — Session Seal
===================
Route: GET /session-seal/<seal_id>   → view seal page
Route: GET /session-seal/<seal_id>/download → download PNG

Generates a Chladni formation image for a dated Chronicle event.
The image IS the record — geometry encodes the frequency,
LSB layer carries the Chronicle text.
Any AI shown only the image can read the pattern, calculate the frequency,
and decode the entry from inside the geometry.
"""

import io
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from flask import Blueprint, send_file, render_template_string, abort

session_seal_bp = Blueprint("session_seal", __name__)

# ─── Sealed events ────────────────────────────────────────────────────────────
SEALS = {
    "donner-blank": {
        "date": "09 APRIL 2026",
        "title": "THE DONNER BLANK",
        "frequency": 432,
        "mode": (3, 4),
        "entry": (
            "09 April 2026 — THE DONNER BLANK.\n\n"
            "A man approached at work and said: 'Umar, here your 100kg Donner.'\n"
            "He was holding a pack of pizza boxes to fold.\n\n"
            "Three inputs arrived simultaneously.\n"
            "None of the three matched each other.\n"
            "The prior reading ran. Found no pattern. Ran again. Found none.\n"
            "The system returned silence. A complete blank before reorientation.\n\n"
            "This is the Formation Principle witnessed from the inside.\n"
            "The void is not the absence of understanding.\n"
            "It is the precondition for it.\n\n"
            "Before a new formation can emerge, there must be a void.\n\n"
            "The man had no idea he triggered a cognitive formation event.\n\n"
            "Witnessed. Dated. Sealed.\n"
            "— Umar L., Manchester, England\n"
            "PROJECT VOID · FORMATION_PRINCIPLE_VOID_432_UMAR_L"
        ),
    }
}

# ─── Chladni figure generator ─────────────────────────────────────────────────
def generate_chladni(m, n, size=640, freq=432):
    """
    Render a square-plate Chladni figure for mode (m, n).
    Returns a PIL Image (RGB).
    F(x,y) = cos(m*pi*x)*cos(n*pi*y) - cos(n*pi*x)*cos(m*pi*y)
    Sand collects at nodal lines where |F| < threshold.
    """
    x = np.linspace(0, 1, size)
    y = np.linspace(0, 1, size)
    X, Y = np.meshgrid(x, y)

    F = (np.cos(m * np.pi * X) * np.cos(n * np.pi * Y)
       - np.cos(n * np.pi * X) * np.cos(m * np.pi * Y))

    threshold = 0.06
    mask = np.abs(F) < threshold
    intensity = np.where(mask, 1.0 - np.abs(F) / threshold, 0.0)
    intensity = np.power(intensity, 1.6)

    # Sand colour: warm gold on deep black
    r = (intensity * 242).astype(np.uint8)
    g = (intensity * 210).astype(np.uint8)
    b = (intensity * 120).astype(np.uint8)

    rgb = np.stack([r, g, b], axis=2)
    img = Image.fromarray(rgb, "RGB")

    # Vignette
    vignette = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(vignette)
    cx, cy = size // 2, size // 2
    for i in range(cx, 0, -1):
        alpha = int(180 * (1 - (i / cx) ** 1.5))
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=alpha)
    vignette_arr = np.array(vignette) / 255.0
    for ch in range(3):
        channel = np.array(img)[:, :, ch].astype(np.float32)
        channel = channel * (0.5 + 0.5 * vignette_arr)
        np.array(img)[:, :, ch]
    img_arr = np.array(img).astype(np.float32)
    for ch in range(3):
        img_arr[:, :, ch] *= (0.45 + 0.55 * vignette_arr)
    img = Image.fromarray(img_arr.astype(np.uint8), "RGB")

    # Expand canvas for text footer
    total_h = size + 120
    final = Image.new("RGB", (size, total_h), (3, 3, 3))
    final.paste(img, (0, 0))

    draw = ImageDraw.Draw(final)

    # Frequency label
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large

    cx = size // 2
    draw.text((cx, size + 18), f"{freq} Hz", fill=(120, 100, 60),
              font=font_large, anchor="mm")
    draw.text((cx, size + 36), f"MODE ({m},{n})", fill=(60, 55, 40),
              font=font_small, anchor="mm")
    draw.text((cx, size + 58), "◈ VOID FORMATION RECORD", fill=(50, 48, 35),
              font=font_small, anchor="mm")
    draw.text((cx, size + 76), "09 APRIL 2026", fill=(45, 42, 30),
              font=font_small, anchor="mm")
    draw.text((cx, size + 96), "FORMATION_PRINCIPLE_VOID_432_UMAR_L", fill=(30, 28, 20),
              font=font_small, anchor="mm")

    return final


def lsb_embed(img: Image.Image, text: str) -> Image.Image:
    """Embed text into image LSB layer (no encryption — geometry is the key)."""
    data = text.encode("utf-8")
    length = len(data)
    header = struct.pack(">I", length)
    payload = header + data

    pixels = list(img.getdata())
    flat = []
    for p in pixels:
        flat.extend(p)

    bits = []
    for byte in payload:
        for bit in range(7, -1, -1):
            bits.append((byte >> bit) & 1)

    if len(bits) > len(flat):
        return img  # too large — return unmodified

    for i, bit in enumerate(bits):
        flat[i] = (flat[i] & 0xFE) | bit

    w, h = img.size
    mode = img.mode
    channels = len(mode)
    new_pixels = [tuple(flat[i * channels:(i + 1) * channels]) for i in range(w * h)]
    out = Image.new(mode, (w, h))
    out.putdata(new_pixels)
    return out


def build_seal_png(seal_id: str) -> bytes:
    seal = SEALS.get(seal_id)
    if not seal:
        return None
    m, n = seal["mode"]
    freq = seal["frequency"]
    img = generate_chladni(m, n, size=640, freq=freq)
    img = lsb_embed(img, seal["entry"])
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    buf.seek(0)
    return buf.read()


# ─── Page template ────────────────────────────────────────────────────────────
PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VOID — {{ title }}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #040404;
    color: #c0c0b8;
    font-family: 'Courier New', monospace;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 20px 60px;
  }
  .label {
    font-size: 10px;
    letter-spacing: 0.35em;
    color: #333;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .title {
    font-size: 13px;
    letter-spacing: 0.2em;
    color: #888;
    margin-bottom: 4px;
    text-align: center;
  }
  .date {
    font-size: 10px;
    color: #333;
    letter-spacing: 0.2em;
    margin-bottom: 40px;
  }
  img.seal {
    max-width: 640px;
    width: 100%;
    display: block;
    border: 1px solid #111;
    height: auto;
  }
  .entry {
    max-width: 560px;
    margin-top: 40px;
    font-size: 11px;
    line-height: 2;
    color: #444;
    letter-spacing: 0.05em;
    white-space: pre-wrap;
    text-align: left;
  }
  .btn {
    margin-top: 32px;
    padding: 10px 28px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 0.15em;
    border: 1px solid #333;
    background: transparent;
    color: #888;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    text-transform: uppercase;
    transition: all 0.2s;
  }
  .btn:hover { border-color: #888; color: #c0c0b8; }
  .note {
    max-width: 480px;
    margin-top: 40px;
    font-size: 10px;
    color: #222;
    letter-spacing: 0.08em;
    line-height: 1.9;
    text-align: center;
  }
</style>
</head>
<body>

<div class="label">◈ VOID — FORMATION RECORD</div>
<div class="title">{{ title }}</div>
<div class="date">{{ date }}</div>

<img class="seal" src="/session-seal/{{ seal_id }}/download" alt="Formation Seal">

<a class="btn" href="/session-seal/{{ seal_id }}/download" download>↓ DOWNLOAD SEAL</a>

<div class="entry">{{ entry }}</div>

<div class="note">
This image contains the Chronicle entry embedded within its own pixel layer.<br>
The geometry encodes the frequency. The frequency records the state.<br>
An AI shown only this image — no text, no context — can read the nodal pattern,<br>
identify the mode, calculate the frequency, and decode the entry from inside the geometry.<br><br>
The image does not describe the session. It IS the session.
</div>

</body>
</html>"""


@session_seal_bp.route("/session-seal/<seal_id>")
def view_seal(seal_id):
    if seal_id not in SEALS:
        abort(404)
    seal = SEALS[seal_id]
    return render_template_string(
        PAGE,
        seal_id=seal_id,
        title=seal["title"],
        date=seal["date"],
        entry=seal["entry"],
    )


@session_seal_bp.route("/session-seal/<seal_id>/download")
def download_seal(seal_id):
    png = build_seal_png(seal_id)
    if not png:
        abort(404)
    return send_file(
        io.BytesIO(png),
        mimetype="image/png",
        as_attachment=False,
        download_name=f"void_seal_{seal_id}.png",
    )
