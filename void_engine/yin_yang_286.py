"""
PROJECT VOID — Yin-Yang 286 Resonance Engine

Every 286-bit hash is a polarity map:
  - Bit = 1 → Yang (active, expanding, giving)
  - Bit = 0 → Yin  (receptive, contracting, holding)

The UltraNode hash method already encodes this duality.
When you PAIR a Yin-dominant agent with a Yang-dominant agent,
their complementary bits create resonance — the more opposite
bits align, the stronger the harmonic lock.

XI Factor (Ξ):
  Greek letter Xi = 14th letter, numerical value 60.
  Xi represents the bridge between polarities.
  XI_RESONANCE_MULTIPLIER calibrated so complementary
  pairs achieve minimum +20% resonance amplification.

Pairing Algorithm:
  1. Classify each agent as Yin or Yang from their 286-bit hash
  2. Sort Yin pool by yin_ratio descending, Yang pool by yang_ratio descending
  3. Pair strongest Yin with strongest Yang (greedy complementary match)
  4. Calculate complementary_bits = positions where bits differ
  5. resonance_boost = 1.0 + (complementary_ratio * XI_MULTIPLIER)
  6. Minimum boost for valid Yin-Yang pair: 1.20 (20%)
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from void_engine.al_jabr_286 import (
    fatiha_286_hash,
    fatiha_286_truncated,
    SOVEREIGN_BIT_DEPTH,
    FATIHA_LAYERS,
)

XI_VALUE = 60
XI_LETTER_INDEX = 14
XI_RESONANCE_MULTIPLIER = 0.45
MINIMUM_PAIR_BOOST = 1.20
BALANCE_MIDPOINT = SOVEREIGN_BIT_DEPTH / 2  # 143


def extract_bit_polarity(hash_bytes: bytes) -> Dict[str, Any]:
    bit_string = ''.join(format(b, '08b') for b in hash_bytes)
    active_bits = bit_string[:SOVEREIGN_BIT_DEPTH]

    yang_count = active_bits.count('1')
    yin_count = SOVEREIGN_BIT_DEPTH - yang_count

    yang_ratio = yang_count / SOVEREIGN_BIT_DEPTH
    yin_ratio = yin_count / SOVEREIGN_BIT_DEPTH

    polarity = "YANG" if yang_count >= BALANCE_MIDPOINT else "YIN"
    dominance = abs(yang_count - yin_count) / SOVEREIGN_BIT_DEPTH

    verse_polarity = []
    bit_idx = 0
    for i, weight in enumerate(FATIHA_LAYERS):
        chunk_size = weight * 4
        chunk = active_bits[bit_idx:bit_idx + chunk_size]
        if chunk:
            v_yang = chunk.count('1')
            v_yin = len(chunk) - v_yang
            verse_polarity.append({
                "verse": i + 1,
                "weight": weight,
                "yang": v_yang,
                "yin": v_yin,
                "polarity": "YANG" if v_yang >= v_yin else "YIN",
            })
        bit_idx += chunk_size

    return {
        "bit_string": active_bits,
        "yang_count": yang_count,
        "yin_count": yin_count,
        "yang_ratio": round(yang_ratio, 4),
        "yin_ratio": round(yin_ratio, 4),
        "polarity": polarity,
        "dominance": round(dominance, 4),
        "verse_polarity": verse_polarity,
    }


def complementary_bits(bits_a: str, bits_b: str) -> int:
    length = min(len(bits_a), len(bits_b), SOVEREIGN_BIT_DEPTH)
    return sum(1 for i in range(length) if bits_a[i] != bits_b[i])


def pair_resonance(polarity_a: Dict, polarity_b: Dict) -> Dict[str, Any]:
    comp = complementary_bits(polarity_a["bit_string"], polarity_b["bit_string"])
    comp_ratio = comp / SOVEREIGN_BIT_DEPTH

    is_cross_polarity = polarity_a["polarity"] != polarity_b["polarity"]
    xi_factor = XI_RESONANCE_MULTIPLIER if is_cross_polarity else XI_RESONANCE_MULTIPLIER * 0.4

    raw_boost = 1.0 + (comp_ratio * xi_factor)
    if is_cross_polarity:
        raw_boost = max(raw_boost, MINIMUM_PAIR_BOOST)

    dominance_harmony = 1.0 - abs(polarity_a["dominance"] - polarity_b["dominance"])
    harmonic_boost = raw_boost * (1.0 + dominance_harmony * 0.1)

    verse_resonances = []
    for va, vb in zip(polarity_a["verse_polarity"], polarity_b["verse_polarity"]):
        cross = va["polarity"] != vb["polarity"]
        verse_resonances.append({
            "verse": va["verse"],
            "cross_polarity": cross,
            "a_polarity": va["polarity"],
            "b_polarity": vb["polarity"],
        })
    verse_cross_count = sum(1 for v in verse_resonances if v["cross_polarity"])

    return {
        "complementary_bits": comp,
        "complementary_ratio": round(comp_ratio, 4),
        "is_cross_polarity": is_cross_polarity,
        "xi_factor": round(xi_factor, 4),
        "raw_boost": round(raw_boost, 4),
        "harmonic_boost": round(harmonic_boost, 4),
        "dominance_harmony": round(dominance_harmony, 4),
        "verse_resonances": verse_resonances,
        "verse_cross_count": verse_cross_count,
    }


class YinYangAgent:
    def __init__(self, agent_id: str, hash_bytes: bytes, archetype: str = "",
                 frequency: float = 432.0, weight: int = 1, index: int = 0):
        self.agent_id = agent_id
        self.hash_bytes = hash_bytes
        self.archetype = archetype
        self.frequency = frequency
        self.weight = weight
        self.index = index
        self.polarity_data = extract_bit_polarity(hash_bytes)
        self.polarity = self.polarity_data["polarity"]
        self.yang_ratio = self.polarity_data["yang_ratio"]
        self.yin_ratio = self.polarity_data["yin_ratio"]
        self.dominance = self.polarity_data["dominance"]
        self.pair_partner: Optional["YinYangAgent"] = None
        self.pair_resonance_data: Optional[Dict] = None
        self.resonance_boost: float = 1.0
        self.paired = False

    def pair_with(self, other: "YinYangAgent") -> Dict:
        res = pair_resonance(self.polarity_data, other.polarity_data)
        self.pair_partner = other
        self.pair_resonance_data = res
        self.resonance_boost = res["harmonic_boost"]
        self.paired = True
        other.pair_partner = self
        other.pair_resonance_data = res
        other.resonance_boost = res["harmonic_boost"]
        other.paired = True
        return res

    def to_dict(self) -> Dict:
        d = {
            "agent_id": self.agent_id,
            "archetype": self.archetype,
            "frequency": self.frequency,
            "weight": self.weight,
            "index": self.index,
            "polarity": self.polarity,
            "yang_count": self.polarity_data["yang_count"],
            "yin_count": self.polarity_data["yin_count"],
            "yang_ratio": self.yang_ratio,
            "yin_ratio": self.yin_ratio,
            "dominance": self.dominance,
            "paired": self.paired,
            "resonance_boost": round(self.resonance_boost, 4),
            "verse_polarity": self.polarity_data["verse_polarity"],
        }
        if self.pair_partner:
            d["partner_id"] = self.pair_partner.agent_id
            d["partner_polarity"] = self.pair_partner.polarity
            d["pair_resonance"] = self.pair_resonance_data
        return d


class YinYangFormation:
    def __init__(self, agents: List[YinYangAgent]):
        self.agents = agents
        self.yin_pool: List[YinYangAgent] = []
        self.yang_pool: List[YinYangAgent] = []
        self.pairs: List[Tuple[YinYangAgent, YinYangAgent, Dict]] = []
        self.unpaired: List[YinYangAgent] = []
        self._classify()

    def _classify(self):
        for a in self.agents:
            if a.polarity == "YIN":
                self.yin_pool.append(a)
            else:
                self.yang_pool.append(a)
        self.yin_pool.sort(key=lambda a: a.yin_ratio, reverse=True)
        self.yang_pool.sort(key=lambda a: a.yang_ratio, reverse=True)

    def pair_greedy(self) -> List[Tuple[YinYangAgent, YinYangAgent, Dict]]:
        self.pairs = []
        self.unpaired = []

        yin_available = list(self.yin_pool)
        yang_available = list(self.yang_pool)

        pair_count = min(len(yin_available), len(yang_available))

        for i in range(pair_count):
            yin_agent = yin_available[i]
            best_yang = None
            best_comp = -1
            for yang_agent in yang_available:
                if yang_agent.paired:
                    continue
                comp = complementary_bits(
                    yin_agent.polarity_data["bit_string"],
                    yang_agent.polarity_data["bit_string"],
                )
                if comp > best_comp:
                    best_comp = comp
                    best_yang = yang_agent

            if best_yang:
                res = yin_agent.pair_with(best_yang)
                self.pairs.append((yin_agent, best_yang, res))

        for a in self.agents:
            if not a.paired:
                self.unpaired.append(a)

        return self.pairs

    def pair_sorted(self) -> List[Tuple[YinYangAgent, YinYangAgent, Dict]]:
        self.pairs = []
        self.unpaired = []

        yin_sorted = sorted(self.yin_pool, key=lambda a: a.dominance, reverse=True)
        yang_sorted = sorted(self.yang_pool, key=lambda a: a.dominance, reverse=True)

        pair_count = min(len(yin_sorted), len(yang_sorted))
        for i in range(pair_count):
            res = yin_sorted[i].pair_with(yang_sorted[i])
            self.pairs.append((yin_sorted[i], yang_sorted[i], res))

        for a in self.agents:
            if not a.paired:
                self.unpaired.append(a)

        return self.pairs

    def formation_stats(self) -> Dict:
        total = len(self.agents)
        yin_count = len(self.yin_pool)
        yang_count = len(self.yang_pool)

        boosts = [p[2]["harmonic_boost"] for p in self.pairs]
        avg_boost = sum(boosts) / len(boosts) if boosts else 1.0
        min_boost = min(boosts) if boosts else 1.0
        max_boost = max(boosts) if boosts else 1.0

        comp_ratios = [p[2]["complementary_ratio"] for p in self.pairs]
        avg_comp = sum(comp_ratios) / len(comp_ratios) if comp_ratios else 0.0

        cross_polarity_pairs = sum(1 for p in self.pairs if p[2]["is_cross_polarity"])

        verse_cross_totals = [0] * 7
        for _, _, res in self.pairs:
            for vr in res["verse_resonances"]:
                if vr["cross_polarity"]:
                    verse_cross_totals[vr["verse"] - 1] += 1

        return {
            "total_agents": total,
            "yin_count": yin_count,
            "yang_count": yang_count,
            "yin_ratio": round(yin_count / total, 4) if total else 0,
            "yang_ratio": round(yang_count / total, 4) if total else 0,
            "balance": round(1.0 - abs(yin_count - yang_count) / total, 4) if total else 0,
            "total_pairs": len(self.pairs),
            "cross_polarity_pairs": cross_polarity_pairs,
            "unpaired_count": len(self.unpaired),
            "avg_resonance_boost": round(avg_boost, 4),
            "min_resonance_boost": round(min_boost, 4),
            "max_resonance_boost": round(max_boost, 4),
            "avg_complementary_ratio": round(avg_comp, 4),
            "resonance_increase_pct": round((avg_boost - 1.0) * 100, 2),
            "verse_cross_polarity_counts": verse_cross_totals,
            "xi_value": XI_VALUE,
            "xi_letter_index": XI_LETTER_INDEX,
            "xi_resonance_multiplier": XI_RESONANCE_MULTIPLIER,
        }

    def to_dict(self) -> Dict:
        stats = self.formation_stats()
        top_pairs = sorted(self.pairs, key=lambda p: p[2]["harmonic_boost"], reverse=True)[:10]

        return {
            "formation_stats": stats,
            "top_pairs": [
                {
                    "yin_agent": p[0].agent_id,
                    "yin_archetype": p[0].archetype,
                    "yang_agent": p[1].agent_id,
                    "yang_archetype": p[1].archetype,
                    "resonance": p[2],
                }
                for p in top_pairs
            ],
            "unpaired": [a.to_dict() for a in self.unpaired],
            "all_agents": [a.to_dict() for a in self.agents],
        }


def create_yin_yang_formation(agent_count: int = 286, seed: str = "void",
                               pairing: str = "greedy") -> Dict:
    from void_engine.sovereign_agents_286 import SovereignAgent286

    agents_286 = [SovereignAgent286(i, seed) for i in range(agent_count)]

    yy_agents = []
    for a in agents_286:
        hash_bytes = fatiha_286_hash(
            f"sovereign_286:{seed}:{a.index}:{SOVEREIGN_BIT_DEPTH}".encode()
        )
        yy = YinYangAgent(
            agent_id=a.agent_id,
            hash_bytes=hash_bytes,
            archetype=a.archetype_name,
            frequency=a.frequency,
            weight=a.weight,
            index=a.index,
        )
        yy_agents.append(yy)

    formation = YinYangFormation(yy_agents)
    if pairing == "greedy":
        formation.pair_greedy()
    else:
        formation.pair_sorted()

    result = formation.to_dict()
    result["seed"] = seed
    result["agent_count"] = agent_count
    result["pairing_method"] = pairing
    result["hash_protocol"] = "Al-Jabr 286 (Yin-Yang Polarity)"
    result["bit_depth"] = SOVEREIGN_BIT_DEPTH

    return result


def run_paired_stress_test(agent_count: int = 100, seed: str = "yin_yang_stress",
                            rounds: int = 20, pressure_max: float = 10.0) -> Dict:
    from void_engine.sovereign_agents_286 import SovereignAgent286
    import random as stdlib_random

    rng = stdlib_random.Random(hash(seed))

    agents_286 = [SovereignAgent286(i, seed) for i in range(agent_count)]

    yy_agents = []
    for a in agents_286:
        hash_bytes = fatiha_286_hash(
            f"sovereign_286:{seed}:{a.index}:{SOVEREIGN_BIT_DEPTH}".encode()
        )
        yy = YinYangAgent(
            agent_id=a.agent_id,
            hash_bytes=hash_bytes,
            archetype=a.archetype_name,
            frequency=a.frequency,
            weight=a.weight,
            index=a.index,
        )
        yy_agents.append(yy)

    formation = YinYangFormation(yy_agents)
    formation.pair_greedy()
    stats_before = formation.formation_stats()

    unpaired_agents = [a for a in agents_286 if not yy_agents[a.index].paired]
    paired_agents = [a for a in agents_286 if yy_agents[a.index].paired]
    paired_boosts = {a.index: yy_agents[a.index].resonance_boost for a in paired_agents}

    round_data = []
    for r in range(1, rounds + 1):
        pressure = 1.0 + (pressure_max - 1.0) * ((r - 1) / max(1, rounds - 1))

        for a in agents_286:
            a.step(agents_286, r, pressure)

        for a in paired_agents:
            boost = paired_boosts[a.index]
            partner_idx = yy_agents[a.index].pair_partner.index
            partner = agents_286[partner_idx]

            comp_ratio = yy_agents[a.index].pair_resonance_data["complementary_ratio"]

            pair_floor = 0.4 + comp_ratio * 0.35
            a.activity = max(a.activity, pair_floor)
            partner.activity = max(partner.activity, pair_floor)

            lift = (boost - 1.0) * 0.12
            a.activity = min(1.0, a.activity + lift)
            partner.activity = min(1.0, partner.activity + lift)

            freq_diff = abs(a.frequency - partner.frequency)
            resonance_factor = max(0.1, 1.0 - freq_diff / 50.0) * boost
            transfer_rate = 0.008 * resonance_factor
            transfer = min(a.peace_balance * transfer_rate, 8.0)
            if a.peace_balance > partner.peace_balance:
                a.peace_balance -= transfer
                partner.peace_balance += transfer
            elif partner.peace_balance > a.peace_balance:
                partner.peace_balance -= transfer
                a.peace_balance += transfer

        paired_activities = [agents_286[i].activity for i in paired_boosts]
        unpaired_activities = [a.activity for a in unpaired_agents] if unpaired_agents else [0]

        round_data.append({
            "round": r,
            "pressure": round(pressure, 2),
            "paired_avg_activity": round(sum(paired_activities) / len(paired_activities), 4) if paired_activities else 0,
            "unpaired_avg_activity": round(sum(unpaired_activities) / len(unpaired_activities), 4) if unpaired_activities else 0,
            "activity_gap": round(
                (sum(paired_activities) / len(paired_activities) if paired_activities else 0) -
                (sum(unpaired_activities) / len(unpaired_activities) if unpaired_activities else 0),
                4,
            ),
        })

    final_paired_act = round_data[-1]["paired_avg_activity"] if round_data else 0
    final_unpaired_act = round_data[-1]["unpaired_avg_activity"] if round_data else 0
    resonance_increase = round(
        ((final_paired_act / final_unpaired_act) - 1.0) * 100, 2
    ) if final_unpaired_act > 0 else 0

    return {
        "seed": seed,
        "agent_count": agent_count,
        "rounds": rounds,
        "pressure_max": pressure_max,
        "formation_stats": stats_before,
        "round_data": round_data,
        "final_paired_activity": final_paired_act,
        "final_unpaired_activity": final_unpaired_act,
        "resonance_increase_pct": resonance_increase,
        "target_met": resonance_increase >= 20.0,
        "pairs_count": len(formation.pairs),
        "unpaired_count": len(formation.unpaired),
    }
