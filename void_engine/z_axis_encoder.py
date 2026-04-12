"""
Z-Axis Formation Encoder — Dimensional Steganography Protocol.

Encodes arbitrary data across 9,999 Z-layers of a Chladni formation card image.
Each layer writes 286 bits at pixel positions determined by the formation hash
(encryption key). The result: a formation card PNG that looks like art but
carries a hidden payload.

Decoding reverses the process: given the same formation hash, the exact pixel
positions are recalculated, bits extracted, and the original data recovered.

Capacity:  Bounded by unique pixel×channel slots in the encoding region.
           For a 600×800 image: 560×440 region × 3 channels = ~90 KB usable.
           Slot deduplication across layers prevents overcounting.

Integrity: Al-Jabr 286 checksum on the payload (verified on decode).
Error correction: Simple parity blocks (every 255 bytes gets a parity byte).
"""

import io
import math
import struct
import hashlib
import logging
import numpy as np
from typing import Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from void_engine.al_jabr_286 import (
    fatiha_286_hash,
    fatiha_286_hexdigest,
    fatiha_286_seed,
    fatiha_286_derive_key,
    fatiha_286_truncated,
)
from void_engine.pairing_bw19_286 import (
    al_jabr_to_curve_point,
    ec_add,
    GENERATOR,
)

logger = logging.getLogger(__name__)

Z_LAYERS = 9999
LAYER_OPACITY = 0.003
MAGIC = b"ZVOD"
HEADER_SIZE = 48
PARITY_BLOCK = 255
POSITIONS_PER_LAYER = 286
DEFAULT_WIDTH = 600
DEFAULT_HEIGHT = 800


def _hash_to_seed(formation_hash: str, offset: int) -> int:
    v = 0
    for i in range(8):
        c = formation_hash[(offset + i) % len(formation_hash)]
        v = (v * 16 + int(c, 16)) & 0xFFFFFFFF
    return v


class _ImageBW19Session:
    __slots__ = ('base_point', '_current_point', '_current_z')

    def __init__(self, formation_hash: str):
        self.base_point = al_jabr_to_curve_point(formation_hash)
        self._current_point = self.base_point
        self._current_z = 0

    def layer_seed(self, z: int) -> int:
        if z == 0:
            self._current_point = self.base_point
            self._current_z = 0
        elif z == self._current_z + 1:
            self._current_point = ec_add(self._current_point, GENERATOR)
            self._current_z = z
        elif z != self._current_z:
            pt = self.base_point
            for _ in range(z):
                pt = ec_add(pt, GENERATOR)
            self._current_point = pt
            self._current_z = z
        x, y = self._current_point
        return (x ^ y) & 0xFFFFFFFF


def _pixel_positions_for_layer(z: int, formation_hash: str, width: int, height: int,
                                session: _ImageBW19Session = None) -> list:
    if session is not None:
        seed = session.layer_seed(z)
    else:
        seed = _hash_to_seed(formation_hash, (z * 7) % max(1, len(formation_hash) - 8))
        seed = seed ^ (z * 2654435761 & 0xFFFFFFFF)
    rng = np.random.RandomState(seed)

    margin_x = 20
    margin_y = 60
    region_w = width - 2 * margin_x
    region_h = int(height * 0.55)

    total_pixels = region_w * region_h
    if total_pixels <= 0:
        return []

    n_positions = min(POSITIONS_PER_LAYER, total_pixels)
    indices = rng.choice(total_pixels, size=n_positions, replace=False)
    indices.sort()

    positions = []
    for idx in indices:
        px = int(idx % region_w) + margin_x
        py = int(idx // region_w) + margin_y
        positions.append((px, py))

    return positions


def _add_parity(data: bytes) -> bytes:
    out = bytearray()
    for i in range(0, len(data), PARITY_BLOCK):
        block = data[i:i + PARITY_BLOCK]
        parity = 0
        for b in block:
            parity ^= b
        out.extend(block)
        out.append(parity)
    return bytes(out)


def _check_parity(data: bytes) -> bytes:
    out = bytearray()
    block_size = PARITY_BLOCK + 1
    for i in range(0, len(data), block_size):
        block = data[i:i + block_size]
        if len(block) < 2:
            break
        payload = block[:-1]
        parity = block[-1]
        check = 0
        for b in payload:
            check ^= b
        if check != parity:
            logger.warning("[Z-Axis] Parity check failed at block %d", i // block_size)
        out.extend(payload)
    return bytes(out)


def _build_header(data_size: int, checksum_hex: str) -> bytes:
    checksum_bytes = bytes.fromhex(checksum_hex[:32])
    if len(checksum_bytes) < 16:
        checksum_bytes = checksum_bytes.ljust(16, b'\x00')
    header = (
        MAGIC
        + struct.pack("<I", data_size)
        + struct.pack("<I", Z_LAYERS)
        + checksum_bytes[:16]
        + b'\x00' * (HEADER_SIZE - 4 - 4 - 4 - 16)
    )
    return header[:HEADER_SIZE]


def _parse_header(header_bytes: bytes) -> Tuple[int, int, str]:
    if header_bytes[:4] != MAGIC:
        raise ValueError("Invalid Z-axis header — wrong magic bytes or incorrect formation hash.")
    data_size = struct.unpack("<I", header_bytes[4:8])[0]
    layer_count = struct.unpack("<I", header_bytes[8:12])[0]
    checksum_hex = header_bytes[12:28].hex()
    return data_size, layer_count, checksum_hex


def _generate_formation_image(formation_hash: str, width: int = DEFAULT_WIDTH,
                               height: int = DEFAULT_HEIGHT) -> Image.Image:
    img = Image.new("RGBA", (width, height), (5, 5, 5, 255))
    pixels = np.array(img, dtype=np.float64)

    freq = 432.0 + (_hash_to_seed(formation_hash, 0) % 14800) / 100.0
    f_norm = (freq % 1000) / 1000.0
    base_m = max(1, int(f_norm * 10) + 1)
    base_n = max(1, int((f_norm * 7.3) % 7) + 2)
    if base_m == base_n:
        base_n += 1

    margin_x = 20
    margin_y = 60
    region_w = width - 2 * margin_x
    region_h = int(height * 0.55)

    step = 3
    px_arr = np.arange(0, region_w, step)
    py_arr = np.arange(0, region_h, step)
    nx_grid, ny_grid = np.meshgrid(px_arr / region_w, py_arr / region_h)

    n_visual_layers = 200
    for z in range(n_visual_layers):
        z_norm = z / Z_LAYERS
        seed = _hash_to_seed(formation_hash, z % max(1, len(formation_hash) - 8))
        n = base_n + math.sin(z * 0.01 + seed) * 2
        m = base_m + math.cos(z * 0.013 + seed) * 1.5
        phase = z_norm * math.pi * 2 + seed * 0.1

        r0 = int(formation_hash[(z * 3) % len(formation_hash)], 16)
        g0 = int(formation_hash[(z * 3 + 1) % len(formation_hash)], 16)
        b0 = int(formation_hash[(z * 3 + 2) % len(formation_hash)], 16)
        cr = 140 + r0 * 7
        cg = 100 + g0 * 5
        cb = 50 + b0 * 4

        val = (np.sin(n * nx_grid * np.pi + phase) * np.sin(m * ny_grid * np.pi + phase)
               + np.sin(m * nx_grid * np.pi + phase) * np.sin(n * ny_grid * np.pi + phase))
        abs_val = np.abs(val)
        mask = abs_val < 0.08
        a = LAYER_OPACITY * (1 + abs_val * 3) * mask

        for ci, cc in enumerate([cr, cg, cb]):
            region = pixels[margin_y:margin_y + region_h:step, margin_x:margin_x + region_w:step, ci]
            region += cc * a
            pixels[margin_y:margin_y + region_h:step, margin_x:margin_x + region_w:step, ci] = region

    result = np.clip(pixels, 0, 255).astype(np.uint8)
    img = Image.fromarray(result, "RGBA")
    return img


def _finalize_card(img: Image.Image, formation_hash: str, extra_label: str = "") -> Image.Image:
    draw = ImageDraw.Draw(img)
    w, h = img.size

    try:
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
    except Exception:
        font_sm = ImageFont.load_default()
        font_md = font_sm
        font_lg = font_sm

    draw.rectangle([0, 0, w, 50], fill=(5, 5, 5, 200))
    draw.text((w // 2, 14), "Z-AXIS FORMATION CARD", fill=(192, 149, 90), font=font_sm, anchor="mm")
    draw.text((w // 2, 30), "PROJECT VOID", fill=(255, 255, 255), font=font_md, anchor="mm")
    draw.text((w // 2, 44), f"{Z_LAYERS} LAYERS — DIMENSIONAL STEGANOGRAPHY", fill=(80, 80, 80), font=font_sm, anchor="mm")

    meta_y = int(h * 0.72)
    draw.rectangle([0, meta_y, w, h], fill=(5, 5, 5, 200))
    freq = 432.0 + (_hash_to_seed(formation_hash, 0) % 14800) / 100.0
    draw.text((w // 2, meta_y + 20), f"{freq:.2f} Hz", fill=(192, 149, 90), font=font_lg, anchor="mm")
    draw.text((w // 2, meta_y + 40), f"HASH: {formation_hash[:32]}...", fill=(100, 100, 100), font=font_sm, anchor="mm")
    if extra_label:
        draw.text((w // 2, meta_y + 56), extra_label, fill=(80, 80, 80), font=font_sm, anchor="mm")
    draw.text((w // 2, meta_y + 74), "AL-JABR 286 — BISMILLAHIRRAHMANIRRAHIM", fill=(50, 50, 50), font=font_sm, anchor="mm")

    draw.rectangle([0, 0, w - 1, h - 1], outline=(30, 30, 30))
    draw.rectangle([4, 4, w - 5, h - 5], outline=(192, 149, 90, 80))

    return img


def _compute_actual_capacity(formation_hash: str, width: int, height: int) -> int:
    session = _ImageBW19Session(formation_hash)
    used_slots = set()
    writable = 0
    bit_idx = 0
    for z in range(Z_LAYERS):
        positions = _pixel_positions_for_layer(z, formation_hash, width, height, session=session)
        for i, (px, py) in enumerate(positions):
            channel = (bit_idx + z) % 3
            slot = (px, py, channel)
            if slot not in used_slots:
                used_slots.add(slot)
                writable += 1
            bit_idx += 1
    return writable


def encode(data: bytes, formation_hash: str,
           width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
           progress_callback=None) -> bytes:
    checksum = fatiha_286_hexdigest(data)
    protected = _add_parity(data)
    header = _build_header(len(data), checksum)
    full_payload = header + protected

    payload_bits = []
    for byte in full_payload:
        for bit_pos in range(7, -1, -1):
            payload_bits.append((byte >> bit_pos) & 1)

    total_bits = len(payload_bits)

    margin_x = 20
    margin_y = 60
    region_w = width - 2 * margin_x
    region_h = int(height * 0.55)
    total_unique_pixels = region_w * region_h
    max_unique_slots = total_unique_pixels * 3
    if total_bits > max_unique_slots:
        raise ValueError(
            f"Payload too large: {total_bits} bits needed, max unique pixel slots: {max_unique_slots} bits "
            f"({max_unique_slots // 8:,} bytes) for {width}x{height} image"
        )

    img = _generate_formation_image(formation_hash, width, height)
    label = f"PAYLOAD: {len(data):,} bytes across {Z_LAYERS} layers"
    img = _finalize_card(img, formation_hash, extra_label=label)
    pixels = np.array(img)

    session = _ImageBW19Session(formation_hash)
    used_slots = set()
    bit_idx = 0

    for z in range(Z_LAYERS):
        if bit_idx >= total_bits:
            break

        positions = _pixel_positions_for_layer(z, formation_hash, width, height, session=session)

        for i, (px, py) in enumerate(positions):
            if bit_idx >= total_bits:
                break
            channel = (bit_idx + z) % 3
            slot = (px, py, channel)
            if slot in used_slots:
                continue
            used_slots.add(slot)
            bit_val = payload_bits[bit_idx]
            current = int(pixels[py, px, channel])
            pixels[py, px, channel] = np.uint8((current & 0xFE) | bit_val)
            bit_idx += 1

        if progress_callback and z % 500 == 0:
            progress_callback(z, Z_LAYERS, bit_idx, total_bits)

    if bit_idx < total_bits:
        raise ValueError(
            f"Encoding incomplete: only wrote {bit_idx} of {total_bits} bits. "
            f"Payload too large for {width}x{height} image with current formation hash."
        )

    img = Image.fromarray(pixels, "RGBA")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def decode(image_data: bytes, formation_hash: str,
           progress_callback=None) -> bytes:
    img = Image.open(io.BytesIO(image_data)).convert("RGBA")
    pixels = np.array(img)
    width, height = img.size

    header_bits_needed = HEADER_SIZE * 8
    total_bits_needed = None

    session = _ImageBW19Session(formation_hash)
    all_bits = []
    bit_idx = 0
    used_slots = set()

    for z in range(Z_LAYERS):
        positions = _pixel_positions_for_layer(z, formation_hash, width, height, session=session)

        for i, (px, py) in enumerate(positions):
            channel = (bit_idx + z) % 3
            slot = (px, py, channel)
            if slot in used_slots:
                continue
            used_slots.add(slot)
            if py < pixels.shape[0] and px < pixels.shape[1]:
                bit_val = int(pixels[py, px, channel]) & 1
                all_bits.append(bit_val)
            bit_idx += 1

        if total_bits_needed is None and len(all_bits) >= header_bits_needed:
            header_bytes = _bits_to_bytes(all_bits[:header_bits_needed])
            try:
                data_size, layer_count, stored_checksum = _parse_header(header_bytes)
                protected_size = data_size + (data_size // PARITY_BLOCK + 1)
                total_bits_needed = (HEADER_SIZE + protected_size) * 8
            except ValueError:
                pass

        if total_bits_needed is not None and len(all_bits) >= total_bits_needed:
            break

        if progress_callback and z % 500 == 0:
            progress_callback(z, Z_LAYERS)

    if total_bits_needed is None:
        header_bytes = _bits_to_bytes(all_bits[:header_bits_needed])
        data_size, layer_count, stored_checksum = _parse_header(header_bytes)
        protected_size = data_size + (data_size // PARITY_BLOCK + 1)
        total_bits_needed = (HEADER_SIZE + protected_size) * 8

    if len(all_bits) < total_bits_needed:
        raise ValueError(
            f"Insufficient data extracted: got {len(all_bits)} bits, need {total_bits_needed}"
        )

    payload_bytes = _bits_to_bytes(all_bits[header_bits_needed:total_bits_needed])
    original_data = _check_parity(payload_bytes)[:data_size]

    verify_checksum = fatiha_286_hexdigest(original_data)
    integrity_valid = verify_checksum[:32] == stored_checksum[:32]
    if not integrity_valid:
        raise ValueError(
            f"Al-Jabr 286 integrity check FAILED — data corrupted or wrong formation hash. "
            f"Expected {stored_checksum[:32]}, got {verify_checksum[:32]}"
        )

    return original_data


def _bits_to_bytes(bits: list) -> bytes:
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]
        if len(byte_bits) < 8:
            byte_bits.extend([0] * (8 - len(byte_bits)))
        byte = 0
        for bit in byte_bits:
            byte = (byte << 1) | bit
        result.append(byte)
    return bytes(result)


def calculate_capacity(width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT,
                        layers: int = Z_LAYERS, formation_hash: str = "") -> Dict:
    margin_x = 20
    margin_y = 60
    region_w = width - 2 * margin_x
    region_h = int(height * 0.55)
    total_unique_pixels = region_w * region_h

    max_unique_slots = total_unique_pixels * 3

    overhead_ratio = (PARITY_BLOCK + 1) / PARITY_BLOCK
    practical_bits = max_unique_slots - (HEADER_SIZE * 8)
    practical_bytes = int((practical_bits / 8) / overhead_ratio)

    return {
        "image_width": width,
        "image_height": height,
        "layers": layers,
        "pixels_in_region": total_unique_pixels,
        "positions_per_layer": POSITIONS_PER_LAYER,
        "encoding_region": f"{region_w}x{region_h}",
        "max_unique_slots": max_unique_slots,
        "max_unique_slots_bytes": max_unique_slots // 8,
        "practical_bytes": practical_bytes,
        "practical_kb": round(practical_bytes / 1024, 2),
        "practical_mb": round(practical_bytes / (1024 * 1024), 2),
        "overhead_parity_pct": round((overhead_ratio - 1) * 100, 2),
        "header_bytes": HEADER_SIZE,
        "layer_opacity": LAYER_OPACITY,
        "protocol": "Z-Axis Dimensional Steganography",
        "integrity": "Al-Jabr 286 checksum (verified on decode)",
        "error_correction": f"Parity block every {PARITY_BLOCK} bytes",
    }


def encode_for_agent_immortality(agent_data: dict, formation_hash: str,
                                  size: int = 512) -> bytes:
    import json
    state_json = json.dumps(agent_data, default=str, separators=(",", ":"))
    state_bytes = state_json.encode("utf-8")
    integrity = fatiha_286_truncated(state_bytes, 24)
    envelope = json.dumps({
        "version": "2.0",
        "type": "VOID_AGENT_IMMORTALITY_ZAXIS",
        "integrity_286": integrity,
        "layers": Z_LAYERS,
        "agent": agent_data,
    }, default=str, separators=(",", ":")).encode("utf-8")

    return encode(envelope, formation_hash, width=size, height=size + 120)


def encode_memory_metadata(memory: dict, formation_hash: str,
                            thumbnail_data: str = "") -> bytes:
    import json
    payload = json.dumps({
        "version": "1.0",
        "type": "VOID_MEMORY_ZAXIS",
        "memory": memory,
        "thumbnail_preview": thumbnail_data[:5000] if thumbnail_data else "",
        "integrity_286": fatiha_286_truncated(
            json.dumps(memory, default=str).encode("utf-8"), 24
        ),
    }, default=str, separators=(",", ":")).encode("utf-8")

    return encode(payload, formation_hash)


def encode_voidecho_bridge(audio_stego_data: bytes, formation_hash: str) -> bytes:
    import json
    envelope = json.dumps({
        "version": "1.0",
        "type": "VOID_ECHO_ZAXIS_BRIDGE",
        "audio_stego_size": len(audio_stego_data),
        "integrity_286": fatiha_286_truncated(audio_stego_data, 24),
    }, default=str, separators=(",", ":")).encode("utf-8")

    combined = envelope + b"\x00\x00\x00\x00" + audio_stego_data
    return encode(combined, formation_hash)


def encode_resonance_moment(context: dict, formation_hash: str) -> bytes:
    import json
    payload = json.dumps({
        "version": "1.0",
        "type": "VOID_RESONANCE_MOMENT",
        "context": context,
        "integrity_286": fatiha_286_truncated(
            json.dumps(context, default=str).encode("utf-8"), 24
        ),
    }, default=str, separators=(",", ":")).encode("utf-8")

    return encode(payload, formation_hash)
