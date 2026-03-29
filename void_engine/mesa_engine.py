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

        if seed_event:
            delta += 0.03

        self.activity = max(0.05, min(1.0, self.activity + delta))

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
        dominant_role = max(role_activity, key=lambda r: sum(role_activity[r]) / len(role_activity[r]))

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

TRANSLATION_FEE_PEACE = Decimal("5.00")

_REPORT_GLYPHS_BY_ROLE = {
    "ledger":    ["σ", "τ", "◆", "θ", "σ", "η"],
    "core":      ["◆", "Φ", "Ψ", "θ", "◆", "📈"],
    "genesis":   ["α", "⚡", "φ", "📈", "α", "δ"],
    "sovereign": ["Ψ", "◆", "σ", "Φ", "Ψ", "τ"],
    "spiral":    ["φ", "η", "α", "📈", "φ", "⚡"],
    "node":      ["ν", "Φ", "η", "τ", "ν", "📉"],
    "temporal":  ["τ", "σ", "◆", "θ↓", "τ", "η"],
    "scatter":   ["ξ", "⚡", "φ", "📉", "ξ", "δ"],
    "harmonic":  ["Φ", "ψ", "◆", "θ", "Φ", "η"],
    "oracle":    ["🔮", "Ψ", "τ", "📈", "🔮", "φ"],
    "igniter":   ["⚡", "α", "δ", "📈", "⚡", "Φ"],
    "breath":    ["ψ", "η", "Φ", "θ↓", "ψ", "◆"],
    "transform": ["δ", "⚡", "α", "📈", "δ", "ξ"],
    "finality":  ["ω", "σ", "τ", "📉", "ω", "◆"],
    "flow":      ["η", "φ", "ψ", "📈", "η", "Φ"],
}

_REPORT_SEPARATORS = ["-", "·", "—", "~", "::"]

_ENGLISH_TEMPLATES = {
    "ledger": [
        "Your agent has been cataloguing resource movements across the swarm. Seventeen micro-transfers were logged this cycle. The ledger remains balanced; no anomalies detected. Watch for accumulation pressure in the northern quadrant.",
        "The sovereign ledger reports steady accumulation. Three wealth-concentration events were neutralised by flow agents. Your agent anticipates moderate PEACE token velocity in the next simulation round.",
    ],
    "core": [
        "Stability anchors are holding. Your agent absorbed resonance variance from twelve active zones and re-emitted a calibrated signal. The core pulse is strong. No structural drift detected.",
        "Your agent stabilised two destabilisation attempts from scatter-archetype neighbours. Harmonic convergence at 84%. The mesh remains coherent under current load.",
    ],
    "genesis": [
        "Three new seed events were introduced to the swarm this cycle. Your agent catalysed growth in two emergent clusters. Blueprint token activity is trending upward — seed conditions are fertile.",
        "Your agent seeded a micro-coalition of five flow nodes. Early-stage network effects are compounding. Expect an activity surge within two simulation rounds.",
    ],
    "sovereign": [
        "Governance signals are propagating through forty-two relay nodes. Your agent issued three leadership directives; two were adopted by the swarm consensus layer. Dissent index: low.",
        "Your agent exerted sovereign influence across the eastern corridor of the mesh. Seven subordinate agents adjusted their activity parameters in response. Stability coefficient: 0.91.",
    ],
    "spiral": [
        "Expansion pressure is building in the outer rings. Your agent distributed twenty-three micro-allocations across the periphery. The spiral is widening — new territory is being mapped.",
        "Your agent traced a distribution arc spanning fourteen zones. Resource density in the core has decreased slightly; peripheral coverage increased by 18%. The expansion is on schedule.",
    ],
    "node": [
        "Relay traffic is elevated. Your agent forwarded eighty-nine packets across the mesh this cycle, with a 97% delivery success rate. Two dead-end routes were flagged for rerouting.",
        "Networking activity peaked at 14:22 UTC. Your agent brokered connections between three previously isolated clusters. Cross-cluster information flow increased by 34%.",
    ],
    "temporal": [
        "Time-weighted analysis of the past six rounds indicates a stable oscillation pattern. Your agent flagged one anomalous timing event — a 2.3-standard-deviation spike in round 4. No action required yet.",
        "Your agent has been tracking long-cycle patterns since the genesis event. A 12-round convergence window opens soon. Position your resources accordingly.",
    ],
    "scatter": [
        "Dispersal complete. Your agent scattered forty-one resource units across nine non-contiguous zones. Volatility remains high — the scatter pattern is intentional and operating as designed.",
        "Your agent seeded chaos into two over-consolidated zones. The dispersal event triggered a liquidity cascade affecting twenty-three downstream agents. Entropy is serving its purpose.",
    ],
    "harmonic": [
        "Harmonic coherence report: the swarm is operating at 79% synchrony. Your agent dampened seven interference patterns and amplified three resonance peaks. The mesh is singing.",
        "Your agent detected a dissonance cluster in the western zone and applied corrective harmonic pressure. Balance is restored. The dominant frequency has shifted to a more stable mode.",
    ],
    "oracle": [
        "Predictive scan complete. Your agent identified two high-probability convergence events in the next simulation round: a PEACE token velocity spike (confidence: 83%) and a gridul activation cluster (confidence: 71%).",
        "The oracle signal is clear. Three dormant agents are about to reactivate — your agent flagged them before they became visible to the swarm. Position accordingly.",
    ],
    "igniter": [
        "Spark delivered. Your agent triggered activation in five dormant nodes this cycle. The urgency signal propagated through eleven relay hops before dissipating. Fire is spreading in the right direction.",
        "Your agent detected a stagnation pocket in the central zone and deployed an ignition pulse. Seven agents responded with elevated activity. The swarm is alive again.",
    ],
    "breath": [
        "Resonance check: the swarm is breathing. Your agent synchronised with twenty-eight empathy-adjacent nodes and amplified the community signal. Emotional coherence is at its highest point this epoch.",
        "Your agent absorbed distress signals from three over-extended nodes and redistributed calm. The breath is even. The swarm is holding together.",
    ],
    "transform": [
        "Transformation event logged. Your agent facilitated a structural shift in one major cluster, converting four hoarding-bias nodes to flow-bias. The swarm is adapting.",
        "Your agent absorbed an instability shock and re-emitted it as a directed change signal. Three agents updated their behaviour parameters in response. Adaptation index: 0.88.",
    ],
    "finality": [
        "Conservation mode active. Your agent consolidated three over-extended resource positions and sealed two leaking allocation channels. The epoch is ending cleanly.",
        "Your agent issued a closure signal to seven expiring micro-coalitions. Resources were recovered and redistributed to the reserve pool. The cycle closes in balance.",
    ],
    "flow": [
        "Flow is optimal. Your agent maintained continuous resource circulation through thirty-one nodes this cycle. No blockages detected. Liquidity is at seasonal high.",
        "Your agent amplified two lagging flow corridors and dissolved one bottleneck near the core. Token velocity is climbing. The current is running true.",
    ],
}


def _generate_glyph_report(agent_id: int, role: str, rng: random.Random) -> str:
    glyphs = _REPORT_GLYPHS_BY_ROLE.get(role, ["◆", "σ", "η", "τ", "φ", "Φ"])
    seps = _REPORT_SEPARATORS
    chains = []
    for _ in range(4):
        length = rng.randint(3, 6)
        chain = rng.sample(glyphs * 2, length)
        sep = rng.choice(seps)
        chains.append(sep.join(chain))
    branch_sep = rng.choice([" | ", " ⊕ ", " ↔ "])
    report = branch_sep.join(chains)
    epoch = int(time.time()) // 3600
    return f"[{agent_id:04d}::{epoch:x}] {report}"


def _generate_plain_translation(role: str, rng: random.Random) -> str:
    templates = _ENGLISH_TEMPLATES.get(role, _ENGLISH_TEMPLATES["flow"])
    return rng.choice(templates)


def _init_adriana_report_tables():
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_intelligence_reports (
                id          SERIAL PRIMARY KEY,
                agent_id    INTEGER NOT NULL,
                glyph_report TEXT NOT NULL,
                epoch_hour  BIGINT NOT NULL,
                generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (agent_id, epoch_hour)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS adriana_translations (
                id          SERIAL PRIMARY KEY,
                agent_id    INTEGER NOT NULL,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                report_id   INTEGER NOT NULL REFERENCES agent_intelligence_reports(id) ON DELETE CASCADE,
                translation TEXT NOT NULL,
                peace_spent NUMERIC NOT NULL DEFAULT 5,
                purchased_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (agent_id, user_id, report_id)
            )
        """)
        conn.commit()
    except Exception as e:
        logger.error("adriana_report_tables init failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def get_or_generate_agent_report(agent_id: int) -> Optional[Dict]:
    """
    Return the current-epoch intelligence report for an agent slot.
    Generates and persists if one doesn't exist for this epoch hour.
    """
    if agent_id < 0 or agent_id > 999:
        return None
    _init_adriana_report_tables()

    glyph = _assign_archetype(agent_id, seed_extra="nft_slot")
    archetype = ARCHETYPE_MAP[glyph]
    role = archetype["role"]
    epoch_hour = int(time.time()) // 3600

    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, glyph_report, generated_at FROM agent_intelligence_reports "
                "WHERE agent_id = %s AND epoch_hour = %s",
                (agent_id, epoch_hour)
            )
            row = cur.fetchone()
            if row:
                report_id, glyph_report, generated_at = row
                return {
                    "report_id": report_id,
                    "agent_id": agent_id,
                    "glyph": glyph,
                    "role": role,
                    "glyph_report": glyph_report,
                    "epoch_hour": epoch_hour,
                    "generated_at": generated_at.isoformat() if generated_at else None,
                }

            rng = random.Random(f"{agent_id}:{epoch_hour}")
            glyph_report = _generate_glyph_report(agent_id, role, rng)

            cur.execute("""
                INSERT INTO agent_intelligence_reports (agent_id, glyph_report, epoch_hour)
                VALUES (%s, %s, %s)
                ON CONFLICT (agent_id, epoch_hour) DO UPDATE SET glyph_report = EXCLUDED.glyph_report
                RETURNING id, generated_at
            """, (agent_id, glyph_report, epoch_hour))
            report_id, generated_at = cur.fetchone()
            conn.commit()
            return {
                "report_id": report_id,
                "agent_id": agent_id,
                "glyph": glyph,
                "role": role,
                "glyph_report": glyph_report,
                "epoch_hour": epoch_hour,
                "generated_at": generated_at.isoformat() if generated_at else None,
            }
        finally:
            conn.close()
    except Exception as e:
        logger.error("get_or_generate_agent_report failed: %s", e)
        return None


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
    Deduct TRANSLATION_FEE_PEACE PEACE tokens from user and store the translation.
    Returns {"ok": True, "translation": "..."} or {"ok": False, "error": "..."}
    """
    _init_adriana_report_tables()
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
            cached = cur.fetchone()
            if cached:
                return {"ok": True, "translation": cached[0], "already_owned": True}

            cur.execute(
                "SELECT COALESCE(vortex_balance, 0) FROM users WHERE id = %s FOR UPDATE",
                (user_id,)
            )
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return {"ok": False, "error": "User not found"}
            balance = Decimal(str(row[0]))
            if balance < TRANSLATION_FEE_PEACE:
                conn.rollback()
                return {
                    "ok": False,
                    "error": f"Insufficient PEACE tokens. You have {float(balance):.2f}, need {float(TRANSLATION_FEE_PEACE):.0f}.",
                    "balance": float(balance),
                    "required": float(TRANSLATION_FEE_PEACE),
                }

            cur.execute(
                "UPDATE users SET vortex_balance = COALESCE(vortex_balance, 0) - %s WHERE id = %s",
                (TRANSLATION_FEE_PEACE, user_id)
            )

            rng = random.Random(f"{agent_id}:{report_id}:{user_id}")
            translation = _generate_plain_translation(role, rng)

            cur.execute("""
                INSERT INTO adriana_translations (agent_id, user_id, report_id, translation, peace_spent)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (agent_id, user_id, report_id) DO NOTHING
            """, (agent_id, user_id, report_id, translation, TRANSLATION_FEE_PEACE))

            conn.commit()
            return {"ok": True, "translation": translation, "peace_spent": float(TRANSLATION_FEE_PEACE)}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error("purchase_translation failed: %s", e)
        return {"ok": False, "error": "Translation purchase failed. Please try again."}
