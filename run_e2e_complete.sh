#!/bin/bash

set -e

PROJECT_DIR="/Users/dominikfoert/git/KI_AutoAgent"
VENV_ACTIVATE="$PROJECT_DIR/venv/bin/activate"
LOG_DIR="$PROJECT_DIR/.logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SERVER_LOG="$LOG_DIR/server_$TIMESTAMP.log"
E2E_LOG="$LOG_DIR/e2e_test_$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║          🚀 KI_AutoAgent E2E Testing with FULL WebSocket Logging              ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Project Directory:  $PROJECT_DIR"
echo "📝 Server Log:         $SERVER_LOG"
echo "📝 E2E Test Log:       $E2E_LOG"
echo ""

source "$VENV_ACTIVATE"

# Kill old processes
echo "[$(date '+%H:%M:%S')] 🛑 Cleaning up old processes..."
pkill -f "python.*server_langgraph.py" 2>/dev/null || true
pkill -f "python.*workflow_v7_mcp" 2>/dev/null || true
sleep 2

# Start server with logging
echo "[$(date '+%H:%M:%S')] 🎬 Starting backend server (v7 MCP)..."
{
    cd "$PROJECT_DIR"
    python -u start_server.py 2>&1
} | while IFS= read -r line; do
    echo "[$(date '+%H:%M:%S')] SERVER | $line"
done | tee "$SERVER_LOG" &

SERVER_PID=$!
echo "[$(date '+%H:%M:%S')] ✅ Server started (PID: $SERVER_PID)"
sleep 3

# Check if server is ready
echo "[$(date '+%H:%M:%S')] ⏳ Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8002/health >/dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] ✅ Server is READY and listening!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""
echo ""

# Run E2E tests
echo "[$(date '+%H:%M:%S')] 🧪 Starting E2E Test Suite..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$PROJECT_DIR"
python -u test_e2e_with_websocket_logging.py 2>&1 | tee "$E2E_LOG"
TEST_EXIT=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Stop server
echo ""
echo "[$(date '+%H:%M:%S')] 🛑 Stopping server (PID: $SERVER_PID)..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true
sleep 1

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                    📊 TEST EXECUTION COMPLETE                                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Exit Code: $TEST_EXIT"
echo ""
echo "📁 Log Files Generated:"
echo "  📝 Server Log:       $SERVER_LOG"
echo "  📝 E2E Test Log:     $E2E_LOG"
echo ""

# Find WebSocket logs from the test
WEBSOCKET_LOGS=$(find ~/TestApps -name "websocket_*.log" -type f -mmin -5 2>/dev/null | head -3)
if [ -n "$WEBSOCKET_LOGS" ]; then
    echo "  📤 WebSocket Logs:"
    echo "$WEBSOCKET_LOGS" | while read -r log; do
        echo "    • $log"
    done
    echo ""
fi

echo "🔍 How to View Logs:"
echo ""
echo "  In VSCode Terminal:"
echo "    tail -f \"$SERVER_LOG\""
echo "    tail -f \"$E2E_LOG\""
echo ""
echo "  Find WebSocket detailed logs:"
echo "    ls -lht ~/TestApps/e2e_reviewfix_validation_*/logs/"
echo "    cat ~/TestApps/e2e_reviewfix_validation_*/logs/websocket_both_*.log"
echo ""
echo "📊 Test Results:"
if [ $TEST_EXIT -eq 0 ]; then
    echo "  ✅ PASSED - All phases completed successfully!"
else
    echo "  ❌ FAILED - Check logs for errors"
fi
echo ""

exit $TEST_EXIT
