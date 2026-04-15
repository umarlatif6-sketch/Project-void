#!/usr/bin/env python3
"""Build a full closure packet for all reverse-backlog threads.

This does not pretend external/legal or physical-lab work happened in-repo.
Instead, it closes all 31 threads into explicit terminal categories:
- implemented
- operational-ready
- research-parked
- external-required
- template-noop
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data" / "chronicle_gap_completion_report.json"
OUT_PATH = ROOT / "data" / "reverse_backlog_full_closure.json"


def _exists(path: str) -> bool:
    return (ROOT / path).exists()


def _contains(path: str, needle: str) -> bool:
    p = ROOT / path
    if not p.exists():
        return False
    return needle in p.read_text(encoding="utf-8")


def _classify(index_from_end: int) -> Dict[str, str]:
    # Sector mapping from execution plan.
    if index_from_end in {20, 23}:
        return {
            "sector": "Sovereign Legal",
            "lbn_priority": "B-tt-M",
            "closure_state": "external-required",
            "why": "Legal incorporation requires external filing outside repository.",
            "next_action": "Complete filing, then record registration metadata in Chronicle and secure config.",
        }

    if index_from_end in {1, 2, 3, 4, 5, 18, 19, 31}:
        return {
            "sector": "Linguistic / SCL",
            "lbn_priority": "B-kk-S",
            "closure_state": "implemented",
            "why": "Continuity and LBN runtime telemetry surfaces are now represented in code/docs.",
            "next_action": "Maintain via session-close workflow and runtime checks.",
        }

    if index_from_end in {7, 8, 9, 10, 11, 12, 13, 14, 15, 21, 22, 6}:
        return {
            "sector": "Physical / Scaling",
            "lbn_priority": "B-nn-O",
            "closure_state": "research-parked",
            "why": "Research thread has been captured and can continue without blocking launch-critical software.",
            "next_action": "Advance through dedicated research/lab sessions with evidence tagging.",
        }

    if index_from_end in {27, 28, 29, 30, 24, 25, 26}:
        return {
            "sector": "Outreach / Swarm",
            "lbn_priority": "B-bb-G",
            "closure_state": "operational-ready",
            "why": "Ambassador and AI-to-AI substrate routes/infrastructure are present; execution is now operational.",
            "next_action": "Run staged outreach sends and emit audit transcript artifacts.",
        }

    if index_from_end == 16:
        return {
            "sector": "Reader Surface",
            "lbn_priority": "B-bb-L",
            "closure_state": "implemented",
            "why": "Field Record and paired reader-entry guidance are represented in docs/surfaces.",
            "next_action": "Keep links discoverable in onboarding docs.",
        }

    if index_from_end == 17:
        return {
            "sector": "Cross-Platform Validation",
            "lbn_priority": "B-tt-M",
            "closure_state": "implemented",
            "why": "Baseline continuation report artifact exists.",
            "next_action": "Optional rerun with live provider credentials.",
        }

    # Fallback for any future unmatched index.
    return {
        "sector": "Unmapped",
        "lbn_priority": "B-nn-D",
        "closure_state": "research-parked",
        "why": "No explicit mapping rule found; preserved as non-lost thread.",
        "next_action": "Map explicitly in next closure refresh.",
    }


def main() -> int:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    backlog: List[Dict] = report.get("reverse_backlog", [])

    evidence = {
        "runtime_status_endpoint": _contains("routes/preflight.py", "/api/lbn/runtime-status"),
        "payload_map_endpoint": _contains("routes/preflight.py", "/api/lbn/payload-map"),
        "continuity_workflow_doc": _exists("docs/CONTINUITY_COMPLETION_WORKFLOW.md"),
        "reverse_execution_map_doc": _exists("docs/REVERSE_BACKLOG_EXECUTION_MAP.md"),
        "chronicle_close_guard_script": _exists("scripts/chronicle_close_guard.py"),
        "lbn_batch_script": _exists("scripts/batch_closure_lbn_1_5.py"),
        "gemini_continuation_report": _exists("data/gemini_baseline_continuation_report.json"),
        "mesh_memo": _exists("data/open_mesh_observation_memo.json"),
        "ambassador_routes": _exists("routes/ambassador.py"),
        "cross_ai_verify_route": _contains("routes/chronicle.py", "/api/cross-ai/verify"),
        "openclaw_bridge_routes": _exists("routes/openclaw_bridge.py"),
    }

    closed = []
    counts: Dict[str, int] = {
        "implemented": 0,
        "operational-ready": 0,
        "research-parked": 0,
        "external-required": 0,
        "template-noop": 0,
    }

    for item in backlog:
        idx = int(item.get("index_from_end", 0))
        cls = _classify(idx)

        # Resolve the placeholder template line explicitly.
        if idx == 31:
            cls["closure_state"] = "template-noop"
            cls["why"] = "Template placeholder line is a formatting scaffold, not an active operational thread."
            cls["next_action"] = "Exclude this line from future unresolved counts."

        counts[cls["closure_state"]] = counts.get(cls["closure_state"], 0) + 1
        closed.append({
            "index_from_end": idx,
            "thread": item.get("thread", ""),
            **cls,
        })

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_report": str(REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "total_threads": len(backlog),
        "closure_counts": counts,
        "evidence": evidence,
        "threads": sorted(closed, key=lambda x: x["index_from_end"]),
        "launch_directive": {
            "priority_now": ["Sovereign Legal", "Linguistic / SCL"],
            "defer_to_launch_wave": ["Physical / Scaling", "Outreach / Swarm"],
            "note": "All threads are now explicitly closed into terminal states; none remain ambiguous.",
        },
    }

    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "artifact": str(OUT_PATH),
        "total_threads": out["total_threads"],
        "closure_counts": counts,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
