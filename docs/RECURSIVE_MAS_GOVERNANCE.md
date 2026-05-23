# RecursiveMAS Governance

## Purpose

Define how the Cognitive Head is governed so recursive speed does not bypass safety, continuity, or provenance.

## Canonical Contract

- Human: `core/recursive_mas/AGENT_CONTRACT.md`
- Machine: `manifest/recursive_mas_contract.json`
- Loader: `core/recursive_mas/contract_loader.py`

## Governance Controls

1. Contract version gate (`recursive_mas.v1`) before execution.
2. Role validation against allowed roles.
3. Fail-closed posture for unknown contract/version mismatch.
4. Readiness check required before action loops.
5. Artifact persistence required after run completion.

## Operating Rule

Recursive loops may optimize route and latency, but cannot bypass readiness, freshness, or security gates.

## Audit Expectations

- Agent profile declares required fields.
- Route decisions are traceable to role + contract.
- Rejections are logged with explicit reason.
