# Claude Handoff for void-codon-library

Start here:

- [README.md](README.md)
- [PROOF.md](PROOF.md)
- [void_codon_library/catalog.py](void_codon_library/catalog.py)

## What This Package Is

`void-codon-library` is the standalone codon lookup layer extracted from Project VOID.

It is intentionally narrow. It packages:

- platform codons used across Project VOID system zones
- SCL-LBN codons used for the London-Bolton operator naming layer

It does not package the full runtime, routes, Chronicle, or packet security system.

## What You Can Verify Quickly

1. The package has a clean Python API in `void_codon_library/catalog.py`.
2. The package has a scoped proof document in `PROOF.md` tied to existing repo evidence.
3. The package has a minimal regression test in `tests/test_catalog.py`.

## Fast Validation

From `void-codon-library/` run:

```bash
/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py'
```

## The Main Positioning Line

This is the codon library artifact itself: the lookup layer, not the whole organism.

## If You Need the Repo-Level Evidence

Use these source files in the parent repo:

- `void_engine/void_codon_vocab.py`
- `SCL_LBN_PROTOCOL.md`
- `PROOF_OF_EFFICIENCY.md`
