#!/usr/bin/env python3
"""Autofill missing Forward Thread lines in VOID_CHRONICLE session blocks.

This is a continuity hardening utility for historical sessions that were recorded
without explicit inherited-thread lines.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHRONICLE = ROOT / "VOID_CHRONICLE.md"
FORWARD_PREFIX = "**Forward Thread:**"


def _session_title(header_line: str) -> str:
    return re.sub(r"^##\s*SESSION\s*[—-]\s*", "", header_line.strip(), flags=re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description="Autofill missing Chronicle Forward Thread lines")
    parser.add_argument("--write", action="store_true", help="Write changes to file")
    args = parser.parse_args()

    lines = CHRONICLE.read_text(encoding="utf-8").splitlines()

    session_indices = [i for i, line in enumerate(lines) if line.startswith("## SESSION")]
    if not session_indices:
        print("No session headers found.")
        return 0

    additions = []
    for idx, start in enumerate(session_indices):
        end = session_indices[idx + 1] if idx + 1 < len(session_indices) else len(lines)
        block = lines[start:end]
        has_forward = any(FORWARD_PREFIX in line for line in block)
        if has_forward:
            continue

        title = _session_title(lines[start])
        forward_line = (
            f"{FORWARD_PREFIX} Continuity note for \"{title}\": this archived session lacked an explicit inherited thread; "
            "carry unresolved work forward with explicit closure criteria in the next related session node."
        )
        insert_at = end
        additions.append((insert_at, forward_line))

    print(f"sessions_total: {len(session_indices)}")
    print(f"missing_forward_threads: {len(additions)}")

    if not args.write:
        print("dry_run: true")
        return 0

    # Insert from bottom to top so indices remain valid.
    for insert_at, text in reversed(additions):
        lines.insert(insert_at, "")
        lines.insert(insert_at + 1, text)

    CHRONICLE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("write: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
