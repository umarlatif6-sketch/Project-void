"""Simple ROI calculator for the connector-first VOID pitch.

This script converts the proven and modeled cost deltas in
COST_SAVINGS_ANALYSIS.md into buyer-facing outputs for a given scale.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


PROVEN_PER_USER_ANNUAL_SAVINGS = 38.52
PROVEN_PER_USER_MONTHLY_SAVINGS = 3.21
HARNESS_REDUCTION = 0.8235
HARNESS_REFERENCE_CALLS = 2_000_000
HARNESS_REFERENCE_ANNUAL_SAVINGS = 1_750_000


@dataclass
class RoiResult:
    users: int
    monthly_calls: int
    annual_calls: int
    monthly_savings_usd: float
    annual_savings_usd: float
    harness_scaled_annual_savings_usd: float
    harness_reduction_pct: float


def calculate_roi(users: int, monthly_calls: int) -> RoiResult:
    annual_calls = monthly_calls * 12
    monthly_savings = round(users * PROVEN_PER_USER_MONTHLY_SAVINGS, 2)
    annual_savings = round(users * PROVEN_PER_USER_ANNUAL_SAVINGS, 2)
    harness_scaled = round(
        (annual_calls / HARNESS_REFERENCE_CALLS) * HARNESS_REFERENCE_ANNUAL_SAVINGS,
        2,
    )
    return RoiResult(
        users=users,
        monthly_calls=monthly_calls,
        annual_calls=annual_calls,
        monthly_savings_usd=monthly_savings,
        annual_savings_usd=annual_savings,
        harness_scaled_annual_savings_usd=harness_scaled,
        harness_reduction_pct=round(HARNESS_REDUCTION * 100, 2),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="PROJECT VOID ROI calculator")
    parser.add_argument("--users", type=int, required=True, help="Number of active users")
    parser.add_argument(
        "--monthly-calls",
        type=int,
        required=True,
        help="Monthly AI calls across the deployment",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of plain text",
    )
    args = parser.parse_args()

    result = calculate_roi(args.users, args.monthly_calls)
    if args.json:
        print(json.dumps(asdict(result), indent=2))
        return

    print("PROJECT VOID ROI")
    print(f"Users: {result.users}")
    print(f"Monthly calls: {result.monthly_calls}")
    print(f"Annual calls: {result.annual_calls}")
    print(f"Monthly savings (modeled): ${result.monthly_savings_usd:,.2f}")
    print(f"Annual savings (modeled): ${result.annual_savings_usd:,.2f}")
    print(f"Annual savings (harness scaled): ${result.harness_scaled_annual_savings_usd:,.2f}")
    print(f"Harness reduction: {result.harness_reduction_pct:.2f}%")


if __name__ == "__main__":
    main()
