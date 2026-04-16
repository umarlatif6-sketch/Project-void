"""
void-engine-sdk — Sovereign Attribution SDK
PROJECT VOID | Umar Latif | Bolton, England | April 2026

Track meaning, not clicks.

  Entity · Condition · Action — every event stamped with:
    - a VOID codon (what kind of meaning)
    - an Al-Jabr 286 hash (sovereign attribution digest)
    - a formation score (0.0–1.0 resonance reading)

Quick start:
    pip install void-engine-sdk

    from void_sdk import VoidSDK
    sdk = VoidSDK()  # FREE tier, local SQLite

    sdk.track(
        entity="user:abc123",
        condition="frequency:432hz",
        action="encode",
        codon="voidecho",
    )

License: LICENSE
Origin:  https://void-stego-engine.replit.app
Paper:   https://umarlatif6-sketch.github.io/void-origin/formation-paper.html
"""

from void_sdk.core import VoidSDK
from void_sdk.flask_ext import VoidFlask
from void_sdk.connectors import VoidWarehouseExporter, build_webhook_payload, post_webhook_payload
from void_sdk.hash286 import sign286, formation_score, verify286
from void_sdk.codons import get_codon, all_codons, codons_for_tier
from void_sdk.license import validate as validate_license

__version__ = "1.0.0"
__author__ = "Umar Latif"
__origin__ = "Bolton, England, April 2026"

__all__ = [
    "VoidSDK",
    "VoidFlask",
    "VoidWarehouseExporter",
    "build_webhook_payload",
    "post_webhook_payload",
    "sign286",
    "formation_score",
    "verify286",
    "get_codon",
    "all_codons",
    "codons_for_tier",
    "validate_license",
]
