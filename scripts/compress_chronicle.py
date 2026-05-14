"""
Chronicle Codon Compressor — Sovereign Efficiency Protocol
===========================================================
Reads the VOID_CHRONICLE.md, classifies each session entry into a
three-glyph Pure Codon using Adriana's local matching logic, and
outputs both the compressed codon chain and a JSON manifest.

Uses the REAL Al-Jabr 286 hash for formation sealing.
"""

import sys
import os
import re
import json

sys.path.insert(0, "/home/ubuntu/Project-void")

from void_engine.adriana_core import _classify_to_codon
from void_engine.al_jabr_286 import fatiha_286_hexdigest


def compress_chronicle(file_path: str) -> list:
    """Parse VOID_CHRONICLE.md and compress each session into a codon."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    sessions = re.split(r"---", content)
    compressed = []

    for session in sessions:
        session = session.strip()
        if not session or "## SESSION" not in session:
            continue

        lines = session.split("\n")
        title = lines[0] if lines else "Unknown Session"
        narrative = " ".join(lines[1:5])

        codon, expansion = _classify_to_codon(session)

        # Seal each entry with Al-Jabr 286
        seal = fatiha_286_hexdigest(session)

        compressed.append({
            "title": title.replace("## SESSION — ", ""),
            "codon": codon,
            "expansion": expansion,
            "al_jabr_seal": seal[:16] + "...",
        })

    return compressed


def main():
    chronicle_path = "/home/ubuntu/Project-void/VOID_CHRONICLE.md"
    payload = compress_chronicle(chronicle_path)

    # Output the codon chain
    codon_chain = " · ".join(entry["codon"] for entry in payload)
    print(f"Sessions compressed: {len(payload)}")
    print(f"Codon chain ({len(codon_chain)} chars):")
    print(codon_chain)
    print()

    # Save manifest
    manifest_path = "/home/ubuntu/Project-void/scripts/chronicle_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_sessions": len(payload),
            "codon_chain": codon_chain,
            "raw_bytes": len(codon_chain.encode("utf-8")),
            "entries": payload,
        }, f, indent=2, ensure_ascii=False)
    print(f"Manifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()
