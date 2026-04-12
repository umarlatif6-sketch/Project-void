"""
Z-Axis Video Carrier — Gigabyte-Scale Dimensional Steganography.

Encodes arbitrary data across video frames using LSB steganography.
Each frame is a canvas: every pixel×channel slot can hold 1 bit.
A 1-minute 1080p 30fps video = 1,800 frames × ~740 KB/frame = ~1.3 GB capacity.

Encoding flow:
  1. Read input data → ChaCha20 encrypt → Al-Jabr 286 checksum header
  2. For each frame: derive pixel positions from formation hash + frame index
  3. Write payload bits into LSBs at those positions
  4. Reassemble frames into video via ffmpeg (lossless intermediate → final codec)

Decoding flow:
  1. Extract frames via ffmpeg → read LSBs at formation-hash-derived positions
  2. Reassemble bits → verify Al-Jabr 286 checksum → ChaCha20 decrypt → original data

Memory: Frames processed one at a time via ffmpeg pipes. Never loads full video into RAM.
Carrier generation: If no input video, generates animated Chladni formation patterns.
"""

import io
import os
import math
import struct
import hashlib
import logging
import secrets
import subprocess
import tempfile
import numpy as np
from typing import Dict, Optional, Callable

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from void_engine.al_jabr_286 import (
    fatiha_286_hash,
    fatiha_286_hexdigest,
    fatiha_286_seed,
    fatiha_286_derive_key,
    fatiha_286_truncated,
)

logger = logging.getLogger(__name__)

MAGIC = b"ZVID"
HEADER_SIZE = 64
PARITY_BLOCK = 255
VILLAGE_STANDARD_HZ = 432

RESOLUTIONS = {
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}

DEFAULT_FPS = 30
DEFAULT_RESOLUTION = "1080p"


def _hash_to_seed(formation_hash: str, offset: int) -> int:
    v = 0
    for i in range(8):
        c = formation_hash[(offset + i) % len(formation_hash)]
        v = (v * 16 + int(c, 16)) & 0xFFFFFFFF
    return v


def _derive_key(formation_hash: str) -> bytes:
    return fatiha_286_derive_key(formation_hash)


def _encrypt_payload(data: bytes, key: bytes) -> tuple:
    nonce = secrets.token_bytes(16)
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(data) + encryptor.finalize()
    return encrypted, nonce


def _decrypt_payload(encrypted: bytes, key: bytes, nonce: bytes) -> bytes:
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted) + decryptor.finalize()


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
        payload_part = block[:-1]
        parity = block[-1]
        check = 0
        for b in payload_part:
            check ^= b
        if check != parity:
            logger.warning("[Z-Video] Parity check failed at block %d", i // block_size)
        out.extend(payload_part)
    return bytes(out)


def _build_header(data_size: int, checksum_hex: str, nonce: bytes,
                  total_frames: int, width: int, height: int) -> bytes:
    checksum_bytes = bytes.fromhex(checksum_hex[:32])
    if len(checksum_bytes) < 16:
        checksum_bytes = checksum_bytes.ljust(16, b'\x00')
    header = (
        MAGIC
        + struct.pack("<Q", data_size)
        + struct.pack("<I", total_frames)
        + struct.pack("<H", width)
        + struct.pack("<H", height)
        + checksum_bytes[:16]
        + nonce[:16]
        + b'\x00' * (HEADER_SIZE - 4 - 8 - 4 - 2 - 2 - 16 - 16)
    )
    return header[:HEADER_SIZE]


def _parse_header(header_bytes: bytes):
    if len(header_bytes) < HEADER_SIZE:
        raise ValueError("Header too short")
    if header_bytes[:4] != MAGIC:
        raise ValueError("Invalid Z-Video header — wrong magic bytes or incorrect formation hash.")
    data_size = struct.unpack("<Q", header_bytes[4:12])[0]
    total_frames = struct.unpack("<I", header_bytes[12:16])[0]
    width = struct.unpack("<H", header_bytes[16:18])[0]
    height = struct.unpack("<H", header_bytes[18:20])[0]
    checksum_hex = header_bytes[20:36].hex()
    nonce = header_bytes[36:52]
    return data_size, total_frames, width, height, checksum_hex, nonce


def _frame_pixel_positions(frame_idx: int, formation_hash: str,
                           width: int, height: int) -> np.ndarray:
    offset = (frame_idx * 7) % max(1, len(formation_hash) - 8)
    seed = _hash_to_seed(formation_hash, offset)
    rng = np.random.RandomState(seed ^ (frame_idx * 2654435761 & 0xFFFFFFFF))
    total_pixels = width * height
    indices = rng.permutation(total_pixels)
    return indices


def _bits_per_frame(width: int, height: int) -> int:
    return width * height * 3


def calculate_video_capacity(resolution: str = "1080p", fps: int = 30,
                             duration_seconds: int = 60) -> Dict:
    if resolution in RESOLUTIONS:
        w, h = RESOLUTIONS[resolution]
    else:
        w, h = RESOLUTIONS["1080p"]

    total_frames = fps * duration_seconds
    bits_per_f = _bits_per_frame(w, h)
    total_bits = total_frames * bits_per_f

    overhead_ratio = (PARITY_BLOCK + 1) / PARITY_BLOCK
    practical_bits = total_bits - (HEADER_SIZE * 8)
    practical_bytes = int((practical_bits / 8) / overhead_ratio)

    return {
        "resolution": resolution,
        "width": w,
        "height": h,
        "fps": fps,
        "duration_seconds": duration_seconds,
        "total_frames": total_frames,
        "bits_per_frame": bits_per_f,
        "total_bits": total_bits,
        "total_bytes": total_bits // 8,
        "practical_bytes": practical_bytes,
        "practical_kb": round(practical_bytes / 1024, 2),
        "practical_mb": round(practical_bytes / (1024 * 1024), 2),
        "practical_gb": round(practical_bytes / (1024 * 1024 * 1024), 4),
        "overhead_parity_pct": round((overhead_ratio - 1) * 100, 2),
        "header_bytes": HEADER_SIZE,
        "protocol": "Z-Axis Video Carrier — Dimensional Steganography",
        "encryption": "ChaCha20 (formation-hash-derived key)",
        "integrity": "Al-Jabr 286 checksum (verified on decode)",
        "error_correction": f"Parity block every {PARITY_BLOCK} bytes",
    }


def _generate_chladni_frame(frame_idx: int, total_frames: int,
                            formation_hash: str, width: int, height: int) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = 5

    freq = 432.0 + (_hash_to_seed(formation_hash, 0) % 14800) / 100.0
    f_norm = (freq % 1000) / 1000.0
    base_m = max(1, int(f_norm * 10) + 1)
    base_n = max(1, int((f_norm * 7.3) % 7) + 2)
    if base_m == base_n:
        base_n += 1

    step = 2
    px_arr = np.arange(0, width, step)
    py_arr = np.arange(0, height, step)
    nx_grid, ny_grid = np.meshgrid(px_arr / width, py_arr / height)

    pixels = frame.astype(np.float64)
    t = frame_idx / max(1, total_frames - 1)

    n_layers = 8
    for z in range(n_layers):
        z_t = z / n_layers
        seed = _hash_to_seed(formation_hash, (z * 3) % max(1, len(formation_hash) - 8))
        n = base_n + math.sin(z * 0.5 + seed + t * math.pi * 2) * 2
        m = base_m + math.cos(z * 0.7 + seed + t * math.pi * 2) * 1.5
        phase = t * math.pi * 4 + z_t * math.pi * 2 + seed * 0.1

        r0 = int(formation_hash[(z * 3) % len(formation_hash)], 16)
        g0 = int(formation_hash[(z * 3 + 1) % len(formation_hash)], 16)
        b0 = int(formation_hash[(z * 3 + 2) % len(formation_hash)], 16)
        cr = 140 + r0 * 7
        cg = 100 + g0 * 5
        cb = 50 + b0 * 4

        val = (np.sin(n * nx_grid * np.pi + phase) * np.sin(m * ny_grid * np.pi + phase)
               + np.sin(m * nx_grid * np.pi + phase) * np.sin(n * ny_grid * np.pi + phase))
        abs_val = np.abs(val)
        mask = abs_val < 0.15
        a = 0.08 * (1 + abs_val * 3) * mask

        for ci, cc in enumerate([cr, cg, cb]):
            region = pixels[::step, ::step, ci]
            region += cc * a
            pixels[::step, ::step, ci] = region

    result = np.clip(pixels, 0, 255).astype(np.uint8)
    return result


def _required_frames(data_size_bytes: int, width: int, height: int) -> int:
    bpf = _bits_per_frame(width, height)
    overhead_ratio = (PARITY_BLOCK + 1) / PARITY_BLOCK
    protected_size = int(data_size_bytes * overhead_ratio) + 1
    total_bits = (HEADER_SIZE + protected_size) * 8
    return max(1, math.ceil(total_bits / bpf))


def encode_to_video(data: bytes, formation_hash: str,
                    carrier_video_path: Optional[str] = None,
                    resolution: str = "1080p", fps: int = 30,
                    duration_seconds: Optional[int] = None,
                    output_path: Optional[str] = None,
                    progress_callback: Optional[Callable] = None) -> str:
    if not formation_hash:
        formation_hash = fatiha_286_hexdigest(data)

    if resolution in RESOLUTIONS:
        w, h = RESOLUTIONS[resolution]
    else:
        w, h = RESOLUTIONS["1080p"]

    key = _derive_key(formation_hash)
    checksum = fatiha_286_hexdigest(data)
    encrypted, nonce = _encrypt_payload(data, key)
    protected = _add_parity(encrypted)

    if carrier_video_path and os.path.exists(carrier_video_path):
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
            "-of", "csv=p=0",
            carrier_video_path
        ]
        try:
            probe_out = subprocess.check_output(probe_cmd, timeout=30).decode().strip()
            parts = probe_out.split(",")
            w = int(parts[0])
            h = int(parts[1])
            fps_parts = parts[2].split("/")
            fps = int(fps_parts[0]) // max(1, int(fps_parts[1])) if len(fps_parts) == 2 else int(fps_parts[0])
            if len(parts) > 3 and parts[3].isdigit():
                total_frames = int(parts[3])
            elif len(parts) > 4:
                try:
                    dur = float(parts[4])
                    total_frames = int(dur * fps)
                except (ValueError, IndexError):
                    total_frames = None
            else:
                total_frames = None
        except Exception as e:
            logger.warning("[Z-Video] Probe failed, using defaults: %s", e)
            total_frames = None

        min_frames = _required_frames(len(data), w, h)

        if total_frames is not None and total_frames < min_frames:
            raise ValueError(
                f"Carrier video too short: {total_frames} frames available, "
                f"need {min_frames} frames for {len(data):,} bytes payload"
            )
        if total_frames is None:
            total_frames = min_frames * 2
        use_carrier = True
    else:
        min_frames = _required_frames(len(data), w, h)
        if duration_seconds is None:
            duration_seconds = max(5, math.ceil(min_frames / fps) + 1)
        total_frames = fps * duration_seconds
        if total_frames < min_frames:
            duration_seconds = math.ceil(min_frames / fps) + 1
            total_frames = fps * duration_seconds
        use_carrier = False

    header = _build_header(len(data), checksum, nonce, total_frames, w, h)
    full_payload = header + protected

    payload_bits = np.unpackbits(np.frombuffer(full_payload, dtype=np.uint8))
    total_bits = len(payload_bits)

    bpf = _bits_per_frame(w, h)
    capacity_bits = total_frames * bpf

    if total_bits > capacity_bits:
        raise ValueError(
            f"Payload too large: {total_bits} bits needed, "
            f"video capacity: {capacity_bits} bits ({capacity_bits // 8:,} bytes)"
        )

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".mkv")
        os.close(fd)

    if use_carrier:
        _encode_with_carrier(
            carrier_video_path, output_path, formation_hash,
            payload_bits, w, h, fps, progress_callback
        )
    else:
        _encode_generated(
            output_path, formation_hash, payload_bits,
            w, h, fps, total_frames, progress_callback
        )

    return output_path


def _encode_generated(output_path: str, formation_hash: str,
                      payload_bits: np.ndarray, w: int, h: int,
                      fps: int, total_frames: int,
                      progress_callback: Optional[Callable]) -> None:
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{w}x{h}",
        "-r", str(fps),
        "-i", "pipe:0",
        "-c:v", "ffv1",
        "-pix_fmt", "rgb24",
        "-level", "3",
        output_path
    ]

    proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    bpf = _bits_per_frame(w, h)
    bit_offset = 0
    total_bits = len(payload_bits)

    try:
        for frame_idx in range(total_frames):
            frame = _generate_chladni_frame(frame_idx, total_frames, formation_hash, w, h)

            if bit_offset < total_bits:
                chunk_end = min(bit_offset + bpf, total_bits)
                chunk_bits = payload_bits[bit_offset:chunk_end]

                positions = _frame_pixel_positions(frame_idx, formation_hash, w, h)

                bi = 0
                for px_idx in positions:
                    if bi >= len(chunk_bits):
                        break
                    py_coord = int(px_idx // w)
                    px_coord = int(px_idx % w)
                    for ch in range(3):
                        if bi >= len(chunk_bits):
                            break
                        frame[py_coord, px_coord, ch] = (frame[py_coord, px_coord, ch] & 0xFE) | int(chunk_bits[bi])
                        bi += 1

                bit_offset = chunk_end

            proc.stdin.write(frame.tobytes())

            if progress_callback and frame_idx % 30 == 0:
                progress_callback(frame_idx, total_frames, bit_offset, total_bits)

    finally:
        proc.stdin.close()
        proc.wait(timeout=120)


def _encode_with_carrier(carrier_path: str, output_path: str,
                         formation_hash: str, payload_bits: np.ndarray,
                         w: int, h: int, fps: int,
                         progress_callback: Optional[Callable]) -> None:
    extract_cmd = [
        "ffmpeg", "-i", carrier_path,
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-v", "error",
        "pipe:1"
    ]

    encode_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{w}x{h}",
        "-r", str(fps),
        "-i", "pipe:0",
        "-i", carrier_path,
        "-map", "0:v",
        "-map", "1:a?",
        "-c:v", "ffv1",
        "-pix_fmt", "rgb24",
        "-level", "3",
        "-c:a", "copy",
        output_path
    ]

    extract_proc = subprocess.Popen(
        extract_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    encode_proc = subprocess.Popen(
        encode_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    frame_size = w * h * 3
    bpf = _bits_per_frame(w, h)
    bit_offset = 0
    total_bits = len(payload_bits)
    frame_idx = 0

    try:
        while True:
            raw = extract_proc.stdout.read(frame_size)
            if len(raw) < frame_size:
                break

            frame = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3)).copy()

            if bit_offset < total_bits:
                chunk_end = min(bit_offset + bpf, total_bits)
                chunk_bits = payload_bits[bit_offset:chunk_end]

                positions = _frame_pixel_positions(frame_idx, formation_hash, w, h)

                bi = 0
                for px_idx in positions:
                    if bi >= len(chunk_bits):
                        break
                    py_coord = int(px_idx // w)
                    px_coord = int(px_idx % w)
                    for ch in range(3):
                        if bi >= len(chunk_bits):
                            break
                        frame[py_coord, px_coord, ch] = (frame[py_coord, px_coord, ch] & 0xFE) | int(chunk_bits[bi])
                        bi += 1

                bit_offset = chunk_end

            encode_proc.stdin.write(frame.tobytes())
            frame_idx += 1

            if progress_callback and frame_idx % 30 == 0:
                progress_callback(frame_idx, -1, bit_offset, total_bits)

    finally:
        extract_proc.stdout.close()
        extract_proc.wait(timeout=60)
        encode_proc.stdin.close()
        rc = encode_proc.wait(timeout=120)
        if rc != 0:
            stderr_out = encode_proc.stderr.read().decode(errors="replace") if encode_proc.stderr else ""
            raise RuntimeError(f"ffmpeg encode failed (rc={rc}): {stderr_out[:500]}")
        if bit_offset < total_bits:
            raise RuntimeError(
                f"Carrier video ended before all data was written: "
                f"{bit_offset}/{total_bits} bits embedded"
            )


def decode_from_video(video_path: str, formation_hash: str,
                      output_path: Optional[str] = None,
                      progress_callback: Optional[Callable] = None) -> bytes:
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        video_path
    ]
    probe_out = subprocess.check_output(probe_cmd, timeout=30).decode().strip()
    parts = probe_out.split(",")
    w = int(parts[0])
    h = int(parts[1])

    extract_cmd = [
        "ffmpeg", "-i", video_path,
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-v", "error",
        "pipe:1"
    ]

    proc = subprocess.Popen(
        extract_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    frame_size = w * h * 3
    bpf = _bits_per_frame(w, h)
    bit_chunks = []
    total_collected = 0
    header_parsed = False
    data_size = None
    total_frames_expected = None
    checksum_hex = None
    nonce = None
    total_bits_needed = None
    frame_idx = 0

    try:
        while True:
            raw = proc.stdout.read(frame_size)
            if len(raw) < frame_size:
                break

            frame = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3))

            positions = _frame_pixel_positions(frame_idx, formation_hash, w, h)

            needed_this_frame = bpf
            if total_bits_needed is not None:
                needed_this_frame = min(bpf, total_bits_needed - total_collected)
                if needed_this_frame <= 0:
                    break

            n_pixels = (needed_this_frame + 2) // 3
            pos_subset = positions[:n_pixels]
            py_coords = (pos_subset // w).astype(np.intp)
            px_coords = (pos_subset % w).astype(np.intp)
            pixel_vals = frame[py_coords, px_coords, :]
            frame_bits = (pixel_vals & 1).flatten()[:needed_this_frame]
            bit_chunks.append(frame_bits)
            total_collected += len(frame_bits)

            if not header_parsed and total_collected >= HEADER_SIZE * 8:
                all_bits_so_far = np.concatenate(bit_chunks)
                header_bytes = np.packbits(all_bits_so_far[:HEADER_SIZE * 8]).tobytes()
                try:
                    data_size, total_frames_expected, _, _, checksum_hex, nonce = _parse_header(header_bytes)
                    protected_size = data_size + (data_size // PARITY_BLOCK + 1)
                    total_bits_needed = (HEADER_SIZE + protected_size) * 8
                    header_parsed = True
                except ValueError:
                    pass

            if total_bits_needed is not None and total_collected >= total_bits_needed:
                break

            frame_idx += 1

            if progress_callback and frame_idx % 30 == 0:
                progress_callback(frame_idx, total_frames_expected or -1)

    finally:
        proc.stdout.close()
        rc = proc.wait(timeout=60)
        if rc != 0:
            stderr_out = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
            logger.warning("[Z-Video] ffmpeg decode exited rc=%d: %s", rc, stderr_out[:200])

    all_bits = np.concatenate(bit_chunks) if bit_chunks else np.array([], dtype=np.uint8)

    if not header_parsed:
        if len(all_bits) < HEADER_SIZE * 8:
            raise ValueError("Video too short to contain Z-Video header")
        header_bytes = np.packbits(all_bits[:HEADER_SIZE * 8]).tobytes()
        data_size, total_frames_expected, _, _, checksum_hex, nonce = _parse_header(header_bytes)
        protected_size = data_size + (data_size // PARITY_BLOCK + 1)
        total_bits_needed = (HEADER_SIZE + protected_size) * 8

    if len(all_bits) < total_bits_needed:
        raise ValueError(
            f"Insufficient data: got {len(all_bits)} bits, need {total_bits_needed}. "
            f"Video may be too short or wrong formation hash."
        )

    payload_bits = all_bits[HEADER_SIZE * 8:total_bits_needed]
    payload_bytes = np.packbits(payload_bits).tobytes()
    decrypted_protected = _check_parity(payload_bytes)[:data_size]

    key = _derive_key(formation_hash)
    original_data = _decrypt_payload(decrypted_protected, key, nonce)

    verify_checksum = fatiha_286_hexdigest(original_data)
    if verify_checksum[:32] != checksum_hex[:32]:
        raise ValueError(
            f"Al-Jabr 286 integrity check FAILED — data corrupted or wrong formation hash. "
            f"Expected {checksum_hex[:32]}, got {verify_checksum[:32]}"
        )

    if output_path:
        with open(output_path, "wb") as f:
            f.write(original_data)

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


def get_video_info(video_path: str) -> Dict:
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
        "-of", "json",
        video_path
    ]
    import json
    out = subprocess.check_output(probe_cmd, timeout=30).decode()
    info = json.loads(out)
    stream = info.get("streams", [{}])[0]

    w = int(stream.get("width", 0))
    h = int(stream.get("height", 0))
    fps_str = stream.get("r_frame_rate", "30/1")
    fps_parts = fps_str.split("/")
    fps = int(fps_parts[0]) // max(1, int(fps_parts[1])) if len(fps_parts) == 2 else 30

    nb_frames = stream.get("nb_frames", "0")
    if nb_frames and nb_frames != "N/A":
        total_frames = int(nb_frames)
    else:
        dur = float(stream.get("duration", "0") or "0")
        total_frames = int(dur * fps) if dur > 0 else 0

    bpf = _bits_per_frame(w, h)
    cap = calculate_video_capacity.__wrapped__ if hasattr(calculate_video_capacity, '__wrapped__') else None

    return {
        "width": w,
        "height": h,
        "fps": fps,
        "total_frames": total_frames,
        "duration_seconds": total_frames / max(1, fps),
        "bits_per_frame": bpf,
        "capacity_bytes": (total_frames * bpf) // 8,
        "capacity_mb": round((total_frames * bpf) / 8 / 1024 / 1024, 2),
        "capacity_gb": round((total_frames * bpf) / 8 / 1024 / 1024 / 1024, 4),
    }
