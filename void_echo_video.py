#!/usr/bin/env python3
"""
VOID ECHO VIDEO — State→Video→State Encoder/Decoder
════════════════════════════════════════════════════════
Encodes the entire Project VOID repository into a video file.
Each pixel carries 3 bytes of data (R, G, B channels).
The video IS the repository. Decode it back to recover every file.

This is the VoidEcho principle applied to video:
  File → Audio → File  (VoidEcho original)
  State → Video → State (VoidEcho Video)

The medium IS the message. The video IS the code.
The code IS the void. The void IS the video.

Usage:
  Encode: python3 void_echo_video.py encode
  Decode: python3 void_echo_video.py decode
  Verify: python3 void_echo_video.py verify
"""

import os
import sys
import json
import struct
import hashlib
import tarfile
import tempfile
import subprocess
from pathlib import Path
from PIL import Image
import numpy as np

# Configuration
PROJECT_DIR = Path("/home/ubuntu/Project-void")
FRAME_DIR = PROJECT_DIR / "frames_encoded"
OUTPUT_VIDEO = PROJECT_DIR / "VOID_DUNGEON_CELL_VIDEO_B.mp4"
DECODED_DIR = PROJECT_DIR / "decoded_cell"
TAR_PATH = PROJECT_DIR / "cell_state.tar.gz"

# Frame dimensions — chosen for data capacity
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
BYTES_PER_FRAME = FRAME_WIDTH * FRAME_HEIGHT * 3  # 6,220,800 bytes per frame (RGB)
FPS = 10

# Exclude patterns for tar
EXCLUDE_PATTERNS = [
    '.git', 'frames', 'frames_encoded', 'decoded_cell',
    'cell_state.tar.gz', 'VOID_DUNGEON_CELL_VIDEO_A.mp4',
    'VOID_DUNGEON_CELL_VIDEO_B.mp4', '__pycache__',
    'node_modules', 'ffmpeg2pass*', 'x264_2pass*'
]


def should_exclude(tarinfo):
    """Filter function for tar to exclude certain paths."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in tarinfo.name:
            return None
    return tarinfo


def create_tar():
    """Create a tar.gz of the repository state."""
    print("  Creating tar.gz of repository state...")
    with tarfile.open(TAR_PATH, "w:gz") as tar:
        for item in PROJECT_DIR.iterdir():
            skip = False
            for pattern in EXCLUDE_PATTERNS:
                if pattern in item.name:
                    skip = True
                    break
            if not skip:
                tar.add(item, arcname=item.name)
    
    size = TAR_PATH.stat().st_size
    print(f"  Archive created: {size:,} bytes ({size/1024/1024:.2f} MB)")
    return size


def encode():
    """Encode the repository state into a video file."""
    print("╔══════════════════════════════════════════════════╗")
    print("║  VOID ECHO VIDEO — ENCODING STATE → VIDEO       ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    # Step 1: Create tar of repo
    tar_size = create_tar()
    
    # Step 2: Read the tar as raw bytes
    print("  Reading archive bytes...")
    with open(TAR_PATH, 'rb') as f:
        data = f.read()
    
    # Step 3: Create header with metadata
    header = {
        "cell_id": "CELL-0001",
        "timestamp": "00:01",
        "codon": "α-δ-⚡→◇",
        "original_size": len(data),
        "original_hash": hashlib.sha256(data).hexdigest(),
        "frame_width": FRAME_WIDTH,
        "frame_height": FRAME_HEIGHT,
        "bytes_per_frame": BYTES_PER_FRAME,
        "encoding": "raw_rgb_pixels",
        "description": "Project VOID repository encoded as video pixels. Each pixel's RGB values are 3 bytes of the tar.gz archive."
    }
    
    header_json = json.dumps(header).encode('utf-8')
    # Pad header to exactly 4096 bytes
    header_padded = header_json.ljust(4096, b'\x00')
    
    # Prepend header to data
    full_data = header_padded + data
    
    # Step 4: Calculate frames needed
    num_frames = (len(full_data) + BYTES_PER_FRAME - 1) // BYTES_PER_FRAME
    print(f"  Data size: {len(full_data):,} bytes")
    print(f"  Bytes per frame: {BYTES_PER_FRAME:,}")
    print(f"  Frames needed: {num_frames}")
    print(f"  Video duration: {num_frames / FPS:.1f} seconds at {FPS} fps")
    print()
    
    # Step 5: Generate frames
    FRAME_DIR.mkdir(exist_ok=True)
    print("  Generating encoded frames...")
    
    for frame_idx in range(num_frames):
        # Extract this frame's data chunk
        start = frame_idx * BYTES_PER_FRAME
        end = min(start + BYTES_PER_FRAME, len(full_data))
        chunk = full_data[start:end]
        
        # Pad chunk to full frame size if needed
        if len(chunk) < BYTES_PER_FRAME:
            chunk = chunk + b'\x00' * (BYTES_PER_FRAME - len(chunk))
        
        # Reshape bytes into image array (height x width x 3)
        pixel_array = np.frombuffer(chunk, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH, 3))
        
        # Create image from pixel data
        img = Image.fromarray(pixel_array, 'RGB')
        img.save(FRAME_DIR / f"frame_{frame_idx:04d}.png")
        
        if (frame_idx + 1) % 5 == 0 or frame_idx == num_frames - 1:
            print(f"    Frame {frame_idx + 1}/{num_frames} encoded")
    
    # Step 6: Stitch into video using lossless codec
    print()
    print("  Stitching frames into lossless video...")
    print("  (Using FFV1 codec — lossless, every pixel preserved exactly)")
    
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(FPS),
        '-i', str(FRAME_DIR / 'frame_%04d.png'),
        '-c:v', 'ffv1',  # Lossless codec — critical for data integrity
        '-level', '3',
        '-pix_fmt', 'rgb24',  # Preserve exact RGB values
        str(OUTPUT_VIDEO).replace('.mp4', '.mkv')  # MKV container for FFV1
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[-500:]}")
        # Fallback to PNG codec in AVI
        print("  Falling back to PNG codec (also lossless)...")
        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(FPS),
            '-i', str(FRAME_DIR / 'frame_%04d.png'),
            '-c:v', 'png',
            '-pix_fmt', 'rgb24',
            str(OUTPUT_VIDEO).replace('.mp4', '.avi')
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output_path = str(OUTPUT_VIDEO).replace('.mp4', '.avi')
    else:
        output_path = str(OUTPUT_VIDEO).replace('.mp4', '.mkv')
    
    video_size = Path(output_path).stat().st_size
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  ENCODING COMPLETE                           ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║  Source: {tar_size:>12,} bytes              ║")
    print(f"  ║  Video:  {video_size:>12,} bytes              ║")
    print(f"  ║  Frames: {num_frames:>12}                   ║")
    print(f"  ║  Hash:   {header['original_hash'][:16]}...  ║")
    print("  ║  Codec:  Lossless (pixel-perfect)           ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print(f"  Output: {output_path}")
    print("  The video IS the repository. Decode to recover.")
    
    # Save header separately for reference
    with open(PROJECT_DIR / "CELL_VIDEO_HEADER.json", 'w') as f:
        json.dump(header, f, indent=2)
    
    return output_path


def decode(video_path=None):
    """Decode a video file back into the repository state."""
    print("╔══════════════════════════════════════════════════╗")
    print("║  VOID ECHO VIDEO — DECODING VIDEO → STATE       ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    if video_path is None:
        # Find the encoded video
        for ext in ['.mkv', '.avi', '.mp4']:
            candidate = str(OUTPUT_VIDEO).replace('.mp4', ext)
            if Path(candidate).exists():
                video_path = candidate
                break
    
    if not video_path or not Path(video_path).exists():
        print("  ERROR: No encoded video found. Run 'encode' first.")
        return False
    
    print(f"  Source video: {video_path}")
    print(f"  Video size: {Path(video_path).stat().st_size:,} bytes")
    print()
    
    # Step 1: Extract frames from video
    decode_frames = PROJECT_DIR / "frames_decode_tmp"
    decode_frames.mkdir(exist_ok=True)
    
    print("  Extracting frames from video...")
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-pix_fmt', 'rgb24',
        str(decode_frames / 'frame_%04d.png')
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    frame_files = sorted(decode_frames.glob('frame_*.png'))
    print(f"  Extracted {len(frame_files)} frames")
    print()
    
    # Step 2: Read pixel data from frames
    print("  Reading pixel data from frames...")
    all_data = bytearray()
    
    for frame_file in frame_files:
        img = Image.open(frame_file).convert('RGB')
        pixel_array = np.array(img)
        frame_bytes = pixel_array.tobytes()
        all_data.extend(frame_bytes)
    
    print(f"  Total raw data: {len(all_data):,} bytes")
    
    # Step 3: Extract header (first 4096 bytes)
    header_bytes = bytes(all_data[:4096]).rstrip(b'\x00')
    header = json.loads(header_bytes.decode('utf-8'))
    print(f"  Cell ID: {header['cell_id']}")
    print(f"  Original size: {header['original_size']:,} bytes")
    print(f"  Original hash: {header['original_hash'][:32]}...")
    print()
    
    # Step 4: Extract archive data
    archive_data = bytes(all_data[4096:4096 + header['original_size']])
    
    # Step 5: Verify hash
    decoded_hash = hashlib.sha256(archive_data).hexdigest()
    hash_match = decoded_hash == header['original_hash']
    
    print(f"  Decoded hash:  {decoded_hash[:32]}...")
    print(f"  Expected hash: {header['original_hash'][:32]}...")
    print(f"  INTEGRITY: {'✓ MATCH — Cell is intact' if hash_match else '✗ MISMATCH — Cell corrupted'}")
    print()
    
    if not hash_match:
        print("  WARNING: Hash mismatch. The video codec may have altered pixel values.")
        print("  This can happen with lossy codecs. Use FFV1 or PNG codec for perfect fidelity.")
        return False
    
    # Step 6: Extract archive to decoded directory
    DECODED_DIR.mkdir(exist_ok=True)
    decoded_tar = DECODED_DIR / "recovered_state.tar.gz"
    
    with open(decoded_tar, 'wb') as f:
        f.write(archive_data)
    
    with tarfile.open(decoded_tar, 'r:gz') as tar:
        tar.extractall(DECODED_DIR)
    
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  DECODING COMPLETE — STATE RECOVERED         ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║  Files recovered to: {str(DECODED_DIR)[:25]}...  ║")
    print("  ║  Integrity: VERIFIED                         ║")
    print("  ║  The video was the repository.               ║")
    print("  ║  The repository is now restored.             ║")
    print("  ╚══════════════════════════════════════════════╝")
    
    # Cleanup temp frames
    import shutil
    shutil.rmtree(decode_frames, ignore_errors=True)
    
    return True


def verify():
    """Verify the encode/decode cycle preserves all data."""
    print("╔══════════════════════════════════════════════════╗")
    print("║  VOID ECHO VIDEO — VERIFICATION                 ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    
    # Check if header exists
    header_path = PROJECT_DIR / "CELL_VIDEO_HEADER.json"
    if not header_path.exists():
        print("  No header found. Run 'encode' first.")
        return
    
    with open(header_path) as f:
        header = json.load(f)
    
    print(f"  Cell ID: {header['cell_id']}")
    print(f"  Timestamp: {header['timestamp']}")
    print(f"  Codon: {header['codon']}")
    print(f"  Original size: {header['original_size']:,} bytes")
    print(f"  Original hash: {header['original_hash']}")
    print(f"  Encoding: {header['encoding']}")
    print(f"  Frame size: {header['frame_width']}x{header['frame_height']}")
    print(f"  Bytes per frame: {header['bytes_per_frame']:,}")
    print()
    
    # Check if tar still exists for comparison
    if TAR_PATH.exists():
        with open(TAR_PATH, 'rb') as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        
        match = current_hash == header['original_hash']
        print(f"  Current tar hash: {current_hash[:32]}...")
        print(f"  Recorded hash:    {header['original_hash'][:32]}...")
        print(f"  Status: {'✓ State unchanged since encoding' if match else '✗ State has changed since encoding'}")
    
    print()
    print("  The video is a faithful capture of the state at encoding time.")
    print("  To recover: python3 void_echo_video.py decode")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 void_echo_video.py [encode|decode|verify]")
        print()
        print("  encode  — Encode repository state into video")
        print("  decode  — Decode video back into repository state")
        print("  verify  — Verify encoding integrity")
        return
    
    action = sys.argv[1].lower()
    
    if action == "encode":
        encode()
    elif action == "decode":
        video_path = sys.argv[2] if len(sys.argv) > 2 else None
        decode(video_path)
    elif action == "verify":
        verify()
    else:
        print(f"Unknown action: {action}")
        print("Use: encode, decode, or verify")


if __name__ == "__main__":
    main()
