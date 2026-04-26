#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "PROJECT VOID RE-ENTRY CHECKLIST"
echo "Date (UTC): $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo

echo "1) Read system map first:"
echo "   $ROOT_DIR/docs/VOID_SYSTEM_DISCOVERY_MAP_2026-04-26.md"
echo

echo "2) Read compressed seed state:"
echo "   $ROOT_DIR/VOID_SEED_DIGEST.md"
echo

echo "3) Read latest Chronicle tail (last 3 sessions):"
echo "   tail -n 220 $ROOT_DIR/VOID_CHRONICLE.md"
echo

echo "4) Confirm governance rail:"
echo "   $ROOT_DIR/.agents/genesis.md"
echo "   $ROOT_DIR/.agents/policy_engine.json"
echo "   $ROOT_DIR/.agents/bridge_policy.json"
echo

echo "5) Confirm proof rails:"
echo "   ls -1t $ROOT_DIR/data/void_proofboard/*.md | head -n 5"
echo "   ls -1t $ROOT_DIR/data/abyss_sim/* | head -n 5"
echo

echo "6) Claim boundary reminder:"
echo "   Model outputs are decision-grade, not factual physical certification until calibrated in physical tests."
echo

echo "7) Quick health command:"
echo "   git -C $ROOT_DIR status --short"
echo

echo "Re-entry complete. Continue from the most recent Forward Thread in VOID_CHRONICLE.md."
