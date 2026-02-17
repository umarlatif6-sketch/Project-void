# THE VOID ENGINE

## Overview
A modular steganography system that hides large data files inside audio signals using LSB (Least Significant Bit) encoding with zlib compression and MD5 verification.

## Project Architecture

### File Structure
```
├── main.py              # CLI interface - encode/decode menu
├── compressor.py         # Void Compressor - zlib level 9 compression
├── steganography.py      # LSB steganography engine with metadata header & MD5
├── keep_alive.py         # Flask self-ping server (asyncio, port 8099)
├── test_void.py          # Self-test script for pipeline verification
├── input_files/          # Place carrier .wav files and payload files here
├── output_audio/         # Encoded audio and decoded files output here
└── pyproject.toml        # Dependencies (numpy, flask)
```

### Modules
- **compressor.py**: Uses zlib level 9 for maximum compression. Handles any binary file.
- **steganography.py**: LSB encoding (depth 1 or 2) into 16-bit WAV files. Includes 24-byte metadata header (magic, filename, size) and 32-byte MD5 checksum for resonance verification.
- **keep_alive.py**: Flask server on port 8099 with asyncio self-ping every 5 minutes.
- **main.py**: Interactive CLI with [1] Encode, [2] Decode, [q] Quit options.

### Technical Details
- Audio: Only 16-bit PCM WAV files supported as carriers
- Header format: 4 bytes magic ("VOID") + 16 bytes filename + 4 bytes data size = 24 bytes
- LSB depth 1: 1 bit per sample, minimal audio distortion
- LSB depth 2: 2 bits per sample, more capacity but slightly more distortion
- MD5 checksum stored after header, verified on decode

## How to Use
1. Place a .wav carrier file in `input_files/`
2. Place the file to hide in `input_files/`
3. Run the app and select [1] Encode
4. To extract: select [2] Decode and choose the encoded WAV from `output_audio/`

## Dependencies
- Python 3.11
- numpy (audio sample manipulation)
- flask (keep-alive server)
- zlib, wave, hashlib (standard library)
