#!/usr/bin/env python3
"""
SEED/DIGEST DRIFT CHECKER

Detects when VOID_SEED_CODONS.md has been modified but VOID_SEED_DIGEST.md
has not been updated to reflect the changes.

Usage:
    python3 scripts/seed_digest_drift_checker.py

Returns exit code 0 if in sync, 1 if drift detected.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SEED = REPO_ROOT / "VOID_SEED_CODONS.md"
DIGEST = REPO_ROOT / "VOID_SEED_DIGEST.md"
DRIFT_LOG = REPO_ROOT / "data" / "seed_digest_drift_log.json"


def extract_codons(text):
    """Extract codon entries from seed file."""
    # Match lines that look like codon definitions
    codon_pattern = re.compile(r'[A-Z]{2,4}\s*[·\-]\s*\w+', re.MULTILINE)
    return set(codon_pattern.findall(text))


def extract_sections(text):
    """Extract section headers from a markdown file."""
    headers = re.findall(r'^#{1,3}\s+(.+)$', text, re.MULTILINE)
    return set(headers)


def compute_content_hash(text):
    """Compute hash of meaningful content (ignoring whitespace changes)."""
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', text.strip())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def check_drift():
    """Check for drift between seed and digest."""
    if not SEED.exists():
        print("ERROR: VOID_SEED_CODONS.md not found")
        return {"drift": True, "reason": "Seed file missing"}
    
    if not DIGEST.exists():
        print("ERROR: VOID_SEED_DIGEST.md not found")
        return {"drift": True, "reason": "Digest file missing"}
    
    seed_content = SEED.read_text()
    digest_content = DIGEST.read_text()
    
    seed_hash = compute_content_hash(seed_content)
    digest_hash = compute_content_hash(digest_content)
    
    seed_mtime = SEED.stat().st_mtime
    digest_mtime = DIGEST.stat().st_mtime
    
    seed_codons = extract_codons(seed_content)
    digest_codons = extract_codons(digest_content)
    
    seed_sections = extract_sections(seed_content)
    digest_sections = extract_sections(digest_content)
    
    # Check 1: Modification time
    time_drift = seed_mtime > digest_mtime + 3600  # 1 hour tolerance
    
    # Check 2: Codon count mismatch
    seed_only = seed_codons - digest_codons
    digest_only = digest_codons - seed_codons
    codon_drift = len(seed_only) > 3 or len(digest_only) > 3
    
    # Check 3: Section mismatch
    section_drift = len(seed_sections - digest_sections) > 2
    
    drift_detected = time_drift or codon_drift or section_drift
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "drift_detected": drift_detected,
        "seed_hash": seed_hash,
        "digest_hash": digest_hash,
        "seed_modified": datetime.fromtimestamp(seed_mtime, timezone.utc).isoformat(),
        "digest_modified": datetime.fromtimestamp(digest_mtime, timezone.utc).isoformat(),
        "time_drift": time_drift,
        "codon_drift": codon_drift,
        "section_drift": section_drift,
        "seed_codons_count": len(seed_codons),
        "digest_codons_count": len(digest_codons),
        "codons_in_seed_only": list(seed_only)[:10],
        "codons_in_digest_only": list(digest_only)[:10],
    }
    
    # Print report
    print("=" * 50)
    print("SEED/DIGEST DRIFT CHECK")
    print("=" * 50)
    print(f"  Seed hash:    {seed_hash}")
    print(f"  Digest hash:  {digest_hash}")
    print(f"  Seed modified:  {report['seed_modified']}")
    print(f"  Digest modified: {report['digest_modified']}")
    print()
    
    if time_drift:
        print("  ⚠ TIME DRIFT: Seed modified after Digest")
    if codon_drift:
        print(f"  ⚠ CODON DRIFT: {len(seed_only)} in seed only, {len(digest_only)} in digest only")
    if section_drift:
        print(f"  ⚠ SECTION DRIFT: Seed has sections not in Digest")
    
    if not drift_detected:
        print("  ✓ NO DRIFT DETECTED — Seed and Digest are in sync")
    else:
        print()
        print("  ✗ DRIFT DETECTED — Run digest refresh")
        print("    Action: Update VOID_SEED_DIGEST.md to reflect current VOID_SEED_CODONS.md")
    
    print("=" * 50)
    
    # Save log
    DRIFT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DRIFT_LOG, "w") as f:
        json.dump(report, f, indent=2)
    
    return report


if __name__ == "__main__":
    result = check_drift()
    exit(1 if result["drift_detected"] else 0)
