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

Buffer Spore (Task #81):
  A digital cache layer predicts mushroom health during Mycelium Lag
  (periods when real bio-state is unavailable).  The last known bio-state
  is stored with a timestamp.  A time-decay model reduces confidence as
  staleness grows.  The estimated vs. real delta is surfaced in the
  status dict under the "buffer_spore" key so the dashboard can display
  it live.  The AI Model Switcher consumes estimated_bio_state instead
  of stalling when readings are absent.
"""

import time
import math
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Buffer Spore state ──────────────────────────────────────────────────────
# Stores the last confirmed real bio-state and the time it was received.
# Half-life: 300 s (5 min) — after that confidence is below 0.5.
_BUFFER_SPORE_HALF_LIFE_S = 300.0
_last_real_bio: Optional[Dict] = None
_last_real_bio_time: float = 0.0
_last_estimated_bio: Optional[Dict] = None
_last_bio_delta: Optional[Dict] = None


def _compute_spore_decay(age_s: float) -> float:
    """Return a [0, 1] confidence score that decays exponentially with age."""
    return math.exp(-math.log(2) * age_s / _BUFFER_SPORE_HALF_LIFE_S)


def _make_estimated_bio(real_bio: Dict, decay: float) -> Dict:
    """
    Produce an estimated bio-state by blending the last known real values
    towards neutral (0.5 / baseline) as confidence drops.
    """
    neutral = {
        "water_level": 0.7,
        "temperature": 23.0,
        "ph": 6.75,
        "dissolved_oxygen": 7.0,
        "growth_density": 0.35,
        "moisture": 0.55,
    }
    estimated = {}
    for k, neutral_v in neutral.items():
        real_v = real_bio.get(k, neutral_v)
        if isinstance(real_v, (int, float)):
            estimated[k] = round(real_v * decay + neutral_v * (1.0 - decay), 4)
        else:
            estimated[k] = real_v
    estimated["csi_source"] = "buffer_spore_estimate"
    return estimated


def _compute_bio_delta(real_bio: Dict, estimated_bio: Dict) -> Dict:
    """
    Compute field-wise absolute delta between the real bio-state and the
    buffer spore estimate, so the dashboard can display divergence live.
    """
    keys = ["water_level", "temperature", "ph", "dissolved_oxygen",
            "growth_density", "moisture"]
    delta = {}
    for k in keys:
        r = real_bio.get(k)
        e = estimated_bio.get(k)
        if isinstance(r, (int, float)) and isinstance(e, (int, float)):
            delta[k] = round(abs(r - e), 4)
    return delta


def get_buffer_spore_state() -> Dict:
    """
    Return the current Buffer Spore prediction state, including:
      - estimated_bio_state: what the switcher should use during lag
      - real_bio_state:      last confirmed reading (may be stale)
      - confidence:          [0, 1] decay score
      - age_s:               seconds since last real reading
      - delta:               per-field divergence (estimated vs real)
    """
    global _last_real_bio, _last_real_bio_time, _last_estimated_bio, _last_bio_delta
    now = time.time()
    age_s = now - _last_real_bio_time if _last_real_bio_time > 0 else float("inf")
    decay = _compute_spore_decay(age_s) if age_s < float("inf") else 0.0

    if _last_real_bio is not None:
        estimated = _make_estimated_bio(_last_real_bio, decay)
        delta = _compute_bio_delta(_last_real_bio, estimated)
    else:
        estimated = None
        delta = None

    _last_estimated_bio = estimated
    _last_bio_delta = delta

    in_lag = (_last_real_bio is None) or (age_s > 30.0)

    return {
        "estimated_bio_state": estimated,
        "real_bio_state": _last_real_bio,
        "confidence": round(decay, 4),
        "age_s": round(age_s, 1) if age_s < float("inf") else None,
        "in_mycelium_lag": in_lag,
        "delta": delta,
    }


def update_buffer_spore(real_bio: Dict) -> None:
    """Record a fresh real bio-state reading, resetting the decay clock."""
    global _last_real_bio, _last_real_bio_time
    _last_real_bio = dict(real_bio)
    _last_real_bio_time = time.time()

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
      - buffer_spore: Buffer Spore prediction cache state (Task #81)
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

    status = network.get_status()
    status["buffer_spore"] = get_buffer_spore_state()
    return status


def _get_bio_inputs() -> List[float]:
    """
    Return VOID resonance inputs for the mycelium forward pass.

    Uses 432 Hz / 7.83 Hz normalised values as the baseline biological
    signal, optionally enriched by the shared BiologicalTransceiver when
    it is already initialised (avoids circular import with csi_bio_monitor).

    Also feeds the Buffer Spore cache with the real bio-state so the
    decay model has a fresh anchor on every successful reading.
    """
    try:
        import routes.shared as _shared
        state = _shared.biological._csi_monitor.read_sensor_state()
        if state.get("csi_source") not in ("no_data", "buffer_spore_estimate"):
            update_buffer_spore(state)
        return [
            float(state.get("water_level", 0.5)),
            min(1.0, float(state.get("temperature", 22.0)) / 30.0),
            float(state.get("growth_density", 0.5)),
            float(state.get("moisture", 0.5)),
        ]
    except Exception:
        # VOID resonance defaults: 432 Hz anchor + Schumann + mid-values
        return [0.432 / 1.0, 7.83 / 30.0, 0.5, 0.5]


def get_bio_state_for_switcher() -> Dict:
    """
    Return the best available bio-state for the AI Model Switcher.

    During Mycelium Lag (no fresh readings), the Buffer Spore estimate is
    returned so the switcher never enters a stutter state.  The caller
    should inspect the 'in_mycelium_lag' and 'confidence' fields to decide
    whether to treat the values as authoritative.
    """
    spore = get_buffer_spore_state()
    if spore["in_mycelium_lag"] and spore["estimated_bio_state"]:
        return spore["estimated_bio_state"]
    if spore["real_bio_state"]:
        return spore["real_bio_state"]
    return {
        "water_level": 0.7,
        "temperature": 23.0,
        "ph": 6.75,
        "dissolved_oxygen": 7.0,
        "growth_density": 0.35,
        "moisture": 0.55,
        "csi_source": "buffer_spore_default",
    }


def get_node_count() -> int:
    """Return the number of currently active (non-idle) mycelium nodes."""
    return get_network_status(run_steps=0).get("active_nodes", 0)
