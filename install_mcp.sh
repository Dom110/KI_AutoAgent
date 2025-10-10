#!/bin/bash
"""
KI AutoAgent MCP Server Installation Script

Registers all 4 MCP servers with Claude CLI:
1. Perplexity - Web search
2. Tree-sitter - Code analysis
3. Memory - Agent memory access
4. Asimov - Code safety & compliance

Usage:
    ./install_mcp.sh

Requirements:
- Claude CLI installed (https://claude.ai/download)
- Backend venv at backend/venv_v6/bin/python
- OPENAI_API_KEY in ~/.ki_autoagent/config/.env

Author: KI AutoAgent Team
Version: 1.0.0
"""

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}KI AutoAgent MCP Server Installation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Claude CLI
echo -e "${YELLOW}1️⃣  Checking Claude CLI...${NC}"
if ! command -v claude &> /dev/null; then
    echo -e "${RED}❌ Claude CLI not found!${NC}"
    echo -e "${YELLOW}Please install from: https://claude.ai/download${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Claude CLI found: $(which claude)${NC}"
echo ""

# Check backend venv
echo -e "${YELLOW}2️⃣  Checking backend venv...${NC}"
VENV_PYTHON="${SCRIPT_DIR}/backend/venv_v6/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}❌ Backend venv not found at: ${VENV_PYTHON}${NC}"
    echo -e "${YELLOW}Please create backend venv first!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend venv found: ${VENV_PYTHON}${NC}"
echo ""

# Check OPENAI_API_KEY
echo -e "${YELLOW}3️⃣  Checking OPENAI_API_KEY...${NC}"
ENV_FILE="$HOME/.ki_autoagent/config/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env file not found at: ${ENV_FILE}${NC}"
    echo -e "${YELLOW}Memory server will require OPENAI_API_KEY!${NC}"
else
    if grep -q "OPENAI_API_KEY" "$ENV_FILE"; then
        echo -e "${GREEN}✅ OPENAI_API_KEY found in .env${NC}"
    else
        echo -e "${YELLOW}⚠️  OPENAI_API_KEY not found in .env${NC}"
        echo -e "${YELLOW}Memory server will require OPENAI_API_KEY!${NC}"
    fi
fi
echo ""

# Register servers
echo -e "${YELLOW}4️⃣  Registering MCP servers...${NC}"
echo ""

# Remove existing registrations first (avoid duplicates)
echo -e "${BLUE}Removing existing registrations (if any)...${NC}"
claude mcp remove perplexity 2>/dev/null || true
claude mcp remove tree-sitter 2>/dev/null || true
claude mcp remove memory 2>/dev/null || true
claude mcp remove asimov 2>/dev/null || true
echo ""

# 1. Perplexity
echo -e "${BLUE}📡 Registering Perplexity MCP Server...${NC}"
claude mcp add perplexity "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/perplexity_server.py"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Perplexity registered${NC}"
else
    echo -e "${RED}❌ Perplexity registration failed${NC}"
    exit 1
fi
echo ""

# 2. Tree-sitter
echo -e "${BLUE}🌲 Registering Tree-sitter MCP Server...${NC}"
claude mcp add tree-sitter "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/tree_sitter_server.py"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Tree-sitter registered${NC}"
else
    echo -e "${RED}❌ Tree-sitter registration failed${NC}"
    exit 1
fi
echo ""

# 3. Memory (use venv Python!)
echo -e "${BLUE}🧠 Registering Memory MCP Server...${NC}"
claude mcp add memory "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/memory_server.py"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Memory registered${NC}"
else
    echo -e "${RED}❌ Memory registration failed${NC}"
    exit 1
fi
echo ""

# 4. Asimov
echo -e "${BLUE}🛡️  Registering Asimov Rules MCP Server...${NC}"
claude mcp add asimov "${VENV_PYTHON}" "${SCRIPT_DIR}/mcp_servers/asimov_server.py"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Asimov registered${NC}"
else
    echo -e "${RED}❌ Asimov registration failed${NC}"
    exit 1
fi
echo ""

# Verify registration
echo -e "${YELLOW}5️⃣  Verifying registration...${NC}"
echo ""
claude mcp list
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Registered MCP Servers:${NC}"
echo -e "  1. ${GREEN}perplexity${NC} - Web search via Perplexity API"
echo -e "  2. ${GREEN}tree-sitter${NC} - Code analysis (Python, JS, TS)"
echo -e "  3. ${GREEN}memory${NC} - Agent memory access"
echo -e "  4. ${GREEN}asimov${NC} - Code safety & compliance validation"
echo ""
echo -e "${BLUE}Usage Examples:${NC}"
echo -e "  ${YELLOW}# Web search${NC}"
echo -e "  claude \"Research Python async patterns using perplexity\""
echo ""
echo -e "  ${YELLOW}# Code analysis${NC}"
echo -e "  claude \"Analyze main.py with tree-sitter\""
echo ""
echo -e "  ${YELLOW}# Code safety${NC}"
echo -e "  claude \"Validate this code with asimov rules\""
echo ""
echo -e "  ${YELLOW}# Memory operations${NC}"
echo -e "  claude \"Store in memory: React 18 + Vite recommended\""
echo -e "  claude \"Search memory for frontend recommendations\""
echo ""
echo -e "${BLUE}Testing:${NC}"
echo -e "  Run tests: ${YELLOW}./test_all_mcp.sh${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
