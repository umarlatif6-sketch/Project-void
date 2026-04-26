#!/usr/bin/env python3
"""Generate model-predicted 2012 vs 2026 comparative curves and report.

This script intentionally produces model outputs (not in-house measured lab facts).
It builds:
- conductivity and structural integrity comparative curves
- 95% CI bands from Monte Carlo variation
- CSV + SVG + Markdown artifacts
"""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "abyss_sim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUT_DIR / "comparative_curves_2012_vs_2026.csv"
SVG_PATH = OUT_DIR / "comparative_curves_2012_vs_2026.svg"
REPORT_PATH = OUT_DIR / "comparative_report_2012_vs_2026.md"


@dataclass
class CurveStats:
    t: int
    c2012_mean: float
    c2012_lo: float
    c2012_hi: float
    c2026_mean: float
    c2026_lo: float
    c2026_hi: float
    i2012_mean: float
    i2012_lo: float
    i2012_hi: float
    i2026_mean: float
    i2026_lo: float
    i2026_hi: float


def percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = q * (len(sorted_vals) - 1)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return sorted_vals[lo]
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def conductivity_2012(t_h: int, peak_s: float, baseline_s: float, decay_start_h: int, tau_h: float) -> float:
    # Rise phase up to the fermentation switch point.
    if t_h <= 72:
        return baseline_s + (peak_s - baseline_s) * (t_h / 72.0)
    # Plateau before instability starts.
    if t_h <= decay_start_h:
        return peak_s
    # Decay due to binder/fermentation collapse.
    dt = t_h - decay_start_h
    return max(0.3, peak_s * math.exp(-dt / tau_h))


def conductivity_2026(t_h: int, sleep_s: float, active_s: float, switch_h: int) -> float:
    # Keep low conductivity before switch, then saturate quickly.
    if t_h < switch_h:
        return sleep_s
    dt = t_h - switch_h
    ramp = 1 - math.exp(-dt / 6.0)
    return sleep_s + (active_s - sleep_s) * ramp


def integrity_2012(t_h: int, crack_start_h: int, decay_tau_h: float) -> float:
    if t_h <= crack_start_h:
        return 1.0
    dt = t_h - crack_start_h
    return max(0.05, math.exp(-dt / decay_tau_h))


def integrity_2026(t_h: int, damage_hours: tuple[int, int], heal_tau_h: float, heal_floor: float) -> float:
    # Simulate two damage events with recovery kinetics.
    base = 0.97
    val = base
    for d_h in damage_hours:
        if t_h >= d_h:
            dt = t_h - d_h
            # Immediate drop then recover.
            drop = 0.25 * math.exp(-dt / heal_tau_h)
            val -= drop
    return max(heal_floor, min(1.0, val))


def monte_carlo(n_samples: int = 4000, max_h: int = 240, step_h: int = 6) -> list[CurveStats]:
    times = list(range(0, max_h + 1, step_h))
    out: list[CurveStats] = []

    for t_h in times:
        c2012_vals: list[float] = []
        c2026_vals: list[float] = []
        i2012_vals: list[float] = []
        i2026_vals: list[float] = []

        for _ in range(n_samples):
            peak = random.uniform(11.0, 13.0)
            baseline = random.uniform(7.0, 8.5)
            decay_start = random.randint(88, 104)
            tau = random.uniform(32.0, 56.0)

            sleep = random.uniform(0.015, 0.03)
            active = random.uniform(220.0, 280.0)
            switch_h = random.randint(1, 3)

            crack_start = random.randint(90, 108)
            decay_tau = random.uniform(24.0, 40.0)

            damage_a = random.randint(42, 54)
            damage_b = random.randint(114, 132)
            heal_tau = random.uniform(6.0, 14.0)
            heal_floor = random.uniform(0.82, 0.9)

            c2012_vals.append(conductivity_2012(t_h, peak, baseline, decay_start, tau))
            c2026_vals.append(conductivity_2026(t_h, sleep, active, switch_h))
            i2012_vals.append(integrity_2012(t_h, crack_start, decay_tau))
            i2026_vals.append(integrity_2026(t_h, (damage_a, damage_b), heal_tau, heal_floor))

        for vals in (c2012_vals, c2026_vals, i2012_vals, i2026_vals):
            vals.sort()

        out.append(
            CurveStats(
                t=t_h,
                c2012_mean=mean(c2012_vals),
                c2012_lo=percentile(c2012_vals, 0.025),
                c2012_hi=percentile(c2012_vals, 0.975),
                c2026_mean=mean(c2026_vals),
                c2026_lo=percentile(c2026_vals, 0.025),
                c2026_hi=percentile(c2026_vals, 0.975),
                i2012_mean=mean(i2012_vals),
                i2012_lo=percentile(i2012_vals, 0.025),
                i2012_hi=percentile(i2012_vals, 0.975),
                i2026_mean=mean(i2026_vals),
                i2026_lo=percentile(i2026_vals, 0.025),
                i2026_hi=percentile(i2026_vals, 0.975),
            )
        )

    return out


def write_csv(rows: list[CurveStats]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "time_h",
                "cond2012_mean_s_per_m",
                "cond2012_ci95_lo",
                "cond2012_ci95_hi",
                "cond2026_mean_s_per_m",
                "cond2026_ci95_lo",
                "cond2026_ci95_hi",
                "integrity2012_mean",
                "integrity2012_ci95_lo",
                "integrity2012_ci95_hi",
                "integrity2026_mean",
                "integrity2026_ci95_lo",
                "integrity2026_ci95_hi",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.t,
                    f"{r.c2012_mean:.6f}",
                    f"{r.c2012_lo:.6f}",
                    f"{r.c2012_hi:.6f}",
                    f"{r.c2026_mean:.6f}",
                    f"{r.c2026_lo:.6f}",
                    f"{r.c2026_hi:.6f}",
                    f"{r.i2012_mean:.6f}",
                    f"{r.i2012_lo:.6f}",
                    f"{r.i2012_hi:.6f}",
                    f"{r.i2026_mean:.6f}",
                    f"{r.i2026_lo:.6f}",
                    f"{r.i2026_hi:.6f}",
                ]
            )


def to_xy(values: list[tuple[float, float]], x0: float, y0: float, w: float, h: float, x_max: float, y_max: float) -> str:
    pts = []
    for x, y in values:
        px = x0 + (x / x_max) * w
        py = y0 + h - (y / y_max) * h
        pts.append(f"{px:.2f},{py:.2f}")
    return " ".join(pts)


def write_svg(rows: list[CurveStats]) -> None:
    width = 1200
    height = 700
    margin = 70

    # Top panel conductivity.
    c_x0, c_y0, c_w, c_h = margin, margin, width - 2 * margin, 250
    # Bottom panel integrity.
    i_x0, i_y0, i_w, i_h = margin, 380, width - 2 * margin, 230

    t_max = max(r.t for r in rows)
    c_max = max(r.c2026_hi for r in rows)

    c2012 = [(r.t, r.c2012_mean) for r in rows]
    c2026 = [(r.t, r.c2026_mean) for r in rows]
    i2012 = [(r.t, r.i2012_mean) for r in rows]
    i2026 = [(r.t, r.i2026_mean) for r in rows]

    c2012_pts = to_xy(c2012, c_x0, c_y0, c_w, c_h, t_max, c_max)
    c2026_pts = to_xy(c2026, c_x0, c_y0, c_w, c_h, t_max, c_max)
    i2012_pts = to_xy(i2012, i_x0, i_y0, i_w, i_h, t_max, 1.0)
    i2026_pts = to_xy(i2026, i_x0, i_y0, i_w, i_h, t_max, 1.0)

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
  <style>
    .axis {{ stroke: #444; stroke-width: 1.2; }}
    .grid {{ stroke: #ddd; stroke-width: 1; }}
    .label {{ font: 14px sans-serif; fill: #222; }}
    .title {{ font: 18px sans-serif; font-weight: 700; fill: #111; }}
    .line2012 {{ fill: none; stroke: #cc3b3b; stroke-width: 2.6; }}
    .line2026 {{ fill: none; stroke: #2060c0; stroke-width: 2.6; }}
    .legend {{ font: 13px sans-serif; fill: #222; }}
  </style>

  <text x='{margin}' y='35' class='title'>Abyss Comparative Digital Twin (Model-Predicted): 2012 Prototype vs 2026 Architecture</text>

  <rect x='{c_x0}' y='{c_y0}' width='{c_w}' height='{c_h}' fill='none' class='axis'/>
  <text x='{c_x0}' y='{c_y0 - 10}' class='label'>Conductivity (S/m)</text>
  <polyline points='{c2012_pts}' class='line2012'/>
  <polyline points='{c2026_pts}' class='line2026'/>

  <rect x='{i_x0}' y='{i_y0}' width='{i_w}' height='{i_h}' fill='none' class='axis'/>
  <text x='{i_x0}' y='{i_y0 - 10}' class='label'>Structural Integrity (0-1)</text>
  <polyline points='{i2012_pts}' class='line2012'/>
  <polyline points='{i2026_pts}' class='line2026'/>

  <line x1='{margin}' y1='{height - 40}' x2='{width - margin}' y2='{height - 40}' class='axis'/>
  <text x='{width - margin - 120}' y='{height - 15}' class='label'>Time (hours)</text>

  <rect x='{width - 330}' y='60' width='250' height='62' fill='white' stroke='#bbb'/>
  <line x1='{width - 315}' y1='82' x2='{width - 275}' y2='82' class='line2012'/>
  <text x='{width - 265}' y='86' class='legend'>2012 Anthocyanin-Circuit</text>
  <line x1='{width - 315}' y1='106' x2='{width - 275}' y2='106' class='line2026'/>
  <text x='{width - 265}' y='110' class='legend'>2026 Abyss Architecture</text>

  <text x='{margin}' y='{height - 15}' class='legend'>Model-only output. Requires physical calibration for factual real-world claims.</text>
</svg>
"""
    SVG_PATH.write_text(svg, encoding="utf-8")


def write_report(rows: list[CurveStats]) -> None:
    by_t = {r.t: r for r in rows}
    r72 = by_t.get(72)
    r96 = by_t.get(96)
    r168 = by_t.get(168)
    r240 = by_t.get(240)

    text = f"""# Comparative Simulation Report: 2012 vs 2026
Date: generated by `scripts/abyss_compare_2012_2026.py`

## Scope
This report is model-predicted and claim-safe. It is not a substitute for physical test certification.

## Inputs Used
- 2012 anchor: fermentation-induced resistance change around 72h and instability beyond ~96h.
- 2026 target architecture: fast activation and higher integrity retention due to self-healing assumptions.
- Monte Carlo sample count: 4000.
- Output confidence interval: 95%.

## Key Model Observations
- 2012 conductivity peaks near 72-96h and then decays strongly by later windows.
- 2026 conductivity ramps rapidly after switch and saturates near the activated regime.
- 2012 structural integrity declines after crack-start regime.
- 2026 integrity recovers after modeled damage events and remains in high-retention band.

## Snapshot Points (mean with 95% CI)
- 72h conductivity: 2012 = {r72.c2012_mean:.2f} [{r72.c2012_lo:.2f}, {r72.c2012_hi:.2f}] S/m; 2026 = {r72.c2026_mean:.2f} [{r72.c2026_lo:.2f}, {r72.c2026_hi:.2f}] S/m
- 96h conductivity: 2012 = {r96.c2012_mean:.2f} [{r96.c2012_lo:.2f}, {r96.c2012_hi:.2f}] S/m; 2026 = {r96.c2026_mean:.2f} [{r96.c2026_lo:.2f}, {r96.c2026_hi:.2f}] S/m
- 168h integrity: 2012 = {r168.i2012_mean:.3f} [{r168.i2012_lo:.3f}, {r168.i2012_hi:.3f}]; 2026 = {r168.i2026_mean:.3f} [{r168.i2026_lo:.3f}, {r168.i2026_hi:.3f}]
- 240h integrity: 2012 = {r240.i2012_mean:.3f} [{r240.i2012_lo:.3f}, {r240.i2012_hi:.3f}]; 2026 = {r240.i2026_mean:.3f} [{r240.i2026_lo:.3f}, {r240.i2026_hi:.3f}]

## Artifacts
- CSV: `data/abyss_sim/comparative_curves_2012_vs_2026.csv`
- SVG graph: `data/abyss_sim/comparative_curves_2012_vs_2026.svg`
- Report: `data/abyss_sim/comparative_report_2012_vs_2026.md`

## Claim Boundary
Use wording such as "model-predicted" and "pending physical calibration" for any external sharing.
"""
    REPORT_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    rows = monte_carlo()
    write_csv(rows)
    write_svg(rows)
    write_report(rows)
    print(f"Wrote: {CSV_PATH}")
    print(f"Wrote: {SVG_PATH}")
    print(f"Wrote: {REPORT_PATH}")


if __name__ == "__main__":
    main()
