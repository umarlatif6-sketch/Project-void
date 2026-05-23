# Seed + Chronicle Protocol

This protocol binds RecursiveMAS to continuity rails so every agent can re-enter Project VOID without intent drift.

## Canonical Sources

- `VOID_SEED_DIGEST.md` (compressed cold-start)
- `VOID_SEED.md` (full ontology and constraints)
- `VOID_CHRONICLE.md` (evolutionary record)
- `SCL_LBN_PROTOCOL.md` (codon ontology)
- `CODON_001.md` (sync packet)

## Re-entry Sequence

1. Read digest first for lane orientation.
2. Read full seed when ontology-sensitive work is in scope.
3. Read last five chronicle entries from newest backward.
4. Load codon map and bind plain technical labels to codon labels.
5. Start execution only after route, security, and continuity checks align.

## Recursive + Codon Synergy

- RecursiveMAS provides high-speed route/verify/critic loops.
- Codons provide compressed semantic anchors and stable ontology labels.
- Combined, they reduce handoff ambiguity and preserve intent under cold starts.

## Session Close Rules

- Add one chronicle entry before session close.
- Include a `Forward Thread` that the next session can inherit.
- If ontology changed, update seed digest active layer.

## Fail-Closed Posture

- Unknown contract version: stop.
- Missing source files: stop.
- Missing forward thread in session closure: mark incomplete.
