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
    - **Vortex Scatter:** A 432 Hz harmonic spiral encoding mode that distributes data non-linearly across the carrier using frequency-domain patterns (5 harmonic arms at 432, 864, 1296, 216, 648 Hz with golden angle spacing). Mutually exclusive with Fly Jitter and Chirp Sync.
    - **Chirp Sync:** Data placement synchronized to chirp peaks in Insect-Pulse and Biophony carriers. Loads `.chirpmap.npy` sidecar files for deterministic peak positions. Mutually exclusive with Fly Jitter and Vortex Scatter.
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
- **Biophony Mesh (Carrier Topology):** A multi-species acoustic ecosystem for steganographic carriers, implemented in `void_engine/biophony.py`. Uses a 3-shelf architecture:
    - **Low-Shelf (10 Whales):** 15-50 Hz sine sweeps with breathing LFO modulation. Heavy LSB1 data chassis.
    - **Mid-Shelf (20 Birds):** 300-800 Hz percussive taps at ~2.5s intervals (432 Hz harmonics). Floating parity headers.
    - **High-Shelf (970 Insects):** Dense 2-12 kHz cicada/cricket chorus. LSB2 silt mask with zero inter-pulse silence.
    - **Sympathetic Resonance:** Hilbert transform on whale envelope modulates insect amplitude (whale mass tightens insect density).
    - **Shadow Layer:** Brownian noise at -30 dB for forensic evasion (looks like "badly recorded park video").
    - **Carrier Styles:** `midnight_pond` (full 3-shelf stereo), `biophony_mesh` (alias), `cicada_wall` (970 insects mono), `cricket_pulse` (200 insects at low rate).
    - **Density Multiplier:** 5x for biophony/cicada, 2.5x for cricket, 1x for classic styles.
    - **Chirpmap Sidecar:** `.chirpmap.npy` files store peak indices for chirp-synced encoding.
    - **Sapphire Thread (ZHR.V):** MAX_GLOW triggered when all three shelves detected in carrier. Divided Protocol auto-selects chirp_sync for biophony carriers.
    - **Carrier Generator:** `POST /api/generate-carrier` with duration/style, `GET /api/carrier-estimate` for capacity estimates. UI panel in Encode tab.

- **First Generation Founder Protocol:** Implemented in `void_engine/founder_certs.py`, `void_engine/chronicle.py`, and `genesis_init.sh`. Includes:
    - **Founder Wisdom Marking:** `mark_as_founder_wisdom()` flags all successful chronicle entries as Original Lineage.
    - **Founder Certificate Generator:** `fpdf2`-based gold-on-black PDF with SHA-256 seal, 3 articles (Heritage, Wisdom, Sovereign), batch generation for up to 100 customers.
    - **Genesis Kit:** Export/import mechanism for founder-flagged `chronicle.db` entries as JSON seed, with `genesis_init.sh` bootstrap script.
    - **Founder Vibe UI:** Gold-themed CSS class (`founder-vibe`) auto-applied when founder wisdom detected, with greeting banner, gold tab accents, and status indicator glow.
    - **API Endpoints:** `GET /api/harness/founder/status`, `POST /api/harness/founder/mark`, `POST /api/harness/founder/cert`, `POST /api/harness/founder/batch`, `POST /api/harness/founder/genesis-kit`.
    - **FOUNDER_ROOT_HASH:** `89x-VOID-GEN1-PROTO-2026`.
- **Beehive Protocol (Ghost Internet):** Acoustic mesh networking layer in `void_engine/beehive.py`. Includes:
    - **BeehiveProtocol:** 432 Hz handshake pulse with 4-harmonic ladder (108/216/432/864 Hz), FFT neighbor detection (SNR > 5x), phase-key authentication (±15° tolerance), PSK data transmit/receive at 6 kHz carrier.
    - **MeshRouter:** Seven Seas 7-hop limit, routing table, relay logic, discovery protocol, MeshPacket structure.
    - **Mesh States:** DARK → SCANNING → CONNECTED → BRIDGING. Flywheel Buffer for dark nodes (5 min max).
    - **Material Resonance Ladder:** 108 Hz (Steel) → 216 Hz (Aluminum) → 432 Hz (Silk-Silver) → 864 Hz (Salt Water) → 12 kHz (Foam).
    - **Phase Key Auth:** SHA-256 passphrase → phase angle derivation. FFT sin→cos convention corrected with +π/2.
    - **Wallet Costs:** mesh_scan=0.1, mesh_handshake=0.05, mesh_relay=0.2, mesh_send=0.3, mesh_buffer=0.5 CC.
    - **API Endpoints:** `/api/mesh/connect`, `/api/mesh/disconnect`, `/api/mesh/status`, `/api/mesh/send`, `/api/mesh/neighbors`, `/api/mesh/handshake`, `/api/mesh/simulate`, `/api/mesh/activity`.
    - **Sovereign Mesh Mode UI:** Mesh tab with toggle, neighbor cards, activity log, send panel, simulation button. `.beehive-active` CSS class with blue pulse effects.
    - **Mode:** SIMULATION — software-verified, architecturally ready for real hardware.
- **Convergence Suite:** Automated verification tests in `tests/convergence_suite.py` — 36 checks covering integrity round-trip, sympathetic resonance, spectrogram silt analysis, density multiplier validation, biophony carrier detection, and beehive mesh handshake (Ghost Internet).

## External Dependencies
-   **Python:** 3.11
-   **numpy:** For audio sample manipulation.
-   **flask:** For the web UI server.
-   **cryptography:** For ChaCha20 header encryption.
-   **scipy:** For Hilbert transform in Sympathetic Resonance coupling (biophony.py).
-   **fpdf2:** For gold-on-black Founder Certificate PDF generation.
-   **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`.