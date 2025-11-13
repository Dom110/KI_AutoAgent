#!/bin/bash

PROJECT_DIR="/Users/dominikfoert/git/KI_AutoAgent"
LOG_DIR="$PROJECT_DIR/.logs"

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                    📊 E2E Test Log Monitor (Real-time)                        ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Find the latest logs
LATEST_FULL=$(ls -t "$LOG_DIR"/e2e_full_*.log 2>/dev/null | head -1)
LATEST_E2E=$(ls -t "$LOG_DIR"/e2e_test_*.log 2>/dev/null | head -1)
LATEST_SERVER=$(ls -t "$LOG_DIR"/server_*.log 2>/dev/null | head -1)

echo "🔍 Monitoring logs:"
echo "   📝 Server:   $LATEST_SERVER"
echo "   📝 E2E Test: $LATEST_E2E"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Monitor server logs
{
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━ SERVER LOGS ━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -f "$LATEST_SERVER"
} &
SERVER_PID=$!

# Monitor E2E logs
{
    sleep 0.5
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━ E2E TEST LOGS ━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -f "$LATEST_E2E"
} &
E2E_PID=$!

# Handle exit
trap "kill $SERVER_PID $E2E_PID 2>/dev/null" EXIT

wait
