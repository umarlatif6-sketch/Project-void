#!/usr/bin/env python3
"""Batch closure artifact for reverse backlog threads #1-#5.

This script inspects repo state and writes a closure artifact with evidence
for the first five LBN/continuity threads from reverse backlog.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data" / "chronicle_gap_completion_report.json"
OUT_PATH = ROOT / "data" / "batch_closure_lbn_1_5.json"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> int:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    backlog = report.get("reverse_backlog", [])
    first_five = [item for item in backlog if 1 <= int(item.get("index_from_end", 0)) <= 5]

    preflight_text = _read_text(ROOT / "routes" / "preflight.py")
    readme_text = _read_text(ROOT / "README.md")

    checks = {
        "runtime_status_endpoint": "/api/lbn/runtime-status" in preflight_text,
        "payload_map_endpoint": "/api/lbn/payload-map" in preflight_text,
        "continuity_workflow_linked": "docs/CONTINUITY_COMPLETION_WORKFLOW.md" in readme_text,
        "reverse_map_linked": "docs/REVERSE_BACKLOG_EXECUTION_MAP.md" in readme_text,
        "chronicle_close_guard_script": (ROOT / "scripts" / "chronicle_close_guard.py").exists(),
    }

    closure = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "reverse_backlog_threads_1_to_5",
        "threads": first_five,
        "checks": checks,
        "status": {
            "thread_1": "implemented" if checks["chronicle_close_guard_script"] else "partial",
            "thread_2": "implemented" if checks["runtime_status_endpoint"] else "partial",
            "thread_3": "implemented" if checks["payload_map_endpoint"] else "partial",
            "thread_4": "research-parked",
            "thread_5": "implemented" if checks["continuity_workflow_linked"] and checks["reverse_map_linked"] else "partial",
        },
        "notes": [
            "Thread #4 (full 45-glyph expansion) is parked as dedicated research/build stream and does not block launch-critical closure.",
            "This artifact is an auditable closure packet for immediate Manchester LBN batch scope.",
        ],
    }

    OUT_PATH.write_text(json.dumps(closure, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "artifact": str(OUT_PATH), "status": closure["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
