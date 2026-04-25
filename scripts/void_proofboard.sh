#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/data/void_proofboard"
STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARTIFACT="$ARTIFACT_DIR/proofboard_$STAMP.md"

mkdir -p "$ARTIFACT_DIR"

cd "$ROOT_DIR"

TEST_CMD=(pytest -q tests/test_oryx_audit_repair_state.py tests/test_oryx_repair_state_endpoints.py)

set +e
TEST_OUTPUT="$(${TEST_CMD[@]} 2>&1)"
TEST_EXIT=$?
set -e

PASS_COUNT=$(printf "%s" "$TEST_OUTPUT" | grep -Eo '[0-9]+ passed' | head -n1 | awk '{print $1}')
if [[ -z "${PASS_COUNT:-}" ]]; then
  PASS_COUNT="0"
fi

FAIL_COUNT=$(printf "%s" "$TEST_OUTPUT" | grep -Eo '[0-9]+ failed' | head -n1 | awk '{print $1}')
if [[ -z "${FAIL_COUNT:-}" ]]; then
  FAIL_COUNT="0"
fi

{
  echo "# VOID Proofboard Artifact"
  echo "Timestamp (UTC): $STAMP"
  echo "Wedge: ORYX Audit Filtering + Repair-State Governance"
  echo
  echo "## Test Summary"
  echo "- Command: ${TEST_CMD[*]}"
  echo "- Exit code: $TEST_EXIT"
  echo "- Passed tests: $PASS_COUNT"
  echo "- Failed tests: $FAIL_COUNT"
  echo
  echo "## KPI Placeholders"
  echo "- Incident triage time reduction (%): [fill after scenario run]"
  echo "- Mean queries to root action reduction (%): [fill after scenario run]"
  echo "- Unauthorized access success rate (%): [expected 0]"
  echo "- Filter correctness (%): [expected 100]"
  echo "- Stability pass rate (%): [expected 100]"
  echo
  echo "## Raw Test Output"
  echo '```text'
  printf "%s\n" "$TEST_OUTPUT"
  echo '```'
} > "$ARTIFACT"

echo "VOID Proofboard artifact written: $ARTIFACT"
if [[ $TEST_EXIT -ne 0 ]]; then
  echo "Proofboard test run failed. See artifact for details."
  exit $TEST_EXIT
fi

echo "Proofboard test run passed."
