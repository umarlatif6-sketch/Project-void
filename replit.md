# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed to embed large data files (up to 1GB) within audio signals. It employs advanced techniques such as LSB encoding, dual compression (zlib and lzma), ChaCha20-encrypted headers with MD5 verification, and innovative acoustic camouflage methods. The project introduces the "Adriana Pocket" architecture, utilizing stereo phase-shift encoding to preserve audio integrity while embedding data in harmonic frequency pockets. This engine is built for extensibility, with a vision to integrate future modules like Silk Web for signal transmission and Graphene Suit for sensor integration. The business vision is to provide a robust, stealthy, and high-capacity data concealment solution with potential applications in secure communication and digital watermarking.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID features a Flask-based web UI and a CLI for interaction. The core `void_engine` package handles compression, steganography, capacity analysis, and signal transmission.

**UI/UX Decisions:**
- **Web UI:** Dark-themed, mobile-responsive interface with eight dedicated tabs: Encode, Decode, Burst, Visualizer, Capacity, Silk Web, Files, and Harness.
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

**Plankton-Orin Harness Architecture (Digital Nervous System):**
- **PreCompletionChecklistMiddleware** (`void_engine/harness.py`): Configurable parameter boundary checks for Aquaponics (pump cycle limits 12/hr, pH 6.0-7.5, temp 18-28°C, dissolved oxygen min 5 ppm, ammonia max 0.5 ppm, water level min 60%), Flywheel (RPM 800-12000, energy reserve min 50 Wh / critical 20 Wh, temp max 65°C, vibration max 2.5g), Silk Wiring (resistance 0.5-50 ohm, delta max 5 ohm, min 4 active strands), and Pressure (seal breach 1.8 atm, high pressure 1.5 atm max, air curtain minimum velocity 10 m/s when pressure elevated). Returns PASS/FAIL/RECONSIDER verdict with diagnostic context per check.
- **VirtualVoidSimulator** (`void_engine/harness.py`): Sandbox execution layer that mirrors the 4000-series machine's I/O state. Simulates proposed actions (pump_cycle, flywheel_boost, sensor_calibrate, nutrient_dose, silk_test, air_curtain_activate, air_curtain_deactivate, nitrogen_vent) against the virtual environment, running the PreCompletionChecklist before allowing execution. Maintains action log and full state history. Includes Air Curtain Pressure Differential subsystem.
- **Air Curtain Pressure Differential** (`void_engine/harness.py`): Internal/external pressure tracking, air curtain velocity control, seal integrity monitoring, nitrogen boil simulation with automatic venting. Physics: nitrogen boil increases pressure at configurable rate, active air curtain (velocity >= 10 m/s) vents 80% of differential automatically. Seal integrity degrades 15% per tick at breach threshold (1.8 atm). Air curtain energy cost: 0.3 Wh per m/s from flywheel.
- **SilkLinkContextMiddleware** (`void_engine/nervous_system.py`): Deterministic Context Injection — automatically injects current sensor readings (silk resistance, aquaponics pH/temp/O2, flywheel RPM/energy, pressure/air curtain/nitrogen/seal) into every agent system prompt. Agent doesn't search for sensor data; it feels it. Categorizes sensors by subsystem (Silk/Aqua/Flywheel/Pressure), tracks injection count and history.
- **AquaponicsBoundaryHook** (`void_engine/nervous_system.py`): Safety interception middleware. 11 built-in boundary rules (pump cycle limit, pH range, flywheel energy floor, overspeed, silk drift, water temp, ammonia spike, seal breach pressure, high pressure, air curtain velocity). When violated, blocks execution and provides specific reconsideration prompts. Custom rules can be added dynamically.
- **LoopDetectionMiddleware** (`void_engine/loop_detector.py`): Doom Loop Breaker — tracks repeated action attempts with delta monitoring. If an action is attempted 5+ times within a 300s window with no meaningful result change (delta < 0.01), triggers a diagnostic alert with hardware-specific suggestions (including air curtain fan motor checks, nitrogen valve inspection, seal gasket inspection). Includes cooldown suppression and alert resolution.
- **NitrogenLeakChaosTest** (`void_engine/chaos_test.py`): Event-driven stress test that simulates escalating nitrogen boil events to verify the safety middleware auto-responds by activating the Air Curtain before seal breach. Configurable parameters: total steps, initial boil rate, escalation factor, auto-respond toggle. Generates detailed step-by-step reports showing pressure, seal integrity, checklist verdicts, boundary violations, and auto-response actions. Test result: PASS when safety middleware detects danger and activates AC before seal fails. Verified: 10-step test at 0.05 initial rate / 1.5x escalation — AC auto-activated at step 5, max pressure 1.22 atm, seal survived at 100%.
- **Harness Tab (Web UI):** Environment State dashboard showing real-time Aquaponics/Flywheel/Silk/Pressure sensor readings with visual pressure bar (warning at 1.3 atm, danger at 1.5 atm, breach at 1.8 atm). Air Curtain activate/deactivate controls with velocity input. Nitrogen Leak Chaos Test panel with configurable parameters and detailed step-by-step results. PreCompletion Checklist with color-coded PASS/FAIL/RECONSIDER verdicts. Virtual Void Simulator for action simulation and execution. Loop Detection alerts with diagnostic suggestions. SilkLink Context Injection preview.
- **Harness API Endpoints:**
  - `GET /api/harness/status` — Full system state, checklist, loop detector and boundary hook stats
  - `POST /api/harness/check` — Simulate an action without executing (dry run)
  - `POST /api/harness/execute` — Execute action through full safety pipeline (boundary hook → loop detector → checklist → apply)
  - `GET /api/harness/loops` — Active doom loop alerts
  - `POST /api/harness/loops/resolve` — Resolve a doom loop alert
  - `GET /api/harness/sensors` — All registered sensor readings
  - `POST /api/harness/sensors/update` — Update a sensor value (propagates to simulator state)
  - `POST /api/harness/context` — Generate SilkLink context-injected prompt
  - `GET /api/harness/params` — Current checklist parameter boundaries
  - `POST /api/harness/params/update` — Update checklist boundaries
  - `GET /api/harness/pressure` — Current pressure system state (internal/external pressure, air curtain, seal integrity)
  - `POST /api/harness/air-curtain` — Activate/deactivate Air Curtain with velocity parameter
  - `POST /api/harness/nitrogen-boil` — Trigger a nitrogen boil simulation tick
  - `POST /api/harness/chaos-test` — Run Nitrogen Leak Chaos Test (steps, initial_boil_rate, escalation_factor, auto_respond)
  - `GET /api/harness/chaos-test/reports` — Historical chaos test reports
  - `POST /api/harness/pressure/reset` — Reset pressure system to nominal (1.0 atm, AC off, seal 100%)

**Adriana Protocol — Semantic Core Language (SCL):**
- **AdrianaLexicon** (`void_engine/adriana.lex`): 45-glyph ontology mapping semantic symbols to domain operations across Aquaponics (α ψ ω μ ν π), Flywheel (Φ Ε Θ Γ), Silk (σ δ λ), Pressure (Ρ Χ Ν Σ), and System (Ω ∞). Three categories: Entity (subjects/sensors), Condition (thresholds/qualifiers like θ 📈 📉 ⚡ ⚖️), Action (operations like ❄️ 💊 🌊 🔋 🛡️ 💨).
- **AdrianaTranspiler** (`void_engine/adriana_transpiler.py`): Parses glyph-chain expressions using Subject-Condition-Action grammar (e.g., `α-θ-❄️` = "When heat exceeds threshold → cool"). Supports multi-branch expressions via `|` separator. Generates VirtualVoidSimulator action sequences, validates against lexicon, produces human-readable narratives, and calculates compression metrics.
- **Frequency Compression**: Measured 11-14x compression ratio vs equivalent Python code. Each semantic glyph carries complete intent — eliminates lexical ambiguity. Multi-branch expressions maintain 11x+ ratios.
- **Safety Integration**: All transpiled commands route through the full Harness safety pipeline (BoundaryHook → LoopDetector → PreCompletionChecklist) before execution. Conditional boundary rules (e.g., air curtain velocity only checked when pressure elevated above 1.1 atm).
- **Harness Tab UI**: Adriana Protocol section with glyph input field, Transpile (dry-run) and Execute buttons, narrative display, compression ratio visualization, Python equivalent preview, safety dry-run results, and toggleable lexicon reference panel.
- **Adriana API Endpoints:**
  - `GET /api/harness/adriana/lexicon` — Full glyph map with categories, domains, descriptions
  - `POST /api/harness/adriana/transpile` — Parse expression, generate commands, dry-run safety checks
  - `POST /api/harness/adriana/execute` — Transpile and execute through full safety pipeline

## External Dependencies
-   **Python:** 3.11
-   **numpy:** For audio sample manipulation.
-   **flask:** For the web UI server and keep-alive functionality.
-   **cryptography:** For ChaCha20 header encryption.
-   **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib` are utilized for compression, WAV file handling, and hashing.