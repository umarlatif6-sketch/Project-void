#!/usr/bin/env python3
"""
Chronicle Close Linter — PROJECT VOID
======================================

Validates that every Chronicle entry follows the required format:
- [ ] Session date + title (## SESSION — [Date] — [Title])
- [ ] Narrative paragraphs (not bullet lists)
- [ ] Forward Thread (what next session inherits)
- [ ] No stale references or incomplete entries

Run: python3 scripts/chronicle_close_linter.py
"""

import re
import json
from pathlib import Path
from datetime import datetime

# ── CONFIGURATION ──────────────────────────────────────────────────────────

CHRONICLE_FILE = Path(__file__).parent.parent / "VOID_CHRONICLE.md"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "chronicle_validation_report.json"

# ── VALIDATION RULES ──────────────────────────────────────────────────────

REQUIRED_ELEMENTS = {
    "session_header": r"^## SESSION — .+ — .+$",
    "narrative_content": r"^[A-Z][^-\[\]]+\.\s*$",  # Paragraph starting with capital, no bullets
    "forward_thread": r"^\*\*Forward Thread:\*\*",
}

# ── ENTRY EXTRACTION ───────────────────────────────────────────────────────

def extract_entries(chronicle_text):
    """Extract individual Chronicle entries from the full text."""
    # Split on "## SESSION —" to get individual entries
    entries = re.split(r"(?=^## SESSION —)", chronicle_text, flags=re.MULTILINE)
    return [e.strip() for e in entries if e.strip()]

def validate_entry(entry_text, entry_number):
    """Validate a single Chronicle entry against all required rules."""
    lines = entry_text.split('\n')
    
    checks = {
        "has_session_header": False,
        "has_narrative": False,
        "has_forward_thread": False,
        "no_bullet_lists": True,
        "has_content": len(entry_text.strip()) > 100,
    }
    
    violations = []
    
    # Check 1: Session header
    header_line = lines[0] if lines else ""
    if re.match(REQUIRED_ELEMENTS["session_header"], header_line):
        checks["has_session_header"] = True
    else:
        violations.append(f"Missing or malformed session header. Got: '{header_line[:50]}'")
    
    # Check 2: Narrative paragraphs (not bullet lists)
    paragraph_count = 0
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            checks["no_bullet_lists"] = False
            violations.append(f"Found bullet list instead of narrative: '{line[:50]}'")
        elif line and not line.startswith("#") and not line.startswith("**") and len(line) > 50:
            paragraph_count += 1
    
    if paragraph_count >= 2:
        checks["has_narrative"] = True
    else:
        violations.append(f"Insufficient narrative content. Found {paragraph_count} paragraphs (need ≥2)")
    
    # Check 3: Forward Thread
    if "**Forward Thread:**" in entry_text:
        checks["has_forward_thread"] = True
    else:
        violations.append("Missing '**Forward Thread:**' section")
    
    # Check 4: Content length
    if len(entry_text.strip()) <= 100:
        violations.append("Entry is too short (< 100 characters)")
        checks["has_content"] = False
    
    # Determine overall status
    all_checks_pass = all(checks.values())
    
    return {
        "entry_number": entry_number,
        "header": header_line[:80],
        "checks": checks,
        "all_pass": all_checks_pass,
        "violations": violations,
    }

def run_validation():
    """Run full Chronicle validation."""
    if not CHRONICLE_FILE.exists():
        print(f"✗ Chronicle file not found: {CHRONICLE_FILE}")
        return None
    
    with open(CHRONICLE_FILE, 'r') as f:
        chronicle_text = f.read()
    
    entries = extract_entries(chronicle_text)
    results = []
    
    print(f"\n📋 CHRONICLE CLOSE LINTER")
    print(f"{'='*60}")
    print(f"File: {CHRONICLE_FILE}")
    print(f"Total entries found: {len(entries)}\n")
    
    for i, entry in enumerate(entries, 1):
        validation = validate_entry(entry, i)
        results.append(validation)
        
        status = "✓" if validation["all_pass"] else "✗"
        print(f"{status} Entry {i}: {validation['header']}")
        
        if not validation["all_pass"]:
            for violation in validation["violations"]:
                print(f"   ⚠ {violation}")
    
    # Summary
    passed = sum(1 for r in results if r["all_pass"])
    failed = len(results) - passed
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed}/{len(results)} entries pass validation")
    
    if failed > 0:
        print(f"⚠ {failed} entries have violations")
    else:
        print(f"✓ All entries are valid")
    
    # Save report
    report = {
        "generated_at": datetime.now().isoformat(),
        "chronicle_file": str(CHRONICLE_FILE),
        "total_entries": len(entries),
        "passed": passed,
        "failed": failed,
        "results": results,
    }
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Report saved: {OUTPUT_FILE}\n")
    
    return report

# ── MAIN ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    report = run_validation()
    
    # Exit with appropriate code
    if report:
        exit(0 if report["failed"] == 0 else 1)
    else:
        exit(1)
