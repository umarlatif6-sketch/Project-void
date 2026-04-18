#!/usr/bin/env python3
"""Validate ORYX repair-state smoke artifact integrity.

Fails closed if either required scenario is missing from
data/oryx_repair_state_smoke.json.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = ROOT / "data" / "oryx_repair_state_smoke.json"
REPORT_PATH = ROOT / "data" / "oryx_repair_state_smoke_check.json"

REQUIRED_SCENARIOS = {"recoverable", "quarantined"}


def main() -> int:
    issues: list[str] = []
    scenarios: list[dict] = []

    if not ARTIFACT_PATH.exists():
        issues.append(f"Artifact missing: {ARTIFACT_PATH}")
    else:
        try:
            payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"Artifact JSON parse failed: {exc}")
            payload = {}

        raw_scenarios = payload.get("scenarios")
        if not isinstance(raw_scenarios, list):
            issues.append("Artifact missing 'scenarios' list.")
        else:
            scenarios = raw_scenarios

    scenario_names = {
        str(item.get("scenario", "")).strip().lower()
        for item in scenarios
        if isinstance(item, dict)
    }

    missing = sorted(REQUIRED_SCENARIOS - scenario_names)
    if missing:
        issues.append(f"Required scenarios missing: {', '.join(missing)}")

    extra = sorted(name for name in scenario_names if name and name not in REQUIRED_SCENARIOS)

    report = {
        "ok": not issues,
        "artifact": str(ARTIFACT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "required_scenarios": sorted(REQUIRED_SCENARIOS),
        "present_scenarios": sorted(scenario_names),
        "extra_scenarios": extra,
        "issue_count": len(issues),
        "issues": issues,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"report": str(REPORT_PATH), **report}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())