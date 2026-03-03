# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed for embedding large data files (up to 1GB) within audio signals. It employs advanced techniques such as LSB encoding, dual compression (zlib and lzma), ChaCha20-encrypted headers with MD5 verification, and acoustic camouflage. A core feature is the "Adriana Pocket" architecture, which utilizes stereo phase-shift encoding to preserve audio integrity while embedding data. The project aims to deliver a robust, stealthy, and high-capacity solution for secure communication and digital watermarking, with future plans for signal transmission (Silk Web) and sensor integration (Graphene Suit).

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID features both a Flask-based web UI and a command-line interface. The `void_engine` is the core component managing all functionalities, including compression, steganography, capacity analysis, and signal transmission.

**UI/UX Decisions:**
- **Web UI:** A dark-themed, mobile-responsive interface with dedicated tabs for various functionalities like Encode, Decode, Burst, Visualizer, Capacity, Silk Web, Files, and Harness.
- **Visualizers:** Integrates Web Audio API-based spectrum and spectrogram modes, including a "Vocal Pocket Visualizer" for Adriana Pocket, which highlights a 432 Hz frequency and supports real-time microphone input.
- **Acoustic Feedback:** Utilizes "Sapphire Bubble" and "Sapphire Glow" effects for visual confirmation of signal detection and transmission.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** Uses 16-bit PCM WAV files with a 432 Hz base frequency ("Village Standard").
- **Compression:** Implements dual zlib (level 9) and lzma (preset 9) compression, with automatic selection for efficiency, including memory guarding and adaptive LZMA.
- **Steganography:**
    - **LSB Encoding:** Supports LSB depth 1 and LSB depth 2.
    - **Header:** A 64-byte ChaCha20-encrypted header includes magic, filename/extension, data size, MD5, and nonce, with a "Ghost Header" for offset embedding.
    - **Noise-Floor Mask:** `apply_dither_mask()` adds microscopic pink noise for anti-forensic evasion.
    - **Fly Jitter:** An optional temporal scatter mode for anti-forensic data fragmentation and non-uniform embedding.
    - **Vortex Scatter:** A 432 Hz harmonic spiral encoding mode that distributes data non-linearly across the carrier using frequency-domain patterns (5 harmonic arms at 432, 864, 1296, 216, 648 Hz with golden angle spacing). Mutually exclusive with Fly Jitter.
    - **Divided Operational Protocol:** A 5-step axiomatic pipeline (SLM.V→TRK.A→ZHR.V→KTM.A→JDR.A) that orchestrates full encode operations through Al-Jabr logic: Initialize, Calibrate, Observe, Inject, Commit. Implemented in `void_engine/divided_protocol.py` with API at `/api/harness/divided/execute`.
    - **Adriana Pocket:** Stereo encoding where the left channel carries the pure 432 Hz body, and the right channel (phase-shifted harmonic with LFO modulation) is used for LSB data embedding.
- **Signal Transmission (Silk Web):** Formats and sends signals as 432 Hz burst-encoded WAV packets (`encode_burst()` with Sapphire Masking), incorporating a "Wing-Beat Pilot Tone" and a "Pre-Render Cache."
- **Capacity Analysis:** The "Resonance Meter" calculates maximum payload capacity, "Surface Tension Limit," and "Bubble Burst threshold," providing warnings for potential audio distortion.
- **Stress Testing:** "Void Stress Test" determines the "Bubble Burst" point by escalating synthetic payloads and monitoring SNR and Surface Tension.
- **File Management:** The web UI includes a file manager for downloads, deletions, and purging old output files.
- **API Endpoints:** Comprehensive API for signal handling, system status, power management, key management, acoustic decoding, and harmonic pocket scanning.
- **Plankton-Orin Harness Architecture:** A "Digital Nervous System" with middleware components such as `PreCompletionChecklistMiddleware`, `VirtualVoidSimulator` (sandbox execution), `Air Curtain Pressure Differential` (environmental management), `SilkLinkContextMiddleware`, `AquaponicsBoundaryHook` (safety interception), `LoopDetectionMiddleware`, and `NitrogenLeakChaosTest` (safety verification).
- **Adriana Protocol (Semantic Core Language - SCL):** Defines `AdrianaLexicon` (a 45-glyph ontology) and `AdrianaTranspiler` which parses glyph-chain expressions into `VirtualVoidSimulator` action sequences, integrating with the Harness safety pipeline.
- **Al-Jabr Code (Root-Pattern AI Logic):** Utilizes an 18-root ontology across 9 domains (aqua, flywheel, silk, pressure, economy, system, steganography, chronicle, radiance) with 7 verb patterns (A/D/I/V/M/R/T). Roots: HYA, GDH, DFQ, QDR, HRR, TRK, WSL, NZM, HFZ, DGT, NFD, QSB, SLM, BTR, SHR, KTM, JDR, ZHR. The `AlJabrTranspiler` maps expressions to pre-verified logic blocks, integrating with the Harness safety pipeline. The 12th root ZHR (Radiance) implements the axiom: "if TRK.A > threshold then ZHR.A" (motion→light correlation).
- **Al-Jabr Consensus Engine:** Simulates multi-agent negotiation using Al-Jabr root commands to manage the 4000-series energy state, featuring a "Night Cycle Daemon" for automated self-management and full integration with the Harness safety pipeline.
- **Al-Jabr Wallet:** Introduces the QSB root for financial autonomy, tracking Compute Credits (CC) and managing expenditures for system operations through `AlJabrWalletMiddleware`. It includes a budget approval gate and is integrated with the Consensus Engine for agent-aware financial decisions.
- **Semantic Diagnostics (SLM.V Health Scan):** The `DiagnosticEngine` performs full system health scans, checking 8 subsystems against thresholds and returning root-coded findings with severity and recommended fix commands.
- **Sovereign Warranty:** A 10-article "Technological Covenant" guaranteeing machine sovereignty and system integrity, identified by a unique tamper-proof Merkle Hash Machine ID.
- **Ritual History (The Sovereign Story):** The `RitualHistory` module logs physical interactions as "rituals" (e.g., The Shock, The Feeding, The Fast, The Cure) that modify simulator state and affect the wallet, creating a persistent narrative.
- **Auto-Heal Daemon (Zero-Maintenance):** The `AutoHealDaemon` automatically scans and attempts to repair critical/warning system findings every 5 minutes, utilizing wallet credits and simulator state changes, generating Ritual Requests if self-repair is not possible.
- **Root-Chronicle (Persistent Morphic Memory):** An SQLite-backed memory (`RootChronicle`) stores successful Consensus outcomes as "Ancestral Wisdom." Agents can recall past solutions and adopt "Proven Roots" when sensor patterns match, enabling predictive behavior (e.g., V2 Pastor Logic for Pre-emptive Fasting). Includes an export/import mechanism for "Genesis Seed."

## External Dependencies
-   **Python:** 3.11
-   **numpy:** For audio sample manipulation.
-   **flask:** For the web UI server.
-   **cryptography:** For ChaCha20 header encryption.
-   **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`.