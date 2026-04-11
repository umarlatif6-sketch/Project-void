"""
VoidVillage Mesa Simulation — Zone Agent Model

Each VOID Plane zone can run a Mesa simulation where agents represent
zone occupants (players with claimed zones), activity nodes, and Adriana
response agents.

A simulation step computes:
  - agent_count: how many agents are active in the zone
  - activity_level: aggregate normalised activity [0–1]
  - resonance_score: composite score derived from activity and VTX flow [0–100]

Compatible with Mesa 3.x (agents auto-register, no mesa.time module required).
"""

import logging
import random
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _run_village_simulation(zone_id: str, owner_activity: float = 0.5,
                             vtx_flow: float = 0.0,
                             seed: Optional[int] = None) -> Dict:
    """
    Run a Mesa 3.x village simulation for a single zone.
    """
    try:
        from mesa import Agent, Model

        rng_seed = seed or (abs(hash(zone_id)) % 2**31)

        class ZoneAgent(Agent):
            def __init__(self, model, agent_type: str, base_activity: float):
                super().__init__(model)
                self.type = agent_type
                self.activity = max(0.0, min(1.0, base_activity + model.rng.gauss(0, 0.08)))

            def step(self):
                delta = self.model.rng.gauss(0, 0.03)
                self.activity = max(0.0, min(1.0, self.activity + delta))
                if self.type == "adriana":
                    others = list(self.model.agents_by_type[ZoneAgent])
                    if others:
                        target = self.model.rng.choice(others)
                        boost = 0.04 * target.activity
                        self.activity = min(1.0, self.activity + boost)
                elif self.type == "cockroach":
                    if self.activity < 0.2:
                        self.activity = min(1.0, self.activity + 0.05)
                    others = list(self.model.agents_by_type[ZoneAgent])
                    if others:
                        weakest = min(others, key=lambda a: a.activity)
                        if weakest.activity < self.activity:
                            self.activity = min(1.0, self.activity + 0.02)
                    self.activity = max(0.12, self.activity)

        class VoidVillageModel(Model):
            def __init__(self, n_agents: int, base_activity: float, rng_seed: int):
                super().__init__(seed=rng_seed)
                self.rng = random.Random(rng_seed)

                n_cockroach = max(1, int(n_agents * 0.1))
                n_adriana = max(1, int(n_agents * 0.2))
                n_nodes = max(1, int(n_agents * 0.25))
                n_players = max(1, n_agents - n_adriana - n_nodes - n_cockroach)

                for _ in range(n_players):
                    ZoneAgent(self, "player", base_activity)
                for _ in range(n_nodes):
                    ZoneAgent(self, "node", base_activity * 0.8)
                for _ in range(n_adriana):
                    ZoneAgent(self, "adriana", base_activity * 1.1)
                for _ in range(n_cockroach):
                    ZoneAgent(self, "cockroach", base_activity * 0.4)

            def step(self):
                self.agents.do("step")

        vtx_norm = min(1.0, vtx_flow / max(vtx_flow + 1.0, 50.0))
        base_act = max(0.1, min(0.9, 0.5 * owner_activity + 0.3 * vtx_norm + 0.2))
        n_agents = max(3, min(20, int(3 + owner_activity * 12 + vtx_norm * 5)))

        model = VoidVillageModel(n_agents, base_act, rng_seed)

        steps = 5
        for _ in range(steps):
            model.step()

        agents = list(model.agents_by_type[ZoneAgent])
        activity_level = sum(a.activity for a in agents) / max(len(agents), 1)

        resonance = min(100.0, max(0.0,
            activity_level * 40.0
            + owner_activity * 30.0
            + vtx_norm * 20.0
            + min(len(agents) / 20.0, 1.0) * 10.0
        ))

        type_counts = {"player": 0, "node": 0, "adriana": 0, "cockroach": 0}
        for a in agents:
            type_counts[a.type] = type_counts.get(a.type, 0) + 1

        return {
            "zone_id": zone_id,
            "agent_count": len(agents),
            "activity_level": round(activity_level, 4),
            "resonance_score": round(resonance, 4),
            "steps_run": steps,
            "agent_types": type_counts,
        }

    except Exception as exc:
        logger.warning("VoidVillage Mesa simulation failed for %s (%s) — using fallback", zone_id, exc)
        return _fallback_simulation(zone_id, owner_activity, vtx_flow)


def _fallback_simulation(zone_id: str, owner_activity: float, vtx_flow: float) -> Dict:
    rng = random.Random(abs(hash(zone_id)) % 2**31)
    n = max(3, int(3 + owner_activity * 8))
    activities = [max(0.0, min(1.0, owner_activity + rng.gauss(0, 0.1))) for _ in range(n)]
    activity_level = sum(activities) / max(len(activities), 1)
    vtx_norm = min(1.0, vtx_flow / 50.0)
    resonance = round(min(100.0, activity_level * 50.0 + vtx_norm * 30.0 + 10.0), 4)
    return {
        "zone_id": zone_id,
        "agent_count": n,
        "activity_level": round(activity_level, 4),
        "resonance_score": resonance,
        "steps_run": 0,
        "agent_types": {"player": n, "node": 0, "adriana": 0},
    }


def simulate_zone(zone_id: str, owner_id: Optional[int] = None) -> Dict:
    """
    Public entry point for /api/village/simulate/<zone_id>.
    Fetches owner activity data from the DB then runs the Mesa model.
    """
    owner_activity = 0.3
    vtx_flow = 0.0

    if owner_id is not None:
        try:
            from void_engine.db_pool import get_db
            from datetime import datetime, timezone, timedelta
            conn = get_db()
            try:
                cur = conn.cursor()
                cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()

                cur.execute("""
                    SELECT COUNT(*) FROM vortex_ledger
                    WHERE (from_user_id = %s OR to_user_id = %s) AND timestamp > %s
                """, (owner_id, owner_id, cutoff))
                row = cur.fetchone()
                vtx_flow = float(row[0]) if row else 0.0

                cur.execute("""
                    SELECT COUNT(*) FROM gridul_move_sessions
                    WHERE user_id = %s AND completed = TRUE AND created_at > %s
                """, (owner_id, cutoff))
                row = cur.fetchone()
                move_count = float(row[0]) if row else 0.0

                owner_activity = min(1.0, (vtx_flow / 50.0) * 0.4 + (move_count / 10.0) * 0.6)
            finally:
                conn.close()
        except Exception as exc:
            logger.debug("VoidVillage DB fetch failed for owner %s: %s", owner_id, exc)

    return _run_village_simulation(zone_id, owner_activity, vtx_flow)
