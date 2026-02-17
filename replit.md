# PROJECT VOID

## Overview
A modular steganography engine that hides massive data files (up to 1GB) inside audio signals using LSB encoding, dual compression (zlib+lzma), ChaCha20-encrypted headers, and MD5 verification. Designed for extensibility with planned modules (Silk Web, Graphene Suit).

## Project Architecture

### File Structure
```
├── app.py                     # Flask web UI server (port 5000)
├── main.py                    # CLI entry point (alternative interface)
├── test_void.py               # Self-test script for pipeline verification
├── generate_carriers.py       # Carrier WAV generator (432 Hz Village Standard)
├── templates/
│   └── index.html             # Web UI template (6 tabs: Encode, Decode, Burst, Visualizer, Capacity, Files)
├── static/
│   ├── style.css              # Dark-themed UI styles (mobile-responsive)
│   └── app.js                 # Frontend JavaScript (includes Web Audio API visualizer)
├── void_engine/               # Core engine package
│   ├── __init__.py            # Package init (v2.0)
│   ├── compressor.py          # Void-Compressor: zlib level 9 + lzma + compress_bytes()
│   ├── stega.py               # Stega Engine: LSB encoding + 64-byte encrypted header + encode_burst()
│   ├── calculator.py          # Resonance Meter: WAV capacity analysis + resonance limits
│   └── keep_alive.py          # Pulse-Wrapper: Flask self-ping every 4 min
├── input_files/               # Place carrier .wav files and payload files here
├── output_audio/              # Encoded audio and decoded files output here
└── pyproject.toml             # Dependencies (numpy, flask, cryptography)
```

### Modules
- **void_engine/compressor.py**: Dual compression using zlib (level 9) and lzma (preset 9). Automatically selects whichever yields smaller output. Tagged output (ZLIB/LZMA prefix) for correct decompression. Also has `compress_bytes()` for raw byte compression (used by Burst mode).
- **void_engine/stega.py**: LSB encoding (depth 1 or 2) into 16-bit WAV files. 64-byte ChaCha20-encrypted header containing magic, filename, data size, MD5 checksum, and nonce. Decode requires the unique Hash Key generated during encoding. Also has `encode_burst()` for Short Burst signal encoding.
- **void_engine/keep_alive.py**: Flask server on port 8099 with asyncio self-ping every 4 minutes.
- **void_engine/calculator.py**: Resonance Meter — scans WAV carriers to calculate max payload capacity at LSB depth 1 and 2, estimates resonance limit (distortion threshold), and projects compressed data capacity with zlib/lzma. Accounts for 64-byte header overhead.
- **main.py**: Interactive CLI with [1] Encode (returns Hash Key), [2] Decode (requires Hash Key), [3] Check Capacity (Resonance Meter), [q] Quit.

### Web UI Features
- **Encode Tab**: Full encode workflow with drag-drop upload, carrier/payload selection, LSB depth, Hash Key display
- **Decode Tab**: Decode with source toggle (input/output), Hash Key input, file download
- **Burst Tab**: Short Burst encoding — encode signal strings (≤10 chars) into 5-second 432 Hz clips at LSB depth 1 with 0% distortion
- **Visualizer Tab**: Web Audio API frequency spectrum analyzer with real-time FFT, 432 Hz gold-highlighted peak, play/stop controls
- **Capacity Tab**: Resonance Meter with bar charts for max capacity, resonance limits, and estimated real data capacity
- **Files Tab**: File manager for input_files/ and output_audio/ with download/delete

### Technical Details
- Village Standard: All carriers tuned to 432 Hz base frequency (not 440 Hz concert pitch)
- Audio: Only 16-bit PCM WAV files supported as carriers
- Header format (64 bytes): 4B magic ("PVOD") + 24B filename/ext + 4B data size + 16B MD5 (raw) + 16B nonce
- Header encryption: ChaCha20 with key derived from SHA-256 of passphrase
- Compression: Best-of zlib/lzma selected automatically, tagged for decompression
- LSB depth 1: 1 bit per sample, minimal audio distortion (stealth)
- LSB depth 2: 2 bits per sample, more capacity (higher throughput)
- Hash Key: 32-char hex token generated per encode, required for decode
- Short Burst: Generates fresh 5-second 432 Hz mono carrier, encodes at depth 1, zero distortion guaranteed
- Visualizer: Web Audio API with FFT size 4096, frequency range 0-2000 Hz, gold highlight on 432 Hz bin

### Planned Modules
- **Silk Web**: Trading module (future)
- **Graphene Suit**: Sensor module (future)

## How to Use
1. Place a 16-bit .wav carrier file in `input_files/`
2. Place the file to hide in `input_files/`
3. Run the app and select [1] Encode
4. **Save the Hash Key** displayed after encoding
5. To extract: select [2] Decode, choose the WAV, and enter the Hash Key

## Dependencies
- Python 3.11
- numpy (audio sample manipulation)
- flask (keep-alive server)
- cryptography (ChaCha20 header encryption)
- zlib, lzma, wave, hashlib (standard library)
