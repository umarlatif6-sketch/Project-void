#!/usr/bin/env python3
"""Robustness sweep for binary agent selector.

Compares:
- set 0: unpaired 286 formation
- set 1: paired 286 Yin/Yang formation

Runs across multiple seeds and reports win-rate and score margins.
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
    return sum(values) / len(values) if values else 0.0


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

    resilience = _mean(cockroach_curve)
    gini_mean = _mean(gini_curve)
    yy_pairs_mean = _mean(yy_pairs_curve)
    yy_lift_mean = _mean(yy_lift_curve)

    score = (
        grade_points * 10.0
        + resilience * 100.0
        - economy_breaks * 2.0
        - max(0.0, gini_mean - 0.65) * 40.0
        + yy_pairs_mean * 0.5
        + yy_lift_mean * 120.0
    )

    return {
        "grade": verdict.get("grade", "F"),
        "mean_cockroach_activity": round(resilience, 4),
        "economy_breaks": economy_breaks,
        "mean_gini": round(gini_mean, 4),
        "mean_yinyang_pairs": round(yy_pairs_mean, 4),
        "mean_yinyang_activity_lift": round(yy_lift_mean, 4),
        "composite_score": round(score, 6),
    }


def run_robustness(seed_count: int = 10) -> dict:
    seeds = [f"cockroach_selector_seed_{i:02d}" for i in range(1, seed_count + 1)]

    runs = []
    wins_0 = 0
    wins_1 = 0
    ties = 0

    for seed in seeds:
        set0 = run_stress_battery(
            seed=seed,
            integrated=True,
            sovereign_ratio=0.30,
            yin_yang=False,
            cockroach_ratio=0.22,
        )
        set1 = run_stress_battery(
            seed=seed,
            integrated=True,
            sovereign_ratio=0.30,
            yin_yang=True,
            cockroach_ratio=0.22,
        )

        score0 = _score(set0)
        score1 = _score(set1)
        delta = round(score1["composite_score"] - score0["composite_score"], 6)

        if delta > 0:
            winner_bit = 1
            wins_1 += 1
        elif delta < 0:
            winner_bit = 0
            wins_0 += 1
        else:
            winner_bit = 1  # tie-break preference
            wins_1 += 1
            ties += 1

        runs.append(
            {
                "seed": seed,
                "set0": score0,
                "set1": score1,
                "score_delta_set1_minus_set0": delta,
                "winner_bit": winner_bit,
            }
        )

    deltas = [r["score_delta_set1_minus_set0"] for r in runs]
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed_count": seed_count,
        "binary_definition": {
            "0": "unpaired_286",
            "1": "paired_286_yinyang",
        },
        "summary": {
            "wins_set_1": wins_1,
            "wins_set_0": wins_0,
            "ties": ties,
            "set_1_win_rate": round(wins_1 / seed_count, 4),
            "avg_score_delta_set1_minus_set0": round(_mean(deltas), 6),
            "max_delta": round(max(deltas) if deltas else 0.0, 6),
            "min_delta": round(min(deltas) if deltas else 0.0, 6),
            "recommended_bit": 1 if wins_1 >= wins_0 else 0,
            "recommendation": "Use agent set 1" if wins_1 >= wins_0 else "Use agent set 0",
        },
        "runs": runs,
    }

    out = Path("data/cockroach_agent_selector_robustness.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("COCKROACH ROBUSTNESS COMPLETE")
    print(f"seed_count: {seed_count}")
    print(f"wins_set_1: {wins_1}")
    print(f"wins_set_0: {wins_0}")
    print(f"ties: {ties}")
    print(f"set_1_win_rate: {round(wins_1 / seed_count, 4)}")
    print(f"report: {out}")

    return result


if __name__ == "__main__":
    count = 10
    if len(sys.argv) > 1:
        try:
            count = max(1, int(sys.argv[1]))
        except ValueError:
            count = 10
    run_robustness(count)
