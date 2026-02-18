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
- **void_engine/media_bench.py**: Deep Sea Stress Test — full pipeline benchmark with 7 phases: streaming compression competition (ZLIB vs LZMA with 8MB chunk cooling for >50MB files), Ghost Header wrap, carrier loading/generation, Plankton fragmentation log (per-fragment offset/size/gap/depth), Sapphire WAV encode, FFT resonance purity analysis (432 Hz SNR), and decode verification. Supports existing carrier override, synthetic Ocean Payload generator (--ocean flag), and auto-appends full results with Plankton Map to RESONANCE_LOG.md. Surface tension = total_payload / effective_capacity (accounting for ghost offset and LSB depth).
- **void_engine/compressor.py**: Dual compression using zlib (level 9) and lzma (preset 9). Automatically selects whichever yields smaller output. Tagged output (ZLIB/LZMA prefix) for correct decompression. Also has `compress_bytes()` for raw byte compression (used by Burst mode). Optimized for 1GB on Mac 2012: Memory Guard checks available RAM before loading, Adaptive LZMA skips lzma for files >100MB (use deep=True to override), Progress Pulse prints 10% increments during compression.
- **void_engine/stega.py**: LSB encoding (depth 1 or 2) into 16-bit WAV files. 64-byte ChaCha20-encrypted header with Ghost Header (Floating Offset derived from Hash Key — header is not at sample 0). `apply_dither_mask()` adds microscopic pink noise before LSB encoding (Noise-Floor Mask) making digital data indistinguishable from analog warmth. Decode requires the unique Hash Key generated during encoding. Also has `encode_burst()` for Short Burst signal encoding with Sapphire Masking — Harmonic Shimmer LFO modulates base frequency between 430-434 Hz at 0.25 Hz rate using phase accumulation for acoustic camouflage. `check_resonance_purity()` performs FFT-based SNR analysis with quality grades (Clear/Acceptable/Muddled). Fly Jitter: optional temporal scatter mode — breaks payload into 7-20 irregular chunks (Dirichlet distribution) and embeds them at non-uniform positions across the carrier with variable gaps, making data appear/disappear like a fly. Jitter flag stored in bit 31 of data_size field. Auto-fallback to sequential if carrier >80% full.
- **void_engine/keep_alive.py**: Flask server on port 8099 with asyncio self-ping every 4 minutes.
- **void_engine/calculator.py**: Resonance Meter with Acoustic Surface Tension model — scans WAV carriers to calculate max payload capacity at LSB depth 1 and 2, Surface Tension Limit (max data before distortion), and Bubble Burst threshold (90% of membrane — distortion risk zone). Projects compressed data capacity with zlib/lzma. 432 Hz Resonance Bonus: carriers with "432Hz" or "resonate" in filename get +5% LSB1 threshold (0.30 vs 0.25). Bubble analogy: below surface tension = bubble holds (clean audio), near burst = membrane stretching, above burst = bubble pops (audible artifacts). Every analysis appended to RESONANCE_LOG.md.
- **void_engine/silk_web.py**: Silk Web Signal Ticker — formats signals (uppercase, max 10 chars), sends them as 432 Hz burst-encoded WAV packets via encode_burst(), maintains in-memory signal history (last 50), thread-safe queue with deque+lock, auto-logs to RESONANCE_LOG.md. Auto-Pulse heartbeat thread fires HEARTBEAT signal every 30 min if idle, keeps 432 Hz resonance alive. Network health API: Resonant (signal within 35 min) / Desynced (no signal for 35+ min). API: SignalTicker.send_signal(text) → {id, signal, hash_key, output_file, ...}, SignalTicker.get_signals(limit) → safe feed (hash tails only, no full keys), SignalTicker.get_network_health() → {status, last_signal_age_seconds}.
- **main.py**: Interactive CLI with [1] Encode (returns Hash Key), [2] Decode (requires Hash Key), [3] Check Capacity (Resonance Meter), [q] Quit.

### Web UI Features
- **Encode Tab**: Full encode workflow with drag-drop upload, carrier/payload selection, LSB depth, Fly Jitter toggle, Hash Key display
- **Decode Tab**: Decode with source toggle (input/output), Hash Key input, file download
- **Burst Tab**: Short Burst encoding — encode signal strings (≤10 chars) into 5-second 432 Hz clips at LSB depth 1 with 0% distortion
- **Visualizer Tab**: Web Audio API with Spectrum and Spectrogram modes. Spectrum: real-time FFT bar chart with 432 Hz gold peak. Spectrogram: scrolling frequency-over-time waterfall display with glowing sapphire thread at 432 Hz confirming the Moat is active. Toggle between modes. Mic Listener mode for live signal detection with gold glow border
- **Capacity Tab**: Resonance Meter with Surface Tension / Bubble Burst bar charts showing max capacity, membrane limits (90% burst threshold), and estimated real data capacity
- **Silk Web Tab**: Signal Ticker with Sonar Listener — send signals (≤10 chars) through 432 Hz network as Sapphire Bubbles, Acoustic Lock-on listener (FFT 8192, precise bin math, 0.5s sustained threshold), Village Default Key for auto-decode, scrollable signal feed, Sapphire Glow animation on successful send/catch. Sonar ring visualizes listener state (scanning → locking → bubble caught)
- **Files Tab**: File manager for input_files/ and output_audio/ with download/delete, Purge button to clear output_audio/ files older than 24 hours (Mac 2012 storage maintenance)

### Technical Details
- Village Standard: All carriers tuned to 432 Hz base frequency (not 440 Hz concert pitch)
- Audio: Only 16-bit PCM WAV files supported as carriers
- Header format (64 bytes): 4B magic ("PVOD") + 24B filename/ext + 4B data size (bit 31 = jitter flag) + 16B MD5 (raw) + 16B nonce
- Header encryption: ChaCha20 with key derived from SHA-256 of passphrase
- Compression: Best-of zlib/lzma selected automatically, tagged for decompression
- LSB depth 1: 1 bit per sample, minimal audio distortion (stealth)
- LSB depth 2: 2 bits per sample, more capacity (higher throughput)
- Hash Key: 32-char hex token generated per encode, required for decode
- Noise-Floor Mask: apply_dither_mask() adds pink noise (1/f spectral density) to carrier before LSB embedding — makes digital data look like natural analog warmth, defeats forensic steganalysis
- Ghost Header: 64-byte encrypted header placed at Floating Offset (derived from SHA-256 of "ghost:" + passphrase, mod total_samples/4) — sniffers see solid audio, no header at position 0
- Fly Jitter: Temporal scatter anti-forensic mode. Payload data (after header) broken into 7-20 irregular chunks using Dirichlet distribution (PRNG seeded from SHA-256 of "jitter:" + passphrase). Chunks placed at non-uniform positions across carrier with variable gaps (hundreds to tens of thousands of samples). Header always sequential at ghost offset; only data is scattered. Jitter flag = bit 31 of data_size in header. Auto-fallback: if carrier >80% full, reverts to sequential (not enough room for meaningful gaps). Decoder regenerates identical jitter map from passphrase. Web UI: "Fly Jitter" checkbox on Encode tab.
- Short Burst: Generates 5.5-second audio (0.5s Pilot Tone + 5s 432 Hz body with Harmonic Shimmer), encodes at depth 1, Sapphire Masking camouflage
- Wing-Beat Pilot Tone: 0.5s dual-frequency preamble (432 Hz + 864 Hz harmonic) prepended to every burst — acts as acoustic wake-up call for phone mic detection. 60/30% mix with 10ms fade in/out.
- Pre-Render Cache: Carrier waveforms (pilot tone, 5s burst body) cached in memory after first generation — subsequent encode_burst() calls skip waveform calculation entirely. Saves CPU during 18-hour window.
- Sapphire Bubble Effect: When mic listener detects sustained Pilot Tone (432+864 Hz for 400ms), entire screen transitions from Dark Void to shimmering Sapphire Bubble — radial gradient overlay with shimmer animation, blue-glowing visualizer border. Confirms Fly is caught.
- Spectrogram Mode: Visualizer toggle shows frequency-over-time waterfall with scrolling pixel columns, glowing sapphire thread at 432 Hz confirms Void is secure
- Acoustic Lock-on: FFT size 8192 for high precision, target bin = 432 * (FFT_SIZE / SampleRate), 0.5s sustained dual-threshold (432 Hz ≥100, 864 Hz harmonic ≥40) before triggering 6-second capture
- Visualizer Pilot Detection: FFT 4096, 432 Hz ≥100 + 864 Hz ≥50, 400ms sustained before Sapphire Bubble activates
- Sapphire Glow: Translucent blue gradient pulse animation on Silk Web panel when signal successfully sent or acoustically caught
- Bubble Burst Warning: Encode response includes bubble_status (safe/stretch/burst) and bubble_warning message based on Surface Tension analysis
- Low-Power Resonance Mode: Toggle in header disables LZMA compression during encoding, maintains heartbeat and ticker
- Village Default Key: Persistent hash key for auto-decode of acoustically captured signals via /api/decode/audio
- Visualizer: Web Audio API with FFT size 4096, frequency range 0-2000 Hz, gold highlight on 432 Hz bin, mic listener mode with gold glow on signal detection (threshold 120/255)
- Auto-Pulse: Background heartbeat every 30 min if idle, keeps Replit session alive and 432 Hz resonance constant
- Network Health: Resonant (last signal <35 min) / Desynced (>35 min since last signal)
- Purge: Automated cleanup of output_audio/ files older than 24 hours via /api/purge

### API Endpoints — Silk Web
- `POST /api/silk/send` — Send a signal through Silk Web. Body: `{"signal": "BUY_GOLD"}`. Returns: `{success, id, signal, output_file, output_size, hash_key, timestamp}`
- `GET /api/silk/signals?limit=20` — Fetch recent signal feed (hash tails only, no full keys exposed)

### API Endpoints — System
- `GET /api/status` — System status with RAM, CPU, file counts, network health, and low_power flag
- `POST /api/purge` — Delete output_audio/ files older than 24 hours. Returns: `{success, purged_count, freed_bytes, files}`
- `POST /api/low-power` — Toggle Low-Power Resonance mode. Body: `{"enabled": true/false}`
- `GET /api/low-power` — Get current low-power mode state
- `POST /api/settings/default-key` — Set/clear Village Default Key. Body: `{"key": "..."}`
- `GET /api/settings/default-key` — Check if default key is set
- `POST /api/decode/audio` — Acoustic decode: upload captured audio (WAV/WebM), optional hash_key, returns decoded signal with purity analysis (SNR, quality grade)

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
