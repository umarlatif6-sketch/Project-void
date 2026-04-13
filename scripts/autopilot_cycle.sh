#!/bin/bash
# One-command autopilot cycle for chat-first operation.
# Runs story-world + public-source ingestion, builds chronicles, and emits a single summary.
#
# Usage:
#   bash scripts/autopilot_cycle.sh
#   bash scripts/autopilot_cycle.sh --threshold 0.30 --store-db true
#   bash scripts/autopilot_cycle.sh --team-role founder

set -euo pipefail

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

THRESHOLD="0.30"
STORE_DB="true"
TEAM_ROLE="all"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --threshold)
      THRESHOLD="${2:-0.30}"
      shift 2
      ;;
    --store-db)
      STORE_DB="${2:-true}"
      shift 2
      ;;
    --team-role)
      TEAM_ROLE="${2:-all}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ "$TEAM_ROLE" != "all" && "$TEAM_ROLE" != "founder" && "$TEAM_ROLE" != "operator" && "$TEAM_ROLE" != "research" ]]; then
  echo "Invalid --team-role value: $TEAM_ROLE"
  echo "Allowed values: all, founder, operator, research"
  exit 1
fi

echo "============================================================"
echo "AUTOPILOT CYCLE START"
echo "============================================================"
echo "threshold=$THRESHOLD store_db=$STORE_DB team_role=$TEAM_ROLE"
echo

run_store_db_arg=()
if [[ "$STORE_DB" == "true" ]]; then
  run_store_db_arg=(--store-db)
fi

ensure_input_or_skip() {
  local input_file="$1"
  local label="$2"
  if [[ -f "$input_file" ]]; then
    echo "✓ Found $label input: $input_file"
    return 0
  fi
  echo "⚠ Skipping $label (missing input: $input_file)"
  return 1
}

# 1) Story-world lane
if ensure_input_or_skip "data/story_world_ingest_template.jsonl" "story-world"; then
  python3 scripts/story_world_to_ecosystem_selective.py \
    --input data/story_world_ingest_template.jsonl \
    --output data/story_world_ecosystem.jsonl \
    --threshold "$THRESHOLD" \
    --source-label story_world \
    "${run_store_db_arg[@]}"

  python3 scripts/build_story_world_chronicle.py \
    --input data/story_world_ecosystem.jsonl \
    --output docs/STORY_WORLD_CHRONICLE.md \
    --title "Story World Chronicle"
fi

# 2) Public source lane - VoxCPM
if ensure_input_or_skip "data/public_source_voxcpm_template.jsonl" "public-source VoxCPM"; then
  python3 scripts/public_source_to_ecosystem_selective.py \
    --input data/public_source_voxcpm_template.jsonl \
    --output data/public_source_voxcpm_ecosystem.jsonl \
    --threshold "$THRESHOLD" \
    --source-label public_source \
    "${run_store_db_arg[@]}"

  python3 scripts/build_story_world_chronicle.py \
    --input data/public_source_voxcpm_ecosystem.jsonl \
    --output docs/PUBLIC_SOURCE_VOXCPM_CHRONICLE.md \
    --title "Public Source Chronicle"
fi

# 3) Public source lane - MiniCPM
if ensure_input_or_skip "data/public_source_minicpm_template.jsonl" "public-source MiniCPM"; then
  python3 scripts/public_source_to_ecosystem_selective.py \
    --input data/public_source_minicpm_template.jsonl \
    --output data/public_source_minicpm_ecosystem.jsonl \
    --threshold "$THRESHOLD" \
    --source-label public_source \
    "${run_store_db_arg[@]}"

  python3 scripts/build_story_world_chronicle.py \
    --input data/public_source_minicpm_ecosystem.jsonl \
    --output docs/PUBLIC_SOURCE_MINICPM_CHRONICLE.md \
    --title "Public Source Chronicle"
fi

# 4) Unified markdown summary (single glance)
python3 - <<'PY'
import json
from collections import defaultdict
from pathlib import Path

inputs = [
    ("story_world", Path("data/story_world_ecosystem.jsonl")),
    ("public_voxcpm", Path("data/public_source_voxcpm_ecosystem.jsonl")),
    ("public_minicpm", Path("data/public_source_minicpm_ecosystem.jsonl")),
]

rows = []
for source_key, path in inputs:
    if not path.exists():
        continue
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            obj["_feed"] = source_key
            rows.append(obj)
        except Exception:
            continue

clusters = defaultdict(lambda: {"name": "", "count": 0, "analogies": 0, "perspectives": 0, "feeds": set()})
for r in rows:
    t = r.get("tree") or {}
    idx = t.get("name_index", -1)
    name = t.get("name", "Unknown")
    c = clusters[idx]
    c["name"] = name
    c["count"] += 1
    c["analogies"] += len(r.get("analogies") or [])
    c["perspectives"] += len(r.get("perspectives") or [])
    c["feeds"].add(r.get("_feed", "unknown"))

ordered = sorted(clusters.items(), key=lambda kv: (kv[1]["analogies"] + kv[1]["perspectives"], kv[1]["count"]), reverse=True)

out = []
out.append("# Autopilot Cycle Summary")
out.append("")
out.append(f"Total entries across feeds: {len(rows)}")
out.append("")
out.append("## Feed Totals")
out.append("")
for feed_key, path in inputs:
    count = 0
    if path.exists():
        count = sum(1 for l in path.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip())
    out.append(f"- {feed_key}: {count}")
out.append("")
out.append("## Top Name Clusters")
out.append("")
for idx, data in ordered[:12]:
    z = str(idx).zfill(2) if isinstance(idx, int) and idx >= 0 else "??"
    out.append(
        f"- [{z}] {data['name']} | entries={data['count']} | analogies={data['analogies']} | perspectives={data['perspectives']} | feeds={','.join(sorted(data['feeds']))}"
    )
out.append("")
out.append("## Next Action")
out.append("")
out.append("- Open /knowledge-tree and use Signals Navigator with source=All signal feeds.")
out.append("- Filter by perspective to extract forward scenarios quickly.")

Path("docs/AUTOPILOT_CYCLE_SUMMARY.md").write_text("\n".join(out), encoding="utf-8")
print("WROTE docs/AUTOPILOT_CYCLE_SUMMARY.md")
print("ROWS", len(rows))
PY

# 5) Integration web + Adriana judgment narrative
python3 scripts/build_integration_web.py

# 6) Universal resonance-weaver baseline (same theory, different story)
python3 scripts/build_resonance_weaver_baseline.py

# 7) Team-facing one-page state card (role-aware)
python3 scripts/build_team_state_card.py --role "$TEAM_ROLE"

echo
echo "============================================================"
echo "AUTOPILOT CYCLE COMPLETE"
echo "============================================================"
echo "Summary: docs/AUTOPILOT_CYCLE_SUMMARY.md"
