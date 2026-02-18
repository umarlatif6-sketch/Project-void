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
│   └── index.html             # Web UI template (7 tabs: Encode, Decode, Burst, Visualizer, Capacity, Silk Web, Files)
├── static/
│   ├── style.css              # Dark-themed UI styles (mobile-responsive)
│   └── app.js                 # Frontend JavaScript (includes Web Audio API visualizer)
├── void_engine/               # Core engine package
│   ├── __init__.py            # Package init (v2.0)
│   ├── compressor.py          # Void-Compressor: zlib level 9 + lzma + compress_bytes()
│   ├── stega.py               # Stega Engine: LSB encoding + 64-byte encrypted header + encode_burst()
│   ├── calculator.py          # Resonance Meter: WAV capacity analysis + resonance limits
│   ├── keep_alive.py          # Pulse-Wrapper: Flask self-ping every 4 min
│   └── silk_web.py            # Silk Web: Signal Ticker — sends signals as 432 Hz burst packets
├── input_files/               # Place carrier .wav files and payload files here
├── output_audio/              # Encoded audio and decoded files output here
└── pyproject.toml             # Dependencies (numpy, flask, cryptography)
```

### Modules
- **void_engine/compressor.py**: Dual compression using zlib (level 9) and lzma (preset 9). Automatically selects whichever yields smaller output. Tagged output (ZLIB/LZMA prefix) for correct decompression. Also has `compress_bytes()` for raw byte compression (used by Burst mode). Optimized for 1GB on Mac 2012: Memory Guard checks available RAM before loading, Adaptive LZMA skips lzma for files >100MB (use deep=True to override), Progress Pulse prints 10% increments during compression.
- **void_engine/stega.py**: LSB encoding (depth 1 or 2) into 16-bit WAV files. 64-byte ChaCha20-encrypted header containing magic, filename, data size, MD5 checksum, and nonce. Decode requires the unique Hash Key generated during encoding. Also has `encode_burst()` for Short Burst signal encoding.
- **void_engine/keep_alive.py**: Flask server on port 8099 with asyncio self-ping every 4 minutes.
- **void_engine/calculator.py**: Resonance Meter — scans WAV carriers to calculate max payload capacity at LSB depth 1 and 2, estimates resonance limit (distortion threshold), and projects compressed data capacity with zlib/lzma. Accounts for 64-byte header overhead. 432 Hz Resonance Bonus: carriers with "432Hz" or "resonate" in filename get +5% LSB1 threshold (0.30 vs 0.25). Every analysis is appended to RESONANCE_LOG.md with timestamps.
- **void_engine/silk_web.py**: Silk Web Signal Ticker — formats signals (uppercase, max 10 chars), sends them as 432 Hz burst-encoded WAV packets via encode_burst(), maintains in-memory signal history (last 50), thread-safe queue with deque+lock, auto-logs to RESONANCE_LOG.md. Auto-Pulse heartbeat thread fires HEARTBEAT signal every 30 min if idle, keeps 432 Hz resonance alive. Network health API: Resonant (signal within 35 min) / Desynced (no signal for 35+ min). API: SignalTicker.send_signal(text) → {id, signal, hash_key, output_file, ...}, SignalTicker.get_signals(limit) → safe feed (hash tails only, no full keys), SignalTicker.get_network_health() → {status, last_signal_age_seconds}.
- **main.py**: Interactive CLI with [1] Encode (returns Hash Key), [2] Decode (requires Hash Key), [3] Check Capacity (Resonance Meter), [q] Quit.

### Web UI Features
- **Encode Tab**: Full encode workflow with drag-drop upload, carrier/payload selection, LSB depth, Hash Key display
- **Decode Tab**: Decode with source toggle (input/output), Hash Key input, file download
- **Burst Tab**: Short Burst encoding — encode signal strings (≤10 chars) into 5-second 432 Hz clips at LSB depth 1 with 0% distortion
- **Visualizer Tab**: Web Audio API frequency spectrum analyzer with real-time FFT, 432 Hz gold-highlighted peak, play/stop controls, Mic Listener mode (uses phone microphone to detect 432 Hz signals in the room — gold glow border when signal detected)
- **Capacity Tab**: Resonance Meter with bar charts for max capacity, resonance limits, and estimated real data capacity
- **Silk Web Tab**: Signal Ticker — send signals (≤10 chars) through the 432 Hz network as burst packets, scrollable signal feed with timestamps and hash tails, copy Hash Key for decode
- **Files Tab**: File manager for input_files/ and output_audio/ with download/delete, Purge button to clear output_audio/ files older than 24 hours (Mac 2012 storage maintenance)

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
- Visualizer: Web Audio API with FFT size 4096, frequency range 0-2000 Hz, gold highlight on 432 Hz bin, mic listener mode with gold glow on signal detection (threshold 120/255)
- Auto-Pulse: Background heartbeat every 30 min if idle, keeps Replit session alive and 432 Hz resonance constant
- Network Health: Resonant (last signal <35 min) / Desynced (>35 min since last signal)
- Purge: Automated cleanup of output_audio/ files older than 24 hours via /api/purge

### API Endpoints — Silk Web
- `POST /api/silk/send` — Send a signal through Silk Web. Body: `{"signal": "BUY_GOLD"}`. Returns: `{success, id, signal, output_file, output_size, hash_key, timestamp}`
- `GET /api/silk/signals?limit=20` — Fetch recent signal feed (hash tails only, no full keys exposed)

### API Endpoints — System
- `GET /api/status` — System status with RAM, CPU, file counts, and network health (Resonant/Desynced)
- `POST /api/purge` — Delete output_audio/ files older than 24 hours. Returns: `{success, purged_count, freed_bytes, files}`

### Planned Modules
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
