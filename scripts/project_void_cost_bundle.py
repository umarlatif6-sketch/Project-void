#!/usr/bin/env python3
"""Generate Project VOID cost comparison and positioning bundle."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ACTUAL_TOOLING_SPEND_GBP = 1326.50
OLD_LOW_GBP = 25000.0
OLD_MID_GBP = 80000.0
OLD_HIGH_GBP = 250000.0
TOKEN_REDUCTION_PCT = 82.35
PROJECT_VOID_TOKEN_BASELINE_RATIO = 1.0 - (TOKEN_REDUCTION_PCT / 100.0)


def pct_savings(old: float, new: float) -> float:
    return round(((old - new) / old) * 100.0, 2)


def multiple(old: float, new: float) -> float:
    return round(old / new, 2) if new else 0.0


def monthly_example(normal_spend: float) -> dict:
    pv_spend = round(normal_spend * PROJECT_VOID_TOKEN_BASELINE_RATIO, 2)
    savings = round(normal_spend - pv_spend, 2)
    return {
        "normal_token_spend_gbp": normal_spend,
        "project_void_token_spend_gbp": pv_spend,
        "monthly_savings_gbp": savings,
    }


def build_bundle() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "headline": {
            "actual_tooling_spend_gbp": ACTUAL_TOOLING_SPEND_GBP,
            "token_reduction_pct": TOKEN_REDUCTION_PCT,
            "project_void_token_baseline_ratio": round(PROJECT_VOID_TOKEN_BASELINE_RATIO, 4),
        },
        "three_way_comparison": {
            "old_method": {
                "build_cost_gbp": {
                    "low": OLD_LOW_GBP,
                    "mid": OLD_MID_GBP,
                    "high": OLD_HIGH_GBP,
                },
                "ongoing_cost_profile": "People-heavy: engineers, designers, coordination overhead, handoff loss, agency or contractor burn.",
                "token_cost_profile": "Low direct token cost, high human labor cost.",
                "what_you_get": "Slower delivery, more fragmentation, less continuity, more reinterpretation between roles.",
            },
            "new_method": {
                "build_cost_gbp": ACTUAL_TOOLING_SPEND_GBP,
                "ongoing_cost_profile": "Subscription stack keeps accumulating across AI tools and platforms.",
                "token_cost_profile": "High token baseline because context is repeatedly reloaded and continuity is lost.",
                "what_you_get": "Fast iteration, but memory loss and model drift increase spend and reduce coherence.",
            },
            "project_void": {
                "build_cost_gbp": ACTUAL_TOOLING_SPEND_GBP,
                "ongoing_cost_profile": "Same modern tool substrate, but used through Chronicle, codons, pair-locking, and continuity infrastructure.",
                "token_cost_profile": f"About {round(PROJECT_VOID_TOKEN_BASELINE_RATIO * 100, 2)}% of the normal token baseline.",
                "what_you_get": "Continuity, compression, auditable reasoning, sovereign world identity, resilience logic, and lower recurring token burn.",
            },
        },
        "old_method_cost_equivalents": {
            "versus_old_low": {
                "old_cost_gbp": OLD_LOW_GBP,
                "multiple_more_expensive": multiple(OLD_LOW_GBP, ACTUAL_TOOLING_SPEND_GBP),
                "pct_more_expensive": pct_savings(OLD_LOW_GBP, ACTUAL_TOOLING_SPEND_GBP),
            },
            "versus_old_mid": {
                "old_cost_gbp": OLD_MID_GBP,
                "multiple_more_expensive": multiple(OLD_MID_GBP, ACTUAL_TOOLING_SPEND_GBP),
                "pct_more_expensive": pct_savings(OLD_MID_GBP, ACTUAL_TOOLING_SPEND_GBP),
            },
            "versus_old_high": {
                "old_cost_gbp": OLD_HIGH_GBP,
                "multiple_more_expensive": multiple(OLD_HIGH_GBP, ACTUAL_TOOLING_SPEND_GBP),
                "pct_more_expensive": pct_savings(OLD_HIGH_GBP, ACTUAL_TOOLING_SPEND_GBP),
            },
        },
        "token_examples": [
            monthly_example(100.0),
            monthly_example(500.0),
            monthly_example(1000.0),
            monthly_example(10000.0),
        ],
        "investor_paragraph": (
            "For roughly 1.3K GBP in tooling spend, Project VOID produced what would normally require a far larger R&D budget: "
            "a functioning continuity stack, measurable token-cost compression, multi-agent resilience logic, auditable reports, "
            "and user-specific sovereign world generation. This is not a consumer AI spend pattern. It is a capital-efficient "
            "infrastructure build that demonstrates unusually high output per pound deployed."
        ),
        "negotiation_version": (
            "What cost about 1.3K GBP to force into existence here would likely cost 25K to 250K GBP through the old method, "
            "depending on whether you used freelancers, a small startup team, or an R&D agency. The value is not the chat tools. "
            "The value is the continuity architecture, the measured savings, and the fact that the system already runs."
        ),
        "one_minute_spoken_script": (
            "I spent about thirteen hundred pounds across the modern AI tool stack. If I had built this the old way, it likely "
            "would have cost between twenty-five thousand and two hundred fifty thousand pounds depending on the team structure. "
            "But the more important difference is not just build cost. The normal new method keeps paying for forgetting, because "
            "every session reloads context and burns tokens again. Project VOID changes that. It remembers. It compresses. It reduces "
            "token spend by over eighty-two percent in the modeled case while producing user-specific world identity, agent resilience logic, "
            "and an auditable continuity trail. So this is not just cheaper software development. It is a third category: infrastructure that pays "
            "back its own memory."
        ),
        "short_lines": [
            "Old method pays for labor.",
            "New method pays for forgetting.",
            "Project VOID pays once, then remembers.",
        ],
    }


def main() -> None:
    bundle = build_bundle()
    out_path = Path("data/project_void_cost_positioning.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    print("PROJECT VOID COST BUNDLE COMPLETE")
    print(f"output: {out_path}")
    print(f"actual_spend_gbp: {ACTUAL_TOOLING_SPEND_GBP}")
    print(f"token_reduction_pct: {TOKEN_REDUCTION_PCT}")
    print(f"project_void_token_ratio: {round(PROJECT_VOID_TOKEN_BASELINE_RATIO, 4)}")


if __name__ == "__main__":
    main()