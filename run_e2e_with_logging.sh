#!/bin/bash

set -e

PROJECT_DIR="/Users/dominikfoert/git/KI_AutoAgent"
VENV_ACTIVATE="$PROJECT_DIR/venv/bin/activate"
LOG_DIR="$PROJECT_DIR/.logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SERVER_LOG="$LOG_DIR/server_$TIMESTAMP.log"
E2E_LOG="$LOG_DIR/e2e_test_$TIMESTAMP.log"
WEBSOCKET_LOG="$LOG_DIR/websocket_$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "🚀 KI_AutoAgent E2E Testing with Full Logging"
echo "=================================================="
echo "📁 Project: $PROJECT_DIR"
echo "📝 Server Log: $SERVER_LOG"
echo "📝 E2E Test Log: $E2E_LOG"
echo "📝 WebSocket Log: $WEBSOCKET_LOG"
echo ""

# Aktiviere venv
source "$VENV_ACTIVATE"

# Stoppe alte Server
echo "[$(date '+%H:%M:%S')] 🛑 Stopping old server processes..."
pkill -f "python.*server_langgraph.py" || true
pkill -f "python.*workflow_v7_mcp.py" || true
sleep 2

# Starte Server mit tee
echo "[$(date '+%H:%M:%S')] 🎬 Starting server with logging..."
{
    cd "$PROJECT_DIR/backend"
    python -u server_langgraph.py 2>&1 | while IFS= read -r line; do
        echo "$(date '+%Y-%m-%d %H:%M:%S.%N' | cut -c1-23) | SERVER | $line"
    done
} | tee "$SERVER_LOG" &
SERVER_PID=$!

echo "[$(date '+%H:%M:%S')] ✅ Server started (PID: $SERVER_PID)"
echo ""

# Warte bis Server bereit ist
echo "[$(date '+%H:%M:%S')] ⏳ Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] ✅ Server is READY!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Starte E2E Tests mit WebSocket-Logging
echo "[$(date '+%H:%M:%S')] 🧪 Starting E2E Tests..."
echo ""

cd "$PROJECT_DIR"

# Erstelle Wrapper-Script für WebSocket-Logging
cat > "$LOG_DIR/test_runner_$TIMESTAMP.py" << 'EOF'
import sys
sys.path.insert(0, '/Users/dominikfoert/git/KI_AutoAgent')

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

WEBSOCKET_LOG = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/websocket.log")

class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        with open(WEBSOCKET_LOG, 'a') as f:
            f.write(msg + '\n')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger()
logger.addHandler(WebSocketLogHandler())

# Import und starte Tests
import test_e2e_reviewfix_validation

asyncio.run(test_e2e_reviewfix_validation.main())
EOF

python "$LOG_DIR/test_runner_$TIMESTAMP.py" "$WEBSOCKET_LOG" 2>&1 | tee "$E2E_LOG"
TEST_EXIT=$?

echo ""
echo "[$(date '+%H:%M:%S')] 🛑 Stopping server..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "=================================================="
echo "📊 Test Execution Complete (Exit Code: $TEST_EXIT)"
echo ""
echo "📁 Log Files:"
echo "  • Server:    $SERVER_LOG"
echo "  • E2E Test:  $E2E_LOG"
echo "  • WebSocket: $WEBSOCKET_LOG"
echo ""
echo "🔍 View logs with:"
echo "  tail -f \"$SERVER_LOG\""
echo "  tail -f \"$E2E_LOG\""
echo "  tail -f \"$WEBSOCKET_LOG\""
echo ""
echo "🔗 Summary:"
tail -20 "$E2E_LOG" | grep -E "PASS|FAIL|ERROR|===|---" || echo "  No summary found"
echo ""

exit $TEST_EXIT
