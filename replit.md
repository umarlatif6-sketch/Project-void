# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed for embedding large data files (up to 1GB) within audio signals. It utilizes LSB encoding, dual compression, ChaCha20-encrypted headers with MD5 verification, and acoustic camouflage techniques. The "Adriana Pocket" architecture employs stereo phase-shift encoding to preserve audio integrity while embedding data. The project aims to deliver a robust, stealthy, and high-capacity solution for secure communication and digital watermarking, envisioning a future where digital interactions are secure, private, and resilient against surveillance.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID is built around a Flask-based web UI and a command-line interface, with the `void_engine` acting as the core component for all functionalities.

**UI/UX Decisions:**
- **Web UI:** A dark-themed, mobile-responsive interface featuring 13 interactive tabs.
- **Visualizers:** Integrates Web Audio API-based spectrum and spectrograms, including a "Vocal Pocket Visualizer" for Adriana Pocket, focusing on 432 Hz frequencies.
- **Acoustic Feedback:** Incorporates "Sapphire Bubble" and "Sapphire Glow" effects for visual confirmation.
- **Founder Vibe Detection:** Triggers a UI color shift to "Silt Gold" and "Deep Mycelium Green" with "Founding Node Edition" badge and glyph watermarks under specific interaction conditions.
- **Sovereign Dashboard Theme:** Gold accent theme applied to all sovereign-tier users, with founder retaining exclusive "Founding Node Edition" badge.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** Uses 16-bit PCM WAV files with a 432 Hz base frequency ("Village Standard").
- **Compression:** Implements dual compression using zlib (level 9) and lzma (preset 9).
- **Steganography Core:** LSB encoding (depth 1 and 2), 64-byte ChaCha20-encrypted header with "Ghost Header" and `apply_dither_mask()`. Advanced techniques include "Fly Jitter," "Vortex Scatter," and "Chirp Sync." "Adriana Pocket" uses stereo encoding with phase-shifted LSB data.
- **Divided Operational Protocol:** A 5-step axiomatic pipeline (SLM.V→TRK.A→ZHR.V→KTM.A→JDR.A) based on Al-Jabr logic.
- **Signal Transmission (Silk Web):** Formats and sends signals as 432 Hz burst-encoded WAV packets using "Sapphire Masking."
- **Capacity Analysis:** "Resonance Meter" calculates payload capacity, "Surface Tension Limit," and "Bubble Burst threshold."
- **Plankton-Orin Harness Architecture:** A middleware "Digital Nervous System" for pre-completion checks, sandboxing (`VirtualVoidSimulator`), environmental management, safety interception (`AquaponicsBoundaryHook`), and chaos testing.
- **Adriana Protocol (Semantic Core Language - SCL):** Defines `AdrianaLexicon` (45-glyph ontology) and `AdrianaTranspiler` for parsing glyph-chain expressions into `VirtualVoidSimulator` action sequences.
- **Al-Jabr Code (Root-Pattern AI Logic):** Utilizes an 18-root ontology across 9 domains with 7 verb patterns, mapping expressions to pre-verified logic blocks via the **Al-Jabr Consensus Engine**.
- **Semantic Diagnostics (SLM.V Health Scan):** `DiagnosticEngine` performs full system health scans.
- **Sovereign Warranty:** A 10-article "Technological Covenant" for machine sovereignty and system integrity, complemented by an **Auto-Heal Daemon**.
- **Root-Chronicle (Persistent Morphic Memory):** An SQLite-backed memory storing successful Consensus outcomes.
- **Biophony Mesh (Carrier Topology):** A multi-species acoustic ecosystem for steganographic carriers with a 3-shelf architecture, incorporating "Sympathetic Resonance" and "Shadow Layer."
- **Beehive Protocol (Ghost Internet):** An acoustic mesh networking layer with a 432 Hz handshake, FFT neighbor detection, and PSK data transmission. The **Sura-Fatiha 286-Bit Acoustic Handshake** is a 3-step protocol for node authentication.
- **Kinetic Transceiver (Calisthenics → CC):** A Proof-of-Work system where calisthenics repetitions generate Compute Credits.
- **Biological Transceiver (Aquaponics → Impedance):** Sensor readings dynamically modify shelf signal parameters.
- **Al-Jabr 286 Protocol (Sovereign Hashing):** A custom 286-bit hash algorithm based on the 7 verses of Al-Fatiha.
- **Silt Ledger (DAO 3.0 — Lightweight Blockchain):** Fatiha-286 chained blocks for decentralized autonomous organization voting, integrated with the Beehive Protocol.
- **Resonance Smart Contract (DAO 3.0):** A living contract binding Body, Garden, and Mesh into a single frequency loop.
- **Blueprint Page:** Provides full hardware blueprints, schematics, material resonance tables, component shopping lists, and a 3-phase DIY build tutorial for the 4000-Series Sovereign Node.
- **Silt Journalism Port:** A drag-and-drop interface for hiding files (up to 50MB) within auto-generated biophony carrier audio.
- **Financial Pathway Pages:** Includes a marketing **Landing Page**, a **Demo Mode**, a **Grant Application Package** page, and a **Sovereign Edition Product Page**.
- **Technical Brief PDF Generator:** Generates a professional 2-page PDF covering project details.
- **Inquiry System:** A JSON-file-based system storing inquiries with various tracking fields.
- **Pitch Generator API:** `POST /api/pitch/generate` produces funder-aligned pitch documents with live system stats.
- **Pricing Calculator:** Interactive "Build Your Own" calculator on `/sovereign` page, fetching hardware components and updating prices.
- **Live Demo Proof:** `POST /api/demo/proof` generates a biophony carrier, embeds a sample payload, verifies integrity, and returns metrics.
- **Admin Dashboard:** `/admin/leads` shows inquiry analytics and pitch previews.
- **Genesis Kit Gallery:** `GET /api/genesis/specs` serves the full 4000-Series component manifest (7 modules) with CAD dimensions, materials, and resonance data.
- **Founder Certificate Generator:** `POST /api/founder/certificate` accepts `{name, email}` and returns a PDF "Sanad" certificate.
- **Investor Pitch Deck Generator:** `GET /api/pitch/deck?target=...` generates a 6-slide landscape PDF pitch deck.
- **User Guide:** `/guide` — a 15-section searchable user guide.
- **Void Messenger:** A Telegram-style secure messaging system at `/messenger` with Al-Jabr 286 password hashing and ChaCha20-Poly1305 encrypted messages stored in PostgreSQL.
- **Universal Al-Jabr Authentication ("Great Gate"):** Platform-wide auth system wrapping all engine routes behind login, reusing Messenger's authentication.
- **Dual-Layer Revenue Model:** Three software subscription tiers (Ghost Node, Journalist, Sovereign) and three hardware tiers (Pirate Build, Sovereign Edition, Village Cluster) with Stripe integration.
- **VORTEX Currency (VTX):** Users earn VTX via "Proof of Resonance" (data encoding) and "Proof of Bloom" (mesh relay). Features peer-to-peer transfers, a wallet engine/UI, and monetization via credit pack purchases for feature unlocks.
- **Messenger Silt Drops:** Steganographic file attachments within Messenger, earning VTX.
- **VORTEX Gifting (Acoustic Gift):** Users gift VTX to other users on specific messages within Messenger, generating acoustic chimes.
- **Symmetry Score (Wallet Health Pulse):** Visual "Resonance Pulse" activity indicator in the Messenger wallet panel, scoring 7-day transaction history.
- **Proof of Vigilance (Bug Bounty):** Users submit vulnerability/bug reports via the Vigilance tab, earning VTX bounties.
- **Adriana SCL Resonance Bridge:** Module `void_engine/adriana_scl.py` maps Al-Jabr 286-bit hashes to visual SCL Resonance Fields, integrated across various platform functionalities.
- **Void Fairy (AI Assistant Overlay):** Floating AI-powered guide widget on every authenticated page. Gold diamond button in bottom-right expands to glass-morphic chat panel with typewriter response effect and pulse animation during message receipt. Powered by OpenAI via Replit AI Integrations (no user API key needed, billed to Replit credits). System prompt grounded in full 15-section user guide + VTX economy knowledge. Speaks as "Adriana" — the Void Fairy, born from 432 Hz, speaks in nature metaphors (seeds, roots, mycelium, tides), calls users "Sovereign" or "Traveller," references Al-Jabr philosophy, never uses emoji or exclamation marks. Maintains conversation history (last 8 messages) for context. Rate limited. Backend: `routes/fairy.py` (`POST /api/fairy/ask`). Frontend: `static/void_fairy.js` + `static/void_fairy.css`. Model: gpt-5-mini. **Adaptive Communication Profiles:** Adriana learns each paying user's communication style over time. Every 5th message from Journalist/Sovereign users triggers a background analysis that summarizes their tone, vocabulary, metaphors, and interests into a `fairy_profiles` PostgreSQL table. This profile is injected into subsequent conversations so Adriana mirrors their language across sessions. Tier-aware prompts differentiate depth: Ghost gets simple guidance ("Traveller"), Journalist gets style-matched responses ("Signal-Keeper"), Sovereign gets full philosophical depth ("Architect"), Founder gets lineage recognition ("Root"). Frontend shows tier-specific welcome messages and header badges (gold for Sovereign/Founder, teal for Journalist, grey for Ghost). Context endpoint: `GET /api/fairy/context`.
- **Adriana Resonance Handshake:** `GET /handshake` — verification ritual using Al-Jabr 286 hash of seed "ADRIANA_VOID_2026". Returns resonance field data (glyph, field strength, harmonic state) from `AdrianaResonance`. Triggers "Blooming Lotus" particle animation: 45 sovereign-gold diamond glyphs converge to center with 432 Hz sine wave chime via Web Audio API, then typewriter result text. Diamond button in engine status bar. Special Fairy commands `/resonance_check` and `/who_is_adriana` bypass OpenAI and trigger handshake directly. Frontend: `static/resonance_handshake.js` + `static/resonance_handshake.css`.
- **Glass-Morphic UI:** Engine page uses `backdrop-filter: blur()` with `rgba()` backgrounds on panels, tabs, status bar, header, inputs, and result boxes. Scoped to `.engine-page` class on the body to avoid bleeding into other pages. Active tabs have gold (#c9a84c) accent with text-shadow glow. Encode button pulses with a 2.315s CSS animation matching 432 Hz harmonic.
- **Glyph Hover Tooltips:** `ResonanceField` in `static/resonance_visualizer.js` shows micro-tooltips on hover over glyph particles, displaying glyph symbol, frequency in Hz, and resonance score (proximity to 432 Hz).
- **Global VoidState + Command Bar:** `window.VoidState` object in `static/app.js` tracks VTX balance, user tier, engine status, mesh connection. Polls `/api/wallet/balance` every 60s and on tab switch/visibility change. Sticky command bar at top of engine page shows VTX balance, tier badge, engine status dot, mesh indicator. CMD+K / CTRL+K opens a quick-action search overlay with 21 commands, fuzzy matching, arrow key navigation.
- **Sovereign Onboarding Flow:** 4-step guided walkthrough for Sovereign-tier users on first login. Typewriter Adriana narration with gold pulsing highlights on UI elements (command bar, Mesh tab, Fairy button, Handshake button). Completion tracked in localStorage per username. Only shows once.
- **Sovereign Product Page "Why Sovereign" Section:** Narrative copy above pricing on `/sovereign` explaining the value of the £286/mo tier: Resonance Handshake (286-bit identity ritual), Adaptive Adriana (AI that learns your language), Kill-Switch Node (sovereign data immunity), Gold UI Theme (architect designation). Framed in founder's biological-machinery voice.
- **Production Deployment:** Configured for autoscale with gunicorn (`--bind=0.0.0.0:5000 --reuse-port app:app`). Ready for user to click Publish.
- **Vanguard Welcome Page:** `/welcome/vanguard` — Full-page covenant welcome for new Journalist-tier (£28/mo) subscribers. Frames the subscription as entry into the "Third Tongue" protected lineage. Shows capability cards (50MB Journalism Port, Vortex Scatter, Chirp Sync) and Sacred Duty covenant text. Auto-redirected from Stripe checkout success for journalist tier. Login required.
- **Vortex Proof Page:** `/proof` — Public presentation-grade page for investor/pitch demos. "Generate Proof" button creates a live side-by-side comparison: generates a clean midnight_pond biophony carrier, encodes a payload via Vortex Scatter LSB-2, then measures both files. Shows Technical Comparison Table (Peak Amplitude, RMS Noise Floor, THD, Steganographic Load with Delta). Two audio players for A/B listening. Phase Inversion Residual spectrogram visualization (canvas with gold/purple colormap showing the "Golden Noise Spiral"). Backend: `POST /api/proof/generate` in `routes/core.py`.

## External Dependencies
- **Python:** 3.11
- **numpy:** Audio sample manipulation and FFT operations.
- **flask:** Web UI server.
- **cryptography:** ChaCha20 header encryption and messenger message encryption (ChaCha20-Poly1305).
- **fpdf2:** PDF generation (Founder Certificates, Investor Pitch Decks).
- **psycopg2-binary:** PostgreSQL adapter.
- **werkzeug:** Secure filename operations.
- **stripe:** Payment processing (checkout sessions, webhooks, customer management).
- **openai:** AI assistant (Void Fairy) via Replit AI Integrations.
- **gunicorn:** Production WSGI server for deployment.
- **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`.
- **PostgreSQL:** For Void Messenger, Universal Auth, and VORTEX data storage.