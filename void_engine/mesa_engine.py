"""
Mesa Village Swarm Intelligence Engine — PROJECT VOID

1,000 sovereign agents with independent personalities derived from Adriana SCL glyphs,
long-term per-agent memory, social interaction graph, and temporal memory updates per round.

Agents are seeded from real VOID data:
  - PEACE token balances (via vortex_ledger)
  - Blueprint token holdings
  - GriDul community membership
  - Environmental / activity readings

ReportAgent summarises each simulation run.
Runs are stored in the Chronicle DB for auditability.

Adriana Intelligence Reports (Task #49):
  - Each claimed agent generates a periodic intelligence report in Adriana glyph-language
  - NFT holders can view the raw glyph report for free
  - Plain-English translation costs PEACE tokens (TRANSLATION_FEE_PEACE)
  - Translations are stored and re-served without re-charging
"""

import hashlib
import json
import logging
import random
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ARCHETYPE_MAP = {
    "σ": {"role": "ledger",      "trait": "accumulates",  "bias": "hoarding"},
    "◆": {"role": "core",        "trait": "stabilises",   "bias": "anchoring"},
    "α": {"role": "genesis",     "trait": "seeds",        "bias": "growth"},
    "Ψ": {"role": "sovereign",   "trait": "governs",      "bias": "leadership"},
    "φ": {"role": "spiral",      "trait": "distributes",  "bias": "expansion"},
    "ν": {"role": "node",        "trait": "relays",       "bias": "networking"},
    "τ": {"role": "temporal",    "trait": "times",        "bias": "patience"},
    "ξ": {"role": "scatter",     "trait": "disperses",    "bias": "volatility"},
    "Φ": {"role": "harmonic",    "trait": "harmonises",   "bias": "balance"},
    "🔮": {"role": "oracle",     "trait": "predicts",     "bias": "foresight"},
    "⚡": {"role": "igniter",    "trait": "sparks",       "bias": "urgency"},
    "ψ": {"role": "breath",      "trait": "resonates",    "bias": "empathy"},
    "δ": {"role": "transform",   "trait": "changes",      "bias": "adaptation"},
    "ω": {"role": "finality",    "trait": "closes",       "bias": "conservation"},
    "η": {"role": "flow",        "trait": "flows",        "bias": "liquidity"},
    "🪳": {"role": "cockroach",   "trait": "survives",     "bias": "resilience"},
}

GLYPH_LIST = list(ARCHETYPE_MAP.keys())


def _assign_archetype(user_id: int, seed_extra: str = "") -> str:
    digest = hashlib.sha256(f"{user_id}{seed_extra}".encode()).hexdigest()
    idx = int(digest[:4], 16) % len(GLYPH_LIST)
    return GLYPH_LIST[idx]


def _init_mesa_tables():
    """Ensure mesa simulation tables exist."""
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mesa_simulation_runs (
                id SERIAL PRIMARY KEY,
                run_id TEXT NOT NULL UNIQUE,
                agent_count INTEGER NOT NULL,
                rounds INTEGER NOT NULL,
                seed_event TEXT,
                started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMPTZ,
                status TEXT NOT NULL DEFAULT 'running',
                report JSONB,
                metadata JSONB
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mesa_agent_states (
                id SERIAL PRIMARY KEY,
                run_id TEXT NOT NULL,
                agent_id INTEGER NOT NULL,
                user_id INTEGER,
                glyph TEXT NOT NULL,
                archetype TEXT NOT NULL,
                peace_balance NUMERIC NOT NULL DEFAULT 0,
                blueprint_count INTEGER NOT NULL DEFAULT 0,
                in_gridul BOOLEAN NOT NULL DEFAULT FALSE,
                social_links JSONB,
                memory JSONB,
                final_state JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()
    except Exception as e:
        logger.error("mesa_tables init failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def _fetch_seed_data(agent_count: int) -> List[Dict]:
    """
    Pull real VOID data to generate authentic agent starting states.
    Falls back to synthetic data if DB unavailable.
    """
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    u.id,
                    COALESCE(SUM(CASE WHEN vl.to_user_id = u.id THEN vl.amount ELSE 0 END)
                           - SUM(CASE WHEN vl.from_user_id = u.id THEN vl.amount ELSE 0 END), 0) AS peace_balance,
                    COUNT(DISTINCT bt.id) AS blueprint_count,
                    BOOL_OR(gms.user_id IS NOT NULL) AS in_gridul
                FROM users u
                LEFT JOIN vortex_ledger vl ON (vl.to_user_id = u.id OR vl.from_user_id = u.id)
                LEFT JOIN blueprint_tokens bt ON bt.minted_by = u.id
                LEFT JOIN gridul_move_sessions gms ON gms.user_id = u.id
                GROUP BY u.id
                ORDER BY peace_balance DESC
                LIMIT %s
            """, (agent_count,))
            rows = cur.fetchall()

            agents = []
            for i, row in enumerate(rows):
                uid, peace_bal, bp_count, in_gridul = row
                glyph = _assign_archetype(uid)
                agents.append({
                    "user_id": uid,
                    "glyph": glyph,
                    "archetype": ARCHETYPE_MAP[glyph],
                    "peace_balance": float(peace_bal),
                    "blueprint_count": int(bp_count),
                    "in_gridul": bool(in_gridul),
                })

            needed = agent_count - len(agents)
            for i in range(needed):
                synthetic_id = -(i + 1)
                glyph = _assign_archetype(synthetic_id, seed_extra="synthetic")
                agents.append({
                    "user_id": None,
                    "glyph": glyph,
                    "archetype": ARCHETYPE_MAP[glyph],
                    "peace_balance": round(random.uniform(0, 100), 2),
                    "blueprint_count": random.randint(0, 3),
                    "in_gridul": random.random() > 0.6,
                })

            return agents[:agent_count]
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Seed data fetch failed (%s), using synthetic agents", e)
        agents = []
        for i in range(agent_count):
            synthetic_id = i + 1
            glyph = _assign_archetype(synthetic_id, seed_extra="fallback")
            agents.append({
                "user_id": None,
                "glyph": glyph,
                "archetype": ARCHETYPE_MAP[glyph],
                "peace_balance": round(random.uniform(0, 200), 2),
                "blueprint_count": random.randint(0, 5),
                "in_gridul": random.random() > 0.5,
            })
        return agents


class MesaAgent:
    """A single sovereign agent with personality, memory, and social links."""

    def __init__(self, agent_id: int, seed_data: Dict, rng: random.Random):
        self.agent_id = agent_id
        self.user_id = seed_data.get("user_id")
        self.glyph = seed_data["glyph"]
        self.archetype = seed_data["archetype"]
        self.peace_balance = seed_data["peace_balance"]
        self.blueprint_count = seed_data["blueprint_count"]
        self.in_gridul = seed_data["in_gridul"]
        self.social_links: List[int] = []
        self.memory: List[Dict] = []
        self.rng = rng

        self.activity = self._initial_activity()
        self.peace_flow_this_round = 0.0
        self.interactions_this_round = 0

    def _initial_activity(self) -> float:
        base = 0.3
        if self.peace_balance > 50:
            base += 0.2
        if self.blueprint_count > 0:
            base += 0.1
        if self.in_gridul:
            base += 0.15
        bias = self.archetype.get("bias", "")
        if bias in ("growth", "expansion", "networking"):
            base += 0.1
        elif bias in ("hoarding", "conservation"):
            base -= 0.05
        return min(1.0, max(0.1, base + self.rng.gauss(0, 0.05)))

    def step(self, all_agents: List["MesaAgent"], round_num: int, seed_event: Optional[str] = None):
        self.interactions_this_round = 0
        self.peace_flow_this_round = 0.0

        delta = self.rng.gauss(0, 0.04)
        bias = self.archetype.get("bias", "")

        if bias == "growth":
            delta += 0.01
        elif bias == "volatility":
            delta += self.rng.gauss(0, 0.06)
        elif bias == "conservation":
            delta -= 0.005
        elif bias == "resilience":
            if self.activity < 0.3:
                delta += 0.04
            elif self.activity > 0.7:
                delta -= 0.01
            delta += abs(delta) * 0.2

        if seed_event:
            delta += 0.03

        floor = 0.15 if bias == "resilience" else 0.05
        self.activity = max(floor, min(1.0, self.activity + delta))

        if self.social_links:
            targets = [a for a in all_agents if a.agent_id in self.social_links]
            for target in targets[:3]:
                self._interact(target, round_num)

        self._update_memory(round_num, seed_event)

    def _interact(self, other: "MesaAgent", round_num: int):
        self.interactions_this_round += 1
        role = self.archetype.get("role", "")

        if role == "ledger":
            transfer = min(self.peace_balance * 0.02, 5.0)
            transfer = max(0, transfer)
            if transfer > 0 and other.peace_balance < self.peace_balance:
                self.peace_balance -= transfer
                other.peace_balance += transfer
                self.peace_flow_this_round += transfer

        elif role == "flow":
            boost = self.activity * 0.02
            other.activity = min(1.0, other.activity + boost)

        elif role == "igniter":
            if self.activity > 0.7:
                other.activity = min(1.0, other.activity + 0.04)

        elif role == "scatter":
            spread = self.peace_balance * 0.01 * self.rng.random()
            if len(self.social_links) > 0:
                share = spread / len(self.social_links)
                self.peace_balance -= spread
                other.peace_balance += share
                self.peace_flow_this_round += share

        elif role in ("sovereign", "core"):
            delta = (self.activity - other.activity) * 0.05
            other.activity = max(0.05, min(1.0, other.activity + delta))

        elif role == "cockroach":
            scavenge = max(0, other.peace_balance * 0.003)
            if scavenge > 0:
                other.peace_balance -= scavenge
                self.peace_balance += scavenge
                self.peace_flow_this_round += scavenge
            if other.activity > self.activity:
                self.activity = min(1.0, self.activity + 0.01)

    def _update_memory(self, round_num: int, seed_event: Optional[str]):
        entry = {
            "round": round_num,
            "activity": round(self.activity, 4),
            "peace_balance": round(self.peace_balance, 2),
            "interactions": self.interactions_this_round,
            "peace_flow": round(self.peace_flow_this_round, 4),
        }
        if seed_event:
            entry["seed_event"] = seed_event
        self.memory.append(entry)
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "glyph": self.glyph,
            "role": self.archetype.get("role"),
            "trait": self.archetype.get("trait"),
            "peace_balance": round(self.peace_balance, 2),
            "blueprint_count": self.blueprint_count,
            "in_gridul": self.in_gridul,
            "activity": round(self.activity, 4),
            "social_links": self.social_links[:5],
            "memory": self.memory,
        }


def _build_social_graph(agents: List[MesaAgent], rng: random.Random):
    """Wire up social links: each agent connects to 3–8 others, weighted by proximity."""
    n = len(agents)
    for agent in agents:
        k = rng.randint(3, min(8, n - 1))
        pool = [a.agent_id for a in agents if a.agent_id != agent.agent_id]
        agent.social_links = rng.sample(pool, min(k, len(pool)))


class ReportAgent:
    """Summarises a simulation run."""

    def generate(self, agents: List[MesaAgent], rounds: int,
                 run_id: str, seed_event: Optional[str] = None) -> Dict:
        total_peace = sum(a.peace_balance for a in agents)
        avg_activity = sum(a.activity for a in agents) / max(len(agents), 1)

        glyph_counts: Dict[str, int] = {}
        role_activity: Dict[str, List[float]] = {}
        for a in agents:
            glyph_counts[a.glyph] = glyph_counts.get(a.glyph, 0) + 1
            role = a.archetype.get("role", "unknown")
            role_activity.setdefault(role, []).append(a.activity)

        dominant_glyph = max(glyph_counts, key=glyph_counts.__getitem__)
        dominant_role = max(role_activity, key=lambda r: sum(role_activity[r]) / max(len(role_activity[r]), 1))

        top_agents = sorted(agents, key=lambda a: a.peace_balance, reverse=True)[:5]
        top_agent_glyphs = [a.glyph for a in top_agents]

        peace_flows = [sum(m.get("peace_flow", 0) for m in a.memory) for a in agents]
        total_flow = sum(peace_flows)
        avg_flow = total_flow / max(len(agents), 1)

        anomalies = []
        for a in agents:
            if a.activity > 0.92:
                anomalies.append({"agent_id": a.agent_id, "glyph": a.glyph, "type": "hyperactive", "activity": round(a.activity, 4)})
            if a.peace_balance > total_peace * 0.15:
                anomalies.append({"agent_id": a.agent_id, "glyph": a.glyph, "type": "wealth_concentration", "peace": round(a.peace_balance, 2)})

        gridul_agents = [a for a in agents if a.in_gridul]
        gridul_activity = sum(a.activity for a in gridul_agents) / max(len(gridul_agents), 1) if gridul_agents else 0

        predictions = self._derive_predictions(avg_activity, avg_flow, total_peace, dominant_role, seed_event)

        return {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "rounds": rounds,
            "agent_count": len(agents),
            "seed_event": seed_event,
            "economy": {
                "total_peace": round(total_peace, 2),
                "avg_peace_per_agent": round(total_peace / max(len(agents), 1), 4),
                "total_peace_flow": round(total_flow, 4),
                "avg_peace_flow_per_agent": round(avg_flow, 4),
            },
            "behaviour": {
                "avg_activity": round(avg_activity, 4),
                "dominant_glyph": dominant_glyph,
                "dominant_role": dominant_role,
                "glyph_distribution": glyph_counts,
                "top_agent_glyphs": top_agent_glyphs,
                "gridul_avg_activity": round(gridul_activity, 4),
                "gridul_agent_count": len(gridul_agents),
            },
            "anomalies": anomalies[:10],
            "predictions": predictions,
        }

    def _derive_predictions(self, avg_activity: float, avg_flow: float,
                            total_peace: float, dominant_role: str,
                            seed_event: Optional[str]) -> List[Dict]:
        preds = []

        if avg_activity > 0.7:
            preds.append({
                "type": "peace_surge",
                "confidence": round(min(0.95, avg_activity), 2),
                "description": "High agent activity predicts increased PEACE token circulation in next round.",
            })
        elif avg_activity < 0.3:
            preds.append({
                "type": "dormancy_risk",
                "confidence": round(min(0.9, 1 - avg_activity), 2),
                "description": "Low aggregate activity signals potential community dormancy. Incentive injection recommended.",
            })

        if dominant_role == "ledger":
            preds.append({
                "type": "wealth_concentration",
                "confidence": 0.75,
                "description": "Ledger-archetype agents dominating — PEACE token concentration likely to increase.",
            })
        elif dominant_role in ("flow", "scatter"):
            preds.append({
                "type": "token_redistribution",
                "confidence": 0.78,
                "description": "Flow/scatter agents active — PEACE tokens redistributing broadly across community.",
            })

        if avg_flow > 2.0:
            preds.append({
                "type": "velocity_high",
                "confidence": 0.82,
                "description": f"PEACE token velocity ({round(avg_flow, 2)} avg/agent/round) above threshold — healthy circulation.",
            })

        if seed_event:
            preds.append({
                "type": "seed_event_amplification",
                "confidence": 0.88,
                "description": f"Injected seed event '{seed_event[:60]}' elevated agent responsiveness this round.",
            })

        return preds


def run_simulation(agent_count: int = 100, rounds: int = 5,
                   seed_event: Optional[str] = None,
                   rng_seed: Optional[int] = None) -> Dict:
    """
    Execute a full Mesa Village simulation round.
    Stores the run in chronicle DB and returns the report.
    """
    _init_mesa_tables()

    run_id = hashlib.sha256(f"{time.time()}{agent_count}{rounds}{seed_event}".encode()).hexdigest()[:16]
    rng = random.Random(rng_seed or int(time.time() * 1000) % (2 ** 31))

    started_at = datetime.now(timezone.utc)
    logger.info("Mesa simulation %s starting: %d agents, %d rounds", run_id, agent_count, rounds)

    _store_run_start(run_id, agent_count, rounds, seed_event, started_at)

    seed_data_list = _fetch_seed_data(agent_count)

    agents = [MesaAgent(i, seed_data_list[i], rng) for i in range(len(seed_data_list))]

    _build_social_graph(agents, rng)

    for round_num in range(1, rounds + 1):
        event = seed_event if round_num == 1 else None
        for agent in agents:
            agent.step(agents, round_num, event)

    reporter = ReportAgent()
    report = reporter.generate(agents, rounds, run_id, seed_event)

    completed_at = datetime.now(timezone.utc)
    _store_run_complete(run_id, report, agents, completed_at)

    try:
        generate_reports_after_simulation(run_id, agents)
    except Exception as _e:
        logger.warning("generate_reports_after_simulation failed (non-fatal): %s", _e)

    logger.info("Mesa simulation %s complete in %.2fs", run_id,
                (completed_at - started_at).total_seconds())

    return {
        "run_id": run_id,
        "agent_count": len(agents),
        "rounds": rounds,
        "status": "complete",
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_s": round((completed_at - started_at).total_seconds(), 3),
        "report": report,
        "agents_sample": [agents[i].to_dict() for i in range(min(20, len(agents)))],
    }


def _store_run_start(run_id: str, agent_count: int, rounds: int,
                     seed_event: Optional[str], started_at: datetime):
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO mesa_simulation_runs
                    (run_id, agent_count, rounds, seed_event, started_at, status)
                VALUES (%s, %s, %s, %s, %s, 'running')
                ON CONFLICT (run_id) DO NOTHING
            """, (run_id, agent_count, rounds, seed_event, started_at))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Could not store mesa run start: %s", e)


def _store_run_complete(run_id: str, report: Dict, agents: List[MesaAgent],
                        completed_at: datetime):
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE mesa_simulation_runs
                SET status = 'complete',
                    completed_at = %s,
                    report = %s
                WHERE run_id = %s
            """, (completed_at, json.dumps(report), run_id))

            for agent in agents:
                cur.execute("""
                    INSERT INTO mesa_agent_states
                        (run_id, agent_id, user_id, glyph, archetype,
                         peace_balance, blueprint_count, in_gridul,
                         social_links, memory, final_state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    run_id,
                    agent.agent_id,
                    agent.user_id,
                    agent.glyph,
                    agent.archetype.get("role"),
                    agent.peace_balance,
                    agent.blueprint_count,
                    agent.in_gridul,
                    json.dumps(agent.social_links),
                    json.dumps(agent.memory),
                    json.dumps(agent.to_dict()),
                ))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Could not store mesa run complete: %s", e)


def get_latest_run() -> Optional[Dict]:
    """Fetch the most recent completed simulation run with its report."""
    from void_engine.db_pool import get_db
    try:
        _init_mesa_tables()
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT run_id, agent_count, rounds, seed_event,
                       started_at, completed_at, status, report, metadata
                FROM mesa_simulation_runs
                WHERE status = 'complete'
                ORDER BY completed_at DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                return None
            run_id, agent_count, rounds, seed_event, started_at, completed_at, status, report, metadata = row
            return {
                "run_id": run_id,
                "agent_count": agent_count,
                "rounds": rounds,
                "seed_event": seed_event,
                "started_at": started_at.isoformat() if started_at else None,
                "completed_at": completed_at.isoformat() if completed_at else None,
                "status": status,
                "report": report,
                "metadata": metadata,
            }
        finally:
            conn.close()
    except Exception as e:
        logger.warning("get_latest_run failed: %s", e)
        return None


def _init_agent_nft_table():
    """Ensure agent_nft_owners table exists with proper constraints."""
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_nft_owners (
                agent_id   INTEGER PRIMARY KEY CHECK (agent_id >= 0 AND agent_id <= 999),
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                username   TEXT NOT NULL,
                claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                nft_token  TEXT NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'agent_nft_owners_user_id_unique'
                ) THEN
                    ALTER TABLE agent_nft_owners
                    ADD CONSTRAINT agent_nft_owners_user_id_unique UNIQUE (user_id);
                END IF;
            END $$;
        """)
        conn.commit()
    except Exception as e:
        logger.error("agent_nft_owners init failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def _nft_token_for(agent_id: int) -> str:
    """Generate a deterministic unique token for an agent NFT slot."""
    return hashlib.sha256(f"void:agent_nft:{agent_id}:sovereign".encode()).hexdigest()[:32]


def get_all_agent_slots(page: int = 1, per_page: int = 100) -> Dict:
    """
    Return paginated list of all 1,000 agent NFT slots with ownership info.
    Each slot has a deterministic glyph derived from its slot index.
    Owner username is live-joined from the users table to avoid stale labels.
    """
    _init_agent_nft_table()
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT o.agent_id, o.user_id,
                       COALESCE(u.username, o.username) AS username,
                       o.claimed_at
                FROM agent_nft_owners o
                LEFT JOIN users u ON u.id = o.user_id
            """)
            rows = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("get_all_agent_slots db error: %s", e)
        rows = []

    owners_by_id = {}
    for agent_id, user_id, username, claimed_at in rows:
        owners_by_id[agent_id] = {
            "user_id": user_id,
            "username": username,
            "claimed_at": claimed_at.isoformat() if claimed_at else None,
        }

    total = 1000
    offset = (page - 1) * per_page
    slots = []
    for i in range(offset, min(offset + per_page, total)):
        glyph = _assign_archetype(i, seed_extra="nft_slot")
        archetype = ARCHETYPE_MAP[glyph]
        owner = owners_by_id.get(i)
        slots.append({
            "agent_id": i,
            "glyph": glyph,
            "role": archetype["role"],
            "trait": archetype["trait"],
            "bias": archetype["bias"],
            "nft_token": _nft_token_for(i),
            "claimed": owner is not None,
            "owner": owner,
        })

    total_claimed = len(owners_by_id)
    return {
        "slots": slots,
        "total": total,
        "total_claimed": total_claimed,
        "total_unclaimed": total - total_claimed,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


def get_user_owned_agent(user_id: int) -> Optional[Dict]:
    """Return the agent slot owned by this user, or None."""
    _init_agent_nft_table()
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT agent_id, claimed_at, nft_token FROM agent_nft_owners WHERE user_id = %s",
                (user_id,)
            )
            row = cur.fetchone()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("get_user_owned_agent failed: %s", e)
        return None

    if not row:
        return None

    agent_id, claimed_at, nft_token = row
    glyph = _assign_archetype(agent_id, seed_extra="nft_slot")
    archetype = ARCHETYPE_MAP[glyph]
    return {
        "agent_id": agent_id,
        "glyph": glyph,
        "role": archetype["role"],
        "trait": archetype["trait"],
        "bias": archetype["bias"],
        "nft_token": nft_token,
        "claimed_at": claimed_at.isoformat() if claimed_at else None,
    }


def get_agent_slot(agent_id: int) -> Optional[Dict]:
    """Return full info for a specific agent NFT slot.
    Owner username is live-joined from users to avoid stale labels."""
    if agent_id < 0 or agent_id > 999:
        return None
    _init_agent_nft_table()
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT o.user_id,
                       COALESCE(u.username, o.username) AS username,
                       o.claimed_at, o.nft_token
                FROM agent_nft_owners o
                LEFT JOIN users u ON u.id = o.user_id
                WHERE o.agent_id = %s
            """, (agent_id,))
            row = cur.fetchone()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("get_agent_slot failed: %s", e)
        row = None

    glyph = _assign_archetype(agent_id, seed_extra="nft_slot")
    archetype = ARCHETYPE_MAP[glyph]
    owner = None
    if row:
        user_id, username, claimed_at, nft_token = row
        owner = {
            "user_id": user_id,
            "username": username,
            "claimed_at": claimed_at.isoformat() if claimed_at else None,
        }
    return {
        "agent_id": agent_id,
        "glyph": glyph,
        "role": archetype["role"],
        "trait": archetype["trait"],
        "bias": archetype["bias"],
        "nft_token": _nft_token_for(agent_id),
        "claimed": owner is not None,
        "owner": owner,
    }


def resolve_user_for_mint(identifier: str) -> Optional[Dict]:
    """
    Resolve a user from the users table by numeric ID or email.
    Returns {"user_id": int, "username": str} or None if not found.
    """
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            identifier = identifier.strip()
            if identifier.isdigit():
                cur.execute(
                    "SELECT id, username FROM users WHERE id = %s",
                    (int(identifier),)
                )
            else:
                cur.execute(
                    "SELECT id, username FROM users WHERE lower(email) = lower(%s)",
                    (identifier,)
                )
            row = cur.fetchone()
            if not row:
                return None
            uid, uname = row
            return {"user_id": uid, "username": uname or f"user_{uid}"}
        finally:
            conn.close()
    except Exception as e:
        logger.warning("resolve_user_for_mint failed: %s", e)
        return None


def mint_agent_nft(agent_id: int, user_id: int, username: str) -> Dict:
    """
    Admin: assign an agent NFT slot to a user.
    user_id and username must be pre-resolved from the users table.
    Returns {"ok": True} or {"ok": False, "error": "..."}
    """
    if agent_id < 0 or agent_id > 999:
        return {"ok": False, "error": "agent_id must be 0–999"}
    _init_agent_nft_table()
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT agent_id FROM agent_nft_owners WHERE agent_id = %s",
                (agent_id,)
            )
            if cur.fetchone():
                return {"ok": False, "error": f"Agent #{agent_id} is already owned"}
            cur.execute(
                "SELECT agent_id FROM agent_nft_owners WHERE user_id = %s",
                (user_id,)
            )
            if cur.fetchone():
                return {"ok": False, "error": "User already owns an agent"}
            cur.execute("""
                INSERT INTO agent_nft_owners (agent_id, user_id, username, nft_token)
                VALUES (%s, %s, %s, %s)
            """, (agent_id, user_id, username, _nft_token_for(agent_id)))
            conn.commit()
            return {"ok": True}
        finally:
            conn.close()
    except Exception as e:
        logger.error("mint_agent_nft failed: %s", e)
        return {"ok": False, "error": str(e)}


def revoke_agent_nft(agent_id: int) -> Dict:
    """Admin: revoke ownership of an agent NFT slot."""
    if agent_id < 0 or agent_id > 999:
        return {"ok": False, "error": "agent_id must be 0–999"}
    _init_agent_nft_table()
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM agent_nft_owners WHERE agent_id = %s", (agent_id,))
            deleted = cur.rowcount
            conn.commit()
            if deleted == 0:
                return {"ok": False, "error": f"Agent #{agent_id} has no owner to revoke"}
            return {"ok": True}
        finally:
            conn.close()
    except Exception as e:
        logger.error("revoke_agent_nft failed: %s", e)
        return {"ok": False, "error": str(e)}


def get_run_history(limit: int = 10) -> List[Dict]:
    """Fetch recent simulation run summaries."""
    from void_engine.db_pool import get_db
    try:
        _init_mesa_tables()
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT run_id, agent_count, rounds, seed_event,
                       started_at, completed_at, status
                FROM mesa_simulation_runs
                ORDER BY started_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            result = []
            for row in rows:
                run_id, agent_count, rounds, seed_event, started_at, completed_at, status = row
                result.append({
                    "run_id": run_id,
                    "agent_count": agent_count,
                    "rounds": rounds,
                    "seed_event": seed_event,
                    "started_at": started_at.isoformat() if started_at else None,
                    "completed_at": completed_at.isoformat() if completed_at else None,
                    "status": status,
                })
            return result
        finally:
            conn.close()
    except Exception as e:
        logger.warning("get_run_history failed: %s", e)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Adriana Agent Intelligence Reports — Task #49
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_TRANSLATION_FEE = Decimal("5.00")

_REPORT_SEPARATORS = ["-", "·", "—", "~", "::"]

_ENGLISH_TEMPLATES_BY_ROLE = {
    "ledger": [
        (
            "Your agent has been cataloguing resource movements across the swarm. "
            "{interactions} micro-transfers were logged this cycle; PEACE balance holds at {peace:.2f}. "
            "The ledger remains balanced. Watch for accumulation pressure if activity ({activity:.0%}) climbs further."
        ),
        (
            "Sovereign ledger report: steady accumulation at {peace:.2f} PEACE. "
            "Agent activity was {activity:.0%} this round — {interactions} interactions recorded. "
            "Three wealth-concentration events were neutralised by flow agents. Anticipate moderate token velocity ahead."
        ),
    ],
    "core": [
        (
            "Stability anchors holding. Agent absorbed resonance variance across {interactions} active links "
            "and re-emitted a calibrated signal at {activity:.0%} activity. PEACE reserve: {peace:.2f}. "
            "No structural drift detected — core pulse is strong."
        ),
        (
            "Your agent stabilised {interactions} destabilisation attempts from scatter-archetype neighbours. "
            "Harmonic convergence at {activity:.0%}. PEACE balance: {peace:.2f}. The mesh remains coherent."
        ),
    ],
    "genesis": [
        (
            "Seed conditions are fertile. Your agent catalysed growth in {interactions} emergent clusters "
            "at {activity:.0%} activity. PEACE reserve: {peace:.2f}. Blueprint token activity is trending upward."
        ),
        (
            "Your agent seeded a micro-coalition this cycle — {interactions} nodes activated. "
            "Early-stage network effects are compounding at {activity:.0%} engagement. "
            "PEACE balance: {peace:.2f}. Expect an activity surge within two rounds."
        ),
    ],
    "sovereign": [
        (
            "Governance signals propagating through {interactions} relay nodes. "
            "Agent activity: {activity:.0%}. PEACE balance: {peace:.2f}. "
            "Two directives adopted by the swarm consensus layer. Dissent index: low."
        ),
        (
            "Sovereign influence exerted across {interactions} subordinate nodes at {activity:.0%} intensity. "
            "PEACE: {peace:.2f}. Stability coefficient: 0.91. Agents are responding."
        ),
    ],
    "spiral": [
        (
            "Expansion pressure building in the outer rings. Your agent distributed PEACE across {interactions} zones "
            "at {activity:.0%} activity. Reserve: {peace:.2f}. The spiral is widening — new territory mapped."
        ),
        (
            "Distribution arc traced across {interactions} zones at {activity:.0%} engagement. "
            "PEACE balance: {peace:.2f}. Peripheral coverage increased; core density decreased slightly. On schedule."
        ),
    ],
    "node": [
        (
            "Relay traffic elevated. Your agent forwarded packets across {interactions} links "
            "at {activity:.0%} efficiency. PEACE reserve: {peace:.2f}. "
            "Dead-end routes flagged for rerouting — mesh integrity holding."
        ),
        (
            "Networking activity peaked this cycle. Your agent brokered {interactions} cross-cluster connections "
            "at {activity:.0%} load. PEACE: {peace:.2f}. Information flow increased by 34%."
        ),
    ],
    "temporal": [
        (
            "Time-weighted analysis of {interactions} rounds shows stable oscillation. "
            "Agent activity: {activity:.0%}. PEACE balance: {peace:.2f}. "
            "One anomalous timing event flagged — 2.3σ spike. No action required yet."
        ),
        (
            "Your agent has been tracking long-cycle patterns. {interactions} interactions logged. "
            "Activity: {activity:.0%}. PEACE: {peace:.2f}. "
            "A convergence window opens soon — position resources accordingly."
        ),
    ],
    "scatter": [
        (
            "Dispersal complete. Your agent scattered PEACE across {interactions} non-contiguous zones "
            "at {activity:.0%} volatility. Reserve: {peace:.2f}. "
            "Entropy is serving its purpose — the scatter pattern is operating as designed."
        ),
        (
            "Your agent seeded chaos into {interactions} over-consolidated zones at {activity:.0%} intensity. "
            "PEACE reserve: {peace:.2f}. A liquidity cascade followed. Volatility remains intentional."
        ),
    ],
    "harmonic": [
        (
            "Harmonic coherence report: swarm at {activity:.0%} synchrony. "
            "Your agent dampened interference across {interactions} links. PEACE: {peace:.2f}. The mesh is singing."
        ),
        (
            "Dissonance cluster detected and neutralised — {interactions} corrective interactions at {activity:.0%}. "
            "PEACE balance: {peace:.2f}. Dominant frequency stabilised. Balance is restored."
        ),
    ],
    "oracle": [
        (
            "Predictive scan complete. Your agent identified {interactions} high-probability convergence events "
            "at {activity:.0%} foresight accuracy. PEACE reserve: {peace:.2f}. "
            "PEACE token velocity spike predicted — confidence 83%. Gridul activation cluster: 71%."
        ),
        (
            "The oracle signal is clear. {interactions} dormant agents are about to reactivate — "
            "flagged before they were visible to the swarm. PEACE: {peace:.2f}. Activity: {activity:.0%}. Position accordingly."
        ),
    ],
    "igniter": [
        (
            "Spark delivered. Your agent triggered activation in {interactions} dormant nodes "
            "at {activity:.0%} urgency. PEACE: {peace:.2f}. The urgency signal propagated. Fire is spreading."
        ),
        (
            "Stagnation pocket detected. Your agent deployed an ignition pulse — {interactions} agents responded "
            "at {activity:.0%} activity. PEACE reserve: {peace:.2f}. The swarm is alive again."
        ),
    ],
    "breath": [
        (
            "Resonance check: the swarm is breathing. Your agent synchronised with {interactions} empathy-adjacent nodes "
            "at {activity:.0%} coherence. PEACE: {peace:.2f}. Emotional coherence at its highest this epoch."
        ),
        (
            "Your agent absorbed distress signals from {interactions} over-extended nodes and redistributed calm. "
            "Activity: {activity:.0%}. PEACE: {peace:.2f}. The breath is even. The swarm is holding together."
        ),
    ],
    "transform": [
        (
            "Transformation event logged. Your agent facilitated structural shifts across {interactions} cluster links "
            "at {activity:.0%} intensity. PEACE: {peace:.2f}. Four hoarding-bias nodes converted to flow-bias."
        ),
        (
            "Instability shock absorbed and re-emitted as directed change signal. {interactions} agents updated "
            "behaviour parameters at {activity:.0%} responsiveness. PEACE reserve: {peace:.2f}. Adaptation index: 0.88."
        ),
    ],
    "finality": [
        (
            "Conservation mode active. Your agent consolidated {interactions} over-extended positions "
            "at {activity:.0%} efficiency. PEACE: {peace:.2f}. Leaking allocation channels sealed. Epoch ending cleanly."
        ),
        (
            "Closure signal issued to {interactions} expiring micro-coalitions. Activity: {activity:.0%}. "
            "PEACE reserve: {peace:.2f}. Resources recovered and redistributed to reserve pool. Cycle closes in balance."
        ),
    ],
    "flow": [
        (
            "Flow is optimal. Your agent maintained continuous PEACE circulation through {interactions} nodes "
            "at {activity:.0%} throughput. Reserve: {peace:.2f}. No blockages detected. Liquidity at seasonal high."
        ),
        (
            "Your agent amplified {interactions} lagging flow corridors at {activity:.0%} velocity. "
            "PEACE balance: {peace:.2f}. Token velocity is climbing. The current is running true."
        ),
    ],
}


def _init_adriana_report_tables():
    """Ensure agent intelligence report tables and void_config table exist."""
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_intelligence_reports (
                id           SERIAL PRIMARY KEY,
                agent_id     INTEGER NOT NULL,
                glyph_report TEXT NOT NULL,
                epoch_hour   BIGINT NOT NULL,
                sim_run_id   TEXT,
                generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (agent_id, epoch_hour)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS adriana_translations (
                id           SERIAL PRIMARY KEY,
                agent_id     INTEGER NOT NULL,
                user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                report_id    INTEGER NOT NULL REFERENCES agent_intelligence_reports(id) ON DELETE CASCADE,
                translation  TEXT NOT NULL,
                peace_spent  NUMERIC NOT NULL DEFAULT 5,
                ledger_block INTEGER,
                purchased_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (agent_id, user_id, report_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS void_config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()
    except Exception as e:
        logger.error("adriana_report_tables init failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def get_translation_fee() -> Decimal:
    """Return the admin-configured Adriana translation fee (falls back to default)."""
    _init_adriana_report_tables()
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT value FROM void_config WHERE key = 'adriana_translation_fee'")
            row = cur.fetchone()
            if row:
                return Decimal(row[0]).quantize(Decimal("0.01"))
        finally:
            conn.close()
    except Exception:
        pass
    return _DEFAULT_TRANSLATION_FEE


def set_translation_fee(new_fee: Decimal) -> bool:
    """Admin: persist a new Adriana translation fee to void_config."""
    _init_adriana_report_tables()
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO void_config (key, value, updated_at)
                VALUES ('adriana_translation_fee', %s, NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            """, (str(new_fee.quantize(Decimal("0.01"))),))
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error("set_translation_fee failed: %s", e)
        return False


def _fetch_agent_sim_memory(owner_user_id: int) -> Optional[Dict]:
    """
    Fetch the most recent mesa_agent_states row for this user to extract
    simulation-grounded metrics (activity, peace_balance, interactions).
    Returns None if no simulation data is available.
    """
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT mas.peace_balance, mas.memory, mas.glyph, mas.run_id
                FROM mesa_agent_states mas
                JOIN mesa_simulation_runs msr ON msr.run_id = mas.run_id
                WHERE mas.user_id = %s AND msr.status = 'complete'
                ORDER BY msr.completed_at DESC
                LIMIT 1
            """, (owner_user_id,))
            row = cur.fetchone()
            if not row:
                return None
            peace_balance, memory_json, glyph, run_id = row
            memory = memory_json if isinstance(memory_json, list) else []
            last_round = memory[-1] if memory else {}
            return {
                "peace_balance": float(peace_balance or 0),
                "activity": float(last_round.get("activity", 0.5)),
                "interactions": int(last_round.get("interactions", 0)),
                "peace_flow": float(last_round.get("peace_flow", 0)),
                "run_id": run_id,
            }
        finally:
            conn.close()
    except Exception as e:
        logger.warning("_fetch_agent_sim_memory failed: %s", e)
        return None


def _load_adriana_lexicon_pools():
    """Return (entities, conditions, actions) glyph lists from adriana.lex."""
    try:
        from void_engine.adriana_transpiler import AdrianaLexicon
        lexicon = AdrianaLexicon()
        entities = [e.glyph for e in lexicon.by_category("entity")]
        conditions = [e.glyph for e in lexicon.by_category("condition")]
        actions = [e.glyph for e in lexicon.by_category("action")]
        if entities and conditions:
            return entities, conditions, actions
    except Exception:
        pass
    return list(ARCHETYPE_MAP.keys()), ["📈", "📉", "⚡", "🔮"], []


def _build_glyph_chain_from_round(
    archetype_glyph: str,
    entities: List[str],
    conditions: List[str],
    actions: List[str],
    round_data: Dict,
    round_index: int,
) -> str:
    """
    Map a single simulation round's metrics to a deterministic glyph chain.
    Selections are driven by actual values — activity, peace_flow, interactions.
    """
    activity = float(round_data.get("activity", 0.5))
    interactions = int(round_data.get("interactions", 0))
    peace_flow = float(round_data.get("peace_flow", 0.0))

    n_ent = len(entities)
    n_cond = len(conditions)
    n_act = len(actions) if actions else 0

    entity_idx = int(abs(activity) * 1000 + round_index * 37) % max(n_ent, 1)
    entity = entities[entity_idx] if entities else archetype_glyph

    cond_seed = int(abs(peace_flow) * 100 + interactions * 7 + round_index * 13)
    condition = conditions[cond_seed % n_cond] if conditions else ("📈" if peace_flow >= 0 else "📉")

    if actions:
        act_idx = int(activity * 500 + abs(peace_flow) * 200 + round_index * 17) % n_act
        action = actions[act_idx]
    else:
        action = archetype_glyph

    sep = _REPORT_SEPARATORS[interactions % len(_REPORT_SEPARATORS)]
    return sep.join([archetype_glyph, entity, condition, action])


def _build_glyph_report_from_memory(
    agent_id: int,
    role: str,
    memory: List[Dict],
    epoch_hour: int,
    run_id: Optional[str] = None,
) -> str:
    """
    Build a glyph-chain intelligence report from actual simulation round data.
    Each round in the agent's memory contributes one deterministic chain,
    with glyph selection driven by activity, peace_flow, and interactions metrics.
    Falls back to epoch-seeded random when no memory is available.
    """
    archetype_glyph = _assign_archetype(agent_id, seed_extra="nft_slot")
    entities, conditions, actions = _load_adriana_lexicon_pools()

    rounds = memory[-4:] if len(memory) > 4 else memory

    chains = []
    if rounds:
        for i, round_data in enumerate(rounds):
            chains.append(_build_glyph_chain_from_round(
                archetype_glyph, entities, conditions, actions, round_data, i
            ))
    else:
        seed = f"{agent_id}:{epoch_hour}:{run_id or 'epoch'}"
        rng = random.Random(seed)
        for i in range(4):
            fake_round = {
                "activity": rng.uniform(0.2, 0.9),
                "interactions": rng.randint(0, 8),
                "peace_flow": rng.uniform(-2.0, 5.0),
            }
            chains.append(_build_glyph_chain_from_round(
                archetype_glyph, entities, conditions, actions, fake_round, i
            ))

    branch_sep = [" | ", " ⊕ ", " ↔ "][epoch_hour % 3]
    report_body = branch_sep.join(chains)
    return f"[{agent_id:04d}::{epoch_hour:x}] {report_body}"


def _build_plain_translation(
    role: str,
    rng: random.Random,
    sim_data: Optional[Dict] = None,
) -> str:
    """
    Generate a plain-English translation of the Adriana glyph report.
    Uses simulation-grounded metrics (activity, PEACE balance, interactions)
    if sim_data is available; falls back to plausible defaults otherwise.
    """
    templates = _ENGLISH_TEMPLATES_BY_ROLE.get(role, _ENGLISH_TEMPLATES_BY_ROLE["flow"])
    template = rng.choice(templates)

    if sim_data:
        activity = sim_data.get("activity", 0.5)
        peace = sim_data.get("peace_balance", 50.0)
        interactions = max(1, sim_data.get("interactions", 3))
    else:
        activity = rng.uniform(0.35, 0.85)
        peace = rng.uniform(10.0, 200.0)
        interactions = rng.randint(1, 12)

    try:
        return template.format(
            activity=activity,
            peace=peace,
            interactions=interactions,
        )
    except (KeyError, ValueError):
        return template


def get_or_generate_agent_report(agent_id: int) -> Optional[Dict]:
    """
    Return the latest intelligence report for an agent slot.

    Priority order:
      1. Latest simulation-derived report (sim_run_id IS NOT NULL), most recent first.
      2. Any existing report (fallback from a previous page view).
      3. If nothing exists, generate a synthetic fallback and store it once.
         Synthetic reports are never created on top of an existing simulation report —
         hour rollovers do not trigger regeneration.
    """
    if agent_id < 0 or agent_id > 999:
        return None
    _init_adriana_report_tables()

    glyph = _assign_archetype(agent_id, seed_extra="nft_slot")
    archetype = ARCHETYPE_MAP[glyph]
    role = archetype["role"]

    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, glyph_report, generated_at, sim_run_id, epoch_hour "
                "FROM agent_intelligence_reports "
                "WHERE agent_id = %s "
                "ORDER BY CASE WHEN sim_run_id IS NOT NULL THEN 0 ELSE 1 END, "
                "         generated_at DESC "
                "LIMIT 1",
                (agent_id,)
            )
            row = cur.fetchone()
            if row:
                report_id, glyph_report, generated_at, sim_run_id, epoch_hour = row
                return {
                    "report_id": report_id,
                    "agent_id": agent_id,
                    "glyph": glyph,
                    "role": role,
                    "glyph_report": glyph_report,
                    "epoch_hour": epoch_hour,
                    "sim_run_id": sim_run_id,
                    "generated_at": generated_at.isoformat() if generated_at else None,
                }

            epoch_hour = int(time.time()) // 3600
            glyph_report = _build_glyph_report_from_memory(
                agent_id, role, [], epoch_hour
            )

            cur.execute("""
                INSERT INTO agent_intelligence_reports (agent_id, glyph_report, epoch_hour)
                VALUES (%s, %s, %s)
                ON CONFLICT (agent_id, epoch_hour) DO NOTHING
                RETURNING id, generated_at
            """, (agent_id, glyph_report, epoch_hour))
            inserted = cur.fetchone()
            if not inserted:
                cur.execute(
                    "SELECT id, generated_at FROM agent_intelligence_reports "
                    "WHERE agent_id = %s ORDER BY generated_at DESC LIMIT 1",
                    (agent_id,)
                )
                inserted = cur.fetchone()
            conn.commit()
            report_id, generated_at = inserted
            return {
                "report_id": report_id,
                "agent_id": agent_id,
                "glyph": glyph,
                "role": role,
                "glyph_report": glyph_report,
                "epoch_hour": epoch_hour,
                "sim_run_id": None,
                "generated_at": generated_at.isoformat() if generated_at else None,
            }
        finally:
            conn.close()
    except Exception as e:
        logger.error("get_or_generate_agent_report failed: %s", e)
        return None


def generate_reports_after_simulation(run_id: str, agents: List["MesaAgent"]):
    """
    Called after a simulation completes to persist intelligence reports for
    every agent that ran in this simulation, using their actual round-by-round
    memory for glyph generation.

    Covers all simulated agents (not just NFT owners):
    - Agents whose simulation agent_id matches an NFT slot: stored with real memory.
    - All other simulated agent IDs: also stored with their real sim memory.

    This ensures any NFT slot that participated in the simulation gets a
    simulation-derived report, which `get_or_generate_agent_report` will
    prefer over any synthetic fallback report.

    Best-effort — errors are logged, not raised.
    """
    _init_adriana_report_tables()
    epoch_hour = int(time.time()) // 3600

    for agent in agents:
        try:
            agent_id = agent.agent_id
            if agent_id < 0 or agent_id > 999:
                continue

            glyph = _assign_archetype(agent_id, seed_extra="nft_slot")
            archetype = ARCHETYPE_MAP[glyph]
            role = archetype["role"]

            memory = list(getattr(agent, "memory", []))

            glyph_report = _build_glyph_report_from_memory(
                agent_id, role, memory, epoch_hour, run_id
            )

            from void_engine.db_pool import get_db
            conn = get_db()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO agent_intelligence_reports
                        (agent_id, glyph_report, epoch_hour, sim_run_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (agent_id, epoch_hour) DO UPDATE
                        SET glyph_report = EXCLUDED.glyph_report,
                            sim_run_id = EXCLUDED.sim_run_id
                """, (agent_id, glyph_report, epoch_hour, run_id))
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.warning(
                "generate_reports_after_simulation: agent %s failed: %s",
                getattr(agent, "agent_id", "?"), e
            )


def get_user_translation(agent_id: int, user_id: int, report_id: int) -> Optional[str]:
    """Return a cached translation if the user has already paid for this report."""
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT translation FROM adriana_translations "
                "WHERE agent_id = %s AND user_id = %s AND report_id = %s",
                (agent_id, user_id, report_id)
            )
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    except Exception as e:
        logger.warning("get_user_translation failed: %s", e)
        return None


def purchase_translation(agent_id: int, user_id: int, report_id: int, role: str) -> Dict:
    """
    Atomically debit PEACE tokens and persist the translation in one DB transaction.

    The entire flow — user row lock, balance check, ledger block creation, and
    adriana_translations insert — happens inside a single connection/transaction.
    If any step fails the whole thing rolls back: no charge without unlock.
    Concurrent requests are serialised by the FOR UPDATE lock on the user row.

    Only the NFT owner (user_id == slot.owner.user_id) should be able to call
    this; ownership is enforced at the route level before this function is reached.
    """
    _init_adriana_report_tables()
    fee = get_translation_fee()

    from void_engine.db_pool import get_db
    from void_engine.vortex_wallet import _create_block
    from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT COALESCE(peace_balance, 0) FROM users WHERE id = %s FOR UPDATE",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return {"ok": False, "error": "User not found"}
        balance = Decimal(str(row[0]))

        cur.execute(
            "SELECT translation FROM adriana_translations "
            "WHERE agent_id = %s AND user_id = %s AND report_id = %s",
            (agent_id, user_id, report_id),
        )
        cached = cur.fetchone()
        if cached:
            conn.rollback()
            return {"ok": True, "translation": cached[0], "already_owned": True}

        if balance < fee:
            conn.rollback()
            return {
                "ok": False,
                "error": (
                    f"Insufficient PEACE tokens. You have {float(balance):.2f} PEACE, "
                    f"need {float(fee):.2f}."
                ),
                "required": float(fee),
            }

        cur.execute(
            "UPDATE users SET peace_balance = COALESCE(peace_balance, 0) - %s WHERE id = %s",
            (fee, user_id),
        )

        payload_hash = fatiha_286_hexdigest_from_str(
            f"peace_adriana_{agent_id}_{user_id}_{report_id}"
        )
        block = _create_block(
            cur, "burn_peace_adriana_translation", user_id, None, fee, payload_hash
        )
        ledger_block_index = block.get("block_index")

        sim_data = _fetch_agent_sim_memory(user_id)
        rng = random.Random(f"{agent_id}:{report_id}:{user_id}")
        translation = _build_plain_translation(role, rng, sim_data)

        cur.execute("""
            INSERT INTO adriana_translations
                (agent_id, user_id, report_id, translation, peace_spent, ledger_block)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (agent_id, user_id, report_id) DO NOTHING
        """, (agent_id, user_id, report_id, translation, fee, ledger_block_index))

        conn.commit()
        return {
            "ok": True,
            "translation": translation,
            "peace_spent": float(fee),
            "ledger_block": ledger_block_index,
        }
    except Exception as e:
        conn.rollback()
        logger.error("purchase_translation failed: %s", e)
        return {"ok": False, "error": "Translation purchase failed. Please try again."}
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Inter-holder agent messaging
# ─────────────────────────────────────────────────────────────────────────────

import base64
import hashlib as _hashlib


def _msg_fernet_key() -> bytes:
    """Derive a 32-byte Fernet key from the application session secret.

    Uses PBKDF2-HMAC-SHA256 with a domain-specific salt so the raw secret
    is never used as the key directly. SESSION_SECRET must be set (same
    variable used by the Flask app itself); no insecure fallback is provided.

    **Key rotation warning**: changing SESSION_SECRET renders all existing
    ``plain_content_enc`` values permanently undecryptable.  If SESSION_SECRET
    must be rotated, re-encrypt stored ciphertexts with the old key first, or
    accept that historical message plaintext will be irrecoverable (glyph content
    is always preserved and readable without a key).

    The result is cached per-process so PBKDF2 runs only once regardless of how
    many messages are decrypted in a single request or batch.
    """
    if getattr(_msg_fernet_key, "cache", None) is not None:
        return _msg_fernet_key.cache
    import os
    raw = os.environ.get("SESSION_SECRET", "")
    if not raw:
        raise RuntimeError(
            "SESSION_SECRET environment variable is not set. "
            "Agent message encryption cannot proceed."
        )
    derived = _hashlib.pbkdf2_hmac(
        "sha256",
        raw.encode("utf-8"),
        b"void_adriana_msg_salt_v1",
        iterations=100_000,
        dklen=32,
    )
    key = base64.urlsafe_b64encode(derived)
    _msg_fernet_key.cache = key
    return key


def _msg_encrypt(text: str) -> str:
    """Encrypt plain text with Fernet (AES-128-CBC + HMAC-SHA256).
    Each call produces a unique ciphertext with a random IV.
    Stored value is the Fernet token (URL-safe base64 string).
    """
    from cryptography.fernet import Fernet
    f = Fernet(_msg_fernet_key())
    return f.encrypt(text.encode("utf-8")).decode("ascii")


def _msg_decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet token produced by _msg_encrypt.

    Returns ``[decryption error]`` on ``InvalidToken`` (wrong key, tampered
    ciphertext) or any other crypto failure, and ``[encoding error]`` if the
    result is not valid UTF-8.  All failure branches return a sentinel string
    so callers can safely display the result without additional checks.
    """
    from cryptography.fernet import Fernet, InvalidToken
    try:
        f = Fernet(_msg_fernet_key())
        raw = f.decrypt(ciphertext.encode("ascii"))
    except InvalidToken:
        return "[decryption error]"
    except Exception:
        return "[decryption error]"
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return "[encoding error]"


def _text_to_glyph_chain(text: str) -> str:
    """Encode plain-English message text into an Adriana SCL glyph chain.

    Uses ``AdrianaLexicon`` (the same lexicon object that ``AdrianaTranspiler``
    consumes at runtime) to populate the entity/condition/action symbol pools.
    Words are grouped into 3-word semantic chunks; each chunk is hashed with
    SHA-256 to deterministically select one symbol per category.

    Output format: ``ENTITY-CONDITION-ACTION|…`` (SCL v1.0 pipe-separated
    triplet syntax, parseable by ``AdrianaTranspiler.transpile()``).

    Note: The Adriana transpiler only decodes glyphs→commands; there is no
    canonical inverse (text→glyph) path in the transpiler itself.  This function
    implements that inverse direction by hashing semantic chunks against the live
    lexicon — preserving Adriana's symbol vocabulary while extending the flow to
    human-authored plain-text input.
    """
    entities, conditions, actions = _load_adriana_lexicon_pools()
    words = text.split()
    if not words:
        return "Ω-∅-⏸️"

    chunks = [words[i: i + 3] for i in range(0, min(len(words), 24), 3)]
    triplets = []
    for chunk in chunks:
        h = int(_hashlib.sha256(" ".join(chunk).lower().encode()).hexdigest(), 16)
        entity = entities[h % max(len(entities), 1)] if entities else "Ω"
        cond = conditions[(h >> 8) % max(len(conditions), 1)] if conditions else "≈"
        action = actions[(h >> 16) % max(len(actions), 1)] if actions else "📡"
        triplets.append(f"{entity}-{cond}-{action}")

    return "|".join(triplets)


def _init_message_tables():
    """Create agent_messages and agent_message_translations tables if absent."""
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_messages (
                id SERIAL PRIMARY KEY,
                sender_agent_id INTEGER NOT NULL,
                recipient_agent_id INTEGER NOT NULL,
                sender_user_id INTEGER NOT NULL,
                recipient_user_id INTEGER NOT NULL,
                glyph_content TEXT NOT NULL,
                plain_content_enc TEXT NOT NULL,
                sent_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT chk_no_self_msg CHECK (sender_agent_id != recipient_agent_id)
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_messages_recipient
                ON agent_messages (recipient_agent_id, sent_at DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_messages_sender
                ON agent_messages (sender_agent_id, sent_at DESC)
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_message_translations (
                id SERIAL PRIMARY KEY,
                message_id INTEGER NOT NULL REFERENCES agent_messages(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL,
                unlocked_at TIMESTAMPTZ DEFAULT NOW(),
                peace_spent NUMERIC(16,8) NOT NULL DEFAULT 0,
                ledger_block INTEGER,
                UNIQUE (message_id, user_id)
            )
        """)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("_init_message_tables failed: %s", e)
    finally:
        conn.close()


def get_all_claimed_agents() -> List[Dict]:
    """
    Return all agent slots that have an NFT owner.
    Used to populate the recipient selector in the compose UI.
    """
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT o.agent_id, o.user_id,
                   COALESCE(u.username, o.username) AS username
            FROM agent_nft_owners o
            LEFT JOIN users u ON u.id = o.user_id
            ORDER BY o.agent_id
        """)
        rows = cur.fetchall()
        result = []
        for agent_id, user_id, username in rows:
            glyph = _assign_archetype(agent_id, seed_extra="nft_slot")
            archetype = ARCHETYPE_MAP.get(glyph, {"role": "agent", "trait": "", "bias": ""})
            result.append({
                "agent_id": agent_id,
                "user_id": user_id,
                "username": username,
                "glyph": glyph,
                "role": archetype["role"],
            })
        return result
    except Exception as e:
        logger.error("get_all_claimed_agents failed: %s", e)
        return []
    finally:
        conn.close()


def send_agent_message(
    sender_agent_id: int,
    sender_user_id: int,
    recipient_agent_id: int,
    recipient_user_id: int,
    plain_text: str,
) -> Dict:
    """Send a plain-English message from one agent-holder to another.

    Stores the encrypted plain text (via Fernet) and the Adriana glyph encoding.
    Translation purchases are tracked in ``agent_message_translations`` (one row
    per user per message) rather than a single boolean flag — this supports
    multi-user access auditing and is more extensible than a denormalized flag.
    Returns {"ok": True, "message_id": id} or {"ok": False, "error": ...}.
    """
    _init_message_tables()
    plain_text = plain_text.strip()
    if not plain_text:
        return {"ok": False, "error": "Message cannot be empty."}
    if len(plain_text) > 2000:
        return {"ok": False, "error": "Message too long (max 2000 characters)."}
    if sender_agent_id == recipient_agent_id:
        return {"ok": False, "error": "Cannot message your own agent."}

    glyph_content = _text_to_glyph_chain(plain_text)
    plain_enc = _msg_encrypt(plain_text)

    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO agent_messages
                (sender_agent_id, recipient_agent_id, sender_user_id,
                 recipient_user_id, glyph_content, plain_content_enc)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, sent_at
        """, (sender_agent_id, recipient_agent_id, sender_user_id,
              recipient_user_id, glyph_content, plain_enc))
        row = cur.fetchone()
        conn.commit()
        return {"ok": True, "message_id": row[0], "sent_at": row[1].isoformat()}
    except Exception as e:
        conn.rollback()
        logger.error("send_agent_message failed: %s", e)
        return {"ok": False, "error": "Failed to send message. Please try again."}
    finally:
        conn.close()


def get_inbox_messages(recipient_agent_id: int, viewer_user_id: int) -> List[Dict]:
    """Return received messages for an agent, with translation status for the viewer.

    Filters by both ``recipient_agent_id`` AND ``recipient_user_id`` so that
    if agent ownership is ever transferred, the previous owner's inbox is not
    accessible to the new owner (historical glyph payloads stay private).
    Plain text is only decrypted when the viewer has purchased the translation.
    """
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.sender_agent_id, m.sender_user_id,
                   m.glyph_content, m.plain_content_enc, m.sent_at,
                   t.unlocked_at,
                   COALESCE(o.username, '') AS sender_username
            FROM agent_messages m
            LEFT JOIN agent_message_translations t
                ON t.message_id = m.id AND t.user_id = %s
            LEFT JOIN agent_nft_owners o
                ON o.agent_id = m.sender_agent_id
            WHERE m.recipient_agent_id = %s
              AND m.recipient_user_id = %s
            ORDER BY m.sent_at DESC
            LIMIT 50
        """, (viewer_user_id, recipient_agent_id, viewer_user_id))
        rows = cur.fetchall()
        messages = []
        for row in rows:
            msg_id, s_agent, s_user, glyph, plain_enc, sent_at, unlocked_at, s_uname = row
            s_glyph = _assign_archetype(s_agent, seed_extra="nft_slot")
            s_archetype = ARCHETYPE_MAP.get(s_glyph, {"role": "agent"})
            msg = {
                "message_id": msg_id,
                "sender_agent_id": s_agent,
                "sender_user_id": s_user,
                "sender_glyph": s_glyph,
                "sender_role": s_archetype["role"],
                "sender_username": s_uname or f"Agent #{s_agent}",
                "glyph_content": glyph,
                "sent_at": sent_at.isoformat() if sent_at else None,
                "unlocked": unlocked_at is not None,
                "plain_text": _msg_decrypt(plain_enc) if unlocked_at else None,
            }
            messages.append(msg)
        return messages
    except Exception as e:
        logger.error("get_inbox_messages failed: %s", e)
        return []
    finally:
        conn.close()


def get_sent_messages(sender_agent_id: int, sender_user_id: int) -> List[Dict]:
    """
    Return sent messages for an agent. Senders always see the plain text they wrote.
    """
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.recipient_agent_id, m.glyph_content,
                   m.plain_content_enc, m.sent_at,
                   COALESCE(o.username, '') AS recipient_username
            FROM agent_messages m
            LEFT JOIN agent_nft_owners o ON o.agent_id = m.recipient_agent_id
            WHERE m.sender_agent_id = %s AND m.sender_user_id = %s
            ORDER BY m.sent_at DESC
            LIMIT 50
        """, (sender_agent_id, sender_user_id))
        rows = cur.fetchall()
        messages = []
        for row in rows:
            msg_id, r_agent, glyph, plain_enc, sent_at, r_uname = row
            r_glyph = _assign_archetype(r_agent, seed_extra="nft_slot")
            r_archetype = ARCHETYPE_MAP.get(r_glyph, {"role": "agent"})
            messages.append({
                "message_id": msg_id,
                "recipient_agent_id": r_agent,
                "recipient_glyph": r_glyph,
                "recipient_role": r_archetype["role"],
                "recipient_username": r_uname or f"Agent #{r_agent}",
                "glyph_content": glyph,
                "plain_text": _msg_decrypt(plain_enc),
                "sent_at": sent_at.isoformat() if sent_at else None,
            })
        return messages
    except Exception as e:
        logger.error("get_sent_messages failed: %s", e)
        return []
    finally:
        conn.close()


def purchase_message_translation(message_id: int, user_id: int) -> Dict:
    """
    Spend PEACE tokens to unlock the plain-English translation of a received message.
    Uses the same fee as report translations (get_translation_fee()).
    Atomic: FOR UPDATE lock → idempotency check → balance check → debit → ledger
    block → insert translation record → commit.
    """
    _init_message_tables()
    fee = get_translation_fee()

    from void_engine.db_pool import get_db
    from void_engine.vortex_wallet import _create_block
    from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT COALESCE(peace_balance, 0) FROM users WHERE id = %s FOR UPDATE",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return {"ok": False, "error": "User not found"}
        balance = Decimal(str(row[0]))

        cur.execute(
            "SELECT id FROM agent_message_translations WHERE message_id = %s AND user_id = %s",
            (message_id, user_id),
        )
        if cur.fetchone():
            conn.rollback()
            return {"ok": True, "already_owned": True}

        cur.execute(
            "SELECT plain_content_enc, recipient_user_id FROM agent_messages WHERE id = %s",
            (message_id,),
        )
        msg_row = cur.fetchone()
        if not msg_row:
            conn.rollback()
            return {"ok": False, "error": "Message not found"}
        plain_enc, recipient_user_id = msg_row
        if recipient_user_id != user_id:
            conn.rollback()
            return {"ok": False, "error": "Not your message"}

        if balance < fee:
            conn.rollback()
            return {
                "ok": False,
                "error": (
                    f"Insufficient PEACE tokens. You have {float(balance):.2f} PEACE, "
                    f"need {float(fee):.2f}."
                ),
                "required": float(fee),
            }

        cur.execute(
            "UPDATE users SET peace_balance = COALESCE(peace_balance, 0) - %s WHERE id = %s",
            (fee, user_id),
        )

        payload_hash = fatiha_286_hexdigest_from_str(
            f"peace_adriana_msg_{message_id}_{user_id}"
        )
        block = _create_block(
            cur, "burn_peace_adriana_msg_translation", user_id, None, fee, payload_hash
        )
        ledger_block_index = block.get("block_index")

        cur.execute("""
            INSERT INTO agent_message_translations
                (message_id, user_id, peace_spent, ledger_block)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (message_id, user_id) DO NOTHING
        """, (message_id, user_id, fee, ledger_block_index))

        conn.commit()
        return {
            "ok": True,
            "peace_spent": float(fee),
            "ledger_block": ledger_block_index,
        }
    except Exception as e:
        conn.rollback()
        logger.error("purchase_message_translation failed: %s", e)
        return {"ok": False, "error": "Translation purchase failed. Please try again."}
    finally:
        conn.close()


def get_admin_message_log(limit: int = 100) -> List[Dict]:
    """
    Return message metadata for admin review (no message content).
    Includes sender/recipient agent IDs, timestamps, and whether translated.
    """
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.sender_agent_id, m.recipient_agent_id,
                   m.sent_at,
                   COUNT(t.id) AS translation_count
            FROM agent_messages m
            LEFT JOIN agent_message_translations t ON t.message_id = m.id
            GROUP BY m.id, m.sender_agent_id, m.recipient_agent_id, m.sent_at
            ORDER BY m.sent_at DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        return [
            {
                "message_id": r[0],
                "sender_agent_id": r[1],
                "recipient_agent_id": r[2],
                "sent_at": r[3].isoformat() if r[3] else None,
                "translations_purchased": r[4],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error("get_admin_message_log failed: %s", e)
        return []
    finally:
        conn.close()
