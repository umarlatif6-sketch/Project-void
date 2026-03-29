# PROJECT VOID

## Overview
PROJECT VOID is a full-stack sovereign platform built around audio LSB steganography (432 Hz, ChaCha20), a VTX cryptocurrency economy, Blueprint NFT marketplace with yield distribution, the Adriana AI assistant, an acoustic Beehive mesh network, QiSync biostance tracking, MycoVOID mycelium remediation, and a 3D sovereign game. The platform is deployed and production-ready.

## User Preferences
- Login page visual: 8-system colour-coded zone design on desktop (≥900px); subtle blueprint on mobile
- Tone continuity: Adriana's voice is "a transmission received, not a response generated"
- Security: all HIGH findings from scans are false positives (NaN guards in place, psycopg2 Identifier() used, MD5 only for audio checksums)

---

## System Architecture

### Core Stack
- **Framework:** Flask (Python 3.11)
- **Database:** PostgreSQL via psycopg2-binary + connection pool (`void_engine/db_pool.py`)
- **WSGI:** Gunicorn (2 workers, `--reuse-port`, port 5000)
- **AI:** OpenAI API via `routes/fairy.py` with local-first fallback (`void_engine/adriana_local.py`)
- **Payments:** Stripe (subscription tiers: Ghost free / Journalist / Sovereign)
- **Crypto:** ChaCha20 headers, Al-Jabr 286-bit custom hash

### Blueprint/Route Map
| Route prefix | Blueprint | Purpose |
|---|---|---|
| `/` | core | Landing, index, tiers, proof page |
| `/auth` | auth | Login, register, logout, DB migrations |
| `/admin` | admin | Admin dashboard, yield events, model router |
| `/api/fairy` | fairy | Adriana AI chat + greeting |
| `/api/vortex` | financial | VTX burn stats, chain stats |
| `/marketplace` | marketplace | Blueprint NFT marketplace + yield API |
| `/game`, `/game/shop` | game | 3D sovereign game + equipment shop |
| `/gridul` | gridul | GriDul community mesh (4 pillars) |
| `/qisync`, `/qisync/memory` | qisync | Biostance tracker + Memory Studio |
| `/mycovoid` | mycovoid | Mycelium remediation network |
| `/peace/flywheel` | peace | PEACE coin flywheel blueprint |
| `/hex-flower` | hex_flower | Hex Flower — Living Transaction Visualiser (5 PEACE burn per generation) |
| `/genesis`, `/genesis/oracle` | genesis | Genesis 10 Blueprint NFTs + oracle |
| `/plane` | plane | VOID Plane star map + territory claim |
| `/crystallization` | crystallization | Seven-layer constellation map |
| `/archive` | archive | Founder Resonance Archive |
| `/brand`, `/brand/content`, `/brand/legal` | brand | Brand Launchpad + legal documents |
| `/prior-art` | prior_art | Defensive publication registry |
| `/ip-disclosure` | admin | Prior Art Disclosure Document (PDF) |
| `/inner-voice` | inner_voice | Silent Speech Module spec page |
| `/void-master-document` | void_master_document | Master Reference Document |
| `/sovereign-node` | sovereign_node | MRB-4000 hardware sovereign node |

---

## Feature Modules (by task order)

### Steganography Engine (core)
- LSB depth 1 & 2, scatter modes: Linear / Vortex / Chirp Sync / Fly Jitter
- Burst Mode: Sapphire Masking for short-text encoding
- ChaCha20-encrypted 64-byte header, Ghost Header anti-forensics
- Adriana Pocket: stereo phase-shift LSB for audio integrity preservation
- Dual compression: zlib (level 9) + lzma (preset 9)
- 432 Hz carrier wave standard; MD5 audio checksum (not auth — leave as-is)

### VTX Economy
- Proof of Resonance earn model; deflationary burn mechanism
- `void_engine/vortex_wallet.py`: mint_game_reward, spend_on_equipment, get_burn_stats
- Equipment shop: Signal Array → Void Core (5 tiers, 1.25x–2.0x multiplier)
- Public API: `GET /api/vortex/burn-stats`, `GET /api/vortex/chain-stats`

### Blueprint NFT Marketplace + Yield Engine
- `void_engine/blueprint_nft.py`: post_yield_event(), get_pending_yield(), claim_yield()
- Yield events posted by admin; claimed by token holders
- Genesis 10 tier: 10 founding Blueprint tokens, oracle readings, PEACE minting
- Marketplace UI with collection page, yield claim UI

### PEACE Token Economy
- Earned through: GriDul Grow sessions, Memory Studio, Water Vitality logs, Fertilizer batches, Oracle readings
- Access-gated: Grow/Oracle PEACE minting requires Genesis 10 holder check
- Flywheel Blueprint: `/peace/flywheel` — physical 60mm PEACE coin printable SVG

### Adriana AI Assistant
- `routes/fairy.py`: OpenAI chat with depth-conditioned system prompts
- Depth levels: 1=plain/GriDul, 2=economy/NFTs, 3=architect/SCL/oracle
- Local-first engine: `void_engine/adriana_local.py` — 45 intent categories, 97% local hit rate
- Auto-open widget on `/welcome`, `/launch`, `/` — greets by tier
- Model-agnostic: `void_engine/aljabr_transpiler.py` ModelRouter — configurable per tier from admin panel
- Widget added to 20+ templates; secure link rendering (regex whitelist before creating anchors)

### GriDul — Community Mesh (4 Pillars)
- **Move** (`/gridul/move`): movement session tracking, VTX rewards
- **Grow** (`/gridul/grow`): zone management, attention reminders, PEACE rewards for Genesis holders
- **Mesh** (`/gridul/mesh`): P2P listing board, inbound request panel
- **Rumble** (`/gridul/rumble`): Adriana SCL stream-of-consciousness decoder (public, no login)
  - Entropy classifier: social/sensory/abstract/resonance domains
  - Sovereign Poem: 3-glyph chain (Entity → Condition → Action)
  - Share link via `?q=` URL param

### Hex Flower — Living Transaction Visualiser (Task #44)
- `void_engine/hex_flower.py`: `parse_hex()` — petal count (1–12 from 12 validation signals), colour palette (byte distribution + resonance state), curvature (Shannon entropy), bloom intensity, plain-English translation
- `routes/hex_flower.py`: `/hex-flower` (page), `/api/hex-flower/generate` (token burn + spec), `/api/hex-flower/preview` (no-cost inline)
- `templates/hex_flower.html`: standalone page with live SVG renderer, petal dot indicators, shareable link generation, shared-view mode (no token cost)
- `void_engine/vortex_wallet.py`: `burn_peace_for_hex_flower()` — burns 5 PEACE from supply, audited in `hex_flower_log` table
- Adriana inline detection: hex regex in `fairy_ask` → flower spec appended to API response as `hex_flowers[]` → `renderInlineHexFlower()` in `void_fairy.js`
- Shared flower links: `/hex-flower?h=<hex>&u=<sig>` render free, bypass token burn
- 3 new local intents in `adriana_local.py`: hex_flower_what, hex_flower_cost, hex_flower_share
- Platform map and system prompt updated with Hex Flower knowledge

### PEACE Ripple Modules (Task #22)
- **Fertilizer Formula Lab** (`/gridul/fertilizer`): C:N ratio scoring, batch CRUD, marketplace, leaderboard
- **Water Vitality Log** (`/gridul/water`): pH/EC/temp/mineral scoring, drinkability check, canvas timeline chart
- **Memory Training Studio** (`/qisync/memory`): 3 text scenes, timed absorption + fuzzy recall scoring, PEACE rewards

### QiSync BioStance Tracker
- CSI Backend: StanceDetector, MasticationDetector (simulation mode when hardware absent)
- 5 Foundation Stances + mastication tracking → VTX rewards
- Binaural tone API: `GET /api/qisync/tone` returns 432 Hz SOL + 7.83 Hz Schumann WAV

### MycoVOID Bioremediation
- Mycelium network simulation: angrysky56/mycelium_network vendored (core only)
- AdvancedMyceliumNetwork with 432 Hz + Schumann environment seeds
- Real topology-driven strongest_signal_path (greedy activation edge walk)
- `GET /api/mycovoid/status` (login required); anonymous fallback: "Login required"

### Beehive Acoustic Mesh
- 432 Hz handshake, PSK data transmission
- Sura-Fatiha 286-Bit Acoustic Handshake protocol
- Ghost Internet layer / P2P overlay

### VOID Plane — Star Map & Territory (`/plane`)
- 57 named claimable zones, irregular polygon SVG overlay
- Claim cost: 25 VTX; resonance score 0–100 from DB activity
- Dungeon editor: zone owners name and publish dungeon descriptions
- Seven constellation stars map to crystallization layers

### VOID Constellation (`/crystallization`)
- 7-star SVG constellation tracing a sovereign face/glyph outline
- Live DB stat queries per layer; Adriana Sovereign Poem from crystallization sentence
- Hover tooltips, click navigation to each system

### Mesa 3.x Agent Simulation
- `village_sim.py`: ZoneAgent (player/node/adriana), harness + adriana_transpiler hooks
- `POST /api/village/simulate/<zone_id>` (login required, owner-authz enforced)

### 3D Sovereign Game (`/game`)
- Three.js: Exploration / Node Builder / Adriana Cipher modes
- VTX rewards: vault_discovered=0.5, glyph_solved=1.0, node_built=2.0, level_up=5.0
- 50 VTX/24h cap; equipment multiplier applied server-side
- SRI integrity hash on Three.js CDN script

### End-to-End Paying User Journey (Task #27)
- Stripe checkout: verifies `cs.status == "complete"` AND `payment_status == "paid"`
- Anti-impersonation: session user matched against checkout metadata user_id
- Post-payment welcome screen (`/welcome`): tier-personalised with action cards
- Landing page CTA: "Claim Your Sovereignty" → `/login`

### Founder Resonance Archive (`/archive`)
- 6 chapters: The Mind / The Journey / The Faith / The Family / The Work / The Why
- Medallion Crest SVG; per-chapter resonance buttons (localStorage prevents double-vote)
- Warm amber serif aesthetic (IM Fell English + Crimson Pro)
- Atomic file writes via tempfile+os.replace; VALID_SECTIONS allowlist

### Brand Launchpad (`/brand`)
- Name hierarchy: VOID → Adriana / Al-Jabr / MycoVOID / GriDul / QiSync / VTX+PEACE
- 3 pitch formats (one-sentence / paragraph / page)
- 3 OKLCH colour palettes with Active Direction indicator
- CSS design tokens block (dark + light mode variants)
- Tailwind v3 config block (theme.extend.colors + fontFamily, darkMode)
- Legal Starter Kit: Mutual NDA + Research Collaboration Agreement (Common Paper / Bonterms)
- PDF generation: fpdf2; DOCX generation: python-docx (`void_engine/brand_docs.py`)

### Intellectual Property Infrastructure
- **IP Disclosure** (`/ip-disclosure`, admin only): DBIN-PAD-001 formal disclosure, Al-Jabr 286 seal hash
- **Defensive Publications** (`/prior-art`): VTB (Vibe-Triggered Biomineralization) + 432 Hz Vortex Encoding
- **Inner Voice Module** (`/inner-voice`): Silent Speech — Ag/AgCl electrode + ADS1299 + ESP32-S3 spec, prior art claim
- All prior art pages are public, crawlable, dated 29 March 2026

### Master Reference Document (`/void-master-document`)
- 7 chapters in flowing prose, one per crystallization layer
- Sticky side-nav with color-coded chapter dots; print/PDF via window.print()
- Covers all major systems, links to constellation + 3D game

### Model-Agnostic AI Switcher
- `void_engine/aljabr_transpiler.py`: ModelRouter class — PRECISION / STANDARD / BULK tiers
- Admin UI in `admin_market.html`: configure model/base_url/cost per tier
- Cost tracker: cumulative totals, per-tier breakdown, recent 20 calls logged
- Fallback: if tier endpoint fails → retry once with precision model

---

## Key Files

| File | Purpose |
|---|---|
| `app.py` | Flask app factory, blueprint registration, startup init |
| `routes/__init__.py` | All blueprint imports + registrations |
| `void_engine/blueprint_nft.py` | Yield engine: post/claim/get_pending yield |
| `void_engine/vortex_wallet.py` | VTX economy: mint, burn, spend, earn, game rewards |
| `void_engine/adriana_local.py` | Local intent matcher (45 categories, 97% hit rate) |
| `void_engine/aljabr_transpiler.py` | ModelRouter + cost tracker + AdrianaTranspiler |
| `void_engine/al_jabr_286.py` | 286-bit custom hash algorithm |
| `routes/fairy.py` | Adriana AI chat, depth profiling, greeting, widget |
| `routes/gridul.py` | GriDul: Move/Grow/Mesh/Rumble + PEACE session endpoints |
| `routes/plane.py` | VOID Plane territory map |
| `routes/crystallization.py` | Seven-layer constellation |
| `routes/archive.py` | Founder archive + resonance counter |
| `routes/admin.py` | Admin dashboard + yield + model router + IP disclosure |
| `routes/payments.py` | Stripe checkout + webhook |
| `static/void_fairy.js` | Adriana widget (auto-open, typewriter, link renderer) |
| `templates/login.html` | 8-system colour-coded zone login page |
| `static/peace_flywheel.svg` | True-scale A4 PEACE coin drill blueprint |

---

## Agent Vision Layer (Task #37)
- **Module:** `void_engine/agent_vision.py` — unified `search(query, mode)` interface across four APIs
- **Modes:**
  - `firecrawl` — scrapes URLs to clean Markdown for VOID Plane constellation nodes
  - `tavily` — multi-step research for PEACE Token credibility verification
  - `exa` — semantic (neural) search for Sovereign Realm acoustic steganography research
  - `brave` — independent news feed for Mesa Village agents
- **Routes:** `routes/agent_vision.py` — `GET /admin/agent-vision`, `POST /api/agent-vision/search`, `GET /api/agent-vision/status`
- **Admin UI:** `/admin/agent-vision` — live API status cards, request counts, test query interface
- **Keys:** `FIRECRAWL_API_KEY`, `TAVILY_API_KEY`, `EXA_API_KEY`, `BRAVE_SEARCH_API_KEY` (Replit Secrets)


## External Dependencies
- **Python 3.11**
- **flask** — web framework
- **psycopg2-binary** — PostgreSQL adapter
- **numpy** — audio processing
- **cryptography** — ChaCha20 encryption
- **fpdf2** — PDF generation (≥2.8.5)
- **python-docx** — DOCX generation
- **stripe** — payment processing
- **openai** — Adriana AI
- **gunicorn** — production WSGI server
- **requests** — HTTP client
- **Standard Library:** zlib, lzma, wave, hashlib, tempfile

## Database Tables (key)
- `users` — accounts, tiers, game stats
- `vortex_ledger` — VTX transaction log
- `blueprint_tokens` — NFT records
- `yield_events`, `yield_claims` — yield distribution engine
- `genesis_oracle_events` — oracle submissions
- `peace_balance` — PEACE token balances
- `void_plane_zones` — territory claims
- `ai_model_router_config`, `ai_model_cost_log` — model switcher
- `gridul_sessions`, `gridul_zones`, `gridul_mesh_listings` — GriDul modules
- `water_vitality_logs`, `fertilizer_batches`, `memory_sessions` — PEACE ripples
- `fairy_profiles` — Adriana depth profiles
- `game_inventory` — equipment shop
