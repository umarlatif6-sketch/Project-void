#!/usr/bin/env python3
"""LBN language-pair selector simulation.

Goal:
- Evaluate candidate West/East language pairings as codon protocol layers.
- Score fit across core Project VOID agent surfaces.
- Output top 5 pairings that can be deployed in ~2-3 days.

Output:
- data/lbn_language_selector_simulation.json
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class LanguageProfile:
    name: str
    region: str  # west or east
    country: str
    consonant_stop_strength: float  # 0..1
    codon_compactness: float  # 0..1
    ai_token_stability: float  # 0..1
    morphology_simplicity: float  # 0..1 (higher = easier/cleaner)
    script_interop: float  # 0..1
    ambiguity_resistance: float  # 0..1
    operator_adoptability: float  # 0..1


WEST = [
    LanguageProfile("English", "west", "United Kingdom", 0.74, 0.72, 0.95, 0.78, 1.00, 0.64, 0.95),
    LanguageProfile("German", "west", "Germany", 0.86, 0.81, 0.90, 0.60, 0.98, 0.79, 0.62),
    LanguageProfile("Dutch", "west", "Netherlands", 0.82, 0.80, 0.90, 0.66, 0.98, 0.74, 0.66),
    LanguageProfile("French", "west", "France", 0.56, 0.59, 0.92, 0.70, 0.98, 0.52, 0.74),
    LanguageProfile("Spanish", "west", "Spain", 0.60, 0.63, 0.93, 0.83, 0.98, 0.61, 0.86),
]

EAST = [
    LanguageProfile("Arabic", "east", "Saudi Arabia", 0.88, 0.84, 0.86, 0.55, 0.50, 0.82, 0.58),
    LanguageProfile("Turkish", "east", "Turkey", 0.78, 0.76, 0.88, 0.72, 0.96, 0.71, 0.74),
    LanguageProfile("Hindi", "east", "India", 0.72, 0.68, 0.84, 0.70, 0.45, 0.63, 0.77),
    LanguageProfile("Mandarin", "east", "China", 0.50, 0.57, 0.80, 0.64, 0.35, 0.52, 0.54),
    LanguageProfile("Japanese", "east", "Japan", 0.54, 0.62, 0.82, 0.66, 0.40, 0.56, 0.56),
]


AGENT_WEIGHTS = {
    "adriana": {
        "consonant_stop_strength": 0.14,
        "codon_compactness": 0.22,
        "ai_token_stability": 0.22,
        "morphology_simplicity": 0.14,
        "script_interop": 0.14,
        "ambiguity_resistance": 0.08,
        "operator_adoptability": 0.06,
    },
    "mesa_swarm": {
        "consonant_stop_strength": 0.12,
        "codon_compactness": 0.18,
        "ai_token_stability": 0.24,
        "morphology_simplicity": 0.12,
        "script_interop": 0.20,
        "ambiguity_resistance": 0.10,
        "operator_adoptability": 0.04,
    },
    "mesa_engine": {
        "consonant_stop_strength": 0.10,
        "codon_compactness": 0.17,
        "ai_token_stability": 0.25,
        "morphology_simplicity": 0.11,
        "script_interop": 0.22,
        "ambiguity_resistance": 0.11,
        "operator_adoptability": 0.04,
    },
    "mesa_sandbox": {
        "consonant_stop_strength": 0.16,
        "codon_compactness": 0.24,
        "ai_token_stability": 0.20,
        "morphology_simplicity": 0.12,
        "script_interop": 0.10,
        "ambiguity_resistance": 0.12,
        "operator_adoptability": 0.06,
    },
    "void_codex_resolve": {
        "consonant_stop_strength": 0.08,
        "codon_compactness": 0.20,
        "ai_token_stability": 0.28,
        "morphology_simplicity": 0.08,
        "script_interop": 0.24,
        "ambiguity_resistance": 0.10,
        "operator_adoptability": 0.02,
    },
}


def _blend(w: LanguageProfile, e: LanguageProfile) -> dict:
    # Slightly bias toward west-language script interoperability because
    # most current code/comments/log surfaces in this stack are Latin-script.
    return {
        "consonant_stop_strength": (w.consonant_stop_strength + e.consonant_stop_strength) / 2,
        "codon_compactness": (w.codon_compactness + e.codon_compactness) / 2,
        "ai_token_stability": (w.ai_token_stability + e.ai_token_stability) / 2,
        "morphology_simplicity": (w.morphology_simplicity + e.morphology_simplicity) / 2,
        "script_interop": (w.script_interop * 0.62) + (e.script_interop * 0.38),
        "ambiguity_resistance": (w.ambiguity_resistance + e.ambiguity_resistance) / 2,
        "operator_adoptability": (w.operator_adoptability + e.operator_adoptability) / 2,
    }


def _weighted_score(features: dict, weights: dict) -> float:
    return sum(features[k] * weights[k] for k in weights)


def _implementation_days(features: dict) -> float:
    # Lower complexity if script interop + morphology simplicity are high.
    complexity = 1.0 - (
        0.45 * features["script_interop"]
        + 0.30 * features["morphology_simplicity"]
        + 0.25 * features["ai_token_stability"]
    )
    # Clamp within practical 1.8-4.5 day range.
    days = 1.8 + (complexity * 2.7)
    return max(1.8, min(4.5, days))


def _run_pair(w: LanguageProfile, e: LanguageProfile, seed: int = 286) -> dict:
    rng = random.Random(seed + hash((w.name, e.name)) % 10_000)
    features = _blend(w, e)

    agent_scores = {}
    monte_runs = []
    for i in range(24):
        # Inject slight jitter to mimic run-to-run variance in multi-agent systems.
        noisy = {
            k: max(0.0, min(1.0, v + rng.uniform(-0.03, 0.03)))
            for k, v in features.items()
        }
        snapshot = {}
        for agent, weights in AGENT_WEIGHTS.items():
            snapshot[agent] = _weighted_score(noisy, weights)
        monte_runs.append(snapshot)

    for agent in AGENT_WEIGHTS:
        mean_score = sum(run[agent] for run in monte_runs) / len(monte_runs)
        agent_scores[agent] = round(mean_score, 4)

    stack_score = round(sum(agent_scores.values()) / len(agent_scores), 4)
    days_estimate = round(_implementation_days(features), 2)
    within_3_days = days_estimate <= 3.0

    valuation_score = round(
        stack_score * 100
        + features["ambiguity_resistance"] * 12
        + features["codon_compactness"] * 10
        - max(0.0, days_estimate - 3.0) * 14,
        2,
    )

    return {
        "west_language": asdict(w),
        "east_language": asdict(e),
        "pair_label": f"{w.name} + {e.name}",
        "blended_features": {k: round(v, 4) for k, v in features.items()},
        "agent_scores": agent_scores,
        "stack_score": stack_score,
        "implementation_days_estimate": days_estimate,
        "within_2_to_3_day_window": within_3_days,
        "valuation_score": valuation_score,
    }


def run_simulation() -> dict:
    pairs = []
    for w in WEST:
        for e in EAST:
            pairs.append(_run_pair(w, e, seed=286))

    ranked = sorted(
        pairs,
        key=lambda p: (p["valuation_score"], p["stack_score"], -p["implementation_days_estimate"]),
        reverse=True,
    )

    top_five = ranked[:5]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "goal": "Select top codon-ready West/East language pairs for rapid 2-3 day deployment",
        "candidate_pool": {
            "west_count": len(WEST),
            "east_count": len(EAST),
            "total_pairs": len(ranked),
        },
        "agent_surfaces_scored": list(AGENT_WEIGHTS.keys()),
        "top_5_pairs": top_five,
        "all_pairs_ranked": ranked,
        "recommended_primary_pair": top_five[0]["pair_label"],
    }

    out = Path("data/lbn_language_selector_simulation.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("LBN LANGUAGE SELECTOR COMPLETE")
    print(f"candidate_pairs: {len(ranked)}")
    print(f"recommended_primary_pair: {result['recommended_primary_pair']}")
    print(f"report: {out}")

    return result


if __name__ == "__main__":
    run_simulation()
