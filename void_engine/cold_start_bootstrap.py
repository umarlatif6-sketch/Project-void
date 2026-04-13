"""
Cold Start Bootstrap — Chronicle + Codon Packet Builder
========================================================

Purpose:
Create one deterministic bootstrap packet for memory-less AI agents.

Pipeline implemented here:
1. Read VOID_SEED_DIGEST.md (fallback: VOID_SEED.md)
2. Read the last N session entries from VOID_CHRONICLE.md (default 5)
3. Read files linked inside those Chronicle entries (markdown links + inline .md paths)
4. Compress the last M messages into codon triplets (default 5)
5. Emit one compact context packet + prebuilt prompt string

This mirrors the ritual in VOID_SEED.md section 15, but makes it executable.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
from void_engine.void_script import CANONICAL_GLYPHS

SESSION_HEADER_RE = re.compile(r"^##\s+SESSION\s+—\s+", re.MULTILINE)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
INLINE_MD_PATH_RE = re.compile(r"(?<![A-Za-z0-9_./-])([A-Za-z0-9_./-]+\.md)(?![A-Za-z0-9_./-])")


@dataclass
class ChronicleSession:
    header: str
    body: str

    @property
    def excerpt(self) -> str:
        text = self.body.strip().replace("\n", " ")
        return text[:420] + ("..." if len(text) > 420 else "")


@dataclass
class CodonPacket:
    glyph_seq: str
    entity: str
    condition: str
    action: str
    digest_286: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _role_glyphs(role: str) -> List[str]:
    return [g for g, m in CANONICAL_GLYPHS.items() if m.get("role") == role]


def _codon_for_text(text: str) -> CodonPacket:
    digest = fatiha_286_hexdigest_from_str(text)

    entities = _role_glyphs("entity")
    conditions = _role_glyphs("condition")
    actions = _role_glyphs("action")

    if not entities or not conditions or not actions:
        raise ValueError("Canonical glyph roles are incomplete")

    e_idx = int(digest[0:4], 16) % len(entities)
    c_idx = int(digest[4:8], 16) % len(conditions)
    a_idx = int(digest[8:12], 16) % len(actions)

    e = entities[e_idx]
    c = conditions[c_idx]
    a = actions[a_idx]

    return CodonPacket(
        glyph_seq=f"{e}·{c}·{a}",
        entity=e,
        condition=c,
        action=a,
        digest_286=digest,
    )


def _split_chronicle_sessions(chronicle_text: str) -> List[ChronicleSession]:
    matches = list(SESSION_HEADER_RE.finditer(chronicle_text))
    if not matches:
        return []

    sessions: List[ChronicleSession] = []
    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(chronicle_text)
        block = chronicle_text[start:end].strip()

        first_newline = block.find("\n")
        if first_newline == -1:
            header = block
            body = ""
        else:
            header = block[:first_newline].strip()
            body = block[first_newline + 1 :].strip()

        sessions.append(ChronicleSession(header=header, body=body))

    return sessions


def _extract_linked_paths(text: str) -> List[str]:
    links: List[str] = []

    for target in MARKDOWN_LINK_RE.findall(text):
        if target.startswith("http://") or target.startswith("https://"):
            continue
        if target.endswith(".md"):
            links.append(target)

    for target in INLINE_MD_PATH_RE.findall(text):
        links.append(target)

    unique: List[str] = []
    seen = set()
    for p in links:
        cleaned = p.strip().lstrip("./")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


def _read_linked_context(repo_root: Path, paths: List[str], max_chars: int = 1400) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for rel in paths:
        p = (repo_root / rel).resolve()
        try:
            p.relative_to(repo_root)
        except ValueError:
            continue

        if not p.exists() or not p.is_file():
            continue

        try:
            text = _read_text(p)
        except Exception:
            continue

        snippet = text[:max_chars].strip()
        out.append({
            "path": str(p.relative_to(repo_root)).replace("\\", "/"),
            "snippet": snippet,
        })
    return out


def _recent_git_activity(repo_root: Path, max_commits: int = 10) -> List[Dict[str, str]]:
    """Return recent local git commits for freshness context."""
    cmd = [
        "git",
        "log",
        f"--max-count={max_commits}",
        "--date=short",
        "--pretty=format:%h|%ad|%s",
    ]
    try:
        raw = subprocess.check_output(
            cmd,
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return []

    out: List[Dict[str, str]] = []
    for line in raw.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        out.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})
    return out


def build_cold_start_packet(
    last_messages: Optional[List[str]] = None,
    chronicle_entries: int = 5,
    message_codons: int = 5,
    include_linked_context: bool = True,
) -> Dict:
    """
    Build a deterministic cold-start packet for memory-less AI sessions.

    Args:
        last_messages: Recent dialogue/user messages to codon-compress.
        chronicle_entries: Number of most recent Chronicle sessions to include.
        message_codons: Number of most recent messages to codonize.
        include_linked_context: If True, read linked markdown sources from those sessions.

    Returns:
        Dict containing seed excerpt, chronicle tail, codon chain, and bootstrap prompt.
    """
    repo = _repo_root()

    seed_digest_path = repo / "VOID_SEED_DIGEST.md"
    seed_full_path = repo / "VOID_SEED.md"
    chronicle_path = repo / "VOID_CHRONICLE.md"

    seed_source = seed_digest_path if seed_digest_path.exists() else seed_full_path
    seed_text = _read_text(seed_source) if seed_source.exists() else ""

    chronicle_text = _read_text(chronicle_path) if chronicle_path.exists() else ""
    sessions = _split_chronicle_sessions(chronicle_text)
    tail = sessions[-chronicle_entries:] if chronicle_entries > 0 else []

    linked_paths: List[str] = []
    for s in tail:
        linked_paths.extend(_extract_linked_paths(f"{s.header}\n{s.body}"))

    # Also harvest linked docs from seed text so the packet remains useful
    # even when recent Chronicle entries contain no explicit markdown links.
    linked_paths.extend(_extract_linked_paths(seed_text[:6000]))

    # De-duplicate while preserving order
    dedup_paths: List[str] = []
    seen = set()
    for p in linked_paths:
        if p not in seen:
            seen.add(p)
            dedup_paths.append(p)

    linked_context = _read_linked_context(repo, dedup_paths) if include_linked_context else []
    recent_commits = _recent_git_activity(repo, max_commits=12)

    messages = last_messages or []
    codon_input = messages[-message_codons:] if message_codons > 0 else []
    codons = []
    for msg in codon_input:
        c = _codon_for_text(msg)
        codons.append(
            {
                "source": msg,
                "glyph_seq": c.glyph_seq,
                "entity": c.entity,
                "condition": c.condition,
                "action": c.action,
                "digest_286": c.digest_286,
            }
        )

    chronicle_payload = [
        {
            "header": s.header,
            "excerpt": s.excerpt,
        }
        for s in tail
    ]

    codon_chain = " | ".join(c["glyph_seq"] for c in codons) if codons else ""

    prompt_parts = [
        "[VOID COLD START PACKET]",
        "",
        f"Seed Source: {seed_source.name}",
        "Read this seed excerpt first:",
        seed_text[:1800].strip(),
        "",
        "Most recent Chronicle sessions:",
    ]

    for item in chronicle_payload:
        prompt_parts.append(f"- {item['header']}")
        prompt_parts.append(f"  {item['excerpt']}")

    if linked_context:
        prompt_parts.append("")
        prompt_parts.append("Linked context snippets:")
        for lc in linked_context[:8]:
            snippet = lc["snippet"].replace("\n", " ")[:280]
            prompt_parts.append(f"- {lc['path']}: {snippet}{'...' if len(lc['snippet']) > 280 else ''}")

    if codon_chain:
        prompt_parts.append("")
        prompt_parts.append(f"Recent message codon chain: {codon_chain}")

    if recent_commits:
        prompt_parts.append("")
        prompt_parts.append("Recent git activity:")
        for row in recent_commits[:5]:
            prompt_parts.append(f"- {row['date']} {row['hash']} {row['subject']}")

    prompt = "\n".join(prompt_parts)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed_source": str(seed_source.relative_to(repo)).replace("\\", "/") if seed_source.exists() else "",
        "seed_excerpt": seed_text[:1800],
        "chronicle_sessions": chronicle_payload,
        "linked_paths": dedup_paths,
        "linked_context": linked_context,
        "recent_git_activity": recent_commits,
        "message_codons": codons,
        "codon_chain": codon_chain,
        "bootstrap_prompt": prompt,
    }


def build_cold_start_packet_json(
    last_messages: Optional[List[str]] = None,
    chronicle_entries: int = 5,
    message_codons: int = 5,
    include_linked_context: bool = True,
) -> str:
    """JSON wrapper for easy API/CLI usage."""
    packet = build_cold_start_packet(
        last_messages=last_messages,
        chronicle_entries=chronicle_entries,
        message_codons=message_codons,
        include_linked_context=include_linked_context,
    )
    return json.dumps(packet, ensure_ascii=True, indent=2)


if __name__ == "__main__":
    demo_messages = [
        "Load my latest context from the chronicle.",
        "Summarize what changed in the last session.",
        "Compress this into codons.",
        "Anchor to 432 and produce a short handoff packet.",
        "What should the next agent do first?",
    ]
    print(build_cold_start_packet_json(last_messages=demo_messages))
