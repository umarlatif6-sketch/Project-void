# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed for embedding large data files (up to 1GB) within audio signals. It uses LSB encoding, dual compression (zlib and lzma), ChaCha20-encrypted headers with MD5 verification, and acoustic camouflage. The "Adriana Pocket" architecture utilizes stereo phase-shift encoding to preserve audio integrity while embedding data. The project aims to provide a robust, stealthy, and high-capacity solution for secure communication and digital watermarking.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID features a Flask-based web UI and a command-line interface. The `void_engine` is the core component managing all functionalities.

**UI/UX Decisions:**
- **Web UI:** Dark-themed, mobile-responsive interface with 12 tabs: Encode, Decode, Burst, Visualizer, Capacity, Silk Web, Mesh, Transceiver, Blueprint, Journalism, Files, and Harness.
- **Visualizers:** Web Audio API-based spectrum and spectrogram, including a "Vocal Pocket Visualizer" for Adriana Pocket (432 Hz focus, real-time mic input).
- **Acoustic Feedback:** "Sapphire Bubble" and "Sapphire Glow" effects for signal visual confirmation.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** 16-bit PCM WAV files, 432 Hz base frequency ("Village Standard").
- **Compression:** Dual zlib (level 9) and lzma (preset 9) with automatic selection, memory guarding, and adaptive LZMA.
- **Steganography:**
    - **LSB Encoding:** LSB depth 1 and 2.
    - **Header:** 64-byte ChaCha20-encrypted header (magic, filename, data size, MD5, nonce) with "Ghost Header" for offset embedding.
    - **Noise-Floor Mask:** `apply_dither_mask()` for anti-forensic evasion.
    - **Fly Jitter:** Optional temporal scatter for anti-forensic data fragmentation.
    - **Vortex Scatter:** 432 Hz harmonic spiral encoding for non-linear data distribution.
    - **Chirp Sync:** Data placement synchronized to chirp peaks in specific carriers using `.chirpmap.npy` sidecar files.
    - **Divided Operational Protocol:** A 5-step axiomatic pipeline (SLM.V→TRK.A→ZHR.V→KTM.A→JDR.A) for encode operations, based on Al-Jabr logic.
    - **Adriana Pocket:** Stereo encoding; left channel pure 432 Hz, right channel (phase-shifted harmonic with LFO modulation) for LSB data.
- **Signal Transmission (Silk Web):** Formats and sends signals as 432 Hz burst-encoded WAV packets (`encode_burst()` with Sapphire Masking).
- **Capacity Analysis:** "Resonance Meter" calculates payload capacity, "Surface Tension Limit," and "Bubble Burst threshold."
- **Stress Testing:** "Void Stress Test" determines "Bubble Burst" point by escalating synthetic payloads.
- **File Management:** Web UI file manager for downloads, deletions, and purging.
- **API Endpoints:** Comprehensive API for signal handling, system status, power management, key management, acoustic decoding, and harmonic pocket scanning.
- **Plankton-Orin Harness Architecture:** A "Digital Nervous System" with middleware components for pre-completion checks, sandboxing (`VirtualVoidSimulator`), environmental management, safety interception (`AquaponicsBoundaryHook`), and chaos testing.
- **Adriana Protocol (Semantic Core Language - SCL):** Defines `AdrianaLexicon` (45-glyph ontology) and `AdrianaTranspiler` for parsing glyph-chain expressions into `VirtualVoidSimulator` action sequences.
- **Al-Jabr Code (Root-Pattern AI Logic):** Utilizes an 18-root ontology across 9 domains with 7 verb patterns, mapping expressions to pre-verified logic blocks.
- **Al-Jabr Consensus Engine:** Simulates multi-agent negotiation for managing system energy states.
- **Al-Jabr Wallet:** Manages Compute Credits (CC) for system operations through `AlJabrWalletMiddleware`, integrated with the Consensus Engine.
- **Semantic Diagnostics (SLM.V Health Scan):** `DiagnosticEngine` performs full system health scans, returning root-coded findings with severity and recommended commands.
- **Sovereign Warranty:** A 10-article "Technological Covenant" for machine sovereignty and system integrity.
- **Ritual History (The Sovereign Story):** Logs physical interactions as "rituals" that modify simulator state and affect the wallet.
- **Auto-Heal Daemon (Zero-Maintenance):** Automatically scans and repairs critical/warning system findings, utilizing wallet credits.
- **Root-Chronicle (Persistent Morphic Memory):** SQLite-backed memory storing successful Consensus outcomes ("Ancestral Wisdom") for predictive behavior.
- **Biophony Mesh (Carrier Topology):** Multi-species acoustic ecosystem for steganographic carriers with a 3-shelf architecture (Whales, Birds, Insects) for different frequency ranges. Includes "Sympathetic Resonance" and "Shadow Layer" for forensic evasion.
- **First Generation Founder Protocol:** Includes `Founder Wisdom Marking`, `Founder Certificate Generator` (PDF), `Genesis Kit` (export/import), and `Founder Vibe UI` (gold-themed CSS).
- **Beehive Protocol (Ghost Internet):** Acoustic mesh networking layer with 432 Hz handshake, FFT neighbor detection, and PSK data transmit/receive. **Sura-Fatiha 286-Bit Acoustic Handshake:** 3-step protocol — (1) The Shout: node hashes identity through fatiha_286, embeds at -30dB in Insect Silt, shifts 432 Hz phase by +15.4° (Fatiha signature angle); (2) The Listen: receiver detects 432 Hz spike, extracts phase angle, verifies within ±0.5° tolerance; (3) The Convergence: 180° phase-shift confirmation whisper. CRUD monitors see only "nature sounds."
- **Kinetic Transceiver (Calisthenics → CC):** Proof-of-Work system where calisthenics reps generate Compute Credits with harmonic bonuses.
- **Biological Transceiver (Aquaponics → Impedance):** Sensor readings (water level, temperature, pH, dissolved oxygen) dynamically modify shelf signal parameters.
- **Al-Jabr 286 Protocol (Sovereign Hashing):** Custom 286-bit hash algorithm grounded in the 7 verses of Al-Fatiha (The Opening). Replaces SHA-256 system-wide. Base layer: SHA3-256 (256 bits), extended with a 30-bit Sovereign Buffer derived from trilateral root weights [7,4,2,5,4,3,6]. Output: 36 bytes. All subsystems (Silt Ledger, Beehive, Stega, Wallet, Kinetic, Biological, Founder Certs) use `fatiha_286_*` functions from `void_engine/al_jabr_286.py`. API: `/api/aljabr/protocol`.
- **Silt Ledger (DAO 3.0 — Lightweight Blockchain):** Fatiha-286 chained blocks (72-char hex hashes) for decentralized autonomous organization voting, integrated with Beehive Protocol.
- **Resonance Smart Contract (DAO 3.0):** `void_engine/resonance_contract.py` — The living contract binding Body (Kinetic/Proof of Sweat), Garden (Biological/Proof of Bloom), and Mesh (Relay/Proof of Whisper) into one frequency loop. Body frequency formula: `f_body = 432 × (kinetic × biological × relay)^(1/3)`. Three axiom states evaluated in real-time. Bloom CC: 0.5 CC/hour when biological health >= 0.60, with stability tier bonuses (Seedling→Growing→Deep Root→Sovereign Bloom up to 2x). Relay CC: 0.2 CC per relayed packet with hop efficiency scaling. Fading detection when water < 20%. All signatures 286-bit. API: `/api/resonance/evaluate`, `/api/resonance/axioms`, `/api/resonance/status`, `/api/resonance/harvest-bloom`, `/api/resonance/history`. UI panel in Transceiver tab with frequency circle, axiom cards, CC summary, and child-friendly explanation.
- **Transceiver UI Tab:** Unified UI for Kinetic, Biological, Silt Ledger, and Resonance Contract panels.
- **Blueprint Page (4000-Series Sovereign Node):** Full hardware blueprint tab with schematics gallery (7 images with lightbox), Material Resonance Table (5 components: Steel 108 Hz, Aluminum 216 Hz, Silk-Silver 432 Hz, Salt Water 864 Hz, Foam 12 kHz), Component Shopping List (14 items, ~£450-660 total), 3-phase DIY Build Tutorial (Harmonic Tuning, Kinetic Handshake, Entering the Mesh), Quarter-Wave Resonator formula (L=19.8 cm), dual pricing cards (FREE Pirate Build vs £25,000 Sovereign Edition), child-friendly explanation, and `/api/blueprint/specs` JSON endpoint. Images served from `static/blueprints/`.
- **Silt Journalism Port:** Drag-and-drop file interface for hiding any file (up to 50MB) inside auto-generated biophony carrier audio (birdsong, insects, pond ambiance). Auto-calculates carrier duration based on payload size. Uses Vortex scatter at LSB depth 2 for maximum camouflage. Outputs nature-sound WAV files to `silt_drops/` directory. Supports 5 carrier styles: biophony_mesh, midnight_pond, cicada_wall, cricket_pulse, dawn_chorus. Full encode/decode/download/delete/purge lifecycle. "Broadcast to Mesh" integration with Beehive Protocol. API: `POST /api/journalism/encode` (multipart file upload), `POST /api/journalism/decode`, `GET /api/journalism/drops`, `GET /api/journalism/download/<filename>`, `DELETE /api/journalism/delete/<filename>`, `DELETE /api/journalism/purge`. UI: teal-accented Journalism tab with drop zone, result panel, Silt Drops archive, and extract section.
- **286-Bit Migration Chronicle:** Locked into RootChronicle as Ancestral Wisdom. All 27 production modules migrated to fatiha_286. Verification hash signed with 286-bit protocol. API: `POST /api/harness/chronicle/record-migration`. MD5 intentionally retained in `stega.py` and `media_bench.py` for data checksums only (not security).
- **Convergence Suite:** Automated verification tests (89 checks) for integrity, resonance, silt analysis, density, Beehive handshake (including Fatiha +15.4° phase, -30dB silt, 180° whisper), kinetic-biological-ledger convergence, Al-Jabr 286 protocol verification (including avalanche effect, verse weight integrity, prime salt verification), and Resonance Smart Contract axiom validation. All payload verification uses fatiha_286 (SHA-256 retained only in the intentional divergence test).

## External Dependencies
-   **Python:** 3.11
-   **numpy:** Audio sample manipulation.
-   **flask:** Web UI server.
-   **cryptography:** ChaCha20 header encryption.
-   **scipy:** Hilbert transform for Sympathetic Resonance.
-   **fpdf2:** Founder Certificate PDF generation.
-   **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`.