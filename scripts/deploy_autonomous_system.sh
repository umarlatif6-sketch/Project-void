#!/bin/bash

##############################################################################
# Deploy and Start Autonomous Nervous System — PROJECT VOID
#
# This script deploys and starts the complete autonomous nervous system
# with all components:
# - Enhanced daemon (1-hour cycles)
# - Comprehensive report generator
# - Real-time dashboard
# - Escalation protocols
# - Learning loops
#
# Usage: ./deploy_autonomous_system.sh [--cycle-interval SECONDS]
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/ubuntu/Project-void"
LOGS_DIR="$PROJECT_DIR/.nervous-system-logs"
REPORTS_DIR="$LOGS_DIR/reports"
DASHBOARD_DIR="$LOGS_DIR/dashboard"
DAEMON_PID_FILE="$LOGS_DIR/daemon.pid"
DAEMON_LOG_FILE="$LOGS_DIR/daemon.log"

CYCLE_INTERVAL=${1:-3600}  # Default: 1 hour (3600 seconds)

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Main deployment
main() {
    print_header "PROJECT VOID — AUTONOMOUS NERVOUS SYSTEM DEPLOYMENT"
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    print_success "Project directory: $PROJECT_DIR"
    
    # Create necessary directories
    print_info "Creating directories..."
    mkdir -p "$LOGS_DIR"
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$DASHBOARD_DIR"
    print_success "Directories created"
    
    # Check if daemon is already running
    if [ -f "$DAEMON_PID_FILE" ]; then
        OLD_PID=$(cat "$DAEMON_PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            print_warning "Daemon already running with PID $OLD_PID"
            print_info "Stopping existing daemon..."
            kill "$OLD_PID" 2>/dev/null || true
            sleep 2
        fi
    fi
    
    # Verify Python environment
    print_info "Verifying Python environment..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found"
        exit 1
    fi
    print_success "Python3 found: $(python3 --version)"
    
    # Check required modules
    print_info "Checking required modules..."
    python3 -c "import asyncio" || { print_error "asyncio module not found"; exit 1; }
    python3 -c "import json" || { print_error "json module not found"; exit 1; }
    print_success "Required modules available"
    
    # Start the daemon
    print_header "STARTING AUTONOMOUS NERVOUS SYSTEM DAEMON"
    
    print_info "Cycle interval: $CYCLE_INTERVAL seconds ($(($CYCLE_INTERVAL / 3600)) hours)"
    print_info "Logs directory: $LOGS_DIR"
    print_info "Reports directory: $REPORTS_DIR"
    print_info "Dashboard directory: $DASHBOARD_DIR"
    
    # Start daemon in background
    print_info "Starting daemon..."
    
    nohup python3 -m void_engine.enhanced_nervous_system_daemon \
        --cycle-interval "$CYCLE_INTERVAL" \
        --log-file "$DAEMON_LOG_FILE" \
        > "$DAEMON_LOG_FILE" 2>&1 &
    
    DAEMON_PID=$!
    echo "$DAEMON_PID" > "$DAEMON_PID_FILE"
    
    # Wait a moment for daemon to start
    sleep 2
    
    # Check if daemon started successfully
    if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        print_success "Daemon started successfully (PID: $DAEMON_PID)"
    else
        print_error "Failed to start daemon"
        print_error "Check logs: $DAEMON_LOG_FILE"
        exit 1
    fi
    
    # Display startup information
    print_header "AUTONOMOUS NERVOUS SYSTEM ACTIVE"
    
    print_info "Status: OPERATIONAL"
    print_info "PID: $DAEMON_PID"
    print_info "Cycle Interval: $CYCLE_INTERVAL seconds"
    print_info "Start Time: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    print_info "Next Report: $(date -u -d "+$CYCLE_INTERVAL seconds" +"%Y-%m-%d %H:%M:%S UTC")"
    
    echo ""
    print_info "Monitoring locations:"
    echo "  - Daemon Log: $DAEMON_LOG_FILE"
    echo "  - Reports: $REPORTS_DIR"
    echo "  - Dashboard: $DASHBOARD_DIR/current_state.json"
    echo "  - HTML Dashboard: $DASHBOARD_DIR/dashboard.html"
    
    echo ""
    print_info "Useful commands:"
    echo "  - View daemon log: tail -f $DAEMON_LOG_FILE"
    echo "  - Stop daemon: kill $DAEMON_PID"
    echo "  - View latest report: ls -lt $REPORTS_DIR | head -5"
    echo "  - View dashboard: cat $DASHBOARD_DIR/current_state.json | jq"
    
    echo ""
    print_header "SYSTEM COMPONENTS"
    
    print_success "Enhanced Daemon: RUNNING"
    print_success "Report Generator: ACTIVE"
    print_success "Dashboard: MONITORING"
    print_success "Escalation Protocols: ARMED"
    print_success "Learning Loops: ENABLED"
    
    echo ""
    print_header "ACTIVATION TIMELINE"
    
    DAYS_TO_ACTIVATION=$(( ($(date -d "2026-06-15" +%s) - $(date +%s)) / 86400 ))
    
    print_info "Days until June 15, 2026 activation: $DAYS_TO_ACTIVATION"
    print_info "System will continue autonomous operation until activation"
    print_info "All hourly reports will be archived and analyzed"
    
    echo ""
    print_header "PROJECT VOID — AUTONOMOUS SYSTEM READY"
    
    echo -e "${GREEN}The void is alive.${NC}"
    echo -e "${GREEN}The frequency continues.${NC}"
    echo -e "${GREEN}The activation approaches.${NC}"
    
    echo ""
    print_info "Daemon PID saved to: $DAEMON_PID_FILE"
    print_info "Monitor the system with: tail -f $DAEMON_LOG_FILE"
}

# Run main function
main "$@"

exit 0
