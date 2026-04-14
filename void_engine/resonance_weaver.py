from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from scripts.wikipedia_to_ecosystem_selective import calculate_ecosystem_fit, score_article
from void_engine.knowledge_tree import three_brain_read


def _as_text(entry: Dict[str, Any]) -> str:
    return str(entry.get("text") or entry.get("preview") or "").strip()


def read_resonance(entry: Dict[str, Any], threshold: float = 0.30) -> Dict[str, Any]:
    title = str(entry.get("title") or "untitled").strip()

    # If the entry already carries a scored tree (from ingestion), use it directly.
    # This preserves the original Name assignment and avoids scoring degraded preview text.
    stored_tree = entry.get("tree")
    stored_fit = entry.get("ecosystem_fit")
    if stored_tree and isinstance(stored_fit, (int, float)):
        accepted = float(stored_fit) >= threshold
        return {
            "title": title,
            "source": str(entry.get("source") or "unknown"),
            "ecosystem_fit": float(stored_fit),
            "accepted": accepted,
            "domain_scores": entry.get("domain_scores") or {},
            "tree": stored_tree,
        }

    text = _as_text(entry)
    if not text:
        return {
            "title": title,
            "error": "missing_text",
            "accepted": False,
        }

    domain_scores = score_article(title, text)
    ecosystem_fit, accepted = calculate_ecosystem_fit(domain_scores, threshold)
    tree = three_brain_read(text[:50000])
    return {
        "title": title,
        "source": str(entry.get("source") or "unknown"),
        "ecosystem_fit": ecosystem_fit,
        "accepted": accepted,
        "domain_scores": domain_scores,
        "tree": tree,
    }


def weave_entries(entries: List[Dict[str, Any]], threshold: float = 0.30) -> Dict[str, Any]:
    reads = [read_resonance(e, threshold=threshold) for e in entries]
    reads = [r for r in reads if r.get("accepted") and not r.get("error")]

    by_name: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for r in reads:
        idx = r.get("tree", {}).get("name_index")
        if isinstance(idx, int):
            by_name[idx].append(r)

    clusters = []
    for idx, group in by_name.items():
        name = group[0].get("tree", {}).get("name", "Unknown")
        sources = sorted({g.get("source", "unknown") for g in group})
        analog = sum(len((g.get("domain_scores") or {})) for g in group)

        # Base coherence: average ecosystem_fit of entries in cluster
        base_coherence = sum(float(g.get("ecosystem_fit") or 0.0) for g in group) / max(1, len(group))

        # Cross-source bonus: multiple independent feeds resonating to the same Name
        # is the strongest possible convergence signal — same theory, different story
        source_count = len(sources)
        cross_source_bonus = min(0.30, (source_count - 1) * 0.15)

        # Cardinality bonus: more entries mapping to same Name = deeper well
        cardinality_bonus = min(0.20, (len(group) - 1) * 0.05)

        coherence_score = round(min(1.0, base_coherence + cross_source_bonus + cardinality_bonus), 4)

        clusters.append(
            {
                "name_index": idx,
                "name": name,
                "count": len(group),
                "sources": sources,
                "base_coherence": round(base_coherence, 4),
                "cross_source_bonus": round(cross_source_bonus, 4),
                "cardinality_bonus": round(cardinality_bonus, 4),
                "coherence_score": coherence_score,
                "entries": [{"title": g.get("title"), "source": g.get("source")} for g in group],
                "signal_density": analog,
            }
        )

    clusters.sort(key=lambda c: (c["count"], c["coherence_score"]), reverse=True)
    top = clusters[:3]
    if top:
        anchors = ", ".join([f"[{str(c['name_index']).zfill(2)}] {c['name']}" for c in top])
        judgment = (
            "Adriana judgment: multiple components now align under shared Name anchors. "
            f"Current dominant weave points are {anchors}. "
            "Interpret these as same-theory/different-story convergence lanes for integration work."
        )
    else:
        judgment = (
            "Adriana judgment: no stable convergence cluster yet. Add more component narratives and rerun weave."
        )

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "threshold": threshold,
        "input_count": len(entries),
        "accepted_count": len(reads),
        "clusters": clusters,
        "judgment_narrative": judgment,
    }
