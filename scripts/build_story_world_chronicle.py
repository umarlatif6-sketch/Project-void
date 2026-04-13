#!/usr/bin/env python3
"""
Build a markdown chronicle from story-world selective output.

Input:
- JSONL produced by scripts/story_world_to_ecosystem_selective.py

Output:
- Markdown digest highlighting analogies and perspectives by series
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def _read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _score(row: Dict) -> float:
    return float(row.get("ecosystem_fit") or 0.0)


def _top_domain(row: Dict) -> str:
    scores = row.get("domain_scores") or {}
    if not isinstance(scores, dict) or not scores:
        return "unknown"
    return max(scores.items(), key=lambda kv: float(kv[1] or 0.0))[0]


def build_markdown(rows: List[Dict], limit_per_series: int = 8) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: List[str] = []
    lines.append("# Story World Chronicle")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append(f"Entries processed: {len(rows)}")
    lines.append("")

    if not rows:
        lines.append("No entries found.")
        return "\n".join(lines)

    rows_sorted = sorted(rows, key=_score, reverse=True)
    by_series: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows_sorted:
        series = str(row.get("series") or "Unlabeled").strip() or "Unlabeled"
        by_series[series].append(row)

    lines.append("## Top Signals")
    lines.append("")
    for row in rows_sorted[:10]:
        title = row.get("title", "untitled")
        name = (row.get("tree") or {}).get("name", "unknown")
        fit = _score(row)
        lines.append(f"- {title} | Name: {name} | Fit: {fit:.3f} | Domain: {_top_domain(row)}")
    lines.append("")

    for series in sorted(by_series.keys()):
        lines.append(f"## Series: {series}")
        lines.append("")
        for row in by_series[series][:limit_per_series]:
            title = row.get("title", "untitled")
            tree = row.get("tree") or {}
            analogies = row.get("analogies") or []
            perspectives = row.get("perspectives") or []
            lines.append(f"### {title}")
            lines.append("")
            lines.append(
                f"- Name: {tree.get('name', 'unknown')} ({tree.get('name_index', 'n/a')}) | "
                f"Frequency: {tree.get('frequency_hz', 'n/a')} Hz | Fit: {_score(row):.3f}"
            )
            lines.append(f"- Dominant Domain: {_top_domain(row)}")
            if analogies:
                lines.append(f"- Analogy: {analogies[0]}")
            if perspectives:
                lines.append(f"- Perspective: {perspectives[0]}")
            tags = row.get("tags")
            if tags:
                lines.append(f"- Tags: {tags}")
            lines.append("")

    lines.append("## Action Queue")
    lines.append("")
    lines.append("- Promote top-fit entries into strategic design notes.")
    lines.append("- Cross-link repeated analogies to the same 99 Name cluster.")
    lines.append("- Convert high-confidence perspectives into scenario experiments.")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a story-world chronicle markdown digest.")
    parser.add_argument("--input", required=True, help="Path to story-world ecosystem JSONL")
    parser.add_argument("--output", required=True, help="Path to markdown chronicle output")
    parser.add_argument("--limit-per-series", type=int, default=8, help="Entries per series in digest")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    rows = _read_jsonl(input_path)
    markdown = build_markdown(rows, args.limit_per_series)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Chronicle written: {output_path}")
    print(f"Entries: {len(rows)}")


if __name__ == "__main__":
    main()
