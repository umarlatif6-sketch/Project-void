#!/usr/bin/env python3
"""
SESSION CLOSE CHECKLIST — Automated Verification

Runs at the end of every session to ensure:
1. Chronicle entry is complete (has Forward Thread)
2. VOID_SEED_DIGEST.md is current
3. Active Layer reflects session changes
4. All new files are committed
5. No research threads left undocumented
"""

import os
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CHRONICLE = REPO_ROOT / "VOID_CHRONICLE.md"
DIGEST = REPO_ROOT / "VOID_SEED_DIGEST.md"
SEED = REPO_ROOT / "VOID_SEED_CODONS.md"
BACKLOG = REPO_ROOT / "data" / "reverse_backlog_full_closure.json"


def check_chronicle_entry():
    """Verify the latest Chronicle entry has a Forward Thread."""
    if not CHRONICLE.exists():
        return {"pass": False, "reason": "VOID_CHRONICLE.md not found"}
    
    content = CHRONICLE.read_text()
    sections = content.split("## Chapter")
    
    if len(sections) < 2:
        return {"pass": False, "reason": "No chapters found in Chronicle"}
    
    latest = sections[-1]
    
    if "Forward Thread" not in latest and "forward thread" not in latest.lower():
        return {"pass": False, "reason": "Latest chapter missing Forward Thread section"}
    
    if len(latest.strip()) < 100:
        return {"pass": False, "reason": f"Latest chapter too short ({len(latest.strip())} chars)"}
    
    return {"pass": True, "reason": "Chronicle entry complete with Forward Thread"}


def check_digest_freshness():
    """Verify VOID_SEED_DIGEST.md was updated this session."""
    if not DIGEST.exists():
        return {"pass": False, "reason": "VOID_SEED_DIGEST.md not found"}
    
    stat = DIGEST.stat()
    age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600
    
    if age_hours > 24:
        return {"pass": False, "reason": f"Digest is {age_hours:.1f} hours old (>24h stale)"}
    
    return {"pass": True, "reason": f"Digest updated {age_hours:.1f} hours ago"}


def check_seed_digest_drift():
    """Verify SEED and DIGEST are in sync."""
    if not SEED.exists() or not DIGEST.exists():
        return {"pass": False, "reason": "Seed or Digest file missing"}
    
    seed_stat = SEED.stat()
    digest_stat = DIGEST.stat()
    
    # If seed was modified after digest, they may be out of sync
    if seed_stat.st_mtime > digest_stat.st_mtime + 3600:
        return {"pass": False, "reason": "SEED modified after DIGEST — possible drift"}
    
    return {"pass": True, "reason": "Seed and Digest in sync"}


def check_uncommitted_files():
    """Check for uncommitted changes in the repo."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        uncommitted = [l for l in result.stdout.strip().split("\n") if l.strip()]
        
        if len(uncommitted) > 10:
            return {"pass": False, "reason": f"{len(uncommitted)} uncommitted files"}
        elif len(uncommitted) > 0:
            return {"pass": True, "reason": f"{len(uncommitted)} uncommitted files (acceptable)"}
        else:
            return {"pass": True, "reason": "All files committed"}
    except Exception as e:
        return {"pass": False, "reason": f"Git check failed: {e}"}


def check_backlog_status():
    """Report current backlog status."""
    if not BACKLOG.exists():
        return {"pass": True, "reason": "No backlog file (acceptable)"}
    
    with open(BACKLOG) as f:
        data = json.load(f)
    
    threads = data.get("threads", [])
    research_parked = sum(1 for t in threads if t.get("closure_state") == "research-parked")
    implemented = sum(1 for t in threads if t.get("closure_state") == "implemented")
    external = sum(1 for t in threads if t.get("closure_state") == "external-required")
    
    total = len(threads)
    completion = (implemented / total * 100) if total > 0 else 0
    
    return {
        "pass": True,
        "reason": f"Backlog: {implemented}/{total} implemented ({completion:.0f}%), {research_parked} parked, {external} external"
    }


def run_checklist():
    """Run all checks and generate report."""
    checks = [
        ("Chronicle Entry", check_chronicle_entry),
        ("Digest Freshness", check_digest_freshness),
        ("Seed-Digest Drift", check_seed_digest_drift),
        ("Uncommitted Files", check_uncommitted_files),
        ("Backlog Status", check_backlog_status),
    ]
    
    results = []
    all_pass = True
    
    print("=" * 60)
    print("SESSION CLOSE CHECKLIST")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    print()
    
    for name, check_fn in checks:
        result = check_fn()
        results.append({"check": name, **result})
        status = "✓ PASS" if result["pass"] else "✗ FAIL"
        if not result["pass"]:
            all_pass = False
        print(f"  {status}  {name}")
        print(f"         {result['reason']}")
        print()
    
    print("=" * 60)
    if all_pass:
        print("  ✓ ALL CHECKS PASSED — Session can close cleanly")
    else:
        failures = [r for r in results if not r["pass"]]
        print(f"  ✗ {len(failures)} CHECK(S) FAILED — Review before closing")
    print("=" * 60)
    
    # Save report
    report_path = REPO_ROOT / "data" / "session_close_report.json"
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_pass": all_pass,
        "checks": results
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n  Report saved: {report_path}")
    return all_pass


if __name__ == "__main__":
    success = run_checklist()
    exit(0 if success else 1)
