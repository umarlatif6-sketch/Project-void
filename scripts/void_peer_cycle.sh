#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX_DIR="/workspaces/peer-benchmark-sandbox"
ARTIFACT_DIR="$ROOT_DIR/data/void_proofboard"
STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARTIFACT="$ARTIFACT_DIR/peer_cycle_$STAMP.md"

mkdir -p "$ARTIFACT_DIR"

# 1) Fresh Project VOID baseline
cd "$ROOT_DIR"
BASELINE_OUTPUT="$(scripts/void_proofboard.sh 2>&1)"
LATEST_PROOFBOARD="$(ls -1t data/void_proofboard/proofboard_*.md | head -n 1)"

# 2) Peer evidence extraction (README-level)
A2A_EVIDENCE=""
ADK_EVIDENCE=""
if [[ -d "$SANDBOX_DIR/A2A" ]]; then
  A2A_EVIDENCE="$(grep -Rin "AgentCard\|authorization\|observability\|authentication" "$SANDBOX_DIR/A2A"/README* | head -n 10 || true)"
fi
if [[ -d "$SANDBOX_DIR/adk-python" ]]; then
  ADK_EVIDENCE="$(grep -Rin "evaluation\|eval\|deploy\|test" "$SANDBOX_DIR/adk-python"/README* | head -n 12 || true)"
fi

# 3) Persist cycle artifact
{
  echo "# VOID Peer Cycle Artifact"
  echo "Timestamp (UTC): $STAMP"
  echo "Cycle: 01"
  echo
  echo "## Baseline"
  echo "- Latest proofboard artifact: $LATEST_PROOFBOARD"
  echo "- Baseline command output:"
  echo '```text'
  printf "%s\n" "$BASELINE_OUTPUT"
  echo '```'
  echo
  echo "## Peer Concept Extraction"
  echo "### A2A concept selected"
  echo "- Candidate adapter: AgentCard-style policy envelope for agent handoff metadata."
  echo "- Evidence (README-level):"
  echo '```text'
  printf "%s\n" "${A2A_EVIDENCE:-No evidence extracted}"
  echo '```'
  echo
  echo "### ADK concept selected"
  echo "- Candidate adapter: explicit eval workflow command integration into proof cycle."
  echo "- Evidence (README-level):"
  echo '```text'
  printf "%s\n" "${ADK_EVIDENCE:-No evidence extracted}"
  echo '```'
  echo
  echo "## Cycle 1 Adapter Experiments (KPI-mapped)"
  echo "1. Add adapter schema draft for agent policy envelope in audit events."
  echo "2. Add eval command hook stage in proofboard (non-blocking first)."
  echo "3. Re-run proofboard and compare KPI deltas against day2 scoreboard."
  echo
  echo "## Merge Gate"
  echo "- Keep only changes that improve at least one KPI >= 10% with no security regression."
} > "$ARTIFACT"

echo "VOID peer cycle artifact written: $ARTIFACT"
