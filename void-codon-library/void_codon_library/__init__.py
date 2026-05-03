"""Standalone Project VOID codon library.

This package exposes the Project VOID codon catalogs as plain Python data with
small helper functions for lookup, filtering, and chaining.
"""

from .catalog import (
    CodonEntry,
    all_codons,
    codon_chain,
    export_catalog,
    get_codon,
    get_platform_codons,
    get_lbn_codons,
)

__all__ = [
    "CodonEntry",
    "all_codons",
    "codon_chain",
    "export_catalog",
    "get_codon",
    "get_platform_codons",
    "get_lbn_codons",
]
