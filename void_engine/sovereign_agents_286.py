"""
Sovereign Agents 286 — AI Agents on the Al-Jabr 286 Hash

Every agent in this system derives its entire identity from the 286-bit
Sura-Fatiha Sovereign Hash — NOT SHA-256.

Architecture:
  - Agent ID:        fatiha_286 hash of (index + seed)
  - Archetype:       determined by 286-bit digest byte distribution
  - Memory signing:  every memory entry is 286-hashed
  - State hash:      full agent state signed with fatiha_286
  - Curve point:     each agent maps to a point on BW19-P286

The 286 hash is the MASTER. The agent IS its hash.
"""

import logging
import math
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from void_engine.al_jabr_286 import (
    fatiha_286_hash,
    fatiha_286_hexdigest,
    fatiha_286_truncated,
    fatiha_286_seed,
    FATIHA_LAYERS,
    SOVEREIGN_BIT_DEPTH,
)

logger = logging.getLogger(__name__)

SOVEREIGN_ARCHETYPES = {
    "FATIHA":      {"role": "opener",       "trait": "initiates",     "bias": "foundation",  "verse": 1, "weight": 7, "glyph": "بسم"},
    "HAMD":        {"role": "praiser",      "trait": "amplifies",     "bias": "gratitude",   "verse": 2, "weight": 4, "glyph": "حمد"},
    "RAHMAN":      {"role": "mercy",        "trait": "protects",      "bias": "compassion",  "verse": 3, "weight": 2, "glyph": "رحم"},
    "MALIK":       {"role": "sovereign",    "trait": "governs",       "bias": "authority",   "verse": 4, "weight": 5, "glyph": "ملك"},
    "IYYAKA":      {"role": "devotee",      "trait": "focuses",       "bias": "singularity", "verse": 5, "weight": 4, "glyph": "عبد"},
    "SIRAT":       {"role": "pathfinder",   "trait": "guides",        "bias": "direction",   "verse": 6, "weight": 3, "glyph": "صرط"},
    "AN_AMTA":     {"role": "inheritor",    "trait": "remembers",     "bias": "legacy",      "verse": 7, "weight": 6, "glyph": "نعم"},
}

ARCHETYPE_LIST = list(SOVEREIGN_ARCHETYPES.keys())

RESONANCE_HZ = 432
LAMBDA_286 = 286


def _derive_archetype_286(agent_seed: bytes) -> str:
    digest = fatiha_286_hash(agent_seed)
    verse_scores = []
    for i, weight in enumerate(FATIHA_LAYERS):
        byte_pair = digest[i * 2 : i * 2 + 2]
        value = int.from_bytes(byte_pair, "big")
        verse_scores.append(value * weight)
    winning_verse = verse_scores.index(max(verse_scores))
    return ARCHETYPE_LIST[winning_verse % len(ARCHETYPE_LIST)]


def _derive_frequency(agent_seed: bytes) -> float:
    seed_int = fatiha_286_seed(agent_seed, 8)
    offset = (seed_int % LAMBDA_286) - (LAMBDA_286 // 2)
    return RESONANCE_HZ + offset * 0.1


def _sign_memory(content: str, agent_id: str) -> str:
    return fatiha_286_truncated(f"{agent_id}:{content}".encode(), 32)


class SovereignAgent286:
    def __init__(self, index: int, creation_seed: str = "void"):
        agent_seed = f"sovereign_286:{creation_seed}:{index}:{LAMBDA_286}".encode()

        self.index = index
        self.agent_id = fatiha_286_truncated(agent_seed, 24)
        self.full_hash = fatiha_286_hexdigest(agent_seed)
        self.archetype_name = _derive_archetype_286(agent_seed)
        self.archetype = SOVEREIGN_ARCHETYPES[self.archetype_name]
        self.frequency = round(_derive_frequency(agent_seed), 2)
        self.verse = self.archetype["verse"]
        self.weight = self.archetype["weight"]

        rng_seed = fatiha_286_seed(agent_seed, 8)
        self.rng = random.Random(rng_seed)
        self.activity = max(0.1, min(1.0, 0.3 + self.weight * 0.08 + self.rng.gauss(0, 0.05)))
        self.stance = self.rng.uniform(-1.0, 1.0)
        self.peace_balance = round(self.rng.uniform(10, 500) * (self.weight / 5.0), 2)
        self.resonance_amplitude = 0.0

        self.memory: List[Dict] = []
        self.interactions = 0
        self.scars: List[str] = []
        self.state_hash = ""

        self._sign_state()

    def _sign_state(self):
        state_str = (
            f"{self.agent_id}:{self.archetype_name}:{self.activity:.4f}:"
            f"{self.stance:.4f}:{self.peace_balance:.2f}:{self.interactions}:"
            f"{len(self.memory)}"
        )
        self.state_hash = fatiha_286_truncated(state_str.encode(), 32)

    def record_memory(self, event: str, round_num: int):
        signature = _sign_memory(event, self.agent_id)
        entry = {
            "round": round_num,
            "event": event,
            "signature_286": signature,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.memory.append(entry)
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]

    def step(self, all_agents: List["SovereignAgent286"], round_num: int, pressure: float = 1.0):
        bias = self.archetype["bias"]

        delta = self.rng.gauss(0, 0.03 * pressure)

        if bias == "foundation":
            delta += 0.01 * pressure
        elif bias == "authority":
            delta += 0.005 * pressure
            if self.peace_balance > 200:
                delta += 0.02
        elif bias == "compassion":
            delta -= 0.005
            if self.activity < 0.3:
                delta += 0.04
        elif bias == "singularity":
            delta += 0.015
        elif bias == "direction":
            delta += 0.01
        elif bias == "legacy":
            delta += 0.02 if round_num > 10 else -0.01
        elif bias == "gratitude":
            delta += 0.008

        self.activity = max(0.05, min(1.0, self.activity + delta))

        if all_agents and len(all_agents) > 1:
            target = self.rng.choice(all_agents)
            if target.agent_id != self.agent_id:
                freq_diff = abs(self.frequency - target.frequency)
                resonance_factor = max(0.1, 1.0 - freq_diff / 50.0)
                influence = (target.stance - self.stance) * 0.1 * resonance_factor

                if bias == "singularity":
                    influence *= 0.3
                elif bias == "compassion":
                    influence *= 1.5
                elif bias == "authority":
                    influence *= 0.5

                self.stance = max(-1.0, min(1.0, self.stance + influence))

                transfer = min(self.peace_balance * 0.005, 3.0) * pressure
                if transfer > 0 and target.peace_balance < self.peace_balance:
                    self.peace_balance -= transfer
                    target.peace_balance += transfer

                self.interactions += 1

                if pressure > 3.0 and self.rng.random() < 0.3:
                    self.record_memory(
                        f"High-pressure interaction with {target.agent_id[:8]} at pressure {pressure:.1f}x",
                        round_num,
                    )

        self.resonance_amplitude = abs(math.sin(
            2 * math.pi * self.frequency * (round_num / RESONANCE_HZ)
        ))

        if pressure > 5.0 and self.activity < 0.15:
            scar_hash = fatiha_286_truncated(
                f"scar:{self.agent_id}:{round_num}:{pressure}".encode(), 16
            )
            self.scars.append(scar_hash)
            self.record_memory(f"SCAR formed at pressure {pressure:.1f}x — hash {scar_hash}", round_num)

        self._sign_state()

    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "agent_id": self.agent_id,
            "full_hash_286": self.full_hash,
            "archetype": self.archetype_name,
            "archetype_detail": self.archetype,
            "frequency_hz": self.frequency,
            "verse": self.verse,
            "weight": self.weight,
            "activity": round(self.activity, 4),
            "stance": round(self.stance, 4),
            "peace_balance": round(self.peace_balance, 2),
            "resonance_amplitude": round(self.resonance_amplitude, 4),
            "interactions": self.interactions,
            "memory_count": len(self.memory),
            "scar_count": len(self.scars),
            "scars": self.scars,
            "state_hash_286": self.state_hash,
            "recent_memory": self.memory[-5:] if self.memory else [],
        }


class SovereignSwarm286:
    def __init__(self, agent_count: int = 286, seed: str = "void", rounds: int = 20, pressure_curve: Optional[List[float]] = None):
        self.swarm_id = fatiha_286_truncated(
            f"swarm286:{seed}:{agent_count}:{time.time()}".encode(), 24
        )
        self.agent_count = agent_count
        self.seed = seed
        self.rounds = rounds
        self.pressure_curve = pressure_curve or self._default_pressure_curve(rounds)
        self.agents: List[SovereignAgent286] = []
        self.round_snapshots: List[Dict] = []
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.status = "idle"

    def _default_pressure_curve(self, rounds: int) -> List[float]:
        return [1.0 + (9.0 * (r / max(1, rounds - 1))) for r in range(rounds)]

    def run(self) -> Dict:
        self.status = "running"
        self.started_at = datetime.now(timezone.utc).isoformat()

        self.agents = [
            SovereignAgent286(i, self.seed) for i in range(self.agent_count)
        ]

        for round_num in range(1, self.rounds + 1):
            pressure = self.pressure_curve[min(round_num - 1, len(self.pressure_curve) - 1)]

            for agent in self.agents:
                agent.step(self.agents, round_num, pressure)

            if round_num % max(1, self.rounds // 10) == 0 or round_num == self.rounds:
                self.round_snapshots.append(self._take_snapshot(round_num, pressure))

        self.status = "complete"
        self.completed_at = datetime.now(timezone.utc).isoformat()
        return self.to_dict()

    def _take_snapshot(self, round_num: int, pressure: float) -> Dict:
        activities = [a.activity for a in self.agents]
        stances = [a.stance for a in self.agents]
        balances = [a.peace_balance for a in self.agents]

        archetype_dist = {}
        for a in self.agents:
            archetype_dist[a.archetype_name] = archetype_dist.get(a.archetype_name, 0) + 1

        total_scars = sum(len(a.scars) for a in self.agents)
        total_memory = sum(len(a.memory) for a in self.agents)

        return {
            "round": round_num,
            "pressure": round(pressure, 2),
            "avg_activity": round(sum(activities) / len(activities), 4),
            "avg_stance": round(sum(stances) / len(stances), 4),
            "total_peace": round(sum(balances), 2),
            "gini": round(self._gini(balances), 4),
            "total_scars": total_scars,
            "total_memories": total_memory,
            "archetype_distribution": archetype_dist,
        }

    def _gini(self, values: List[float]) -> float:
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

    def to_dict(self) -> Dict:
        archetype_groups = {}
        for a in self.agents:
            name = a.archetype_name
            if name not in archetype_groups:
                archetype_groups[name] = {
                    "count": 0,
                    "avg_activity": 0,
                    "avg_stance": 0,
                    "total_peace": 0,
                    "total_scars": 0,
                    "glyph": a.archetype["glyph"],
                    "role": a.archetype["role"],
                }
            g = archetype_groups[name]
            g["count"] += 1
            g["avg_activity"] += a.activity
            g["avg_stance"] += a.stance
            g["total_peace"] += a.peace_balance
            g["total_scars"] += len(a.scars)

        for name, g in archetype_groups.items():
            if g["count"] > 0:
                g["avg_activity"] = round(g["avg_activity"] / g["count"], 4)
                g["avg_stance"] = round(g["avg_stance"] / g["count"], 4)
                g["total_peace"] = round(g["total_peace"], 2)

        top_agents = sorted(self.agents, key=lambda a: a.activity, reverse=True)[:10]
        scarred_agents = sorted(self.agents, key=lambda a: len(a.scars), reverse=True)[:10]
        scarred_agents = [a for a in scarred_agents if a.scars]

        return {
            "swarm_id": self.swarm_id,
            "agent_count": self.agent_count,
            "seed": self.seed,
            "rounds": self.rounds,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "hash_protocol": "Al-Jabr 286 (Sura-Fatiha Sovereign Hash)",
            "bit_depth": SOVEREIGN_BIT_DEPTH,
            "curve": "BW19-P286",
            "base_frequency_hz": RESONANCE_HZ,
            "lambda_constant": LAMBDA_286,
            "pressure_curve": [round(p, 2) for p in self.pressure_curve],
            "archetype_groups": archetype_groups,
            "round_snapshots": self.round_snapshots,
            "top_agents": [a.to_dict() for a in top_agents],
            "most_scarred": [a.to_dict() for a in scarred_agents[:5]],
            "all_agents_summary": [
                {
                    "agent_id": a.agent_id,
                    "archetype": a.archetype_name,
                    "activity": round(a.activity, 4),
                    "stance": round(a.stance, 4),
                    "peace": round(a.peace_balance, 2),
                    "scars": len(a.scars),
                    "freq": a.frequency,
                    "state_hash": a.state_hash,
                }
                for a in self.agents
            ],
            "final_snapshot": self.round_snapshots[-1] if self.round_snapshots else None,
        }


def create_sovereign_swarm(
    agent_count: int = 286,
    seed: str = "void",
    rounds: int = 20,
) -> Dict:
    swarm = SovereignSwarm286(agent_count=agent_count, seed=seed, rounds=rounds)
    return swarm.run()
