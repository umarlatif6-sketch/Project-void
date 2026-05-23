# Seed + Chronicle Governance

## Purpose

Protect continuity across cold starts by governing how agents consume Seed and Chronicle rails.

## Canonical Contract

- Human: `core/recursive_mas/SEED_CHRONICLE_PROTOCOL.md`
- Machine: `manifest/continuity_chordon_contract.json`
- Loader: `core/recursive_mas/continuity_loader.py`

## Governance Controls

1. Deterministic read order for continuity sources.
2. Forward Thread inheritance as required session input.
3. Session-close Chronicle entry requirement.
4. Seed digest alignment check when ontology changes.
5. Codon labels must remain recoverable to plain engineering meaning.

## Operating Rule

No continuity-sensitive execution should start without inherited Forward Thread context and source alignment.

## Audit Expectations

- Source rails are present and readable.
- Session close includes an explicit Forward Thread.
- Continuity contract keys remain complete.
