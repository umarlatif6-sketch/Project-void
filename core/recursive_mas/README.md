# RecursiveMAS

The Cognitive Head of Project VOID.

This layer executes recursive multi-agent inference using latent-space routing between agents to bypass text bottlenecks and preserve inference speed.

## Canonical Integration

All agents should bootstrap from the same contract artifacts:

- [AGENT_CONTRACT.md](AGENT_CONTRACT.md)
- [agent_profile.template.json](agent_profile.template.json)
- [../../manifest/recursive_mas_contract.json](../../manifest/recursive_mas_contract.json)
- Python loader: [contract_loader.py](contract_loader.py)

## Continuity Integration (Seed + Chronicle)

Use these assets for continuity-safe re-entry and codon alignment:

- [SEED_CHRONICLE_PROTOCOL.md](SEED_CHRONICLE_PROTOCOL.md)
- [TIMELINE_PASSPORT.md](TIMELINE_PASSPORT.md)
- [continuity_loader.py](continuity_loader.py)
- [../../manifest/continuity_chordon_contract.json](../../manifest/continuity_chordon_contract.json)
- [../../manifest/timeline_passport.json](../../manifest/timeline_passport.json)

## Agent Bootstrap Flow

1. Load `manifest/recursive_mas_contract.json`.
2. Verify `contract == recursive_mas.v1`.
3. Register/validate local profile shape against `agent_profile.template.json`.
4. Check readiness via `/api/adriana/mesh/readiness`.
5. Prefer `latent_embedding.v1`; fall back to codon bridge only when required.
6. Persist artifacts and resonance events for every completed run.
