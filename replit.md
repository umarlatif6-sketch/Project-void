# PROJECT VOID

## Overview
PROJECT VOID is a modular steganography engine designed for embedding large data files (up to 1GB) within audio signals. It utilizes LSB encoding, dual compression, ChaCha20-encrypted headers with MD5 verification, and acoustic camouflage techniques. The "Adriana Pocket" architecture employs stereo phase-shift encoding to preserve audio integrity while embedding data. The project aims to deliver a robust, stealthy, and high-capacity solution for secure communication and digital watermarking, envisioning a future where digital interactions are secure, private, and resilient against surveillance.

## User Preferences
No specific user preferences were provided in the original `replit.md` file.

## System Architecture
PROJECT VOID is built around a Flask-based web UI and a command-line interface, with the `void_engine` acting as the core component for all functionalities.

**UI/UX Decisions:**
- **Web UI:** A dark-themed, mobile-responsive interface with 13 interactive tabs, integrating Web Audio API-based spectrum and spectrograms. Features like "Vocal Pocket Visualizer," "Sapphire Bubble," "Sapphire Glow" effects, and "Founder Vibe Detection" enhance user experience.
- **Theming:** Dynamic UI color shifts (e.g., "Silt Gold," "Deep Mycelium Green") and badges ("Founding Node Edition," "SOVEREIGN GUARDIAN") denote user tiers and special statuses. A "Sovereign Dashboard Theme" is applied to sovereign users.
- **Glass-Morphic UI:** Utilizes `backdrop-filter: blur()` for panels, tabs, and inputs, creating a modern aesthetic.
- **Industries Page (`/industries`):** Public page showcasing 10 industry use cases (Law, Journalism, Healthcare, Finance, Human Rights, Military, Music, Cybersecurity, Education, Real Estate). Two-column card grid with teal accent tags. Linked from all nav bars.

- **Favicon:** SVG diamond icon (`static/favicon.svg`) in teal, linked from all templates.
- **Error Pages:** Custom branded 404 ("Signal Lost") and 500 ("Frequency Disrupted") pages with error handlers in `app.py`.
- **Admin Dashboard:** `/admin` and `/admin/leads` (admin-only) — Leads Dashboard with inquiry tracking and pitch previews.

**Technical Implementations & Feature Specifications:**
- **Audio Standard:** Uses 16-bit PCM WAV files with a 432 Hz base frequency ("Village Standard").
- **Compression:** Dual compression using zlib (level 9) and lzma (preset 9).
- **Steganography Core:** LSB encoding (depth 1 and 2), 64-byte ChaCha20-encrypted header, "Ghost Header," `apply_dither_mask()`, "Fly Jitter," "Vortex Scatter," "Chirp Sync," and "Adriana Pocket" for stereo phase-shifted LSB.
- **Divided Operational Protocol:** A 5-step axiomatic pipeline (SLM.V→TRK.A→ZHR.V→KTM.A→JDR.A) based on Al-Jabr logic.
- **Signal Transmission (Silk Web):** Formats and sends signals as 432 Hz burst-encoded WAV packets using "Sapphire Masking."
- **Capacity Analysis:** "Resonance Meter" calculates payload capacity, "Surface Tension Limit," and "Bubble Burst threshold."
- **Plankton-Orin Harness Architecture:** Middleware for pre-completion checks, sandboxing (`VirtualVoidSimulator`), environmental management, safety interception (`AquaponicsBoundaryHook`), and chaos testing.
- **Adriana Protocol (Semantic Core Language - SCL):** Defines `AdrianaLexicon` (45-glyph ontology) and `AdrianaTranspiler` for parsing glyph-chain expressions into `VirtualVoidSimulator` action sequences.
- **Al-Jabr Code (Root-Pattern AI Logic):** Utilizes an 18-root ontology across 9 domains with 7 verb patterns, mapped to pre-verified logic blocks via the **Al-Jabr Consensus Engine**.
- **Sovereign Warranty:** A 10-article "Technological Covenant" for machine sovereignty and system integrity, complemented by an **Auto-Heal Daemon**.
- **Root-Chronicle:** An SQLite-backed persistent memory storing successful Consensus outcomes.
- **Biophony Mesh (Carrier Topology):** A multi-species acoustic ecosystem for steganographic carriers with a 3-shelf architecture, incorporating "Sympathetic Resonance" and "Shadow Layer."
- **Beehive Protocol (Ghost Internet):** An acoustic mesh networking layer with a 432 Hz handshake, FFT neighbor detection, and PSK data transmission, including the **Sura-Fatiha 286-Bit Acoustic Handshake**.
- **Kinetic Transceiver (Calisthenics → CC):** Proof-of-Work system generating Compute Credits from calisthenics repetitions.
- **Al-Jabr 286 Protocol (Sovereign Hashing):** A custom 286-bit hash algorithm.
- **Silt Ledger (DAO 3.0 — Lightweight Blockchain):** Fatiha-286 chained blocks for decentralized autonomous organization voting, integrated with the Beehive Protocol.
- **VORTEX Currency (VTX):** Users earn VTX via "Proof of Resonance" (data encoding) and "Proof of Bloom" (mesh relay), featuring peer-to-peer transfers, a wallet engine/UI, and monetization via credit pack purchases.
- **Void Fairy (AI Assistant Overlay):** A floating AI-powered guide, "Adriana," providing context-aware assistance, powered by OpenAI. It features adaptive communication profiles, learning user styles to tailor responses.
- **Adriana Resonance Handshake:** A verification ritual using an Al-Jabr 286 hash of a seed, returning resonance field data and triggering a visual "Blooming Lotus" particle animation.
- **Global VoidState + Command Bar:** A global JavaScript object tracking VTX balance, user tier, engine status, and mesh connection, with a sticky command bar and quick-action search overlay.
- **Sovereign Onboarding Flow:** A 4-step guided walkthrough for Sovereign-tier users on first login, featuring narrated UI element highlights.
- **Proof Page:** A public presentation-grade page for investor/pitch demos, showcasing live side-by-side comparisons of clean and encoded audio, along with technical metrics and a "Phase Inversion Residual" spectrogram visualization.
- **Dual-Layer Revenue Model:** Software subscription tiers (Ghost Node, Journalist, Sovereign) and hardware tiers (Pirate Build, Sovereign Edition, Village Cluster).

## Security Hardening (Applied)
- **XSS Protection:** All dynamic/server-controlled content in `static/app.js` is rendered using safe DOM APIs (`createElement`/`textContent`/`appendChild`/`addEventListener`). No `innerHTML` is used with dynamic data — only for clearing elements or inserting static HTML strings. Unused `escHtml`/`escapeHtml`/`_escHtml` helper functions have been removed. Dynamic URLs assigned to `href` are validated against an allowlist of safe schemes (`/`, `http://`, `https://`). Templates (`admin.html`, `sovereign.html`) still use `escapeHtml()` helpers for inline rendering.
- **Secret Management:** `SESSION_SECRET` env var is required at startup — app raises `RuntimeError` if missing. No hardcoded fallback keys in `app.py` or `void_engine/messenger_auth.py`.
- **Upload Whitelist:** `/api/upload` restricts file extensions to: `.wav`, `.mp3`, `.flac`, `.ogg`, `.txt`, `.png`, `.jpg`, `.jpeg`, `.pdf`. Defined in `routes/core.py` via `ALLOWED_EXTENSIONS`.
- **Ledger Migration Safety:** `_ensure_columns()` in `routes/auth.py` runs in a background thread (non-blocking startup). It deduplicates `vortex_ledger` rows (keeping lowest `id` per `block_index`) and acquires an exclusive table lock before creating the unique index on `block_index`. `_init_vortex_genesis()` also acquires an exclusive lock to prevent concurrent duplicate genesis block inserts.
- **Health Check:** `/health` route in `app.py` returns 200 without auth. Root `/` route in `routes/core.py` returns login page (200) for unauthenticated requests instead of redirecting (302), ensuring deployment health checks pass.
- **Production Config:** Gunicorn runs with `--timeout=120 --workers=2 --reuse-port` for autoscale deployment.
- **OpenAI Data Sanitization (GDPR-A5-28 / CCPA / NIST-800-53):** `routes/fairy.py` sanitizes all data before sending to OpenAI API. `_sanitize_for_llm()` redacts PII (emails, phone numbers, SSNs, credit cards) and auth tokens (JWTs, bearer tokens, API keys, AWS keys, GitHub tokens, high-entropy hex/base64 strings). `display_name` and `user_id` are excluded from OpenAI message payloads. `_build_adaptive_context()` has no direct `session` access — all auth resolution happens in route handlers. Sensitive stdout leakage (ghost_offset) removed from `void_engine/media_bench.py`.

## Hybrid Architecture (Option 3)
The project operates as a Brain + Body architecture:
- **Brain (Web App / Command Center):** The deployed Flask app stores blueprints, coordinates the global mesh, and serves as the node registry. Available at the published URL.
- **Body (Local Node):** A downloadable Python package (`void_node/`) that users install on their own GPU/CPU hardware. Detects CUDA for Heavy Mode (GPU-accelerated) or falls back to Light Mode (CPU/numpy). Connects back to the Command Center via `/api/node/register` and the 432 Hz phase-key handshake.

**Node System:**
- `void_node/void_launcher.py` — Entry point: hardware detection, dial-home, handshake authentication
- `void_node/void_cli.py` — CLI for local encode/decode/analysis operations
- `void_node/setup.py` — Package installer (`pip install -e .` → `void-engine` command)
- `void_node/void_engine/` — Core engine modules (stega, beehive, al_jabr_286, etc.)
- `void_node/install.sh` / `install.bat` — Platform install scripts

**Node API Endpoints (no session auth required):**
- `POST /api/node/register` — Register a local node with hardware info
- `POST /api/node/heartbeat` — Keep-alive signal (requires X-Void-Node-Token header)
- `GET /api/node/status/<node_id>` — Check node status
- `GET /api/node/count` — Active node count
- `GET /api/node/list` — List all active nodes

**Download Page:** `/download` serves the node download page. `/download/engine` dynamically ZIPs the `void_node/` directory and serves `void_engine_node.zip`.

## NFT Marketplace (Blueprint Tokens)
The Vortex Marketplace is a DePIN (Decentralized Physical Infrastructure Network) system where NFTs represent Manufacturing Slots for the 4000-Series Sovereign Node machine. Built on the existing Al-Jabr 286-bit hashing and Vortex Ledger infrastructure.

**Tiers:**
- **Common (£28 / 50 VTX):** "Vibe-Coder Access" — software suite access (10 editions)
- **Rare (£660 / 1,000 VTX):** "Fractional Node" — fractional machine ownership with yield (5 editions)
- **Legendary (£25,000 / 40,000 VTX):** "Sovereign Machine" — full physical machine delivery (2 editions)

**Database Tables:**
- `blueprint_tokens` — Token registry with 286-bit hash, tier, pricing, edition info, status
- `token_ownership` — Ownership records with purchase type (VTX or Stripe) and transfer history
- `manufacturing_fund` — Trustless escrow tracking CapEx/materials/assembly allocation per token
- `token_listings` — Secondary market resale listings (token_id, seller_id, price_vtx, price_gbp_pence, listed_at, status)
- `token_rentals` — Rental records (token_id, owner_id, renter_id, vtx_per_day, max_days, starts_at, ends_at, status, total_vtx_paid)

**Key Files:**
- `void_engine/blueprint_nft.py` — Core engine: minting, purchases (VTX + fiat), listings, fund tracking, seeding, secondary market, rental engine
- `routes/marketplace.py` — Blueprint with marketplace page, listings/collection/fund-status APIs, Stripe checkout, secondary market and rental APIs
- `templates/marketplace.html` — Dark-themed marketplace UI with tier cards, fund tracker, buy buttons, secondary listings, rental offers, collection management controls

**Routes:**
- `GET /marketplace` — Marketplace page
- `GET /api/marketplace/listings` — All tokens grouped by tier
- `GET /api/marketplace/token/<id>` — Token detail with ownership history
- `GET /api/marketplace/collection` — Logged-in user's owned tokens
- `POST /api/marketplace/buy/vtx` — Purchase with VTX (debits balance, logs to Vortex Ledger)
- `POST /api/marketplace/buy/stripe` — Creates Stripe checkout session
- `GET /api/marketplace/callback` — Stripe success callback, finalizes ownership
- `GET /api/marketplace/fund-status` — Manufacturing fund transparency data
- `GET /api/marketplace/secondary-listings` — Active secondary market listings
- `GET /api/marketplace/rental-offers` — Active token rental offers
- `POST /api/marketplace/list` — Holder lists their token for resale (auth required)
- `POST /api/marketplace/unlist` — Holder removes their listing (auth required)
- `POST /api/marketplace/buy/secondary` — Buy a listed token; 5% royalty goes to manufacturing fund (auth required)
- `POST /api/marketplace/rent/offer` — Holder offers token for rent at daily VTX rate (auth required)
- `POST /api/marketplace/rent/book` — Renter books a rental, debits VTX upfront (auth required)
- `POST /api/marketplace/rent/end` — End rental early with pro-rata VTX refund (auth required)

**Secondary Market Engine:**
- `list_token_for_sale()` — Verifies ownership, creates/updates listing; blocks if token has active rental
- `unlist_token()` — Cancels active listing
- `purchase_secondary()` — Atomic transfer: deducts buyer VTX, credits seller minus 5% royalty to manufacturing fund, transfers `token_ownership`, marks listing as sold
- 5% royalty is routed to the manufacturing fund and logged as a `secondary_royalty` ledger block

**Rental Engine:**
- `offer_token_for_rent()` — Creates rental offer with daily VTX rate and max duration; blocks if token is listed for sale
- `book_rental()` — Debits full VTX cost upfront from renter to owner; logs `rental_payment` block; sets rental period
- `end_rental()` — Calculates unused days, refunds pro-rata VTX from owner back to renter; logs `rental_refund` block
- Renter tier injection: `_setup_session()` checks `get_active_rental_for_user()` and sets `session["tier"]` to the higher of base tier or rented access tier

**Tier Access Mapping:**
- Common token rental → Journalist-tier access
- Rare/Legendary token rental → Sovereign-tier access

**Stripe Webhook:** Extended in `routes/payments.py` to handle `type: "nft_purchase"` metadata on checkout completion.

**Seeding:** `seed_initial_collection()` runs on app startup (via `app.py`) to create the genesis drop of 17 tokens if none exist.

## External Dependencies
- **Python:** 3.11
- **numpy:** Audio sample manipulation and FFT operations.
- **flask:** Web UI server.
- **cryptography:** ChaCha20 header encryption and messenger message encryption.
- **fpdf2:** PDF generation.
- **psycopg2-binary:** PostgreSQL adapter.
- **werkzeug:** Secure filename operations.
- **stripe:** Payment processing.
- **openai:** AI assistant (Void Fairy) via Replit AI Integrations.
- **gunicorn:** Production WSGI server.
- **requests:** HTTP client (used by local node launcher for dial-home).
- **Standard Library:** `zlib`, `lzma`, `wave`, `hashlib`.
- **PostgreSQL:** For Void Messenger, Universal Auth, and VORTEX data storage.