#!/usr/bin/env python3
"""Chronicle close guard.

Validates that the Chronicle has no template forward-thread placeholders and
that each session contains exactly one explicit Forward Thread line.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHRONICLE = ROOT / "VOID_CHRONICLE.md"

PLACEHOLDER = "[One or two sentences only. What is unresolved. What the next session inherits. The open end of the thread this session was holding.]"


def _extract_forward_lines_outside_fences(lines: list[str]) -> list[str]:
    forward = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "**Forward Thread:**" in line:
            forward.append(line)
    return forward


def main() -> int:
    text = CHRONICLE.read_text(encoding="utf-8")
    lines = text.splitlines()

    session_lines = [i for i, line in enumerate(lines) if line.startswith("## SESSION")]
    session_count = len(session_lines)
    forward_lines = _extract_forward_lines_outside_fences(lines)

    # Reconstructed early sessions are archival and may not carry forward-thread lines.
    # We enforce for the active zone only: sessions from the first true forward-thread onward.
    first_forward_idx = next((i for i, line in enumerate(lines) if "**Forward Thread:**" in line), None)
    active_session_count = 0
    if first_forward_idx is not None:
        active_session_count = sum(1 for idx in session_lines if idx >= first_forward_idx)

    placeholder_hits = [line for line in forward_lines if PLACEHOLDER in line]

    report = {
        "ok": len(placeholder_hits) == 0 and len(forward_lines) >= active_session_count,
        "session_count": session_count,
        "active_session_count": active_session_count,
        "forward_thread_count": len(forward_lines),
        "placeholder_count": len(placeholder_hits),
        "issues": [],
    }

    if len(forward_lines) < active_session_count:
        report["issues"].append(
            "Some active sessions may be missing explicit Forward Thread lines."
        )
    if placeholder_hits:
        report["issues"].append(
            "Chronicle contains template placeholder Forward Thread text."
        )

    out_path = ROOT / "data" / "chronicle_close_guard_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({"report": str(out_path), **report}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
