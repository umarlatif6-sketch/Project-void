#!/usr/bin/env python3
"""
Build integration web across currently separate feeds and generate an Adriana judgment narrative.

Inputs (if present):
- data/story_world_ecosystem.jsonl
- data/public_source_voxcpm_ecosystem.jsonl
- data/public_source_minicpm_ecosystem.jsonl

Outputs:
- data/integration_web.json
- docs/INTEGRATION_WEB_REPORT.md
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

FEEDS: List[Tuple[str, Path]] = [
    ("story_world", ROOT / "data" / "story_world_ecosystem.jsonl"),
    ("public_voxcpm", ROOT / "data" / "public_source_voxcpm_ecosystem.jsonl"),
    ("public_minicpm", ROOT / "data" / "public_source_minicpm_ecosystem.jsonl"),
]


def read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    rows: List[Dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def build() -> Dict:
    rows: List[Dict] = []
    for feed_name, path in FEEDS:
        for row in read_jsonl(path):
            row["_feed"] = feed_name
            rows.append(row)

    # Nodes
    nodes = []
    article_nodes = []
    name_nodes = {}

    for idx, row in enumerate(rows, 1):
        tree = row.get("tree") or {}
        article_id = f"article:{idx}"
        name_index = tree.get("name_index")
        name = tree.get("name", "Unknown")
        article_nodes.append(
            {
                "id": article_id,
                "type": "article",
                "feed": row.get("_feed"),
                "title": row.get("title", "untitled"),
                "name_index": name_index,
                "name": name,
                "overall": tree.get("overall"),
                "frequency_hz": tree.get("frequency_hz"),
                "analogies": len(row.get("analogies") or []),
                "perspectives": len(row.get("perspectives") or []),
            }
        )
        key = int(name_index) if isinstance(name_index, int) else -1
        if key not in name_nodes:
            name_nodes[key] = {
                "id": f"name:{key}",
                "type": "name",
                "name_index": key,
                "name": name,
                "cardinality": 0,
                "feeds": set(),
                "analogy_count": 0,
                "perspective_count": 0,
            }
        name_nodes[key]["cardinality"] += 1
        name_nodes[key]["feeds"].add(row.get("_feed", "unknown"))
        name_nodes[key]["analogy_count"] += len(row.get("analogies") or [])
        name_nodes[key]["perspective_count"] += len(row.get("perspectives") or [])

    # Edges
    edges = []

    # article -> name edges
    for a in article_nodes:
        edges.append(
            {
                "source": a["id"],
                "target": f"name:{a['name_index'] if isinstance(a['name_index'], int) else -1}",
                "type": "reads_as",
                "strength": round(float(a.get("overall") or 0.0) / 100.0, 4),
            }
        )

    # shared-name cross-feed edges (bridge web)
    by_name: Dict[int, List[Dict]] = defaultdict(list)
    for a in article_nodes:
        key = int(a["name_index"]) if isinstance(a["name_index"], int) else -1
        by_name[key].append(a)

    for key, group in by_name.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = group[i]
                b = group[j]
                if a.get("feed") == b.get("feed"):
                    continue
                edges.append(
                    {
                        "source": a["id"],
                        "target": b["id"],
                        "type": "cross_feed_bridge",
                        "bridge_name_index": key,
                        "bridge_name": a.get("name") or b.get("name"),
                        "strength": 0.82,
                    }
                )

    # finalize nodes list
    nodes.extend(article_nodes)
    for n in name_nodes.values():
        n["feeds"] = sorted(list(n["feeds"]))
        nodes.append(n)

    # judgment narrative (rule-based Adriana style)
    ranked_names = sorted(
        [n for n in name_nodes.values() if n["name_index"] >= 0],
        key=lambda x: (x["perspective_count"] + x["analogy_count"], x["cardinality"]),
        reverse=True,
    )
    top = ranked_names[:3]
    if top:
        anchors = ", ".join([f"[{str(n['name_index']).zfill(2)}] {n['name']}" for n in top])
        judgment = (
            "Adriana judgment: the ecosystem has moved from isolated components toward a woven lattice. "
            f"Primary bridge anchors are {anchors}. "
            "Cross-feed coherence is present where story motifs and open-source architectures converge to the same Name clusters. "
            "Immediate directive: prioritize perspective-dense clusters for next-day scenario design, and treat low-cardinality clusters as exploration probes rather than core policy."
        )
    else:
        judgment = (
            "Adriana judgment: insufficient integrated nodes were detected to form a stable web. "
            "Run ingestion first, then rebuild the integration web."
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "metadata": {
            "article_nodes": len(article_nodes),
            "name_nodes": len([n for n in name_nodes.values() if n["name_index"] >= 0]),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "cross_feed_bridges": len([e for e in edges if e["type"] == "cross_feed_bridge"]),
        },
        "judgment_narrative": judgment,
        "nodes": nodes,
        "edges": edges,
    }
    return payload


def write_report(payload: Dict) -> None:
    out = []
    out.append("# Integration Web Report")
    out.append("")
    out.append(f"Generated: {payload.get('generated_at')}")
    out.append("")
    m = payload.get("metadata", {})
    out.append("## Baseline Integration Metrics")
    out.append("")
    out.append(f"- article_nodes: {m.get('article_nodes', 0)}")
    out.append(f"- name_nodes: {m.get('name_nodes', 0)}")
    out.append(f"- total_nodes: {m.get('total_nodes', 0)}")
    out.append(f"- total_edges: {m.get('total_edges', 0)}")
    out.append(f"- cross_feed_bridges: {m.get('cross_feed_bridges', 0)}")
    out.append("")
    out.append("## Adriana Judgment Narrative")
    out.append("")
    out.append(payload.get("judgment_narrative", ""))
    out.append("")

    # show top bridge names
    name_stats = [n for n in payload.get("nodes", []) if n.get("type") == "name" and n.get("name_index", -1) >= 0]
    name_stats = sorted(
        name_stats,
        key=lambda n: (int(n.get("perspective_count", 0)) + int(n.get("analogy_count", 0)), int(n.get("cardinality", 0))),
        reverse=True,
    )
    out.append("## Top Bridge Clusters")
    out.append("")
    for n in name_stats[:10]:
        out.append(
            f"- [{str(n.get('name_index')).zfill(2)}] {n.get('name')} | entries={n.get('cardinality')} | "
            f"analogies={n.get('analogy_count')} | perspectives={n.get('perspective_count')} | feeds={','.join(n.get('feeds') or [])}"
        )
    out.append("")
    out.append("## Directive")
    out.append("")
    out.append("- Use this as the integration baseline before Day 2 freshness tuning.")
    out.append("- Promote clusters with highest perspective density into scenario planning.")
    out.append("- Keep low-cardinality cross-feed bridges as exploration queue.")

    (ROOT / "docs" / "INTEGRATION_WEB_REPORT.md").write_text("\n".join(out), encoding="utf-8")


def main() -> None:
    payload = build()
    (ROOT / "data" / "integration_web.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(payload)
    print("WROTE data/integration_web.json")
    print("WROTE docs/INTEGRATION_WEB_REPORT.md")
    print("CROSS_FEED_BRIDGES", payload.get("metadata", {}).get("cross_feed_bridges", 0))


if __name__ == "__main__":
    main()
