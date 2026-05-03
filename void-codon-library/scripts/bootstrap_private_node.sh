#!/usr/bin/env bash
set -euo pipefail

# One-command bootstrap for trusted node hosts (e.g., ESP32 gateway/control host).
# Creates an isolated venv, installs void-codon-library privately, and validates import.

BASE_DIR="${VOID_NODE_BASE_DIR:-${HOME}/.void-node}"
VENV_DIR="${VOID_NODE_VENV:-${BASE_DIR}/venv}"
SYSTEM_PYTHON="${VOID_NODE_SYSTEM_PYTHON:-python3}"
DRY_RUN="${1:-}"

if [[ "${DRY_RUN}" == "--dry-run" ]]; then
  echo "[dry-run] bootstrap_private_node.sh"
  echo "[dry-run] base_dir=${BASE_DIR}"
  echo "[dry-run] venv_dir=${VENV_DIR}"
  echo "[dry-run] system_python=${SYSTEM_PYTHON}"
  echo "[dry-run] requires GH_TOKEN and repo read access"
  exit 0
fi

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "Missing GH_TOKEN. Export a token with repository read access." >&2
  exit 1
fi

mkdir -p "${BASE_DIR}"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  "${SYSTEM_PYTHON}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${VENV_DIR}/bin/python" GH_TOKEN="${GH_TOKEN}" "${SCRIPT_DIR}/install_private.sh"

"${VENV_DIR}/bin/python" - << 'PY'
from void_codon_library import get_codon, get_lbn_codons

entry = get_codon("adriana", library="platform")
if entry is None:
    raise SystemExit("bootstrap smoke test failed: adriana codon missing")

if len(get_lbn_codons()) != 10:
    raise SystemExit("bootstrap smoke test failed: unexpected LBN codon count")

print("bootstrap_ok", entry.codon)
PY

cat << EOF
Node bootstrap complete.
Venv: ${VENV_DIR}
Quick test:
  ${VENV_DIR}/bin/python -c "from void_codon_library import get_codon; print(get_codon('adriana', library='platform').codon)"
EOF
