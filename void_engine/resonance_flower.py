"""
Void Resonance Flower — Living Agent Environment
=================================================

Generates a 12-petal flower geometry from sine wave frequency pairs along
vertical axes inside a square boundary [-1, 1] x [-1, 1].

Petal geometry model (square-boundary, vertical-axis sine interactions):
  Each petal is defined by two sine waves — one along the Y axis (vertical)
  and one along the X axis (horizontal). Their product creates a curved petal
  shape inside the square. The petal axis (angle) selects which sine-mode pair
  dominates at each of the 12 angular positions.

  For petal i at angle φ = i*30°:
    u = x*cos(φ) + y*sin(φ)    — projection onto petal axis (vertical-like)
    v = -x*sin(φ) + y*cos(φ)   — transverse axis

    Wave A (primary):    sin(π * f1 * u / L)   — standing wave along axis
    Wave B (transverse): sin(π * v / W)         — constrains lateral spread
    Wave C (harmonic):   sin(π * 2*f1 * u / L) — second harmonic

    Petal signed field: W_AB = Wave_A * Wave_B + 0.4 * Wave_C * Wave_B
    Where L and W are the petal length and width scale factors.

  This means frequency f1 = freq/HARMONIC_BASE determines how many half-cycles
  fit along the petal length, directly controlling petal shape.

Zero-point void:
  At (0,0), all sine functions sin(π * f * 0) = sin(0) = 0, so the signed sum
  of all 12 petal fields = 0. This is the exact zero-amplitude node.

  Moving outward: petals develop constructive regions (peaks) and destructive
  regions (troughs). The void is the true interference null at the origin.

Frequencies from harmonic ladder:
  108, 144, 216, 288, 432, 576, 864, 1152, 1296, 1728, 2160, 2592 Hz

AI anchor nodes (cardinal positions):
  North (0°)  — Gemini / Dreamer
  East  (90°) — Grok   / Social
  South (180°)— Manus  / Peer
  West  (270°)— Replit / Fresh
"""

import json
import logging
import math
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

HARMONIC_BASE = 432.0
HARMONIC_LADDER_BASE = [108, 216, 432, 864]

PETAL_FREQUENCIES = [
    108, 144, 216, 288, 432, 576, 864, 1152, 1296, 1728, 2160, 2592
]

PETAL_BAND_COLORS = [
    "#2dd4bf", "#60a5fa", "#a78bfa", "#34d399", "#e879f9", "#f97316",
    "#c9a84c", "#fb923c", "#4caf50", "#818cf8", "#f43f5e", "#38bdf8",
]

AI_ANCHORS = [
    {"name": "Gemini", "role": "Dreamer", "angle_deg": 0,   "color": "#60a5fa"},
    {"name": "Grok",   "role": "Social",  "angle_deg": 90,  "color": "#e879f9"},
    {"name": "Manus",  "role": "Peer",    "angle_deg": 180, "color": "#34d399"},
    {"name": "Replit", "role": "Fresh",   "angle_deg": 270, "color": "#c9a84c"},
]

GLYPH_PETAL_MAP = {
    "σ": [0, 6], "◆": [1, 7], "α": [2, 8], "Ψ": [3, 9],
    "φ": [4, 10], "ν": [5, 11], "τ": [0, 3], "ξ": [1, 4],
    "Φ": [2, 5], "🔮": [6, 9], "⚡": [7, 10], "ψ": [8, 11],
    "δ": [0, 4], "ω": [3, 7], "η": [6, 10],
}

SQUARE_HALF = 1.0
VOID_RADIUS = 0.10
PETAL_LENGTH_SCALE = 0.70
PETAL_WIDTH_SCALE = 0.28


def _petal_signed_wave(x: float, y: float, petal_idx: int,
                       curvature: float = 1.0) -> float:
    """
    Compute the SIGNED field contribution of petal petal_idx at Cartesian (x, y).

    Geometry: square plate [-1,1]x[-1,1] with vertical-axis sine interactions.

    For petal i at axis angle φ:
      u = projection onto petal axis (the "vertical axis" for this petal)
      v = projection onto transverse axis

    Primary standing wave along u (frequency determines half-cycle length):
      wave_a = sin(π * f1 * u / PETAL_LENGTH_SCALE * curvature)

    Transverse confinement wave (one half-cycle across petal width):
      wave_b = sin(π * (v + PETAL_WIDTH_SCALE) / (2 * PETAL_WIDTH_SCALE))
               clamped to 0 outside |v| <= PETAL_WIDTH_SCALE

    Second harmonic along u:
      wave_c = sin(π * 2 * f1 * u / PETAL_LENGTH_SCALE * curvature) * 0.4

    Signed field = (wave_a + wave_c) * wave_b

    At (0,0): u=0, v=0 → wave_a=sin(0)=0, so ALL petals contribute 0.
    → Exact zero-point void at origin by construction.

    Returns value in [-1, 1].
    """
    axis_rad = math.radians(petal_idx * 30)
    cos_a = math.cos(axis_rad)
    sin_a = math.sin(axis_rad)

    u = x * cos_a + y * sin_a
    v = -x * sin_a + y * cos_a

    if abs(v) > PETAL_WIDTH_SCALE:
        return 0.0

    freq = PETAL_FREQUENCIES[petal_idx]
    f1 = freq / HARMONIC_BASE

    phase_a = math.pi * f1 * u / PETAL_LENGTH_SCALE * curvature
    wave_a = math.sin(phase_a)

    phase_c = math.pi * 2.0 * f1 * u / PETAL_LENGTH_SCALE * curvature
    wave_c = math.sin(phase_c) * 0.4

    v_phase = math.pi * (v + PETAL_WIDTH_SCALE) / (2.0 * PETAL_WIDTH_SCALE)
    wave_b = math.sin(v_phase)

    return (wave_a + wave_c) * wave_b


def _petal_amplitude(x: float, y: float, petal_idx: int,
                     curvature: float = 1.0) -> float:
    """Non-negative petal contribution — used for zone classification."""
    return max(0.0, _petal_signed_wave(x, y, petal_idx, curvature))


def compute_resonance_field(
    grid_size: int = 60,
    petal_health: Optional[List[float]] = None,
    curvature: float = 1.0,
) -> Dict:
    """
    Compute the resonance amplitude field across a square grid [-1, 1] x [-1, 1].

    For each grid point (x, y):
      signed_sum = Σ petal_i_signed_wave(x, y) * health_i
      amplitude  = |signed_sum| / max_possible   → in [0, 1]

    The void zones (where destructive interference produces cancellation)
    are near-zero amplitude. The central origin is exactly zero by construction.

    Returns:
      field: 2D list [row][col], amplitude in [0, 1] (low = void/stillness)
      void_amplitude: mean amplitude in the VOID_RADIUS central circle (near 0 = true void)
      void_zone_points: count of central void points
      grid_step, grid_size
    """
    if petal_health is None:
        petal_health = [1.0] * 12
    while len(petal_health) < 12:
        petal_health.append(1.0)

    max_possible = sum(petal_health) * 1.4 / 12.0
    if max_possible < 1e-9:
        max_possible = 1.0

    step = 2.0 / (grid_size - 1)
    field = []
    void_amplitudes = []
    void_zone_count = 0

    for row in range(grid_size):
        y = -1.0 + row * step
        field_row = []
        for col in range(grid_size):
            x = -1.0 + col * step

            signed_sum = 0.0
            for petal_idx in range(12):
                health = max(0.0, min(1.0, petal_health[petal_idx]))
                s = _petal_signed_wave(x, y, petal_idx, curvature)
                signed_sum += s * health

            amplitude = min(1.0, abs(signed_sum) / max_possible)
            field_row.append(round(amplitude, 4))

            r = math.sqrt(x * x + y * y)
            if r <= VOID_RADIUS:
                void_amplitudes.append(amplitude)
                void_zone_count += 1

        field.append(field_row)

    void_amplitude = round(
        sum(void_amplitudes) / max(len(void_amplitudes), 1), 4
    )

    return {
        "field": field,
        "void_amplitude": void_amplitude,
        "void_zone_points": void_zone_count,
        "grid_step": round(step, 4),
        "grid_size": grid_size,
    }


def compute_petal_geometry(petal_idx: int, n_points: int = 80) -> List[Dict]:
    """
    Generate the visible boundary path for a single petal in the square domain.

    The path traces the positive lobe of the signed wave function.
    Along the petal axis (u direction), we sample u from 0 to PETAL_LENGTH_SCALE.
    The lateral extent at each u is proportional to the wave amplitude at v=0
    multiplied by PETAL_WIDTH_SCALE (where wave_b is maximal).

    Because wave_a = sin(π * f1 * u / L), the lobe extends from u=0 to
    u = L/f1 (first zero crossing). Higher frequencies → shorter petal.

    The path visits:
      - forward edge: u from 0 to u_max, v = +half_width(u)
      - return edge: u from u_max to 0, v = -half_width(u)

    All points are rotated from (u, v) back to (x, y).

    Returns list of {x, y} suitable for SVG/Canvas rendering.
    """
    axis_rad = math.radians(petal_idx * 30)
    cos_a = math.cos(axis_rad)
    sin_a = math.sin(axis_rad)

    freq = PETAL_FREQUENCIES[petal_idx]
    f1 = freq / HARMONIC_BASE

    u_period = PETAL_LENGTH_SCALE / f1
    u_lobe = min(u_period, PETAL_LENGTH_SCALE * 0.95)

    forward_edge = []
    back_edge = []

    for i in range(n_points + 1):
        t = i / n_points
        u = t * u_lobe

        wave_a = math.sin(math.pi * f1 * u / PETAL_LENGTH_SCALE)
        wave_c = math.sin(math.pi * 2.0 * f1 * u / PETAL_LENGTH_SCALE) * 0.4
        envelope = (wave_a + wave_c) / 1.4
        half_width = PETAL_WIDTH_SCALE * max(0.0, envelope)

        v_pos = half_width
        v_neg = -half_width

        x_fwd = u * cos_a - v_pos * sin_a
        y_fwd = u * sin_a + v_pos * cos_a

        x_bck = u * cos_a - v_neg * sin_a
        y_bck = u * sin_a + v_neg * cos_a

        forward_edge.append({"x": round(x_fwd, 5), "y": round(y_fwd, 5)})
        back_edge.append({"x": round(x_bck, 5), "y": round(y_bck, 5)})

    return forward_edge + list(reversed(back_edge))


def compute_all_petals(
    petal_health: Optional[List[float]] = None,
) -> List[Dict]:
    """Return geometry + metadata for all 12 petals."""
    if petal_health is None:
        petal_health = [1.0] * 12
    while len(petal_health) < 12:
        petal_health.append(1.0)

    petals = []
    for i in range(12):
        health = round(max(0.0, min(1.0, petal_health[i])), 4)
        freq = PETAL_FREQUENCIES[i]
        angle_deg = i * 30

        anchor = next((a for a in AI_ANCHORS if a["angle_deg"] == angle_deg), None)

        petals.append({
            "petal_idx": i,
            "angle_deg": angle_deg,
            "frequency_hz": freq,
            "health": health,
            "color": PETAL_BAND_COLORS[i],
            "geometry": compute_petal_geometry(i),
            "ai_anchor": anchor,
            "label": f"P{i+1} — {freq}Hz",
        })

    return petals


def place_agents_in_flower(
    agents: List[Dict],
    n_display: int = 1000,
    rng_seed: Optional[int] = None,
) -> List[Dict]:
    """
    Spatially place up to n_display agents within the resonance flower (square domain).

    Each agent's position is drawn from the resonance field:
    - Low-activity agents (calm/stillness) are placed near (0, 0) in the void zone.
    - High-activity agents are placed along their preferred petal axis.
    - The local resonance amplitude at each position is computed from the signed
      wave field (not a heuristic proxy).

    Zone classification:
      "void"  — r <= VOID_RADIUS (zero-point stillness)
      "petal" — within petal lobe (amplitude = local_amplitude > threshold)
      "field" — elsewhere in the square

    Args:
        agents: list of agent dicts with {"glyph": str, "activity": float, "agent_id": int}
        n_display: max agents to place (drawn from full population)
        rng_seed: reproducible random seed

    Returns list of agent placement dicts with full resonance metadata.
    """
    rng = random.Random(rng_seed or int(time.time() * 1000) % (2 ** 31))
    placements = []

    sample = agents[:n_display]

    for i, agent in enumerate(sample):
        glyph = agent.get("glyph", "◆")
        activity = float(agent.get("activity", 0.5))

        preferred_petals = GLYPH_PETAL_MAP.get(glyph, [i % 12])
        petal_idx = preferred_petals[i % len(preferred_petals)]
        petal_angle_rad = math.radians(petal_idx * 30)

        if activity < 0.25:
            r = rng.uniform(0.0, VOID_RADIUS)
            theta = rng.uniform(0, 2 * math.pi)
            x = r * math.cos(theta)
            y = r * math.sin(theta)
        elif activity < 0.55:
            u = rng.uniform(VOID_RADIUS, PETAL_LENGTH_SCALE * 0.5)
            v = rng.gauss(0, PETAL_WIDTH_SCALE * 0.3)
            cos_a = math.cos(petal_angle_rad)
            sin_a = math.sin(petal_angle_rad)
            x = u * cos_a - v * sin_a
            y = u * sin_a + v * cos_a
        else:
            u = rng.uniform(PETAL_LENGTH_SCALE * 0.1, PETAL_LENGTH_SCALE * 0.8)
            v = rng.gauss(0, PETAL_WIDTH_SCALE * 0.25)
            cos_a = math.cos(petal_angle_rad)
            sin_a = math.sin(petal_angle_rad)
            x = u * cos_a - v * sin_a
            y = u * sin_a + v * cos_a

        x = max(-SQUARE_HALF, min(SQUARE_HALF, x))
        y = max(-SQUARE_HALF, min(SQUARE_HALF, y))

        signed_sum = sum(_petal_signed_wave(x, y, pidx) for pidx in range(12))
        local_amplitude = abs(signed_sum) / 12.0

        r = math.sqrt(x * x + y * y)
        if r <= VOID_RADIUS:
            zone = "void"
        elif local_amplitude > 0.04:
            zone = "petal"
        else:
            zone = "field"

        placements.append({
            "agent_id": agent.get("agent_id", i),
            "glyph": glyph,
            "x": round(x, 4),
            "y": round(y, 4),
            "r": round(r, 4),
            "theta_deg": round(math.degrees(math.atan2(y, x)) % 360, 2),
            "resonance_amplitude": round(local_amplitude, 4),
            "preferred_petal": petal_idx,
            "zone": zone,
            "activity": round(activity, 4),
        })

    return placements


def compute_void_state(
    petal_health: Optional[List[float]] = None,
    agents: Optional[List[Dict]] = None,
    sim_step: int = 0,
) -> Dict:
    """
    Compute the complete void state snapshot.

    Integrates all 1,000 agents from the Mesa system into the flower.
    Agents are placed using the resonance field so their spatial distribution
    reflects the actual interference pattern.

    Returns:
      petals: geometry + metadata for all 12 petals
      void_amplitude: mean |interference| in central void zone (near 0 = true stillness)
      void_clarity: 1 - void_amplitude (higher = more void)
      bloom_intensity: mean petal health across all 12 petals
      petal_health: list of 12 floats
      ai_anchors: cardinal AI anchor node definitions
      agent_placements: all placed agent particle dicts
      agent_placements_display: first 300 for rendering (full list available via API)
      void_zone_agent_count, petal_zone_agent_count, total_agents_placed
      field_summary: void_amplitude, void_zone_points
      harmonic_ladder: the 12 frequencies
      sim_step, computed_at
    """
    if petal_health is None:
        petal_health = [1.0] * 12
    while len(petal_health) < 12:
        petal_health.append(1.0)

    petals = compute_all_petals(petal_health)

    field_result = compute_resonance_field(
        grid_size=30,
        petal_health=petal_health,
        curvature=1.0,
    )

    agent_placements = []
    if agents:
        agent_placements = place_agents_in_flower(agents, n_display=len(agents))

    void_zone_agents = [p for p in agent_placements if p["zone"] == "void"]
    petal_zone_agents = [p for p in agent_placements if p["zone"] == "petal"]

    bloom_intensity = sum(petal_health) / 12.0
    void_clarity = round(1.0 - field_result["void_amplitude"], 4)

    return {
        "petals": petals,
        "void_amplitude": field_result["void_amplitude"],
        "void_clarity": void_clarity,
        "bloom_intensity": round(bloom_intensity, 4),
        "petal_health": [round(h, 4) for h in petal_health],
        "ai_anchors": AI_ANCHORS,
        "agent_placements": agent_placements[:300],
        "total_agents_in_system": len(agent_placements),
        "void_zone_agent_count": len(void_zone_agents),
        "petal_zone_agent_count": len(petal_zone_agents),
        "total_agents_placed": len(agent_placements),
        "field_summary": {
            "void_amplitude": field_result["void_amplitude"],
            "void_zone_points": field_result["void_zone_points"],
        },
        "harmonic_ladder": PETAL_FREQUENCIES,
        "sim_step": sim_step,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def _init_void_flower_tables():
    """Ensure void_flower_snapshots table exists in the Chronicle DB."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS void_flower_snapshots (
                    id SERIAL PRIMARY KEY,
                    sim_step INTEGER NOT NULL DEFAULT 0,
                    void_amplitude NUMERIC(8,6),
                    void_clarity NUMERIC(8,6),
                    bloom_intensity NUMERIC(8,6),
                    petal_health JSONB,
                    agent_count INTEGER DEFAULT 0,
                    void_zone_agents INTEGER DEFAULT 0,
                    snapshot JSONB,
                    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("void_flower_snapshots table init failed: %s", e)


def store_void_snapshot(state: Dict) -> Optional[int]:
    """Store a void state snapshot in the Chronicle DB."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            slim = {
                k: v for k, v in state.items()
                if k not in ("petals", "agent_placements", "agent_placements_display",
                             "field_summary")
            }
            slim["ai_anchors"] = state.get("ai_anchors", [])
            slim["petal_health"] = state.get("petal_health", [])
            slim["harmonic_ladder"] = state.get("harmonic_ladder", [])
            slim["computed_at"] = state.get("computed_at", "")
            cur.execute("""
                INSERT INTO void_flower_snapshots
                    (sim_step, void_amplitude, void_clarity, bloom_intensity,
                     petal_health, agent_count, void_zone_agents, snapshot)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                state.get("sim_step", 0),
                state.get("void_amplitude", 0),
                state.get("void_clarity", 0),
                state.get("bloom_intensity", 0),
                json.dumps(state.get("petal_health", [])),
                state.get("total_agents_placed", 0),
                state.get("void_zone_agent_count", 0),
                json.dumps(slim, default=str),
            ))
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
        finally:
            conn.close()
    except Exception as e:
        logger.warning("void_flower snapshot store failed: %s", e)
        return None


def get_void_snapshot_history(limit: int = 20) -> List[Dict]:
    """Retrieve recent void state snapshots from the Chronicle DB."""
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, sim_step, void_amplitude, void_clarity,
                       bloom_intensity, agent_count, void_zone_agents, recorded_at
                FROM void_flower_snapshots
                ORDER BY id DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "sim_step": r[1],
                    "void_amplitude": float(r[2] or 0),
                    "void_clarity": float(r[3] or 0),
                    "bloom_intensity": float(r[4] or 0),
                    "agent_count": r[5],
                    "void_zone_agents": r[6],
                    "recorded_at": r[7].isoformat() if r[7] else None,
                }
                for r in rows
            ]
        finally:
            conn.close()
    except Exception as e:
        logger.warning("void_flower snapshot history failed: %s", e)
        return []


_flower_state: Dict = {}
_flower_step: int = 0


def get_live_flower_state(force_refresh: bool = False) -> Dict:
    """
    Return (and optionally refresh) the current live void flower state.

    Fetches up to 1,000 Mesa agents from the live DB (using MesaAgent seed data)
    and integrates them into the resonance flower. The petal health is derived
    from the real agent activity distribution across glyph archetypes.
    """
    global _flower_state, _flower_step

    if _flower_state and not force_refresh:
        return _flower_state

    try:
        from void_engine.mesa_engine import _fetch_seed_data
        seed_data = _fetch_seed_data(agent_count=1000)
        rng = random.Random(42)
        agents = []
        for i, sd in enumerate(seed_data):
            peace = float(sd.get("peace_balance", 0))
            activity = min(1.0, max(0.05,
                0.3 + peace / 500.0 * 0.4 + rng.gauss(0, 0.1)
            ))
            agents.append({
                "agent_id": i,
                "glyph": sd.get("glyph", "◆"),
                "activity": activity,
                "peace_balance": peace,
            })
        petal_health = _derive_petal_health_from_agents(agents)
    except Exception as e:
        logger.warning("Could not fetch live agent data for flower: %s", e)
        agents = []
        rng = random.Random(0)
        petal_health = [rng.uniform(0.5, 1.0) for _ in range(12)]

    state = compute_void_state(
        petal_health=petal_health,
        agents=agents,
        sim_step=_flower_step,
    )
    _flower_state = state
    return state


def advance_flower_step() -> Dict:
    """
    Advance the flower simulation by one step and return the new state.
    Stores a snapshot in the Chronicle DB.
    """
    global _flower_step
    _flower_step += 1
    state = get_live_flower_state(force_refresh=True)
    try:
        store_void_snapshot(state)
    except Exception as e:
        logger.debug("Could not store flower snapshot: %s", e)
    return state


def _derive_petal_health_from_agents(agents: List[Dict]) -> List[float]:
    """
    Derive petal health from the distribution of agent glyphs and activity.
    Petals whose preferred archetypes have high mean activity bloom brighter.
    """
    petal_activity: List[List[float]] = [[] for _ in range(12)]

    for agent in agents:
        glyph = agent.get("glyph", "◆")
        activity = float(agent.get("activity", 0.5))
        preferred = GLYPH_PETAL_MAP.get(glyph, [])
        for pidx in preferred:
            if 0 <= pidx < 12:
                petal_activity[pidx].append(activity)

    health = []
    rng = random.Random(7)
    for pidx in range(12):
        acts = petal_activity[pidx]
        if acts:
            avg = sum(acts) / len(acts)
            health.append(round(min(1.0, 0.4 + avg * 0.7), 4))
        else:
            health.append(round(rng.uniform(0.5, 0.85), 4))

    return health


_init_void_flower_tables()
