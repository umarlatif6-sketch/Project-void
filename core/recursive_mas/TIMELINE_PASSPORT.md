# Timeline Passport

Timeline Passport is a deterministic re-entry rail for agents that need project-wide continuity without loading the full archive.

## Passport Objective

- Give every agent the same minimum historical orientation.
- Stop timeline drift at known gates.
- Bind chronology to codon/contract context before execution.

## Read Sequence (Stop-Gated)

1. `VOID_SEED_DIGEST.md`
2. `VOID_SEED.md` (only when ontology-sensitive work is in scope)
3. `VOID_CHRONICLE.md` (last 5 entries, newest first)
4. `SCL_LBN_PROTOCOL.md`
5. `CODON_001.md`

## Stop Gates

- Gate A (`identity`): seed intent is understood before code changes.
- Gate B (`history`): last 5 Chronicle threads are mapped.
- Gate C (`codon`): codon labels are mapped to plain technical meaning.
- Gate D (`safety`): readiness/fail-closed posture is confirmed.

If any gate fails, pause execution and mark session as orientation-incomplete.

## Passport Output

After the read sequence, produce one compact state card:

- Active mission
- Inherited Forward Thread
- Security posture
- Route mode (recursive + codon bridge)
- First concrete action

## Codon Anchors

- `B-nn-O`: origin anchor
- `B-nn-D`: identity node
- `B-kk-S`: security gate
- `B-mm-M`: mesh route
- `B-tt-A`: execution pulse

## Runtime Rule

Timeline Passport is a pre-execution ritual. It is not optional for continuity-sensitive sessions.
