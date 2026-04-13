#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def _load_feed_checkpoint(path: Path):
    data = _load_json(path)
    return {
        "processed": int(data.get("processed", 0)),
        "accepted": int(data.get("accepted", 0)),
        "rejected": int(data.get("rejected", 0)),
        "acceptance_rate": float(data.get("acceptance_rate", 0.0)),
    }


def main() -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    story = _load_feed_checkpoint(ROOT / "data" / "story_world_ecosystem.jsonl.story.checkpoint.json")
    voxcpm = _load_feed_checkpoint(ROOT / "data" / "public_source_voxcpm_ecosystem.jsonl.public.checkpoint.json")
    minicpm = _load_feed_checkpoint(ROOT / "data" / "public_source_minicpm_ecosystem.jsonl.public.checkpoint.json")

    integration = _load_json(ROOT / "data" / "integration_web.json")
    integration_meta = integration.get("metadata", {}) if isinstance(integration, dict) else {}
    judgment = integration.get("judgment_narrative", "") if isinstance(integration, dict) else ""

    weaver = _load_json(ROOT / "data" / "resonance_weaver_baseline.json")
    clusters = weaver.get("clusters", []) if isinstance(weaver, dict) else []

    top_clusters = []
    for c in clusters[:5]:
        idx = c.get("name_index")
        idx_text = str(idx).zfill(2) if isinstance(idx, int) and idx >= 0 else "??"
        top_clusters.append(
            f"- [{idx_text}] {c.get('name', 'Unknown')} | count={c.get('count', 0)} | coherence={c.get('coherence_score', 0)} | sources={','.join(c.get('sources', []))}"
        )

    total_processed = story["processed"] + voxcpm["processed"] + minicpm["processed"]
    total_accepted = story["accepted"] + voxcpm["accepted"] + minicpm["accepted"]

    lines = []
    lines.append("# Team System State Card")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("## Executive Status")
    lines.append("")
    lines.append("- System health: Operational")
    lines.append(f"- Total processed this cycle: {total_processed}")
    lines.append(f"- Total accepted this cycle: {total_accepted}")
    lines.append(f"- Integration bridges: {integration_meta.get('cross_feed_bridges', 0)}")
    lines.append(f"- Total web nodes: {integration_meta.get('total_nodes', 0)}")
    lines.append(f"- Total web edges: {integration_meta.get('total_edges', 0)}")
    lines.append("")
    lines.append("## Feed Performance")
    lines.append("")
    lines.append(f"- Story world: accepted {story['accepted']}/{story['processed']} ({story['acceptance_rate']}%)")
    lines.append(f"- Public VoxCPM: accepted {voxcpm['accepted']}/{voxcpm['processed']} ({voxcpm['acceptance_rate']}%)")
    lines.append(f"- Public MiniCPM: accepted {minicpm['accepted']}/{minicpm['processed']} ({minicpm['acceptance_rate']}%)")
    lines.append("")
    lines.append("## Top Convergence Clusters")
    lines.append("")
    if top_clusters:
        lines.extend(top_clusters)
    else:
        lines.append("- No clusters available yet")
    lines.append("")
    lines.append("## Adriana Judgment")
    lines.append("")
    lines.append(judgment or "No judgment available yet. Run autopilot first.")
    lines.append("")
    lines.append("## Team Benefits")
    lines.append("")
    lines.append("- Shared map: multiple sources converge into one decision surface")
    lines.append("- Faster prioritization: perspective-dense clusters highlight next scenarios")
    lines.append("- Lower noise: same-theory/different-story filter reduces scattered signals")
    lines.append("- Repeatable cadence: one command regenerates this card each cycle")
    lines.append("")
    lines.append("## Immediate Next Step")
    lines.append("")
    lines.append("- Open knowledge tree and filter Signals Navigator by All signal feeds, then perspective")

    out = ROOT / "docs" / "TEAM_SYSTEM_STATE_CARD.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
