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
- **Founder Vibe Detection:** After 3+ minutes on `/sovereign` or calculator interaction, the UI shifts from standard accent to "Silt Gold" (#c9a84c) and "Deep Mycelium Green" (#2d6a4f), with Adriana SCL glyph watermarks in the margins and a pulsing "Founding Node Edition" badge.

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
- **Inquiry System:** A JSON-file-based system storing inquiries with `source_page`, `configuration`, `organisation`, `phone`, `interest`, and `consent` tracking fields. Consent is required (returns 400 if missing). Forms on all 4 pages: landing, demo, sovereign, grants.
- **Pitch Generator API:** `POST /api/pitch/generate` produces funder-aligned pitch documents (OTF, FPF, Mozilla, General) with live system stats, capacity demonstrations, and technical proof points. `GET /api/pitch/targets` lists available targets.
- **Pricing Calculator:** Interactive "Build Your Own" calculator on `/sovereign` page — fetches 14 hardware components from `/api/blueprint/specs`, allows toggling self-source per component, live-updates price between £25,000 and self-source minimum (~£443-660), with "Request Custom Quote" pre-filling the inquiry form.
- **Live Demo Proof:** `POST /api/demo/proof` generates a midnight_pond biophony carrier, embeds a sample payload via Vortex scatter at LSB-2, verifies integrity, and returns full metrics with download link. Available via "Live Proof" tab in demo mode.
- **Admin Dashboard:** `/admin/leads` (SESSION_SECRET auth via query param `?token=`) shows inquiry analytics by type and source, recent inquiries table (with organisation, phone, interest, consent columns), source breakdown bar, and pitch previews for all funder targets.
- **Genesis Kit Gallery:** `GET /api/genesis/specs` serves the full 4000-Series component manifest (7 modules: Brain, Artery, Skin, Al-Jabr Chip, Flywheel, Reservoir, Transceiver) with CAD dimensions, materials, and resonance data. Displayed as interactive cards on `/sovereign` page with assembly table and sequence.
- **Founder Certificate Generator:** `POST /api/founder/certificate` accepts `{name, email}` and returns a PDF "Sanad" — gold-on-black certificate with Al-Jabr 286-bit seal, 5 articles of lineage, machine hash, root hash reference. Offered after successful sovereign inquiry submission.
- **Investor Pitch Deck Generator:** `GET /api/pitch/deck?target=otf|fpf|mozilla|general` generates a 6-slide landscape PDF pitch deck with gold-on-black aesthetic. Slides: Cover, Problem, Solution (live stats), Hardware (Genesis Kit 7 modules), Business Model (pricing tiers + funders), Call to Action (alignment + seal). Download buttons on `/sovereign` (Sovereign Edition card) and `/grants` (appears after generating pitch, pre-selects funder target). Built in `void_engine/pitch_deck.py`.
- **Founder Vibe Detection:** JS on `/sovereign` tracks page time (3+ minutes) and calculator interaction to trigger a Silt Gold / Mycelium Green UI shift via `data-founder-vibe` attribute, with floating glyph watermarks and "Founding Node Edition" badge.

- **Void Messenger:** A Telegram-style secure messaging system at `/messenger`. Users register/login with Al-Jabr 286 password hashing, search for other users, and exchange ChaCha20-Poly1305 encrypted messages stored in PostgreSQL. Features: conversation list with last message preview, real-time polling (3s), mobile-responsive with sidebar toggle, new chat modal with user search, message bubbles with sent/received styling. All messages stored encrypted in the database — plaintext never touches disk. Routes in `routes/messenger.py`, auth/crypto logic in `void_engine/messenger_auth.py`.

## External Dependencies
- **Python:** 3.11
- **numpy:** Used for audio sample manipulation and FFT operations.
- **flask:** Provides the web UI server.
- **cryptography:** Utilized for ChaCha20 header encryption and messenger message encryption (ChaCha20-Poly1305).
- **fpdf2:** Employed for generating Founder Certificate PDFs and Investor Pitch Deck PDFs.
- **psycopg2-binary:** PostgreSQL adapter for the Void Messenger user/message database.
- **werkzeug:** Handles secure filename operations.
- **Standard Library:** Includes `zlib`, `lzma`, `wave`, `hashlib` for core functionalities.

## Database
- **PostgreSQL** (Replit built-in): Used for Void Messenger. Tables: `users`, `conversations`, `conversation_members`, `messages`. Messages are ChaCha20-Poly1305 encrypted before storage. Connection via `DATABASE_URL` env var.

## Key Data Files
- **data/genesis_specs.json:** Full 4000-Series hardware manifest with 7 modules, CAD dimensions, materials, and resonance data.
