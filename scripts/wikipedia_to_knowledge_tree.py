#!/usr/bin/env python3
"""Stream Wikipedia content into the Tree of Knowledge.

Supports:
- MediaWiki XML dumps (.xml or .xml.bz2)
- Plain text files where each line is treated as one article body
- JSONL files with keys like title/text/extract/content

Output:
- JSONL rows containing title, source metadata, and Tree of Knowledge readout

Examples:
  python3 scripts/wikipedia_to_knowledge_tree.py \
    --input /path/to/enwiki-latest-pages-articles.xml.bz2 \
    --output data/wiki_tree_nodes.jsonl \
    --limit 1000

  python3 scripts/wikipedia_to_knowledge_tree.py \
    --input /path/to/sample.jsonl \
    --format jsonl \
    --output data/wiki_tree_nodes.jsonl
"""

from __future__ import annotations

import argparse
import bz2
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Generator, Iterable, Optional, TextIO, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from void_engine.knowledge_tree import three_brain_read
from void_engine.knowledge_tree_store import (
    get_import_run,
    init_knowledge_tree_tables,
    upsert_import_run,
    upsert_knowledge_tree_node,
)


WIKI_NS = "{http://www.mediawiki.org/xml/export-0.10/}"
TITLE_RE = re.compile(r"={2,}.*?={2,}")
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
TEMPLATE_RE = re.compile(r"\{\{.*?\}\}", re.DOTALL)
LINK_RE = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]")
EXTERNAL_LINK_RE = re.compile(r"\[(https?://[^\s\]]+)\s+([^\]]+)\]")
MULTISPACE_RE = re.compile(r"\s+")


def _open_text(path: Path) -> TextIO:
    if path.suffix == ".bz2":
        return bz2.open(path, "rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def _clean_wiki_text(text: str) -> str:
    text = REF_RE.sub(" ", text)
    text = TEMPLATE_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    text = EXTERNAL_LINK_RE.sub(r"\2", text)
    text = TAG_RE.sub(" ", text)
    text = TITLE_RE.sub(" ", text)
    text = text.replace("'''", " ").replace("''", " ")
    text = text.replace("&nbsp;", " ")
    text = MULTISPACE_RE.sub(" ", text)
    return text.strip()


def _extract_xml_pages(path: Path) -> Generator[Tuple[str, str], None, None]:
    with _open_text(path) as handle:
        context = ET.iterparse(handle, events=("end",))
        for _, elem in context:
            if elem.tag == f"{WIKI_NS}page":
                title = elem.findtext(f"{WIKI_NS}title") or ""
                ns = elem.findtext(f"{WIKI_NS}ns") or "0"
                redirect = elem.find(f"{WIKI_NS}redirect")
                revision = elem.find(f"{WIKI_NS}revision")
                text_node = revision.find(f"{WIKI_NS}text") if revision is not None else None
                raw_text = text_node.text if text_node is not None and text_node.text else ""

                if ns == "0" and redirect is None and raw_text.strip():
                    yield title, raw_text

                elem.clear()


def _extract_jsonl_rows(path: Path) -> Generator[Tuple[str, str], None, None]:
    with _open_text(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            title = row.get("title") or row.get("id") or "untitled"
            text = row.get("text") or row.get("extract") or row.get("content") or ""
            if text:
                yield str(title), str(text)


def _extract_plain_lines(path: Path) -> Generator[Tuple[str, str], None, None]:
    with _open_text(path) as handle:
        for index, line in enumerate(handle, 1):
            line = line.strip()
            if line:
                yield f"line_{index}", line


def _article_source(path: Path, fmt: str) -> Iterable[Tuple[str, str]]:
    if fmt == "xml":
        return _extract_xml_pages(path)
    if fmt == "jsonl":
        return _extract_jsonl_rows(path)
    return _extract_plain_lines(path)


def _infer_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".xml") or name.endswith(".xml.bz2"):
        return "xml"
    if name.endswith(".jsonl") or name.endswith(".ndjson"):
        return "jsonl"
    return "text"


def build_record(title: str, raw_text: str, source_name: str) -> Dict:
    cleaned = _clean_wiki_text(raw_text)
    result = three_brain_read(cleaned[:50000])
    return {
        "title": title,
        "source": source_name,
        "text_chars": len(cleaned),
        "preview": cleaned[:280],
        "tree": result,
    }


def _checkpoint_path(output_path: Path, override: Optional[Path]) -> Path:
    if override is not None:
        return override
    return output_path.with_suffix(output_path.suffix + ".checkpoint.json")


def _load_checkpoint(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_checkpoint(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolve_resume_state(input_path: Path, fmt: str, checkpoint_path: Path, resume: bool) -> Dict:
    state = {
        "processed": 0,
        "skipped": 0,
        "last_title": "",
        "status": "fresh",
    }
    if not resume:
        return state

    checkpoint = _load_checkpoint(checkpoint_path)
    import_run = get_import_run(str(input_path), fmt)
    candidate = checkpoint or (import_run or {}).get("checkpoint_payload") or import_run
    if not candidate:
        return state

    return {
        "processed": int(candidate.get("processed", candidate.get("processed_count", 0)) or 0),
        "skipped": int(candidate.get("skipped", candidate.get("skipped_count", 0)) or 0),
        "last_title": str(candidate.get("last_title", "") or ""),
        "status": str(candidate.get("status", "running") or "running"),
    }


def run(
    input_path: Path,
    output_path: Path,
    fmt: str,
    limit: int,
    store_db: bool,
    checkpoint_every: int,
    checkpoint_path: Optional[Path],
    resume: bool,
) -> Dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if store_db:
        init_knowledge_tree_tables()

    resolved_checkpoint = _checkpoint_path(output_path, checkpoint_path)
    resume_state = _resolve_resume_state(input_path, fmt, resolved_checkpoint, resume)
    skip_until_seen = bool(resume_state["last_title"])
    mode = "a" if resume and output_path.exists() else "w"

    processed = resume_state["processed"]
    skipped = resume_state["skipped"]
    written_this_run = 0
    last_title = resume_state["last_title"]

    with output_path.open(mode, encoding="utf-8") as out:
        for title, text in _article_source(input_path, fmt):
            if skip_until_seen:
                if title == resume_state["last_title"]:
                    skip_until_seen = False
                continue
            cleaned = _clean_wiki_text(text)
            if len(cleaned) < 200:
                skipped += 1
                continue
            record = build_record(title, text, input_path.name)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            if store_db:
                upsert_knowledge_tree_node(record)
            processed += 1
            written_this_run += 1
            last_title = title

            if checkpoint_every and processed % checkpoint_every == 0:
                checkpoint_payload = {
                    "input": str(input_path),
                    "format": fmt,
                    "processed": processed,
                    "skipped": skipped,
                    "last_title": last_title,
                    "status": "running",
                }
                _write_checkpoint(resolved_checkpoint, checkpoint_payload)
                if store_db:
                    upsert_import_run(str(input_path), fmt, processed, skipped, last_title, checkpoint_payload, "running")

            if limit and processed >= limit:
                break

    final_status = "complete"
    checkpoint_payload = {
        "input": str(input_path),
        "format": fmt,
        "processed": processed,
        "skipped": skipped,
        "last_title": last_title,
        "status": final_status,
    }
    _write_checkpoint(resolved_checkpoint, checkpoint_payload)
    if store_db:
        upsert_import_run(str(input_path), fmt, processed, skipped, last_title, checkpoint_payload, final_status)

    return {
        "input": str(input_path),
        "output": str(output_path),
        "checkpoint": str(resolved_checkpoint),
        "format": fmt,
        "processed": processed,
        "skipped": skipped,
        "written_this_run": written_this_run,
        "resumed": resume,
        "stored_in_db": store_db,
        "limit": limit,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Wikipedia-like content into Tree of Knowledge JSONL.")
    parser.add_argument("--input", required=True, help="Path to XML/XML.BZ2, JSONL, or text input")
    parser.add_argument("--output", required=True, help="Path to JSONL output")
    parser.add_argument("--format", choices=["xml", "jsonl", "text"], default=None, help="Override input format")
    parser.add_argument("--limit", type=int, default=0, help="Maximum articles to process (0 = no explicit limit)")
    parser.add_argument("--store-db", action="store_true", help="Persist extracted nodes into the knowledge tree database")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint/import-run state when available")
    parser.add_argument("--checkpoint-every", type=int, default=100, help="Write checkpoint state every N processed records")
    parser.add_argument("--checkpoint-file", default=None, help="Optional checkpoint JSON path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    fmt = args.format or _infer_format(input_path)
    summary = run(
        input_path,
        Path(args.output),
        fmt,
        args.limit,
        args.store_db,
        args.checkpoint_every,
        Path(args.checkpoint_file) if args.checkpoint_file else None,
        args.resume,
    )

    print("WIKIPEDIA TREE EXTRACTION COMPLETE")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
