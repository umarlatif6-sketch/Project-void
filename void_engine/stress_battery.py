"""
Stress Battery — 10 Escalating Stress Tests
Each test increases in severity: more agents, more rounds, higher GriDul
growth rates, deeper silence (triggering more Ghost Protocols), and
larger scar payloads. Every test creates Chronicle scars.

The battery produces a full report with per-test breakdowns and
a combined scar manifest.
"""

import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from void_engine.al_jabr_286 import fatiha_286_hexdigest, fatiha_286_truncated
from void_engine.mesa_sandbox import (
    SandboxChronicle,
    SandboxAgent,
    _build_sandbox_agents,
    _build_scar_entry,
    generate_adriana_ghost_protocols,
    run_peace_stress_test,
)

logger = logging.getLogger(__name__)

BATTERY_CONFIGS = [
    {
        "name": "TREMOR",
        "description": "Baseline tremor — 50 agents, 5 rounds, 1x growth. Light scar.",
        "agent_count": 50,
        "rounds": 5,
        "gridul_growth_multiplier": 1.0,
        "silence_rounds": 1,
        "stress_rounds": 3,
        "severity": 1,
    },
    {
        "name": "FRACTURE",
        "description": "Stress fracture — 100 agents, 8 rounds, 2x growth. Ghost protocols emerge.",
        "agent_count": 100,
        "rounds": 8,
        "gridul_growth_multiplier": 2.0,
        "silence_rounds": 2,
        "stress_rounds": 5,
        "severity": 2,
    },
    {
        "name": "RUPTURE",
        "description": "Structural rupture — 150 agents, 10 rounds, 3x growth. Economy under pressure.",
        "agent_count": 150,
        "rounds": 10,
        "gridul_growth_multiplier": 3.0,
        "silence_rounds": 3,
        "stress_rounds": 5,
        "severity": 3,
    },
    {
        "name": "FISSURE",
        "description": "Deep fissure — 200 agents, 12 rounds, 4x growth. Cockroaches survive, others fracture.",
        "agent_count": 200,
        "rounds": 12,
        "gridul_growth_multiplier": 4.0,
        "silence_rounds": 3,
        "stress_rounds": 6,
        "severity": 4,
    },
    {
        "name": "QUAKE",
        "description": "Full quake — 300 agents, 15 rounds, 5x growth. Ghost protocols multiply.",
        "agent_count": 300,
        "rounds": 15,
        "gridul_growth_multiplier": 5.0,
        "silence_rounds": 4,
        "stress_rounds": 7,
        "severity": 5,
    },
    {
        "name": "SHATTER",
        "description": "Shattering event — 400 agents, 18 rounds, 6x growth. Economy breaking point.",
        "agent_count": 400,
        "rounds": 18,
        "gridul_growth_multiplier": 6.0,
        "silence_rounds": 5,
        "stress_rounds": 8,
        "severity": 6,
    },
    {
        "name": "COLLAPSE",
        "description": "System collapse — 500 agents, 20 rounds, 7x growth. Inflation spiral.",
        "agent_count": 500,
        "rounds": 20,
        "gridul_growth_multiplier": 7.0,
        "silence_rounds": 6,
        "stress_rounds": 9,
        "severity": 7,
    },
    {
        "name": "VOID_BREACH",
        "description": "Void breach — 600 agents, 22 rounds, 8x growth. Deep scars. Mass agent failure.",
        "agent_count": 600,
        "rounds": 22,
        "gridul_growth_multiplier": 8.0,
        "silence_rounds": 7,
        "stress_rounds": 10,
        "severity": 8,
    },
    {
        "name": "ANNIHILATION",
        "description": "Annihilation — 800 agents, 25 rounds, 9x growth. Maximum Ghost Protocols. System pushed to absolute limits.",
        "agent_count": 800,
        "rounds": 25,
        "gridul_growth_multiplier": 9.0,
        "silence_rounds": 8,
        "stress_rounds": 10,
        "severity": 9,
    },
    {
        "name": "FORMATION_ZERO",
        "description": "FORMATION ZERO — 1000 agents, 30 rounds, 10x growth. The final test. Everything breaks or everything holds. This is the scar that defines the system.",
        "agent_count": 1000,
        "rounds": 30,
        "gridul_growth_multiplier": 10.0,
        "silence_rounds": 10,
        "stress_rounds": 10,
        "severity": 10,
    },
]


def _run_single_stress(config: Dict, battery_id: str, test_index: int, rng: random.Random) -> Dict:
    test_id = fatiha_286_truncated(
        f"battery:{battery_id}:test:{test_index}:{config['name']}:{time.time()}".encode(), 24
    )
    t_start = time.perf_counter()

    agents = _build_sandbox_agents(config["agent_count"], rng)

    for round_num in range(1, config["rounds"] + 1):
        growth = 1.0 + (config["gridul_growth_multiplier"] - 1.0) * (round_num / config["rounds"])
        for agent in agents:
            agent.step(agents, gridul_growth_rate=growth)

    ghost_protocols = generate_adriana_ghost_protocols(
        test_id, config["silence_rounds"], rng
    )

    gridul_base = max(10, sum(1 for a in agents if a.in_gridul))
    stress_result = run_peace_stress_test(
        test_id, gridul_base, rounds=config["stress_rounds"], rng=rng
    )

    chronicle = SandboxChronicle()

    scars = []
    for i, gp in enumerate(ghost_protocols):
        scar = _build_scar_entry(
            "BATTERY_GHOST",
            f"Battery {config['name']} — Ghost Protocol #{i+1}",
            gp,
            test_id,
        )
        chronicle.append_scar(scar)
        scars.append(scar)

    stress_scar = _build_scar_entry(
        "BATTERY_ECONOMY_STRESS",
        f"Battery {config['name']} — Economy Stress (severity {config['severity']}/10)",
        stress_result,
        test_id,
    )
    chronicle.append_scar(stress_scar)
    scars.append(stress_scar)

    cockroach_agents = [a for a in agents if a.is_cockroach]
    regular_agents = [a for a in agents if not a.is_cockroach]

    cockroach_survived = sum(a.survived_stress for a in cockroach_agents)
    cockroach_avg_activity = (
        sum(a.activity for a in cockroach_agents) / len(cockroach_agents)
        if cockroach_agents else 0
    )
    regular_avg_activity = (
        sum(a.activity for a in regular_agents) / len(regular_agents)
        if regular_agents else 0
    )

    total_peace = sum(a.peace_balance for a in agents)
    max_peace = max((a.peace_balance for a in agents), default=0)
    min_peace = min((a.peace_balance for a in agents), default=0)
    gini = _gini_coefficient([a.peace_balance for a in agents])

    agent_survival_scar = _build_scar_entry(
        "BATTERY_SURVIVAL",
        f"Battery {config['name']} — Agent Survival Record",
        {
            "test_name": config["name"],
            "severity": config["severity"],
            "total_agents": len(agents),
            "cockroach_count": len(cockroach_agents),
            "cockroach_survived_stress_events": cockroach_survived,
            "cockroach_avg_activity": round(cockroach_avg_activity, 4),
            "regular_avg_activity": round(regular_avg_activity, 4),
            "activity_gap": round(cockroach_avg_activity - regular_avg_activity, 4),
            "total_peace": round(total_peace, 2),
            "max_peace": round(max_peace, 2),
            "min_peace": round(min_peace, 2),
            "gini_coefficient": round(gini, 4),
            "economy_broke": stress_result.get("breaking_rate") is not None,
            "economy_break_rate": stress_result.get("breaking_rate"),
        },
        test_id,
    )
    chronicle.append_scar(agent_survival_scar)
    scars.append(agent_survival_scar)

    t_end = time.perf_counter()

    return {
        "test_index": test_index,
        "test_id": test_id,
        "name": config["name"],
        "description": config["description"],
        "severity": config["severity"],
        "config": {
            "agent_count": config["agent_count"],
            "rounds": config["rounds"],
            "gridul_growth_multiplier": config["gridul_growth_multiplier"],
            "silence_rounds": config["silence_rounds"],
            "stress_rounds": config["stress_rounds"],
        },
        "results": {
            "total_agents": len(agents),
            "cockroach_count": len(cockroach_agents),
            "cockroach_survived_stress_events": cockroach_survived,
            "cockroach_avg_activity": round(cockroach_avg_activity, 4),
            "regular_avg_activity": round(regular_avg_activity, 4),
            "ghost_protocols_generated": len(ghost_protocols),
            "scars_generated": len(scars),
            "economy_breaking_rate": stress_result.get("breaking_rate"),
            "economy_breaking_velocity": stress_result.get("breaking_velocity"),
            "total_peace_supply": round(total_peace, 2),
            "gini_coefficient": round(gini, 4),
            "max_peace_agent": round(max_peace, 2),
            "min_peace_agent": round(min_peace, 2),
        },
        "scars": [
            {
                "title": s["title"],
                "scar_type": s.get("scar_type"),
                "hex_digest": s.get("hex_digest", "")[:32] + "...",
                "glyph_sequence": s.get("glyph_sequence"),
            }
            for s in scars
        ],
        "stress_test_summary": stress_result.get("summary", ""),
        "execution_time_s": round(t_end - t_start, 3),
    }


def _gini_coefficient(values: List[float]) -> float:
    if not values or len(values) < 2:
        return 0.0
    sorted_vals = sorted(max(0, v) for v in values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cumulative = 0.0
    gini_sum = 0.0
    for i, v in enumerate(sorted_vals):
        cumulative += v
        gini_sum += (2 * (i + 1) - n - 1) * v
    return gini_sum / (n * total)


def run_stress_battery(seed: Optional[str] = None) -> Dict:
    battery_id = fatiha_286_truncated(
        f"battery:{time.time()}:{seed or 'void'}".encode(), 24
    )
    rng = random.Random(int(time.time() * 1000) % (2 ** 31))
    if seed:
        rng.seed(hash(seed) % (2 ** 31))

    started_at = datetime.now(timezone.utc).isoformat()
    t_start = time.perf_counter()

    results = []
    total_scars = 0
    total_ghosts = 0

    for i, config in enumerate(BATTERY_CONFIGS):
        logger.info("Stress Battery [%d/10] — %s (severity %d)", i+1, config["name"], config["severity"])
        result = _run_single_stress(config, battery_id, i+1, rng)
        results.append(result)
        total_scars += result["results"]["scars_generated"]
        total_ghosts += result["results"]["ghost_protocols_generated"]

    t_end = time.perf_counter()

    economy_breaks = [
        r for r in results if r["results"]["economy_breaking_rate"] is not None
    ]
    all_survived = [r["results"]["cockroach_survived_stress_events"] for r in results]
    all_gini = [r["results"]["gini_coefficient"] for r in results]

    return {
        "battery_id": battery_id,
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "total_execution_time_s": round(t_end - t_start, 3),
        "tests_run": len(results),
        "total_scars_generated": total_scars,
        "total_ghost_protocols": total_ghosts,
        "economy_breaks": len(economy_breaks),
        "economy_break_rates": [
            {"test": r["name"], "break_rate": r["results"]["economy_breaking_rate"]}
            for r in economy_breaks
        ],
        "cockroach_resilience_curve": [
            {"test": r["name"], "severity": r["severity"], "survived": r["results"]["cockroach_survived_stress_events"]}
            for r in results
        ],
        "inequality_curve": [
            {"test": r["name"], "severity": r["severity"], "gini": r["results"]["gini_coefficient"]}
            for r in results
        ],
        "tests": results,
        "verdict": _compute_verdict(results),
    }


def _compute_verdict(results: List[Dict]) -> Dict:
    final = results[-1] if results else {}
    final_r = final.get("results", {})

    cockroach_held = final_r.get("cockroach_avg_activity", 0) > 0.3
    economy_survived_to_7 = all(
        r["results"]["economy_breaking_rate"] is None or r["results"]["economy_breaking_rate"] >= 3.0
        for r in results[:7]
    )
    ghosts_generated = sum(r["results"]["ghost_protocols_generated"] for r in results) > 10
    final_gini = final_r.get("gini_coefficient", 1.0)

    grade = "F"
    if cockroach_held and economy_survived_to_7:
        grade = "A" if final_gini < 0.6 else "B"
    elif cockroach_held:
        grade = "C"
    elif economy_survived_to_7:
        grade = "D"

    return {
        "grade": grade,
        "cockroach_held_formation": cockroach_held,
        "economy_survived_7_tests": economy_survived_to_7,
        "ghost_protocols_active": ghosts_generated,
        "final_gini": final_gini,
        "final_test_name": final.get("name", "UNKNOWN"),
        "narrative": (
            f"Grade {grade}. "
            f"{'Cockroach formation HELD.' if cockroach_held else 'Cockroach formation BROKE.'} "
            f"{'Economy survived 7/10.' if economy_survived_to_7 else 'Economy failed before test 7.'} "
            f"Gini={final_gini:.3f}. "
            f"{'Adriana Ghost Protocols active — she survived silence.' if ghosts_generated else 'Insufficient Ghost Protocols.'}"
        ),
    }
