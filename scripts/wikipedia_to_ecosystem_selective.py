#!/usr/bin/env python3
"""
Selective Wikipedia → Ecosystem Importer

Only ingest Wikipedia articles that resonate with the 19 core domains 
Project VOID operates within. This turns Wikipedia from a raw bulk source 
into an intelligent evolution feed — only pulling what the ecosystem needs.

The 19 core domains:
1. Acoustic/Frequency (432 Hz, resonance, vibration, tone)
2. Cryptography & Identity (hashing, sovereignty, proof, secrets)
3. Biology & Life Systems (mycelium, DNA, neurons, growth patterns)
4. Economics & Value (tokens, pricing, exchange, incentives)
5. Theology & Names (divine attributes, meaning, sacred structure)
6. Narrative & Time (chronicle, history, causality, records)
7. Network & Mesh (Beehive, mycelium, graph, topology, routing)
8. Information Theory (steganography, encoding, layers, lossy compression)
9. Mathematics & Ratios (sacred geometry, Fibonacci, golden ratio, primes)
10. Law & Rights (jurisdiction, warranty, contract, obligation)
11. Language & Meaning (Adriana, SCL, glyphs, interpretation, semantics)
12. Neurology & Brains (three-brain model, neural patterns, cognition)
13. Physics & Waves (vibration, oscillation, wave function, nodes)
14. Identity & Markers (codon, hex, glyph, fingerprint, signature)
15. Ritual & Cycles (ceremony, rhythm, repetition, periodicity)
16. Movement & Formation (dance, swarm, pattern, choreography, topology)
17. Hydrology & Flow (water, capillary, pressure, osmosis, permeability)
18. Optics & Light (visibility, transparency, refraction, clarity, signal)
19. Harmony & Consonance (pitch, tuning, resonance, dissonance, chord)

Usage:
  python3 scripts/wikipedia_to_ecosystem_selective.py \
    --input /path/to/enwiki-latest-pages-articles.xml.bz2 \
    --output data/ecosystem_feed.jsonl \
    --threshold 0.5 \
    --store-db \
    --resume
"""

from __future__ import annotations

import argparse
import bz2
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Generator, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from void_engine.knowledge_tree import three_brain_read
from void_engine.knowledge_tree_store import (
    get_import_run,
    init_knowledge_tree_tables,
    upsert_import_run,
    upsert_knowledge_tree_node,
)


# ─── 19 core domains with keyword signatures ────────────────────────────────

ECOSYSTEM_DOMAINS = {
    "acoustic_frequency": {
        "keywords": ["frequency", "hz", "vibration", "tone", "pitch", "resonance", 
                     "hertz", "oscillation", "sound wave", "432", "tuning"],
        "weight": 1.0,
    },
    "cryptography_identity": {
        "keywords": ["hash", "encryption", "cryptography", "proof", "private key", 
                     "signature", "blockchain", "ledger", "covenant", "sovereign",
                     "286", "al-jabr"],
        "weight": 1.0,
    },
    "biology_life": {
        "keywords": ["mycelium", "fungi", "dna", "neural", "neuron", "organism", 
                     "life", "growth", "cell", "biology", "genetics", "symbiosis",
                     "network", "organism"],
        "weight": 0.9,
    },
    "economics_value": {
        "keywords": ["token", "economy", "price", "exchange", "value", "currency", 
                     "vault", "cost", "transaction", "wallet", "incentive", "market"],
        "weight": 0.8,
    },
    "theology_names": {
        "keywords": ["divine", "sacred", "attribute", "name", "quran", "allah", 
                     "islam", "theology", "meaning", "spiritual", "surah", "ninety-nine"],
        "weight": 0.9,
    },
    "narrative_time": {
        "keywords": ["chronicle", "history", "record", "narrative", "time", "causality", 
                     "sequence", "event", "story", "past", "memory", "timeline"],
        "weight": 0.7,
    },
    "network_mesh": {
        "keywords": ["network", "mesh", "topology", "graph", "routing", "beehive", 
                     "node", "connection", "path", "link", "graph theory"],
        "weight": 1.0,
    },
    "information_theory": {
        "keywords": ["encoding", "compression", "steganography", "information", 
                     "data", "layer", "signal", "noise", "entropy", "codon", "glyph"],
        "weight": 0.9,
    },
    "mathematics_ratio": {
        "keywords": ["fibonacci", "golden ratio", "geometry", "prime", "number", 
                     "ratio", "proportion", "symmetry", "pattern", "constant"],
        "weight": 0.8,
    },
    "law_rights": {
        "keywords": ["law", "contract", "rights", "jurisdiction", "warranty", 
                     "legal", "obligation", "covenant", "agreement"],
        "weight": 0.6,
    },
    "language_meaning": {
        "keywords": ["language", "semantic", "meaning", "glyph", "word", "symbol", 
                     "alphabet", "interpretation", "intent", "adriana"],
        "weight": 0.8,
    },
    "neurology_brain": {
        "keywords": ["brain", "neural", "neuron", "cognition", "thought", "mind", 
                     "consciousness", "thinking", "perception", "synapse"],
        "weight": 0.8,
    },
    "physics_wave": {
        "keywords": ["wave", "oscillation", "frequency", "vibration", "chladni", 
                     "node", "antinode", "physics", "motion", "force"],
        "weight": 0.9,
    },
    "identity_marker": {
        "keywords": ["identifier", "fingerprint", "signature", "codon", "hex", 
                     "code", "unique", "marker", "label", "address"],
        "weight": 0.8,
    },
    "ritual_cycle": {
        "keywords": ["ritual", "ceremony", "cycle", "rhythm", "repetition", "periodic", 
                     "pattern", "circadian", "standard", "protocol"],
        "weight": 0.7,
    },
    "movement_formation": {
        "keywords": ["dance", "movement", "formation", "swarm", "behavior", "choreography", 
                     "pattern", "coordination", "synchrony", "tawaf"],
        "weight": 0.8,
    },
    "hydrology_flow": {
        "keywords": ["water", "flow", "capillary", "osmosis", "pressure", "current", 
                     "stream", "river", "aquifer", "permeability"],
        "weight": 0.6,
    },
    "optics_light": {
        "keywords": ["light", "optical", "visible", "transparent", "reflection", 
                     "refraction", "clarity", "brightness", "photon"],
        "weight": 0.6,
    },
    "harmony_consonance": {
        "keywords": ["harmony", "chord", "consonant", "dissonant", "pitch", "tone", 
                     "tuning", "scale", "musical", "resonance"],
        "weight": 0.9,
    },
}


def _open_text(path: Path):
    if path.suffix == ".bz2":
        return bz2.open(path, "rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def _clean_wiki_text(text: str) -> str:
    """Clean Wikipedia markup."""
    ref_re = re.compile(r"<ref[^>]*>.*?</ref>", re.IGNORECASE | re.DOTALL)
    template_re = re.compile(r"\{\{.*?\}\}", re.DOTALL)
    link_re = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]")
    external_re = re.compile(r"\[(https?://[^\s\]]+)\s+([^\]]+)\]")
    tag_re = re.compile(r"<[^>]+>")
    title_re = re.compile(r"={2,}.*?={2,}")
    multispace_re = re.compile(r"\s+")

    text = ref_re.sub(" ", text)
    text = template_re.sub(" ", text)
    text = link_re.sub(r"\1", text)
    text = external_re.sub(r"\2", text)
    text = tag_re.sub(" ", text)
    text = title_re.sub(" ", text)
    text = text.replace("'''", " ").replace("''", " ")
    text = text.replace("&nbsp;", " ")
    text = multispace_re.sub(" ", text)
    return text.strip()


def _extract_xml_pages(path: Path) -> Generator[Tuple[str, str], None, None]:
    """Extract Wikipedia XML pages."""
    WIKI_NS = "{http://www.mediawiki.org/xml/export-0.10/}"
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


def _extract_jsonl_pages(path: Path) -> Generator[Tuple[str, str], None, None]:
    """Extract from JSONL (title, text)."""
    with _open_text(path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                title = row.get("title", "")
                text = row.get("text", "")
                if title and text:
                    yield str(title), str(text)
            except json.JSONDecodeError:
                pass


def _infer_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".xml") or name.endswith(".xml.bz2"):
        return "xml"
    if name.endswith(".jsonl") or name.endswith(".ndjson"):
        return "jsonl"
    return "text"


def _extract_pages(path: Path, fmt: str) -> Generator[Tuple[str, str], None, None]:
    """Extract pages from input based on format."""
    if fmt == "xml":
        yield from _extract_xml_pages(path)
    elif fmt == "jsonl":
        yield from _extract_jsonl_pages(path)
    else:
        # Plain text: treat each line as independent article
        with _open_text(path) as handle:
            for idx, line in enumerate(handle, 1):
                line = line.strip()
                if line:
                    yield f"line_{idx}", line


def score_against_domain(text: str, domain_name: str, keywords: list[str]) -> float:
    """
    Score text against a domain's keyword signature.
    Returns a float 0-1 indicating resonance with the domain.
    """
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    max_matches = len(keywords)
    return min(1.0, matches / max(1, max_matches * 0.5))  # Normalize


def score_article(title: str, text: str) -> Dict[str, float]:
    """
    Score an article across all 19 ecosystem domains.
    Returns a dict with domain names and their resonance scores.
    """
    combined = f"{title} {text}"
    scores = {}
    for domain_name, domain_data in ECOSYSTEM_DOMAINS.items():
        domain_score = score_against_domain(combined, domain_name, domain_data["keywords"])
        weighted_score = domain_score * domain_data["weight"]
        scores[domain_name] = weighted_score
    return scores


def calculate_ecosystem_fit(scores: Dict[str, float], threshold: float = 0.5) -> Tuple[float, bool]:
    """
    Calculate overall ecosystem fit score and whether article should be imported.

    An article is imported if:
    - It scores high on at least 2 domains (compound resonance)
    - OR one domain score exceeds threshold by a margin
    """
    sorted_scores = sorted(scores.values(), reverse=True)
    
    # Top domain score
    top_score = sorted_scores[0] if sorted_scores else 0.0
    
    # Second domain score (compound resonance)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
    
    # Fitness: can be high via one strong domain OR two moderate domains
    fit = max(
        top_score,
        (top_score + second_score) / 2 if second_score > 0 else 0,
    )
    
    should_import = fit >= threshold
    return fit, should_import


def run(
    input_path: Path,
    output_path: Path,
    fmt: str = "xml",
    threshold: float = 0.5,
    store_db: bool = False,
    resume: bool = False,
    limit: int = 0,
) -> Dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if store_db:
        init_knowledge_tree_tables()

    checkpoint_path = output_path.with_suffix(output_path.suffix + ".eco.checkpoint.json")
    resume_state = {}
    if resume and checkpoint_path.exists():
        try:
            resume_state = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    mode = "a" if resume and output_path.exists() else "w"
    processed, accepted, rejected = resume_state.get("processed", 0), resume_state.get("accepted", 0), resume_state.get("rejected", 0)
    skip_until_seen = bool(resume_state.get("last_title", ""))
    last_title = resume_state.get("last_title", "")

    with output_path.open(mode, encoding="utf-8") as out:
        for title, raw_text in _extract_pages(input_path, fmt):
            if skip_until_seen:
                if title == last_title:
                    skip_until_seen = False
                continue

            cleaned = _clean_wiki_text(raw_text)
            if len(cleaned) < 300:  # Higher threshold for selective mode
                rejected += 1
                continue

            # Score against ecosystem domains
            domain_scores = score_article(title, cleaned)
            fit_score, should_import = calculate_ecosystem_fit(domain_scores, threshold)

            if should_import:
                # Ingest this article
                result = three_brain_read(cleaned[:50000])
                record = {
                    "title": title,
                    "source": "wikipedia_selective",
                    "text_chars": len(cleaned),
                    "preview": cleaned[:280],
                    "tree": result,
                    "ecosystem_fit": fit_score,
                    "domain_scores": domain_scores,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                if store_db:
                    upsert_knowledge_tree_node(record)
                accepted += 1
            else:
                rejected += 1

            processed += 1
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
                }
                checkpoint_path.write_text(json.dumps(checkpoint_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                if store_db:
                    upsert_import_run(str(input_path), "wikipedia_selective", processed, rejected, last_title, checkpoint_payload, "running")
                print(f"  Checkpoint: {processed} processed, {accepted} accepted, {rejected} filtered")

            if limit and accepted >= limit:
                break

    final_payload = {
        "input": str(input_path),
        "output": str(output_path),
        "threshold": threshold,
        "processed": processed,
        "accepted": accepted,
        "rejected": rejected,
        "acceptance_rate": round(100 * accepted / max(1, processed), 2),
        "status": "complete",
    }
    checkpoint_path.write_text(json.dumps(final_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if store_db:
        upsert_import_run(str(input_path), "wikipedia_selective", processed, rejected, last_title, final_payload, "complete")

    return final_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Selectively ingest Wikipedia into the ecosystem.")
    parser.add_argument("--input", required=True, help="Path to XML/XML.BZ2, JSONL, or text Wikipedia dump")
    parser.add_argument("--output", required=True, help="Path to JSONL output")
    parser.add_argument("--format", choices=["xml", "jsonl", "text"], default=None, help="Override input format")
    parser.add_argument("--threshold", type=float, default=0.5, help="Ecosystem fit threshold (0-1)")
    parser.add_argument("--store-db", action="store_true", help="Persist to knowledge tree database")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--limit", type=int, default=0, help="Max articles to accept (0=no limit)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    fmt = args.format or _infer_format(input_path)
    summary = run(input_path, Path(args.output), fmt, args.threshold, args.store_db, args.resume, args.limit)

    print("\nWIKIPEDIA → ECOSYSTEM SELECTIVE IMPORT COMPLETE")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
