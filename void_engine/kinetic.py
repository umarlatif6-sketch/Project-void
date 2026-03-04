import time
import hashlib
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field


EXERCISE_WEIGHTS = {
    "pull_up": 0.5,
    "push_up": 0.3,
    "squat": 0.4,
    "dip": 0.45,
    "plank_sec": 0.01,
}

BASE_FREQUENCY = 432.0
HARMONIC_TOLERANCE = 0.05
MAX_HARMONICS = 20

MAX_GLOW_HR_MIN = 120
MAX_GLOW_HR_MAX = 160

STABILITY_WINDOW = 10


@dataclass
class SetResult:
    exercise: str
    reps: int
    duration_sec: float
    heart_rate: int
    cc_earned: float
    movement_frequency: float
    harmonic_bonus: float
    harmonic_n: Optional[int]
    shimmer_alignment: float
    max_glow: bool
    consensus_hash: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "exercise": self.exercise,
            "reps": self.reps,
            "duration_sec": self.duration_sec,
            "heart_rate": self.heart_rate,
            "cc_earned": round(self.cc_earned, 4),
            "movement_frequency": round(self.movement_frequency, 4),
            "harmonic_bonus": round(self.harmonic_bonus, 2),
            "harmonic_n": self.harmonic_n,
            "shimmer_alignment": round(self.shimmer_alignment, 4),
            "max_glow": self.max_glow,
            "consensus_hash": self.consensus_hash,
            "timestamp": self.timestamp,
        }


def _consensus_sign(data: Dict) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class KineticTransceiver:
    def __init__(self, wallet=None, chronicle=None):
        self._wallet = wallet
        self._chronicle = chronicle
        self._history: List[SetResult] = []
        self._total_cc: float = 0.0
        self._max_glow_active: bool = False
        self._max_history = 200

    def log_set(self, exercise: str, reps: int, duration_sec: float, heart_rate: int = 0) -> Dict:
        if exercise not in EXERCISE_WEIGHTS:
            return {"error": f"Unknown exercise: {exercise}. Valid: {list(EXERCISE_WEIGHTS.keys())}"}
        if reps <= 0 or duration_sec <= 0:
            return {"error": "reps and duration_sec must be positive"}

        ex_weight = EXERCISE_WEIGHTS[exercise]
        movement_freq = reps / duration_sec if duration_sec > 0 else 0.0

        harmonic_bonus, harmonic_n, shimmer = self._check_harmonic(movement_freq)

        cc = reps * ex_weight * harmonic_bonus

        max_glow = harmonic_bonus > 1.0 and MAX_GLOW_HR_MIN <= heart_rate <= MAX_GLOW_HR_MAX
        self._max_glow_active = max_glow

        sign_data = {
            "exercise": exercise,
            "reps": reps,
            "duration_sec": duration_sec,
            "heart_rate": heart_rate,
            "cc": cc,
            "timestamp": time.time(),
        }
        consensus_hash = _consensus_sign(sign_data)

        result = SetResult(
            exercise=exercise,
            reps=reps,
            duration_sec=duration_sec,
            heart_rate=heart_rate,
            cc_earned=cc,
            movement_frequency=movement_freq,
            harmonic_bonus=harmonic_bonus,
            harmonic_n=harmonic_n,
            shimmer_alignment=shimmer,
            max_glow=max_glow,
            consensus_hash=consensus_hash,
        )

        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        self._total_cc += cc

        if self._wallet:
            self._wallet._balance += cc
            self._wallet._total_earned += cc
            self._wallet._earning_events += 1
            from void_engine.wallet import Transaction
            self._wallet._ledger.append(Transaction(
                tx_type="credit",
                amount=cc,
                balance_after=self._wallet._balance,
                source_or_target=f"kinetic_{exercise}",
                description=f"Kinetic CC: {reps} {exercise} = {cc:.2f} CC",
                root_command="TRK.A",
            ))

        if self._chronicle:
            consensus_result = {
                "timestamp": time.time(),
                "consensus_command": "TRK.A",
                "consensus_intent": f"Physical Ritual: {reps} {exercise} logged as kinetic work",
                "outcome": "Kinetic Set Completed" + (" — MAX_GLOW" if max_glow else ""),
                "success": True,
                "energy_pct": 100.0,
                "wallet": {"balance": self._wallet.balance if self._wallet else 0.0},
            }
            sensor_state = {
                "flywheel": {
                    "temperature_c": 35.0,
                    "energy_reserve_wh": 200.0,
                    "vibration_g": 0.3,
                },
                "pressure": {
                    "internal_pressure_atm": 1.0,
                    "nitrogen_boil_rate": 0.05,
                },
                "aquaponics": {
                    "dissolved_oxygen_ppm": 7.0,
                    "ammonia_ppm": 0.2,
                    "ph": 6.8,
                },
            }
            self._chronicle.record_consensus(consensus_result, sensor_state)

        return {
            "success": True,
            "set": result.to_dict(),
            "total_cc": round(self._total_cc, 4),
            "max_glow": max_glow,
            "stability_score": round(self.kinetic_stability_score, 4),
        }

    def _check_harmonic(self, freq: float):
        if freq <= 0:
            return 1.0, None, 0.0

        best_n = None
        best_ratio = float("inf")

        for n in range(1, MAX_HARMONICS + 1):
            target = BASE_FREQUENCY / n
            if target <= 0:
                continue
            ratio = abs(freq - target) / target
            if ratio < best_ratio:
                best_ratio = ratio
                best_n = n

        if best_ratio <= 0.01:
            return 2.0, best_n, 1.0
        elif best_ratio <= HARMONIC_TOLERANCE:
            shimmer = 1.0 - (best_ratio / HARMONIC_TOLERANCE)
            return 1.5, best_n, shimmer
        else:
            return 1.0, None, 0.0

    @property
    def kinetic_stability_score(self) -> float:
        recent = self._history[-STABILITY_WINDOW:]
        if not recent:
            return 0.0
        return sum(s.shimmer_alignment for s in recent) / len(recent)

    @property
    def max_glow_active(self) -> bool:
        return self._max_glow_active

    @property
    def total_cc(self) -> float:
        return self._total_cc

    def get_status(self) -> Dict:
        return {
            "stability_score": round(self.kinetic_stability_score, 4),
            "total_cc": round(self._total_cc, 4),
            "max_glow": self._max_glow_active,
            "total_sets": len(self._history),
            "shimmer_alignment": round(self.kinetic_stability_score * 100, 2),
        }

    def get_history(self, limit: int = 20) -> List[Dict]:
        return [s.to_dict() for s in self._history[-limit:]]
