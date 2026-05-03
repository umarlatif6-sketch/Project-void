# Proof for void-codon-library

## What This Proves

This document shows that the standalone codon library is a real extraction of the codon layer already used in Project VOID, and that the codon layer is tied to an existing efficiency proof in the repository.

## Verified Source Surfaces

The package is grounded in these existing repo artifacts:

- `void_engine/void_codon_vocab.py` - platform codon vocabulary used across system zones and routes
- `SCL_LBN_PROTOCOL.md` - London-Bolton codex definitions and operator rules
- `PROOF_OF_EFFICIENCY.md` - repo-level token efficiency proof

## Efficiency Claim Already Present in Repo

Project VOID already records this efficiency baseline:

| Metric | Baseline | Codon-compressed | Reduction |
|---|---|---|---|
| Token count to orient a new agent | 75,155 tokens | ~300 tokens | 250x |

That proof is documented in `PROOF_OF_EFFICIENCY.md` and presented again in `static/void_foundation_live.html`.

## What This Package Contributes

This package does not invent a new compression claim.

It contributes a cleaner artifact boundary:

1. The codon definitions are separated from the larger runtime.
2. The codon catalogs can be imported directly as a reusable library.
3. The lookup layer can be presented independently from the broader SDK, routes, or governance system.

## Why This Matters

Before this extraction, the codon system was real but distributed:

- part of runtime code
- part of protocol documents
- part of broader SDK surfaces

That made it harder to point to "the codon library" as a single deliverable.

Now there is a focused package that exposes the codon layer directly.

## Claim Boundary

Safe claim:

`void-codon-library` is the standalone packaged codon lookup layer for Project VOID, extracted from existing repo sources and aligned to the existing codon efficiency proof.

Unsafe claim:

`void-codon-library` alone proves all Project VOID performance, governance, or economic claims.

The package is one real artifact inside the larger system, not the entire system.
