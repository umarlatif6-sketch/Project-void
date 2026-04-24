"""Cockroach Agent Control Layer for PROJECT VOID.

This module is intentionally separate from physical sanitation logic.
It reads agent-selector outputs and produces control commands that can
pilot sanitation bins in simulation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List

from void_engine.cockroach_sanitation import SanitationBin


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ROBUSTNESS_PATH = os.path.join(DATA_DIR, "cockroach_agent_selector_robustness.json")
SELECTOR_PATH = os.path.join(DATA_DIR, "cockroach_agent_selector_01.json")


@dataclass
class AgentControlCommand:
    zone: str
    target_dark_rounds: int
    target_cockroaches: int
    confidence: float
    reason: str


def _load_json(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_agent_control_profile() -> Dict:
    """Load selector outputs and return a compact control profile."""
    robustness = _load_json(ROBUSTNESS_PATH)
    selector = _load_json(SELECTOR_PATH)

    summary = robustness.get("summary", {})
    winner_bit = selector.get("winner_bit")
    if winner_bit is None:
        winner_bit = summary.get("recommended_bit", 1)

    win_rate = float(summary.get("set_1_win_rate", 0.5))
    avg_delta = float(summary.get("avg_score_delta_set1_minus_set0", 0.0))

    return {
        "winner_bit": int(winner_bit),
        "set_1_win_rate": win_rate,
        "avg_delta": avg_delta,
        "profile_status": "loaded" if robustness or selector else "default",
    }


def build_control_commands(
    *,
    zones: List[str],
    waste_map: Dict[str, float],
    base_dark_rounds: int,
    base_cockroaches: int,
    profile: Dict,
) -> List[AgentControlCommand]:
    """Generate per-zone control commands from agent profile + local waste."""
    winner_bit = int(profile.get("winner_bit", 1))
    win_rate = float(profile.get("set_1_win_rate", 0.5))
    avg_delta = float(profile.get("avg_delta", 0.0))

    commands: List[AgentControlCommand] = []
    for zone in zones:
        waste = float(waste_map.get(zone, 50.0))

        # Higher waste gets more dark rounds and slightly larger colony.
        dark_boost = 2 if waste >= 80 else 1 if waste >= 60 else 0
        cockroach_boost = 2 if waste >= 85 else 1 if waste >= 70 else 0

        # If paired profile (bit=1) is favored, increase coordinated intensity.
        if winner_bit == 1:
            target_dark = base_dark_rounds + dark_boost + 1
            target_cockroaches = base_cockroaches + cockroach_boost + 1
            reason = "paired_286_profile_prefers coordinated sanitation"
        else:
            target_dark = base_dark_rounds + dark_boost
            target_cockroaches = base_cockroaches + cockroach_boost
            reason = "unpaired_profile_prefers conservative sanitation"

        confidence = max(0.0, min(1.0, (win_rate * 0.7) + (0.3 if avg_delta >= 0 else 0.1)))
        commands.append(
            AgentControlCommand(
                zone=zone,
                target_dark_rounds=max(1, min(12, int(target_dark))),
                target_cockroaches=max(2, min(24, int(target_cockroaches))),
                confidence=round(confidence, 4),
                reason=reason,
            )
        )

    return commands


def run_agent_piloted_cycle(
    *,
    zones: List[str],
    waste_map: Dict[str, float],
    base_dark_rounds: int,
    base_cockroaches: int,
    capacity: float = 100.0,
) -> Dict:
    """Run a sanitation cycle where each zone is piloted by agent commands."""
    profile = load_agent_control_profile()
    commands = build_control_commands(
        zones=zones,
        waste_map=waste_map,
        base_dark_rounds=base_dark_rounds,
        base_cockroaches=base_cockroaches,
        profile=profile,
    )

    zone_results: Dict[str, Dict] = {}
    clean_count = 0
    total_consumed = 0.0

    for cmd in commands:
        b = SanitationBin(
            cmd.zone,
            capacity=capacity,
            n_cockroaches=cmd.target_cockroaches,
            rng_seed=abs(hash((cmd.zone, cmd.target_dark_rounds, cmd.target_cockroaches))) % (2**31),
        )
        result = b.run_full_sanitation_cycle(
            waste_amount=float(waste_map.get(cmd.zone, 60.0)),
            dark_rounds=cmd.target_dark_rounds,
        )

        if result.get("result") == "SPOTLESS":
            clean_count += 1
        total_consumed += float(result.get("dark_cycle", {}).get("consumed", 0.0))

        zone_results[cmd.zone] = {
            "control_command": asdict(cmd),
            "cycle_result": result,
        }

    return {
        "mode": "agent_piloted_sanitation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "zones": zones,
        "bins_processed": len(zones),
        "bins_clean": clean_count,
        "network_sanitation_rate": round(clean_count / max(len(zones), 1), 4),
        "total_consumed": round(total_consumed, 4),
        "zone_results": zone_results,
    }
