"""
VOID Vortex Shield Network — 10,000-node energy absorption grid.

Each node is a formation point that creates a local vacuum zone through
destructive interference of vibration patterns (silk / membrane oscillation).
The nodes collectively form a distributed shield that:

  1. Detects incoming energy wavefronts (blast, radiation, kinetic)
  2. Does NOT resist — creates vacuum channels that ABSORB
  3. Routes absorbed energy through vortex spirals to accumulation sinks
  4. Dissipates or stores the energy harmlessly

The mathematics:
  - Each node vibrates at its resonant frequency (base 432 Hz, harmonics)
  - Adjacent nodes create destructive interference → vacuum corridors
  - Vacuum corridors channel energy toward vortex accumulation points
  - Vortex points spin absorbed energy into thermal dissipation

Inspired by:
  - Formation Principle: frequency creates structure
  - Chladni patterns: standing waves create void zones
  - Metamaterial cloaking: route waves around a region
  - Faraday cage: but for kinetic/blast energy, not EM

A nuclear detonation at ground zero:
  - Blast wave radiates outward at ~300 m/s
  - Nodes detect pressure wavefront arrival
  - Each node activates vacuum channel toward nearest vortex sink
  - Energy flows INTO the vortex network instead of through the area
  - Vortex sinks dissipate energy as heat through underground channels
"""

import math
import time
import random
import hashlib
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

GRID_BASE_FREQ = 432.0
NODE_COUNT_DEFAULT = 10_000
VORTEX_SINK_RATIO = 0.02
VACUUM_THRESHOLD = 0.15
ABSORPTION_EFFICIENCY_BASE = 0.78
VORTEX_SPIN_RATE = 7.83
ENERGY_DISSIPATION_RATE = 0.94
BLAST_SPEED_MS = 300.0
SHIELD_ACTIVATION_MS = 0.8


class VortexNode:
    __slots__ = (
        "node_id", "x", "y", "freq", "phase", "is_vortex_sink",
        "vacuum_strength", "absorbed_energy", "active",
        "neighbours", "activation_time", "spin_rate",
    )

    def __init__(self, node_id: int, x: float, y: float, freq: float,
                 is_vortex_sink: bool = False, rng: random.Random = None):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.freq = freq
        self.phase = (rng or random).uniform(0, 2 * math.pi)
        self.is_vortex_sink = is_vortex_sink
        self.vacuum_strength = 0.0
        self.absorbed_energy = 0.0
        self.active = True
        self.neighbours: List[int] = []
        self.activation_time = 0.0
        self.spin_rate = VORTEX_SPIN_RATE if is_vortex_sink else 0.0

    def distance_to(self, other: "VortexNode") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def interference_with(self, other: "VortexNode") -> float:
        phase_diff = abs(self.phase - other.phase) % (2 * math.pi)
        return abs(math.cos(phase_diff / 2))

    def to_dict(self) -> Dict:
        return {
            "id": self.node_id,
            "x": round(self.x, 4),
            "y": round(self.y, 4),
            "freq": round(self.freq, 2),
            "is_vortex_sink": self.is_vortex_sink,
            "vacuum_strength": round(self.vacuum_strength, 6),
            "absorbed_energy": round(self.absorbed_energy, 4),
            "active": self.active,
            "spin_rate": round(self.spin_rate, 4),
        }


class BlastEvent:
    __slots__ = ("origin_x", "origin_y", "yield_kt", "speed_ms", "energy_total")

    def __init__(self, origin_x: float, origin_y: float, yield_kt: float):
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.yield_kt = yield_kt
        self.speed_ms = BLAST_SPEED_MS
        self.energy_total = yield_kt * 4.184e12

    def energy_at_distance(self, dist_m: float) -> float:
        if dist_m < 1.0:
            dist_m = 1.0
        return self.energy_total / (4 * math.pi * dist_m ** 2)

    def arrival_time(self, dist_m: float) -> float:
        return dist_m / self.speed_ms


class VortexShieldNetwork:
    def __init__(self, area_km: float = 50.0, node_count: int = NODE_COUNT_DEFAULT,
                 seed: str = "VOID_SHIELD_432"):
        self.area_km = area_km
        self.area_m = area_km * 1000.0
        self.node_count = node_count
        self.seed = seed
        self.rng = random.Random(
            int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
        )
        self.nodes: List[VortexNode] = []
        self.vortex_sinks: List[VortexNode] = []
        self.vacuum_corridors: List[Tuple[int, int, float]] = []
        self.total_absorbed = 0.0
        self.total_dissipated = 0.0
        self.shield_grade = "INACTIVE"
        self.build_time = 0.0

        self._build_network()

    def _build_network(self):
        t0 = time.time()
        half = self.area_m / 2.0
        n_sinks = max(10, int(self.node_count * VORTEX_SINK_RATIO))

        sink_ids = set(self.rng.sample(range(self.node_count), n_sinks))

        harmonics = [1, 2, 3, 4, 5, 6, 7]
        for i in range(self.node_count):
            x = self.rng.uniform(-half, half)
            y = self.rng.uniform(-half, half)
            harmonic = harmonics[i % len(harmonics)]
            freq = GRID_BASE_FREQ * harmonic
            is_sink = i in sink_ids

            node = VortexNode(i, x, y, freq, is_sink, self.rng)
            if is_sink:
                node.spin_rate = VORTEX_SPIN_RATE * (1 + self.rng.uniform(0, 0.5))
            self.nodes.append(node)

        for node in self.nodes:
            if node.is_vortex_sink:
                self.vortex_sinks.append(node)

        self._build_neighbour_grid()
        self._compute_vacuum_corridors()

        self.build_time = time.time() - t0
        logger.info(
            "[VortexShield] Network built: %d nodes, %d vortex sinks, "
            "%d vacuum corridors in %.3fs",
            self.node_count, len(self.vortex_sinks),
            len(self.vacuum_corridors), self.build_time
        )

    def _build_neighbour_grid(self):
        cell_size = self.area_m / 50.0
        grid: Dict[Tuple[int, int], List[int]] = {}

        for node in self.nodes:
            cx = int((node.x + self.area_m / 2) / cell_size)
            cy = int((node.y + self.area_m / 2) / cell_size)
            grid.setdefault((cx, cy), []).append(node.node_id)

        for node in self.nodes:
            cx = int((node.x + self.area_m / 2) / cell_size)
            cy = int((node.y + self.area_m / 2) / cell_size)
            neighbours = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for nid in grid.get((cx + dx, cy + dy), []):
                        if nid != node.node_id:
                            neighbours.append(nid)
            node.neighbours = neighbours[:12]

    def _compute_vacuum_corridors(self):
        corridors = []
        for node in self.nodes:
            for nid in node.neighbours:
                if nid > node.node_id:
                    other = self.nodes[nid]
                    interference = node.interference_with(other)
                    if interference < VACUUM_THRESHOLD:
                        strength = 1.0 - interference / VACUUM_THRESHOLD
                        corridors.append((node.node_id, nid, strength))
                        node.vacuum_strength = max(node.vacuum_strength, strength)
                        other.vacuum_strength = max(other.vacuum_strength, strength)

        self.vacuum_corridors = corridors

    def simulate_blast(self, blast: BlastEvent, time_steps: int = 100) -> Dict:
        t0 = time.time()

        corridor_map: Dict[int, List[Tuple[int, float]]] = {}
        for (a, b, strength) in self.vacuum_corridors:
            corridor_map.setdefault(a, []).append((b, strength))
            corridor_map.setdefault(b, []).append((a, strength))

        node_dists = []
        for node in self.nodes:
            dist = math.sqrt(
                (node.x - blast.origin_x) ** 2 +
                (node.y - blast.origin_y) ** 2
            )
            node_dists.append((dist, node))
        node_dists.sort(key=lambda x: x[0])

        nodes_destroyed = 0
        energy_absorbed_total = 0.0
        energy_passed_total = 0.0
        vortex_accumulation = 0.0
        activation_wave = []

        for dist, node in node_dists:
            arrival_t = blast.arrival_time(dist)
            node.activation_time = arrival_t
            if len(activation_wave) < 20:
                activation_wave.append({
                    "node_id": node.node_id,
                    "time": round(arrival_t, 4),
                    "distance_m": round(dist, 1),
                })

            incoming_energy = blast.energy_at_distance(dist)

            vacuum_factor = node.vacuum_strength
            absorption = incoming_energy * ABSORPTION_EFFICIENCY_BASE * (0.5 + 0.5 * vacuum_factor)
            passed = incoming_energy - absorption

            node.absorbed_energy += absorption
            energy_absorbed_total += absorption

            if node.is_vortex_sink:
                spin_absorption = passed * 0.6 * (node.spin_rate / VORTEX_SPIN_RATE)
                node.absorbed_energy += spin_absorption
                vortex_accumulation += spin_absorption
                energy_absorbed_total += spin_absorption
                passed -= spin_absorption

            for (nid, corridor_strength) in corridor_map.get(node.node_id, []):
                neighbour = self.nodes[nid]
                if neighbour.is_vortex_sink and neighbour.active:
                    routed = passed * corridor_strength * 0.3
                    neighbour.absorbed_energy += routed
                    vortex_accumulation += routed
                    energy_absorbed_total += routed
                    passed -= routed

            energy_passed_total += max(0, passed)

            if incoming_energy > blast.energy_total * 0.0001 and vacuum_factor < 0.05:
                node.active = False
                nodes_destroyed += 1

        nodes_survived = sum(1 for n in self.nodes if n.active)

        intercepted_total = energy_absorbed_total + energy_passed_total
        if intercepted_total > 0:
            shield_efficiency = (energy_absorbed_total / intercepted_total) * 100
        else:
            shield_efficiency = 0.0

        dissipated = vortex_accumulation * ENERGY_DISSIPATION_RATE
        self.total_absorbed = energy_absorbed_total
        self.total_dissipated = dissipated

        if shield_efficiency > 85:
            self.shield_grade = "SOVEREIGN"
        elif shield_efficiency > 70:
            self.shield_grade = "FORTIFIED"
        elif shield_efficiency > 55:
            self.shield_grade = "ACTIVE"
        elif shield_efficiency > 40:
            self.shield_grade = "PARTIAL"
        else:
            self.shield_grade = "COMPROMISED"

        sim_time = time.time() - t0

        return {
            "seed": self.seed,
            "area_km": self.area_km,
            "node_count": self.node_count,
            "vortex_sinks": len(self.vortex_sinks),
            "vacuum_corridors": len(self.vacuum_corridors),
            "blast": {
                "origin": [blast.origin_x, blast.origin_y],
                "yield_kt": blast.yield_kt,
                "energy_total_j": blast.energy_total,
            },
            "results": {
                "nodes_destroyed": nodes_destroyed,
                "nodes_survived": nodes_survived,
                "survival_rate": round(nodes_survived / max(self.node_count, 1) * 100, 2),
                "energy_absorbed_j": round(energy_absorbed_total, 2),
                "energy_passed_j": round(energy_passed_total, 2),
                "shield_efficiency_pct": round(shield_efficiency, 2),
                "vortex_accumulation_j": round(vortex_accumulation, 2),
                "vortex_dissipated_j": round(dissipated, 2),
            },
            "shield_grade": self.shield_grade,
            "activation_wave_sample": activation_wave[:20],
            "simulation_time_s": round(sim_time, 4),
            "build_time_s": round(self.build_time, 4),
        }

    def get_field_snapshot(self, resolution: int = 50) -> Dict:
        half = self.area_m / 2.0
        step = self.area_m / resolution

        field = []
        for iy in range(resolution):
            row = []
            y = -half + iy * step
            for ix in range(resolution):
                x = -half + ix * step

                total_vacuum = 0.0
                total_energy = 0.0
                count = 0

                for node in self.vortex_sinks:
                    dist = math.sqrt((x - node.x) ** 2 + (y - node.y) ** 2)
                    if dist < step * 3:
                        total_vacuum += node.vacuum_strength
                        total_energy += node.absorbed_energy
                        count += 1

                if count > 0:
                    row.append({
                        "v": round(total_vacuum / count, 4),
                        "e": round(total_energy / count, 4),
                    })
                else:
                    row.append({"v": 0, "e": 0})
            field.append(row)

        return {
            "resolution": resolution,
            "area_km": self.area_km,
            "field": field,
        }

    def network_summary(self) -> Dict:
        active = sum(1 for n in self.nodes if n.active)
        avg_vacuum = sum(n.vacuum_strength for n in self.nodes) / max(len(self.nodes), 1)
        max_vacuum = max((n.vacuum_strength for n in self.nodes), default=0)
        total_absorbed = sum(n.absorbed_energy for n in self.nodes)
        sink_absorbed = sum(n.absorbed_energy for n in self.vortex_sinks)

        return {
            "total_nodes": self.node_count,
            "active_nodes": active,
            "vortex_sinks": len(self.vortex_sinks),
            "vacuum_corridors": len(self.vacuum_corridors),
            "avg_vacuum_strength": round(avg_vacuum, 6),
            "max_vacuum_strength": round(max_vacuum, 6),
            "total_absorbed_energy": round(total_absorbed, 4),
            "sink_absorbed_energy": round(sink_absorbed, 4),
            "shield_grade": self.shield_grade,
            "build_time_s": round(self.build_time, 4),
        }
