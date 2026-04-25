# Project VOID — Manchester IP Clinic · One-Page Handout
**Date:** April 24, 2026 · **Founder:** Umar Latif · **Contact:** [see intake packet]

---

## What Is Project VOID?

A multi-layer sovereign data transport system with three distinct product layers:

1. **Z-Axis Carrier** — deterministic LSB video steganography over MKV/FFV1, encrypted with ChaCha20, verified by Al-Jabr 286 checksum. Payload survives compression artefacts via parity reconstruction and frame-position mapping.
2. **VOID Node** — encrypted P2P packet routing layer with packet freshness windows, Ed25519 signing, and fail-closed handling. Sector authorisation controls per-node access scope.
3. **Cockroach System** — dual-track resilience engine: (a) physical sanitation network simulation, (b) agent-archetype command pilot for robustness under adversarial conditions.

---

## Top 5 IP Assets (Evidence-Backed)

| # | Asset | Evidence |
|---|-------|----------|
| 1 | Al-Jabr 286 hash function | `void_engine/al_jabr_286.py` — novel construction, proprietary carve-out in LICENSE |
| 2 | Z-Axis steganographic transport | `void_engine/z_axis_video.py` + `void_engine/stega.py` — working roundtrip demo |
| 3 | VOID Node packet protocol | `void_node/` — freshness windows, Ed25519, fail-closed; documented in `VOID_AI_PACKET.md` |
| 4 | Cockroach dual-track resilience | `void_engine/cockroach_sanitation.py` + `cockroach_agent_control.py` — 4 passing tests |
| 5 | SCL-LBN Codon Routing Layer | `VOID_SEED_CODONS.md` — sovereign operator language ontology |

---

## What Is NOT Claimed

- No patent filed yet — these are trade secret / copyright positions pending formal filing
- `openclaw/` is MIT-licensed upstream (openclaw org) — not founder-origin IP
- ORYX creator engine is a separate sub-project, not in scope for this filing session
- 54 GB roundtrip not yet independently verified — lab proof only

---

## Ownership

- All VOID-origin code: **Umar Latif**, sole founder
- License: **BSL 1.1** with explicit proprietary carve-outs for `al_jabr_286.py` and `stega.py`
- Repository: `github.com/umarlatif6-sketch/Project-void`

---

## Three Questions for the Clinic

1. Can Al-Jabr 286 be filed as a provisional patent on a novel hash construction, or is it a trade secret?
2. Does BSL 1.1 adequately protect steganographic transport pending formal IP registration?
3. What is the minimum filing path to establish priority date on Z-Axis + VOID Node today?
