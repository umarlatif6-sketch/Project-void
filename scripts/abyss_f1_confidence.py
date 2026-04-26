#!/usr/bin/env python3
"""Generate claim-safe F1 confidence report from Abyss comparative simulation curves.

Input:
- data/abyss_sim/comparative_curves_2012_vs_2026.csv

Outputs:
- data/abyss_sim/f1_speed_confidence_2012_vs_2026.csv
- data/abyss_sim/f1_confidence_report_2012_vs_2026.md

All outputs are model-predicted and assumption-bound.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
IN_CSV = ROOT / "data" / "abyss_sim" / "comparative_curves_2012_vs_2026.csv"
OUT_CSV = ROOT / "data" / "abyss_sim" / "f1_speed_confidence_2012_vs_2026.csv"
OUT_MD = ROOT / "data" / "abyss_sim" / "f1_confidence_report_2012_vs_2026.md"


@dataclass
class RowOut:
    t: int
    dr2012_mean: float
    dr2012_lo: float
    dr2012_hi: float
    dr2026_mean: float
    dr2026_lo: float
    dr2026_hi: float
    gain2012_mean: float
    gain2012_lo: float
    gain2012_hi: float
    gain2026_mean: float
    gain2026_lo: float
    gain2026_hi: float


def speed_gain_pct_from_drag_reduction(dr_frac: float) -> float:
    dr = max(0.0, min(0.85, dr_frac))
    # Power-limited top-speed approximation: v ~ (1/Cd)^(1/3).
    return (((1.0 / (1.0 - dr)) ** (1.0 / 3.0)) - 1.0) * 100.0


def drag_reduction_model(conductivity_s_m: float, integrity: float) -> float:
    # Normalize conductivity to activation target envelope.
    cond_norm = max(0.0, min(1.0, conductivity_s_m / 250.0))
    integ_norm = max(0.0, min(1.0, integrity))

    # Assumption-weighted readiness score.
    readiness = 0.65 * integ_norm + 0.35 * cond_norm

    # Map readiness to drag reduction fraction.
    # Floor 6% (base microtexture effect), up to about 38% in strong readiness state.
    return max(0.0, min(0.40, 0.06 + 0.32 * readiness))


def parse_f(v: str) -> float:
    return float(v.strip())


def main() -> None:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Missing required input: {IN_CSV}")

    rows_out: list[RowOut] = []

    with IN_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            t = int(r["time_h"])

            c12_m = parse_f(r["cond2012_mean_s_per_m"])
            c12_l = parse_f(r["cond2012_ci95_lo"])
            c12_h = parse_f(r["cond2012_ci95_hi"])
            c26_m = parse_f(r["cond2026_mean_s_per_m"])
            c26_l = parse_f(r["cond2026_ci95_lo"])
            c26_h = parse_f(r["cond2026_ci95_hi"])

            i12_m = parse_f(r["integrity2012_mean"])
            i12_l = parse_f(r["integrity2012_ci95_lo"])
            i12_h = parse_f(r["integrity2012_ci95_hi"])
            i26_m = parse_f(r["integrity2026_mean"])
            i26_l = parse_f(r["integrity2026_ci95_lo"])
            i26_h = parse_f(r["integrity2026_ci95_hi"])

            dr12_m = drag_reduction_model(c12_m, i12_m)
            dr12_l = drag_reduction_model(c12_l, i12_l)
            dr12_h = drag_reduction_model(c12_h, i12_h)

            dr26_m = drag_reduction_model(c26_m, i26_m)
            dr26_l = drag_reduction_model(c26_l, i26_l)
            dr26_h = drag_reduction_model(c26_h, i26_h)

            g12_m = speed_gain_pct_from_drag_reduction(dr12_m)
            g12_l = speed_gain_pct_from_drag_reduction(dr12_l)
            g12_h = speed_gain_pct_from_drag_reduction(dr12_h)

            g26_m = speed_gain_pct_from_drag_reduction(dr26_m)
            g26_l = speed_gain_pct_from_drag_reduction(dr26_l)
            g26_h = speed_gain_pct_from_drag_reduction(dr26_h)

            rows_out.append(
                RowOut(
                    t=t,
                    dr2012_mean=dr12_m,
                    dr2012_lo=dr12_l,
                    dr2012_hi=dr12_h,
                    dr2026_mean=dr26_m,
                    dr2026_lo=dr26_l,
                    dr2026_hi=dr26_h,
                    gain2012_mean=g12_m,
                    gain2012_lo=g12_l,
                    gain2012_hi=g12_h,
                    gain2026_mean=g26_m,
                    gain2026_lo=g26_l,
                    gain2026_hi=g26_h,
                )
            )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "time_h",
                "drag_reduction_2012_mean_frac",
                "drag_reduction_2012_ci95_lo",
                "drag_reduction_2012_ci95_hi",
                "drag_reduction_2026_mean_frac",
                "drag_reduction_2026_ci95_lo",
                "drag_reduction_2026_ci95_hi",
                "free_speed_gain_2012_mean_pct",
                "free_speed_gain_2012_ci95_lo",
                "free_speed_gain_2012_ci95_hi",
                "free_speed_gain_2026_mean_pct",
                "free_speed_gain_2026_ci95_lo",
                "free_speed_gain_2026_ci95_hi",
            ]
        )
        for x in rows_out:
            w.writerow(
                [
                    x.t,
                    f"{x.dr2012_mean:.6f}",
                    f"{x.dr2012_lo:.6f}",
                    f"{x.dr2012_hi:.6f}",
                    f"{x.dr2026_mean:.6f}",
                    f"{x.dr2026_lo:.6f}",
                    f"{x.dr2026_hi:.6f}",
                    f"{x.gain2012_mean:.6f}",
                    f"{x.gain2012_lo:.6f}",
                    f"{x.gain2012_hi:.6f}",
                    f"{x.gain2026_mean:.6f}",
                    f"{x.gain2026_lo:.6f}",
                    f"{x.gain2026_hi:.6f}",
                ]
            )

    # Focus window where F1 usage is practical for this model: 24h to 168h.
    window = [r for r in rows_out if 24 <= r.t <= 168]
    if not window:
        window = rows_out

    avg_12 = mean(r.gain2012_mean for r in window)
    avg_26 = mean(r.gain2026_mean for r in window)
    avg_dr_12 = mean(r.dr2012_mean for r in window) * 100.0
    avg_dr_26 = mean(r.dr2026_mean for r in window) * 100.0

    # Pick an anchor speed for practical interpretation.
    baseline_mph = 120.0
    delta_12 = baseline_mph * (avg_12 / 100.0)
    delta_26 = baseline_mph * (avg_26 / 100.0)

    best_26 = max(window, key=lambda r: r.gain2026_mean)
    best_12 = max(window, key=lambda r: r.gain2012_mean)

    report = f"""# F1 Confidence Interval Report: 2012 vs 2026 (Model-Predicted)
Date: generated by `scripts/abyss_f1_confidence.py`

## Claim Boundary
This report is model-predicted and assumption-bound. It is not certified wind-tunnel or track telemetry data.

## Model Assumptions
1. Free-speed estimate uses power-limited approximation where velocity scales with inverse drag coefficient to the one-third power.
2. Drag reduction readiness combines structural integrity (65% weight) and conductivity activation state (35% weight).
3. Conductivity normalization uses 250 S/m as the activation envelope cap.
4. Outputs are comparative indicators for decision support, pending physical calibration.

## Practical Window Summary (24h to 168h)
- 2012 mean modeled drag reduction: {avg_dr_12:.2f}%
- 2026 mean modeled drag reduction: {avg_dr_26:.2f}%
- 2012 mean modeled free-speed gain: {avg_12:.2f}%
- 2026 mean modeled free-speed gain: {avg_26:.2f}%

At 120 mph baseline equivalent:
- 2012 modeled speed delta: +{delta_12:.2f} mph
- 2026 modeled speed delta: +{delta_26:.2f} mph

## Peak Window Indicators (within 24h-168h)
- 2012 best modeled point: t={best_12.t}h, gain={best_12.gain2012_mean:.2f}% (CI [{best_12.gain2012_lo:.2f}, {best_12.gain2012_hi:.2f}])
- 2026 best modeled point: t={best_26.t}h, gain={best_26.gain2026_mean:.2f}% (CI [{best_26.gain2026_lo:.2f}, {best_26.gain2026_hi:.2f}])

## Output Artifacts
- CSV: `data/abyss_sim/f1_speed_confidence_2012_vs_2026.csv`
- This report: `data/abyss_sim/f1_confidence_report_2012_vs_2026.md`

## Next Calibration Step
Map one modeled point (recommended: 72h) to a physical coupon wind-tunnel run and update model weights from measured residuals.
"""

    OUT_MD.write_text(report, encoding="utf-8")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_MD}")


if __name__ == "__main__":
    main()
