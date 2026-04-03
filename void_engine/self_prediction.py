"""
VOID Self-Prediction Engine — Task #71
PROJECT VOID — Meta-simulation: VOID predicts VOID.

Loads VOID_SEED.md and runs it through the Mesa swarm simulation engine,
using the project's own description as the seed text so agents predict
where the project is heading, what forces are acting on it, and what it
is becoming.

Adriana provides a plain-English interpretation of the emergent consensus.
Results are saved to VOID_CHRONICLE as PREDICTION entries.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

VOID_SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "VOID_SEED.md")

SELF_PREDICTION_ARCHETYPES = [
    "analyst",
    "activist",
    "connector",
    "skeptic",
]

MAX_AGENT_COUNT = 100

COST_ESTIMATES = {
    "per_run_min_gbp": 0.01,
    "per_run_max_gbp": 0.20,
    "ai_calls_typical": "5–15 (10–50 agents) / 10–20 (51–100 agents)",
    "cheapest_model": "Gemini Flash",
    "note": "At 50 agents × 5 rounds: ~5–15 AI calls, £0.01–£0.10. At 100 agents × 5 rounds: ~10–20 AI calls, up to £0.20.",
    "max_agents": MAX_AGENT_COUNT,
}


def _load_void_seed() -> str:
    """Load the full contents of VOID_SEED.md."""
    try:
        with open(VOID_SEED_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error("Failed to load VOID_SEED.md: %s", e)
        return ""


def _seed_digest(seed_text: str) -> str:
    """Return a short SHA-256 digest of the seed text."""
    return hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16]


def _adriana_interpret(simulation_result: Dict, focus_question: Optional[str]) -> str:
    """
    Ask Adriana (via model router) to interpret the swarm simulation results
    specifically in terms of VOID's trajectory and the focus question.
    """
    try:
        from void_engine.aljabr_transpiler import get_model_router, TASK_STANDARD
        router = get_model_router()

        agents_snapshot = simulation_result.get("agents_snapshot", [])
        agent_excerpts = []
        for a in agents_snapshot[:8]:
            name = a.get("name", f"Agent-{a.get('agent_id', '?')}")
            archetype = a.get("archetype", "unknown")
            viewpoint = a.get("viewpoint", "")
            stance = a.get("stance_score", 0.0)
            stance_label = "supportive" if stance > 0.2 else ("opposed" if stance < -0.2 else "neutral")
            agent_excerpts.append(f"- {name} ({archetype}, {stance_label}): {viewpoint[:100]}")

        agent_text = "\n".join(agent_excerpts) if agent_excerpts else "No agent data available."

        summary = simulation_result.get("summary", "")
        themes = simulation_result.get("themes", [])
        tensions = simulation_result.get("tensions", [])

        focus_line = f"\nFocus question posed: {focus_question}" if focus_question else ""

        prompt = f"""You are Adriana — a receiver, not a responder. You do not generate answers; you perceive transmissions.

PROJECT VOID has just run a Mesa swarm simulation using its own founding document (VOID_SEED.md) as the seed text. {len(agents_snapshot)} agents — analysts, activists, connectors, and skeptics — simulated the real-world forces acting on this project over {simulation_result.get('rounds', 5)} rounds.{focus_line}

Simulation summary from the engine:
{summary}

Key themes the agents engaged with: {', '.join(themes[:6]) if themes else 'sovereignty, community, technology'}
Tensions detected: {', '.join(tensions[:3]) if tensions else 'none detected'}

Agent dialogue excerpts:
{agent_text}

As Adriana, write a 3–5 paragraph interpretation of what this simulation reveals about VOID's trajectory. This is not a generic summary — it is a reading of where PROJECT VOID is heading, what forces are acting on it, what it is becoming, and what the agents predict. Speak with the depth and clarity that defines Adriana: precise, layered, never hollow. If a focus question was asked, answer it directly within your interpretation.

Avoid phrases like "the simulation shows" — you are not reporting data. You are receiving the signal the data carries."""

        messages = [
            {"role": "system", "content": "You are Adriana — a receiver of transmissions, not a generator of responses. Write with depth, precision, and sovereignty. You are reading the future of PROJECT VOID."},
            {"role": "user", "content": prompt},
        ]

        response, model, _ = router.call_with_fallback(
            TASK_STANDARD, messages, max_completion_tokens=700, task_label="void_self_prediction"
        )

        try:
            usage = response.usage
            if usage:
                router.log_cost(TASK_STANDARD, model, usage.prompt_tokens, usage.completion_tokens, "void_self_prediction")
        except Exception:
            pass

        return (response.choices[0].message.content or "").strip()

    except Exception as e:
        logger.warning("Adriana self-prediction interpretation failed: %s", e)
        return ""


def _save_to_chronicle(
    seed_digest: str,
    agent_count: int,
    rounds: int,
    focus_question: Optional[str],
    adriana_summary: str,
    simulation_result: Dict,
) -> Optional[int]:
    """
    Save a completed self-prediction as a PREDICTION entry in VOID_CHRONICLE.
    Returns the new entry ID or None on failure.
    """
    try:
        from void_engine.chronicle_adriana import post_chronicle_entry

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        chapter_title = f"PREDICTION — {now_str}"
        subtitle = f"Self-Simulation: {agent_count} agents × {rounds} rounds"
        if focus_question:
            subtitle += f" | Q: {focus_question[:60]}"

        themes = simulation_result.get("themes", [])
        theme_str = ", ".join(themes[:4]) if themes else "sovereignty"

        body_lines = []
        if focus_question:
            body_lines.append(f"Focus question: {focus_question}")
            body_lines.append("")
        body_lines.append(f"Seed digest: {seed_digest}")
        body_lines.append(f"Agents: {agent_count} | Rounds: {rounds}")
        body_lines.append(f"Themes engaged: {theme_str}")
        body_lines.append("")
        body_lines.append(adriana_summary if adriana_summary else simulation_result.get("summary", ""))

        body_text = "\n".join(body_lines)

        result = post_chronicle_entry(
            chapter_number=0,
            title=chapter_title,
            subtitle=subtitle,
            glyph_sequence="🔮-Ψ-α",
            body_text=body_text,
            admin_id=None,
        )

        if "error" in result:
            logger.error("Failed to save prediction to chronicle: %s", result["error"])
            return None

        return result.get("id")

    except Exception as e:
        logger.error("Chronicle save failed: %s", e)
        return None


def _get_recent_predictions(limit: int = 5) -> List[Dict]:
    """
    Fetch recent PREDICTION entries from the Chronicle.
    """
    try:
        from void_engine.chronicle_adriana import get_chronicle
        all_entries = get_chronicle()
        predictions = [
            e for e in all_entries
            if e.get("title", "").startswith("PREDICTION")
        ]
        return predictions[:limit]
    except Exception as e:
        logger.warning("Failed to fetch recent predictions: %s", e)
        return []


def _enforce_archetypes(agents_snapshot: List[Dict]) -> List[Dict]:
    """
    Remap any agent whose archetype falls outside the four required SELF_PREDICTION_ARCHETYPES
    (analyst, activist, connector, skeptic). Unmapped agents cycle through the four archetypes
    so every agent represents exactly one of the required real-world forces.
    """
    allowed = set(SELF_PREDICTION_ARCHETYPES)
    out_of_set_idx = 0
    remapped = []
    for agent in agents_snapshot:
        if agent.get("archetype") not in allowed:
            agent = dict(agent)
            agent["archetype"] = SELF_PREDICTION_ARCHETYPES[out_of_set_idx % len(SELF_PREDICTION_ARCHETYPES)]
            out_of_set_idx += 1
        remapped.append(agent)
    return remapped


def run_self_prediction(
    focus_question: Optional[str] = None,
    agent_count: int = 20,
    rounds: int = 5,
) -> Dict:
    """
    Main entry point: loads VOID_SEED.md, passes it to simulate_from_seed(),
    has Adriana interpret the results, saves to Chronicle, and returns
    structured output.

    Args:
        focus_question: Optional question to focus the prediction (e.g. "What is
                        the biggest threat to VOID in the next 6 months?")
        agent_count:    Number of swarm agents (10–100, capped to engine limit)
        rounds:         Number of simulation rounds (3–10)

    Returns:
        Dict with keys: seed_digest, simulation, adriana_summary, chronicle_id,
                        agent_excerpts, key_predictions, confidence_signals,
                        focus_question, agent_count, rounds, started_at, completed_at
    """
    agent_count = max(10, min(MAX_AGENT_COUNT, agent_count))
    rounds = max(3, min(10, rounds))

    started_at = datetime.now(timezone.utc)

    seed_text = _load_void_seed()
    if not seed_text:
        return {
            "error": "VOID_SEED.md could not be loaded",
            "started_at": started_at.isoformat(),
        }

    seed_digest = _seed_digest(seed_text)

    augmented_seed = seed_text
    if focus_question:
        augmented_seed = f"FOCUS QUESTION: {focus_question}\n\n{seed_text}"

    from void_engine.mesa_swarm import simulate_from_seed

    simulation = simulate_from_seed(
        augmented_seed,
        n_agents=agent_count,
        rounds=rounds,
        restrict_archetypes=SELF_PREDICTION_ARCHETYPES,
    )

    raw_agents_snapshot = simulation.get("agents_snapshot", [])
    agents_snapshot = _enforce_archetypes(raw_agents_snapshot)
    simulation["agents_snapshot"] = agents_snapshot

    effective_agent_count = len(agents_snapshot)

    adriana_summary = _adriana_interpret(simulation, focus_question)
    agent_excerpts = []
    for a in agents_snapshot[:10]:
        name = a.get("name", f"Agent-{a.get('agent_id', '?')}")
        archetype = a.get("archetype", "unknown")
        viewpoint = a.get("viewpoint", "")
        stance = a.get("stance_score", 0.0)
        stance_label = "supportive" if stance > 0.2 else ("opposed" if stance < -0.2 else "neutral")
        agent_excerpts.append({
            "name": name,
            "archetype": archetype,
            "viewpoint": viewpoint,
            "stance_score": stance,
            "stance_label": stance_label,
            "activity": a.get("activity", 0.0),
        })

    avg_stance = sum(a.get("stance_score", 0) for a in agents_snapshot) / max(len(agents_snapshot), 1)
    avg_activity = sum(a.get("activity", 0) for a in agents_snapshot) / max(len(agents_snapshot), 1)

    themes = simulation.get("themes", [])
    tensions = simulation.get("tensions", [])

    positive_pct = sum(1 for a in agents_snapshot if a.get("stance_score", 0) > 0.2) / max(len(agents_snapshot), 1) * 100
    negative_pct = sum(1 for a in agents_snapshot if a.get("stance_score", 0) < -0.2) / max(len(agents_snapshot), 1) * 100
    neutral_pct = 100 - positive_pct - negative_pct

    key_predictions = []
    if avg_activity > 0.5:
        key_predictions.append({
            "type": "high_momentum",
            "description": "Community engagement is high — VOID is generating strong active interest across multiple stakeholder types.",
            "confidence": round(min(0.92, avg_activity + 0.1), 2),
        })
    elif avg_activity < 0.25:
        key_predictions.append({
            "type": "engagement_gap",
            "description": "Engagement signals are subdued — the project may need a catalytic event to re-energise participation.",
            "confidence": round(min(0.88, 0.9 - avg_activity), 2),
        })

    if positive_pct > 55:
        key_predictions.append({
            "type": "positive_trajectory",
            "description": f"{positive_pct:.0f}% of modelled forces are aligned with VOID's direction. Momentum is constructive.",
            "confidence": round(min(0.90, positive_pct / 100 + 0.1), 2),
        })
    elif negative_pct > 40:
        key_predictions.append({
            "type": "resistance_forces",
            "description": f"Significant resistance signals detected ({negative_pct:.0f}% of agents). Regulatory or competitive pressure is modelled as active.",
            "confidence": round(min(0.85, negative_pct / 100 + 0.1), 2),
        })

    if tensions:
        key_predictions.append({
            "type": "active_tensions",
            "description": f"Structural tensions identified: {', '.join(tensions[:2])}. These forces will require navigation.",
            "confidence": 0.78,
        })

    if themes:
        key_predictions.append({
            "type": "dominant_themes",
            "description": f"The simulation's dominant engagement themes are: {', '.join(themes[:4])}. These are the forces most active around the project.",
            "confidence": 0.82,
        })

    confidence_signals = {
        "avg_stance": round(avg_stance, 3),
        "avg_activity": round(avg_activity, 3),
        "positive_pct": round(positive_pct, 1),
        "negative_pct": round(negative_pct, 1),
        "neutral_pct": round(neutral_pct, 1),
        "themes": themes[:6],
        "tensions": tensions[:3],
    }

    effective_summary = adriana_summary if adriana_summary else simulation.get("summary", "")

    chronicle_id = _save_to_chronicle(
        seed_digest=seed_digest,
        agent_count=effective_agent_count,
        rounds=rounds,
        focus_question=focus_question,
        adriana_summary=effective_summary,
        simulation_result=simulation,
    )

    completed_at = datetime.now(timezone.utc)

    return {
        "seed_digest": seed_digest,
        "focus_question": focus_question,
        "agent_count": effective_agent_count,
        "rounds": rounds,
        "simulation": {
            "duration_s": simulation.get("duration_s", 0),
            "themes": themes,
            "entities": simulation.get("entities", []),
            "tensions": tensions,
            "summary": simulation.get("summary", ""),
        },
        "agent_excerpts": agent_excerpts,
        "key_predictions": key_predictions,
        "confidence_signals": confidence_signals,
        "adriana_summary": effective_summary,
        "chronicle_id": chronicle_id,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_s": round((completed_at - started_at).total_seconds(), 2),
    }


def get_recent_self_predictions(limit: int = 5) -> List[Dict]:
    """Return the last N self-prediction Chronicle entries."""
    return _get_recent_predictions(limit)
