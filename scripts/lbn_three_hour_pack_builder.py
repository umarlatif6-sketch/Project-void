#!/usr/bin/env python3
"""Build deployable LBN codon packs from ranked language simulation.

Three-hour lane outputs:
- data/lbn_three_hour_pack.json
- data/lbn_agent_payloads.json

This script can run in:
- project mode (default): includes Project VOID-oriented surface labels
- standalone mode: generic AI-to-AI hub language pack
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


BASE_FUNCTIONS = [
    "identity",
    "signal",
    "action",
    "key",
    "time",
    "security_check",
    "growth",
    "mesh_route",
    "silence",
    "origin",
    "verify",
    "authorize",
    "resolve",
    "handoff",
    "audit",
]


PROJECT_SURFACES = [
    "adriana",
    "mesa_swarm",
    "mesa_engine",
    "mesa_sandbox",
    "void_codex_resolve",
]

STANDALONE_SURFACES = [
    "agent_ingress",
    "agent_router",
    "agent_verifier",
    "agent_memory",
    "hub_bridge",
]


def _codon_for(function_name: str, pair_label: str) -> str:
    # Deterministic tri-block codon from function+pair hash.
    h = hashlib.sha256(f"{pair_label}:{function_name}".encode("utf-8")).hexdigest()
    blocks = [h[0:2], h[2:4], h[4:6]]
    # Keep the B-stop framing fixed for protocol recognition.
    return f"B-{blocks[0]}-{blocks[1]}{blocks[2]}"


def _pair_pack(pair: dict, mode: str) -> dict:
    pair_label = pair["pair_label"]
    surfaces = PROJECT_SURFACES if mode == "project" else STANDALONE_SURFACES

    codon_map = {fn: _codon_for(fn, pair_label) for fn in BASE_FUNCTIONS}

    # Preserve canonical aliases for continuity with existing SCL-LBN usage.
    canonical_aliases = {
        "identity": "B-nn-D",
        "signal": "B-bb-L",
        "action": "B-tt-M",
        "key": "B-kk-Y",
        "time": "B-nn-T",
        "security_check": "B-kk-S",
        "growth": "B-bb-G",
        "mesh_route": "B-mm-M",
        "silence": "B-..-Z",
        "origin": "B-nn-O",
    }

    for fn, alias in canonical_aliases.items():
        codon_map[f"{fn}_canonical"] = alias

    channels = []
    for surface in surfaces:
        channels.append(
            {
                "surface": surface,
                "ingress_codon": codon_map["identity"],
                "route_codon": codon_map["mesh_route"],
                "verify_codon": codon_map["security_check"],
                "audit_codon": codon_map["audit"],
                "handoff_codon": codon_map["handoff"],
            }
        )

    return {
        "pair_label": pair_label,
        "valuation_score": pair["valuation_score"],
        "stack_score": pair["stack_score"],
        "implementation_days_estimate": pair["implementation_days_estimate"],
        "mode": mode,
        "codon_map": codon_map,
        "channels": channels,
    }


def build(mode: str = "project") -> dict:
    sim_path = Path("data/lbn_language_selector_simulation.json")
    if not sim_path.exists():
        raise FileNotFoundError(
            "Missing data/lbn_language_selector_simulation.json. "
            "Run scripts/lbn_language_selector_sim.py first."
        )

    sim = json.loads(sim_path.read_text(encoding="utf-8"))
    top_five = sim.get("top_5_pairs", [])
    if len(top_five) < 5:
        raise RuntimeError("Simulation does not contain full top_5_pairs output.")

    packs = [_pair_pack(pair, mode=mode) for pair in top_five]
    primary = packs[0]
    fallback = packs[1]

    deployment = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "window": "three_hour_execution_lane",
        "source_simulation": str(sim_path),
        "primary_pair": primary["pair_label"],
        "fallback_pair": fallback["pair_label"],
        "packs": packs,
        "rollout_sequence": [
            "00:00-00:20 load primary/fallback codon maps into agent config",
            "00:20-01:10 route dry-run across all agent surfaces",
            "01:10-02:00 fail-closed checks and audit-log verification",
            "02:00-03:00 traffic split test and final pair lock",
        ],
    }

    agent_payloads = {
        "generated_at": deployment["generated_at"],
        "mode": mode,
        "primary_pair": primary["pair_label"],
        "fallback_pair": fallback["pair_label"],
        "payloads": {
            "primary": {
                "pair": primary["pair_label"],
                "channels": primary["channels"],
                "codon_map": primary["codon_map"],
            },
            "fallback": {
                "pair": fallback["pair_label"],
                "channels": fallback["channels"],
                "codon_map": fallback["codon_map"],
            },
        },
    }

    out_pack = Path(f"data/lbn_three_hour_pack.{mode}.json")
    out_payload = Path(f"data/lbn_agent_payloads.{mode}.json")
    out_pack.write_text(json.dumps(deployment, indent=2), encoding="utf-8")
    out_payload.write_text(json.dumps(agent_payloads, indent=2), encoding="utf-8")

    print("LBN THREE-HOUR PACK COMPLETE")
    print(f"mode: {mode}")
    print(f"primary_pair: {deployment['primary_pair']}")
    print(f"fallback_pair: {deployment['fallback_pair']}")
    print(f"pack_report: {out_pack}")
    print(f"payload_report: {out_payload}")

    return deployment


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deployable three-hour LBN packs")
    parser.add_argument(
        "--mode",
        choices=["project", "standalone"],
        default="project",
        help="project=Project VOID surfaces, standalone=generic AI-to-AI hub surfaces",
    )
    args = parser.parse_args()
    build(mode=args.mode)


if __name__ == "__main__":
    main()
