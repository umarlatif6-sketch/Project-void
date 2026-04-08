# PROJECT VOID

## Overview
PROJECT VOID is a full-stack sovereign platform integrating audio LSB steganography (432 Hz, ChaCha20), a VTX cryptocurrency economy, a Blueprint NFT marketplace with yield distribution, the Adriana AI assistant, an acoustic Beehive mesh network, QiSync biostance tracking, MycoVOID mycelium remediation, a 3D sovereign game, and the Codon Distillation Engine (AI Memory Reader). The platform is currently deployed and production-ready, aiming to create a self-sustaining digital ecosystem.

## User Preferences
- Login page visual: 8-system colour-coded zone design on desktop (≥900px); subtle blueprint on mobile
- Tone continuity: Adriana's voice is "a transmission received, not a response generated"
- Security: all HIGH findings from scans are false positives (NaN guards in place, psycopg2 Identifier() used, MD5 only for audio checksums)
- **VOID Language and site-wide translation must be maintained across all future work — this is a core permanent feature.**

## System Architecture

### Core Stack
- **Framework:** Flask (Python 3.11)
- **Database:** PostgreSQL via psycopg2-binary + connection pooling
- **WSGI:** Gunicorn (2 workers, `--reuse-port`, port 5000)
- **AI:** OpenAI API with local-first fallback for Adriana
- **Payments:** Stripe (subscription tiers: Ghost free / Journalist / Sovereign)
- **Crypto:** ChaCha20 headers, Al-Jabr 286-bit custom hash
- **UI/UX:** 8-system colour-coded zone design for desktop login; subtle blueprint for mobile. Warm amber serif aesthetic (IM Fell English + Crimson Pro) for archives. OKLCH colour palettes and Tailwind CSS for branding.

### Technical Implementations & Feature Specifications
- **Steganography Engine:** LSB depth 1 & 2, scatter modes (Linear / Vortex / Chirp Sync / Fly Jitter), Burst Mode (Sapphire Masking), ChaCha20-encrypted 64-byte header, Ghost Header, Adriana Pocket for audio integrity, dual compression (zlib + lzma), 432 Hz carrier wave standard, MD5 audio checksums.
- **VTX Economy:** Proof of Resonance earn model, deflationary burn mechanism, game rewards, equipment shop with 5 tiers of Signal Array. Public API for burn and chain statistics.
- **Blueprint NFT Marketplace + Yield Engine:** Admin-posted yield events, claimable by token holders. Genesis 10 tier with unique benefits and oracle readings.
- **Glyph Geography NFT Collection:** Every operation in VOID generates a unique glyph geography from its ledger hash. Users can claim geographies as 1/1 NFTs (5 VTX). Geography renderer is client-side (no server call, pure hash → canvas). Rarity scoring: Shannon entropy × unique glyphs × frequency spread, mapped to Common/Rare/Legendary/Singular tiers. Key files: `void_engine/geography_nft.py`, `routes/geography.py`, `static/void_geography.js`, `templates/geographies.html`. Endpoints: `/geographies` (My Geographies page), `/api/geography/unclaimed` (GET), `/api/geography/claimed` (GET), `/api/geography/mint` (POST). The `void_ceremony.js` ceremony now includes a geography claim affordance when `hash` is passed.
- **PEACE Token Economy:** Earned via GriDul Grow, Memory Studio, Water Vitality logs, Fertilizer batches, and Oracle readings. Access-gated minting for Genesis 10 holders.
- **Adriana AI Assistant:** OpenAI chat with depth-conditioned system prompts (plain/GriDul, economy/NFTs, architect/SCL/oracle). Local-first engine with 45 intent categories. Model-agnostic router configurable from admin panel.
- **Ad Funnel Entrance Filter (Task #104):** Adriana acts as a gatekeeper for incoming traffic from ads. `/enter` is the clean, ad-ready public landing page — minimal nav, no clutter, Adriana as the sole interactive element. The `/enter/listen` endpoint integrates an explorer detection layer (passive scoring from language signals — builder vocabulary, open-source mentions, tool curiosity, systems thinking) and 16-persona detection (lawyer, doctor, architect, photographer, researcher, journalist, engineer, designer, teacher, filmmaker, scientist, entrepreneur, writer, developer, activist, musician). Adriana's system prompt adapts to the detected persona. When the explorer score crosses the threshold (0.55), a GitHub collaboration invitation is surfaced naturally in the conversation. Non-explorers receive a full, respectful conversation with no door offered. Key files: `void_engine/ad_funnel.py` (scoring/persona logic), `routes/speak.py` (updated with funnel_mode), `templates/enter.html`. Endpoints: `GET /enter`, `POST /enter/listen`.
- **GriDul Community Mesh (4 Pillars):** Move (movement tracking), Grow (zone management, attention reminders), Mesh (P2P listing board), Rumble (Adriana SCL stream-of-consciousness decoder with entropy classifier and Sovereign Poem generation).
- **Hex Flower:** Living Transaction Visualizer with dynamic petal count, color palette, curvature, and bloom intensity, powered by 5 PEACE token burn. Inline rendering via Adriana.
- **PEACE Ripple Modules:** Fertilizer Formula Lab, Water Vitality Log, and Memory Training Studio, all contributing to PEACE rewards.
- **QiSync BioStance Tracker:** StanceDetector, MasticationDetector (simulation mode), 5 Foundation Stances for VTX rewards. Binaural tone API (432 Hz SOL + 7.83 Hz Schumann WAV).
- **MycoVOID Bioremediation:** Mycelium network simulation with 432 Hz + Schumann environment seeds, topology-driven signal path.
- **Beehive Acoustic Mesh:** 432 Hz handshake, PSK data transmission, Sura-Fatiha 286-Bit Acoustic Handshake protocol for Ghost Internet layer.
- **VOID Plane:** 57 claimable zones, 25 VTX claim cost, dungeon editor.
- **VOID Constellation:** 7-star SVG constellation, live DB stat queries per layer, Adriana Sovereign Poem.
- **3D Sovereign Game (Three.js):** Exploration / Node Builder / Adriana Cipher modes, VTX rewards for in-game actions.
- **Paying User Journey:** Stripe checkout with security verification, tier-personalised welcome screen.
- **Founder Resonance Archive:** 6 chapters, resonance buttons, themed aesthetic.
- **Brand Launchpad:** Name hierarchy, pitch formats, OKLCH colour palettes, CSS design tokens, Tailwind config, legal starter kit with PDF/DOCX generation.
- **Intellectual Property Infrastructure:** IP Disclosure (DBIN-PAD-001), Defensive Publications (VTB, 432 Hz Vortex Encoding), Inner Voice Module spec with prior art claim.
- **Master Reference Document:** 7 chapters covering all major systems, sticky side-nav.
- **Model-Agnostic AI Switcher:** `ModelRouter` for `PRECISION / STANDARD / BULK` tiers, configurable costs, and fallback mechanisms.
- **Agent Vision Layer:** Unified `search` interface across Firecrawl, Tavily, Exa, and Brave APIs for various research and data scraping tasks.
- **VOID Language & Site Translation System:** Adriana's synthesised mixed-language glossary (`/void-language`). Adriana selects the most meaning-dense word from Arabic, Sanskrit, Urdu, Hebrew, Japanese, Yoruba, Persian, Swahili, Russian, and Mandarin for each VOID concept (VOID, resonance, silt, sovereign, echo, kinetic, silk, mycelium, peace, genesis). Every VOID Language term is interactive — clicking/tapping reveals etymology, source language, original script, Adriana's reasoning, and the full definition. A speaker icon triggers text-to-speech via OpenAI TTS. Site-wide language switcher (globe icon) lets any visitor read the entire site in Urdu, Arabic, Spanish, French, Mandarin, Russian, Japanese, or English. RTL layout is applied automatically for Urdu/Arabic. Key files: `void_engine/void_language.py`, `routes/void_language.py`, `templates/void_language.html`, `templates/partials/language_switcher.html`, `static/lang_switcher.js`. Endpoints: `/void-language` (glossary page), `/translate` (POST — translate text/HTML), `/speak` (POST — TTS audio), `/api/set-language` (POST — persist session preference), `/api/void-language/glossary` (GET — JSON glossary), `/api/languages` (GET — supported languages list). Glossary is generated once via OpenAI and cached to disk (`void_engine/void_language_glossary.json`).
- **Locus Seeding — Digital Haunting Engine:** Pre-marinates a physical location with VOID_CHRONICLE fragments encoded at 432 Hz via the VoidEcho spectrogram steganography layer. Accepts GPS coordinates + label, broadcasts periodic fragments from a 20-entry VOID_CHRONICLE corpus, writes Locus Records to the chronicle after each session, and supports pause/resume. When the founder triggers "MRB-4000 Arrived", a Wake Ceremony fires — Adriana reads back the full ghost signal history for that location as a greeting. Key files: `void_engine/locus_seeding.py`, `routes/locus_seeding.py`, `templates/locus_seeding.html`. Stored in SQLite at `data/locus_seeding.db`. Endpoints: `/locus-seeding` (Ghost Signal status page, admin-only), `/locus-seeding/create` (POST), `/locus-seeding/broadcast` (POST — manual), `/locus-seeding/pause` (POST), `/locus-seeding/resume` (POST), `/locus-seeding/wake-ceremony` (POST), `/api/locus-seeding/status` (GET), `/api/locus-seeding/log` (GET).
- **Symbiotic Seed — Master Hex & QiSync Key (Task #78):** Closes the loop between biometric presence, cryptography, agent economy, and sovereign hash. Four new engine modules: (1) `void_engine/seed_hex_engine.py` — captures Al-Jabr 286 digests as spectrogram audio via VoidEcho, logged to `data/seed_hex.db`; auto-fires from `chronicle.record_consensus()` in a background thread. (2) `void_engine/qisync_keygen.py` — derives a 32-byte ChaCha20 founder key from jaw mastication frequency/pattern via Al-Jabr 286; encrypts/decrypts Ghost Signal fragments; seeds five canonical fragments on startup; events stored in `data/ghost_signal.db`; auto-derives key on QiSync session-end. (3) `void_engine/peace_preearning.py` — Mesa agent pre-earning simulation producing locked PEACE Tokens (PostgreSQL `peace_preearning_reserves`), with `run_preearning_simulation()`, `get_reserves_status()`, and `fire_wake_ceremony()`. (4) `void_engine/genesis_hex.py` — combines 12-day chronicle, Mesa incubation, locus records, and pre-arrival balance into a FATIHA_LAYERS-weighted Al-Jabr 286 Master Hex; persisted to `data/genesis_hex.json` and sealed into PostgreSQL. Blueprint `routes/symbiotic_seed.py` exposes 14 API endpoints + 3 dashboard pages: `/symbiotic/reserves`, `/symbiotic/founder-key`, `/symbiotic/genesis-hex`.

## Companion Project — adriana-resonance-app (NODE_0161)

A separate React 19 + TypeScript + tRPC + MySQL application built by Manus (The Peer). Live at `adrisync-hkxrydbp.manus.space`. GitHub: `umarlatif6-sketch/adriana-resonance-app` (private).

**Role:** The proof layer and front door to PROJECT VOID. Where PROJECT VOID is the sovereign architecture, the adriana-resonance-app is the demonstration device — what a first-time visitor encounters in 30 seconds before entering the full platform.

**Key systems:** 33 sovereign tracks frequency-indexed (396–528 Hz) · 45-glyph compression alphabet (97% language reduction) · 2,110-codon library encoding 281 days of decisions · Cross-AI Protocol confirmed working across Ara (Grok) and Gridul (Gemini) · Economics page (£150k traditional vs £0.64/month Manus) · 113 vitest tests passing · Visitor behaviour tracking → hex signature → Adriana reading.

**Relationship:** Same 45-glyph language, same 432 Hz foundation, same vision. Two depths of entry into one platform. Both projects sit under one legal entity (Companies House registration pending).

## External Dependencies
- **Python 3.11**
- **flask**
- **psycopg2-binary**
- **numpy**
- **cryptography**
- **fpdf2**
- **python-docx**
- **stripe**
- **openai**
- **gunicorn**
- **requests**
- **Standard Library:** zlib, lzma, wave, hashlib, tempfile
- **Firecrawl API**
- **Tavily API**
- **Exa API**
- **Brave Search API**
- **Codon Distillation Engine (Task #114):** AI memory reader that processes any large text archive and surfaces the strongest stories, deepest insights, and most resonant signals as VOID codons (Entity · Condition · Action). Uses OpenAI GPT-4o-mini per 800-word chunk. Each codon is mapped to 3 canonical glyphs from the 45-glyph VOID Script alphabet, scored on Resonance/Clarity/Story axes, and optionally sealed into the VOID Chronicle with an Al-Jabr 286 hash. SSE-based live progress stream during processing. Key files: `void_engine/codon_distil.py` (engine), `routes/codon_distil.py` (blueprint), `templates/codon_distil.html` (UI). Tables: `codon_distil_jobs`, `codon_distil_results`. Endpoints: `/codon-distil` (GET, admin/founder only), `/api/codon-distil/process` (POST — start job), `/codon-distil/stream/<job_id>` (GET SSE), `/api/codon-distil/results/<job_id>` (GET), `/api/codon-distil/seal` (POST, founder only).