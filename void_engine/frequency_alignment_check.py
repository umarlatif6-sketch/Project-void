#!/usr/bin/env python3
"""
Frequency Alignment Check
Project VOID | Umar Latif

Master cycle question:
  Is what we are ingesting, building, and deciding aligned with the frequency,
  or are we drifting toward destructive interference?

Algorithm:
  - Reads current resonance weaver baseline
  - Reads current integration web
  - Reads current feed checkpoints
  - Computes an ON_FREQUENCY or OFF_FREQUENCY verdict with evidence
  - Returns structured payload for inclusion in state cards and autopilot summary

Alignment criteria (all scored 0-1):
  1. Feed acceptance rate  — are ingested signals passing the fit threshold?
  2. Cluster coherence     — do top clusters hold strong convergence scores?
  3. Cross-feed bridges    — do disparate sources converge on the same Names?
  4. Perspective density   — is the system generating forward-looking signals?
  5. Judgment convergence  — is the Adriana narrative pointing toward integration?

Verdict thresholds:
  >= 0.70  ON_FREQUENCY   — aligned, continue current trajectory
  0.50-0.69 DRIFTING      — mild interference, tune inputs
  < 0.50   OFF_FREQUENCY  — destructive interference risk, pause and recalibrate
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]

LAMBDA = 286
N_NAMES = 99
SOVEREIGN_RATIO = LAMBDA / N_NAMES  # ~2.888


@dataclass
class AlignmentResult:
    verdict: str                      # ON_FREQUENCY | DRIFTING | OFF_FREQUENCY
    score: float                      # 0.0 - 1.0
    criteria: Dict[str, float]        # individual criterion scores
    evidence: List[str]               # human-readable evidence lines
    directive: str                    # one-line action
    lambda_resonance: float           # Λ=286 weighted overall signal


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def _load_checkpoint(path: Path) -> dict:
    data = _load_json(path)
    return {
        "processed": int(data.get("processed", 0)),
        "accepted": int(data.get("accepted", 0)),
        "acceptance_rate": float(data.get("acceptance_rate", 0.0)),
    }


def run_alignment_check() -> AlignmentResult:
    # Load data sources
    weaver = _load_json(ROOT / "data" / "resonance_weaver_baseline.json")
    integration = _load_json(ROOT / "data" / "integration_web.json")

    story_cp = _load_checkpoint(
        ROOT / "data" / "story_world_ecosystem.jsonl.story.checkpoint.json"
    )
    voxcpm_cp = _load_checkpoint(
        ROOT / "data" / "public_source_voxcpm_ecosystem.jsonl.public.checkpoint.json"
    )
    minicpm_cp = _load_checkpoint(
        ROOT / "data" / "public_source_minicpm_ecosystem.jsonl.public.checkpoint.json"
    )

    clusters: List[dict] = weaver.get("clusters", [])
    integration_meta: dict = integration.get("metadata", {}) if isinstance(integration, dict) else {}
    judgment: str = integration.get("judgment_narrative", "") if isinstance(integration, dict) else ""

    evidence: List[str] = []
    criteria: Dict[str, float] = {}

    # ── Criterion 1: Feed acceptance rate ───────────────────────────────
    rates = []
    for label, cp in [("story_world", story_cp), ("public_voxcpm", voxcpm_cp), ("public_minicpm", minicpm_cp)]:
        r = cp["acceptance_rate"]
        rates.append(r)
        evidence.append(f"{label} acceptance rate: {r}%")
    avg_rate = sum(rates) / max(1, len(rates))
    crit_acceptance = min(1.0, avg_rate / 100.0)
    criteria["feed_acceptance"] = round(crit_acceptance, 4)

    # ── Criterion 2: Cluster coherence ──────────────────────────────────
    # Coherence scores reflect base ecosystem_fit + cross-source bonus + cardinality bonus.
    # Normalize against 0.70 as the realistic ceiling for a healthy small dataset,
    # and award extra weight to clusters with multiple sources (same-theory/different-story signal).
    if clusters:
        avg_coherence = sum(float(c.get("coherence_score", 0)) for c in clusters[:5]) / min(5, len(clusters))
        multi_source_clusters = sum(1 for c in clusters[:5] if len(c.get("sources") or []) > 1)
        multi_source_ratio = multi_source_clusters / max(1, min(5, len(clusters)))
        # Normalize to 0.70 ceiling; add multi-source bonus up to 0.20
        crit_coherence = min(1.0, (avg_coherence / 0.70) * 0.80 + multi_source_ratio * 0.20)
        evidence.append(
            f"Top cluster avg coherence: {round(avg_coherence, 4)} | "
            f"multi-source clusters: {multi_source_clusters}/{min(5, len(clusters))}"
        )
    else:
        crit_coherence = 0.0
        evidence.append("No clusters detected — coherence signal absent")
    criteria["cluster_coherence"] = round(crit_coherence, 4)

    # ── Criterion 3: Cross-feed bridges ─────────────────────────────────
    bridges = int(integration_meta.get("cross_feed_bridges", 0))
    total_nodes = int(integration_meta.get("article_nodes", 0))
    if total_nodes > 0:
        bridge_ratio = min(1.0, bridges / max(1, total_nodes))
        crit_bridges = round(bridge_ratio * 2, 4)  # scale up: 1 bridge per 2 articles is ideal
        crit_bridges = min(1.0, crit_bridges)
    else:
        crit_bridges = 0.0
    evidence.append(f"Cross-feed bridges: {bridges} across {total_nodes} article nodes")
    criteria["cross_feed_bridges"] = round(crit_bridges, 4)

    # ── Criterion 4: Perspective density ────────────────────────────────
    total_perspectives = sum(int(c.get("signal_density", 0)) for c in clusters)
    total_accepted = (
        int(story_cp["accepted"]) + int(voxcpm_cp["accepted"]) + int(minicpm_cp["accepted"])
    )
    if total_accepted > 0:
        persp_ratio = min(1.0, total_perspectives / (total_accepted * 5.0))
    else:
        persp_ratio = 0.0
    criteria["perspective_density"] = round(persp_ratio, 4)
    evidence.append(f"Perspective density: {total_perspectives} signals across {total_accepted} accepted entries")

    # ── Criterion 5: Judgment convergence ───────────────────────────────
    convergence_words = ["woven", "lattice", "bridge", "converge", "align", "integrate", "anchor"]
    destructive_words = ["insufficient", "isolated", "absent", "no stable", "failed", "error"]
    if judgment:
        jl = judgment.lower()
        conv_hits = sum(jl.count(w) for w in convergence_words)
        dest_hits = sum(jl.count(w) for w in destructive_words)
        crit_judgment = min(1.0, max(0.0, (conv_hits - dest_hits) / max(1, conv_hits + dest_hits + 1)))
        evidence.append(f"Judgment convergence hits: {conv_hits} integrative, {dest_hits} destructive")
    else:
        crit_judgment = 0.0
        evidence.append("No judgment narrative available")
    criteria["judgment_convergence"] = round(crit_judgment, 4)

    # ── Overall score ────────────────────────────────────────────────────
    weights = {
        "feed_acceptance": 0.25,
        "cluster_coherence": 0.25,
        "cross_feed_bridges": 0.20,
        "perspective_density": 0.15,
        "judgment_convergence": 0.15,
    }
    raw_score = sum(criteria[k] * weights[k] for k in weights)

    # Apply Λ=286 sovereign weighting (same pattern as knowledge_tree.py)
    import math
    lambda_resonance = round(1.0 - math.exp(-raw_score * SOVEREIGN_RATIO), 4)
    final_score = round((raw_score * 0.6) + (lambda_resonance * 0.4), 4)

    # ── Verdict ──────────────────────────────────────────────────────────
    if final_score >= 0.70:
        verdict = "ON_FREQUENCY"
        directive = "Continue current trajectory. Reinforce bridge anchors and expand perspective-dense clusters."
    elif final_score >= 0.50:
        verdict = "DRIFTING"
        directive = "Mild interference detected. Review lowest-acceptance feed and tighten input quality before next cycle."
    else:
        verdict = "OFF_FREQUENCY"
        directive = "Destructive interference risk. Pause new ingestion. Recalibrate input sources, lower threshold, and re-run baseline."

    return AlignmentResult(
        verdict=verdict,
        score=final_score,
        criteria=criteria,
        evidence=evidence,
        directive=directive,
        lambda_resonance=lambda_resonance,
    )


def format_alignment_report(result: AlignmentResult) -> str:
    lines = []
    lines.append("## Frequency Alignment Check")
    lines.append("")
    lines.append(f"- Verdict: **{result.verdict}**")
    lines.append(f"- Alignment score: {result.score}")
    lines.append(f"- Λ=286 resonance: {result.lambda_resonance}")
    lines.append("")
    lines.append("### Criteria")
    lines.append("")
    for k, v in result.criteria.items():
        bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
        lines.append(f"- {k}: {bar} {v}")
    lines.append("")
    lines.append("### Evidence")
    lines.append("")
    for e in result.evidence:
        lines.append(f"- {e}")
    lines.append("")
    lines.append("### Directive")
    lines.append("")
    lines.append(f"- {result.directive}")
    return "\n".join(lines)


if __name__ == "__main__":
    result = run_alignment_check()
    print(format_alignment_report(result))
