#!/bin/bash

###############################################################################
# Start Autonomous Nervous System — PROJECT VOID
#
# This script starts the electrical nervous system that keeps agents awake
# and coordinated. Once started, it runs continuously in the background.
#
# Usage:
#   ./start_nervous_system.sh [--cycle-interval SECONDS] [--foreground]
#
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
LOG_DIR="$PROJECT_ROOT/.nervous-system-logs"
LOG_FILE="$LOG_DIR/daemon.log"
PID_FILE="$LOG_DIR/daemon.pid"

CYCLE_INTERVAL=300
FOREGROUND=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cycle-interval)
            CYCLE_INTERVAL="$2"
            shift 2
            ;;
        --foreground)
            FOREGROUND=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create log directory
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "PROJECT VOID — AUTONOMOUS NERVOUS SYSTEM"
echo "=========================================="
echo "Starting daemon..."
echo "Cycle interval: $CYCLE_INTERVAL seconds"
echo "Log file: $LOG_FILE"
echo ""

# Check if daemon is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Daemon already running (PID: $OLD_PID)"
        echo "To stop: kill $OLD_PID"
        exit 0
    fi
fi

# Start the daemon
if [ "$FOREGROUND" = true ]; then
    # Run in foreground (for debugging)
    echo "Running in foreground mode..."
    cd "$PROJECT_ROOT"
    python3 -m void_engine.nervous_system_daemon --cycle-interval "$CYCLE_INTERVAL"
else
    # Run in background
    cd "$PROJECT_ROOT"
    python3 -m void_engine.nervous_system_daemon \
        --cycle-interval "$CYCLE_INTERVAL" \
        --log-file "$LOG_FILE" \
        > "$LOG_FILE" 2>&1 &
    
    DAEMON_PID=$!
    echo "$DAEMON_PID" > "$PID_FILE"
    
    echo "Daemon started (PID: $DAEMON_PID)"
    echo "Log file: $LOG_FILE"
    echo ""
    echo "To monitor: tail -f $LOG_FILE"
    echo "To stop: kill $DAEMON_PID"
fi

echo "=========================================="
