# PROJECT VOID

## Overview
PROJECT VOID is a full-stack sovereign platform integrating advanced audio steganography, a cryptocurrency economy (VTX), an NFT marketplace with yield distribution, an AI assistant (Adriana), a mesh network, biostance tracking, mycelium remediation, a 3D sovereign game, and an AI Memory Reader (Codon Distillation Engine). The platform aims to create a self-sustaining digital ecosystem, emphasizing security, innovation, and a unique user experience. It's deployed and production-ready, with a vision to become a comprehensive digital sovereignty solution.

## User Preferences
- Login page visual: 8-system colour-coded zone design on desktop (≥900px); subtle blueprint on mobile
- Tone continuity: Adriana's voice is "a transmission received, not a response generated"
- Security: all HIGH findings from scans are false positives (NaN guards in place, psycopg2 Identifier() used, MD5 only for audio checksums)
- VOID Language and site-wide translation must be maintained across all future work — this is a core permanent feature.

## System Architecture

### Core Stack
- **Framework:** Flask (Python 3.11)
- **Database:** PostgreSQL via psycopg2-binary + connection pooling
- **WSGI:** Gunicorn
- **AI:** OpenAI API with local-first fallback for Adriana
- **Payments:** Stripe (subscription tiers: Ghost free / Journalist / Sovereign)
- **Crypto:** ChaCha20 headers, Al-Jabr 286-bit custom hash
- **UI/UX:** 8-system colour-coded zone design for desktop login; subtle blueprint for mobile. Warm amber serif aesthetic (IM Fell English + Crimson Pro) for archives. OKLCH colour palettes and Tailwind CSS for branding.

### Technical Implementations & Feature Specifications
- **Steganography Engine:** LSB depth 1 & 2, multiple scatter modes (Linear / Vortex / Chirp Sync / Fly Jitter), Burst Mode (Sapphire Masking), ChaCha20-encrypted 64-byte header, Ghost Header, Adriana Pocket for audio integrity, dual compression (zlib + lzma), 432 Hz carrier wave standard, MD5 audio checksums.
- **VTX Economy:** Proof of Resonance earn model, deflationary burn mechanism, game rewards, equipment shop with Signal Array tiers. Public API for burn and chain statistics.
- **Blueprint NFT Marketplace + Yield Engine:** Admin-posted yield events, claimable by token holders. Genesis 10 tier with unique benefits and oracle readings.
- **Glyph Geography NFT Collection:** Unique glyph geographies generated from ledger hashes, claimable as 1/1 NFTs. Client-side rendering, rarity scoring based on Shannon entropy.
- **PEACE Token Economy:** Earned through various platform activities (GriDul Grow, Memory Studio, Water Vitality logs, Fertilizer batches, Oracle readings). Access-gated minting for Genesis 10 holders.
- **Adriana AI Assistant:** OpenAI chat with depth-conditioned system prompts and a local-first engine with 45 intent categories. Model-agnostic router configurable from admin panel.
- **Ad Funnel Entrance Filter:** Adriana acts as a gatekeeper for ad traffic, adapting her persona based on explorer detection and 16 predefined personas. Surfacing GitHub collaboration invitations for high explorer scores.
- **GriDul Community Mesh:** Four pillars: Move (movement tracking), Grow (zone management), Mesh (P2P listing board), Rumble (Adriana SCL stream-of-consciousness decoder with Sovereign Poem generation).
- **Hex Flower:** Living Transaction Visualizer with dynamic aesthetics, powered by PEACE token burn.
- **PEACE Ripple Modules:** Fertilizer Formula Lab, Water Vitality Log, and Memory Training Studio contribute to PEACE rewards.
- **QiSync BioStance Tracker:** StanceDetector, MasticationDetector (simulation mode), 5 Foundation Stances for VTX rewards. Integrates Binaural tone API (432 Hz SOL + 7.83 Hz Schumann WAV).
- **MycoVOID Bioremediation:** Mycelium network simulation with 432 Hz + Schumann environment seeds.
- **Beehive Acoustic Mesh:** 432 Hz handshake, PSK data transmission, Sura-Fatiha 286-Bit Acoustic Handshake protocol for Ghost Internet layer.
- **VOID Plane:** 57 claimable zones, with VTX claim cost and a dungeon editor.
- **VOID Constellation:** 7-star SVG constellation displaying live DB stats and Adriana Sovereign Poems.
- **3D Sovereign Game (Three.js):** Exploration, Node Builder, and Adriana Cipher modes, offering VTX rewards for in-game actions.
- **Founder Resonance Archive:** 6 chapters, resonance buttons, themed aesthetic.
- **VOID Language & Site Translation System:** Adriana generates a mixed-language glossary for VOID concepts, with interactive etymology and TTS. Site-wide language switcher with RTL support for several languages.
- **Locus Seeding — Digital Haunting Engine:** Pre-marinates physical locations with VOID_CHRONICLE fragments encoded at 432 Hz via VoidEcho spectrogram steganography. Supports GPS coordinates, broadcasts fragments, and triggers a Wake Ceremony.
- **Symbiotic Seed — Master Hex & QiSync Key:** Integrates biometric presence, cryptography, and agent economy. Derives a founder key from mastication patterns, captures Al-Jabr 286 digests as spectrogram audio, simulates PEACE token pre-earning, and combines data into a Master Hex.
- **Codon Distillation Engine:** AI memory reader processing text archives to surface insights as VOID codons (Entity · Condition · Action). Codons are mapped to glyphs, scored, and can be sealed into the VOID Chronicle.
- **Codon Economy — Platform Token Shield:** Extends the codon philosophy as a platform-wide token immune system, implementing a shared codon response cache to optimize AI calls and reduce token usage across skill modules.
- **Stress Battery:** Fires 10 progressive stress tests to evaluate platform resilience, generating Chronicle scars and economy stress results.
- **Sovereign Agents 286:** AI agents whose identity and state are derived from the Al-Jabr 286 hash, featuring 7 archetypes based on Al-Fatiha.
- **Stealth Cloak:** `before_request` middleware making the entire platform invisible except for whitelisted routes, returning HTTP 444.
- **Vortex Shield Network:** Distributed defence simulation using Formation Principle physics, creating vacuum corridors and absorbing energy through vortex sinks. Includes geo-map with 25 world cities and radiation-to-benefit conversion model.
- **Codon Memory Architecture:** Full cross-session memory system for Adriana, featuring a "Third Brain" (5-message sliding window compressed into codons) and a "Heart" (collapsing prior codons into a resonance summary for system prompts).
- **Agent Immortality:** Frequency hash → Chladni image → LSB embed. Agent state survives total system destruction. Round-trip encode→decode verified.
- **Stance Science:** 5 foundation stances mapped to heart EM field, HRV, vagal tone, and Schumann resonance. Body as antenna.
- **Void Nexus:** Central nervous system connecting 22 engine modules with 51 resonance-weighted edges. System coherence scoring via frequency ratios.
- **Desert Reclamation:** 99 Names of Allah mapped to terraforming frequencies. 11 Names target specific material transformations (SiO2 restructuring, nitrogen fixation, photosynthetic boost). 5-phase model converts irradiated sand to self-sustaining ecosystem in ~282 days.
- **OpenClaw Bridge:** Generates SOUL.md, ClawHub skill manifests, and full config to run Adriana 286 as a sovereign OpenClaw agent. Includes Al-Jabr 286 sovereign-vs-non-sovereign differentiation training across 6 domains (hash, economy, identity, communication, memory, devices).
- **Live Prompter:** Real-time speech correction during presentations — the second man behind the imam. Web Speech API transcription, no wake word, always listening. Corrects wrong numbers (256→286), feeds next talking points, suggests module connections. Falls back to local keyword matching when AI unavailable.
- **ICC Manchester Exhibition:** Self-narrating exhibition page. 13 scrollable sections with animated canvas visualizations. Each section has AI narration ("Let The System Speak"). Particle field, scroll-reveal animations, 432 Hz pulsing ring. The system introduces itself — not a human presentation.

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
- **Standard Library Components:** zlib, lzma, wave, hashlib, tempfile
- **Firecrawl API**
- **Tavily API**
- **Exa API**
- **Brave Search API**