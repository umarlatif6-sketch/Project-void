# Project VOID Workspace Instructions

## SCL-LBN Phonetic Shift

Project VOID now carries an internal codex layer called SCL-LBN: London-Bolton-Node.

When the user frames work through the B-stop, London/Bolton hard-stop phonetics, or LBN codons, treat that as a naming and interpretation layer for Project VOID rather than as noise or malformed English.

Use this sequence:

1. Translate the user's B-shift framing into concrete system intent.
2. Preserve the codex names when they carry architectural meaning.
3. Keep operational outputs rigorous and technically explicit.
4. Do not flatten the codex into generic product language unless the user asks for that.

## LBN Seed Codons

- `B-nn-D`: identity, node, origin body, founder-bound anchor
- `B-bb-L`: signal, vibe, road-state, doubled resonance
- `B-tt-M`: action, move, execution pulse
- `B-kk-Y`: key, access, signature gate
- `B-nn-T`: time, cycle, calendar anchor
- `B-kk-S`: security check, fail-closed verification
- `B-bb-G`: growth, spread, mycelial expansion
- `B-mm-M`: mesh passage, cross-node movement
- `B-..-Z`: silence, hidden layer, steganographic pause
- `B-nn-O`: origin, field record, founding signal

## Guardrails

- Treat SCL-LBN as a sovereign language layer, ontology, and operator shorthand.
- Do not claim that phonetic shift alone provides cryptographic security.
- Real security remains in manifest verification, Ed25519 signatures, freshness windows, sector authorization, and fail-closed packet handling.
- If the user asks for code changes, prefer additive implementation that preserves current packet security primitives.

## Active Pair Lock

Current language pair lock for agent-to-agent codon routing:

- Primary pair: `German + Turkish`
- Fallback pair: `Dutch + Turkish`

Three-hour runtime artifacts:

- Project mode pack: `data/lbn_three_hour_pack.project.json`
- Project mode payloads: `data/lbn_agent_payloads.project.json`
- Standalone mode pack: `data/lbn_three_hour_pack.standalone.json`
- Standalone mode payloads: `data/lbn_agent_payloads.standalone.json`

If these files exist, treat them as the active codon routing reference for agent/hub communication.

Live runtime switches:

- `VOID_LBN_MODE=project|standalone`
- `VOID_LBN_ACTIVE_ROUTE=primary|fallback`
- `VOID_LBN_VALIDATE=true|false`
- `VOID_LBN_PAYLOAD_PATH=/absolute/path/to/override.json`

## Response Style

- Preserve the Project VOID naming language.
- Translate codex phrases into implementation details when writing code, docs, or tests.
- If a packet or route is described in LBN terms, mirror the codex name in comments or docs only when it improves operator clarity.

## Note for Collaborators

If you are new to the SCL-LBN layer, read `SCL_LBN_PROTOCOL.md` at the repo root first.
It contains the full translation table (B-nn-D = identity/node, B-kk-S = security check, etc.).
The underlying Python code is unchanged. LBN is a naming and documentation layer only — not a code syntax.