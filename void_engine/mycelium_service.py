"""
Mycelium Network Service — backed by angrysky56/mycelium_network
================================================================
Wraps the vendored AdvancedMyceliumNetwork (see void_engine/mycelium/)
and exposes a dashboard-ready get_network_status() API that is consumed
by routes/mycovoid.py and void_engine/csi_bio_monitor.py.

The VOID environment seeds two resonance resources:
  (0.432, 0.432) — 432 Hz SOL anchor
  (0.783, 0.216) — 7.83 Hz Schumann sub-tone

Network signals are fed by VOID biological readings so the mycelium
responds to the same inputs as the rest of the engine.
"""

import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_NETWORK_INSTANCE: Optional["_VoidMyceliumWrapper"] = None
_LAST_STEP_TIME: float = 0.0

# How many signal channels we expose to the mycelium network
_INPUT_SIZE = 4   # water_level, temperature, growth_density, moisture
_OUTPUT_SIZE = 4  # mapped back to VOID resonance channels


class _VoidMyceliumWrapper:
    """
    Thin wrapper around AdvancedMyceliumNetwork (angrysky56/mycelium_network)
    that maintains VOID-specific environment initialisation and exposes
    the get_status() contract expected by the rest of the engine.
    """

    def __init__(self):
        from void_engine.mycelium.network import AdvancedMyceliumNetwork
        from void_engine.mycelium.environment import Environment

        self._env = Environment(dimensions=2, size=1.0)

        # Seed 432 Hz and Schumann resonance resource points into the environment
        self._env.add_resource((0.432, 0.432), 10.0)   # 432 Hz SOL anchor
        self._env.add_resource((0.783, 0.216), 7.83)   # 7.83 Hz Schumann
        self._env.add_resource((0.5, 0.5), 5.0)        # centre node

        self._net = AdvancedMyceliumNetwork(
            environment=self._env,
            input_size=_INPUT_SIZE,
            output_size=_OUTPUT_SIZE,
        )

        self._step_count = 0
        self._created_at = time.time()
        logger.info(
            "VoidMyceliumWrapper initialised: %d total nodes (angrysky56/mycelium_network)",
            self._net.get_network_statistics().get("node_count", 0),
        )

    def _compute_strongest_path(self, max_length: int = 5) -> List[int]:
        """
        Trace the strongest activation path through the real network topology.

        Selects the highest-activation node that has at least one outgoing
        connection as the starting point (prefers regular nodes), then greedily
        follows the highest-activation neighbour at each step without revisiting,
        returning the ordered list of real node IDs.
        """
        nodes = self._net.nodes  # dict[int, MyceliumNode]
        if not nodes:
            return []

        input_set = set(self._net.input_nodes)
        output_set = set(self._net.output_nodes)

        # Candidate nodes: must have ≥1 connection; prefer regular nodes first
        connected = [
            (nid, getattr(n, "activation", 0.0))
            for nid, n in nodes.items()
            if getattr(n, "connections", [])
        ]
        if not connected:
            return list(nodes.keys())[:max_length]

        # Start from the connected regular node with the highest activation;
        # fall back to any connected node if no regular node is connected.
        regular_connected = [(nid, act) for nid, act in connected if nid not in input_set and nid not in output_set]
        candidates = regular_connected if regular_connected else connected
        start_id = max(candidates, key=lambda x: x[1])[0]

        path = [start_id]
        visited = {start_id}
        current_id = start_id

        for _ in range(max_length - 1):
            node = nodes.get(current_id)
            if node is None:
                break
            conns = getattr(node, "connections", [])
            best_id, best_act = None, -1.0
            for conn_id in conns:
                if conn_id in visited or conn_id not in nodes:
                    continue
                act = getattr(nodes[conn_id], "activation", 0.0)
                if act > best_act:
                    best_act = act
                    best_id = conn_id
            if best_id is None:
                break
            path.append(best_id)
            visited.add(best_id)
            current_id = best_id

        return path

    def step(self, inputs: Optional[List[float]] = None) -> None:
        """
        Run one forward pass through the network using VOID bio-signals.

        inputs should be [water_level, temperature, growth_density, moisture]
        normalised to [0, 1].  Falls back to neutral values if not provided.
        """
        if inputs is None:
            inputs = [0.5, 0.5, 0.5, 0.5]
        inputs = inputs[:_INPUT_SIZE]
        while len(inputs) < _INPUT_SIZE:
            inputs.append(0.5)

        try:
            self._net.forward(inputs)
        except Exception as exc:
            logger.debug("mycelium forward pass failed: %s", exc)

        self._step_count += 1

    def get_status(self) -> Dict:
        stats = self._net.get_network_statistics()

        total_nodes = stats.get("node_count", 0)
        input_nodes = stats.get("input_nodes", 0)
        output_nodes = stats.get("output_nodes", 0)
        regular_nodes = stats.get("regular_nodes", 0)
        avg_energy = stats.get("avg_energy", 0.0)
        total_resources = stats.get("total_resources", 0.0)
        iteration = stats.get("iteration", self._step_count)

        # Map avg_energy to node state breakdown (energy thresholds)
        # absorbing: energy > 0.8, active: 0.4–0.8, idle: 0.2–0.4, warn: < 0.2
        absorbing_est = int(regular_nodes * max(0, min(1, (avg_energy - 0.8) / 0.2)))
        idle_est = int(regular_nodes * max(0, min(1, (0.4 - avg_energy) / 0.2)))
        warn_est = int(regular_nodes * max(0, min(1, (0.2 - avg_energy) / 0.2)))
        active_est = regular_nodes - absorbing_est - idle_est - warn_est

        node_breakdown = {
            "active": max(0, active_est),
            "absorbing": max(0, absorbing_est),
            "idle": max(0, idle_est),
            "warn": max(0, warn_est),
        }
        active_nodes = node_breakdown["active"] + node_breakdown["absorbing"]

        # Strongest signal path: walk actual node connections by activation level
        strongest_path = self._compute_strongest_path(max_length=5)

        return {
            "active_nodes": active_nodes,
            "idle_nodes": node_breakdown["idle"],
            "warn_nodes": node_breakdown["warn"],
            "total_nodes": total_nodes,
            "total_resource_flow": round(float(total_resources), 3),
            "avg_signal_strength": round(float(avg_energy), 4),
            "strongest_signal_path": strongest_path,
            "step_count": self._step_count,
            "uptime_sec": round(time.time() - self._created_at, 1),
            "node_breakdown": node_breakdown,
        }


def _get_network() -> _VoidMyceliumWrapper:
    global _NETWORK_INSTANCE
    if _NETWORK_INSTANCE is None:
        _NETWORK_INSTANCE = _VoidMyceliumWrapper()
    return _NETWORK_INSTANCE


def get_network_status(run_steps: int = 1) -> Dict:
    """
    Run one or more network forward passes and return the current state.

    Throttled to at most one real step every 5 seconds so that rapid calls
    to /api/mycovoid/status do not over-consume CPU.

    Returns a dashboard-ready dict:
      - active_nodes: int
      - total_resource_flow: float
      - strongest_signal_path: list[int]
      - avg_signal_strength: float
      - step_count: int
      - uptime_sec: float
      - node_breakdown: dict
    """
    global _LAST_STEP_TIME
    network = _get_network()

    now = time.time()
    if run_steps > 0 and now - _LAST_STEP_TIME >= 5.0:
        # Pull latest bio-signals to feed the network
        bio_inputs = _get_bio_inputs()
        for _ in range(run_steps):
            network.step(bio_inputs)
        _LAST_STEP_TIME = now

    return network.get_status()


def _get_bio_inputs() -> List[float]:
    """
    Return VOID resonance inputs for the mycelium forward pass.

    Uses 432 Hz / 7.83 Hz normalised values as the baseline biological
    signal, optionally enriched by the shared BiologicalTransceiver when
    it is already initialised (avoids circular import with csi_bio_monitor).
    """
    try:
        import routes.shared as _shared
        # Use the already-running biological monitor if available
        state = _shared.biological._csi_monitor.read_sensor_state()
        return [
            float(state.get("water_level", 0.5)),
            min(1.0, float(state.get("temperature", 22.0)) / 30.0),
            float(state.get("growth_density", 0.5)),
            float(state.get("moisture", 0.5)),
        ]
    except Exception:
        # VOID resonance defaults: 432 Hz anchor + Schumann + mid-values
        return [0.432 / 1.0, 7.83 / 30.0, 0.5, 0.5]


def get_node_count() -> int:
    """Return the number of currently active (non-idle) mycelium nodes."""
    return get_network_status(run_steps=0).get("active_nodes", 0)
