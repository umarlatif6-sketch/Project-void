# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed to embed large data files (up to 1GB) within audio signals. It employs advanced techniques such as LSB encoding, dual compression (zlib and lzma), ChaCha20-encrypted headers with MD5 verification, and innovative acoustic camouflage methods. The project introduces the "Adriana Pocket" architecture, utilizing stereo phase-shift encoding to preserve audio integrity while embedding data in harmonic frequency pockets. This engine is built for extensibility, with a vision to integrate future modules like Silk Web for signal transmission and Graphene Suit for sensor integration. The business vision is to provide a robust, stealthy, and high-capacity data concealment solution with potential applications in secure communication and digital watermarking.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID features a Flask-based web UI and a CLI for interaction. The core `void_engine` package handles compression, steganography, capacity analysis, and signal transmission.

**UI/UX Decisions:**
- **Web UI:** Dark-themed, mobile-responsive interface with seven dedicated tabs: Encode, Decode, Burst, Visualizer, Capacity, Silk Web, and Files.
- **Visualizers:** Features Web Audio API-based spectrum and spectrogram modes, including a "Vocal Pocket Visualizer" for Adriana Pocket, with specific highlights for 432 Hz frequency and real-time mic listener capabilities.
- **Acoustic Feedback:** Utilizes "Sapphire Bubble" and "Sapphire Glow" effects for visual confirmation of signal detection and transmission.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** All carriers are tuned to a 432 Hz base frequency (Village Standard). Supports only 16-bit PCM WAV files as carriers.
- **Compression:** Dual zlib (level 9) and lzma (preset 9) compression, automatically selecting the more efficient method. Includes memory guarding and adaptive LZMA.
- **Steganography:**
    - **LSB Encoding:** Supports LSB depth 1 (minimal distortion) and LSB depth 2 (higher capacity).
    - **Header:** 64-byte ChaCha20-encrypted header (magic, filename/ext, data size, MD5, nonce) with a "Ghost Header" (floating offset) to avoid detection at sample 0.
    - **Noise-Floor Mask:** `apply_dither_mask()` adds microscopic pink noise for forensic steganalysis evasion.
    - **Fly Jitter:** Optional temporal scatter mode that fragments and embeds data chunks at non-uniform positions for anti-forensic purposes.
    - **Adriana Pocket:** Stereo encoding where the left channel carries the pure 432 Hz body, and the right channel (phase-shifted harmonic channel with LFO modulation) is used for LSB data embedding.
- **Signal Transmission (Silk Web):** Formats and sends signals as 432 Hz burst-encoded WAV packets (`encode_burst()` with Sapphire Masking). Features a "Wing-Beat Pilot Tone" for acoustic wake-up and a "Pre-Render Cache" for efficiency. Includes network health monitoring.
- **Capacity Analysis:** "Resonance Meter" calculates max payload capacity, "Surface Tension Limit," and "Bubble Burst threshold," providing warnings for potential audio distortion.
- **Stress Testing:** "Void Stress Test" automatically finds the "Bubble Burst" point by escalating synthetic payloads and monitoring SNR and Surface Tension.
- **File Management:** Web UI includes a file manager with download/delete and a purge function for old output files.
- **API Endpoints:** Comprehensive API for signal sending, system status, low-power mode control, default key management, acoustic decoding, and harmonic pocket scanning (`POST /api/pockets`). Encode/decode endpoints auto-detect stereo carriers and route to Adriana Pocket functions.
- **Vocal Pocket Visualizer:** Third visualizer mode showing pulsing radial 432 Hz breath cycle with 8 orbiting pocket indicators (sapphire orbs) that open/close with the breath phase. States: POCKET OPEN / POCKET SEALED / TRANSITIONING.
- **Stress Test Results (Stereo):** 60s stereo carrier at LSB1 holds ~330KB. 100KB: 31% tension, 31.1 dB SNR (Clear). 250KB: 77.4% tension, 31.1 dB SNR (Clear). All verified with MD5 round-trip.

## External Dependencies
-   **Python:** 3.11
-   **numpy:** For audio sample manipulation.
-   **flask:** For the web UI server and keep-alive functionality.
-   **cryptography:** For ChaCha20 header encryption.
-   **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib` are utilized for compression, WAV file handling, and hashing.