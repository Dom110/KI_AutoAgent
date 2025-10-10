#!/bin/bash
"""
KI AutoAgent MCP Server Uninstallation Script

Removes all MCP server registrations from Claude CLI.

Usage:
    ./uninstall_mcp.sh

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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}KI AutoAgent MCP Server Uninstallation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Claude CLI
echo -e "${YELLOW}Checking Claude CLI...${NC}"
if ! command -v claude &> /dev/null; then
    echo -e "${RED}❌ Claude CLI not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Claude CLI found${NC}"
echo ""

# Remove servers
echo -e "${YELLOW}Removing MCP servers...${NC}"
echo ""

# 1. Perplexity
echo -e "${BLUE}Removing Perplexity...${NC}"
if claude mcp remove perplexity 2>/dev/null; then
    echo -e "${GREEN}✅ Perplexity removed${NC}"
else
    echo -e "${YELLOW}⚠️  Perplexity not registered (skipping)${NC}"
fi

# 2. Tree-sitter
echo -e "${BLUE}Removing Tree-sitter...${NC}"
if claude mcp remove tree-sitter 2>/dev/null; then
    echo -e "${GREEN}✅ Tree-sitter removed${NC}"
else
    echo -e "${YELLOW}⚠️  Tree-sitter not registered (skipping)${NC}"
fi

# 3. Memory
echo -e "${BLUE}Removing Memory...${NC}"
if claude mcp remove memory 2>/dev/null; then
    echo -e "${GREEN}✅ Memory removed${NC}"
else
    echo -e "${YELLOW}⚠️  Memory not registered (skipping)${NC}"
fi

echo ""

# Verify
echo -e "${YELLOW}Verifying removal...${NC}"
echo ""
claude mcp list
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Uninstallation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}All MCP servers have been removed.${NC}"
echo ""
echo -e "${YELLOW}To reinstall:${NC}"
echo -e "  ./install_mcp.sh"
echo ""
