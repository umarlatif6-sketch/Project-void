# PROJECT VOID

## Overview
PROJECT VOID is a full-stack sovereign platform integrating audio LSB steganography (432 Hz, ChaCha20), a VTX cryptocurrency economy, a Blueprint NFT marketplace with yield distribution, the Adriana AI assistant, an acoustic Beehive mesh network, QiSync biostance tracking, MycoVOID mycelium remediation, and a 3D sovereign game. The platform is currently deployed and production-ready, aiming to create a self-sustaining digital ecosystem.

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
- **PEACE Token Economy:** Earned via GriDul Grow, Memory Studio, Water Vitality logs, Fertilizer batches, and Oracle readings. Access-gated minting for Genesis 10 holders.
- **Adriana AI Assistant:** OpenAI chat with depth-conditioned system prompts (plain/GriDul, economy/NFTs, architect/SCL/oracle). Local-first engine with 45 intent categories. Model-agnostic router configurable from admin panel.
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