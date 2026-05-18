#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_results(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not data:
        raise ValueError("input_results_invalid_or_empty")
    return data


def _slice_results(data: dict, max_fields: int, max_per_field: int) -> dict:
    out: dict = {}
    for i, (field, entries) in enumerate(data.items()):
        if i >= max_fields:
            break
        if not isinstance(entries, list):
            continue
        out[field] = entries[:max_per_field]
    if not out:
        raise ValueError("no_valid_results_after_slice")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run an end-to-end Internet Window demo: capture -> encode -> verify."
    )
    parser.add_argument(
        "--input",
        default="data/resonance_web/session_001_results.json",
        help="Path to resonance search results JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/internet_windows",
        help="Directory for output artifacts.",
    )
    parser.add_argument(
        "--name",
        default="DEMO_WINDOW_001",
        help="Base name for generated files.",
    )
    parser.add_argument(
        "--max-fields",
        type=int,
        default=4,
        help="Max concept fields to include.",
    )
    parser.add_argument(
        "--max-per-field",
        type=int,
        default=5,
        help="Max entries per concept field.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing output files.",
    )

    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        print("error: ffmpeg_not_found", file=sys.stderr)
        print("install ffmpeg and re-run the demo.", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    input_path = (root / args.input).resolve()
    out_dir = (root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    video_path = out_dir / f"{args.name}.mkv"
    report_path = out_dir / f"{args.name}_report.json"

    if not input_path.exists():
        print(f"error: input_not_found: {input_path}", file=sys.stderr)
        return 2

    if not args.overwrite and (video_path.exists() or report_path.exists()):
        print("error: output_exists_use_overwrite", file=sys.stderr)
        print(f"video: {video_path}", file=sys.stderr)
        print(f"report: {report_path}", file=sys.stderr)
        return 2

    # Import here so this script can fail fast on preflight checks first.
    from void_engine.internet_window import create_window_from_session, verify_window_integrity

    raw = _load_results(input_path)
    sliced = _slice_results(raw, max_fields=args.max_fields, max_per_field=args.max_per_field)

    source_concepts = list(sliced.keys())
    session_name = f"internet_window_demo::{args.name}"

    created_path = create_window_from_session(
        session_results=sliced,
        session_name=session_name,
        source_concepts=source_concepts,
        output_path=str(video_path),
    )

    integrity = verify_window_integrity(created_path)
    file_size = video_path.stat().st_size
    index_path = Path(str(video_path).rsplit(".", 1)[0] + "_index.json")

    report = {
        "ok": bool(integrity.get("hash_match") and integrity.get("all_pages_intact")),
        "generated_at": _utc_now(),
        "input": str(input_path),
        "video": str(video_path),
        "index": str(index_path),
        "video_size_bytes": file_size,
        "source_concepts": source_concepts,
        "integrity": integrity,
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("Internet Window demo complete")
    print(f"video:  {video_path}")
    print(f"index:  {index_path}")
    print(f"report: {report_path}")
    print(f"ok:     {report['ok']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
