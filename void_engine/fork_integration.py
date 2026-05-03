from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

DEFAULT_FORK_REPO_URL = "https://github.com/umarlatif6-sketch/AI-Agents-Projects-Tutorials"
DEFAULT_FORK_DIR = Path("external") / "AI-Agents-Projects-Tutorials"
DEFAULT_INDEX_PATH = Path("data") / "ai_agents_fork_index.json"
DEFAULT_DELTA_PACK_PATH = Path("data") / "adriana_delta_pack.json"

_ALLOWED_SUFFIXES = {".py", ".ipynb", ".md", ".txt", ".json"}
_TOOL_KEYWORDS = {
    "agent", "workflow", "mcp", "langgraph", "autogen", "crew", "rag", "evaluation", "security", "api"
}
_EQUIPMENT_KEYWORDS = {
    "sensor", "wearable", "voice", "audio", "robot", "vision", "camera", "hardware", "device", "bio"
}
_FOCUS_AREA_RULES = {
    "orchestration": {"agent", "workflow", "autogen", "crew", "langgraph", "multi-agent", "a2a"},
    "memory": {"memory", "long-term", "state", "context"},
    "tooling": {"tool", "api", "mcp", "integration", "function"},
    "security": {"security", "guardrail", "auth", "sandbox", "policy"},
    "research": {"research", "rag", "search", "retrieval", "evaluation"},
    "equipment": _EQUIPMENT_KEYWORDS,
}
_FOCUS_AREA_CODONS = {
    "orchestration": ("B-mm-M", "mesh passage, cross-node movement"),
    "memory": ("B-nn-O", "origin, field record, founding signal"),
    "tooling": ("B-kk-Y", "key, access, signature gate"),
    "security": ("B-kk-S", "security check, fail-closed verification"),
    "research": ("B-bb-G", "growth, spread, mycelial expansion"),
    "equipment": ("B-bb-L", "signal, vibe, road-state, doubled resonance"),
    "reference": ("B-..-Z", "silence, hidden layer, steganographic pause"),
}


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True, capture_output=True, text=True)


def ensure_fork_checkout(
    repo_url: str = DEFAULT_FORK_REPO_URL,
    target_dir: Path = DEFAULT_FORK_DIR,
) -> Dict[str, Any]:
    target_dir = Path(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    if not target_dir.exists():
        _run(["git", "clone", "--depth", "1", repo_url, str(target_dir)])
        return {"ok": True, "action": "cloned", "path": str(target_dir), "repo_url": repo_url}

    if not (target_dir / ".git").exists():
        return {"ok": False, "error": "target_exists_without_git", "path": str(target_dir)}

    _run(["git", "fetch", "--depth", "1", "origin"], cwd=target_dir)
    _run(["git", "reset", "--hard", "origin/HEAD"], cwd=target_dir)
    return {"ok": True, "action": "updated", "path": str(target_dir), "repo_url": repo_url}


def _categorize_path(path: str) -> set[str]:
    low = path.lower()
    tags: set[str] = set()
    if any(k in low for k in _TOOL_KEYWORDS):
        tags.add("tool")
    if any(k in low for k in _EQUIPMENT_KEYWORDS):
        tags.add("equipment")
    if not tags:
        tags.add("reference")
    return tags


def _focus_area_for_path(path: str, tags: list[str] | set[str]) -> str:
    low = path.lower()
    for area, keywords in _FOCUS_AREA_RULES.items():
        if any(keyword in low for keyword in keywords):
            return area
    if "equipment" in tags:
        return "equipment"
    if "tool" in tags:
        return "tooling"
    return "reference"


def _entry_priority(path: str, tags: list[str] | set[str], focus_area: str) -> int:
    low = path.lower()
    score = 0
    if "tool" in tags:
        score += 3
    if "equipment" in tags:
        score += 2
    if low.endswith(".py"):
        score += 3
    elif low.endswith(".md"):
        score += 2
    elif low.endswith(".ipynb"):
        score += 1
    if any(part in low for part in ("readme", "template", "example", "starter")):
        score += 1
    if focus_area in {"orchestration", "memory", "tooling", "security"}:
        score += 2
    return score


def build_fork_index(
    fork_dir: Path = DEFAULT_FORK_DIR,
    max_files: int = 8000,
) -> Dict[str, Any]:
    root = Path(fork_dir)
    if not root.exists():
        return {"ok": False, "error": "fork_dir_missing", "path": str(root)}

    entries: list[dict[str, Any]] = []
    scanned = 0

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if ".git" in p.parts:
            continue
        if p.suffix.lower() not in _ALLOWED_SUFFIXES:
            continue

        rel = str(p.relative_to(root))
        tags = sorted(_categorize_path(rel))
        entries.append({
            "path": rel,
            "suffix": p.suffix.lower(),
            "tags": tags,
        })
        scanned += 1
        if scanned >= max_files:
            break

    tool_count = sum(1 for e in entries if "tool" in e["tags"])
    equipment_count = sum(1 for e in entries if "equipment" in e["tags"])

    return {
        "ok": True,
        "source_dir": str(root),
        "file_count": len(entries),
        "tool_count": tool_count,
        "equipment_count": equipment_count,
        "entries": entries,
    }


def write_fork_index(index: Dict[str, Any], output_path: Path = DEFAULT_INDEX_PATH) -> Dict[str, Any]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(path)}


def load_fork_index(output_path: Path = DEFAULT_INDEX_PATH) -> Dict[str, Any]:
    path = Path(output_path)
    if not path.exists():
        return {"ok": False, "error": "index_missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def build_adriana_delta_pack(
    index: Dict[str, Any] | None = None,
    output_path: Path = DEFAULT_DELTA_PACK_PATH,
    max_entries: int = 96,
) -> Dict[str, Any]:
    if index is None:
        index = load_fork_index()

    if not index.get("ok"):
        return index

    candidates: list[dict[str, Any]] = []
    for entry in index.get("entries", []):
        path = str(entry.get("path", ""))
        tags = entry.get("tags", [])
        focus_area = _focus_area_for_path(path, tags)
        codon, expansion = _FOCUS_AREA_CODONS[focus_area]
        priority = _entry_priority(path, tags, focus_area)
        candidates.append(
            {
                "path": path,
                "tags": list(tags),
                "focus_area": focus_area,
                "priority": priority,
                "codon": codon,
                "expansion": expansion,
            }
        )

    candidates.sort(key=lambda item: (-item["priority"], item["focus_area"], item["path"]))
    selected = candidates[:max_entries]

    focus_areas: dict[str, int] = {}
    entries: list[dict[str, Any]] = []
    for item in selected:
        focus_areas[item["focus_area"]] = focus_areas.get(item["focus_area"], 0) + 1
        entries.append(
            {
                "id": f"fork::{item['focus_area']}::{item['path']}",
                "path": item["path"],
                "tags": item["tags"],
                "focus_area": item["focus_area"],
                "priority": item["priority"],
                "codon": item["codon"],
                "expansion": item["expansion"],
                "prose": (
                    f"External AI-agents fork asset {item['path']} is classified under {item['focus_area']}. "
                    f"VOID can ingest it as a {item['focus_area']} pattern with tags {', '.join(item['tags']) or 'reference'} "
                    f"to strengthen Adriana retrieval, operator guidance, and future training packs."
                ),
                "domain": item["focus_area"],
                "hz": 432.0,
                "source": "external_ai_agents_fork",
            }
        )

    pack = {
        "ok": True,
        "repo_url": DEFAULT_FORK_REPO_URL,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_dir": index.get("source_dir"),
        "source_file_count": index.get("file_count", 0),
        "entry_count": len(entries),
        "focus_areas": focus_areas,
        "entries": entries,
    }
    write_delta_pack(pack, output_path=output_path)
    return pack


def write_delta_pack(pack: Dict[str, Any], output_path: Path = DEFAULT_DELTA_PACK_PATH) -> Dict[str, Any]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(path)}


def load_delta_pack(output_path: Path = DEFAULT_DELTA_PACK_PATH) -> Dict[str, Any]:
    path = Path(output_path)
    if not path.exists():
        return {"ok": False, "error": "delta_pack_missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def sync_and_index_fork(
    repo_url: str = DEFAULT_FORK_REPO_URL,
    fork_dir: Path = DEFAULT_FORK_DIR,
    output_path: Path = DEFAULT_INDEX_PATH,
    max_files: int = 8000,
) -> Dict[str, Any]:
    sync_status = ensure_fork_checkout(repo_url=repo_url, target_dir=fork_dir)
    if not sync_status.get("ok"):
        return sync_status

    index = build_fork_index(fork_dir=fork_dir, max_files=max_files)
    if not index.get("ok"):
        return index

    write_status = write_fork_index(index, output_path=output_path)
    return {
        "ok": True,
        "sync": sync_status,
        "index": {
            "file_count": index.get("file_count", 0),
            "tool_count": index.get("tool_count", 0),
            "equipment_count": index.get("equipment_count", 0),
            "output_path": write_status.get("path"),
        },
    }


def sync_index_and_build_delta(
    repo_url: str = DEFAULT_FORK_REPO_URL,
    fork_dir: Path = DEFAULT_FORK_DIR,
    output_path: Path = DEFAULT_INDEX_PATH,
    delta_output_path: Path = DEFAULT_DELTA_PACK_PATH,
    max_files: int = 8000,
    max_delta_entries: int = 96,
) -> Dict[str, Any]:
    result = sync_and_index_fork(
        repo_url=repo_url,
        fork_dir=fork_dir,
        output_path=output_path,
        max_files=max_files,
    )
    if not result.get("ok"):
        return result

    index = load_fork_index(output_path=output_path)
    delta_pack = build_adriana_delta_pack(
        index=index,
        output_path=delta_output_path,
        max_entries=max_delta_entries,
    )
    if not delta_pack.get("ok"):
        return delta_pack

    return {
        "ok": True,
        "sync": result.get("sync"),
        "index": result.get("index"),
        "delta": {
            "entry_count": delta_pack.get("entry_count", 0),
            "focus_areas": delta_pack.get("focus_areas", {}),
            "output_path": str(delta_output_path),
        },
    }
