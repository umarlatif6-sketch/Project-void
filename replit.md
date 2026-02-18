# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed to embed large data files (up to 1GB) within audio signals. It utilizes advanced techniques like LSB encoding, dual compression (zlib and lzma), ChaCha20-encrypted headers with MD5 verification, and innovative acoustic camouflage. A key feature is the "Adriana Pocket" architecture, which uses stereo phase-shift encoding to preserve audio integrity while embedding data. The project aims to provide a robust, stealthy, and high-capacity data concealment solution for secure communication and digital watermarking, with future extensibility for signal transmission (Silk Web) and sensor integration (Graphene Suit).

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID features both a Flask-based web UI and a command-line interface. The core `void_engine` handles all functionalities including compression, steganography, capacity analysis, and signal transmission.

**UI/UX Decisions:**
- **Web UI:** A dark-themed, mobile-responsive interface with dedicated tabs for various functionalities like Encode, Decode, Burst, Visualizer, Capacity, Silk Web, Files, and Harness.
- **Visualizers:** Incorporates Web Audio API-based spectrum and spectrogram modes, including a "Vocal Pocket Visualizer" for Adriana Pocket, highlighting a 432 Hz frequency and offering real-time microphone input.
- **Acoustic Feedback:** Uses "Sapphire Bubble" and "Sapphire Glow" effects for visual confirmation of signal detection and transmission.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** Operates with 16-bit PCM WAV files, utilizing a 432 Hz base frequency ("Village Standard").
- **Compression:** Employs dual zlib (level 9) and lzma (preset 9) compression, with automatic selection of the most efficient method, including memory guarding and adaptive LZMA.
- **Steganography:**
    - **LSB Encoding:** Supports LSB depth 1 and LSB depth 2.
    - **Header:** A 64-byte ChaCha20-encrypted header (containing magic, filename/ext, data size, MD5, nonce) with a "Ghost Header" for offset embedding.
    - **Noise-Floor Mask:** `apply_dither_mask()` adds microscopic pink noise for anti-forensic evasion.
    - **Fly Jitter:** An optional temporal scatter mode for anti-forensic data fragmentation and non-uniform embedding.
    - **Adriana Pocket:** Stereo encoding where the left channel carries the pure 432 Hz body, and the right channel (phase-shifted harmonic with LFO modulation) is used for LSB data embedding.
- **Signal Transmission (Silk Web):** Formats and sends signals as 432 Hz burst-encoded WAV packets (`encode_burst()` with Sapphire Masking), featuring a "Wing-Beat Pilot Tone" and a "Pre-Render Cache."
- **Capacity Analysis:** The "Resonance Meter" calculates maximum payload capacity, "Surface Tension Limit," and "Bubble Burst threshold," providing warnings for potential audio distortion.
- **Stress Testing:** "Void Stress Test" finds the "Bubble Burst" point by escalating synthetic payloads and monitoring SNR and Surface Tension.
- **File Management:** The web UI includes a file manager for downloads, deletions, and purging old output files.
- **API Endpoints:** Comprehensive API for signal handling, system status, power management, key management, acoustic decoding, and harmonic pocket scanning.
- **Plankton-Orin Harness Architecture:** A "Digital Nervous System" featuring several middleware components:
    - **PreCompletionChecklistMiddleware:** Configurable parameter boundary checks for various subsystems (Aquaponics, Flywheel, Silk Wiring, Pressure).
    - **VirtualVoidSimulator:** A sandbox execution layer for simulating actions and maintaining state history.
    - **Air Curtain Pressure Differential:** Manages internal/external pressure, air curtain velocity, and seal integrity.
    - **SilkLinkContextMiddleware:** Injects current sensor readings into agent system prompts.
    - **AquaponicsBoundaryHook:** Safety interception middleware with built-in boundary rules.
    - **LoopDetectionMiddleware:** Tracks repeated action attempts to prevent "doom loops."
    - **NitrogenLeakChaosTest:** Simulates escalating nitrogen boil events to verify safety middleware.
- **Harness Tab (Web UI):** Provides an environment state dashboard, controls for the Air Curtain, Nitrogen Leak Chaos Test panel, PreCompletion Checklist, Virtual Void Simulator, and Loop Detection alerts.
- **Adriana Protocol (Semantic Core Language - SCL):**
    - **AdrianaLexicon:** A 45-glyph ontology mapping semantic symbols to domain operations.
    - **AdrianaTranspiler:** Parses glyph-chain expressions using Subject-Condition-Action grammar, generating VirtualVoidSimulator action sequences, and providing human-readable narratives. Integrates with the Harness safety pipeline.
- **Al-Jabr Code (Root-Pattern AI Logic):**
    - **Root Manifest:** 11 trilateral roots mapped across various domains (Aquaponics, Flywheel, Silk, Pressure, System).
    - **7 Verb Patterns:** (Accelerate, Diminish, Isolate, Verify, Monitor, Restore, Transmit) applied to roots via notation (e.g., `QDR.A`).
    - **AlJabrTranspiler:** Parses root-pattern expressions, mapping them to pre-verified logic blocks and integrating with the Harness safety pipeline.

## External Dependencies
-   **Python:** 3.11
-   **numpy:** For audio sample manipulation.
-   **flask:** For the web UI server.
-   **cryptography:** For ChaCha20 header encryption.
-   **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`.