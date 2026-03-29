"""
Mesa Village Swarm Upgrade — GraphRAG + Seed-to-Agent + Temporal Memory
PROJECT VOID — Mesa Swarm Intelligence Layer

Licence decision (Task #41):
  MiroFish (github.com/666ghj/MiroFish) does not publish a clear OSI-approved
  licence file in its repository. To avoid integrating code under an unknown or
  restrictive licence, the architectural patterns from MiroFish (GraphRAG
  relationship graphs, persona generation from seed text, temporal memory) have
  been re-implemented independently from scratch. The OASIS project
  (github.com/camel-ai/oasis, Apache-2.0) was used as a reference for
  multi-agent social simulation design patterns only; no OASIS source code is
  copied or included here. All code in this module is original PROJECT VOID
  implementation.

Capabilities added:
  - seed_to_agents(text, n_agents)  — parse seed text → N distinct agent personas
  - GraphRAG agent relationship map — weighted directed edges by shared interests
  - Temporal memory                 — each agent accumulates cross-round context
  - simulate_from_seed(text, rounds) — full pipeline returning plain-English summary
  - _init_mesa_simulations_table()  — mesa_simulations table for endpoint results
"""

import hashlib
import json
import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


PERSONALITY_ARCHETYPES = [
    {
        "name": "activist",
        "motivations": ["justice", "collective action", "resistance"],
        "stance": "challenges",
        "interaction_style": "confrontational",
    },
    {
        "name": "analyst",
        "motivations": ["accuracy", "evidence", "systemic patterns"],
        "stance": "examines",
        "interaction_style": "methodical",
    },
    {
        "name": "connector",
        "motivations": ["community", "bridge-building", "shared interest"],
        "stance": "mediates",
        "interaction_style": "empathetic",
    },
    {
        "name": "skeptic",
        "motivations": ["doubt", "verification", "counter-narrative"],
        "stance": "questions",
        "interaction_style": "probing",
    },
    {
        "name": "amplifier",
        "motivations": ["visibility", "spread", "signal boosting"],
        "stance": "distributes",
        "interaction_style": "enthusiastic",
    },
    {
        "name": "conservator",
        "motivations": ["stability", "preservation", "risk avoidance"],
        "stance": "resists change",
        "interaction_style": "cautious",
    },
    {
        "name": "visionary",
        "motivations": ["future", "innovation", "transformation"],
        "stance": "imagines",
        "interaction_style": "expansive",
    },
    {
        "name": "chronicler",
        "motivations": ["memory", "documentation", "narrative"],
        "stance": "records",
        "interaction_style": "reflective",
    },
]


def _extract_themes(text: str) -> List[str]:
    """
    Extract key themes from seed text using simple keyword clustering.
    Returns up to 8 theme tokens that describe the topic space.
    """
    text_lower = text.lower()
    word_freq: Dict[str, int] = {}

    stop_words = {
        "the", "a", "an", "is", "it", "in", "on", "at", "to", "of", "and",
        "or", "but", "for", "with", "that", "this", "was", "are", "be",
        "has", "have", "had", "will", "from", "by", "as", "not", "they",
        "he", "she", "we", "you", "i", "its", "their", "our", "what",
        "which", "who", "been", "were", "more", "also", "than", "so",
        "can", "could", "would", "should", "there", "when", "where",
        "about", "into", "through", "during", "before", "after", "above",
        "below", "between", "each", "further", "then", "once", "here",
        "does", "did", "do", "just", "because", "while", "how", "all",
        "both", "few", "same", "such", "those", "these", "over", "under",
    }

    tokens = re.findall(r"\b[a-z]{4,}\b", text_lower)
    for token in tokens:
        if token not in stop_words:
            word_freq[token] = word_freq.get(token, 0) + 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:8]]


def _extract_entities(text: str) -> List[str]:
    """
    Extract likely named entities (capitalized phrases) from seed text.
    Returns up to 6 entity strings.
    """
    entities = re.findall(r"\b[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,})*\b", text)
    seen = []
    for e in entities:
        if e not in seen and len(e) > 3:
            seen.append(e)
    return seen[:6]


def _extract_tensions(text: str) -> List[str]:
    """
    Detect binary tension pairs from seed text (conflict language).
    Returns tension phrases for seeding opposing viewpoints.
    """
    tension_markers = [
        r"(vs\.?|versus|against|opposed to|conflict|dispute|tension between)",
        r"(crisis|collapse|surge|threat|protest|ban|block|restrict)",
        r"(demand(s)?|call(s)? for|push(es)? for|fight(s)? (for|against))",
    ]
    tensions = []
    for marker in tension_markers:
        matches = re.findall(marker, text, re.IGNORECASE)
        if matches:
            tensions.append(marker.replace(r"(", "").replace(r")", "").split("|")[0].strip("\\"))
    return tensions[:4]


def _llm_generate_personas(
    seed_text: str,
    n_agents: int,
    themes: List[str],
    entities: List[str],
) -> Optional[List[Dict]]:
    """
    Use the model router to generate agent personas from seed text.
    Returns a list of persona dicts or None if LLM call fails.
    """
    try:
        from void_engine.aljabr_transpiler import get_model_router, TASK_BULK
        router = get_model_router()

        prompt = f"""You are a social simulation architect. Given the following seed text, generate {n_agents} distinct agent personas who would naturally care about this topic.

Seed text: {seed_text[:800]}

Key themes detected: {', '.join(themes)}
Key entities: {', '.join(entities) if entities else 'none detected'}

Return a JSON array of {n_agents} objects. Each object must have exactly these keys:
- "name": a plausible fictional name (no real people)
- "archetype": one of: activist, analyst, connector, skeptic, amplifier, conservator, visionary, chronicler
- "viewpoint": a 1-sentence description of this agent's position on the seed topic
- "motivation": what drives their interest (1 short phrase)
- "topic_interests": array of 2-3 strings from the key themes above

Return only valid JSON. No explanation."""

        messages = [
            {"role": "system", "content": "You are a concise JSON generator for social simulations. Output only valid JSON arrays."},
            {"role": "user", "content": prompt},
        ]

        response, model, used_fallback = router.call_with_fallback(
            TASK_BULK, messages, max_completion_tokens=1200, task_label="mesa_persona_generation"
        )

        try:
            usage = response.usage
            if usage:
                tier = TASK_BULK
                router.log_cost(tier, model, usage.prompt_tokens, usage.completion_tokens, "mesa_persona_generation")
        except Exception:
            pass

        raw = response.choices[0].message.content or ""
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
        return None
    except Exception as e:
        logger.warning("LLM persona generation failed: %s", e)
        return None


def seed_to_agents(text: str, n_agents: int = 10) -> List["SwarmAgent"]:
    """
    Parse a seed text (news article, PEACE token event log, GriDul Mesh post,
    or any arbitrary text) and generate N agent personas with:
      - distinct personalities and motivations
      - topic interests derived from the seed
      - relationship edges distributed by shared interest (GraphRAG)
      - temporal memory primed with seed context

    Returns a list of SwarmAgent instances ready for simulation.
    """
    n_agents = max(2, min(50, n_agents))
    themes = _extract_themes(text)
    entities = _extract_entities(text)
    tensions = _extract_tensions(text)

    llm_personas = _llm_generate_personas(text, n_agents, themes, entities)

    rng = random.Random(hashlib.sha256(text.encode()).digest()[0])
    agents: List[SwarmAgent] = []

    for i in range(n_agents):
        if llm_personas and i < len(llm_personas):
            p = llm_personas[i]
            archetype_name = p.get("archetype", "connector")
            archetype = next(
                (a for a in PERSONALITY_ARCHETYPES if a["name"] == archetype_name),
                PERSONALITY_ARCHETYPES[i % len(PERSONALITY_ARCHETYPES)]
            )
            agent = SwarmAgent(
                agent_id=i,
                name=p.get("name", f"Agent-{i}"),
                archetype=archetype,
                viewpoint=p.get("viewpoint", ""),
                motivation=p.get("motivation", archetype["motivations"][0]),
                topic_interests=p.get("topic_interests", themes[:2]),
                rng=rng,
            )
        else:
            archetype = PERSONALITY_ARCHETYPES[i % len(PERSONALITY_ARCHETYPES)]
            agent_themes = [themes[i % len(themes)]] if themes else ["community"]
            if len(themes) > 1:
                agent_themes.append(themes[(i + 1) % len(themes)])

            tension_context = tensions[i % len(tensions)] if tensions else ""
            viewpoint = (
                f"This agent {archetype['stance']} the situation"
                + (f" around {tension_context}" if tension_context else "")
                + f", driven by {archetype['motivations'][0]}."
            )
            agent = SwarmAgent(
                agent_id=i,
                name=f"Agent-{i} ({archetype['name'].title()})",
                archetype=archetype,
                viewpoint=viewpoint,
                motivation=archetype["motivations"][0],
                topic_interests=agent_themes,
                rng=rng,
            )

        agent.prime_memory(text[:300], entities, themes)
        agents.append(agent)

    _build_graphrag_edges(agents, themes)
    return agents


def _build_graphrag_edges(agents: List["SwarmAgent"], themes: List[str]):
    """
    Build a GraphRAG relationship map.
    Edges are weighted by shared topic interests. Agents with more overlap
    receive higher-weight connections. Each agent also gets a small number
    of random weak-tie edges for cross-cluster information flow.
    """
    n = len(agents)
    if n < 2:
        return

    for agent in agents:
        agent.relationship_edges = []

    for i, a in enumerate(agents):
        for j, b in enumerate(agents):
            if i == j:
                continue
            shared = set(a.topic_interests) & set(b.topic_interests)
            if shared:
                weight = round(0.3 + 0.2 * len(shared), 2)
                relationship = "ally" if weight > 0.5 else "colleague"
                a.relationship_edges.append({
                    "target_id": b.agent_id,
                    "weight": weight,
                    "shared_interests": list(shared),
                    "relationship": relationship,
                })

    rng = random.Random(42)
    for agent in agents:
        connected_ids = {e["target_id"] for e in agent.relationship_edges}
        candidates = [a.agent_id for a in agents if a.agent_id != agent.agent_id and a.agent_id not in connected_ids]
        n_weak = min(2, len(candidates))
        if n_weak > 0:
            for tid in rng.sample(candidates, n_weak):
                agent.relationship_edges.append({
                    "target_id": tid,
                    "weight": round(rng.uniform(0.05, 0.15), 2),
                    "shared_interests": [],
                    "relationship": "acquaintance",
                })

    for agent in agents:
        agent.relationship_edges.sort(key=lambda e: e["weight"], reverse=True)
        agent.relationship_edges = agent.relationship_edges[:8]


class SwarmAgent:
    """
    A simulation agent with distinct identity, GraphRAG relationship map,
    and temporal memory that persists across simulation rounds.
    """

    def __init__(
        self,
        agent_id: int,
        name: str,
        archetype: Dict,
        viewpoint: str,
        motivation: str,
        topic_interests: List[str],
        rng: random.Random,
    ):
        self.agent_id = agent_id
        self.name = name
        self.archetype = archetype
        self.viewpoint = viewpoint
        self.motivation = motivation
        self.topic_interests = topic_interests
        self.rng = rng

        self.relationship_edges: List[Dict] = []
        self.temporal_memory: List[Dict] = []

        self.stance_score = rng.uniform(-1.0, 1.0)
        self.influence = rng.uniform(0.1, 0.9)
        self.activity_this_round = 0.0

    def prime_memory(self, seed_excerpt: str, entities: List[str], themes: List[str]):
        """
        Set initial temporal memory from the seed text so round 1 behaviour
        is influenced by the seed context.
        """
        self.temporal_memory.append({
            "round": 0,
            "type": "seed_context",
            "excerpt": seed_excerpt[:200],
            "entities_noted": entities[:3],
            "themes_noted": themes[:3],
            "stance_at_start": round(self.stance_score, 3),
        })

    def step(
        self,
        all_agents: List["SwarmAgent"],
        round_num: int,
        seed_event: Optional[str] = None,
    ):
        """
        Advance one simulation round.
        Agent reads its own temporal memory, interacts with connected agents,
        and updates its stance and memory for this round.
        """
        self.activity_this_round = 0.0

        prior_stance = self.stance_score
        prior_rounds = [m for m in self.temporal_memory if m.get("round", 0) > 0]

        memory_inertia = 0.0
        if prior_rounds:
            last = prior_rounds[-1]
            last_delta = last.get("stance_delta", 0.0)
            memory_inertia = last_delta * 0.3

        stance_delta = self.rng.gauss(0, 0.05) + memory_inertia

        archetype_name = self.archetype.get("name", "connector")
        if archetype_name == "activist":
            stance_delta += 0.02 if self.stance_score < 0 else -0.02
        elif archetype_name == "conservator":
            stance_delta *= 0.5
        elif archetype_name == "amplifier":
            stance_delta *= 1.4

        if seed_event:
            stance_delta += self.rng.gauss(0.03, 0.02)

        connected_agents = [a for a in all_agents if any(e["target_id"] == a.agent_id for e in self.relationship_edges)]
        interaction_log = []

        for edge in self.relationship_edges[:4]:
            target = next((a for a in all_agents if a.agent_id == edge["target_id"]), None)
            if not target:
                continue
            weight = edge["weight"]
            influence_delta = (target.stance_score - self.stance_score) * weight * 0.15

            if archetype_name == "skeptic":
                influence_delta *= -0.5
            elif archetype_name == "connector":
                influence_delta *= 1.2

            stance_delta += influence_delta
            self.activity_this_round += weight

            interaction_log.append({
                "with_agent": target.agent_id,
                "edge_weight": weight,
                "relationship": edge.get("relationship", "peer"),
                "stance_pull": round(influence_delta, 4),
            })

        self.stance_score = max(-1.0, min(1.0, self.stance_score + stance_delta))
        self.activity_this_round = min(1.0, self.activity_this_round)

        memory_entry = {
            "round": round_num,
            "type": "round_result",
            "stance": round(self.stance_score, 4),
            "stance_delta": round(stance_delta, 4),
            "activity": round(self.activity_this_round, 4),
            "interactions": interaction_log[:3],
        }
        if seed_event and round_num == 1:
            memory_entry["seed_event_response"] = self.archetype.get("stance", "notes") + f" the event: {seed_event[:80]}"

        self.temporal_memory.append(memory_entry)

        if len(self.temporal_memory) > 12:
            seed_entries = [m for m in self.temporal_memory if m.get("type") == "seed_context"]
            round_entries = [m for m in self.temporal_memory if m.get("type") == "round_result"]
            self.temporal_memory = seed_entries + round_entries[-10:]

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "archetype": self.archetype.get("name"),
            "viewpoint": self.viewpoint,
            "motivation": self.motivation,
            "topic_interests": self.topic_interests,
            "stance_score": round(self.stance_score, 4),
            "influence": round(self.influence, 4),
            "activity": round(self.activity_this_round, 4),
            "relationship_count": len(self.relationship_edges),
            "strong_relationships": [
                e for e in self.relationship_edges if e.get("weight", 0) > 0.4
            ],
            "temporal_memory": self.temporal_memory,
        }


def _run_swarm_rounds(agents: List[SwarmAgent], rounds: int, seed_event: Optional[str] = None):
    """Step all agents through N rounds of simulation."""
    for round_num in range(1, rounds + 1):
        event = seed_event if round_num == 1 else None
        for agent in agents:
            agent.step(agents, round_num, event)


def _build_plain_english_summary(
    agents: List[SwarmAgent],
    rounds: int,
    seed_text: str,
    themes: List[str],
) -> str:
    """
    Produce a plain-English prediction summary from simulation results.
    Uses LLM if available; falls back to a structured text summary.
    """
    avg_stance = sum(a.stance_score for a in agents) / max(len(agents), 1)
    avg_activity = sum(a.activity_this_round for a in agents) / max(len(agents), 1)

    archetype_counts: Dict[str, int] = {}
    for a in agents:
        k = a.archetype.get("name", "unknown")
        archetype_counts[k] = archetype_counts.get(k, 0) + 1

    dominant_archetype = max(archetype_counts, key=archetype_counts.__getitem__)

    positive_agents = [a for a in agents if a.stance_score > 0.2]
    negative_agents = [a for a in agents if a.stance_score < -0.2]
    neutral_agents = [a for a in agents if -0.2 <= a.stance_score <= 0.2]

    highly_active = sorted(agents, key=lambda a: a.activity_this_round, reverse=True)[:3]
    most_connected = sorted(agents, key=lambda a: len(a.relationship_edges), reverse=True)[:3]

    round_trajectories = []
    for a in agents[:5]:
        round_entries = [m for m in a.temporal_memory if m.get("type") == "round_result"]
        if len(round_entries) >= 2:
            delta = round_entries[-1].get("stance", 0) - round_entries[0].get("stance", 0)
            round_trajectories.append(delta)

    avg_trajectory = sum(round_trajectories) / max(len(round_trajectories), 1)
    trend = "shifting toward agreement" if avg_trajectory > 0.05 else ("shifting toward opposition" if avg_trajectory < -0.05 else "remaining polarised")

    simulation_data = {
        "seed_excerpt": seed_text[:300],
        "themes": themes,
        "agent_count": len(agents),
        "rounds": rounds,
        "avg_stance": round(avg_stance, 3),
        "avg_activity": round(avg_activity, 3),
        "positive_pct": round(len(positive_agents) / max(len(agents), 1) * 100, 1),
        "negative_pct": round(len(negative_agents) / max(len(agents), 1) * 100, 1),
        "neutral_pct": round(len(neutral_agents) / max(len(agents), 1) * 100, 1),
        "dominant_archetype": dominant_archetype,
        "trend": trend,
        "highly_active": [a.name for a in highly_active],
        "most_connected": [a.name for a in most_connected],
    }

    llm_summary = _llm_summarise(simulation_data)
    if llm_summary:
        return llm_summary

    lines = []
    lines.append(f"Mesa Village Simulation — {len(agents)} agents, {rounds} rounds")
    lines.append("")

    stance_label = "moderately positive" if avg_stance > 0.2 else ("moderately negative" if avg_stance < -0.2 else "mixed / divided")
    lines.append(f"After {rounds} rounds of interaction, community sentiment is {stance_label} (average stance: {avg_stance:+.2f}).")
    lines.append(f"{len(positive_agents)} agents ({simulation_data['positive_pct']}%) hold a favourable position. "
                 f"{len(negative_agents)} ({simulation_data['negative_pct']}%) are opposed. "
                 f"{len(neutral_agents)} ({simulation_data['neutral_pct']}%) remain undecided.")
    lines.append("")
    lines.append(f"The dominant agent type is the {dominant_archetype} — this community is primarily {PERSONALITY_ARCHETYPES[0]['interaction_style'] if dominant_archetype == PERSONALITY_ARCHETYPES[0]['name'] else 'active'}.")
    lines.append(f"Across rounds, opinions are {trend}.")
    lines.append("")
    if themes:
        lines.append(f"Key themes driving agent behaviour: {', '.join(themes[:4])}.")
    lines.append("")
    lines.append(f"Most active voices: {', '.join(a.name for a in highly_active)}.")
    lines.append(f"Most influential nodes (by connections): {', '.join(a.name for a in most_connected)}.")
    lines.append("")

    if avg_activity > 0.6:
        lines.append("Prediction: High engagement level. Community is mobilising — expect rapid opinion spread and amplification of dominant viewpoints.")
    elif avg_activity < 0.2:
        lines.append("Prediction: Low engagement. The community is likely to fragment unless a catalytic event re-energises participation.")
    else:
        lines.append("Prediction: Moderate engagement. Dialogue is ongoing but no consensus has emerged. Outcome depends on which archetype gains network centrality.")

    return "\n".join(lines)


def _llm_summarise(data: Dict) -> Optional[str]:
    """Use the model router to generate a plain-English summary from simulation data."""
    try:
        from void_engine.aljabr_transpiler import get_model_router, TASK_STANDARD
        router = get_model_router()

        prompt = f"""You are an expert in community dynamics and social simulation.

A Mesa Village swarm simulation was run with the following parameters and results:

Seed text excerpt: "{data['seed_excerpt']}"
Key themes: {', '.join(data['themes'])}
Agents: {data['agent_count']} | Rounds: {data['rounds']}
Average stance score (−1 = fully opposed, +1 = fully supportive): {data['avg_stance']}
Average activity level (0–1): {data['avg_activity']}
Agent breakdown: {data['positive_pct']}% supportive, {data['negative_pct']}% opposed, {data['neutral_pct']}% neutral
Dominant agent archetype: {data['dominant_archetype']}
Opinion trajectory: {data['trend']}
Most active agents: {', '.join(data['highly_active'])}
Most connected agents: {', '.join(data['most_connected'])}

Write a 3–5 paragraph plain-English prediction summary of what this simulation reveals about how this community will respond to the topic in the seed text. Be specific, insightful, and avoid jargon. Focus on what is likely to happen next in the real community."""

        messages = [
            {"role": "system", "content": "You are a community dynamics analyst writing concise, insightful simulation summaries."},
            {"role": "user", "content": prompt},
        ]

        response, model, _ = router.call_with_fallback(
            TASK_STANDARD, messages, max_completion_tokens=600, task_label="mesa_summary"
        )

        try:
            usage = response.usage
            if usage:
                router.log_cost(TASK_STANDARD, model, usage.prompt_tokens, usage.completion_tokens, "mesa_summary")
        except Exception:
            pass

        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning("LLM summary generation failed: %s", e)
        return None


def simulate_from_seed(
    seed_text: str,
    n_agents: int = 10,
    rounds: int = 3,
) -> Dict:
    """
    Full pipeline: seed text → agents → GraphRAG graph → simulation → plain-English summary.
    Returns a dict with: agents_snapshot, summary, metadata.
    """
    started_at = datetime.now(timezone.utc)
    themes = _extract_themes(seed_text)
    entities = _extract_entities(seed_text)
    tensions = _extract_tensions(seed_text)

    agents = seed_to_agents(seed_text, n_agents)

    _run_swarm_rounds(agents, rounds, seed_event=seed_text[:200])

    summary = _build_plain_english_summary(agents, rounds, seed_text, themes)

    completed_at = datetime.now(timezone.utc)
    duration_s = (completed_at - started_at).total_seconds()

    return {
        "seed_excerpt": seed_text[:300],
        "themes": themes,
        "entities": entities,
        "tensions": tensions,
        "agent_count": len(agents),
        "rounds": rounds,
        "agents_snapshot": [a.to_dict() for a in agents],
        "summary": summary,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_s": round(duration_s, 3),
    }


def _init_mesa_simulations_table():
    """
    Ensure the mesa_simulations table exists for /mesa/simulate endpoint results.
    Separate from mesa_simulation_runs (used by the legacy mesa_engine).
    """
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mesa_simulations (
                    id SERIAL PRIMARY KEY,
                    seed TEXT NOT NULL,
                    agent_count INTEGER NOT NULL,
                    rounds INTEGER NOT NULL,
                    result JSONB NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning("mesa_simulations table init failed: %s", e)


def store_simulation_result(seed: str, agent_count: int, rounds: int, result: Dict) -> int:
    """
    Store a /mesa/simulate result in the mesa_simulations table.
    Returns the new row id. Raises on DB failure so the caller can surface a warning.
    """
    _init_mesa_simulations_table()
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO mesa_simulations (seed, agent_count, rounds, result, summary, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            seed[:2000],
            agent_count,
            rounds,
            json.dumps(result),
            result.get("summary", ""),
        ))
        row = cur.fetchone()
        conn.commit()
        if not row:
            raise RuntimeError("INSERT returned no id")
        return row[0]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_recent_simulations(limit: int = 5) -> List[Dict]:
    """
    Return recent /mesa/simulate results for Adriana to summarise.
    """
    _init_mesa_simulations_table()
    from void_engine.db_pool import get_db
    try:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, seed, agent_count, rounds, summary, created_at
                FROM mesa_simulations
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            results = []
            for row in rows:
                rid, seed, agent_count, rounds, summary, created_at = row
                results.append({
                    "id": rid,
                    "seed_excerpt": (seed or "")[:120],
                    "agent_count": agent_count,
                    "rounds": rounds,
                    "summary": summary,
                    "created_at": created_at.isoformat() if created_at else None,
                })
            return results
        finally:
            conn.close()
    except Exception as e:
        logger.warning("get_recent_simulations failed: %s", e)
        return []
