# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed for embedding large data files (up to 1GB) within audio signals. It employs LSB encoding, dual compression, ChaCha20-encrypted headers with MD5 verification, and acoustic camouflage techniques. The "Adriana Pocket" architecture utilizes stereo phase-shift encoding to preserve audio integrity. The project aims to provide a robust, stealthy, and high-capacity solution for secure communication and digital watermarking, fostering secure and private digital interactions.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## VOID: Sovereign Realm — 3D Game (Task #18)
- **Route:** `/game` (login required) — rendered by `routes/game.py` blueprint
- **Template:** `templates/game.html` — full Three.js 3D game with embedded CSS/JS
- **Three Game Modes:**
  - **Exploration:** Fly through procedural icosahedron signal vaults; click to discover (0.5 VTX each)
  - **Node Builder:** Deploy octahedron sovereign nodes on a 3D hex-grid (2.0 VTX each)
  - **Adriana Cipher:** Solve glyph-sequence puzzles in floating 3D chamber (1.0 VTX each)
- **VTX Rewards:** `mint_game_reward()` in `void_engine/vortex_wallet.py`; daily cap 50 VTX/user
- **Reward tiers:** vault_discovered=0.5, glyph_solved=1.0, node_built=2.0, level_up=5.0
- **Level-up logic:** Triggered automatically when total actions >= level*3
- **Game Stats columns on users table:** game_level, nodes_built, vaults_opened, glyphs_solved, total_game_vtx
- **API endpoints:** POST /api/game/reward, GET /api/game/stats
- **Navigation:** "VOID Game" link added to main engine nav (index.html) and landing nav (landing.html)
- **Landing page teaser:** `landing-game-teaser` section with mode cards added to /launch page
- **Styles:** Game teaser CSS appended to static/style.css; game page uses self-contained embedded styles
- **Ledger:** All rewards recorded in vortex_ledger with tx_type='mint_game'

## System Architecture
PROJECT VOID features a Flask-based web UI and a command-line interface, with the `void_engine` as its core. It operates on a Brain (Flask web app) + Body (local Python node) hybrid architecture.

**UI/UX Decisions:**
- **Web UI:** Dark-themed, mobile-responsive interface with interactive tabs, Web Audio API-based spectrum/spectrograms, and visual effects like "Vocal Pocket Visualizer."
- **Theming:** Dynamic UI color shifts and badges indicate user tiers. Features glass-morphic elements for a modern aesthetic.
- **Dedicated Pages:** Includes an Industries page showcasing use cases, custom branded error pages, and an admin dashboard for lead management.
- **Favicon:** SVG diamond icon in teal.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** Uses 16-bit PCM WAV files at a 432 Hz base frequency ("Village Standard").
- **Compression:** Dual compression using zlib (level 9) and lzma (preset 9).
- **Steganography Core:** LSB encoding (depth 1 and 2), 64-byte ChaCha20-encrypted headers, "Ghost Header," "Fly Jitter," "Vortex Scatter," "Chirp Sync," and "Adriana Pocket" for stereo phase-shifted LSB.
- **Data Protocols:** "Divided Operational Protocol" (5-step axiomatic pipeline), "Signal Transmission (Silk Web)" using 432 Hz burst-encoded WAV packets with "Sapphire Masking."
- **Capacity Analysis:** "Resonance Meter" calculates payload capacity, "Surface Tension Limit," and "Bubble Burst threshold."
- **Middleware:** "Plankton-Orin Harness Architecture" for pre-completion checks, sandboxing, and safety.
- **Semantic Core Language (SCL):** "Adriana Protocol" defines `AdrianaLexicon` and `AdrianaTranspiler` for parsing glyph-chain expressions.
- **AI Logic:** "Al-Jabr Code" utilizes an 18-root ontology across 9 domains with 7 verb patterns, mapped via the "Al-Jabr Consensus Engine."
- **System Integrity:** "Sovereign Warranty" (10-article "Technological Covenant") and an "Auto-Heal Daemon" ensure machine sovereignty. "Root-Chronicle" stores successful Consensus outcomes.
- **Acoustic Mesh Network:** "Biophony Mesh" (carrier topology) and "Beehive Protocol" (Ghost Internet) form an acoustic mesh with a 432 Hz handshake and PSK data transmission, including the "Sura-Fatiha 286-Bit Acoustic Handshake."
- **Proof-of-Work:** "Kinetic Transceiver" generates Compute Credits from calisthenics repetitions.
- **Hashing:** "Al-Jabr 286 Protocol" is a custom 286-bit hash algorithm.
- **Decentralized Ledger:** "Silt Ledger" (DAO 3.0) is a Fatiha-286 chained blockchain for voting, integrated with the Beehive Protocol.
- **Cryptocurrency:** "VORTEX Currency (VTX)" is earned via "Proof of Resonance" and "Proof of Bloom," supporting peer-to-peer transfers and credit pack purchases.
- **AI Assistant:** "Void Fairy" is an OpenAI-powered guide, "Adriana," offering context-aware assistance and adaptive communication.
- **Verification:** "Adriana Resonance Handshake" uses an Al-Jabr 286 hash for verification, triggering a "Blooming Lotus" animation.
- **Global State:** "Global VoidState + Command Bar" tracks VTX balance, user tier, engine status, and mesh connection.
- **Onboarding:** "Sovereign Onboarding Flow" provides a guided walkthrough for new Sovereign-tier users.
- **Proof Page:** A public presentation page for demos, displaying audio comparisons and technical metrics.
- **Revenue Model:** Dual-layer model with software subscription tiers and hardware tiers.
- **Security Hardening:** XSS protection, environment variable for secret management, file upload whitelisting, database migration safety, health checks, and OpenAI data sanitization.
- **Hybrid Architecture:** The web app (Brain) manages blueprints and coordinates the mesh, while a downloadable Python package (Body) handles local processing, detecting CUDA for GPU acceleration or falling back to CPU.
- **NFT Marketplace (Blueprint Tokens):** A DePIN system where NFTs represent manufacturing slots for Sovereign Node machines, built on Al-Jabr 286-bit hashing and the Vortex Ledger. Includes Common, Rare, and Legendary tiers with corresponding access and ownership.
- **QiSync BioStance & Mastication Tracker:** A feature (`/qisync`) that uses a CSI Backend (`StanceDetector`, `MasticationDetector`) to monitor user biometrics (stance, mastication) via Wi-Fi CSI, phone sensors, or simulation. Users earn VTX rewards based on a composite metabolism score.

## External Dependencies
- **Python:** 3.11
- **numpy:** Audio processing
- **flask:** Web framework
- **cryptography:** Encryption
- **fpdf2:** PDF generation
- **psycopg2-binary:** PostgreSQL adapter
- **werkzeug:** Security utilities
- **stripe:** Payment processing
- **openai:** AI assistant
- **gunicorn:** Production WSGI server
- **requests:** HTTP client
- **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`
- **PostgreSQL:** Database