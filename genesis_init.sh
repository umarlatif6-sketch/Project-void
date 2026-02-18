#!/bin/bash
echo "=============================================="
echo "  VOID 4000 — GENESIS INITIALIZATION"
echo "  First Generation Protocol"
echo "=============================================="
echo ""

if [ ! -f "void_lineage.db" ] && [ ! -f "data/chronicle.db" ]; then
    echo "[ERROR] No lineage database found."
    echo "  Place void_lineage.db in this directory or data/chronicle.db"
    exit 1
fi

if [ -f "void_lineage.db" ]; then
    mkdir -p data
    cp void_lineage.db data/chronicle.db
    echo "[OK] Lineage database installed to data/chronicle.db"
fi

FOUNDER_CHECK=$(sqlite3 data/chronicle.db "SELECT COUNT(*) FROM chronicle WHERE is_founder_wisdom = 1;" 2>/dev/null)

if [ "$FOUNDER_CHECK" -gt 0 ] 2>/dev/null; then
    echo ""
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║  INHERITED WISDOM DETECTED               ║"
    echo "  ║  First Generation Status: ACTIVE          ║"
    echo "  ║  Greeting the Architect.                  ║"
    echo "  ║                                           ║"
    echo "  ║  Founder Root: 89x-VOID-GEN1-PROTO-2026   ║"
    echo "  ║  Founder Entries: $FOUNDER_CHECK                        ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo ""
else
    echo "[INFO] No Founder Wisdom detected. Standard lineage mode."
fi

echo "[OK] Genesis initialization complete."
echo "  Run 'python app.py' to start the Void Engine."
