# Project VOID Scripts Index

**Complete Catalog of 55 Scripts**

For full script contents see: [PROJECT_VOID_ALL_SCRIPTS_MANIFEST.pdf](PROJECT_VOID_ALL_SCRIPTS_MANIFEST.pdf)

## Tier Key

| Tier | Meaning |
|------|---------|
| 🟢 Active | Core operational — run regularly, do not remove |
| 🟡 Dormant | Useful but not running in current cycle — review before deleting |
| 🔵 Archive | One-off or exploratory — safe to ignore, keep for reference |

**Rule:** Before writing a new script, check if an existing one covers it. If a script hasn't been run in 30 days and is not 🟢, move it to 🔵.

---

## Quick Navigation

- [Abyss Bio-Hybrid](#abyss-bio-hybrid)
- [Adriana Language](#adriana-language)
- [Build & Integration](#build--integration)
- [Chronicle & History](#chronicle--history)
- [Data Ingestion](#data-ingestion)
- [Health & Monitoring](#health--monitoring)
- [LBN Codex](#lbn-codex)
- [ORYX & Repair State](#oryx--repair-state)
- [Shell Scripts](#shell-scripts)
- [Testing & Validation](#testing--validation)
- [Utilities & Tools](#utilities--tools)
- [VOID Core](#void-core)

---

## Abyss Bio-Hybrid

**Count:** 2 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `abyss_compare_2012_2026.py` | Python | 🟢 Active | Monte Carlo 2012 vs 2026 conductivity simulation with confidence intervals |
| `abyss_f1_confidence.py` | Python | 🟡 Dormant | F1-specific confidence model — framework ready, not yet calibrated |

## Adriana Language

**Count:** 2 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `adriana_rank_and_trigger.py` | Python | 🟢 Active | Ranks glyph signals and triggers responses in the 45-glyph receiver system |
| `adriana_translate.py` | Python | 🟢 Active | Translates input through Adriana 432 Hz language layer |

## Build & Integration

**Count:** 9 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `build_ecosystem_resonance_graph.py` | Python | 🟡 Dormant | Builds graph of resonance relationships across ecosystem nodes |
| `build_integration_web.py` | Python | 🟡 Dormant | Constructs integration dependency web between VOID components |
| `build_resonance_weaver_baseline.py` | Python | 🟡 Dormant | Establishes baseline for resonance weaver calibration |
| `build_team_state_card.py` | Python | 🔵 Archive | One-off team state snapshot builder |
| `game_world_construction_10m.py` | Python | 🔵 Archive | 10-minute world construction exploratory run |
| `icc_three_hour_world_rebuild.sh` | Shell | 🟡 Dormant | ICC 3-hour world rebuild cycle shell runner |
| `public_source_to_ecosystem_selective.py` | Python | 🟡 Dormant | Selectively ingests public sources into ecosystem graph |
| `story_world_to_ecosystem_selective.py` | Python | 🔵 Archive | Maps story world structure to ecosystem — exploratory |
| `wikipedia_to_ecosystem_selective.py` | Python | 🟡 Dormant | Selective Wikipedia-to-ecosystem ingestion (filtered) |

## Chronicle & History

**Count:** 5 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `build_story_world_chronicle.py` | Python | 🔵 Archive | Builds narrative chronicle from story world data |
| `chronicle_autofill_forward_threads.py` | Python | 🟡 Dormant | Auto-fills forward thread entries in VOID_CHRONICLE.md |
| `chronicle_close_guard.py` | Python | 🟢 Active | Guards chronicle from premature session closure — run at session end |
| `chronicle_gap_completion.py` | Python | 🟡 Dormant | Fills temporal gaps in chronicle entries |
| `chronicle_research_closure.py` | Python | 🟡 Dormant | Closes open research threads in chronicle |

## Data Ingestion

**Count:** 4 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `generate_synthetic_wikipedia.py` | Python | 🔵 Archive | Generates synthetic Wikipedia-style articles for training data |
| `ingest_wikipedia.sh` | Shell | 🔵 Archive | Shell wrapper for Wikipedia ingestion pipeline |
| `monitor_wikipedia_pipeline.py` | Python | 🔵 Archive | Monitors Wikipedia ingestion run status |
| `wikipedia_to_knowledge_tree.py` | Python | 🟡 Dormant | Converts Wikipedia articles into knowledge tree structure |

## Health & Monitoring

**Count:** 1 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `heartbeat_probe.py` | Python | 🟢 Active | Probes node heartbeat — confirms system is alive and responding |

## LBN Codex

**Count:** 3 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `batch_closure_lbn_1_5.py` | Python | 🟡 Dormant | Batch closes LBN codon cycles 1–5 |
| `lbn_language_selector_sim.py` | Python | 🟢 Active | Simulates language pair selection (German/Turkish primary, Dutch/Turkish fallback) |
| `lbn_three_hour_pack_builder.py` | Python | 🟢 Active | Builds 3-hour runtime packs for LBN agent/hub routing |

## ORYX & Repair State

**Count:** 2 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `check_oryx_repair_state_smoke_artifact.py` | Python | 🟢 Active | Checks ORYX repair state smoke test artifacts — Day 2 wedge validation |
| `oryx_repair_state_smoke.py` | Python | 🟢 Active | Runs ORYX repair state smoke test — primary proof of audit-filtering wedge |

## Shell Scripts

**Count:** 2 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `autopilot_cycle.sh` | Shell | 🟡 Dormant | Runs an automated cycle without manual intervention |
| `post-merge.sh` | Shell | 🟢 Active | Post-merge hook — runs after git merge to maintain repo state |

## Testing & Validation

**Count:** 3 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `full_stack_convergence_test.py` | Python | 🟢 Active | End-to-end convergence test across full VOID stack |
| `mycelium_health_check.py` | Python | 🟡 Dormant | Validates mycelium scaffold layer — relevant when Abyss testing resumes |
| `smoke_test.sh` | Shell | 🟢 Active | Fast smoke test — run first after any deployment or re-entry |

## Utilities & Tools

**Count:** 15 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `agent_broadcast_books.py` | Python | 🟡 Dormant | Broadcasts book-format knowledge packages to agent network |
| `agent_memory_carrier_pack.py` | Python | 🟡 Dormant | Packages agent memory for carrier transport across sessions |
| `beehive_demo.py` | Python | 🔵 Archive | Beehive mesh protocol demonstration — reference only |
| `cockroach_agent_selector_01.py` | Python | 🟡 Dormant | First CockroachDB-aware agent selector |
| `cockroach_agent_selector_robustness.py` | Python | 🟡 Dormant | Robustness variant of CockroachDB agent selector |
| `domain_goldmine.py` | Python | 🔵 Archive | Domain discovery/scoring exploratory tool |
| `drift_scan.py` | Python | 🟢 Active | Scans for system drift — flags divergence from baseline state |
| `migrate.py` | Python | 🟢 Active | Database migration runner |
| `packet_key_manager.py` | Python | 🟢 Active | Manages packet signing keys — part of Al-Jabr 286 security layer |
| `resonance_select.py` | Python | 🟡 Dormant | Selects resonance patterns for active routing |
| `reverse_backlog_full_closure.py` | Python | 🔵 Archive | One-off full backlog closure run |
| `run_all_promised_next_steps.py` | Python | 🔵 Archive | Batch executor for forward thread promises — superseded by void_reentry.sh |
| `run_startup_migrations.py` | Python | 🟢 Active | Runs all startup migrations on boot |
| `update_seed.py` | Python | 🟢 Active | Updates VOID_SEED_DIGEST.md from current system state |
| `vocal_resonance_pipeline.py` | Python | 🟡 Dormant | Processes vocal resonance input through signal pipeline |

## VOID Core

**Count:** 7 scripts

| Script | Type | Tier | Purpose |
|--------|------|------|---------|
| `project_void_cost_bundle.py` | Python | 🟢 Active | Calculates and bundles cost metrics for VOID operations |
| `void_aggregate.py` | Python | 🟢 Active | Aggregates VOID node outputs into unified state |
| `void_peer_cycle.sh` | Shell | 🟢 Active | Runs peer benchmarking cycle against A2A / ADK / AutoGen |
| `void_proofboard.sh` | Shell | 🟢 Active | Generates proofboard artifacts for KPI validation |
| `void_reentry.sh` | Shell | 🟢 Active | One-command re-entry checklist — run this first after any break |
| `void_roi_calculator.py` | Python | 🟡 Dormant | ROI calculator for VOID deployment scenarios |
| `void_swarm_interface.py` | Python | 🟡 Dormant | Interface layer for swarm-mode agent coordination |

---

## Summary

| Tier | Count |
|------|-------|
| 🟢 Active | 18 |
| 🟡 Dormant | 22 |
| 🔵 Archive | 15 |
| **Total** | **55** |
