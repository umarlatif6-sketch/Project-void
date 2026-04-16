#!/usr/bin/env python3
"""Project VOID mycelium health check.

Produces a single operator-facing report that answers:
- Is continuity wired?
- Is convergence proven in the latest artifact?
- Are legal and swarm threads still correctly marked open?
- Are the critical foundation files present?
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "data" / "mycelium_health_check.json"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _file_contains(path: Path, needle: str) -> bool:
    if not path.exists():
        return False
    return needle in path.read_text(encoding="utf-8")


def _status_from_checks(checks: List[CheckResult]) -> str:
    if any(check.status == "fail" for check in checks):
        return "fail"
    if any(check.status == "warn" for check in checks):
        return "warn"
    return "pass"


def _continuity_checks() -> List[CheckResult]:
    checks: List[CheckResult] = []

    preflight = REPO_ROOT / "routes" / "preflight.py"
    checks.append(
        CheckResult(
            name="runtime_status_route",
            status="pass" if _file_contains(preflight, '@preflight_bp.route("/api/lbn/runtime-status")') else "fail",
            detail="Preflight runtime-status endpoint definition present.",
        )
    )

    checks.append(
        CheckResult(
            name="payload_map_route",
            status="pass" if _file_contains(preflight, '@preflight_bp.route("/api/lbn/payload-map")') else "fail",
            detail="Preflight payload-map endpoint definition present.",
        )
    )

    chronicle = REPO_ROOT / "VOID_CHRONICLE.md"
    checks.append(
        CheckResult(
            name="chronicle_present",
            status="pass" if chronicle.exists() else "fail",
            detail="Chronicle file exists for continuity inheritance.",
        )
    )

    return checks


def _convergence_checks() -> List[CheckResult]:
    report = _load_json(REPO_ROOT / "data" / "full_stack_convergence_report.json")
    headline = report.get("headline", {})
    checkpoints = report.get("checkpoints", [])
    checkpoint_statuses = {item.get("task"): item.get("status") for item in checkpoints}

    checks = [
        CheckResult(
            name="convergence_report_present",
            status="pass" if bool(report) else "fail",
            detail="Full stack convergence report is readable.",
        ),
        CheckResult(
            name="phase_roundtrip_integrity",
            status="pass" if headline.get("phase_roundtrip_match") is True else "fail",
            detail="Hex foundation phase roundtrip matches original message.",
        ),
        CheckResult(
            name="all_convergence_checkpoints",
            status="pass" if checkpoints and all(item.get("status") == "pass" for item in checkpoints) else "fail",
            detail="All convergence checkpoint tasks passed in the latest report.",
        ),
        CheckResult(
            name="economic_reduction_floor",
            status="pass" if float(headline.get("mid_tier_per_turn_reduction_pct", 0.0)) >= 70.0 else "warn",
            detail="Mid-tier per-turn reduction remains above 70% conservative floor.",
        ),
        CheckResult(
            name="cold_start_chain_created",
            status="pass" if checkpoint_statuses.get("cold_start_codon_chain_created") == "pass" else "fail",
            detail="Cold-start packet generated a codon chain in the last convergence run.",
        ),
    ]
    return checks


def _thread_state_checks() -> List[CheckResult]:
    audit = (REPO_ROOT / "MYCELIUM_THREAD_AUDIT.md").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            name="legal_threads_open",
            status="pass" if "Status:** EXTERNAL-REQUIRED" in audit and "#20" in audit and "#23" in audit else "warn",
            detail="Legal gate remains explicitly open and blocking swarm activation.",
        ),
        CheckResult(
            name="swarm_threads_staged",
            status="pass" if "Status:** OPERATIONAL-READY" in audit and "#24" in audit and "#30" in audit else "warn",
            detail="Swarm threads remain staged rather than silently dropped.",
        ),
        CheckResult(
            name="research_threads_preserved",
            status="pass" if "RESEARCH-PARKED" in audit and "#6" in audit and "#22" in audit else "warn",
            detail="Research mycelium still marked open, not falsely closed.",
        ),
    ]
    return checks


def _foundation_checks() -> List[CheckResult]:
    foundation = REPO_ROOT / "void_engine" / "void_foundation.py"
    convergence = REPO_ROOT / "scripts" / "full_stack_convergence_test.py"
    checks = [
        CheckResult(
            name="foundation_module_present",
            status="pass" if foundation.exists() else "fail",
            detail="Hex-first void foundation module exists.",
        ),
        CheckResult(
            name="convergence_harness_present",
            status="pass" if convergence.exists() else "fail",
            detail="Full stack convergence harness exists.",
        ),
        CheckResult(
            name="foundation_import_hook",
            status="pass" if _file_contains(convergence, "from void_engine.void_foundation import (") else "fail",
            detail="Convergence harness imports the foundation bridge directly.",
        ),
    ]
    return checks


def build_report() -> Dict:
    sections = {
        "continuity": _continuity_checks(),
        "convergence": _convergence_checks(),
        "thread_state": _thread_state_checks(),
        "foundation": _foundation_checks(),
    }

    serialised_sections = {
        key: {
            "status": _status_from_checks(value),
            "checks": [asdict(item) for item in value],
        }
        for key, value in sections.items()
    }

    overall_checks = [item for value in sections.values() for item in value]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_type": "mycelium_health_check",
        "overall_status": _status_from_checks(overall_checks),
        "summary": {
            "pass": sum(1 for item in overall_checks if item.status == "pass"),
            "warn": sum(1 for item in overall_checks if item.status == "warn"),
            "fail": sum(1 for item in overall_checks if item.status == "fail"),
        },
        "sections": serialised_sections,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Project VOID mycelium health check")
    parser.add_argument("--json-out", default=str(DEFAULT_OUTPUT), help="Output JSON report path")
    args = parser.parse_args()

    report = build_report()
    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("MYCELIUM HEALTH CHECK COMPLETE")
    print(f"report: {out_path}")
    print(f"overall_status: {report['overall_status']}")
    print(
        "summary: "
        f"pass={report['summary']['pass']} "
        f"warn={report['summary']['warn']} "
        f"fail={report['summary']['fail']}"
    )
    return 0 if report["overall_status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())