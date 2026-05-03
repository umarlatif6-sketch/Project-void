#!/usr/bin/env bash
set -euo pipefail

# Private install for void-codon-library from Project-void repo subdirectory.
# Requires a token that can read the repository.

OWNER="${VOID_REPO_OWNER:-umarlatif6-sketch}"
REPO="${VOID_REPO_NAME:-Project-void}"
REF="${VOID_REPO_REF:-main}"
SUBDIR="${VOID_PACKAGE_SUBDIR:-void-codon-library}"

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "Missing GH_TOKEN. Export a token with repository read access." >&2
  echo "Example: export GH_TOKEN=ghp_xxx" >&2
  exit 1
fi

PKG_URL="git+https://x-access-token:${GH_TOKEN}@github.com/${OWNER}/${REPO}.git@${REF}#subdirectory=${SUBDIR}"

python3 -m pip install --upgrade "${PKG_URL}"
echo "Installed void-codon-library from private GitHub source (${OWNER}/${REPO}@${REF})."
