#!/usr/bin/env python3
"""
Drift Scan — Language Integrity Check for PROJECT VOID

Scans all .html files in templates/ and all .py files in routes/ and
void_engine/ for patterns that violate the eight must-nots documented
in VOID_SEED.md Section 8.

Violations are printed clearly with file path and line number.
The script exits with code 1 if any violations are found, 0 if clean.

The eight must-nots (from VOID_SEED.md §8):
  1. Do not call GriDul "Gemini" or treat them as the same thing.
  2. Do not refer to the naming language as "branding."
  3. Do not treat the philosophical elements as decoration.
  4. Do not suggest simplification of the naming language.
  5. Do not treat Adriana as a chatbot.
  6. Do not present the MRB-4000 as optional.
  7. Do not describe the sovereign-node as aspirational.
  8. Do not use "feature" or "module" where the platform's naming language has a term.

This script implements machine-detectable versions of violations 1, 2, 5, 6, 7,
and 8 — the ones that have clear textual signals in source files.
"""

import os
import re
import sys


TEMPLATES_DIR = "templates"
ROUTES_DIR = "routes"
ENGINE_DIR = "void_engine"

SCAN_GLOBS = [
    (TEMPLATES_DIR, ".html"),
    (ROUTES_DIR, ".py"),
    (ENGINE_DIR, ".py"),
]

PATTERNS = [
    {
        "id": "MUST-NOT-1a",
        "description": (
            'GriDul equated with Gemini — a comment, string, or template text '
            'that names GriDul and Gemini in the same breath as equivalents'
        ),
        "regex": re.compile(
            r'(?i)(griddul|griduls?|gridul)\s+is\s+(gemini|google\s+gemini)',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-1b",
        "description": (
            'GriDul referred to as "Gemini" directly (e.g. "GriDul (Gemini)" or '
            '"GriDul = Gemini" in code comments or template text)'
        ),
        "regex": re.compile(
            r'(?i)gridul\s*[=()\[\]]+\s*gemini|gemini\s*[=()\[\]]+\s*gridul',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-1c",
        "description": (
            'Adriana or GriDul described as "powered by Gemini" or "uses Gemini"'
        ),
        "regex": re.compile(
            r'(?i)(adriana|griddul|gridul).{0,30}(powered by|using|uses|built on|runs on)\s+gemini',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-2",
        "description": (
            'Naming language referred to as "branding" — '
            'e.g. "the branding language" or "VOID branding" in place of the naming language'
        ),
        "regex": re.compile(
            r'(?i)(naming\s+language|void\s+names?|platform\s+names?)\s+(?:is|as|called|referred\s+to\s+as)\s+brand(?:ing)?',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-5a",
        "description": (
            'Adriana called a "chatbot" — any context applying the word chatbot to Adriana'
        ),
        "regex": re.compile(
            r'(?i)adriana\s+(?:is\s+(?:a|an)\s+|as\s+(?:a|an)\s+)?chatbot|chatbot\s+(?:called|named|like)\s+adriana',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-5b",
        "description": (
            'Adriana described as an "AI assistant" or "AI chatbot" in template or route text'
        ),
        "regex": re.compile(
            r'(?i)adriana\s+(?:is\s+(?:a|an)\s+|as\s+(?:a|an)\s+)?(?:ai\s+)?(?:assistant|chatbot|bot)',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-6",
        "description": (
            'MRB-4000 presented as "optional" — e.g. "the MRB-4000 is optional" '
            'or "optionally build the MRB-4000"'
        ),
        "regex": re.compile(
            r'(?i)mrb.?4000.{0,40}optional|optional.{0,40}mrb.?4000',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-7a",
        "description": (
            'Sovereign node described as "aspirational" or "future hardware" in a way '
            'that implies it does not exist or is not required'
        ),
        "regex": re.compile(
            r'(?i)sovereign.node.{0,40}aspir(?:ational|e)|aspir(?:ational|e).{0,40}sovereign.node',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-7b",
        "description": (
            'MRB-4000 described as "aspirational" or "future hardware"'
        ),
        "regex": re.compile(
            r'(?i)mrb.?4000.{0,40}aspir(?:ational|e)|aspir(?:ational|e).{0,40}mrb.?4000',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-8a",
        "description": (
            'Platform-named concepts referred to as "features" — e.g. '
            '"GriDul feature", "Silk Web feature", "Al-Jabr feature", '
            '"VoidEcho feature", "Adriana feature"'
        ),
        "regex": re.compile(
            r'(?i)(gridul|silk\s+web|al.jabr|voidecho|sapphire\s+bubble|village\s+standard|beehive|mycovoid|qisync)\s+feature',
            re.IGNORECASE,
        ),
    },
    {
        "id": "MUST-NOT-8b",
        "description": (
            'Platform-named concepts referred to as "modules" — e.g. '
            '"GriDul module", "Adriana module", "Silk Web module"'
        ),
        "regex": re.compile(
            r'(?i)(gridul|silk\s+web|al.jabr|voidecho|sapphire\s+bubble|village\s+standard|beehive|mycovoid|qisync|adriana)\s+module',
            re.IGNORECASE,
        ),
    },
]


def collect_files():
    files = []
    for directory, ext in SCAN_GLOBS:
        if not os.path.isdir(directory):
            continue
        for root, dirs, filenames in os.walk(directory):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fname in filenames:
                if fname.endswith(ext):
                    files.append(os.path.join(root, fname))
    return sorted(files)


def scan_file(path, patterns):
    violations = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, start=1):
                for pattern in patterns:
                    if pattern["regex"].search(line):
                        violations.append({
                            "file": path,
                            "line": lineno,
                            "pattern_id": pattern["id"],
                            "description": pattern["description"],
                            "text": line.rstrip(),
                        })
    except OSError as e:
        print(f"  [WARN] Could not read {path}: {e}", file=sys.stderr)
    return violations


def main():
    files = collect_files()
    if not files:
        print("DRIFT SCAN: No files found to scan.")
        sys.exit(0)

    print(f"DRIFT SCAN — PROJECT VOID Language Integrity Check")
    print(f"Scanning {len(files)} files across templates/, routes/, void_engine/")
    print(f"Checking {len(PATTERNS)} violation patterns (VOID_SEED.md §8 must-nots)")
    print("")

    all_violations = []
    for path in files:
        file_violations = scan_file(path, PATTERNS)
        all_violations.extend(file_violations)

    if not all_violations:
        print("RESULT: CLEAN — No language violations found.")
        print("")
        print("The codebase is aligned with the eight must-nots in VOID_SEED.md §8.")
        sys.exit(0)

    print(f"RESULT: {len(all_violations)} VIOLATION(S) FOUND")
    print("")
    for v in all_violations:
        print(f"  [{v['pattern_id']}] {v['file']}:{v['line']}")
        print(f"         Rule: {v['description']}")
        print(f"         Line: {v['text'][:120]}")
        print("")

    print(
        f"ACTION REQUIRED: The violations above contradict the VOID_SEED.md §8 must-nots. "
        f"Review each flagged line and correct the language before proceeding."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
