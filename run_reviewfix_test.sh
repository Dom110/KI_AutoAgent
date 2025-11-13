#!/bin/bash
#
# Run ReviewFix E2E Test
#

set -e

PROJECT_ROOT="/Users/dominikfoert/git/KI_AutoAgent"
VENV="$PROJECT_ROOT/venv/bin/python"

echo "🚀 ReviewFix E2E Test Runner"
echo "============================"

# Kill any old processes
echo "🛑 Stopping old server processes..."
pkill -f "server_v7_mcp" 2>/dev/null || true
sleep 2

# Start server in background
echo "🔧 Starting server..."
$VENV "$PROJECT_ROOT/backend/api/server_v7_mcp.py" > "$PROJECT_ROOT/test_server.log" 2>&1 &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"

# Wait for server to start
echo "⏳ Waiting for server startup..."
for i in {1..30}; do
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    echo -n "."
    sleep 1
done

# Check if server is running
if ! curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "❌ Server failed to start"
    echo "Log:"
    tail -30 "$PROJECT_ROOT/test_server.log"
    exit 1
fi

# Run test
echo ""
echo "🧪 Running ReviewFix test..."
echo ""
$VENV "$PROJECT_ROOT/test_reviewfix_simple.py"
TEST_RESULT=$?

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $SERVER_PID 2>/dev/null || true

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ TEST PASSED"
else
    echo "❌ TEST FAILED"
fi

exit $TEST_RESULT