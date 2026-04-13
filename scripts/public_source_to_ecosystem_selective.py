#!/usr/bin/env python3
"""
Public Source -> Ecosystem Selective Importer

Purpose:
- Ingest public open-source/public-web summaries, notes, or extracted observations
- Score entries against the ecosystem domains
- Encode accepted entries into the same 99-Names resonance pipeline

Recommended use:
- GitHub repo summaries
- Public docs or README notes
- Public research/project digests written by the user or generated from open sources
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from void_engine.knowledge_tree import three_brain_read
from void_engine.knowledge_tree_store import (
    init_knowledge_tree_tables,
    upsert_import_run,
    upsert_knowledge_tree_node,
)
from scripts.story_world_to_ecosystem_selective import (
    _clean_text,
    _extract_signals,
    _infer_format,
    _iter_entries,
)
from scripts.wikipedia_to_ecosystem_selective import calculate_ecosystem_fit, score_article


def run(
    input_path: Path,
    output_path: Path,
    fmt: str,
    threshold: float,
    source_label: str,
    min_chars: int,
    store_db: bool,
    resume: bool,
    limit: int,
    delimiter: str,
) -> Dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if store_db:
        init_knowledge_tree_tables()

    checkpoint_path = output_path.with_suffix(output_path.suffix + ".public.checkpoint.json")
    resume_state: Dict = {}
    if resume and checkpoint_path.exists():
        try:
            resume_state = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception:
            resume_state = {}

    processed = int(resume_state.get("processed", 0))
    accepted = int(resume_state.get("accepted", 0))
    rejected = int(resume_state.get("rejected", 0))
    last_title = str(resume_state.get("last_title", ""))
    skip_until_seen = bool(last_title)

    mode = "a" if resume and output_path.exists() else "w"

    with output_path.open(mode, encoding="utf-8") as out:
        for row in _iter_entries(input_path, fmt, delimiter):
            title = str(row.get("title", "")).strip()
            text = _clean_text(str(row.get("text", "")))

            if skip_until_seen:
                if title == last_title:
                    skip_until_seen = False
                continue

            processed += 1

            if not title or not text or len(text) < min_chars:
                rejected += 1
                continue

            domain_scores = score_article(title, text)
            fit_score, should_import = calculate_ecosystem_fit(domain_scores, threshold)
            if should_import:
                tree = three_brain_read(text[:50000])
                analogies, prospectives = _extract_signals(text)
                record = {
                    "title": title,
                    "source": source_label,
                    "source_origin": row.get("source", ""),
                    "series": row.get("series", ""),
                    "chapter": row.get("chapter", ""),
                    "url": row.get("url", ""),
                    "tags": row.get("tags", ""),
                    "text_chars": len(text),
                    "preview": text[:280],
                    "tree": tree,
                    "ecosystem_fit": fit_score,
                    "domain_scores": domain_scores,
                    "analogies": analogies,
                    "perspectives": prospectives,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                if store_db:
                    upsert_knowledge_tree_node(record)
                accepted += 1
            else:
                rejected += 1

            last_title = title
            if processed % 100 == 0:
                checkpoint_payload = {
                    "input": str(input_path),
                    "processed": processed,
                    "accepted": accepted,
                    "rejected": rejected,
                    "last_title": last_title,
                    "threshold": threshold,
                    "status": "running",
                    "source_label": source_label,
                }
                checkpoint_path.write_text(json.dumps(checkpoint_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                if store_db:
                    upsert_import_run(str(input_path), "public_source_selective", processed, rejected, last_title, checkpoint_payload, "running")

            if limit and accepted >= limit:
                break

    final_payload = {
        "input": str(input_path),
        "output": str(output_path),
        "threshold": threshold,
        "source_label": source_label,
        "processed": processed,
        "accepted": accepted,
        "rejected": rejected,
        "acceptance_rate": round(100 * accepted / max(1, processed), 2),
        "status": "complete",
    }
    checkpoint_path.write_text(json.dumps(final_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if store_db:
        upsert_import_run(str(input_path), "public_source_selective", processed, rejected, last_title, final_payload, "complete")
    return final_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Selectively ingest public-source text into the ecosystem.")
    parser.add_argument("--input", required=True, help="Path to JSONL, CSV, TXT, or MD source")
    parser.add_argument("--output", required=True, help="Path to JSONL output")
    parser.add_argument("--format", choices=["jsonl", "csv", "text"], default=None, help="Override input format")
    parser.add_argument("--threshold", type=float, default=0.40, help="Ecosystem fit threshold (0-1)")
    parser.add_argument("--source-label", default="public_source", help="Logical source label stored in output")
    parser.add_argument("--min-chars", type=int, default=220, help="Minimum text length to evaluate")
    parser.add_argument("--store-db", action="store_true", help="Persist accepted entries to knowledge tree database")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--limit", type=int, default=0, help="Max accepted entries (0 = no limit)")
    parser.add_argument("--delimiter", default="\n===\n", help="Delimiter for text mode blocks")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    fmt = _infer_format(input_path, args.format)
    summary = run(
        input_path=input_path,
        output_path=Path(args.output),
        fmt=fmt,
        threshold=args.threshold,
        source_label=args.source_label,
        min_chars=args.min_chars,
        store_db=args.store_db,
        resume=args.resume,
        limit=args.limit,
        delimiter=args.delimiter,
    )

    print("\nPUBLIC SOURCE -> ECOSYSTEM SELECTIVE IMPORT COMPLETE")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()