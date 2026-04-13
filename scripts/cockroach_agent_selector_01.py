#!/usr/bin/env python3
"""Binary selector for resilient formations.

Agent Set 0: Hybrid 286 formation without polarity pairing.
Agent Set 1: Hybrid 286 formation with hex-derived Yin/Yang pairing.

Outputs a hard winner bit (0/1) and writes a report to:
  data/cockroach_agent_selector_01.json
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from void_engine.stress_battery import run_stress_battery


GRADE_POINTS = {
    "A+": 10,
    "A": 9,
    "B+": 8,
    "B": 7,
    "C+": 6,
    "C": 5,
    "D": 4,
    "F": 1,
}


def _mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def _score(report: dict) -> dict:
    verdict = report.get("verdict", {})
    tests = report.get("tests", [])

    cockroach_curve = [t["results"]["cockroach_avg_activity"] for t in tests]
    gini_curve = [t["results"]["gini_coefficient"] for t in tests]
    yy_pairs_curve = [t["results"].get("yin_yang_pairs", 0) for t in tests]
    yy_lift_curve = [
        t["results"].get("yy_paired_avg_activity", 0) - t["results"].get("yy_unpaired_avg_activity", 0)
        for t in tests
    ]

    grade_points = GRADE_POINTS.get(verdict.get("grade", "F"), 1)
    economy_breaks = report.get("economy_breaks", 0)

    # Composite score:
    # - Grade carries most weight
    # - Cockroach average activity is direct resilience signal
    # - Lower economy breaks is better
    # - Gini penalty for collapse into extreme inequality
    resilience = _mean(cockroach_curve)
    gini_mean = _mean(gini_curve)
    yy_pairs_mean = _mean(yy_pairs_curve)
    yy_lift_mean = _mean(yy_lift_curve)

    final_score = (
        grade_points * 10.0
        + resilience * 100.0
        - economy_breaks * 2.0
        - max(0.0, gini_mean - 0.65) * 40.0
        + yy_pairs_mean * 0.5
        + yy_lift_mean * 120.0
    )

    return {
        "grade": verdict.get("grade", "F"),
        "grade_points": grade_points,
        "mean_cockroach_activity": round(resilience, 4),
        "economy_breaks": economy_breaks,
        "mean_gini": round(gini_mean, 4),
        "mean_yinyang_pairs": round(yy_pairs_mean, 4),
        "mean_yinyang_activity_lift": round(yy_lift_mean, 4),
        "composite_score": round(final_score, 4),
    }


def run_selector() -> dict:
    seed = "cockroach_selector_286"

    # Set 0 = hybrid 286, no Yin/Yang pairing
    set0 = run_stress_battery(
        seed=seed,
        integrated=True,
        sovereign_ratio=0.30,
        yin_yang=False,
        cockroach_ratio=0.22,
    )

    # Set 1 = hybrid 286, with Yin/Yang pairing (hex polarity 0/1 coupling)
    set1 = run_stress_battery(
        seed=seed,
        integrated=True,
        sovereign_ratio=0.30,
        yin_yang=True,
        cockroach_ratio=0.22,
    )

    score0 = _score(set0)
    score1 = _score(set1)

    score_delta = round(score1["composite_score"] - score0["composite_score"], 6)
    winner_bit = 1 if score_delta >= 0 else 0
    tie_break_reason = (
        "paired_286_lock_preferred_when_equal"
        if score_delta == 0
        else "higher_composite_score"
    )

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selector": "agent_set_0_or_1",
        "agent_set_0": {
            "label": "binary_0_unpaired_286",
            "mode": set0.get("mode"),
            "cockroach_ratio": set0.get("cockroach_ratio"),
            "sovereign_ratio": set0.get("sovereign_ratio"),
            "binary_definition": "0 = no yin/yang pair lock",
            "score": score0,
            "verdict": set0.get("verdict", {}),
        },
        "agent_set_1": {
            "label": "binary_1_paired_286",
            "mode": set1.get("mode"),
            "cockroach_ratio": set1.get("cockroach_ratio"),
            "sovereign_ratio": set1.get("sovereign_ratio"),
            "binary_definition": "1 = yin/yang pair lock from 286-bit polarity",
            "score": score1,
            "verdict": set1.get("verdict", {}),
        },
        "winner_bit": winner_bit,
        "winner_label": "agent_set_1" if winner_bit == 1 else "agent_set_0",
        "decision": "Use agent set 1" if winner_bit == 1 else "Use agent set 0",
        "score_delta_set1_minus_set0": score_delta,
        "tie_break_reason": tie_break_reason,
    }

    out = Path("data/cockroach_agent_selector_01.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("COCKROACH AGENT SELECTOR COMPLETE")
    print(f"winner_bit: {winner_bit}")
    print(f"decision: {result['decision']}")
    print(f"report: {out}")

    return result


if __name__ == "__main__":
    run_selector()
