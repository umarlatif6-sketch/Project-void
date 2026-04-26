#!/usr/bin/env bash
set -euo pipefail

compose_cmd=(docker compose)
build_flag="--build"
keep_running=0
use_proxy=0
timeout_seconds="180"
run_oryx=0

usage() {
  cat <<'EOF'
Usage: scripts/smoke_test.sh [--proxy] [--keep-running] [--no-build] [--timeout SECONDS] [--oryx]

Boots the Project VOID Docker stack, waits for the selected HTTP surface,
checks /health and /wake, then tears the stack down unless --keep-running is set.
If --oryx is provided, also runs ORYX repair-state smoke and artifact checks.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --proxy)
      use_proxy=1
      shift
      ;;
    --keep-running)
      keep_running=1
      shift
      ;;
    --no-build)
      build_flag=""
      shift
      ;;
    --timeout)
      timeout_seconds="${2:-}"
      shift 2
      ;;
    --oryx)
      run_oryx=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

PORT="${PORT:-5000}"
PROXY_PORT="${PROXY_PORT:-8080}"
base_url="http://127.0.0.1:${PORT}"
profile_args=()
services=(db init web)

if [[ "$use_proxy" -eq 1 ]]; then
  profile_args+=(--profile proxy)
  services+=(proxy)
  base_url="http://127.0.0.1:${PROXY_PORT}"
fi

cleanup() {
  if [[ "$keep_running" -eq 0 ]]; then
    "${compose_cmd[@]}" "${profile_args[@]}" down --remove-orphans >/dev/null 2>&1 || true
  fi
}

show_failure_context() {
  echo "Smoke test failed. Recent compose status:" >&2
  "${compose_cmd[@]}" "${profile_args[@]}" ps >&2 || true
  echo >&2
  echo "Recent compose logs:" >&2
  "${compose_cmd[@]}" "${profile_args[@]}" logs --tail=80 >&2 || true
}

trap cleanup EXIT
trap show_failure_context ERR

echo "[void-smoke] Booting stack: ${services[*]}"
if [[ -n "$build_flag" ]]; then
  "${compose_cmd[@]}" "${profile_args[@]}" up -d "$build_flag" "${services[@]}"
else
  "${compose_cmd[@]}" "${profile_args[@]}" up -d "${services[@]}"
fi

echo "[void-smoke] Waiting for ${base_url}/health"
deadline=$((SECONDS + timeout_seconds))
until curl -fsS "${base_url}/health" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for ${base_url}/health" >&2
    exit 1
  fi
  sleep 2
done

echo "[void-smoke] Checking /wake"
wake_payload="$(mktemp)"
curl -fsS "${base_url}/wake" > "$wake_payload"
grep -q 'ghajini_tattoo\|genesis_seal\|seed_digest' "$wake_payload"
rm -f "$wake_payload"

echo "[void-smoke] Checking /preflight"
preflight_payload="$(mktemp)"
curl -fsS "${base_url}/preflight" > "$preflight_payload"
grep -q 'Pre-Flight Check' "$preflight_payload"
rm -f "$preflight_payload"

echo "[void-smoke] Checking /sdk"
sdk_payload="$(mktemp)"
curl -fsS "${base_url}/sdk" > "$sdk_payload"
grep -q 'Deterministic Event Integrity' "$sdk_payload"
rm -f "$sdk_payload"

if [[ "$run_oryx" -eq 1 ]]; then
  echo "[void-smoke] Running ORYX repair-state smoke flows"
  python3 scripts/oryx_repair_state_smoke.py --mode both --persist-db

  echo "[void-smoke] Validating ORYX smoke artifact"
  python3 scripts/check_oryx_repair_state_smoke_artifact.py
fi

echo "[void-smoke] PASS"
if [[ "$keep_running" -eq 1 ]]; then
  echo "[void-smoke] Stack left running by request"
fi