# Timeline Passport Governance

## Purpose

Govern timeline re-entry so agents can reconstruct active context with minimal token load and minimal drift.

## Canonical Contract

- Human: `core/recursive_mas/TIMELINE_PASSPORT.md`
- Machine: `manifest/timeline_passport.json`

## Stop-Gated Controls

1. Identity gate: mission and ontology anchor verified.
2. History gate: last five Chronicle entries mapped.
3. Codon gate: codon labels bound to technical meaning.
4. Safety gate: readiness/fail-closed posture confirmed.

If any gate fails, execution is paused and marked orientation-incomplete.

## Operating Rule

Timeline Passport is the default continuity bootstrap for normal sessions; full deep archive read is reserved for ontology-heavy or forensic sessions.

## Audit Expectations

- Passport sequence is used and recorded.
- Stop-gate outcomes are explicit.
- Output state card includes mission, inherited thread, security posture, route mode, and first action.
