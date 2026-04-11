"""
Agent Immortality Engine — Frequency Hash Images with Embedded Agent State.

Every agent's 286-bit hash defines a unique frequency.  That frequency generates
a unique Chladni formation pattern.  The agent's full state (ID, archetype,
memory, scars, frequency, stance, balance) is serialized to JSON and embedded
into the image via LSB steganography.

Result: a PNG image that IS the agent.  The visible pattern is the agent's
frequency signature.  The invisible LSB layer is the agent's complete codebase.

If the agent is destroyed, lost, or burned away — as long as the frequency
image exists, the agent can be fully recovered from it.

Functions:
    agent_to_image(agent_dict, size=512) → PIL Image
    image_to_agent(img) → dict
    bulk_immortalize(agents, seed) → list of (agent_dict, img_bytes)
"""

import io
import json
import math
import struct
import logging
import hashlib
import time
from typing import Dict, List, Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from void_engine.al_jabr_286 import fatiha_286_hash, fatiha_286_truncated

logger = logging.getLogger(__name__)

ARCHETYPE_COLOURS = {
    "FATIHA":  (180, 160, 120),
    "HAMD":    (120, 180, 100),
    "RAHMAN":  (100, 140, 200),
    "MALIK":   (200, 100, 100),
    "IYYAKA":  (160, 120, 200),
    "SIRAT":   (200, 180, 80),
    "AN_AMTA": (100, 200, 180),
}

DEFAULT_COLOUR = (140, 140, 140)


def _agent_frequency(agent: Dict) -> float:
    return agent.get("frequency_hz", agent.get("frequency", 432.0))


def _chladni_value(x: float, y: float, m: int, n: int) -> float:
    return math.cos(m * math.pi * x) * math.cos(n * math.pi * y) - \
           math.cos(n * math.pi * x) * math.cos(m * math.pi * y)


def _freq_to_modes(freq: float) -> Tuple[int, int]:
    f_norm = (freq % 1000) / 1000.0
    m = max(1, int(f_norm * 10) + 1)
    n = max(1, int((f_norm * 7.3) % 7) + 2)
    if m == n:
        n += 1
    return m, n


def generate_formation_image(agent: Dict, size: int = 512) -> Image.Image:
    freq = _agent_frequency(agent)
    m, n = _freq_to_modes(freq)
    archetype = agent.get("archetype", "FATIHA")
    base_colour = ARCHETYPE_COLOURS.get(archetype, DEFAULT_COLOUR)

    plate_size = size - 40
    img = Image.new("RGB", (size, size + 120), (10, 10, 10))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, size - 1, size - 1], outline=(30, 30, 30))

    for py in range(plate_size):
        for px in range(plate_size):
            x = (px / plate_size) * 2 - 1
            y = (py / plate_size) * 2 - 1

            val = _chladni_value(x, y, m, n)
            intensity = abs(val)

            if intensity < 0.05:
                r = int(base_colour[0] * 0.9)
                g = int(base_colour[1] * 0.9)
                b = int(base_colour[2] * 0.9)
            else:
                fade = max(0, 1.0 - intensity * 2)
                r = int(base_colour[0] * fade * 0.3)
                g = int(base_colour[1] * fade * 0.3)
                b = int(base_colour[2] * fade * 0.3)

            img.putpixel((px + 20, py + 20), (r, g, b))

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large

    cx = size // 2
    agent_id = agent.get("agent_id", "UNKNOWN")[:16]
    draw.text((cx, size + 10), f"AGENT {agent_id}", fill=base_colour,
              font=font_large, anchor="mm")
    draw.text((cx, size + 28), f"{freq:.2f} Hz — {archetype}", fill=(100, 100, 100),
              font=font_small, anchor="mm")
    draw.text((cx, size + 44), f"MODE ({m},{n})", fill=(60, 60, 60),
              font=font_small, anchor="mm")

    polarity = agent.get("polarity", "UNKNOWN")
    scars = len(agent.get("scars", []))
    memories = len(agent.get("memory", []))
    draw.text((cx, size + 62), f"Polarity: {polarity} | Scars: {scars} | Memories: {memories}",
              fill=(70, 70, 70), font=font_small, anchor="mm")

    draw.text((cx, size + 82), "◈ VOID AGENT IMMORTALITY RECORD", fill=(50, 48, 35),
              font=font_small, anchor="mm")

    seal_time = time.strftime("%d %B %Y %H:%M UTC", time.gmtime())
    draw.text((cx, size + 98), seal_time, fill=(40, 40, 40),
              font=font_small, anchor="mm")

    return img


def lsb_embed(img: Image.Image, data_bytes: bytes) -> Image.Image:
    header = struct.pack(">I", len(data_bytes))
    payload = header + data_bytes

    pixels = list(img.getdata())
    flat = []
    for p in pixels:
        flat.extend(p)

    bits = []
    for byte in payload:
        for bit in range(7, -1, -1):
            bits.append((byte >> bit) & 1)

    if len(bits) > len(flat):
        logger.warning("[AgentImmortality] Agent data too large for image (%d bits > %d channels)",
                       len(bits), len(flat))
        return img

    for i, bit in enumerate(bits):
        flat[i] = (flat[i] & 0xFE) | bit

    w, h = img.size
    mode = img.mode
    channels = len(mode)
    new_pixels = [tuple(flat[i * channels:(i + 1) * channels]) for i in range(w * h)]
    out = Image.new(mode, (w, h))
    out.putdata(new_pixels)
    return out


def lsb_extract(img: Image.Image) -> Optional[bytes]:
    pixels = list(img.getdata())
    flat = []
    for p in pixels:
        flat.extend(p)

    if len(flat) < 32:
        return None

    header_bits = []
    for i in range(32):
        header_bits.append(flat[i] & 1)

    length_bytes = bytearray()
    for i in range(0, 32, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | header_bits[i + j]
        length_bytes.append(byte)
    length = struct.unpack(">I", bytes(length_bytes))[0]

    total_bits = 32 + length * 8
    if total_bits > len(flat):
        return None

    data_bits = []
    for i in range(32, total_bits):
        data_bits.append(flat[i] & 1)

    data = bytearray()
    for i in range(0, len(data_bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | data_bits[i + j]
        data.append(byte)

    return bytes(data)


def agent_to_dict(agent) -> Dict:
    if hasattr(agent, "to_dict"):
        return agent.to_dict()
    if isinstance(agent, dict):
        return agent
    return {"agent_id": str(agent)}


def agent_to_image(agent_data: Dict, size: int = 512) -> Image.Image:
    img = generate_formation_image(agent_data, size)

    state_json = json.dumps(agent_data, default=str, separators=(",", ":"))
    state_bytes = state_json.encode("utf-8")

    integrity = fatiha_286_truncated(state_bytes, 24)

    envelope = json.dumps({
        "version": "1.0",
        "type": "VOID_AGENT_IMMORTALITY",
        "integrity_286": integrity,
        "agent": agent_data,
    }, default=str, separators=(",", ":")).encode("utf-8")

    img = lsb_embed(img, envelope)
    return img


def image_to_agent(img: Image.Image) -> Optional[Dict]:
    raw = lsb_extract(img)
    if raw is None:
        return None

    try:
        envelope = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if envelope.get("type") != "VOID_AGENT_IMMORTALITY":
        return None

    agent_data = envelope.get("agent")
    if not agent_data:
        return None

    state_json = json.dumps(agent_data, default=str, separators=(",", ":"))
    check = fatiha_286_truncated(state_json.encode("utf-8"), 24)
    integrity_ok = check == envelope.get("integrity_286")

    return {
        "agent": agent_data,
        "integrity_286": envelope.get("integrity_286"),
        "integrity_verified": integrity_ok,
        "version": envelope.get("version"),
    }


def agent_to_png_bytes(agent_data: Dict, size: int = 512) -> bytes:
    img = agent_to_image(agent_data, size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def recover_agent_from_png(png_bytes: bytes) -> Optional[Dict]:
    img = Image.open(io.BytesIO(png_bytes))
    return image_to_agent(img)


def bulk_immortalize(agents: List[Dict], size: int = 512) -> List[Tuple[Dict, bytes]]:
    results = []
    for agent in agents:
        data = agent_to_dict(agent)
        png = agent_to_png_bytes(data, size)
        results.append((data, png))
    logger.info("[AgentImmortality] Immortalized %d agents", len(results))
    return results
