#!/usr/bin/env python3
"""
Story World -> Ecosystem Selective Importer

Purpose:
- Ingest user-provided web novel chapter notes/excerpts/summaries
- Score each entry against the 19 ecosystem domains
- Keep only high-resonance entries
- Encode selected entries with Three-Brain reading into the 99 Names ontology

Important:
- This script is designed for user-owned text, licensed exports, or original summaries.
- It does not scrape paywalled or copyrighted chapter text from third-party sites.

Supported input formats:
- JSONL: one object per line with at least {"title": "...", "text": "..."}
- CSV: columns include title,text and optional source,url,series,chapter,tags
- TXT/MD: blocks separated by a delimiter, first line is title and the rest is text

Usage:
  python3 scripts/story_world_to_ecosystem_selective.py \
    --input data/story_world_ingest_template.jsonl \
    --output data/story_world_ecosystem.jsonl \
    --threshold 0.40 \
    --source-label story_world \
    --store-db
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, Generator, Iterable, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from void_engine.knowledge_tree import three_brain_read
from void_engine.knowledge_tree_store import (
    init_knowledge_tree_tables,
    upsert_import_run,
    upsert_knowledge_tree_node,
)
from scripts.wikipedia_to_ecosystem_selective import (
    calculate_ecosystem_fit,
    score_article,
)


ANALOGY_CUES = (
    "like ",
    "as if",
    "resembles",
    "mirror",
    "analog",
    "metaphor",
    "maps to",
)

PROSPECTIVE_CUES = (
    "could",
    "future",
    "next",
    "predict",
    "likely",
    "will",
    "scenario",
    "roadmap",
    "shows",
    "implies",
    "depends",
    "under pressure",
    "strategy",
    "risk",
    "opportunity",
)


def _sentence_chunks(text: str) -> list[str]:
    chunks = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    return chunks


def _extract_signals(text: str, max_items: int = 6) -> Tuple[list[str], list[str]]:
    sentences = _sentence_chunks(text)
    analogies: list[str] = []
    prospectives: list[str] = []

    for sentence in sentences:
        lowered = sentence.lower()
        if len(analogies) < max_items and any(cue in lowered for cue in ANALOGY_CUES):
            analogies.append(sentence)
        if len(prospectives) < max_items and any(cue in lowered for cue in PROSPECTIVE_CUES):
            prospectives.append(sentence)
        if len(analogies) >= max_items and len(prospectives) >= max_items:
            break

    if not prospectives:
        # Fallback: capture forward-looking operational statements when explicit cues are absent.
        for sentence in sentences:
            lowered = sentence.lower()
            if any(tok in lowered for tok in ("model", "system", "dynamics", "feedback", "adapt", "emergent")):
                prospectives.append(sentence)
                if len(prospectives) >= max_items:
                    break

    if not analogies:
        for sentence in sentences:
            lowered = sentence.lower()
            if any(tok in lowered for tok in ("map", "model", "pattern", "shows", "mirror", "signals")):
                analogies.append(sentence)
                if len(analogies) >= max_items:
                    break

    if not analogies and sentences:
        analogies.append(sentences[0])
    if not prospectives and sentences:
        prospectives.append(sentences[-1])

    return analogies, prospectives


def _clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _iter_jsonl(path: Path) -> Generator[Dict, None, None]:
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
                yield row


def _iter_csv(path: Path) -> Generator[Dict, None, None]:
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row:
                continue
            yield dict(row)


def _iter_text_blocks(path: Path, delimiter: str) -> Generator[Dict, None, None]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    parts = [p.strip() for p in raw.split(delimiter) if p.strip()]
    for idx, part in enumerate(parts, 1):
        lines = [l.strip() for l in part.splitlines() if l.strip()]
        if not lines:
            continue
        title = lines[0]
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        if not body:
            body = title
            title = f"entry_{idx}"
        yield {
            "title": title,
            "text": body,
        }


def _infer_format(path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    if suffix == ".csv":
        return "csv"
    if suffix in {".txt", ".md"}:
        return "text"
    return "jsonl"


def _iter_entries(path: Path, fmt: str, delimiter: str) -> Iterable[Dict]:
    if fmt == "jsonl":
        return _iter_jsonl(path)
    if fmt == "csv":
        return _iter_csv(path)
    return _iter_text_blocks(path, delimiter)


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

    checkpoint_path = output_path.with_suffix(output_path.suffix + ".story.checkpoint.json")
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

            if not title or not text:
                rejected += 1
                continue

            if len(text) < min_chars:
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
                checkpoint_path.write_text(
                    json.dumps(checkpoint_payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                if store_db:
                    upsert_import_run(
                        str(input_path),
                        "story_world_selective",
                        processed,
                        rejected,
                        last_title,
                        checkpoint_payload,
                        "running",
                    )
                print(f"  Checkpoint: {processed} processed, {accepted} accepted, {rejected} filtered")

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
    checkpoint_path.write_text(
        json.dumps(final_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if store_db:
        upsert_import_run(
            str(input_path),
            "story_world_selective",
            processed,
            rejected,
            last_title,
            final_payload,
            "complete",
        )
    return final_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Selectively ingest story-world text into the ecosystem.")
    parser.add_argument("--input", required=True, help="Path to JSONL, CSV, TXT, or MD source")
    parser.add_argument("--output", required=True, help="Path to JSONL output")
    parser.add_argument("--format", choices=["jsonl", "csv", "text"], default=None, help="Override input format")
    parser.add_argument("--threshold", type=float, default=0.40, help="Ecosystem fit threshold (0-1)")
    parser.add_argument("--source-label", default="story_world", help="Logical source label stored in output")
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

    print("\nSTORY WORLD -> ECOSYSTEM SELECTIVE IMPORT COMPLETE")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
