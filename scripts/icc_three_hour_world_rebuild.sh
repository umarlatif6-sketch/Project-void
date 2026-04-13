#!/usr/bin/env bash
set -euo pipefail

# ICC three-hour world rebuild pipeline
# Perspective over perception: run the proof stack as one coherent formation.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TS_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
OUT_DIR="data/icc_run_${TS_UTC//[:]/-}"
mkdir -p "$OUT_DIR"

echo "=== ICC WORLD REBUILD START ==="
echo "timestamp_utc: $TS_UTC"
echo "output_dir: $OUT_DIR"

echo "[1/5] Full convergence test"
python3 scripts/full_stack_convergence_test.py | tee "$OUT_DIR/01_full_stack_convergence.log"

echo "[2/5] All promised next steps pack"
python3 scripts/run_all_promised_next_steps.py | tee "$OUT_DIR/02_next_steps_pack.log"

echo "[3/5] 10M world construction"
python3 scripts/game_world_construction_10m.py | tee "$OUT_DIR/03_game_world_construction.log"

echo "[4/5] Binary selector (0 vs 1)"
python3 scripts/cockroach_agent_selector_01.py | tee "$OUT_DIR/04_selector_01.log"

echo "[5/5] Robustness selector (10 seeds)"
python3 scripts/cockroach_agent_selector_robustness.py 10 | tee "$OUT_DIR/05_selector_robustness.log"

echo "=== ICC WORLD REBUILD SUMMARY ===" | tee "$OUT_DIR/summary.txt"
{
  echo "generated_at_utc: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "winner_bit: $(grep -E '"winner_bit"' data/cockroach_agent_selector_01.json | head -1 | awk '{print $2}' | tr -d ',')"
  echo "recommended_bit: $(grep -E '"recommended_bit"' data/cockroach_agent_selector_robustness.json | head -1 | awk '{print $2}' | tr -d ',')"
  echo "recommendation: $(grep -E '"recommendation"' data/cockroach_agent_selector_robustness.json | head -1 | cut -d ':' -f2- | sed 's/^ //')"
  echo "convergence_report: data/full_stack_convergence_report.json"
  echo "next_steps_pack: data/next_steps_execution_pack.json"
  echo "world_construction_report: data/game_world_construction_10m.json"
  echo "integrated_world_report: data/void_world_construction_integrated_report.json"
  echo "selector_report: data/cockroach_agent_selector_01.json"
  echo "robustness_report: data/cockroach_agent_selector_robustness.json"
} | tee -a "$OUT_DIR/summary.txt"

echo "summary_file: $OUT_DIR/summary.txt"
echo "=== ICC WORLD REBUILD COMPLETE ==="
