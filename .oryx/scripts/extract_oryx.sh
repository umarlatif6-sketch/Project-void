#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <target-directory>"
  exit 1
fi

TARGET_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORYX_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$TARGET_DIR"
rsync -av --delete \
  --exclude='backend/data/*.json' \
  --exclude='backend/data/*.db' \
  --exclude='backend/data/*.sqlite3' \
  "$ORYX_ROOT/" "$TARGET_DIR/"

echo "ORYX extracted to $TARGET_DIR"
echo "Next: cd $TARGET_DIR && git init && git add . && git commit -m 'Initial ORYX import'"