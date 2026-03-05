# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed for embedding large data files (up to 1GB) within audio signals. It utilizes LSB encoding, dual compression (zlib and lzma), ChaCha20-encrypted headers with MD5 verification, and acoustic camouflage techniques. The "Adriana Pocket" architecture employs stereo phase-shift encoding to preserve audio integrity while embedding data. The project aims to deliver a robust, stealthy, and high-capacity solution for secure communication and digital watermarking, envisioning a future where digital interactions are secure, private, and resilient against surveillance.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID is built around a Flask-based web UI and a command-line interface, with the `void_engine` acting as the core component for all functionalities.

**UI/UX Decisions:**
- **Web UI:** A dark-themed, mobile-responsive interface featuring 12 interactive tabs: Encode, Decode, Burst, Visualizer, Capacity, Silk Web, Mesh, Transceiver, Blueprint, Journalism, Files, and Harness.
- **Visualizers:** Integrates Web Audio API-based spectrum and spectrograms, including a "Vocal Pocket Visualizer" specifically for Adriana Pocket, focusing on 432 Hz frequencies with real-time microphone input.
- **Acoustic Feedback:** Incorporates "Sapphire Bubble" and "Sapphire Glow" effects for visual confirmation of signal processing.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** Uses 16-bit PCM WAV files with a 432 Hz base frequency ("Village Standard").
- **Compression:** Implements dual compression using zlib (level 9) and lzma (preset 9), with automatic selection, memory guarding, and adaptive LZMA.
- **Steganography Core:**
    - **LSB Encoding:** Supports LSB depth 1 and 2.
    - **Header:** Employs a 64-byte ChaCha20-encrypted header (magic, filename, data size, MD5, nonce) with a "Ghost Header" for offset embedding and `apply_dither_mask()` for anti-forensic evasion.
    - **Advanced Techniques:** Features "Fly Jitter" for temporal data scatter, "Vortex Scatter" for 432 Hz harmonic spiral encoding, and "Chirp Sync" for data placement synchronized to chirp peaks.
    - **Adriana Pocket:** Utilizes stereo encoding where the left channel carries pure 432 Hz and the right channel, phase-shifted and LFO modulated, carries LSB data.
- **Divided Operational Protocol:** A 5-step axiomatic pipeline (SLM.V→TRK.A→ZHR.V→KTM.A→JDR.A) based on Al-Jabr logic for encoding operations.
- **Signal Transmission (Silk Web):** Formats and sends signals as 432 Hz burst-encoded WAV packets using "Sapphire Masking."
- **Capacity Analysis:** "Resonance Meter" calculates payload capacity, "Surface Tension Limit," and "Bubble Burst threshold."
- **Plankton-Orin Harness Architecture:** A "Digital Nervous System" with middleware components for pre-completion checks, sandboxing (`VirtualVoidSimulator`), environmental management, safety interception (`AquaponicsBoundaryHook`), and chaos testing.
- **Adriana Protocol (Semantic Core Language - SCL):** Defines `AdrianaLexicon` (45-glyph ontology) and `AdrianaTranspiler` for parsing glyph-chain expressions into `VirtualVoidSimulator` action sequences.
- **Al-Jabr Code (Root-Pattern AI Logic):** Utilizes an 18-root ontology across 9 domains with 7 verb patterns, mapping expressions to pre-verified logic blocks. The **Al-Jabr Consensus Engine** simulates multi-agent negotiation for system energy states, managed by an **Al-Jabr Wallet** for Compute Credits.
- **Semantic Diagnostics (SLM.V Health Scan):** `DiagnosticEngine` performs full system health scans, providing root-coded findings with severity and recommended commands.
- **Sovereign Warranty:** A 10-article "Technological Covenant" for machine sovereignty and system integrity, complemented by an **Auto-Heal Daemon** for automated system repair.
- **Root-Chronicle (Persistent Morphic Memory):** An SQLite-backed memory storing successful Consensus outcomes for predictive behavior.
- **Biophony Mesh (Carrier Topology):** A multi-species acoustic ecosystem for steganographic carriers with a 3-shelf architecture (Whales, Birds, Insects), incorporating "Sympathetic Resonance" and "Shadow Layer" for forensic evasion.
- **Beehive Protocol (Ghost Internet):** An acoustic mesh networking layer featuring a 432 Hz handshake, FFT neighbor detection, and PSK data transmission. The **Sura-Fatiha 286-Bit Acoustic Handshake** is a 3-step protocol for node authentication.
- **Kinetic Transceiver (Calisthenics → CC):** A Proof-of-Work system where calisthenics repetitions generate Compute Credits with harmonic bonuses.
- **Biological Transceiver (Aquaponics → Impedance):** Sensor readings (water level, temperature, pH, dissolved oxygen) dynamically modify shelf signal parameters.
- **Al-Jabr 286 Protocol (Sovereign Hashing):** A custom 286-bit hash algorithm based on the 7 verses of Al-Fatiha, replacing SHA-256 system-wide.
- **Silt Ledger (DAO 3.0 — Lightweight Blockchain):** Fatiha-286 chained blocks for decentralized autonomous organization voting, integrated with the Beehive Protocol.
- **Resonance Smart Contract (DAO 3.0):** A living contract binding Body (Kinetic/Proof of Sweat), Garden (Biological/Proof of Bloom), and Mesh (Relay/Proof of Whisper) into a single frequency loop.
- **Blueprint Page (4000-Series Sovereign Node):** Provides full hardware blueprints, schematics, material resonance tables, component shopping lists, and a 3-phase DIY build tutorial.
- **Silt Journalism Port:** A drag-and-drop interface for hiding files (up to 50MB) within auto-generated biophony carrier audio, utilizing Vortex scatter for camouflage.
- **Financial Pathway Pages:** Includes a marketing **Landing Page**, a **Demo Mode**, a **Grant Application Package** page, and a **Sovereign Edition Product Page** for commercialization.
- **Technical Brief PDF Generator:** Generates a professional 2-page PDF covering project details.
- **Inquiry System:** A simple JSON-file-based system for storing inquiries.

## External Dependencies
- **Python:** 3.11
- **numpy:** Used for audio sample manipulation and FFT operations.
- **flask:** Provides the web UI server.
- **cryptography:** Utilized for ChaCha20 header encryption.
- **fpdf2:** Employed for generating Founder Certificate PDFs.
- **werkzeug:** Handles secure filename operations.
- **Standard Library:** Includes `zlib`, `lzma`, `wave`, `hashlib` for core functionalities.