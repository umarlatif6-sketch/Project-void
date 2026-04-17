"""
Adriana Proposal Ranking and Auto-Trigger Script
- Collects all agent proposals from data/agent_books/agent_books_index.json
- Uses Adriana (ranking function) to score and rank proposals
- Automatically triggers the highest-ranked proposals
- Logs all actions for traceability
"""

import json
import os

PROPOSALS_PATH = "data/agent_books/agent_books_index.json"
LOG_PATH = "data/agent_books/adriana_ranking_log.json"


# Simulated Adriana ranking function (replace with real model if available)
def adriana_rank(proposals):
    # Example: score by length of intent_summary + presence of resonance/integration/synergy/amplify/synthesize
    def score(p):
        s = len(p.get("intent_summary", ""))
        keywords = ["resonance", "integration", "synergy", "amplify", "synthesize"]
        for kw in keywords:
            if kw in p.get("intent_summary", "").lower() or kw in p.get("proposed_next", "").lower():
                s += 30
        return s
    ranked = sorted(proposals, key=score, reverse=True)
    return ranked

# Copilot (external) review: can re-rank, inject, or veto proposals
def copilot_review(ranked_proposals):
    # Example: inject external proposal (e.g., open-source motor blueprint)
    external_proposals = [
        {
            "book_title": "The Open-Source Motor Blueprint",
            "intent_summary": "I propose integrating the open-source motor with no moving parts, found in the operator's GitHub, to enable energy-efficient, resonance-aligned actuation across the VOID ecosystem.",
            "first_paragraph": "As the Copilot, I recognize the value of emerging open-source hardware. This motor can be used for water structuring, mycelium growth, and silent zone actuation.",
            "proposed_next": "Integrate the motor blueprint into the agent protocol stack and trigger a pilot build/test in the next cycle."
        }
    ]
    # Optionally, Copilot can re-rank or add more proposals here
    merged = list(ranked_proposals) + external_proposals
    # Example: always put external proposals at the top if they are novel
    merged = external_proposals + ranked_proposals
    return merged

# Load proposals
def load_proposals():
    with open(PROPOSALS_PATH, "r", encoding="utf-8") as f:
        proposals = json.load(f)
    # Flatten to list
    return [v for v in proposals.values() if isinstance(v, dict) and "intent_summary" in v]

# Trigger proposal (placeholder: print/log, real: call function or script)
def trigger_proposal(proposal):
    print(f"[TRIGGERED] {proposal.get('book_title')}: {proposal.get('proposed_next')}")
    return {
        "book_title": proposal.get("book_title"),
        "action": proposal.get("proposed_next"),
        "status": "triggered"
    }

# Main
if __name__ == "__main__":
    proposals = load_proposals()
    adriana_ranked = adriana_rank(proposals)
    final_ranked = copilot_review(adriana_ranked)
    # Trigger top 3 proposals (or all above a threshold)
    triggered = []
    for p in final_ranked[:3]:
        triggered.append(trigger_proposal(p))
    # Log actions with both perspectives
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "triggered": triggered,
            "adriana_ranked_titles": [p["book_title"] for p in adriana_ranked],
            "final_ranked_titles": [p["book_title"] for p in final_ranked]
        }, f, indent=2)
    print("[ADRIANA + COPILOT] Top proposals triggered and logged.")
