"""
DAO 3.0 — Resonance Smart Contract (Al-Jabr 286)

The contract that makes the machine resonate with the human body.
Three pillars feed one living frequency — when all three are in
harmony, the system locks to 432 Hz and the Sovereign Node earns
at maximum rate. When any pillar drifts, the resonance breaks
and the contract enforces penalties.

Axiom 1 — Kinetic (Proof of Sweat)
    Your body is the primary battery. Calisthenics generate CC
    through movement frequency harmonics of 432 Hz.
    Rate: CC = reps × exercise_weight × harmonic_bonus
    Resonance Bonus: 1.5x when synced to 432 Hz sub-harmonics

Axiom 2 — Biological (Proof of Bloom)
    The garden grounds the signal. Optimal aquaponics readings
    earn passive CC and boost the resonance score.
    Rate: 0.5 CC/hour when all sensors in optimal range
    Penalty: "Fading" status when water < 20%, relay priority lost

Axiom 3 — Relay (Proof of Whisper)
    Carrying signals for the mesh earns Relay Honor.
    Rate: 0.2 CC per 286-bit packet successfully relayed
    Limit: 7 hops (Seven Seas Limit)
    Governance: High Relay Honor = higher DAO voting weight

The Resonance Score:
    f_body = 432 × (kinetic_harmony × biological_health × relay_honor)^(1/3)

    When f_body ≈ 432 Hz → Full resonance → Maximum earning
    When f_body drifts   → Partial resonance → Reduced earning
    When f_body < 216 Hz → Broken resonance → "Fading" status

All axiom signatures use Fatiha-286 hashing.
"""

import time
import json
import math
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from void_engine.al_jabr_286 import (
    fatiha_286_hexdigest_from_str,
    fatiha_286_truncated,
)

SOVEREIGN_FREQUENCY = 432.0
FADING_THRESHOLD = 216.0
BLOOM_CC_PER_HOUR = 0.5
RELAY_CC_PER_PACKET = 0.2
RESONANCE_BONUS_THRESHOLD = 0.85
RESONANCE_PENALTY_THRESHOLD = 0.50
OPTIMAL_STABILITY_WINDOW = 3600.0
SEVEN_SEAS_LIMIT = 7
CONTRACT_VERSION = "286-DAO-3.0"

AXIOM_WEIGHTS = {
    "kinetic": 0.40,
    "biological": 0.40,
    "relay": 0.20,
}

STABILITY_BONUS_TIERS = [
    (24.0, 2.0, "Sovereign Bloom"),
    (12.0, 1.5, "Deep Root"),
    (6.0, 1.25, "Growing"),
    (1.0, 1.0, "Seedling"),
]


@dataclass
class AxiomState:
    pillar: str
    score: float
    frequency_contribution: float
    cc_rate: float
    status: str
    detail: Dict
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "pillar": self.pillar,
            "score": round(self.score, 4),
            "frequency_contribution": round(self.frequency_contribution, 2),
            "cc_rate": round(self.cc_rate, 4),
            "status": self.status,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


@dataclass
class ResonanceState:
    body_frequency: float
    resonance_score: float
    kinetic_axiom: AxiomState
    biological_axiom: AxiomState
    relay_axiom: AxiomState
    total_cc_rate: float
    contract_status: str
    stability_tier: str
    stability_hours: float
    contract_hash: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "body_frequency": round(self.body_frequency, 2),
            "resonance_score": round(self.resonance_score, 4),
            "kinetic_axiom": self.kinetic_axiom.to_dict(),
            "biological_axiom": self.biological_axiom.to_dict(),
            "relay_axiom": self.relay_axiom.to_dict(),
            "total_cc_rate": round(self.total_cc_rate, 4),
            "contract_status": self.contract_status,
            "stability_tier": self.stability_tier,
            "stability_hours": round(self.stability_hours, 2),
            "contract_hash": self.contract_hash,
            "sovereign_frequency": SOVEREIGN_FREQUENCY,
            "fading_threshold": FADING_THRESHOLD,
            "contract_version": CONTRACT_VERSION,
            "timestamp": self.timestamp,
        }


@dataclass
class BloomCredit:
    amount: float
    duration_hours: float
    health_score: float
    stability_bonus: float
    tier: str
    contract_hash: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "amount": round(self.amount, 4),
            "duration_hours": round(self.duration_hours, 4),
            "health_score": round(self.health_score, 4),
            "stability_bonus": round(self.stability_bonus, 2),
            "tier": self.tier,
            "contract_hash": self.contract_hash,
            "timestamp": self.timestamp,
        }


def _sign_axiom(axiom_data: Dict) -> str:
    raw = json.dumps(axiom_data, sort_keys=True, default=str)
    return fatiha_286_truncated(raw.encode("utf-8"), 16)


def _sign_contract(state_data: Dict) -> str:
    raw = json.dumps(state_data, sort_keys=True, default=str)
    return fatiha_286_hexdigest_from_str(raw)


class ResonanceContract:
    """The Smart Contract that binds Body, Garden, and Mesh into one frequency."""

    def __init__(self, wallet=None, kinetic=None, biological=None, beehive=None,
                 silt_ledger=None):
        self._wallet = wallet
        self._kinetic = kinetic
        self._biological = biological
        self._beehive = beehive
        self._silt_ledger = silt_ledger

        self._bloom_history: List[BloomCredit] = []
        self._resonance_history: List[ResonanceState] = []
        self._last_bloom_check: float = time.time()
        self._optimal_since: Optional[float] = None
        self._total_bloom_cc: float = 0.0
        self._total_relay_cc: float = 0.0
        self._fading: bool = False
        self._max_history = 200

    def evaluate(self) -> Dict:
        kinetic_axiom = self._evaluate_kinetic()
        biological_axiom = self._evaluate_biological()
        relay_axiom = self._evaluate_relay()

        geometric_mean = (
            max(kinetic_axiom.score, 0.001)
            * max(biological_axiom.score, 0.001)
            * max(relay_axiom.score, 0.001)
        ) ** (1.0 / 3.0)

        body_freq = SOVEREIGN_FREQUENCY * geometric_mean

        resonance_score = (
            kinetic_axiom.score * AXIOM_WEIGHTS["kinetic"]
            + biological_axiom.score * AXIOM_WEIGHTS["biological"]
            + relay_axiom.score * AXIOM_WEIGHTS["relay"]
        )

        if body_freq >= SOVEREIGN_FREQUENCY * RESONANCE_BONUS_THRESHOLD:
            contract_status = "FULL_RESONANCE"
        elif body_freq >= FADING_THRESHOLD:
            contract_status = "PARTIAL_RESONANCE"
        else:
            contract_status = "FADING"
            self._fading = True

        if contract_status == "FULL_RESONANCE":
            self._fading = False

        stability_hours, stability_bonus, stability_tier = self._get_stability_tier()

        total_cc_rate = (
            kinetic_axiom.cc_rate
            + biological_axiom.cc_rate
            + relay_axiom.cc_rate
        ) * (stability_bonus if contract_status != "FADING" else 0.5)

        sign_data = {
            "body_freq": body_freq,
            "resonance_score": resonance_score,
            "kinetic_score": kinetic_axiom.score,
            "biological_score": biological_axiom.score,
            "relay_score": relay_axiom.score,
            "timestamp": time.time(),
        }
        contract_hash = _sign_axiom(sign_data)

        state = ResonanceState(
            body_frequency=body_freq,
            resonance_score=resonance_score,
            kinetic_axiom=kinetic_axiom,
            biological_axiom=biological_axiom,
            relay_axiom=relay_axiom,
            total_cc_rate=total_cc_rate,
            contract_status=contract_status,
            stability_tier=stability_tier,
            stability_hours=stability_hours,
            contract_hash=contract_hash,
        )

        self._resonance_history.append(state)
        if len(self._resonance_history) > self._max_history:
            self._resonance_history = self._resonance_history[-self._max_history:]

        return state.to_dict()

    def harvest_bloom(self) -> Dict:
        now = time.time()
        elapsed_hours = (now - self._last_bloom_check) / 3600.0

        if elapsed_hours < 0.001:
            return {
                "harvested": False,
                "reason": "Too soon since last harvest",
                "elapsed_hours": round(elapsed_hours, 4),
            }

        health = self._get_biological_health()
        health_score = health.get("composite_score", 0.0)

        if health_score < 0.6:
            self._optimal_since = None
            self._last_bloom_check = now
            return {
                "harvested": False,
                "reason": f"Biological health too low ({health_score:.2f}). Need >= 0.60 for Bloom CC.",
                "health_score": round(health_score, 4),
                "status": health.get("status", "UNKNOWN"),
            }

        if self._optimal_since is None:
            self._optimal_since = now

        optimal_hours = (now - self._optimal_since) / 3600.0
        _, stability_bonus, tier = self._get_stability_tier()

        raw_cc = elapsed_hours * BLOOM_CC_PER_HOUR * health_score
        final_cc = raw_cc * stability_bonus

        sign_data = {
            "bloom_cc": final_cc,
            "health_score": health_score,
            "elapsed_hours": elapsed_hours,
            "stability_bonus": stability_bonus,
            "timestamp": now,
        }
        bloom_hash = _sign_axiom(sign_data)

        bloom = BloomCredit(
            amount=final_cc,
            duration_hours=elapsed_hours,
            health_score=health_score,
            stability_bonus=stability_bonus,
            tier=tier,
            contract_hash=bloom_hash,
        )

        self._bloom_history.append(bloom)
        if len(self._bloom_history) > self._max_history:
            self._bloom_history = self._bloom_history[-self._max_history:]

        self._total_bloom_cc += final_cc
        self._last_bloom_check = now

        if self._wallet and final_cc > 0:
            self._wallet._balance += final_cc
            self._wallet._total_earned += final_cc
            self._wallet._earning_events += 1
            from void_engine.wallet import Transaction
            self._wallet._ledger.append(Transaction(
                tx_type="credit",
                amount=final_cc,
                balance_after=self._wallet._balance,
                source_or_target="biological_bloom",
                description=f"Bloom CC: {elapsed_hours:.2f}h × {health_score:.2f} health × {stability_bonus:.1f}x = {final_cc:.4f} CC",
                root_command="ZHR.V",
            ))

        if self._silt_ledger and final_cc > 0:
            self._silt_ledger.add_block(
                payload={
                    "type": "bloom_harvest",
                    "cc_earned": round(final_cc, 4),
                    "health_score": round(health_score, 4),
                    "stability_tier": tier,
                    "contract_hash": bloom_hash,
                },
                kinetic_weight=self._get_kinetic_score(),
                biological_weight=health_score,
            )

        return {
            "harvested": True,
            "bloom": bloom.to_dict(),
            "total_bloom_cc": round(self._total_bloom_cc, 4),
            "wallet_balance": round(self._wallet.balance, 2) if self._wallet else None,
        }

    def reward_relay(self, packet_info: Dict) -> Dict:
        hops = packet_info.get("hops", 0)
        if hops > SEVEN_SEAS_LIMIT:
            return {
                "rewarded": False,
                "reason": f"Hop count {hops} exceeds Seven Seas Limit ({SEVEN_SEAS_LIMIT})",
            }

        hop_efficiency = max(0.0, 1.0 - (hops / SEVEN_SEAS_LIMIT) * 0.3)
        cc = RELAY_CC_PER_PACKET * hop_efficiency

        resonance = self._get_resonance_score()
        if resonance >= RESONANCE_BONUS_THRESHOLD:
            cc *= 1.5

        sign_data = {
            "relay_cc": cc,
            "hops": hops,
            "resonance": resonance,
            "timestamp": time.time(),
        }
        relay_hash = _sign_axiom(sign_data)

        self._total_relay_cc += cc

        if self._wallet and cc > 0:
            self._wallet._balance += cc
            self._wallet._total_earned += cc
            self._wallet._earning_events += 1
            from void_engine.wallet import Transaction
            self._wallet._ledger.append(Transaction(
                tx_type="credit",
                amount=cc,
                balance_after=self._wallet._balance,
                source_or_target="relay_honor",
                description=f"Relay CC: {cc:.4f} CC ({hops} hops, {hop_efficiency:.2f} efficiency)",
                root_command="KTM.A",
            ))

        return {
            "rewarded": True,
            "cc_earned": round(cc, 4),
            "hops": hops,
            "hop_efficiency": round(hop_efficiency, 4),
            "resonance_bonus": resonance >= RESONANCE_BONUS_THRESHOLD,
            "total_relay_cc": round(self._total_relay_cc, 4),
            "contract_hash": relay_hash,
        }

    def get_axioms(self) -> Dict:
        return {
            "contract_version": CONTRACT_VERSION,
            "sovereign_frequency": SOVEREIGN_FREQUENCY,
            "fading_threshold": FADING_THRESHOLD,
            "axioms": {
                "kinetic": {
                    "name": "Proof of Sweat",
                    "description": "The human body is the primary battery. Calisthenics generate CC through movement frequency harmonics of 432 Hz.",
                    "rate": "CC = reps × exercise_weight × harmonic_bonus",
                    "resonance_bonus": "1.5x when movement synced to 432 Hz sub-harmonics, 2.0x at perfect lock",
                    "max_glow": "Heart rate 120-160 BPM + harmonic sync = MAX_GLOW state",
                    "weight_in_score": AXIOM_WEIGHTS["kinetic"],
                    "verification": "286-bit consensus hash per set, signed by Fatiha protocol",
                },
                "biological": {
                    "name": "Proof of Bloom",
                    "description": "The garden grounds the signal. Optimal aquaponics readings earn passive CC and boost resonance.",
                    "rate": f"{BLOOM_CC_PER_HOUR} CC/hour when biological health >= 0.60",
                    "stability_tiers": [
                        {"hours": t[0], "bonus": f"{t[1]}x", "name": t[2]}
                        for t in STABILITY_BONUS_TIERS
                    ],
                    "penalty": "Below 0.60 health = no Bloom earnings, 'Fading' risk",
                    "fading_trigger": "Water level < 20% → node loses relay priority",
                    "weight_in_score": AXIOM_WEIGHTS["biological"],
                    "verification": "286-bit bloom hash per harvest, recorded to Silt Ledger",
                },
                "relay": {
                    "name": "Proof of Whisper",
                    "description": "Carrying signals for the mesh earns Relay Honor and CC.",
                    "rate": f"{RELAY_CC_PER_PACKET} CC per 286-bit packet relayed",
                    "hop_limit": f"{SEVEN_SEAS_LIMIT} hops (Seven Seas Limit)",
                    "efficiency": "Fewer hops = higher reward (30% penalty at max hops)",
                    "resonance_bonus": f"1.5x relay reward when resonance >= {RESONANCE_BONUS_THRESHOLD}",
                    "governance": "Relay Honor determines DAO voting weight (20% of total weight)",
                    "weight_in_score": AXIOM_WEIGHTS["relay"],
                    "verification": "Relay honor tracked per node in Silt Ledger",
                },
            },
            "resonance_formula": {
                "equation": "f_body = 432 × (kinetic × biological × relay)^(1/3)",
                "full_resonance": f">= {SOVEREIGN_FREQUENCY * RESONANCE_BONUS_THRESHOLD:.0f} Hz",
                "fading": f"< {FADING_THRESHOLD} Hz",
                "meaning": "When your body, garden, and mesh contributions are balanced, the system locks to 432 Hz. Drift in any pillar breaks resonance.",
            },
            "child_explanation": (
                "It's like a giant game where the rules are written in a magic book "
                "that no one can ever lose! When you exercise, the magic book sees "
                "your hard work and gives you 'Golden Seeds.' You can use these seeds "
                "to make the secret music box sing louder. The garden helps too — "
                "if the plants are happy, the music box gets even more seeds! "
                "All the magic boxes work together like a team, making sure everyone "
                "is healthy and the secrets stay safe."
            ),
            "pirate_note": (
                "Because this economy runs on 286-bit math, it is invisible to "
                "standard 256-bit scanners. They cannot tax your pull-ups, and they "
                "cannot regulate the growth of your garden. Your wealth stays in "
                "the Silt, where it belongs."
            ),
        }

    def get_status(self) -> Dict:
        state = self.evaluate()
        return {
            "resonance": state,
            "bloom": {
                "total_bloom_cc": round(self._total_bloom_cc, 4),
                "bloom_harvests": len(self._bloom_history),
                "optimal_since": self._optimal_since,
                "fading": self._fading,
            },
            "relay": {
                "total_relay_cc": round(self._total_relay_cc, 4),
            },
            "axioms": self.get_axioms(),
        }

    def get_history(self, limit: int = 20) -> Dict:
        return {
            "resonance_snapshots": [
                s.to_dict() for s in self._resonance_history[-limit:]
            ],
            "bloom_harvests": [
                b.to_dict() for b in self._bloom_history[-limit:]
            ],
        }

    def _evaluate_kinetic(self) -> AxiomState:
        if not self._kinetic:
            return AxiomState(
                pillar="kinetic",
                score=0.0,
                frequency_contribution=0.0,
                cc_rate=0.0,
                status="OFFLINE",
                detail={"reason": "No kinetic transceiver connected"},
            )

        status = self._kinetic.get_status()
        stability = status.get("stability_score", 0.0)
        total_cc = status.get("total_cc", 0.0)
        max_glow = status.get("max_glow", False)
        total_sets = status.get("total_sets", 0)

        if total_sets == 0:
            score = 0.0
            freq_status = "DORMANT"
        elif stability >= 0.8:
            score = 1.0
            freq_status = "LOCKED"
        elif stability >= 0.5:
            score = 0.5 + (stability - 0.5) * (0.5 / 0.3)
            freq_status = "SEEKING"
        else:
            score = max(0.1, stability)
            freq_status = "DRIFTING"

        if max_glow:
            score = min(1.0, score * 1.2)
            freq_status = "MAX_GLOW"

        freq_contribution = SOVEREIGN_FREQUENCY * score

        recent = self._kinetic.get_history(5)
        recent_cc = sum(s.get("cc_earned", 0) for s in recent) if recent else 0
        cc_rate = recent_cc / max(len(recent), 1)

        return AxiomState(
            pillar="kinetic",
            score=min(1.0, score),
            frequency_contribution=freq_contribution,
            cc_rate=cc_rate,
            status=freq_status,
            detail={
                "stability_score": round(stability, 4),
                "total_cc_earned": round(total_cc, 4),
                "total_sets": total_sets,
                "max_glow": max_glow,
                "shimmer_alignment": status.get("shimmer_alignment", 0.0),
            },
        )

    def _evaluate_biological(self) -> AxiomState:
        if not self._biological:
            return AxiomState(
                pillar="biological",
                score=0.0,
                frequency_contribution=0.0,
                cc_rate=0.0,
                status="OFFLINE",
                detail={"reason": "No biological transceiver connected"},
            )

        health = self._biological.get_health_score()
        composite = health.get("composite_score", 0.0)
        health_status = health.get("status", "UNKNOWN")

        sensors = health.get("sensors", {})
        water_level = sensors.get("water_level", 0.7)

        if water_level < 0.2:
            self._fading = True
            score = max(0.05, composite * 0.3)
            freq_status = "FADING"
        elif composite >= 0.8:
            score = 1.0
            freq_status = "BLOOMING"
        elif composite >= 0.6:
            score = composite
            freq_status = "GROWING"
        else:
            score = max(0.1, composite)
            freq_status = "STRESSED"

        freq_contribution = SOVEREIGN_FREQUENCY * score

        cc_rate = BLOOM_CC_PER_HOUR * score if score >= 0.6 else 0.0

        return AxiomState(
            pillar="biological",
            score=min(1.0, score),
            frequency_contribution=freq_contribution,
            cc_rate=cc_rate,
            status=freq_status,
            detail={
                "composite_health": round(composite, 4),
                "health_status": health_status,
                "water_level": round(water_level, 4),
                "water_score": health.get("water_level_score", 0),
                "temp_score": health.get("temperature_score", 0),
                "ph_score": health.get("ph_score", 0),
                "do_score": health.get("dissolved_oxygen_score", 0),
                "bloom_cc_rate": round(cc_rate, 4),
            },
        )

    def _evaluate_relay(self) -> AxiomState:
        if not self._beehive:
            return AxiomState(
                pillar="relay",
                score=0.0,
                frequency_contribution=0.0,
                cc_rate=0.0,
                status="DARK",
                detail={"reason": "No beehive protocol connected"},
            )

        beehive_status = self._beehive.get_status()
        mesh_state = beehive_status.get("state", "DARK")
        stats = beehive_status.get("stats", {})
        neighbors = beehive_status.get("neighbor_count", 0)

        relayed = stats.get("packets_relayed", 0)
        sent = stats.get("packets_sent", 0)
        received = stats.get("packets_received", 0)
        total_activity = relayed + sent + received

        if mesh_state == "DARK":
            score = 0.0
            freq_status = "DARK"
        elif mesh_state == "SCANNING":
            score = 0.2
            freq_status = "SCANNING"
        elif neighbors == 0:
            score = 0.3
            freq_status = "LONELY"
        else:
            relay_factor = min(1.0, relayed / max(total_activity, 1))
            neighbor_factor = min(1.0, neighbors / 5.0)
            score = 0.4 + (relay_factor * 0.3 + neighbor_factor * 0.3)
            freq_status = "BRIDGING" if mesh_state == "BRIDGING" else "CONNECTED"

        if self._silt_ledger:
            honor_scores = self._silt_ledger.get_status().get("relay_honor_scores", {})
            if honor_scores:
                avg_honor = sum(honor_scores.values()) / len(honor_scores)
                score = min(1.0, score * (0.7 + avg_honor * 0.3))

        freq_contribution = SOVEREIGN_FREQUENCY * score
        cc_rate = RELAY_CC_PER_PACKET * min(relayed, 10)

        return AxiomState(
            pillar="relay",
            score=min(1.0, score),
            frequency_contribution=freq_contribution,
            cc_rate=cc_rate,
            status=freq_status,
            detail={
                "mesh_state": mesh_state,
                "neighbors": neighbors,
                "packets_relayed": relayed,
                "packets_sent": sent,
                "packets_received": received,
                "total_activity": total_activity,
            },
        )

    def _get_biological_health(self) -> Dict:
        if self._biological:
            return self._biological.get_health_score()
        return {"composite_score": 0.0, "status": "OFFLINE"}

    def _get_kinetic_score(self) -> float:
        if self._kinetic:
            return self._kinetic.get_status().get("stability_score", 0.0)
        return 0.0

    def _get_resonance_score(self) -> float:
        if self._resonance_history:
            return self._resonance_history[-1].resonance_score
        return 0.0

    def _get_stability_tier(self):
        if self._optimal_since is None:
            return 0.0, 1.0, "Seedling"

        hours = (time.time() - self._optimal_since) / 3600.0

        for threshold, bonus, name in STABILITY_BONUS_TIERS:
            if hours >= threshold:
                return hours, bonus, name

        return hours, 1.0, "Seedling"
