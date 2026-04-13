#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from void_engine.resonance_weaver import weave_entries

FEEDS: List[Tuple[str, Path]] = [
    ("story_world", ROOT / "data" / "story_world_ecosystem.jsonl"),
    ("public_voxcpm", ROOT / "data" / "public_source_voxcpm_ecosystem.jsonl"),
    ("public_minicpm", ROOT / "data" / "public_source_minicpm_ecosystem.jsonl"),
]


def _read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def main() -> None:
    entries: List[Dict] = []
    for feed, path in FEEDS:
        for row in _read_jsonl(path):
            entries.append(
                {
                    "title": row.get("title", "untitled"),
                    "text": row.get("preview") or "",
                    "source": feed,
                }
            )

    payload = weave_entries(entries, threshold=0.30)
    out_json = ROOT / "data" / "resonance_weaver_baseline.json"
    out_md = ROOT / "docs" / "RESONANCE_WEAVER_BASELINE.md"

    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Resonance Weaver Baseline")
    lines.append("")
    lines.append(f"Generated: {payload.get('generated_at')}")
    lines.append("")
    lines.append(f"Input entries: {payload.get('input_count', 0)}")
    lines.append(f"Accepted entries: {payload.get('accepted_count', 0)}")
    lines.append("")
    lines.append("## Adriana Judgment")
    lines.append("")
    lines.append(payload.get("judgment_narrative", ""))
    lines.append("")
    lines.append("## Top Clusters")
    lines.append("")
    for c in payload.get("clusters", [])[:10]:
        lines.append(
            f"- [{str(c.get('name_index')).zfill(2)}] {c.get('name')} | count={c.get('count')} | coherence={c.get('coherence_score')} | sources={','.join(c.get('sources') or [])}"
        )

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"WROTE {out_json}")
    print(f"WROTE {out_md}")


if __name__ == "__main__":
    main()
