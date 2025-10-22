#!/bin/bash
#
# Start script for v7.0 Supervisor Server
# Ensures correct Python version and environment
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KI AutoAgent v7.0 Server Startup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if we're in the right directory
if [ ! -f "backend/api/server_v7_supervisor.py" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    echo "Please run: cd /Users/dominikfoert/git/KI_AutoAgent"
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️ Virtual environment not found. Creating...${NC}"
    python3.13 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python --version | cut -d' ' -f2)
REQUIRED_VERSION="3.13.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python version $PYTHON_VERSION is too old${NC}"
    echo "Required: Python $REQUIRED_VERSION or higher"
    echo "Please install Python 3.13.8+ and recreate venv"
    exit 1
fi

echo -e "${GREEN}✅ Python version: $PYTHON_VERSION${NC}"

# Install/update requirements
echo "📚 Checking requirements..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Load environment variables if .env exists
ENV_FILE="$HOME/.ki_autoagent/config/.env"
if [ -f "$ENV_FILE" ]; then
    echo "🔑 Loading API keys from $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo -e "${YELLOW}⚠️ No .env file found at $ENV_FILE${NC}"
    echo "Web search will not be available without PERPLEXITY_API_KEY"
fi

# Set Python path
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Start server
echo -e "\n${GREEN}🚀 Starting v7.0 Supervisor Server...${NC}"
echo "📡 WebSocket: ws://localhost:8002/ws/chat"
echo "🔍 Health check: http://localhost:8002/health"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"

# Run the server
python backend/api/server_v7_supervisor.py