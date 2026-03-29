# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed for embedding large data files (up to 1GB) within audio signals. It employs LSB encoding, dual compression, ChaCha20-encrypted headers with MD5 verification, and acoustic camouflage techniques. The "Adriana Pocket" architecture utilizes stereo phase-shift encoding to preserve audio integrity. The project aims to provide a robust, stealthy, and high-capacity solution for secure communication and digital watermarking, fostering secure and private digital interactions.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## PROJECT VOID — Brand Launchpad (Task #31)
- **Routes:** `/brand`, `/brand/content`, `/brand/legal` — `routes/brand.py` blueprint
- **Templates:** `templates/brand.html`, `templates/brand_content.html`, `templates/brand_legal.html`
- **Brand Kit (`/brand`):** Name hierarchy (VOID → Adriana/Al-Jabr, MycoVOID, GriDul, QiSync, VTX+PEACE), one-sentence/paragraph/page pitch formats, brand voice (8 adjectives, 4 tone rules, 10 banned words), 3 OKLCH colour palettes, typography specimens (Space Grotesk + Space Mono), 3 SVG logo concepts, CSS design tokens block
- **Content Playbook (`/brand/content`):** 7 platform-ready post templates — LinkedIn launch, X/Twitter 7-tweet thread, newsletter cold-list intro, acoustic steganography explainer, PEACE coin mechanics explainer, founder sovereignty narrative, community collaborator callout. Each shows hook pattern + char count + platform badge.
- **Legal Starter Kit (`/brand/legal`):** Mutual NDA (pre-filled for PROJECT VOID, 2-year bilateral, common law template) and Research Collaboration Agreement (IP ownership, Background/Foreground IP, publication review, 60-day patent window). Both have plain-English summaries and copy-to-clipboard + print-to-PDF actions.
- **Brand Unification Pass:** "◆ By PROJECT VOID" footer added to `/sovereign-node`, `/mycovoid`, `/mycovoid-concept`, `/apply/interussia`, and `/founder-archive` (archive.html) pages — links back to `/brand` and `/brand/legal`.
- **Typography:** Google Fonts Space Grotesk (display) + Space Mono (mono) loaded on all brand pages.
- **Design language:** OKLCH-grounded palette, Sovereign Gold (`oklch(72% 0.12 85)`), Adriana Teal, GriDul Violet, MycoVOID Green.

## VOID: Sovereign Realm — 3D Game & Economy (Task #18)
- **Routes:** `/game` (3D game), `/game/shop` (equipment shop) — `routes/game.py` blueprint
- **Templates:** `templates/game.html`, `templates/game_shop.html`
- **Three Game Modes (Three.js):**
  - **Exploration:** Fly through procedural icosahedron signal vaults; click to discover
  - **Node Builder:** Deploy octahedron sovereign nodes on a 3D hex-grid
  - **Adriana Cipher:** Solve glyph-sequence puzzles in floating 3D chamber
- **VTX Rewards:** `mint_game_reward()` in `void_engine/vortex_wallet.py`; 50 VTX/24h cap
  - Base tiers: vault_discovered=0.5, glyph_solved=1.0, node_built=2.0, level_up=5.0
  - Equipment multiplier applied server-side via `get_earning_multiplier(user_id)`
- **Equipment Shop (game_inventory table):** 5 tiers of permanent gear purchased with VTX
  - Signal Array (15 VTX, 1.25x), Resonance Coil (35 VTX, 1.25x), Adriana Decoder (50 VTX, 1.5x)
  - Sovereign Rig (150 VTX, 1.75x), Void Core (500 VTX, 2.0x)
  - `spend_on_equipment()`, `get_inventory()`, `get_earning_multiplier()` in vortex_wallet.py
- **VTX Burn Mechanism:** All spending (features, equipment, unlocks) uses tx_type='burn'
  - Deflationary: burned VTX is permanently destroyed, reducing net circulating supply
  - `get_burn_stats()` function tracks total_burned, burn_events, net_supply, burn_rate
  - Public API: `GET /api/vortex/burn-stats`, `GET /api/vortex/chain-stats` (routes/financial.py)
  - Live burn ticker displayed on `/game/shop` page (auto-refreshes every 30s)
- **Game Stats columns on users table:** game_level, nodes_built, vaults_opened, glyphs_solved, total_game_vtx
- **API endpoints:** POST /api/game/reward, POST /api/game/equip, GET /api/game/inventory, GET /api/game/stats
- **Navigation:** "VOID Game" gold link in engine nav and landing nav; "Shop ◆" button in game topbar
- **Ledger:** Rewards use tx_type='mint_game'; spends use tx_type='burn'

## PEACE Flywheel Blueprint (Task #23)
- **Route:** `/peace/flywheel` — `routes/peace.py` blueprint (`peace_bp`)
- **Template:** `templates/peace_flywheel.html`
- **SVG Blueprint:** `static/peace_flywheel.svg` — true-scale 60mm disc, printable on A4
  - Outer circle with 60mm diameter label
  - Two centre string holes (⌀6mm, 20mm apart) with callout labels
  - Three concentric sound-hole rings: inner (16×⌀1.2mm, r10, green), mid (12×⌀2mm, r16, gold), outer (8×⌀3mm, r22, purple)
  - Crosshair drilling alignment guide; PEACE watermark; ring guide dashed circles
- **Page Sections:**
  - SVG blueprint display + download link (standalone SVG file)
  - Material & string specification panel (hardwood/acrylic/brass, thickness, silk string 1.2m)
  - How-to-spin 5-step phirki method panel
  - Frequency reference table (conceptual tones at ~200/400/700 RPM per ring)
  - Blueprint legend (ring colour key)
- **Linked from:**
  - `templates/sovereign.html` — Genesis Kit section (id="genesis-kit-section")
  - `templates/marketplace.html` — PEACE token economy hero section

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

## GriDul Rumble Decoder — Adriana SCL Module (Task #24)
- **Route:** `GET/POST /gridul/rumble` — in `routes/gridul.py` (`gridul_bp`)
- **Template:** `templates/gridul_rumble.html`
- **Public, no login required, no data saved, deterministic from input**
- **Entropy Classifier:** Rule-based Python function `_classify_entropy()` — scores words against three sets:
  - Social/power words (governance, network, economy) → gold domain
  - Sensory/physical words (earth, water, body, root) → teal aqua domain
  - Geometric/abstract words (void, spiral, fractal, ratio) → purple vortex domain
  - Equal spread (< 0.15 ratio spread) → "resonance" domain
- **Glyph selection:** Deterministic SHA-256 hash of input text, offset into domain-specific glyph pool
- **Sovereign Poem:** 3-glyph chain (Entity → Condition → Action) derived from hex seed segments using AdrianaResonance GLYPHS ontology
- **Share link:** URL-encoded `?q=` param — anyone opening the link sees the same decode
- **Animations:** CSS ripple rings, glyph glow-pulse, typewriter poetic decode reveal
- **Mobile:** `navigator.vibrate([100, 50, 200])` on reveal
- **Landing page:** GriDul `gridul.html` updated with Rumble card (Pillar 04/04) and nav link

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