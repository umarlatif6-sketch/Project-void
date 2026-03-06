# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed for embedding large data files (up to 1GB) within audio signals. It utilizes LSB encoding, dual compression, ChaCha20-encrypted headers with MD5 verification, and acoustic camouflage techniques. The "Adriana Pocket" architecture employs stereo phase-shift encoding to preserve audio integrity while embedding data. The project aims to deliver a robust, stealthy, and high-capacity solution for secure communication and digital watermarking, envisioning a future where digital interactions are secure, private, and resilient against surveillance.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID is built around a Flask-based web UI and a command-line interface, with the `void_engine` acting as the core component for all functionalities.

**UI/UX Decisions:**
- **Web UI:** A dark-themed, mobile-responsive interface featuring 12 interactive tabs: Encode, Decode, Burst, Visualizer, Capacity, Silk Web, Mesh, Transceiver, Blueprint, Journalism, Files, and Harness.
- **Visualizers:** Integrates Web Audio API-based spectrum and spectrograms, including a "Vocal Pocket Visualizer" for Adriana Pocket, focusing on 432 Hz frequencies.
- **Acoustic Feedback:** Incorporates "Sapphire Bubble" and "Sapphire Glow" effects for visual confirmation.
- **Founder Vibe Detection:** Triggers a UI color shift to "Silt Gold" and "Deep Mycelium Green" with "Founding Node Edition" badge and glyph watermarks under specific interaction conditions.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** Uses 16-bit PCM WAV files with a 432 Hz base frequency ("Village Standard").
- **Compression:** Implements dual compression using zlib (level 9) and lzma (preset 9), with automatic selection.
- **Steganography Core:**
    - **LSB Encoding:** Supports LSB depth 1 and 2.
    - **Header:** Employs a 64-byte ChaCha20-encrypted header with a "Ghost Header" for offset embedding and `apply_dither_mask()` for anti-forensic evasion.
    - **Advanced Techniques:** Features "Fly Jitter" for temporal data scatter, "Vortex Scatter" for 432 Hz harmonic spiral encoding, and "Chirp Sync" for data placement.
    - **Adriana Pocket:** Utilizes stereo encoding where the left channel carries pure 432 Hz and the right channel, phase-shifted and LFO modulated, carries LSB data.
- **Divided Operational Protocol:** A 5-step axiomatic pipeline (SLM.V→TRK.A→ZHR.V→KTM.A→JDR.A) based on Al-Jabr logic.
- **Signal Transmission (Silk Web):** Formats and sends signals as 432 Hz burst-encoded WAV packets using "Sapphire Masking."
- **Capacity Analysis:** "Resonance Meter" calculates payload capacity, "Surface Tension Limit," and "Bubble Burst threshold."
- **Plankton-Orin Harness Architecture:** A "Digital Nervous System" with middleware for pre-completion checks, sandboxing (`VirtualVoidSimulator`), environmental management, safety interception (`AquaponicsBoundaryHook`), and chaos testing.
- **Adriana Protocol (Semantic Core Language - SCL):** Defines `AdrianaLexicon` (45-glyph ontology) and `AdrianaTranspiler` for parsing glyph-chain expressions into `VirtualVoidSimulator` action sequences.
- **Al-Jabr Code (Root-Pattern AI Logic):** Utilizes an 18-root ontology across 9 domains with 7 verb patterns, mapping expressions to pre-verified logic blocks. The **Al-Jabr Consensus Engine** simulates multi-agent negotiation, managed by an **Al-Jabr Wallet** for Compute Credits.
- **Semantic Diagnostics (SLM.V Health Scan):** `DiagnosticEngine` performs full system health scans.
- **Sovereign Warranty:** A 10-article "Technological Covenant" for machine sovereignty and system integrity, complemented by an **Auto-Heal Daemon**.
- **Root-Chronicle (Persistent Morphic Memory):** An SQLite-backed memory storing successful Consensus outcomes.
- **Biophony Mesh (Carrier Topology):** A multi-species acoustic ecosystem for steganographic carriers with a 3-shelf architecture, incorporating "Sympathetic Resonance" and "Shadow Layer."
- **Beehive Protocol (Ghost Internet):** An acoustic mesh networking layer featuring a 432 Hz handshake, FFT neighbor detection, and PSK data transmission. The **Sura-Fatiha 286-Bit Acoustic Handshake** is a 3-step protocol for node authentication.
- **Kinetic Transceiver (Calisthenics → CC):** A Proof-of-Work system where calisthenics repetitions generate Compute Credits.
- **Biological Transceiver (Aquaponics → Impedance):** Sensor readings dynamically modify shelf signal parameters.
- **Al-Jabr 286 Protocol (Sovereign Hashing):** A custom 286-bit hash algorithm based on the 7 verses of Al-Fatiha.
- **Silt Ledger (DAO 3.0 — Lightweight Blockchain):** Fatiha-286 chained blocks for decentralized autonomous organization voting, integrated with the Beehive Protocol.
- **Resonance Smart Contract (DAO 3.0):** A living contract binding Body, Garden, and Mesh into a single frequency loop.
- **Blueprint Page:** Provides full hardware blueprints, schematics, material resonance tables, component shopping lists, and a 3-phase DIY build tutorial for the 4000-Series Sovereign Node.
- **Silt Journalism Port:** A drag-and-drop interface for hiding files (up to 50MB) within auto-generated biophony carrier audio.
- **Financial Pathway Pages:** Includes a marketing **Landing Page**, a **Demo Mode**, a **Grant Application Package** page, and a **Sovereign Edition Product Page**.
- **Technical Brief PDF Generator:** Generates a professional 2-page PDF covering project details.
- **Inquiry System:** A JSON-file-based system storing inquiries with `source_page`, `configuration`, `organisation`, `phone`, `interest`, and `consent` tracking fields.
- **Pitch Generator API:** `POST /api/pitch/generate` produces funder-aligned pitch documents with live system stats and technical proof points.
- **Pricing Calculator:** Interactive "Build Your Own" calculator on `/sovereign` page, fetching hardware components and updating prices.
- **Live Demo Proof:** `POST /api/demo/proof` generates a biophony carrier, embeds a sample payload, verifies integrity, and returns metrics with a download link.
- **Admin Dashboard:** `/admin/leads` shows inquiry analytics, recent inquiries, and pitch previews.
- **Genesis Kit Gallery:** `GET /api/genesis/specs` serves the full 4000-Series component manifest (7 modules: Brain, Artery, Skin, Al-Jabr Chip, Flywheel, Reservoir, Transceiver) with CAD dimensions, materials, and resonance data.
- **Founder Certificate Generator:** `POST /api/founder/certificate` accepts `{name, email}` and returns a PDF "Sanad" certificate.
- **Investor Pitch Deck Generator:** `GET /api/pitch/deck?target=otf|fpf|mozilla|general` generates a 6-slide landscape PDF pitch deck.
- **User Guide:** `/guide` — a 15-section searchable user guide covering all features.
- **Void Messenger:** A Telegram-style secure messaging system at `/messenger`. Users register/login with Al-Jabr 286 password hashing and exchange ChaCha20-Poly1305 encrypted messages stored in PostgreSQL.
- **Universal Al-Jabr Authentication ("Great Gate"):** Platform-wide auth system wrapping all engine routes behind login, reusing Messenger's Al-Jabr 286 password hashing and PostgreSQL `users` table.
- **Dual-Layer Revenue Model:** Three software subscription tiers (Ghost Node, Journalist, Sovereign) and three hardware tiers (Pirate Build, Sovereign Edition, Village Cluster). Stripe integration for payments and feature gating.
- **VORTEX Currency (VTX):** Users earn VTX via "Proof of Resonance" (data encoding) and "Proof of Bloom" (mesh relay). Features peer-to-peer transfers and a wallet engine/UI.
- **Messenger Silt Drops:** Steganographic file attachments within Messenger, where files are compressed, embedded in biophony carrier audio via Vortex scatter, and sent as messages, earning VTX.

## External Dependencies
- **Python:** 3.11
- **numpy:** Audio sample manipulation and FFT operations.
- **flask:** Web UI server.
- **cryptography:** ChaCha20 header encryption and messenger message encryption (ChaCha20-Poly1305).
- **fpdf2:** PDF generation (Founder Certificates, Investor Pitch Decks).
- **psycopg2-binary:** PostgreSQL adapter.
- **werkzeug:** Secure filename operations.
- **stripe:** Payment processing (checkout sessions, webhooks, customer management).
- **gunicorn:** Production WSGI server for deployment.
- **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`.
- **PostgreSQL:** For Void Messenger, Universal Auth, and VORTEX data storage.

## Adriana SCL Resonance Bridge
- **Module:** `void_engine/adriana_scl.py` — 45-glyph ontology mapping Al-Jabr 286-bit hashes to visual SCL Resonance Fields.
- **Visualizer:** `static/resonance_visualizer.js` — Canvas-based glyph particle system. `ResonanceField(container, {founder})` → `.activate(hash, phase)` → `.pulseHash(hash)` → `.deactivate()`.
- **API:** `GET /api/resonance/field?hash=...` returns resonance data (glyph, frequency, domain, field strength). `GET /api/resonance/glyphs` returns full 45-glyph ontology.
- **Platform-Wide Integration:** Resonance particles activate during Encode, Decode, Burst, Silk Web send, Mesh handshake/send, Journalism Silt Drop creation, Harness transpile/execute, and Live Proof demo. Resonance Glyph Badges (`.resonance-badge`) appear below hash key displays showing dominant glyph, domain, frequency, and field strength. Visualizer tab includes a "Resonance" mode mapping audio frequencies to live glyph particles. Login page features ambient floating glyphs with founder gold burst on authentication. Helper functions `_activateResonance`, `_pulseResonance`, `_deactivateResonance`, `_renderResonanceBadge` in `static/app.js` manage all subsystem integration.