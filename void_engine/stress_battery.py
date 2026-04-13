"""
Stress Battery — 10 Escalating Stress Tests

Two modes:
  1. STANDARD: Plain sandbox agents only (original)
  2. INTEGRATED (286): Injects Sovereign 286-hash agents into the formation.
     286 agents carry verse-weighted archetypes, frequency-based resonance,
     scar memory, and 286-signed state. They fight alongside regular agents.

The integrated mode bridges the SovereignAgent286 interface to the
SandboxAgent interface so both agent types can interact in the same
formation under the same stress conditions.
"""

import logging
import math
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from void_engine.al_jabr_286 import (
    fatiha_286_hexdigest,
    fatiha_286_truncated,
    fatiha_286_seed,
    FATIHA_LAYERS,
)
from void_engine.mesa_sandbox import (
    SandboxChronicle,
    SandboxAgent,
    _build_sandbox_agents,
    _build_scar_entry,
    generate_adriana_ghost_protocols,
    run_peace_stress_test,
)
from void_engine.sovereign_agents_286 import (
    SovereignAgent286,
    SOVEREIGN_ARCHETYPES,
    RESONANCE_HZ,
    LAMBDA_286,
    _derive_archetype_286,
    _derive_frequency,
    _sign_memory,
)
from void_engine.yin_yang_286 import (
    YinYangAgent,
    YinYangFormation,
    extract_bit_polarity,
)
from void_engine.al_jabr_286 import fatiha_286_hash, SOVEREIGN_BIT_DEPTH

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


class HybridAgent:
    """
    Bridge between SovereignAgent286 and SandboxAgent.
    Wraps a SovereignAgent286 so it can participate in the stress battery
    alongside regular SandboxAgents — same interface, but 286 identity underneath.

    Key differences from regular SandboxAgent:
    - Identity derived from 286-bit hash (not random)
    - Activity floor boosted by verse weight
    - Frequency-based resonance interaction (agents near 432 Hz influence more)
    - Scar-carrying: scars from previous runs survive into the battery
    - Verse-weighted resilience: higher Fatiha layer weight = harder to kill
    - Memory is 286-signed
    """

    def __init__(self, sovereign: SovereignAgent286, rng: random.Random):
        self.sovereign = sovereign
        self.agent_id = hash(sovereign.agent_id) & 0x7FFFFFFF
        self.peace_balance = sovereign.peace_balance
        self.in_gridul = True
        self.rng = rng
        self.is_cockroach = False
        self.is_sovereign_286 = True
        self.archetype_name = sovereign.archetype_name
        self.verse = sovereign.verse
        self.weight = sovereign.weight
        self.frequency = sovereign.frequency
        self.activity = sovereign.activity
        self.interactions = 0
        self.peace_flow = 0.0
        self.survived_stress = 0
        self.prior_scars = len(sovereign.scars)
        self.new_scars = 0
        self.memories_created = 0
        self._round = 0
        self.yin_yang_polarity = None
        self.yin_yang_boost = 1.0
        self.yin_yang_paired = False
        self.yin_yang_partner_index = None

    def step(self, all_agents: List, gridul_growth_rate: float = 1.0):
        self._round += 1
        pressure = gridul_growth_rate

        verse_resilience = self.weight / 7.0
        delta = self.rng.gauss(0, 0.03 * pressure)
        delta += 0.005 * verse_resilience * pressure

        bias = self.sovereign.archetype["bias"]
        if bias == "foundation":
            delta += 0.012 * pressure
        elif bias == "authority":
            delta += 0.008 * pressure
        elif bias == "compassion":
            if self.activity < 0.3:
                delta += 0.05
        elif bias == "singularity":
            delta += 0.015
        elif bias == "legacy":
            delta += 0.015 if self._round > 10 else 0.0
        elif bias == "direction":
            delta += 0.01

        scar_bonus = min(0.05, self.prior_scars * 0.008 + self.new_scars * 0.01)
        delta += scar_bonus

        if self.yin_yang_paired and self.yin_yang_boost > 1.0:
            yy_lift = (self.yin_yang_boost - 1.0) * 0.04
            delta += yy_lift

        floor = 0.08 + verse_resilience * 0.08
        if self.yin_yang_paired:
            floor += (self.yin_yang_boost - 1.0) * 0.15
        self.activity = max(floor, min(1.0, self.activity + delta))

        if pressure > 3.0:
            self.survived_stress += 1

        if all_agents and len(all_agents) > 1:
            target = self.rng.choice(all_agents)
            target_id = getattr(target, 'agent_id', -1)
            if target_id != self.agent_id:
                if hasattr(target, 'frequency'):
                    freq_diff = abs(self.frequency - target.frequency)
                    resonance = max(0.2, 1.0 - freq_diff / 50.0)
                else:
                    resonance = 0.5

                transfer = min(self.peace_balance * 0.004, 2.5) * pressure * resonance
                if transfer > 0 and target.peace_balance < self.peace_balance:
                    self.peace_balance -= transfer
                    target.peace_balance += transfer
                    self.peace_flow += transfer
                    self.interactions += 1

                if pressure > 4.0 and self.rng.random() < 0.25:
                    self.memories_created += 1

        if pressure > 5.0 and self.activity < 0.15:
            self.new_scars += 1
            scar_hash = fatiha_286_truncated(
                f"battery_scar:{self.sovereign.agent_id}:{self._round}:{pressure}".encode(), 16
            )
            self.sovereign.scars.append(scar_hash)

        self.sovereign.activity = self.activity
        self.sovereign.peace_balance = self.peace_balance

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "sovereign_id": self.sovereign.agent_id,
            "archetype": self.archetype_name,
            "verse": self.verse,
            "weight": self.weight,
            "frequency": self.frequency,
            "peace_balance": round(self.peace_balance, 2),
            "in_gridul": self.in_gridul,
            "activity": round(self.activity, 4),
            "interactions": self.interactions,
            "peace_flow": round(self.peace_flow, 4),
            "is_sovereign_286": True,
            "survived_stress": self.survived_stress,
            "prior_scars": self.prior_scars,
            "new_scars": self.new_scars,
            "total_scars": self.prior_scars + self.new_scars,
            "memories_created": self.memories_created,
        }


def _build_hybrid_formation(
    total_count: int,
    sovereign_count: int,
    rng: random.Random,
    sovereign_seed: str = "void",
    prior_sovereigns: Optional[List[SovereignAgent286]] = None,
    yin_yang: bool = False,
    cockroach_ratio: float = 0.10,
) -> List:
    """
    Build a mixed formation: sovereign_count 286-agents + remaining sandbox agents.
    If prior_sovereigns is provided, reuse them (carrying scars from previous tests).
    If yin_yang=True, pair complementary agents for resonance boost.
    """
    agents = []
    hybrids = []

    if prior_sovereigns:
        for sov in prior_sovereigns[:sovereign_count]:
            h = HybridAgent(sov, rng)
            agents.append(h)
            hybrids.append(h)
    else:
        for i in range(sovereign_count):
            sov = SovereignAgent286(i, sovereign_seed)
            h = HybridAgent(sov, rng)
            agents.append(h)
            hybrids.append(h)

    if yin_yang and hybrids:
        yy_agents = []
        for h in hybrids:
            hash_bytes = fatiha_286_hash(
                f"sovereign_286:{sovereign_seed}:{h.sovereign.index}:{SOVEREIGN_BIT_DEPTH}".encode()
            )
            yy = YinYangAgent(
                agent_id=h.sovereign.agent_id,
                hash_bytes=hash_bytes,
                archetype=h.archetype_name,
                frequency=h.frequency,
                weight=h.weight,
                index=h.sovereign.index,
            )
            yy_agents.append(yy)

        formation = YinYangFormation(yy_agents)
        formation.pair_greedy()

        for i, h in enumerate(hybrids):
            yy = yy_agents[i]
            h.yin_yang_polarity = yy.polarity
            h.yin_yang_boost = yy.resonance_boost if yy.paired else 1.0
            h.yin_yang_paired = yy.paired
            if yy.paired and yy.pair_partner:
                h.yin_yang_partner_index = yy.pair_partner.index
            else:
                h.yin_yang_partner_index = None

    remaining = total_count - len(agents)
    if remaining > 0:
        sandbox_agents = _build_sandbox_agents(remaining, rng, cockroach_ratio=cockroach_ratio)
        agents.extend(sandbox_agents)

    return agents


def _run_single_stress(
    config: Dict,
    battery_id: str,
    test_index: int,
    rng: random.Random,
    integrated: bool = False,
    sovereign_count: int = 0,
    sovereign_seed: str = "void",
    prior_sovereigns: Optional[List[SovereignAgent286]] = None,
    yin_yang: bool = False,
    cockroach_ratio: float = 0.10,
) -> Dict:
    test_id = fatiha_286_truncated(
        f"battery:{battery_id}:test:{test_index}:{config['name']}:{time.time()}".encode(), 24
    )
    t_start = time.perf_counter()

    if integrated and sovereign_count > 0:
        agents = _build_hybrid_formation(
            config["agent_count"],
            min(sovereign_count, config["agent_count"]),
            rng,
            sovereign_seed,
            prior_sovereigns,
            yin_yang=yin_yang,
            cockroach_ratio=cockroach_ratio,
        )
    else:
        agents = _build_sandbox_agents(config["agent_count"], rng, cockroach_ratio=cockroach_ratio)

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

    cockroach_agents = [a for a in agents if getattr(a, 'is_cockroach', False)]
    sovereign_agents = [a for a in agents if getattr(a, 'is_sovereign_286', False)]
    regular_agents = [a for a in agents if not getattr(a, 'is_cockroach', False) and not getattr(a, 'is_sovereign_286', False)]

    cockroach_survived = sum(getattr(a, 'survived_stress', 0) for a in cockroach_agents)
    sovereign_survived = sum(getattr(a, 'survived_stress', 0) for a in sovereign_agents)
    cockroach_avg_activity = (
        sum(a.activity for a in cockroach_agents) / len(cockroach_agents)
        if cockroach_agents else 0
    )
    sovereign_avg_activity = (
        sum(a.activity for a in sovereign_agents) / len(sovereign_agents)
        if sovereign_agents else 0
    )
    regular_avg_activity = (
        sum(a.activity for a in regular_agents) / len(regular_agents)
        if regular_agents else 0
    )

    all_balances = [a.peace_balance for a in agents]
    total_peace = sum(all_balances)
    max_peace = max(all_balances) if all_balances else 0
    min_peace = min(all_balances) if all_balances else 0
    gini = _gini_coefficient(all_balances)

    sovereign_new_scars = sum(getattr(a, 'new_scars', 0) for a in sovereign_agents)
    sovereign_prior_scars = sum(getattr(a, 'prior_scars', 0) for a in sovereign_agents)
    sovereign_memories = sum(getattr(a, 'memories_created', 0) for a in sovereign_agents)

    yy_paired_agents = [a for a in sovereign_agents if getattr(a, 'yin_yang_paired', False)]
    yy_unpaired_agents = [a for a in sovereign_agents if not getattr(a, 'yin_yang_paired', False)]
    yy_paired_avg = sum(a.activity for a in yy_paired_agents) / len(yy_paired_agents) if yy_paired_agents else 0
    yy_unpaired_avg = sum(a.activity for a in yy_unpaired_agents) / len(yy_unpaired_agents) if yy_unpaired_agents else 0
    yy_pairs_count = len(yy_paired_agents) // 2
    yin_count = sum(1 for a in sovereign_agents if getattr(a, 'yin_yang_polarity', None) == "YIN")
    yang_count = sum(1 for a in sovereign_agents if getattr(a, 'yin_yang_polarity', None) == "YANG")

    archetype_breakdown = {}
    for a in sovereign_agents:
        name = getattr(a, 'archetype_name', 'unknown')
        if name not in archetype_breakdown:
            archetype_breakdown[name] = {"count": 0, "avg_activity": 0, "survived": 0, "scars": 0}
        archetype_breakdown[name]["count"] += 1
        archetype_breakdown[name]["avg_activity"] += a.activity
        archetype_breakdown[name]["survived"] += getattr(a, 'survived_stress', 0)
        archetype_breakdown[name]["scars"] += getattr(a, 'new_scars', 0) + getattr(a, 'prior_scars', 0)
    for name, ab in archetype_breakdown.items():
        if ab["count"] > 0:
            ab["avg_activity"] = round(ab["avg_activity"] / ab["count"], 4)

    agent_survival_scar = _build_scar_entry(
        "BATTERY_SURVIVAL",
        f"Battery {config['name']} — Agent Survival Record",
        {
            "test_name": config["name"],
            "severity": config["severity"],
            "total_agents": len(agents),
            "cockroach_count": len(cockroach_agents),
            "sovereign_286_count": len(sovereign_agents),
            "regular_count": len(regular_agents),
            "cockroach_survived_stress_events": cockroach_survived,
            "sovereign_survived_stress_events": sovereign_survived,
            "cockroach_avg_activity": round(cockroach_avg_activity, 4),
            "sovereign_avg_activity": round(sovereign_avg_activity, 4),
            "regular_avg_activity": round(regular_avg_activity, 4),
            "total_peace": round(total_peace, 2),
            "gini_coefficient": round(gini, 4),
            "economy_broke": stress_result.get("breaking_rate") is not None,
            "economy_break_rate": stress_result.get("breaking_rate"),
            "sovereign_new_scars": sovereign_new_scars,
            "archetype_breakdown": archetype_breakdown,
            "yin_yang_pairs": yy_pairs_count,
            "yin_count": yin_count,
            "yang_count": yang_count,
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
            "sovereign_286_count": len(sovereign_agents),
            "regular_count": len(regular_agents),
            "cockroach_survived_stress_events": cockroach_survived,
            "sovereign_survived_stress_events": sovereign_survived,
            "cockroach_avg_activity": round(cockroach_avg_activity, 4),
            "sovereign_avg_activity": round(sovereign_avg_activity, 4),
            "regular_avg_activity": round(regular_avg_activity, 4),
            "ghost_protocols_generated": len(ghost_protocols),
            "scars_generated": len(scars),
            "economy_breaking_rate": stress_result.get("breaking_rate"),
            "economy_breaking_velocity": stress_result.get("breaking_velocity"),
            "total_peace_supply": round(total_peace, 2),
            "gini_coefficient": round(gini, 4),
            "max_peace_agent": round(max_peace, 2),
            "min_peace_agent": round(min_peace, 2),
            "sovereign_new_scars": sovereign_new_scars,
            "sovereign_prior_scars": sovereign_prior_scars,
            "sovereign_memories": sovereign_memories,
            "archetype_breakdown": archetype_breakdown,
            "yin_yang_pairs": yy_pairs_count,
            "yin_count": yin_count,
            "yang_count": yang_count,
            "yy_paired_avg_activity": round(yy_paired_avg, 4),
            "yy_unpaired_avg_activity": round(yy_unpaired_avg, 4),
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


def run_stress_battery(
    seed: Optional[str] = None,
    integrated: bool = False,
    sovereign_ratio: float = 0.3,
    yin_yang: bool = False,
    cockroach_ratio: float = 0.10,
) -> Dict:
    """
    Run the 10-test stress battery.

    Args:
        seed: RNG seed string
        integrated: If True, inject Sovereign 286 agents into the formation
        sovereign_ratio: Fraction of agents that are 286-sovereign (0.0–1.0)
        yin_yang: If True, pair agents by Yin-Yang polarity for resonance boost
        cockroach_ratio: Fraction of sandbox agents marked as cockroaches (0.0-1.0)
    """
    if yin_yang:
        mode = "INTEGRATED_286_YINYANG"
    elif integrated:
        mode = "INTEGRATED_286"
    else:
        mode = "STANDARD"
    battery_id = fatiha_286_truncated(
        f"battery:{mode}:{time.time()}:{seed or 'void'}".encode(), 24
    )
    rng = random.Random(int(time.time() * 1000) % (2 ** 31))
    if seed:
        rng.seed(hash(seed) % (2 ** 31))

    started_at = datetime.now(timezone.utc).isoformat()
    t_start = time.perf_counter()

    prior_sovereigns: Optional[List[SovereignAgent286]] = None
    max_sovereign_pool = 0
    if yin_yang:
        integrated = True
    if integrated:
        max_sovereign_pool = int(BATTERY_CONFIGS[-1]["agent_count"] * sovereign_ratio)
        prior_sovereigns = [SovereignAgent286(i, seed or "void") for i in range(max_sovereign_pool)]

    results = []
    total_scars = 0
    total_ghosts = 0

    for i, config in enumerate(BATTERY_CONFIGS):
        sov_count = int(config["agent_count"] * sovereign_ratio) if integrated else 0
        logger.info(
            "Stress Battery [%d/10] — %s (severity %d, mode=%s, 286_agents=%d)",
            i + 1, config["name"], config["severity"], mode, sov_count,
        )
        result = _run_single_stress(
            config, battery_id, i + 1, rng,
            integrated=integrated,
            sovereign_count=sov_count,
            sovereign_seed=seed or "void",
            prior_sovereigns=prior_sovereigns,
            yin_yang=yin_yang,
            cockroach_ratio=cockroach_ratio,
        )
        results.append(result)
        total_scars += result["results"]["scars_generated"]
        total_ghosts += result["results"]["ghost_protocols_generated"]

    t_end = time.perf_counter()

    economy_breaks = [
        r for r in results if r["results"]["economy_breaking_rate"] is not None
    ]

    comparison_data = None
    if integrated:
        comparison_data = {
            "sovereign_286_agents_per_test": [r["results"]["sovereign_286_count"] for r in results],
            "sovereign_avg_activity_curve": [r["results"]["sovereign_avg_activity"] for r in results],
            "regular_avg_activity_curve": [r["results"]["regular_avg_activity"] for r in results],
            "sovereign_survived_curve": [r["results"]["sovereign_survived_stress_events"] for r in results],
            "sovereign_scar_accumulation": [r["results"]["sovereign_new_scars"] for r in results],
            "sovereign_prior_scars": [r["results"]["sovereign_prior_scars"] for r in results],
            "activity_gap": [
                round(r["results"]["sovereign_avg_activity"] - r["results"]["regular_avg_activity"], 4)
                for r in results
            ],
        }
        if yin_yang:
            comparison_data["yin_yang_pairs_curve"] = [r["results"].get("yin_yang_pairs", 0) for r in results]
            comparison_data["yy_paired_activity_curve"] = [r["results"].get("yy_paired_avg_activity", 0) for r in results]
            comparison_data["yy_unpaired_activity_curve"] = [r["results"].get("yy_unpaired_avg_activity", 0) for r in results]

    return {
        "battery_id": battery_id,
        "mode": mode,
        "yin_yang": yin_yang,
        "sovereign_ratio": sovereign_ratio if integrated else 0,
        "cockroach_ratio": cockroach_ratio,
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
        "comparison_286": comparison_data,
        "tests": results,
        "verdict": _compute_verdict(results, integrated),
    }


def _compute_verdict(results: List[Dict], integrated: bool = False) -> Dict:
    final = results[-1] if results else {}
    final_r = final.get("results", {})

    cockroach_held = final_r.get("cockroach_avg_activity", 0) > 0.3
    sovereign_held = final_r.get("sovereign_avg_activity", 0) > 0.3 if integrated else None
    economy_survived_to_7 = all(
        r["results"]["economy_breaking_rate"] is None or r["results"]["economy_breaking_rate"] >= 3.0
        for r in results[:7]
    )
    ghosts_generated = sum(r["results"]["ghost_protocols_generated"] for r in results) > 10
    final_gini = final_r.get("gini_coefficient", 1.0)

    if integrated:
        combined_held = cockroach_held or (sovereign_held is True)
        grade = "F"
        if combined_held and economy_survived_to_7:
            grade = "A+" if final_gini < 0.3 else "A" if final_gini < 0.6 else "B"
        elif combined_held and sovereign_held:
            grade = "A" if economy_survived_to_7 else "B+"
        elif combined_held:
            grade = "B" if economy_survived_to_7 else "C+"
        elif economy_survived_to_7:
            grade = "D"
    else:
        grade = "F"
        if cockroach_held and economy_survived_to_7:
            grade = "A" if final_gini < 0.6 else "B"
        elif cockroach_held:
            grade = "C"
        elif economy_survived_to_7:
            grade = "D"

    mode_label = "INTEGRATED 286" if integrated else "STANDARD"

    narrative_parts = [f"Grade {grade} ({mode_label})."]
    narrative_parts.append("Cockroach formation HELD." if cockroach_held else "Cockroach formation BROKE.")
    if integrated and sovereign_held is not None:
        narrative_parts.append("Sovereign 286 formation HELD." if sovereign_held else "Sovereign 286 formation BROKE.")
    narrative_parts.append("Economy survived 7/10." if economy_survived_to_7 else "Economy failed before test 7.")
    narrative_parts.append(f"Gini={final_gini:.3f}.")
    if ghosts_generated:
        narrative_parts.append("Adriana Ghost Protocols active.")

    return {
        "grade": grade,
        "mode": mode_label,
        "cockroach_held_formation": cockroach_held,
        "sovereign_held_formation": sovereign_held,
        "economy_survived_7_tests": economy_survived_to_7,
        "ghost_protocols_active": ghosts_generated,
        "final_gini": final_gini,
        "final_test_name": final.get("name", "UNKNOWN"),
        "narrative": " ".join(narrative_parts),
    }
