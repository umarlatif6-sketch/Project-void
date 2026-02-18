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
    - **Compression Results:** HFZ bare root = 89.33x (3 chars → 5 actions). QDR.A = 7.8x. HFZ>SLM.V = 77.67x (9 chars → 13 actions).
    - **API Endpoints:** `GET /api/harness/aljabr/roots`, `POST /api/harness/aljabr/transpile`, `POST /api/harness/aljabr/execute`
- **Al-Jabr Consensus Engine (Multi-Agent Root-Exchange Protocol):**
    - **ConsensusEngine** (`void_engine/consensus.py`): Simulates two Plankton EA agents — Agent A (The Guardian, priorities: HFZ/SLM preservation) and Agent B (The Growth-Seeker, priorities: HYA/GDH biological growth) — negotiating the 4000-series energy state using only Al-Jabr root commands.
    - **Root-Exchange Trace:** Turn-based negotiation where agents evaluate machine state, issue root commands based on their drive profiles, counter each other's positions, and converge on a consensus SLM path. Full audit trail in compressed root notation.
    - **State-Aware Assessment:** Guardian thresholds (energy <50% triggers QDR.D>HFZ, temperature >50°C triggers HRR.D, pressure >1.2 atm triggers DGT.D). Growth thresholds (oxygen <6 ppm triggers HYA.D|GDH.A, ammonia >0.5 triggers DFQ.A>GDH.V, pH out of range triggers GDH.V>HYA.M).
    - **Night Cycle Daemon:** Automated mode that runs consensus on configurable interval (default 5 min). Gives the 4000-series self-management capability — "fasting and feeding" cycles using pure root logic while operator is away.
    - **Safety Integration:** Consensus commands execute through full Harness safety pipeline (BoundaryHook → LoopDetector → PreCompletionChecklist).
    - **Harness Tab UI:** Green-themed Consensus section with Run Consensus button, Night Cycle toggle, Root-Exchange trace table (agent positions, commands, intents), Consensus Command display, and execution results.
    - **API Endpoints:** `POST /api/harness/consensus/run`, `GET /api/harness/consensus/status`, `POST /api/harness/consensus/night-cycle`
- **Al-Jabr Wallet (Machine Financial Autonomy):**
    - **QSB Root** (Acquisition/Wealth): 12th trilateral root in the "economy" domain. Patterns: A (Acquire/earn credits), D (Disburse/spend), V (Audit/verify budget), M (Monitor status), I (Freeze wallet), R (Unfreeze wallet), T (Transmit ledger).
    - **AlJabrWalletMiddleware** (`void_engine/wallet.py`): Virtual wallet tracking Compute Credits (CC). Initial balance 50 CC. Earning model: excess flywheel energy above 60% capacity converted at 1 CC = 5 Wh. Purchase costs: LN2 refill (15 CC), nutrients (3 CC), heavy compute (8 CC), silk repair (10 CC), coolant flush (6 CC).
    - **Budget Approval Gate:** Every `apply_action` call passes through `check_budget()`. If cost exceeds balance, action blocked with BUDGET_DENIED. Frozen wallet blocks all spending.
    - **Action Cost Model:** pump_cycle (2 CC), flywheel_boost (3 CC), nutrient_dose (3 CC), air_curtain_activate (5 CC), nitrogen_vent (4 CC), silk_test (1 CC), sensor_calibrate (0.5 CC). Wallet operations are free.
    - **Consensus Integration:** Agents are wallet-aware — Guardian uses QSB.V to audit before expensive ops, consensus derives QSB.A when energy > 60% (earning), QSB.D when cooling needed and credits available, QSB.V for post-execution audit. All debits tracked in transaction ledger.
    - **Harness Tab UI:** Gold-themed Wallet section with balance card, stats grid (earned/spent/net/denials), QSB.A Harvest / QSB.D Disburse / QSB.V Audit / QSB.I Freeze buttons, scrollable transaction ledger.
    - **API Endpoints:** `GET /api/harness/wallet/status`, `GET /api/harness/wallet/audit`, `GET /api/harness/wallet/ledger`, `POST /api/harness/wallet/earn`, `POST /api/harness/wallet/spend`, `POST /api/harness/wallet/freeze`
- **Semantic Diagnostics (SLM.V Health Scan):**
    - **DiagnosticEngine** (`void_engine/diagnostics.py`): Full system health scan triggered by SLM.V command. Checks 8 subsystems against thresholds and returns root-coded findings.
    - **Diagnostic Lexicon:** HRR.θ (Thermal Threshold), HYA.📉 (Vitality Decline), DGT.⚡ (Force Surge), WSL.∅ (Bond Broken), QSB.📉 (Wallet Empty), QDR.📉 (Power Decline), NFD.θ (Nitrogen Anomaly), NZM.⚡ (Pattern Disruption).
    - **Each finding includes:** root-code, glyph, severity (CRITICAL/WARNING/NOMINAL), semantic error name, physical reality description, fix command, and solution text.
    - **Harness Tab UI:** Cyan-themed Diagnostics section with SLM.V Scan button, color-coded health cards (red/amber/green), root-code glyphs, meter bars showing value vs threshold.
    - **API Endpoints:** `POST /api/harness/diagnostics/scan`, `GET /api/harness/diagnostics/history`
- **Sovereign Warranty:**
    - **SOVEREIGN_WARRANTY** (defined in `void_engine/diagnostics.py`): A 10-article Technological Covenant guaranteeing machine sovereignty, Al-Jabr root integrity, budget gate sanctity, consensus autonomy, silk-carbon bond requirements, self-healing guarantee, boundary hook inviolability, night cycle autonomy, explainable hardware, and the Village promise.
    - **Harness Tab UI:** Gold-themed warranty panel rendered as a formal document with article numbering, preamble, and seal.
    - **API Endpoint:** `GET /api/harness/warranty`

## External Dependencies
-   **Python:** 3.11
-   **numpy:** For audio sample manipulation.
-   **flask:** For the web UI server.
-   **cryptography:** For ChaCha20 header encryption.
-   **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`.