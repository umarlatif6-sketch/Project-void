# Governance Index

This page is the single entry point for Project VOID governance rails.

## Governance Layers

1. RecursiveMAS governance
- [RECURSIVE_MAS_GOVERNANCE.md](RECURSIVE_MAS_GOVERNANCE.md)
- Contract: [../manifest/recursive_mas_contract.json](../manifest/recursive_mas_contract.json)
- Protocol: [../core/recursive_mas/AGENT_CONTRACT.md](../core/recursive_mas/AGENT_CONTRACT.md)

2. Seed + Chronicle governance
- [SEED_CHRONICLE_GOVERNANCE.md](SEED_CHRONICLE_GOVERNANCE.md)
- Contract: [../manifest/continuity_chordon_contract.json](../manifest/continuity_chordon_contract.json)
- Protocol: [../core/recursive_mas/SEED_CHRONICLE_PROTOCOL.md](../core/recursive_mas/SEED_CHRONICLE_PROTOCOL.md)

3. Timeline Passport governance
- [TIMELINE_PASSPORT_GOVERNANCE.md](TIMELINE_PASSPORT_GOVERNANCE.md)
- Contract: [../manifest/timeline_passport.json](../manifest/timeline_passport.json)
- Protocol: [../core/recursive_mas/TIMELINE_PASSPORT.md](../core/recursive_mas/TIMELINE_PASSPORT.md)

## Runtime Loaders

- Agent contract loader: [../core/recursive_mas/contract_loader.py](../core/recursive_mas/contract_loader.py)
- Continuity contract loader: [../core/recursive_mas/continuity_loader.py](../core/recursive_mas/continuity_loader.py)

## Operator Rule

If a session is continuity-sensitive, start with Timeline Passport, then apply Seed + Chronicle governance, then execute under RecursiveMAS governance gates.
