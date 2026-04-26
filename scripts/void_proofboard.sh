#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/data/void_proofboard"
STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARTIFACT="$ARTIFACT_DIR/proofboard_$STAMP.md"

mkdir -p "$ARTIFACT_DIR"

cd "$ROOT_DIR"

TEST_CMD=(pytest -q tests/test_oryx_audit_repair_state.py tests/test_oryx_repair_state_endpoints.py)
SMOKE_CMD=(python3 scripts/oryx_repair_state_smoke.py --mode both --persist-db)
CHECK_CMD=(python3 scripts/check_oryx_repair_state_smoke_artifact.py)

set +e
TEST_OUTPUT="$(${TEST_CMD[@]} 2>&1)"
TEST_EXIT=$?

SMOKE_OUTPUT="$(${SMOKE_CMD[@]} 2>&1)"
SMOKE_EXIT=$?

CHECK_OUTPUT="$(${CHECK_CMD[@]} 2>&1)"
CHECK_EXIT=$?
set -e

PASS_COUNT=$(printf "%s" "$TEST_OUTPUT" | grep -Eo '[0-9]+ passed' | head -n1 | awk '{print $1}' || true)
if [[ -z "${PASS_COUNT:-}" ]]; then
  PASS_COUNT="0"
fi

FAIL_COUNT=$(printf "%s" "$TEST_OUTPUT" | grep -Eo '[0-9]+ failed' | head -n1 | awk '{print $1}' || true)
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
  echo "- ORYX smoke command: ${SMOKE_CMD[*]}"
  echo "- ORYX smoke exit code: $SMOKE_EXIT"
  echo "- ORYX artifact check command: ${CHECK_CMD[*]}"
  echo "- ORYX artifact check exit code: $CHECK_EXIT"
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
  echo
  echo "## ORYX Smoke Output"
  echo '```text'
  printf "%s\n" "$SMOKE_OUTPUT"
  echo '```'
  echo
  echo "## ORYX Artifact Check Output"
  echo '```text'
  printf "%s\n" "$CHECK_OUTPUT"
  echo '```'
} > "$ARTIFACT"

echo "VOID Proofboard artifact written: $ARTIFACT"
if [[ $TEST_EXIT -ne 0 || $SMOKE_EXIT -ne 0 || $CHECK_EXIT -ne 0 ]]; then
  echo "Proofboard test run failed. See artifact for details."
  if [[ $TEST_EXIT -ne 0 ]]; then
    exit $TEST_EXIT
  fi
  if [[ $SMOKE_EXIT -ne 0 ]]; then
    exit $SMOKE_EXIT
  fi
  exit $CHECK_EXIT
fi

echo "Proofboard test run passed."
