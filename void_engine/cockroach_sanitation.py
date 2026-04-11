"""
Cockroach Sanitation Protocol — PROJECT VOID

Bio-inspired sanitation system modeled on real cyborg-insect research:
  - University of Connecticut (2012): wireless neural control of cockroaches
  - Backyard Brains RoboRoach: electrode stimulation on antenna nerves
  - Texas A&M (2015): autonomous navigation via neural implants
  - Singapore NTU (2022): fuel-cell-powered cyborg cockroaches

The protocol:
  1. CONTAINMENT — cockroach agents are deployed into a bounded zone (the "bin")
  2. DARK CYCLE — lights off, cockroaches activate: consume waste, dead tokens,
     inactive resources, orphaned data. They eat everything organic.
  3. LIGHT CYCLE — lights on, cockroaches go dormant, hide back into the walls.
     The zone is clean, empty, spotless.
  4. NEURAL CONTROL — the system (Adriana/MESA) controls activation via the
     dark/light signal. Cockroaches never operate unsupervised.

Applied commercially:
  - Supermarket waste bins, meat processing, food storage
  - Any contained space where organic matter needs complete removal
  - £0 chemical cost, £0 energy cost for the cleaning itself
  - The cockroach IS the cleaning mechanism

In PROJECT VOID's agent systems:
  - "Waste" = dead tokens, inactive agents, orphaned transactions, economic debris
  - "Bin" = any bounded zone (micro-fracture, sandbox session, village zone)
  - "Dark cycle" = cockroach agents activate and consume
  - "Light cycle" = zone is clean, cockroaches dormant, metrics visible
"""

import hashlib
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CYCLE_STATES = ("DARK", "LIGHT")
DEFAULT_COCKROACH_RATIO = 0.10
CONSUMPTION_RATE_PER_COCKROACH = 0.18
SANITATION_THRESHOLD = 0.95
MIN_WASTE_FLOOR = 0.3


class SanitationBin:
    """
    A contained zone where cockroach agents operate.
    Waste enters. Cockroaches consume during dark cycles. Light cycle reveals clean zone.
    """

    def __init__(self, bin_id: str, capacity: float = 100.0,
                 n_cockroaches: int = 5, rng_seed: Optional[int] = None):
        self.bin_id = bin_id
        self.capacity = capacity
        self.n_cockroaches = n_cockroaches
        self.rng = random.Random(rng_seed or abs(hash(bin_id)) % 2**31)

        self.waste_level = 0.0
        self.cycle = "LIGHT"
        self.cycles_completed = 0
        self.total_consumed = 0.0
        self.cockroach_health = [1.0] * n_cockroaches
        self.contamination_level = 0.0

        self.history: List[Dict] = []

    def deposit_waste(self, amount: float, waste_type: str = "organic") -> Dict:
        """Add waste to the bin. Returns deposit confirmation."""
        actual = min(amount, self.capacity - self.waste_level)
        self.waste_level += actual
        self.contamination_level = min(1.0, self.waste_level / max(self.capacity, 1))
        return {
            "deposited": round(actual, 2),
            "rejected": round(amount - actual, 2),
            "waste_level": round(self.waste_level, 2),
            "contamination": round(self.contamination_level, 4),
            "waste_type": waste_type,
        }

    def run_dark_cycle(self, duration_rounds: int = 3) -> Dict:
        """
        Lights off. Cockroaches activate.
        Each cockroach consumes a portion of waste per round.
        They eat everything they can reach.
        """
        self.cycle = "DARK"
        consumed_this_cycle = 0.0
        round_log = []

        for r in range(duration_rounds):
            round_consumed = 0.0
            for i in range(self.n_cockroaches):
                if self.waste_level <= MIN_WASTE_FLOOR:
                    break

                health = self.cockroach_health[i]
                appetite = self.waste_level * CONSUMPTION_RATE_PER_COCKROACH * health
                noise = self.rng.gauss(0, appetite * 0.1) if appetite > 0 else 0
                bite = max(0, min(self.waste_level, appetite + noise))

                self.waste_level -= bite
                round_consumed += bite

                nutrition = bite * 0.05
                self.cockroach_health[i] = min(1.0, health + nutrition)

            consumed_this_cycle += round_consumed
            round_log.append({
                "round": r + 1,
                "consumed": round(round_consumed, 4),
                "waste_remaining": round(self.waste_level, 4),
                "active_cockroaches": sum(1 for h in self.cockroach_health if h > 0.1),
            })

        self.total_consumed += consumed_this_cycle
        self.waste_level = max(0, self.waste_level)
        self.contamination_level = self.waste_level / max(self.capacity, 1)

        return {
            "cycle": "DARK",
            "duration_rounds": duration_rounds,
            "consumed": round(consumed_this_cycle, 4),
            "waste_remaining": round(self.waste_level, 4),
            "contamination_after": round(self.contamination_level, 4),
            "is_clean": self.waste_level <= MIN_WASTE_FLOOR,
            "rounds": round_log,
        }

    def run_light_cycle(self) -> Dict:
        """
        Lights on. Cockroaches go dormant. Zone is inspected.
        Returns the sanitation report — what the bin looks like now.
        """
        self.cycle = "LIGHT"
        self.cycles_completed += 1

        is_clean = self.waste_level <= MIN_WASTE_FLOOR
        sanitation_score = max(0, 1.0 - (self.waste_level / max(self.capacity, 1)))
        avg_health = sum(self.cockroach_health) / max(len(self.cockroach_health), 1)

        report = {
            "cycle": "LIGHT",
            "bin_id": self.bin_id,
            "cycles_completed": self.cycles_completed,
            "is_clean": is_clean,
            "sanitation_score": round(sanitation_score, 4),
            "waste_remaining": round(self.waste_level, 4),
            "total_consumed_lifetime": round(self.total_consumed, 2),
            "cockroach_count": self.n_cockroaches,
            "avg_cockroach_health": round(avg_health, 4),
            "contamination": round(self.contamination_level, 4),
        }

        self.history.append(report)
        return report

    def run_full_sanitation_cycle(self, waste_amount: float,
                                   waste_type: str = "organic",
                                   dark_rounds: int = 3) -> Dict:
        """
        Complete cycle: deposit waste → dark (cockroaches eat) → light (inspect).
        This is the full bin experience.
        """
        t_start = time.time()

        deposit = self.deposit_waste(waste_amount, waste_type)
        dark = self.run_dark_cycle(dark_rounds)
        light = self.run_light_cycle()

        elapsed = round(time.time() - t_start, 4)

        return {
            "bin_id": self.bin_id,
            "deposit": deposit,
            "dark_cycle": dark,
            "light_cycle": light,
            "elapsed_seconds": elapsed,
            "result": "SPOTLESS" if light["is_clean"] else "RESIDUE",
        }

    def get_status(self) -> Dict:
        return {
            "bin_id": self.bin_id,
            "cycle": self.cycle,
            "waste_level": round(self.waste_level, 2),
            "capacity": self.capacity,
            "contamination": round(self.contamination_level, 4),
            "cockroach_count": self.n_cockroaches,
            "cockroach_health": [round(h, 3) for h in self.cockroach_health],
            "cycles_completed": self.cycles_completed,
            "total_consumed": round(self.total_consumed, 2),
        }


class SanitationNetwork:
    """
    Network of sanitation bins — the commercial deployment.
    Multiple bins across different zones, each with its own cockroach colony.
    Neural control: the network decides when each bin enters dark/light cycle.
    """

    def __init__(self, rng_seed: int = 42):
        self.bins: Dict[str, SanitationBin] = {}
        self.rng = random.Random(rng_seed)
        self.network_id = hashlib.sha256(f"sanitation_{rng_seed}".encode()).hexdigest()[:12]
        self.total_cycles = 0

    def deploy_bin(self, bin_id: str, capacity: float = 100.0,
                   n_cockroaches: int = 5) -> Dict:
        """Deploy a new sanitation bin into the network."""
        seed = self.rng.randint(0, 2**31)
        self.bins[bin_id] = SanitationBin(bin_id, capacity, n_cockroaches, seed)
        return {
            "deployed": bin_id,
            "capacity": capacity,
            "cockroaches": n_cockroaches,
            "network_id": self.network_id,
            "total_bins": len(self.bins),
        }

    def run_network_cycle(self, waste_map: Dict[str, float],
                          dark_rounds: int = 3) -> Dict:
        """
        Run a full dark/light cycle across all bins in the network.
        waste_map: {bin_id: waste_amount}
        """
        results = {}
        clean_count = 0
        total_consumed = 0.0

        for bin_id, waste in waste_map.items():
            if bin_id not in self.bins:
                self.deploy_bin(bin_id)

            b = self.bins[bin_id]
            result = b.run_full_sanitation_cycle(waste, dark_rounds=dark_rounds)
            results[bin_id] = result

            if result["result"] == "SPOTLESS":
                clean_count += 1
            total_consumed += result["dark_cycle"]["consumed"]

        self.total_cycles += 1

        return {
            "network_id": self.network_id,
            "cycle_number": self.total_cycles,
            "bins_processed": len(results),
            "bins_clean": clean_count,
            "bins_with_residue": len(results) - clean_count,
            "total_consumed": round(total_consumed, 2),
            "network_sanitation_rate": round(clean_count / max(len(results), 1), 4),
            "bin_results": results,
        }

    def get_network_status(self) -> Dict:
        statuses = {bid: b.get_status() for bid, b in self.bins.items()}
        total_waste = sum(b.waste_level for b in self.bins.values())
        total_capacity = sum(b.capacity for b in self.bins.values())
        return {
            "network_id": self.network_id,
            "total_bins": len(self.bins),
            "total_cycles": self.total_cycles,
            "total_waste": round(total_waste, 2),
            "total_capacity": round(total_capacity, 2),
            "network_contamination": round(total_waste / max(total_capacity, 1), 4),
            "bins": statuses,
        }


def run_sanitation_demo(zones: Optional[List[str]] = None,
                        waste_per_zone: float = 80.0,
                        cockroaches_per_bin: int = 6,
                        dark_rounds: int = 5) -> Dict:
    """
    Run a full demonstration of the cockroach sanitation protocol.
    Deploys bins across zones, fills them with waste, runs dark/light cycles.

    Args:
        zones: list of zone names (defaults to commercial zones)
        waste_per_zone: how much waste to deposit in each bin
        cockroaches_per_bin: number of cockroaches per bin
        dark_rounds: how many rounds the dark cycle lasts
    """
    if zones is None:
        zones = [
            "supermarket_organic",
            "meat_processing",
            "food_storage",
            "restaurant_waste",
            "market_stall",
        ]

    network = SanitationNetwork(rng_seed=432)

    for zone in zones:
        network.deploy_bin(zone, capacity=100.0, n_cockroaches=cockroaches_per_bin)

    waste_map = {zone: waste_per_zone + network.rng.gauss(0, 10) for zone in zones}
    waste_map = {k: max(10, min(100, v)) for k, v in waste_map.items()}

    result = network.run_network_cycle(waste_map, dark_rounds=dark_rounds)

    status = network.get_network_status()

    return {
        "demo": "cockroach_sanitation_protocol",
        "zones": zones,
        "waste_per_zone": waste_per_zone,
        "cockroaches_per_bin": cockroaches_per_bin,
        "dark_rounds": dark_rounds,
        "cycle_result": result,
        "network_status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
