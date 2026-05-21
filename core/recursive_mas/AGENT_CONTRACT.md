# RecursiveMAS Agent Contract

This document is the canonical integration contract for all agents in Project VOID.

## Purpose

Ensure every agent can participate in the same cognitive architecture without relying on ad hoc per-script assumptions.

## Contract Version

- Contract: `recursive_mas.v1`
- Latent protocol: `latent_embedding.v1`
- Fallback protocol: `codon_text_bridge.v1`

## Required Agent Fields

Every agent profile must declare:

- `agent_id`
- `role`
- `input_schema`
- `output_schema`
- `capabilities`
- `safety_mode`
- `latency_target_ms`
- `freshness_window_s`

## Standard Roles

- `router`
- `research`
- `voice`
- `critic`
- `planner`
- `auditor`
- `operator_bridge`

## Message Modes

1. Primary: latent-space embedding envelope
2. Secondary: codon envelope (compressed symbolic bridge)
3. Last resort: plain text envelope

Agents should always prefer mode 1 when available.

## Runtime Entry Points

- Mesh profiles: `/api/adriana/mesh/profiles`
- Mesh run: `/api/adriana/mesh/run`
- Mesh eval: `/api/adriana/mesh/eval`
- Mesh readiness: `/api/adriana/mesh/readiness`
- Artifact listing: `/api/adriana/mesh/artifacts`
- Health: `/api/mycelium/health`

## Fail-Closed Rules

- Refuse execution if contract version mismatch is strict.
- Refuse execution if readiness is red.
- Refuse execution if freshness window is expired.
- Log rejection reason in resonance logs.

## Discovery Paths

- Machine-readable contract: `manifest/recursive_mas_contract.json`
- Human architecture overview: `README.md`
- Cognitive head docs: `core/recursive_mas/README.md`

## Minimal Bootstrap Sequence

1. Load machine-readable contract.
2. Verify supported contract version.
3. Pull active profile from mesh profile endpoint.
4. Run readiness check before first action.
5. Send/receive through latent envelope when available.
6. Persist result artifact and resonance event.
