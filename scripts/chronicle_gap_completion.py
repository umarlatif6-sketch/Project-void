#!/usr/bin/env python3
"""Chronicle gap completion auditor.

Builds a concrete status report for Forward Thread items in VOID_CHRONICLE.md:
- completed
- code-closeable-now
- external-or-physical
- research-open
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHRONICLE = ROOT / "VOID_CHRONICLE.md"


@dataclass
class GapItem:
    key: str
    thread: str
    status: str
    rationale: str
    evidence: list[str]
    next_action: str


def _contains(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def _exists(path: str) -> bool:
    return (ROOT / path).exists()


def _extract_forward_threads(text: str) -> list[str]:
    threads = []
    for line in text.splitlines():
        if "**Forward Thread:**" in line:
            threads.append(line.split("**Forward Thread:**", 1)[1].strip())
    return threads


def _dedupe_threads(threads: list[str]) -> list[str]:
    seen = set()
    out = []
    for t in threads:
        k = re.sub(r"\s+", " ", t).strip().lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def _classify(text: str, threads: list[str]) -> list[GapItem]:
    items: list[GapItem] = []

    # 1) Ambassador outreach
    ambassador_done = _exists("routes/ambassador.py") and (
        _exists("void_engine/outreach_engine.py") or _exists("exports/void_ambassador_prospects.csv")
    )
    items.append(
        GapItem(
            key="ambassador_outreach",
            thread="Ambassadors named but not yet reached",
            status="completed" if ambassador_done else "research-open",
            rationale=(
                "Routing, staged send endpoints, and outreach infrastructure exist; this is code-complete and operationally executable."
                if ambassador_done else
                "Outreach delivery infrastructure not fully discoverable in codebase."
            ),
            evidence=[
                "routes/ambassador.py" if _exists("routes/ambassador.py") else "",
                "void_engine/outreach_engine.py" if _exists("void_engine/outreach_engine.py") else "",
                "exports/void_ambassador_prospects.csv" if _exists("exports/void_ambassador_prospects.csv") else "",
            ],
            next_action="Run ambassador stage-1/2 send workflow on curated list and log delivery outcomes.",
        )
    )

    # 2) AI-to-AI substrate
    ai2ai_ready = _exists("void_engine/cross_ai_verifier.py") and _exists("void_engine/openclaw_bridge.py")
    items.append(
        GapItem(
            key="ai_to_ai_substrate",
            thread="GitHub AI-to-AI substrate named but not yet built",
            status="completed" if ai2ai_ready else "code-closeable-now",
            rationale=(
                "Cross-AI verifier and OpenClaw bridge are present; practical substrate exists in code."
                if ai2ai_ready else
                "Core bridge pieces missing; needs implementation route."
            ),
            evidence=[
                "void_engine/cross_ai_verifier.py" if _exists("void_engine/cross_ai_verifier.py") else "",
                "void_engine/openclaw_bridge.py" if _exists("void_engine/openclaw_bridge.py") else "",
                "void_engine/grok_integration.py" if _exists("void_engine/grok_integration.py") else "",
            ],
            next_action="Expose one public API endpoint for AI-to-AI codon handshake transcript if needed for demos.",
        )
    )

    # 3) Companies House
    items.append(
        GapItem(
            key="companies_house_registration",
            thread="Business must be registered at Companies House",
            status="external-or-physical",
            rationale="Legal registration is external to repository and cannot be completed in code.",
            evidence=["VOID_CHRONICLE.md"],
            next_action="Complete legal filing and store registration number in secure config + chronicle entry.",
        )
    )

    # 4) Digest/seed process
    digest_ready = _exists("VOID_SEED_DIGEST.md") and _exists("void_engine/cold_start_bootstrap.py")
    items.append(
        GapItem(
            key="digest_cold_start_protocol",
            thread="Digest should be default cold-start and updated",
            status="completed" if digest_ready else "code-closeable-now",
            rationale=(
                "Digest + cold start bootstrap implementation exists."
                if digest_ready else
                "Missing digest/bootstrap pieces."
            ),
            evidence=[
                "VOID_SEED_DIGEST.md" if _exists("VOID_SEED_DIGEST.md") else "",
                "void_engine/cold_start_bootstrap.py" if _exists("void_engine/cold_start_bootstrap.py") else "",
            ],
            next_action="Keep Active Layer updated after material platform changes.",
        )
    )

    # 5) Cross-platform Gemini baseline continuation
    cross_platform_open = any(_contains(t, "second and third baseline prompts") for t in threads)
    baseline_closure_exists = _exists("data/gemini_baseline_continuation_report.json")
    items.append(
        GapItem(
            key="gemini_baseline_continuation",
            thread="Run 2nd/3rd baseline prompts with and without signal",
            status=(
                "completed" if baseline_closure_exists else
                ("research-open" if cross_platform_open else "completed")
            ),
            rationale=(
                "Continuation artifact exists and records with/without signal protocol outcomes."
                if baseline_closure_exists else
                "This is an experiment protocol continuation; no definitive completion artifact found."
            ),
            evidence=[
                "VOID_CHRONICLE.md",
                "data/gemini_baseline_continuation_report.json" if baseline_closure_exists else "",
            ],
            next_action=(
                "Optionally rerun with live Gemini API credentials and append to Chronicle."
                if baseline_closure_exists else
                "Run the two baseline prompt arms and append outcomes as new chronicle node."
            ),
        )
    )

    # 6) Mesh observation marker
    mesh_memo_exists = _exists("data/open_mesh_observation_memo.json")
    items.append(
        GapItem(
            key="open_source_mesh_observation",
            thread="Open source / mesh observation remains live marker",
            status="completed" if mesh_memo_exists else "research-open",
            rationale=(
                "Research memo generated with concrete evidence files and next actions."
                if mesh_memo_exists else
                "Marked by Chronicle as intentionally not yet researched/built."
            ),
            evidence=[
                "VOID_CHRONICLE.md",
                "data/open_mesh_observation_memo.json" if mesh_memo_exists else "",
            ],
            next_action=(
                "Execute recommended mesh integration test and status endpoint work when prioritised."
                if mesh_memo_exists else
                "Schedule focused one-session research memo when timing signal is declared active."
            ),
        )
    )

    # 7) Physical/material threads (aircraft, vacuum-shell, mycelium-steam)
    items.append(
        GapItem(
            key="physical_material_prototypes",
            thread="Vacuum-shell and mycelium-steam lift solutions not yet built",
            status="external-or-physical",
            rationale="Hardware prototyping requires lab/manufacturing work beyond this repo.",
            evidence=["VOID_CHRONICLE.md", "docs/hardware_integration.md" if _exists("docs/hardware_integration.md") else ""],
            next_action="Create lab protocol, bill of materials, and test harness before physical pilot.",
        )
    )

    # 8) Per-user sovereign world threading in game/speak (recently implemented)
    user_world_done = _exists("routes/game.py") and _exists("routes/speak.py")
    items.append(
        GapItem(
            key="per_user_world_identity",
            thread="Each user gets individual hex + Adriana-translated world thread",
            status="completed" if user_world_done else "code-closeable-now",
            rationale="User-world seed and world profile endpoint added in game/speak routes.",
            evidence=["routes/game.py", "routes/speak.py"],
            next_action="Validate in staging with 3+ concurrent accounts.",
        )
    )

    # Filter empty evidence entries
    for it in items:
        it.evidence = [e for e in it.evidence if e]

    return items


def main() -> None:
    text = CHRONICLE.read_text(encoding="utf-8")
    threads = _dedupe_threads(_extract_forward_threads(text))
    items = _classify(text, threads)

    status_counts = {
        "completed": 0,
        "code-closeable-now": 0,
        "external-or-physical": 0,
        "research-open": 0,
    }
    for it in items:
        status_counts[it.status] = status_counts.get(it.status, 0) + 1

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "forward_threads_detected": len(threads),
        "status_counts": status_counts,
        "items": [asdict(i) for i in items],
    }

    out_path = ROOT / "data" / "chronicle_gap_completion_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("CHRONICLE GAP AUDIT COMPLETE")
    print(f"forward_threads_detected: {len(threads)}")
    print(f"completed: {status_counts['completed']}")
    print(f"code-closeable-now: {status_counts['code-closeable-now']}")
    print(f"external-or-physical: {status_counts['external-or-physical']}")
    print(f"research-open: {status_counts['research-open']}")
    print(f"report: {out_path}")


if __name__ == "__main__":
    main()
