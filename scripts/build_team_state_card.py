#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from void_engine.frequency_alignment_check import format_alignment_report, run_alignment_check


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


def _render_card(
    *,
    title: str,
    now: str,
    role: str,
    story: dict,
    voxcpm: dict,
    minicpm: dict,
    integration_meta: dict,
    judgment: str,
    top_clusters: list[str],
    alignment_report: str = "",
) -> str:
    total_processed = story["processed"] + voxcpm["processed"] + minicpm["processed"]
    total_accepted = story["accepted"] + voxcpm["accepted"] + minicpm["accepted"]

    lines: list[str] = []
    lines.append(f"# {title}")
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
    if alignment_report:
        lines.append(alignment_report)
        lines.append("")

    if role == "founder":
        lines.append("## Founder Lens")
        lines.append("")
        lines.append("- Decision priority: reinforce bridge anchors before expanding breadth")
        lines.append("- Capital focus: allocate effort to clusters with high coherence and cross-feed overlap")
        lines.append("- Narrative posture: communicate woven-system advantage over isolated experiments")
        lines.append("")
        lines.append("## Immediate Next Step")
        lines.append("")
        lines.append("- Pick top 2 bridge anchors from this card and define one strategic bet per anchor for the next cycle")
    elif role == "operator":
        lines.append("## Operator Lens")
        lines.append("")
        lines.append("- Cadence priority: keep daily autopilot execution stable and checkpoint-safe")
        lines.append("- Throughput focus: raise weak feed acceptance by tightening low-fit source inputs")
        lines.append("- Delivery posture: convert perspective-dense clusters into concrete next-day tasks")
        lines.append("")
        lines.append("## Immediate Next Step")
        lines.append("")
        lines.append("- Run one quality pass on the lowest-acceptance feed and re-run autopilot to confirm improved signal density")
    elif role == "research":
        lines.append("## Research Lens")
        lines.append("")
        lines.append("- Inquiry priority: test whether low-cardinality clusters are emergent or noisy")
        lines.append("- Validation focus: compare analogy/perspective structure across story and public lanes")
        lines.append("- Evidence posture: document same-theory/different-story examples with cluster references")
        lines.append("")
        lines.append("## Immediate Next Step")
        lines.append("")
        lines.append("- Select 3 clusters and write hypothesis notes on why their convergence appears, then test in the next ingest cycle")
    else:
        lines.append("## Team Benefits")
        lines.append("")
        lines.append("- Shared map: multiple sources converge into one decision surface")
        lines.append("- Faster prioritization: perspective-dense clusters highlight next scenarios")
        lines.append("- Lower noise: same-theory/different-story filter reduces scattered signals")
        lines.append("- Repeatable cadence: one command regenerates this card each cycle")
        lines.append("")
        lines.append("## Immediate Next Step")
        lines.append("")
        lines.append("- Open knowledge tree and filter Signals Navigator by All signal feeds, then perspective filter to extract forward scenarios quickly")

    return "\n".join(lines)


def _write_card(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"WROTE {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build role-aware team system state cards")
    parser.add_argument(
        "--role",
        choices=["all", "founder", "operator", "research"],
        default="all",
        help="Render a specific role view or all views",
    )
    args = parser.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    alignment_result = run_alignment_check()
    alignment_report = format_alignment_report(alignment_result)
    print(f"ALIGNMENT_VERDICT={alignment_result.verdict} score={alignment_result.score}")

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

    if args.role in {"all", "founder"}:
        founder_content = _render_card(
            title="Team System State Card - Founder",
            now=now,
            role="founder",
            story=story,
            voxcpm=voxcpm,
            minicpm=minicpm,
            integration_meta=integration_meta,
            judgment=judgment,
            top_clusters=top_clusters,
            alignment_report=alignment_report,
        )
        _write_card(ROOT / "docs" / "TEAM_SYSTEM_STATE_CARD_FOUNDER.md", founder_content)

    if args.role in {"all", "operator"}:
        operator_content = _render_card(
            title="Team System State Card - Operator",
            now=now,
            role="operator",
            story=story,
            voxcpm=voxcpm,
            minicpm=minicpm,
            integration_meta=integration_meta,
            judgment=judgment,
            top_clusters=top_clusters,
            alignment_report=alignment_report,
        )
        _write_card(ROOT / "docs" / "TEAM_SYSTEM_STATE_CARD_OPERATOR.md", operator_content)

    if args.role in {"all", "research"}:
        research_content = _render_card(
            title="Team System State Card - Research",
            now=now,
            role="research",
            story=story,
            voxcpm=voxcpm,
            minicpm=minicpm,
            integration_meta=integration_meta,
            judgment=judgment,
            top_clusters=top_clusters,
            alignment_report=alignment_report,
        )
        _write_card(ROOT / "docs" / "TEAM_SYSTEM_STATE_CARD_RESEARCH.md", research_content)

    if args.role == "all":
        default_content = _render_card(
            title="Team System State Card",
            now=now,
            role="all",
            story=story,
            voxcpm=voxcpm,
            minicpm=minicpm,
            integration_meta=integration_meta,
            judgment=judgment,
            top_clusters=top_clusters,
            alignment_report=alignment_report,
        )
        _write_card(ROOT / "docs" / "TEAM_SYSTEM_STATE_CARD.md", default_content)


if __name__ == "__main__":
    main()
