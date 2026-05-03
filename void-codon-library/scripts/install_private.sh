#!/usr/bin/env bash
set -euo pipefail

# Private install for void-codon-library from Project-void repo subdirectory.
# Requires a token that can read the repository.

OWNER="${VOID_REPO_OWNER:-umarlatif6-sketch}"
REPO="${VOID_REPO_NAME:-Project-void}"
REF="${VOID_REPO_REF:-main}"
SUBDIR="${VOID_PACKAGE_SUBDIR:-void-codon-library}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DRY_RUN="${1:-}"

if [[ "${DRY_RUN}" == "--dry-run" ]]; then
  echo "[dry-run] install_private.sh"
  echo "[dry-run] owner=${OWNER} repo=${REPO} ref=${REF} subdir=${SUBDIR} python=${PYTHON_BIN}"
  exit 0
fi

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "Missing GH_TOKEN. Export a token with repository read access." >&2
  echo "Example: export GH_TOKEN=ghp_xxx" >&2
  exit 1
fi

PKG_URL="git+https://github.com/${OWNER}/${REPO}.git@${REF}#subdirectory=${SUBDIR}"

# Use GIT_ASKPASS so the token is not embedded in the pip/git command line.
ASKPASS_SCRIPT="$(mktemp)"
trap 'rm -f "${ASKPASS_SCRIPT}"' EXIT

cat > "${ASKPASS_SCRIPT}" << 'EOF'
#!/usr/bin/env sh
case "$1" in
  *Username*)
    echo "x-access-token"
    ;;
  *)
    echo "${GH_TOKEN}"
    ;;
esac
EOF

chmod 700 "${ASKPASS_SCRIPT}"

GIT_ASKPASS="${ASKPASS_SCRIPT}" GIT_TERMINAL_PROMPT=0 "${PYTHON_BIN}" -m pip install --upgrade "${PKG_URL}"
echo "Installed void-codon-library from private GitHub source (${OWNER}/${REPO}@${REF})."
