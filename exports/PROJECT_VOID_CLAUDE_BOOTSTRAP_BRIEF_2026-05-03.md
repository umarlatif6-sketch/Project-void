# Project VOID Claude Bootstrap Brief

Purpose: give an external coding agent enough grounded context to work inside Project VOID without full conversational history.

## 1. What Project VOID Is

Project VOID is a sovereign sensing, translation, and physical-architecture system built around Al-Jabr 286 packet law, 432 Hz resonance discipline, and an SCL-LBN codex naming layer.

It is not just a software repo. It combines:

- environmental sensing
- wearable and conductive-thread systems
- operator translation logic
- physical supply-chain architecture
- simulation and machine-control bridges

The repo is public:

- https://github.com/umarlatif6-sketch/Project-void

## 2. Governing Rules

1. Preserve 286 wrapping and fail-closed behavior.
2. Preserve SCL-LBN names when they carry architectural meaning.
3. Treat metaphor as specification, then translate into rigorous implementation.
4. Prefer additive implementation over destructive rewrites.
5. Keep safety boundaries explicit for hardware, bio, and energy systems.

## 3. Core Doctrine Files

Start here in this order:

1. `MANUS_GITHUB_MASTER_DIRECTIVE.md`
2. `Project_Void_Comprehensive_Overview_V5.md`
3. `MASTER_PROTOCOL_1002.md`
4. `README.md`
5. `SCL_LBN_PROTOCOL.md`
6. `logic/avicenna_protocol.md`

Important companion files:

- `CODON_001.md`
- `SPRINT_10_DAY_ZTM.md`
- `ONBOARDING_SEED.md`
- `VOID_SEED.md`
- `VOID_SEED_CODONS.md`
- `VOID_SEED_DIGEST.md`
- `VOID_SIGNAL.md`
- `VOID_FORMATION_DOCUMENT.md`
- `VOID_VERACITY_PROTOCOL.md`
- `UNIFIED_SIMULATION_DIRECTIVE.md`

## 4. Main Technical Lanes

### A. Eye Lane: Google Earth Engine

Primary files:

- `void_engine/google_earth_engine.py`
- `routes/google_earth_engine.py`

Current implemented capabilities:

- NDVI snapshots
- GRACE water-table trend proxy
- anomaly threshold evaluation
- RFQ trigger logic for supply-chain shifts
- ion-resurrection simulation endpoint
- SWIR mineral overlay screening
- orchestration fan-out across Pakistan presets

Pakistan presets currently include:

- Lahore
- Islamabad
- Soan Valley
- Chagai
- Gilgit-Baltistan

Every major surface is intended to return a 286 sovereign envelope.

### B. Hand Lane: Silk / Conductive Thread / Wearables

Primary files:

- `infrastructure/supply_chain/conductive_thread_specs.json`
- `infrastructure/supply_chain/silk_supply_chain.md`
- `infrastructure/supply_chain/silk_water_resonance_whitepaper.md`
- `infrastructure/wearables/device_profile_schema.json`
- `infrastructure/wearables/WEEK1_BUILD_BLUEPRINT.md`
- `infrastructure/wearables/FIRMWARE_PACKET_SPEC.md`
- `void_engine/wearable/mycelium_adriana_translator.py`

Key idea:

- conductive traces in silk/skin/leather are treated as sovereign edge nodes, not generic wearables

Wearable runtime surfaces:

- `GET /api/wearable/device-profile-schema`
- `POST /api/wearable/ingest`
- `GET /api/wearable/audit?limit=50`

Wearable ingest is token-secured via `VOID_WEARABLE_INGEST_TOKEN`.

### C. Pulse Lane: Energy Resurrection

Primary files:

- `infrastructure/energy_systems/energy_resurrection_schematic.md`
- `infrastructure/energy_systems/ion_resurrection.py`
- `infrastructure/energy_systems/duracell_to_void_conversion_table.md`

Important boundary:

- the current module is simulation/planning only, not direct unsafe hardware actuation

API surface:

- `POST /api/energy/ion-resurrection/simulate`

### D. Ground Lane: Biological / Worm Logic

Primary file:

- `infrastructure/biological_systems/worm_grounding_protocol.md`

Use this as grounding and anomaly logic for bio-processing and circular infrastructure.

### E. Logic Lane: Adriana / Corpus / Fork Assimilation

Primary files:

- `void_engine/adriana_corpus.py`
- `void_engine/fork_integration.py`
- `routes/fork_integration.py`

What exists now:

- external fork indexing
- delta-pack generation for Adriana ingestion
- route registration for the fork integration surface

API surfaces:

- `GET /api/integrations/ai-agents/index`
- `GET /api/integrations/ai-agents/delta-pack`
- `POST /api/integrations/ai-agents/sync`

This lets Project VOID assimilate useful patterns from the external AI-agents fork instead of copying raw tutorial clutter directly into core logic.

## 5. Key Security / Safety Expectations

1. Fail closed on bad auth, bad packet shape, bad checksum, bad replay window, or unknown fields.
2. Keep packet wrapping and signature/freshness logic intact.
3. Do not introduce unsafe medical, electrical, or mining claims as factual certainty.
4. Treat mineral overlay as reconnaissance only, not reserve confirmation.
5. Treat ion resurrection as simulation/planning unless explicit safe hardware controls are added.

## 6. High-Value API Surfaces Already Present

### GEE / Operations

- `POST /api/gee/ndvi`
- `POST /api/gee/water-table-trend`
- `POST /api/gee/anomaly-thresholds`
- `POST /api/gee/rfq-state`
- `GET /api/gee/rfq-audit?limit=50`
- `POST /api/gee/mineral-overlay`
- `POST /api/gee/orchestrate-exploration`

### Wearables / Machine 4000 Bridge

- `GET /api/wearable/device-profile-schema`
- `POST /api/wearable/ingest`
- `GET /api/wearable/audit?limit=50`
- `POST /api/energy/ion-resurrection/simulate`

### Fork Assimilation / Adriana Strengthening

- `GET /api/integrations/ai-agents/index`
- `GET /api/integrations/ai-agents/delta-pack`
- `POST /api/integrations/ai-agents/sync`

## 7. What An External Agent Should Do First

1. Read the doctrine files listed in Section 3.
2. Read `README.md` for current operator-facing surfaces.
3. Read `void_engine/google_earth_engine.py` and `routes/google_earth_engine.py` to understand the existing integration style.
4. Read `void_engine/wearable/mycelium_adriana_translator.py` to understand how Project VOID turns raw signals into codon state and Machine 4000 payloads.
5. Read `void_engine/fork_integration.py` and `void_engine/adriana_corpus.py` to understand how external capability patterns are assimilated into Adriana-readable context.

## 8. What To Preserve When Making Changes

Preserve these concepts explicitly:

- 286 envelope
- base frequency 432 Hz
- warning lane 442 Hz
- SCL-LBN codon vocabulary
- RFQ logic linking environment to material procurement
- wearable token auth and packet validation
- additive physical-architecture docs for silk, wearables, energy, and biological grounding

## 9. What Not To Flatten

Do not rewrite Project VOID into generic startup language.

Keep these as real architectural layers, not decorative words:

- Eye
- Hand
- Pulse
- Ground
- Logic
- Land
- Flow
- Architect

Do not remove codon names when they improve operator clarity.

## 10. Practical Working Guidance

If you are extending the repo:

1. Prefer small additive patches.
2. Extend existing engines and routes instead of creating duplicate lanes.
3. Add focused tests for each new route or module.
4. Validate before push.
5. Keep docs and operator manifests aligned with implementation reality.

## 11. Short Repository Summary

Project VOID is a sovereign, packet-wrapped infrastructure stack that combines environmental sensing, wearable translation, conductive-thread physical systems, simulation-backed machine control, and doctrine-driven operator logic. The repo already contains live lanes for GEE sensing, RFQ procurement shifts, ion-resurrection simulation, wearable secure ingest, and external fork assimilation for Adriana strengthening.

This brief is the shortest serious bootstrap for an external coding agent.