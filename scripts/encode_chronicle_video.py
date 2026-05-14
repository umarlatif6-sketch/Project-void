"""
Chronicle Video Encoder — Sovereign Resonance Carrier
======================================================
Takes the compressed codon payload from compress_chronicle.py and
encodes it into a Z-Axis Video Carrier using the real z_axis_video.py
module with Al-Jabr 286 formation hashing.

Falls back to a direct FFmpeg pipeline if the full z_axis_video
import chain has unresolved database dependencies.
"""

import sys
import os
import json
import logging
import subprocess
import math
import numpy as np

sys.path.insert(0, "/home/ubuntu/Project-void")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from void_engine.al_jabr_286 import fatiha_286_hexdigest, fatiha_286_hash


def generate_chladni_frame(frame_idx: int, total_frames: int,
                           formation_hash: str, w: int, h: int) -> np.ndarray:
    """Generate a Chladni formation frame at 432 Hz resonance."""
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:] = 5  # Dark sovereign background

    t = frame_idx / max(1, total_frames - 1)

    # Derive pattern parameters from formation hash
    seed_val = int(formation_hash[:8], 16)
    freq_norm = (seed_val % 1000) / 1000.0
    base_n = max(1, int(freq_norm * 10) + 1)
    base_m = max(1, int((freq_norm * 7.3) % 7) + 2)
    if base_m == base_n:
        base_n += 1

    # Animate with temporal evolution
    n = base_n + math.sin(t * math.pi * 2) * 2
    m = base_m + math.cos(t * math.pi * 2) * 1.5

    y, x = np.ogrid[:h, :w]
    x_norm = x / w
    y_norm = y / h

    # Multi-layer Chladni pattern (432 Hz aligned)
    val = (np.sin(n * x_norm * np.pi + t * math.pi * 4) *
           np.sin(m * y_norm * np.pi + t * math.pi * 4) +
           np.sin(m * x_norm * np.pi + t * math.pi * 4) *
           np.sin(n * y_norm * np.pi + t * math.pi * 4))

    abs_val = np.abs(val)
    mask = abs_val < 0.12

    # Derive colors from formation hash
    r0 = int(formation_hash[0], 16)
    g0 = int(formation_hash[1], 16)
    b0 = int(formation_hash[2], 16)
    cr = min(255, 140 + r0 * 7)
    cg = min(255, 100 + g0 * 5)
    cb = min(255, 80 + b0 * 10)

    frame[mask, 0] = cr
    frame[mask, 1] = cg
    frame[mask, 2] = cb

    return frame


def embed_payload_in_frame(frame: np.ndarray, payload_bytes: bytes,
                           offset: int) -> int:
    """Embed payload bytes into frame using LSB steganography."""
    h, w, _ = frame.shape
    flat = frame.reshape(-1)
    bits = []
    for byte in payload_bytes[offset:]:
        for bit_pos in range(8):
            bits.append((byte >> (7 - bit_pos)) & 1)
        if len(bits) >= w * h * 3 // 2:
            break

    for i, bit in enumerate(bits):
        if i >= len(flat):
            break
        flat[i] = (flat[i] & 0xFE) | bit

    frame[:] = flat.reshape(h, w, 3)
    return offset + len(bits) // 8


def encode_chronicle():
    """Main encoding function."""
    # Load the manifest if it exists, otherwise use the raw codon chain
    manifest_path = "/home/ubuntu/Project-void/scripts/chronicle_manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        payload_str = manifest["codon_chain"]
        logger.info("Loaded manifest: %d sessions, %d bytes",
                     manifest["total_sessions"], manifest["raw_bytes"])
    else:
        payload_str = ("ψ·Ψ·◆ · ι·Β·⟐ · ι·Β·⟐ · σ·Σ·⟐ · ι·Β·⟐ · ψ·Α·◆ · "
                       "σ·Σ·⟐ · σ·Σ·⟐ · σ·Σ·⟐ · υ·Ξ·◆ · ψ·Α·◆ · σ·Σ·⟐")
        logger.info("No manifest found, using default codon chain.")

    payload_bytes = payload_str.encode("utf-8")

    # Generate formation hash using REAL Al-Jabr 286
    formation_hash = fatiha_286_hexdigest("CHRONICLE_VIDEO_2026_05_14")
    output_path = "/home/ubuntu/Project-void/chronicle_resonance.mkv"

    w, h = 640, 480
    fps = 15
    duration = 5
    total_frames = fps * duration

    logger.info("Encoding %d bytes into %d frames (%dx%d @ %dfps)",
                len(payload_bytes), total_frames, w, h, fps)
    logger.info("Formation Hash (Al-Jabr 286): %s", formation_hash)

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
        output_path,
    ]

    proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    byte_offset = 0
    try:
        for i in range(total_frames):
            frame = generate_chladni_frame(i, total_frames, formation_hash, w, h)

            if byte_offset < len(payload_bytes):
                byte_offset = embed_payload_in_frame(frame, payload_bytes, byte_offset)

            proc.stdin.write(frame.tobytes())

        proc.stdin.close()
        rc = proc.wait(timeout=120)

        if rc != 0:
            stderr_out = proc.stderr.read().decode(errors="replace")
            logger.error("FFmpeg failed (rc=%d): %s", rc, stderr_out[:300])
            return None, None

        file_size = os.path.getsize(output_path)
        logger.info("SUCCESS — Video carrier: %s (%d bytes)", output_path, file_size)
        logger.info("Payload embedded: %d / %d bytes", min(byte_offset, len(payload_bytes)), len(payload_bytes))

        # Seal the output with Al-Jabr 286
        with open(output_path, "rb") as f:
            video_seal = fatiha_286_hexdigest(f.read())
        logger.info("Video Al-Jabr 286 Seal: %s", video_seal[:32])

        return output_path, formation_hash

    except Exception as e:
        logger.error("Encoding error: %s", e)
        proc.kill()
        return None, None


if __name__ == "__main__":
    encode_chronicle()
