#!/bin/bash
# Quick-start script for full Wikipedia → Ecosystem resonance ingestion
# Usage: ./scripts/ingest_wikipedia.sh [threshold] [resume]
# Example: ./scripts/ingest_wikipedia.sh 0.40 false

set -e

cd "$(dirname "$(dirname "$(readlink -f "$0")")")"

THRESHOLD=${1:-0.40}
RESUME=${2:-false}
ONLINE=${ONLINE:-false}

echo "=================================================="
echo "Wikipedia → Ecosystem Resonance Ingestion"
echo "=================================================="
echo ""
echo "Configuration:"
echo "  Threshold: $THRESHOLD (ecosystem relevance score)"
echo "  Resume: $RESUME"
echo "  Check disk: $ONLINE"
echo ""

# ============ Step 0: Pre-flight Checks ============
echo "[Step 0] Pre-flight Checks..."

# Check if Wikipedia source exists
if [ ! -f "data/enwiki-latest-pages-articles.xml.bz2" ]; then
  echo "❌ ERROR: Wikipedia dump not found at data/enwiki-latest-pages-articles.xml.bz2"
  echo ""
  echo "Download from: http://dumps.wikimedia.org/enwiki/latest/"
  echo "File: enwiki-latest-pages-articles.xml.bz2 (~20 GB)"
  echo ""
  echo "To download automatically (requires 20 GB disk + fast connection):"
  echo "  cd data"
  echo "  wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2"
  echo ""
  exit 1
fi

DUMP_SIZE=$(du -h data/enwiki-latest-pages-articles.xml.bz2 | cut -f1)
echo "✓ Wikipedia dump found ($DUMP_SIZE)"

# Check available disk space
AVAILABLE_GB=$(df /workspaces/Project-void/data | tail -1 | awk '{printf "%.0f", $4/1024/1024}')
echo "✓ Available disk space: ${AVAILABLE_GB}G"

if [ "$AVAILABLE_GB" -lt 50 ]; then
  echo "⚠️  WARNING: Less than 50GB available; may run out of space"
  read -p "Continue anyway? (y/n): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Check database
if [ ! -f "void.db" ]; then
  echo "Initializing database..."
  python3 -c "from void_engine.knowledge_tree_store import init_knowledge_tree_tables; init_knowledge_tree_tables()"
fi
echo "✓ Database ready"

# Check Python dependencies
python3 -c "import wikipedia, lxml" 2>/dev/null || {
  echo "Installing dependencies..."
  pip install --quiet wikipedia lxml pyyaml numpy
}
echo "✓ Dependencies installed"

echo ""
echo "=================================================="
echo "Step 1: Selective Encoding (Wikipedia → Names)"
echo "=================================================="
echo "Estimated time: 6-8 hours"
echo "Estimated output: 15-20 GB JSONL + 1-2M database rows"
echo ""

# Run selective encoder
START=$(date +%s)
python3 scripts/wikipedia_to_ecosystem_selective.py \
  --input data/enwiki-latest-pages-articles.xml.bz2 \
  --output data/wikipedia_ecosystem_full.jsonl \
  --threshold "$THRESHOLD" \
  --store-db \
  --verbose \
  $([ "$RESUME" = "true" ] && echo "--resume" || echo "")

ELAPSED=$(($(date +%s) - START))
echo ""
echo "✓ Selective encoding complete (${ELAPSED}s)"

# Count results
ARTICLES=$(grep -c . data/wikipedia_ecosystem_full.jsonl || echo "0")
echo "  Articles processed: $ARTICLES"

echo ""
echo "=================================================="
echo "Step 2: Build Resonance Graph (Names → Graph)"
echo "=================================================="
echo "Estimated time: 1-2 hours"
echo "Estimated output: 2-5 GB graph JSON + 10-20M edges"
echo ""

START=$(date +%s)
python3 scripts/build_ecosystem_resonance_graph.py \
  --corpus data/wikipedia_ecosystem_full.jsonl \
  --output data/wikipedia_resonance_graph_full.json \
  --verbose

ELAPSED=$(($(date +%s) - START))
echo ""
echo "✓ Resonance graph complete (${ELAPSED}s)"

echo ""
echo "=================================================="
echo "✓ FULL PIPELINE COMPLETE"
echo "=================================================="
echo ""
echo "Results:"
echo "  Articles encoded: $ARTICLES"
echo "  Graph: data/wikipedia_resonance_graph_full.json"
echo "  JSONL: data/wikipedia_ecosystem_full.jsonl"
echo "  Database: void.db (knowledge_tree_nodes table)"
echo ""
echo "Next steps:"
echo "  1. Start web interface: python3 main.py"
echo "  2. Visit: http://localhost:5000/knowledge-tree"
echo "  3. Browse articles and resonance convergence"
echo ""
echo "Query the resonance graph:"
echo "  python3 - <<'PY'"
echo "import json"
echo "with open('data/wikipedia_resonance_graph_full.json') as f:"
echo "    graph = json.load(f)"
echo "print(f'Total nodes: {len(graph[\"nodes\"])}')"
echo "print(f'Total edges: {len(graph[\"edges\"])}')"
echo "PY"
echo ""
