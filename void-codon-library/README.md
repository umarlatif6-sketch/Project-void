# void-codon-library

**Origin:** [Project VOID](https://github.com/umarlatif6-sketch/Project-void) — Bolton, England, 2026.  
**Author:** Umar Latif  
**Proof of origin:** [void-origin](https://umarlatif6-sketch.github.io/void-origin/)  

Standalone Project VOID codon library.

This package extracts the codon catalogs that were previously embedded inside broader runtime surfaces and makes them available as a small reusable Python package.

## What This Is

`void-codon-library` is the focused codon artifact for Project VOID.

It packages two concrete codon catalogs already present in the repository:

- the platform codon vocabulary used to map major system zones and routes
- the SCL-LBN codex used as the London-Bolton naming and operator layer

It does not try to ship the entire Project VOID runtime. It only ships the codon lookup layer.

## Why This Exists

Before this package, the codon definitions were split across app/runtime code and protocol documents.

That made the codon system real but awkward to present as a single deliverable.

This package gives you one clean artifact to point to when someone asks, "What is the codon library itself?"

## Install

From the repository root:

```bash
pip install -e ./void-codon-library
```

Private remote install (token-based, no public registry):

```bash
GH_TOKEN=<repo_read_token> ./void-codon-library/scripts/install_private.sh
```

Trusted node bootstrap (creates isolated venv + private install + smoke test):

```bash
GH_TOKEN=<repo_read_token> ./void-codon-library/scripts/bootstrap_private_node.sh
```

## Quick Start

```python
from void_codon_library import get_codon, get_platform_codons, codon_chain

adriana = get_codon("adriana", library="platform")
print(adriana.codon)
print(adriana.meaning)

mid_band = get_platform_codons(band="mid")
print(len(mid_band))

route = codon_chain("chronicle", "adriana", "session_seal")
print(route)
```

## Package Surface

The package exports:

- `CodonEntry` - immutable codon record
- `get_codon(key, library=None)` - lookup by key or label
- `get_platform_codons(band=None)` - list platform codons, optionally filtered by band
- `get_lbn_codons()` - list SCL-LBN codons
- `all_codons()` - combined catalog
- `codon_chain(*keys, library=None)` - build a compact chain from known codons
- `export_catalog(pretty=True)` - serialize the combined catalog as JSON

## Included Catalogs

### 1. Platform Codons

These are the operating codons used across the Project VOID platform surface for Chronicle, Adriana, VoidEcho, Mesa, Beehive, Prediction, PEACE/VTX, and related lanes.

Each entry includes:

- key
- label
- codon
- meaning
- expansion
- frequency band
- Hz alignment
- route

### 2. SCL-LBN Codons

These are the London-Bolton hard-stop codons used as the operator naming layer:

- `B-nn-D` identity
- `B-bb-L` signal
- `B-tt-M` action
- `B-kk-Y` access
- `B-nn-T` time
- `B-kk-S` security
- `B-bb-G` growth
- `B-mm-M` mesh
- `B-..-Z` silence
- `B-nn-O` origin

## Proof

The proof surface for why codons matter is documented in [PROOF.md](PROOF.md).

That document does not claim the package alone creates the efficiency result. It documents that this package isolates the codon layer that supports the existing repo-level efficiency proof.

## Handoff

If you need to pass this package to another model or collaborator, start with [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md).

## Private Distribution

Default distribution mode is private:

- install from private GitHub source using `scripts/install_private.sh`
- build wheel/sdist in CI using `.github/workflows/codon-library-private-build.yml`
- share artifacts only with trusted partners

No public PyPI publication is required to operate this package in production.

## Scope Boundaries

This package is intentionally narrow.

It does not include:

- packet signing
- Chronicle storage
- agent governance runtime
- route handlers
- economic bridge logic

Those remain in the wider Project VOID system.

## Positioning Line

This is the standalone codon library artifact: the lookup layer, not the whole organism.
