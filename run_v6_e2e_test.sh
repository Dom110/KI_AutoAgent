#!/bin/bash

##############################################################################
# Run v6 E2E Integration Test
#
# This script:
# 1. Starts the v6 integrated server (port 8002)
# 2. Waits for server to be ready
# 3. Runs the E2E test (E-Commerce app build)
# 4. Stops the server
# 5. Shows test results
#
# Usage:
#   ./run_v6_e2e_test.sh
#
# Author: KI AutoAgent Team
# Version: 6.0.0
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "============================================================================"
echo "🚀 v6 E2E Integration Test Runner"
echo "============================================================================"
echo ""

# Check if running from correct directory
if [ ! -f "backend/api/server_v6_integrated.py" ]; then
    echo -e "${RED}❌ Error: Must run from KI_AutoAgent root directory${NC}"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Error: Virtual environment not found${NC}"
    echo "   Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if server is already running on port 8002
if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8002 already in use. Killing existing process...${NC}"
    kill $(lsof -t -i:8002) 2>/dev/null || true
    sleep 2
fi

# Start server in background
echo -e "${BLUE}🚀 Starting v6 integrated server (port 8002)...${NC}"
python -m backend.api.server_v6_integrated > /tmp/ki_v6_server.log 2>&1 &
SERVER_PID=$!

echo -e "   Server PID: ${SERVER_PID}"
echo -e "   Log file: /tmp/ki_v6_server.log"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${BLUE}🛑 Stopping v6 integrated server...${NC}"
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Register cleanup function
trap cleanup EXIT INT TERM

# Wait for server to be ready
echo -e "${BLUE}⏳ Waiting for server to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is ready!${NC}"
        echo ""
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo ""
    echo -e "${RED}❌ Server failed to start within 30 seconds${NC}"
    echo ""
    echo "Server log:"
    tail -20 /tmp/ki_v6_server.log
    exit 1
fi

# Show server health
echo -e "${BLUE}📊 Server Health Check:${NC}"
curl -s http://localhost:8002/health | python -m json.tool | head -10
echo ""

# Run E2E test
echo ""
echo "============================================================================"
echo -e "${BLUE}🧪 Running E2E Test: Build E-Commerce Backend${NC}"
echo "============================================================================"
echo ""

if python test_e2e_v6_ecommerce.py; then
    echo ""
    echo "============================================================================"
    echo -e "${GREEN}🎉 E2E TEST PASSED! v6 Integration Validated!${NC}"
    echo "============================================================================"
    echo ""
    exit 0
else
    echo ""
    echo "============================================================================"
    echo -e "${RED}❌ E2E TEST FAILED${NC}"
    echo "============================================================================"
    echo ""
    echo "Server log (last 50 lines):"
    tail -50 /tmp/ki_v6_server.log
    echo ""
    exit 1
fi
