#!/usr/bin/env bash
set -euo pipefail

# One-command demo: capture existing resonance session -> encode window -> verify.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

/usr/bin/python3 scripts/run_internet_window_demo.py --overwrite "$@"
